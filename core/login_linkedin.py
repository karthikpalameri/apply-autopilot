#!/usr/bin/env python3
"""core/login_linkedin.py — LinkedIn login via MCP accessibility snapshots (target refs).
Failure => dumps DOM around the form so we SEE the mistake. Usage: .venv/bin/python core/login_linkedin.py"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browser import McpBrowser
from config.answers import A

b = McpBrowser()
b._rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name":"login","version":"0.1"}})

def snap(): return b.snapshot().get("text","")

def ref_of(snapshot, pattern):
    m = re.search(rf'({pattern})[^\[]*\[ref=(\w+)\]', snapshot)
    return m.group(2) if m else None

def dom_dump():
    """On failure: dump the login form DOM so we can see the real structure."""
    r = b._call("browser_evaluate", {"expression":
        "() => { const f=document.querySelector('form')||document.body; "
        "return f.innerHTML.replace(/</g,'\\n<').slice(0,2500); }"})
    content = (r.get("result") or {}).get("content") or []
    txt = "".join(c.get("text","") for c in content if isinstance(c, dict))
    open("logs/li_login_dom.txt","w").write(txt)
    print("📄 DOM dumped -> logs/li_login_dom.txt")
    return txt

def login(user, pwd):
    b.navigate("https://www.linkedin.com/login")
    time.sleep(5)
    t = snap()
    email_ref = ref_of(t, r'textbox "Email or phone"')
    pwd_ref = ref_of(t, r'textbox "Password"')
    sign_ref = ref_of(t, r'button "Sign in"')
    print(f"refs: email={email_ref} pwd={pwd_ref} sign={sign_ref}")
    if not (email_ref and pwd_ref and sign_ref):
        print("❌ refs missing — dumping DOM"); dom_dump(); return False
    b._call("browser_type", {"target": email_ref, "text": user}); time.sleep(0.4)
    b._call("browser_type", {"target": pwd_ref, "text": pwd}); time.sleep(0.4)
    b._call("browser_click", {"target": sign_ref})
    time.sleep(7)
    t2 = snap()
    ok = ("Feed" in t2 or "Messaging" in t2 or "global-nav" in t2 or "/feed" in t2)
    url = [l.strip() for l in t2.splitlines() if "Page URL" in l]
    print(f"{'✅ LOGGED IN' if ok else '❌ FAILED'} | {url}")
    if not ok:
        print(t2[:800]); dom_dump()
    return ok

if __name__ == "__main__":
    ok = login(A["email"], A.get("linkedin_pass",""))
    sys.exit(0 if ok else 1)
