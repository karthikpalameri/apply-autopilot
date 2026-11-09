#!/usr/bin/env python3
"""runtime/server.py — ctl bridge :9000. TCP JSONL, one request per line.

Rebuilt 2026-10-02. The original lived in gitignored runtime/ and was lost.
Protocol recovered from call sites (core/ctl.py, core/verify.py, core/see.py,
apply/fill_gh_fast.py, apply/li_drive.py, find/sweep.py, core/test_hub.py).

Ops: status | probe | navigate | eval | snap | keys | htype | hfill | fill
     | select | check | upload | mouse_click | upload_cdp

`status` reports the bridge, not the page: it reads PAGE.url, which still answers
after the page is gone. `probe` is the page truth (dead / frozen / ok) and is what
core/page_guard.py calls. See skills/REFERENCE.md#page-guard for the rule.
Profile: runtime/session (persistent, LOGGED-IN sessions). Headed, 1280x800.
"""
import json
import os
import socket
import threading

HOST, PORT = "127.0.0.1", 9000
BASE = os.path.dirname(os.path.abspath(__file__))
PROFILE = os.path.join(BASE, "session")
LOGS = os.path.join(os.path.dirname(BASE), "logs")
os.makedirs(LOGS, exist_ok=True)

from typing import Any

PAGE: Any = None
CTX: Any = None
LOCK = threading.Lock()


# macOS kills an "idle" GUI app (App Nap / Automatic Termination) and takes the
# whole browser with it — measured 2026-11-07: the log shows
# `_kLSApplicationWouldBeTerminatedByTALKey=1` minutes before every dead page.
# These flags keep a headed, unfocused browser alive while we drive it.
KEEPALIVE_ARGS = [
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-background-timer-throttling",
    "--disable-features=CalculateNativeWinOcclusion,IntensiveWakeUpThrottling",
]


# The MCP exposes CDP per session at /cdp/<capability>/... — a plain port is not
# enough (probed 2026-11-07: /json/version on 9333 answers "CDP endpoint not
# found"). Set CTL_CDP_URL to the discovery URL the MCP advertises.
CDP_URL = os.environ.get("CTL_CDP_URL", "")


def _attach():
    """Attach to the MCP-owned browser instead of launching a second one.

    Two headed Chromiums meant two page states: fill_report checked one page while
    the MCP tools drove another (measured 2026-11-07). The MCP server owns the
    browser (scripts/start_mcp.sh --cdp-enabled); this bridge only attaches.

    Needs the capability-scoped discovery URL in CTL_CDP_URL; without it there is
    nothing to attach to and _launch_own() stays the default (unchanged behaviour).
    """
    if not CDP_URL:
        raise RuntimeError("CTL_CDP_URL unset — no MCP browser to attach to")
    from playwright.sync_api import sync_playwright
    global PAGE, CTX
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(CDP_URL, timeout=5000)
    CTX = browser.contexts[0] if browser.contexts else None
    if CTX is None:
        raise RuntimeError("CDP attached but exposed no context")
    return pw


def _launch():
    global PAGE, CTX
    try:
        _attach()
        print(f"[server] attached to MCP browser via CDP {CDP_URL}", flush=True)
    except Exception as e:
        print(f"[server] CDP attach failed ({e}); launching own browser", flush=True)
        _launch_own()
    PAGE = CTX.pages[0] if CTX.pages else CTX.new_page()
    _arm_dialog_handler()


def _launch_own():
    global PAGE, CTX
    try:
        from cloakbrowser import ensure_binary, launch_persistent_context
        print("[server] resolving CloakBrowser binary (first run may download)…", flush=True)
        ensure_binary()
        print("[server] launching CloakBrowser persistent context…", flush=True)
        CTX = launch_persistent_context(
            user_data_dir=PROFILE,
            headless=False,
            viewport={"width": 1280, "height": 800},
            args=KEEPALIVE_ARGS,
        )
    except Exception as e:  # fallback: plain playwright chromium
        print(f"[server] cloakbrowser launch failed ({e}); falling back to playwright chromium", flush=True)
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        CTX = pw.chromium.launch_persistent_context(
            user_data_dir=PROFILE, headless=False,
            viewport={"width": 1280, "height": 800}, args=KEEPALIVE_ARGS)


def _current_page():
    """The live page, re-adopting if the old one died.

    Keeping a dead PAGE around is what made every action fail while `status` said
    ok. Adopting the newest surviving page costs one comparison and keeps tabs
    working after a crash instead of needing a server restart.
    """
    global PAGE
    if PAGE is not None and not PAGE.is_closed():
        return PAGE
    alive = [p for p in CTX.pages if not p.is_closed()]
    PAGE = alive[-1] if alive else CTX.new_page()
    _arm_dialog_handler()
    return PAGE


DIALOGS: list = []


def _arm_dialog_handler():
    """Accept every JS dialog once, at launch, and remember its text.

    A pending alert/confirm blocks every later call with no error message. The
    handler must be registered before any navigation, or the first dialog hangs
    the run — that is why it lives here and not in each script.
    """
    def on_dialog(d):
        try:
            DIALOGS.append({"type": d.type, "message": (d.message or "")[:200]})
            d.accept()
        except Exception as e:  # noqa: BLE001 - a dismissed dialog is not fatal
            print(f"[server] dialog handler: {e}", flush=True)
    for page in CTX.pages:
        page.on("dialog", on_dialog)
    CTX.on("page", lambda p: p.on("dialog", on_dialog))


# Playwright's default action timeout is 30s. A fill/hfill aimed at a selector
# that is not on the page therefore costs THIRTY SECONDS before returning
# ok=False — measured. Apply scripts pass ids for one employer's form, so on any
# other form that is 30s of pure timeout per field, with nothing in the log.
ACTION_TIMEOUT_MS = int(os.environ.get("CTL_ACTION_TIMEOUT_MS", "5000"))


def _locator(spec):
    by, key = spec.get("by", "selector"), spec.get("key", "")
    if by == "name":
        return PAGE.locator(f'[name="{key}"]').first
    if by == "id":
        return PAGE.locator(f'#{key}').first
    return PAGE.locator(key).first


def _clean(v):
    try:
        json.dumps(v)
        return v
    except Exception:
        try:
            return str(v)
        except Exception:
            return None


FIELD_OPS = frozenset({"htype", "hfill", "fill", "select", "check", "upload"})


def _field_op(op, cmd):
    """Fill/choose/tick/attach one form control. Returns a response, or None if `op`
    is not a field operation.

    Split out of handle(): adding the three native controls pushed its branch count
    to 17, over the gate's limit of 12. These six share one concern — "set the value
    of one field and say what happened" — so they belong together.

    All of them pass ACTION_TIMEOUT_MS. Playwright's default is 30 s, and an apply
    script carries field ids from one employer's form, so a selector that is not on
    the page used to cost 30 s of silence per field.
    """
    if op == "htype":
        PAGE.keyboard.type(str(cmd.get("value", "")), delay=30)
        return {"ok": True}
    if op == "hfill":
        loc = _locator(cmd)
        loc.click(timeout=ACTION_TIMEOUT_MS)
        PAGE.keyboard.press("Meta+A")
        PAGE.keyboard.type(str(cmd.get("value", "")), delay=30)
        return {"ok": True}
    if op == "fill":
        _locator(cmd).fill(str(cmd.get("value", "")), timeout=ACTION_TIMEOUT_MS)
        return {"ok": True}
    # Native controls. These used to be hand-written JS at every call site
    # ("el.value = x; el.dispatchEvent(new Event('change'))"), which is a toggle
    # trap for checkboxes, a no-op on a React-controlled select, and cannot do
    # multi-select. Playwright's primitives auto-wait and report what they did.
    if op == "select":
        wanted = cmd.get("value")
        if isinstance(wanted, (str, dict)):
            wanted = [wanted]
        return {"ok": True,
                "selected": _locator(cmd).select_option(wanted, timeout=ACTION_TIMEOUT_MS)}
    if op == "check":
        loc = _locator(cmd)
        if cmd.get("state", "checked") == "unchecked":
            loc.uncheck(timeout=ACTION_TIMEOUT_MS)
        else:
            loc.check(timeout=ACTION_TIMEOUT_MS)
        return {"ok": True, "checked": loc.is_checked()}
    if op == "upload":
        loc = _locator(cmd) if cmd.get("key") else PAGE.locator("input[type=file]").first
        loc.set_input_files(cmd["path"], timeout=ACTION_TIMEOUT_MS)
        return {"ok": True, "path": cmd["path"], "files": loc.evaluate("e => e.files.length")}
    return None


def _probe():
    """Truthful page health. `status` answers from a cache, so it lies after a death.

    state=frozen is reported by the CLIENT (core/page_guard.probe) when this call
    does not answer at all; a native dialog blocks the JS thread, so the server is
    the wrong place to detect it.
    """
    try:
        page = _current_page()
        return {"ok": True, "state": "ok", "reason": "",
                "url": page.url, "dialogs": len(DIALOGS)}
    except Exception as e:  # noqa: BLE001 - the error IS the answer
        return {"ok": True, "state": "dead", "reason": str(e)[:160],
                "dialogs": len(DIALOGS)}


def handle(cmd):
    global PAGE
    op = cmd.get("op")
    try:
        PAGE = _current_page()
        if op == "status":
            return {"ok": True, "status": "ok", "url": PAGE.url}
        if op == "probe":
            return _probe()
        if op == "navigate":
            page = _current_page()
            page.goto(cmd["url"], wait_until="domcontentloaded", timeout=60000)
            return {"ok": True, "url": page.url}
        if op == "eval":
            js = cmd["js"]
            # Playwright calls arrow-function strings and awaits promises.
            # `args` lets one function carry parameters (core.ui.scroll_until);
            # omitted entirely when absent so existing zero-arg expressions are
            # unaffected.
            val = PAGE.evaluate(js, cmd["args"]) if "args" in cmd else PAGE.evaluate(js)
            return {"ok": True, "result": _clean(val)}
        if op == "snap":
            name = cmd.get("name", "view")
            full = bool(cmd.get("full", False))
            path = os.path.join(LOGS, f"{name}.png")
            PAGE.screenshot(path=path, full_page=full)
            return {"ok": True, "path": path}
        if op == "keys":
            PAGE.keyboard.press(cmd["keys"])
            return {"ok": True}
        field = _field_op(op, cmd)
        if field is not None:
            return field
        if op == "mouse_click":
            PAGE.mouse.click(int(cmd.get("x", 0)), int(cmd.get("y", 0)))
            return {"ok": True}
        if op == "upload_cdp":
            PAGE.locator('input[type=file]').first.set_input_files(cmd["path"])
            return {"ok": True, "path": cmd["path"]}
        return {"ok": False, "error": f"unknown op {op!r}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:500]}


def serve():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(4)
        print(f"[server] ctl bridge listening on {HOST}:{PORT}", flush=True)
        while True:
            conn, _ = srv.accept()
            with conn:
                buf = b""
                while not buf.endswith(b"\n"):
                    chunk = conn.recv(65536)
                    if not chunk:
                        break
                    buf += chunk
                    if len(buf) > 200_000_000:
                        break
                try:
                    cmd = json.loads(buf.decode() or "{}")
                except Exception:
                    cmd = {}
                with LOCK:
                    resp = handle(cmd)
                conn.sendall((json.dumps(resp, default=str) + "\n").encode())


if __name__ == "__main__":
    _launch()
    serve()
