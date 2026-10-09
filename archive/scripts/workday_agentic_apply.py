#!/usr/bin/env python3
"""workday_agentic_apply.py — Workday apply, AGENTIC LOOP until positive confirmation.
v2: verify EVERY target before typing; never type into buttons; loop until 'submitted/confirmation'.
Run: .venv/bin/python archive/scripts/workday_agentic_apply.py"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browser import McpBrowser
from core.resume_secure import BEFORE_UPLOAD, POST as RESUME_POST, PICK as RESUME_PICK
from config.answers import A

EMAIL = A["email"]
PW = os.environ.get("ATS_PW", "")  # set in your shell/keychain; never hardcode a password
JOB_URL = "<workday-job-url>/apply/autofillWithResume?source=LinkedIn"

b = McpBrowser()
def snap(): return b.snapshot().get("text","")
def log(m): print(f"  [{time.strftime('%H:%M:%S')}] {m}", flush=True)

def verify_input(sel):
    """GATE: confirm target exists (retry for late-render) before ANY typing."""
    for _ in range(4):
        r = b.eval_js("() => { const i=document.querySelector('" + sel + "'); return i ? JSON.stringify({tag: i.tagName, type: i.type, val: (i.value||'').slice(0,10)}) : 'missing'; }")
        res = r.get("result") if isinstance(r, dict) else r
        if res and 'missing' not in str(res): return res
        time.sleep(1.5)
    return res

def fill_text(sel, val):
    chk = verify_input(sel)
    if not chk or "missing" in str(chk):
        log(f"  ✋ SKIP (no target): {sel}"); return False
    b.eval_js("() => { const i=document.querySelector('" + sel + "'); i.focus(); i.value=''; }")
    time.sleep(0.2)
    b._call("browser_type", {"target": sel, "text": val, "slowly": True})
    time.sleep(0.5)
    got = verify_input(sel)
    ok = val[:8].lower() in str(got).lower()
    log(f"  {'✓' if ok else '✗'} {sel} -> {val[:15]} ({str(got)[:60]})")
    return ok

def combo_pick(btn_ref, want):
    """Open a combobox via its BUTTON (no typing) + click option by exact text (scroll menu as needed)."""
    b._call("browser_click", {"target": btn_ref}); time.sleep(1.5)
    mq = json.dumps(want.lower())
    r = b.eval_js("() => { const o=[...document.querySelectorAll('[role=option], li, div')].find(x=>x.offsetParent && (x.innerText||'').trim().toLowerCase()===" + mq + " && (x.innerText||'').trim().length<40); if(!o) return 'not-found'; o.scrollIntoView({block:'center'}); setTimeout(()=>{o.click();}, 300); return 'clicked'; }")
    time.sleep(1.2)
    res = (r.get("result") if isinstance(r, dict) else r or "")
    if "clicked" in str(res):
        return True
    # fallback: scroll any open menu through options
    r2 = b.eval_js("() => { const menus=[...document.querySelectorAll('[role=listbox], ul, [class*=menu]')].filter(m=>m.offsetParent&&m.scrollHeight>m.clientHeight); for (const m of menus) { for (let i=0;i<40;i++){ m.scrollTop+=120; const o=[...m.querySelectorAll('[role=option], li')].find(x=>(x.innerText||'').trim().toLowerCase()===" + mq + "); if(o){ setTimeout(()=>o.click(),200); return 'clicked-after-scroll'; } } } return 'still-not-found'; }")
    time.sleep(1.2)
    res2 = (r2.get("result") if isinstance(r2, dict) else r2 or "")
    return "clicked" in str(res2)

def success_marker(t):
    return re.search(r'(submitted|application received|thank you|you have applied|confirmation|successfully applied|application complete|we have received)', t, re.I)

def ensure_login():
    b.navigate("https://<tenant>.myworkdayjobs.com/<site>/login"); time.sleep(6)
    t = snap()
    em = re.search(r'textbox "Email Address" \[ref=(\w+)\]', t)
    pw = re.search(r'textbox "Password" \[ref=(\w+)\]', t)
    if not (em and pw):
        log("no signin form (may be logged in)"); return
    b._call("browser_type", {"target": em.group(1), "text": EMAIL, "slowly": True}); time.sleep(0.4)
    b._call("browser_type", {"target": pw.group(1), "text": PW, "slowly": True}); time.sleep(0.4)
    si = re.search(r'button "Sign In" \[ref=(\w+)\]', t)
    if si: b._call("browser_click", {"target": si.group(1)})
    time.sleep(6)
    log("sign-in done")

def main():
    log("=== an employer agentic (loop until confirmed) ===")
    ensure_login()
    b.navigate(JOB_URL); time.sleep(6)
    for loop in range(10):
        t = snap()
        m = success_marker(t)
        if m:
            log("✅✅ CONFIRMED: " + m.group(0)); RESUME_POST(); sys.exit(0)
        stepm = re.search(r'(current|completed) step (\d+) of \d+', t)
        stepn = int(stepm.group(2)) if stepm else 0
        if stepm and stepm.group(1) == 'completed': stepn += 1
        step = stepm and type('s',(),{'group': lambda self,n: str(stepn) if n==1 else stepm.group(n)})() if stepm else None
        log(f"--- loop {loop+1}: step {step.group(1) if step else '?'} ---")
        # STEP 1: autofill
        if step and step.group(1) == "1":
            sel = re.search(r'button "Select file" \[ref=(\w+)\]', t)
            if sel:
                RESUME = BEFORE_UPLOAD()
                b._call("browser_click", {"target": sel.group(1)}); time.sleep(2)
                b._call("browser_file_upload", {"paths": [RESUME]}); time.sleep(5)
                log("resume uploaded (md5 gate ✓)")
            cont = re.search(r'button "Continue" \[ref=(\w+)\]', t)
            if cont: b._call("browser_click", {"target": cont.group(1)}); time.sleep(5)
        # STEP 2: My Information
        elif step and step.group(1) == "2":
            fill_text("input[name='legalName--firstName']", A["first"])
            fill_text("input[name='legalName--lastName']", A["last"])
            t = snap()
            for lbl, want in [("Prefix", "Mr."), ("State", "Karnataka"), ("Device Type", "Mobile")]:
                btn = re.search(rf'button "({re.escape(lbl)}[^"]*Required[^"]*)" \[ref=(\w+)\]', t)
                if btn:
                    ok = combo_pick(btn.group(2), want)
                    log(f"{lbl} -> {want}: {'✓' if ok else '✗'}")
                    t = snap()
            sc = re.search(r'button "Save and Continue" \[ref=(\w+)\]', t)
            if sc: b._call("browser_click", {"target": sc.group(1)}); time.sleep(5)
        # STEP 3: Experience
        elif step and step.group(1) == "3":
            c = re.search(r'button "Continue" \[ref=(\w+)\]', t) or re.search(r'button "Save and Continue" \[ref=(\w+)\]', t)
            if c: b._call("browser_click", {"target": c.group(1)}); time.sleep(5)
        # STEP 4: Questions
        elif step and step.group(1) == "4":
            r = b.eval_js("""() => { const out=[]; for (const i of document.querySelectorAll('input[type=text], textarea')) { const l=i.getAttribute('aria-label')||i.getAttribute('data-automation-id')||''; if (i.offsetParent && l && !(i.value||'').trim()) out.push({sel: "input[aria-label='"+l+"']", l: l.slice(0,30)}); } return JSON.stringify(out.slice(0,8)); }""")
            for f in json.loads(r.get("result") if isinstance(r, dict) else r or "[]"):
                val = str(A["expected_ctc_lpa"]) if re.search(r'salary|ctc', f["l"], re.I) else ("0" if "notice" in f["l"].lower() else (str(A["years"]) if "year" in f["l"].lower() else "I don't wish to answer"))
                fill_text(f["sel"], val)
            c = re.search(r'button "Continue" \[ref=(\w+)\]', t) or re.search(r'button "Save and Continue" \[ref=(\w+)\]', t)
            if c: b._call("browser_click", {"target": c.group(1)}); time.sleep(5)
        # STEP 5: Voluntary
        elif step and step.group(1) == "5":
            c = re.search(r'button "Continue" \[ref=(\w+)\]', t) or re.search(r'button "Save and Continue" \[ref=(\w+)\]', t)
            if c: b._call("browser_click", {"target": c.group(1)}); time.sleep(5)
        # STEP 6 / Submit
        else:
            sub = re.search(r'button "Submit[^"]*" \[ref=(\w+)\]', t)
            if sub:
                b._call("browser_click", {"target": sub.group(1)}); time.sleep(8)
                t = snap()
                m = success_marker(t)
                if m:
                    log("✅✅ CONFIRMED: " + m.group(0)); RESUME_POST(); sys.exit(0)
            b._call("browser_take_screenshot", {}); time.sleep(1)
    t = snap()
    m = success_marker(t)
    if m:
        print("✅✅ CONFIRMED: " + m.group(0)); RESUME_POST(); sys.exit(0)
    open("logs/ats_final_dom.txt","w").write(snap()[-3000:])
    print("❌ NOT CONFIRMED after 10 loops — final state dumped to logs/ats_final_dom.txt")
    sys.exit(1)

if __name__ == "__main__":
    main()
