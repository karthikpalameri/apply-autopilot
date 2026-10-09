#!/usr/bin/env python3
"""core/login_naukri.py — Naukri login via MCP snapshots (modal-scoped). DOM dump on failure."""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browser import McpBrowser
from config.answers import A

b = McpBrowser()
b._rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name":"login","version":"0.1"}})
def snap(): return b.snapshot().get("text","")
def ref_of(t, pattern):
    m = re.search(rf'({pattern})[^\[]*\[ref=(\w+)\]', t)
    return m.group(2) if m else None

def dom_dump(tag):
    r = b._call("browser_evaluate", {"expression":
        "() => { const m=document.querySelector('[class*=modal]'); const f=(m||document).innerHTML; return f.replace(/</g,'\\n<').slice(0,3000); }"})
    content = (r.get("result") or {}).get("content") or []
    txt = "".join(c.get("text","") for c in content if isinstance(c, dict))
    open(f"logs/naukri_{tag}.txt","w").write(txt)
    print(f"📄 DOM dumped -> logs/naukri_{tag}.txt")

def login(user, pwd):
    b.navigate("https://www.naukri.com/qa-jobs-in-bangalore")
    time.sleep(5)
    t = snap()
    print("logged in already?" , "/login" not in b.snapshot().get("text","")[:200] or "LOGIN" in t[:200])
    # click Login button (header)
    login_ref = ref_of(t, r'button "Login"')
    link_ref = ref_of(t, r'link "Login"')
    print("login btn refs:", login_ref, link_ref)
    target = login_ref or link_ref
    if not target:
        print("no login control — check if already logged in"); dom_dump("nologin"); return None
    b._call("browser_click", {"target": target})
    time.sleep(3)
    t2 = snap()
    # find email + password + submit INSIDE modal (all visible textboxes/buttons)
    email_ref = ref_of(t2, r'textbox.*(mail|phone|username)')
    pwd_ref = ref_of(t2, r'textbox "Password"')
    if not email_ref or not pwd_ref:
        print("❌ no email/pwd in snapshot — dumping DOM")
        print(t2[:900]); dom_dump("noform"); return False
    b._call("browser_type", {"target": email_ref, "text": user}); time.sleep(0.4)
    b._call("browser_type", {"target": pwd_ref, "text": pwd}); time.sleep(0.4)
    # submit: any button containing Login in the modal area
    t3 = snap()
    submit_ref = ref_of(t3, r'button "Login"')
    if not submit_ref:
        submit_ref = ref_of(t3, r'button "Login with password"')
    print("submit ref:", submit_ref)
    if submit_ref:
        b._call("browser_click", {"target": submit_ref}); time.sleep(7)
    t4 = snap()
    logged = "LoginRegister" not in t4
    url = [l.strip() for l in t4.splitlines() if "Page URL" in l]
    print(f"{'✅ NAUKRI LOGGED IN' if logged else '❌ FAILED'} | {url}")
    if not logged:
        print(t4[:600]); dom_dump("fail")
    return logged

if __name__ == "__main__":
    ok = login(A["email"], A.get("linkedin_pass",""))
    sys.exit(0 if ok else 1)
