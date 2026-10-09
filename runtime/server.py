#!/usr/bin/env python3
"""runtime/server.py — ctl bridge :9000. TCP JSONL, one request per line.

Rebuilt 2026-10-02. The original lived in gitignored runtime/ and was lost.
Protocol recovered from call sites (core/ctl.py, core/verify.py, core/see.py,
apply/fill_gh_fast.py, apply/li_drive.py, find/sweep.py, core/test_hub.py).

Ops: status | navigate | eval | snap | keys | htype | hfill | fill | mouse_click | upload_cdp
Profile: runtime/session (persistent, LOGGED-IN sessions). Headed, 1280x800.
"""
import json
import os
import socket
import sys
import threading

HOST, PORT = "127.0.0.1", 9000
BASE = os.path.dirname(os.path.abspath(__file__))
PROFILE = os.path.join(BASE, "session")
LOGS = os.path.join(os.path.dirname(BASE), "logs")
os.makedirs(LOGS, exist_ok=True)

PAGE = None
CTX = None
LOCK = threading.Lock()


def _launch():
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
        )
    except Exception as e:  # fallback: plain playwright chromium
        print(f"[server] cloakbrowser launch failed ({e}); falling back to playwright chromium", flush=True)
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        CTX = pw.chromium.launch_persistent_context(
            user_data_dir=PROFILE, headless=False,
            viewport={"width": 1280, "height": 800})
    PAGE = CTX.pages[0] if CTX.pages else CTX.new_page()


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


def handle(cmd):
    op = cmd.get("op")
    try:
        if op == "status":
            return {"ok": True, "status": "ok", "url": PAGE.url}
        if op == "navigate":
            PAGE.goto(cmd["url"], wait_until="domcontentloaded", timeout=60000)
            return {"ok": True, "url": PAGE.url}
        if op == "eval":
            js = cmd["js"]
            # Playwright calls arrow-function strings and awaits promises.
            val = PAGE.evaluate(js)
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
        if op == "htype":
            PAGE.keyboard.type(str(cmd.get("value", "")), delay=30)
            return {"ok": True}
        if op == "hfill":
            loc = _locator(cmd)
            loc.click()
            PAGE.keyboard.press("Meta+A")
            PAGE.keyboard.type(str(cmd.get("value", "")), delay=30)
            return {"ok": True}
        if op == "fill":
            _locator(cmd).fill(str(cmd.get("value", "")))
            return {"ok": True}
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
