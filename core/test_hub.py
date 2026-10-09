#!/usr/bin/env python3
"""core/test_hub.py — hub health check (config, logger, ctl, MCP, sweep). Exit 0 = all green."""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS, FAIL = [], []

def t(name, fn):
    try:
        fn(); PASS.append(name); print(f"  ✅ {name}")
    except Exception as e:
        FAIL.append(name); print(f"  ❌ {name}: {e}")

def test_config():
    from config.answers import A
    assert A["email"], "user.json not configured — run python setup.py"
    assert "LPA" in A["expected"], "expected CTC missing"

def test_logger():
    from core.logger import log
    log.info("test_hub logger ok")
    assert os.path.exists("logs/app.log")

def test_ctl():
    import socket, json as j
    s = socket.create_connection(("127.0.0.1", 9000), timeout=2)
    s.sendall((j.dumps({"op": "eval", "js": "() => 1+1"}) + "\n").encode())
    r = j.loads(s.recv(4096).decode()); s.close()
    assert r.get("result") == 2, r

def test_mcp():
    import urllib.request
    h = json.loads(urllib.request.urlopen("http://127.0.0.1:3000/healthz", timeout=2).read())
    assert h.get("status") == "ok", h

def test_browser_pick():
    from core.browser import pick, McpBrowser, CtlBrowser
    b = pick()
    assert isinstance(b, (McpBrowser, CtlBrowser))

def test_sweep_dry():
    import find.prod_sweep as ps
    d = ps.get("https://boards-api.greenhouse.io/v1/boards/hackerrank/jobs")
    assert d and "jobs" in d

print("=== JOB-APPLY-HUB HEALTH ===")
t("config (user.json + answers)", test_config)
t("logger", test_logger)
t("ctl bridge :9000", test_ctl)
t("MCP :3000", test_mcp)
t("browser abstraction", test_browser_pick)
t("prod_sweep API", test_sweep_dry)
print(f"\n{PASS.__len__() if False else len(PASS)}/{len(PASS)+len(FAIL)} passed")
sys.exit(1 if FAIL else 0)
