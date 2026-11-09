#!/usr/bin/env python3
"""core/test_hub.py — hub health check (config, logger, ctl, MCP, sweep). Exit 0 = all green."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS, FAIL = [], []

def t(name, fn):
    try:
        note = fn()
        PASS.append(name)
        print(f"  ✅ {name}" + (f"  ({note})" if isinstance(note, str) else ""))
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
    from core.fetch import get_json      # single owner of ATS fetches
    d = get_json("https://boards-api.greenhouse.io/v1/boards/hackerrank/jobs")
    assert d and "jobs" in d

def test_company_identity():
    """The dedupe matcher must say YES to real renames and NO to a shared word.

    Regression guard for 2026-11-07: the old any-token-overlap rule made Qualys match
    RSA Security (word "security") and dextr ai match zilo ai (word "ai") — 360 false
    duplicate pairs, each a live role silently skipped.
    """
    from core.applied_ledger import co_key, company_matches
    same = [("AI Squared", "AISquared"), ("hpe", "Hewlett Packard Enterprise"),
            ("hp", "Hewlett Packard Enterprise"), ("Amazon", "Amazon Web Services"),
            ("Everpure (formerly Pure Storage)", "Pure Storage")]
    diff = [("Qualys", "RSA Security"), ("Qualys", "JetStream Security"),
            ("dextr ai", "zilo ai"), ("arista networks", "versa networks"),
            ("Hilabs", "Bosch Group")]
    for a, b in same:
        assert company_matches(co_key(a), co_key(b)), f"missed rename: {a} ~ {b}"
    for a, b in diff:
        assert not company_matches(co_key(a), co_key(b)), f"false duplicate: {a} ~ {b}"
    assert co_key("hpe") == co_key("Hewlett Packard Enterprise"), "alias not applied"
    return f"{len(same)} renames + {len(diff)} non-dupes"


def test_ledger_no_self_dupe():
    """No ledger company may match more than one distinct canonical key."""
    from core.applied_ledger import co_key, company_matches, iter_rows
    keys = sorted({k for k in (co_key(r.get("company", "")) for r in iter_rows()) if k})
    clash = [(a, b) for i, a in enumerate(keys) for b in keys[i + 1:]
             if company_matches(a, b) and not (set(a.split()) <= set(b.split())
                                               or set(b.split()) <= set(a.split()))]
    assert not clash, f"non-subset match survived: {clash[:3]}"
    return f"{len(keys)} keys clean"


def test_fetch_bounded():
    """fetch_many must honour its deadline on dead hosts (asyncio.run did not)."""
    import time
    from core.fetch import fetch_many
    t0 = time.time()
    fetch_many([f"https://nonexistent-{i}.invalid/x" for i in range(60)],
               timeout=2.0, deadline=3.0)
    took = time.time() - t0
    assert took < 6.0, f"deadline overrun: {took:.1f}s for a 3.0s deadline"
    return f"{took:.1f}s <= 3.0s deadline"


def test_freehire_paginates():
    """One page is 2% of the catalogue: search_paged must beat a single page."""
    from core.freehire_client import FreehireClient
    c = FreehireClient()
    one = c.search({"countries": "IN", "category": "qa", "limit": 100})
    many = c.search_paged({"countries": "IN", "category": "qa"}, pages=4, deadline=15)
    assert len(many) > len(one) * 1.5, f"pagination ineffective: {len(one)} -> {len(many)}"
    return f"{len(one)} -> {len(many)} postings"


print("=== JOB-APPLY-HUB HEALTH ===")
t("config (user.json + answers)", test_config)
t("logger", test_logger)
t("ctl bridge :9000", test_ctl)
t("MCP :3000", test_mcp)
t("browser abstraction", test_browser_pick)
t("prod_sweep API", test_sweep_dry)
t("company identity (dedupe)", test_company_identity)
t("ledger no false dupes", test_ledger_no_self_dupe)
t("fetch_many deadline", test_fetch_bounded)
t("freehire pagination", test_freehire_paginates)
print(f"\n{len(PASS)}/{len(PASS)+len(FAIL)} passed")
sys.exit(1 if FAIL else 0)
