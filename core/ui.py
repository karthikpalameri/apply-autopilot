#!/usr/bin/env python3
"""core/ui.py — the ONE owner of "talk to the page" and "wait for the page".

Three things every apply script needed, and had pasted:

1. ev(js)      — evaluate JS through the ctl socket. Was 4 private copies; three
                 identical and one silently missing the `or ""`, so callers got
                 None instead of "" and `re.search(x, None)` blew up differently.
2. text(browser) — the page's visible text. Was 5 identical `snap()` copies.
3. until(fn)   — poll for a condition instead of sleeping a guessed number of
                 seconds.

Why until() matters: the apply scripts held 141 seconds of fixed `time.sleep()`
between them, 14 of them inside loops, so the cost multiplied. `li_drive` alone
slept 1s + 5s per step x 10 steps, then 8s after submit — ~68s of pure waiting per
application, whether the page needed it or not.

A sleep is a guess. `until()` asks the page "ready yet?" every 250ms and returns
the moment it is, with the same ceiling as the old sleep. Fast pages finish fast,
slow pages still get the full timeout, and a timeout is logged instead of being
invisible.
"""
import json
import os
import time

from core.ctl import call
from core.logger import log

DEFAULT_TIMEOUT = 10.0
DEFAULT_INTERVAL = 0.25


def ev(js, timeout=None):
    """Evaluate `js` in the page and return its result as a string ('' on failure)."""
    cmd = {"op": "eval", "js": js}
    resp = call(cmd, timeout=timeout) if timeout else call(cmd)
    result = (resp or {}).get("result")
    return "" if result is None else result


def text(browser):
    """The page's visible text, via a browser instance from core.browser."""
    return (browser.snapshot() or {}).get("text", "") or ""


def until(fn, timeout=DEFAULT_TIMEOUT, interval=DEFAULT_INTERVAL, what="condition"):
    """Call fn() until it returns something truthy, or `timeout` seconds pass.

    Returns the first truthy value, else the last falsy result (so callers can
    keep using `or default`). fn() raising is treated as "not ready yet" — a page
    mid-render throws all the time and that is not an error.

    Use this instead of time.sleep(N). It is never slower than the sleep it
    replaces and is usually much faster.
    """
    start = time.monotonic()
    deadline = start + timeout
    last = None
    tries = 0
    while True:
        tries += 1
        try:
            last = fn()
        except Exception as e:
            log.debug("wait %s: attempt %d raised %s: %s", what, tries, e.__class__.__name__, e)
            last = None
        if last:
            log.debug("wait %s: ready after %.2fs (%d polls)", what, time.monotonic() - start, tries)
            return last
        if time.monotonic() >= deadline:
            log.warning("wait %s: not ready after %.1fs (%d polls)", what, timeout, tries)
            return last
        time.sleep(interval)


def until_change(read, before, timeout=DEFAULT_TIMEOUT, interval=DEFAULT_INTERVAL, what="change"):
    """Wait until read() stops equal to `before`.

    The common shape in the apply scripts: click Next, then sleep 5s hoping the
    step advanced. This waits for the step to actually advance instead.
    read() is called once per poll, not twice.
    """
    def changed():
        value = read()
        return value if value != before else None
    return until(changed, timeout=timeout, interval=interval, what=what)


# Typing one field character-by-character costs 30 ms per character. Measured on
# a 25-char value through the :9000 bridge: hfill 867 ms vs fill 9 ms — 96x.
# An 8-field Greenhouse form therefore costs ~7 s per application in typing alone.
# Keystroke timing means nothing to an ATS; it matters only on sites that
# fingerprint input, so the human path stays available behind PI_HUMAN_FILL=1.
HUMAN_FILL = os.environ.get("PI_HUMAN_FILL", "0") == "1"


def exists(selector, by="selector"):
    """True when the field is on the page right now (~1 ms).

    Worth 1 ms to avoid the alternative: a fill aimed at a selector that is not
    present costs a Playwright action timeout — 30s by default, measured — and
    returns ok=False with nothing in the output. Apply scripts carry field ids
    from one employer's form, so on any other form this is the common case.
    """
    if by != "selector":
        return True                      # only selectors can be checked cheaply
    js = ("() => { try { return !!document.querySelector(%s); } catch (e) { return false; } }"
          % json.dumps(selector))
    return bool(ev(js))


def fill(selector, value, human=None, by="selector"):
    """Fill one form field. Returns True when the bridge accepted it.

    human=True  -> hfill: click, select-all, type at 30 ms/char (stealth)
    human=False -> fill:  set the value in one call (~9 ms)
    """
    if not exists(selector, by=by):
        log.warning("fill(%s): not on this page — skipped (would have cost a "
                    "Playwright action timeout)", selector)
        return False
    op = "hfill" if (HUMAN_FILL if human is None else human) else "fill"
    r = call({"op": op, "by": by, "key": selector, "value": str(value)})
    if not (r or {}).get("ok"):
        log.warning("fill(%s) failed via %s: %s", selector, op, (r or {}).get("error", "no ok"))
    return bool((r or {}).get("ok"))


def select(selector, value, by="selector"):
    """Choose one or more options in a native <select>. Returns the selected values.

    Playwright matches a plain string against the option's VALUE or its LABEL, so
    both select("uk") and select("United Kingdom") pick the same option - measured,
    no per-call flag needed. It handles single AND multiple selects, fires the same
    events the browser would, and reports what it actually selected.

    The scripts used to hand-roll this with `s.value = x; s.dispatchEvent(new
    Event('change'))`, which is a no-op on a React-controlled select and never
    handled multi-select.
    """
    wanted = value if isinstance(value, list) else [value]
    wanted = [str(v) for v in wanted]
    r = call({"op": "select", "by": by, "key": selector, "value": wanted})
    if not (r or {}).get("ok"):
        log.warning("select(%s) failed: %s", selector, (r or {}).get("error", "no ok"))
        return []
    return (r or {}).get("selected") or []


def check(selector, state="checked", by="selector"):
    """Check or uncheck a checkbox/radio. IDEMPOTENT — unlike el.click().

    Measured on the fixture: clicking the same checkbox twice leaves it False, so a
    retry-driven loop silently unticks what it just ticked. Playwright's check() is a
    no-op when already in the requested state, which is what "ensure checked" means.
    """
    r = call({"op": "check", "by": by, "key": selector, "state": state})
    if not (r or {}).get("ok"):
        log.warning("check(%s, %s) failed: %s", selector, state, (r or {}).get("error", "no ok"))
        return False
    return bool((r or {}).get("checked"))


def upload(selector, path, by="selector"):
    """Attach a file and confirm the input actually holds it."""
    r = call({"op": "upload", "by": by, "key": selector, "path": path})
    if not (r or {}).get("ok"):
        log.warning("upload(%s) failed: %s", selector, (r or {}).get("error", "no ok"))
        return 0
    return (r or {}).get("files", 0)


def settle(seconds=0.3):
    """A short deliberate pause, for the rare case where polling cannot help
    (e.g. letting a CSS animation finish before a coordinate click)."""
    time.sleep(seconds)


# ---------------------------------------------------------------------------
# BOUNDED SCROLLING — the ONE owner of "walk a virtual list looking for X".
#
# Why this exists (measured 2026-11-05, this build's Chromium):
#   skills/recipes/workday.md:72  grid.scrollTop += 600 x40 + sleep(120) = 4.87 s
#   skills/recipes/linkedin.md:15 ul.scrollTop   += 2000 x14 + 250ms      = 3.53 s
#   skills/recipes/naukri.md:117  mouse.wheel x5 + 1.4 s                  = 7.03 s
# Every one of them scrolls to the END of the list on a miss, and the miss is the
# common case (wrong tenant, renamed option, list never virtualises). That is the
# "page scrolls up and down for many seconds" behaviour users reported.
#
# The old loops also scrolled the DOCUMENT when the target was inside a scroll
# CONTAINER, so the page jumped while the list never moved.
#
# Rules encoded here:
#   1. Stop the instant the predicate is true — never finish the loop for symmetry.
#   2. Stop at the container's real bottom; do not keep adding to scrollTop.
#   3. Stop when scrollTop stops changing (stuck/at-end) — one wasted step, not 40.
#   4. Cap the wall clock, not just the iteration count.
# ---------------------------------------------------------------------------
SCROLL_MAX_MS = 3000
SCROLL_STEP_PX = 600


def _scroll_probe(container_js, predicate_js, step=SCROLL_STEP_PX):
    """One step of a scroll walk, evaluated in-page. Returns a dict."""
    js = """(args) => {
        const [sel, pred, step] = args;
        const el = sel === null ? document.scrollingElement : document.querySelector(sel);
        if (!el) return {ok: false, reason: 'no-container'};
        const test = () => { try { return !!(new Function('return (' + pred + ')'))(); } catch (e) { return false; } };
        // Test where we ARE first, then move, then test again. Testing only before the
        // step skips the exact offset that satisfies the predicate (measured: target at
        // scrollTop 9000 was stepped over from 8400 straight to 9600 and never matched).
        if (test()) return {ok: true, hit: true, before: el.scrollTop, after: el.scrollTop,
                            max: el.scrollHeight - el.clientHeight, atEnd: false, stuck: false};
        const before = el.scrollTop;
        const max = el.scrollHeight - el.clientHeight;
        el.scrollTop = Math.min(before + step, max);
        const after = el.scrollTop;
        return {ok: true, hit: test(), before: before, after: after,
                max: max, atEnd: after >= max, stuck: after === before};
    }"""
    resp = call({"op": "eval", "js": js, "args": [container_js, predicate_js, step]})
    # call() wraps the page value in {"ok": True, "result": <value>}; unwrap it, or every
    # r.get("atEnd") below reads the envelope instead of the probe and is always None.
    if not (resp or {}).get("ok"):
        return {"ok": False, "reason": (resp or {}).get("error", "eval-failed")}
    inner = resp.get("result")
    return inner if isinstance(inner, dict) else {"ok": False, "reason": "bad-result"}


def scroll_until(predicate_js, container=None, max_ms=SCROLL_MAX_MS,
                 step=SCROLL_STEP_PX, settle_ms=120):
    """Scroll a container (or the document) until `predicate_js` is true.

    `predicate_js` is a JS *expression* evaluated after each step, e.g.
        "[...document.querySelectorAll('[role=option]')].some(o=>o.innerText.trim()==='India')"

    Returns True as soon as it is true. Returns False — fast — when the list is
    exhausted, stuck, or `max_ms` elapses. Never grinds the full iteration count on
    a miss, and never scrolls the wrong element.

    Use this instead of hand-writing `for (...scrollTop += N...)` loops.
    """
    import time as _t
    started = _t.monotonic()
    deadline = started + (max_ms / 1000.0)
    steps = 0
    while True:
        r = (_scroll_probe(container, predicate_js, step) or {})
        if not r.get("ok"):
            log.warning("scroll_until(%s): %s", container or "document", r.get("reason"))
            return False
        steps += 1
        if r.get("hit"):
            log.debug("scroll_until: found after %d step(s) in %d ms", steps,
                      int((_t.monotonic() - started) * 1000))
            return True
        # Stop conditions: end of list, no movement, or budget spent.
        if r.get("atEnd") or r.get("stuck"):
            log.debug("scroll_until: exhausted after %d step(s) (atEnd=%s stuck=%s)",
                      steps, r.get("atEnd"), r.get("stuck"))
            return False
        if _t.monotonic() >= deadline:
            log.warning("scroll_until: budget %d ms spent after %d step(s)", max_ms, steps)
            return False
        settle(settle_ms / 1000.0)
