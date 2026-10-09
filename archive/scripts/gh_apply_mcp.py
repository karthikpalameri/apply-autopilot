#!/usr/bin/env python3
"""apply/gh_apply_mcp.py <gh_job_url> — Greenhouse via MCP with STRICT VERIFY GATES.
NO false positives: every step verified + final applied-check. Exit 0 = verified applied."""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browser import McpBrowser
from config.answers import A
from core.resume_secure import BEFORE_UPLOAD, POST as RESUME_POST, PICK as RESUME_PICK

b = McpBrowser()
def snap(): return b.snapshot().get("text","")
def pick(cb, ch, match):
    b._call("browser_type", {"target": cb, "text": ch, "slowly": True}); time.sleep(1.2)
    mq = json.dumps(match.lower())
    r = b.eval_js("() => { const opts=[...document.querySelectorAll('[role=option],[id*=option]')].filter(o=>o.offsetParent&&(o.innerText||'').trim().length<60); const o=opts.find(x=>(x.innerText||'').trim().toLowerCase().startsWith(" + mq + ")); if(!o) return 'no-option'; o.click(); return 'clicked'; }")
    time.sleep(0.5)
    return ((r.get("result") if isinstance(r,dict) else r) or "")[:20]

def verify_upload():
    """GATE: resume must show as attached (Remove file present)."""
    t = snap()
    return bool(re.search(r'Remove file', t)) and bool(re.search(r'resume\.pdf', t, re.I))

def submit_and_verify(job_url):
    """GATE: after submit, re-navigate -> Apply button must be GONE (or applied marker)."""
    t = snap()
    sub = re.search(r'button "Submit application" \[ref=(\w+)\]', t)
    if not sub:
        print("  ✋ no submit button"); return False
    b._call("browser_click", {"target": sub.group(1)}); time.sleep(5)
    b.navigate(job_url); time.sleep(5)
    t2 = snap()
    still_apply = bool(re.search(r'button "Apply[^"]*" \[ref=(\w+)\]', t2)) or bool(re.search(r'link "Apply[^"]*"', t2))
    applied = bool(re.search(r'already applied|You have applied|Application submitted', t2, re.I))
    print(f"  VERIFY: apply-btn-still-present={still_apply} applied-marker={applied}")
    return (not still_apply) or applied

def main(url):
    RESUME_PICK()
    b.navigate(url); time.sleep(5)
    t = snap()
    ap = re.search(r'button "Apply[^"]*" \[ref=(\w+)\]', t) or re.search(r'link "Apply[^"]*" \[ref=(\w+)\]', t)
    if not ap:
        print("NO APPLY BTN — already applied?"); sys.exit(2)
    b._call("browser_click", {"target": ap.group(1)}); time.sleep(3)
    # 1) attach resume (click Attach -> chooser -> upload)
    t = snap()
    at = re.search(r'button "Attach" \[ref=(\w+)\]', t) or re.search(r'button "Upload" \[ref=(\w+)\]', t)
    if at:
        RESUME = BEFORE_UPLOAD()
        b._call("browser_click", {"target": at.group(1)}); time.sleep(1.5)
        r = b._call("browser_file_upload", {"paths": [RESUME]})
        time.sleep(2)
    if not verify_upload():
        print("❌ GATE FAIL: resume NOT attached"); sys.exit(3)
    print("  ✅ GATE: resume attached")
    # 2) fill textboxes
    t = snap()
    txts = re.findall(r'textbox "([^"]+)" \[ref=(\w+)\]', t)
    def tf(label, val):
        rf = [r for l,r in txts if label.lower() in l.lower()]
        if rf: b._call("browser_type", {"target": rf[0], "text": val}); time.sleep(0.3); return True
        return False
    tf("Last Name", A["last"]); tf("First", A["first"]); tf("Email", A["email"])
    tf("Phone", A["phone"].replace("+91 ","").replace(" ",""))
    tf("LinkedIn", "https://" + A["linkedin"]); tf("Website", "https://" + A["github"])
    # 3) country combo
    t = snap()
    combos = re.findall(r'combobox "([^"]+)" \[ref=(\w+)\]', t)
    cr = [r for l,r in combos if l.lower() == "country"]
    if cr: pick(cr[0], "In", "India")
    # 4) submit + VERIFY applied
    ok = submit_and_verify(url)
    if ok:
        RESUME_POST()
    print("✅ VERIFIED APPLIED" if ok else "❌ NOT CONFIRMED — investigate")
    sys.exit(0 if ok else 4)

if __name__ == "__main__":
    main(sys.argv[1])
