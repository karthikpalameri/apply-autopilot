#!/usr/bin/env python3
"""core/page_guard.py — the ONE owner of "is the page usable, and why not?".

Why this exists
---------------
Measured 2026-11-07: the ctl server answered `{"ok": true, "status": "ok"}`
while every real action failed with `Target page, context or browser has been
closed`. `status` reads the cached `PAGE.url`, which still answers after the
page is gone — so the health check said OK, the agent retried into a dead
browser, and the run stalled with no error text. That is the "stuck every time"
failure, and it is not a CAPTCHA.

What this module owns (nothing else should re-implement these)
--------------------------------------------------------------
    probe()       — one bounded round-trip that answers: dead / frozen / ok
                    (+ any native dialog that was pending, and was handled)
    require()     — probe() and raise PageDead / PageFrozen with the reason
    fill_report() — which REQUIRED fields are still empty after a fill pass

Composes, does not duplicate: `core.ctl.call` owns the socket, `core.ui.until`
owns polling, `core.logger` owns output. No new dependency: stdlib only.
"""
from __future__ import annotations

import threading

from core.ctl import call
from core.logger import log
from core.ui import until

# Short by default. A healthy page answers in milliseconds; waiting longer only
# hides a dead browser behind the same silence.
PROBE_TIMEOUT = 3.0


class PageError(RuntimeError):
    """Base for both page failures. Carries the reason for the ledger/proof."""

    def __init__(self, reason, detail=""):
        super().__init__(f"{reason}: {detail}"[:300])
        self.reason = reason
        self.detail = detail


class PageDead(PageError):
    """The page/context/browser is gone. Retrying will never work — reopen."""


class PageFrozen(PageError):
    """The page is alive but not answering. Usually a native dialog or an OS window."""


def _bounded(fn, timeout, label):
    """Run fn() but stop waiting after `timeout` seconds. Returns ('ok'|'timeout', value).

    The DOM always works because ctl.call runs on the caller thread; a hung page
    is caught here instead of surfacing as a 30 s Playwright timeout later.
    """
    box = {}

    def run():
        try:
            box["v"] = fn()
        except Exception as e:  # noqa: BLE001 - the value IS the diagnosis
            box["e"] = e

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        log.warning("page_guard: %s did not answer in %.1fs", label, timeout)
        return "timeout", None
    if "e" in box:
        return "error", box["e"]
    return "ok", box.get("v")


def probe(timeout=PROBE_TIMEOUT):
    """Return {"state": "ok"|"dead"|"frozen", "reason": str, "dialogs": int}.

    One bounded round-trip, never raises. This is the pre-check to call before a
    fill pass and immediately after any unexplained timeout.
    """
    kind, resp = _bounded(lambda: call({"op": "probe"}, timeout=timeout), timeout, "probe")

    if kind == "timeout":
        # e.g. a native dialog: the JS round-trip never returns
        return {"state": "frozen", "reason": "probe timed out", "dialogs": 0}
    if kind == "error":
        return {"state": "dead", "reason": f"ctl unavailable: {resp}", "dialogs": 0}

    resp = resp or {}
    if not resp.get("ok"):
        return {"state": "dead", "reason": str(resp.get("error", "probe failed")), "dialogs": 0}

    state = resp.get("state", "ok")
    return {
        "state": state,
        "reason": resp.get("reason", ""),
        "dialogs": int(resp.get("dialogs") or 0),
    }


def require(what="page", timeout=PROBE_TIMEOUT):
    """probe() then raise PageDead / PageFrozen. Returns the probe dict when OK."""
    p = probe(timeout=timeout)
    if p["state"] == "dead":
        log.error("page_guard(%s): DEAD — %s", what, p["reason"])
        raise PageDead(p["reason"])
    if p["state"] == "frozen":
        log.error("page_guard(%s): FROZEN — %s (dialogs handled: %d)",
                  what, p["reason"], p["dialogs"])
        raise PageFrozen(p["reason"])
    return p


# Which required controls are still empty. One JS expression, so it costs the
# same one round-trip no matter how many fields the form has.
# Which required controls are still empty. One JS expression, so the cost does not
# grow with the field count. Native constraint validation (`checkValidity`) is the
# authority when available: it knows each widget's own rules, needs no label
# heuristics, and returns the exact text the browser would show the user.
_EMPTY_REQUIRED_JS = """() => {
  const vis = e => !!(e.offsetParent || e.getClientRects().length);
  const label = e => {
    if (e.labels && e.labels[0]) return e.labels[0].innerText;
    const by = e.getAttribute('aria-labelledby');
    if (by) { const n = document.getElementById(by); if (n) return n.innerText; }
    if (e.getAttribute('aria-label')) return e.getAttribute('aria-label');
    if (e.placeholder) return e.placeholder;
    // previous sibling is the usual unlabelled-field pattern. Never climb to a
    // parent: a parent holding the whole form becomes every field's "name".
    const s = e.previousElementSibling;
    if (s && /^(LABEL|SPAN|P|DIV)$/.test(s.tagName)) {
      const t = (s.innerText || '').replace(/\\s+/g, ' ').trim();
      if (t && t.length < 90) return t;
    }
    return e.name || e.id || e.type || 'unidentified';
  };
  const empty = [];
  for (const e of document.querySelectorAll('input, select, textarea')) {
    if (!vis(e) || e.type === 'hidden') continue;
    const required = e.required || e.getAttribute('aria-required') === 'true';
    let bad = false;
    if (typeof e.checkValidity === 'function') bad = !e.checkValidity();
    else if (required) bad = !String(e.value || '').trim();
    if (!bad) continue;
    const kind = e.tagName === 'SELECT' ? 'select'
      : (e.type === 'checkbox' || e.type === 'radio') ? e.type
      : e.tagName === 'TEXTAREA' ? 'textarea' : 'text';
    empty.push({ kind: kind, label: label(e).slice(0, 60), id: e.id, name: e.name,
                 msg: (e.validationMessage || '').slice(0, 60) });
  }
  return empty;
}"""


def fill_report(what="form", timeout=PROBE_TIMEOUT):
    """Which required fields are still empty. Returns a list; empty means complete.

    Call this BEFORE clicking Next/Submit, so the answer costs zero failed submits
    and you get field names instead of a red banner. Never raises: a dead page
    returns [{"kind": "error", "label": ...}], so the caller can branch on it.
    """
    p = probe(timeout=timeout)
    if p["state"] != "ok":
        return [{"kind": "error", "label": p["state"], "name": p["reason"][:80]}]

    kind, resp = _bounded(
        lambda: call({"op": "eval", "js": _EMPTY_REQUIRED_JS}, timeout=timeout),
        timeout, "fill_report")
    if kind == "timeout":
        return [{"kind": "error", "label": "frozen", "name": "required-field read timed out"}]
    if kind == "error":
        return [{"kind": "error", "label": "dead", "name": str(resp)[:80]}]

    resp = resp or {}
    if not resp.get("ok"):
        return [{"kind": "error", "label": "eval failed", "name": str(resp.get("error"))[:80]}]

    missing = resp.get("result") or []
    if missing:
        log.warning("fill_report(%s): %d required field(s) empty:", what, len(missing))
        for m in missing:
            log.warning("  empty %-8s %-34s %s", m.get("kind"),
                        (m.get("label") or m.get("name") or "")[:34], m.get("msg", ""))
    else:
        log.info("fill_report(%s): all required fields valid", what)
    return missing


def wait_ready(predicate_js, timeout=6.0, what="ready"):
    """until() on a JS predicate — the condition-wait you actually want after a click."""
    return bool(until(lambda: call({"op": "eval", "js": predicate_js},
                                   timeout=timeout).get("result"),
                      timeout=timeout, interval=0.25, what=what))
