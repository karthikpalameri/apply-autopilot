#!/usr/bin/env python3
"""apply/acme-workday_resume.py — continue the SAVED AcmeWorkday application (5-step flow, account remembers).
Loops: fix errors (OCR-driven) -> Save & Continue -> Submit -> verify confirmation. ONE session."""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browser import McpBrowser

JOB = "https://<tenant>.myworkdayjobs.com/en-US/AcmeWorkday/job/Bengaluru/Senior-Software-Development-Engineer-Test-I_JR10379/apply?source=LinkedIn"
b = McpBrowser()
def snap(): return b.snapshot().get("text","")
def log(m): print(f"  [{time.strftime('%H:%M:%S')}] {m}", flush=True)

def click_leaf(want):
    mq = json.dumps(want.lower())
    r = b.eval_js("() => { const all=[...document.querySelectorAll('div, li, span')].filter(x=>x.offsetParent && x.children.length===0); const o=all.find(x=>(x.innerText||'').trim().toLowerCase()===" + mq + " && (x.innerText||'').trim().length<45); if(!o) return 'no'; o.click(); return 'yes'; }")
    time.sleep(1)
    return "yes" in str(r.get("result") if isinstance(r, dict) else r or "")

def combo_by_label(lbl, want):
    t = snap()
    btn = re.search(rf'button "([^"]*{re.escape(lbl)}[^"]*Required[^"]*)" \[ref=(\w+)\]', t)
    if btn:
        b._call("browser_click", {"target": btn.group(2)}); time.sleep(6)
        return click_leaf(want)
    return False

def ocr_errors():
    b._call("browser_take_screenshot", {}); time.sleep(2)
    import subprocess
    png = sorted(os.popen("ls -t .playwright-mcp/*.png").read().split())[0]
    txt = subprocess.run(["tesseract", png, "-"], capture_output=True, text=True).stdout
    return txt

def save_continue():
    r = b.eval_js("""() => { const btn=[...document.querySelectorAll('button')].find(x=>/Save and Continue/i.test(x.innerText||'')); if(!btn) return 'no-btn'; btn.scrollIntoView({block:'center'}); setTimeout(()=>btn.click(),250); return 'clicked'; }""")
    time.sleep(8)
    return (r.get("result") if isinstance(r, dict) else r or "")

def main():
    log("=== AcmeWorkday resume (saved app, loop until submitted) ===")
    b.navigate(JOB); time.sleep(8)
    for loop in range(20):
        t = snap()
        m_ok = re.search(r'(submitted|thank you[^.]*|confirmation[^.]*|application complete|you have applied)', t, re.I)
        if m_ok:
            log("✅✅ CONFIRMED: " + m_ok.group(0)); sys.exit(0)
        m = re.search(r'(current|completed) step (\d+) of (\d+)', t)
        st = int(m.group(2)) if m else 0
        log(f"loop {loop+1}: step {st} of {m.group(3) if m else '?'}")
        # FIX known things per step via OCR errors
        if st == 1:  # My Information
            combo_by_label("Country", "India"); combo_by_label("State", "Karnātaka")
            combo_by_label("Prefix", "Mr."); combo_by_label("Device Type", "Mobile")
            save_continue()
        elif st == 2:  # Experience
            save_continue()
        elif st == 3:  # Questions
            save_continue()
        elif st == 4:  # Voluntary
            g = re.search(r'button "Gender Select One Required" \[ref=(\w+)\]', snap())
            if g:
                b._call("browser_click", {"target": g.group(1)}); time.sleep(6); click_leaf("Male")
            save_continue()
        elif st == 5 or "Submit" in t:  # Review / Submit
            sub = re.search(r'button "Submit[^"]*" \[ref=(\w+)\]', t)
            if sub:
                b._call("browser_click", {"target": sub.group(1)}); time.sleep(12)
                t = snap()
                if re.search(r'(submitted|thank you|confirmation|you have applied)', t, re.I):
                    log("✅✅ CONFIRMED SUBMITTED"); sys.exit(0)
            else:
                save_continue()
        # after Save, if errors remain -> OCR them
        time.sleep(1)
        err = ocr_errors()
        errs = re.findall(r'Error - ([A-Za-z][^\n]{3,40})', err)
        if errs:
            log("errors: " + str(errs[:5]))
            for e in errs:
                e2 = e.strip()
                if re.search(r'gender|citizen|birth|date|terms|acknowledge|declar', e2, re.I):
                    if "citizen" in e2.lower():
                        t = snap()
                        cit = re.search(r'button "([^"]*Citizenship[^"]*)" \[ref=(\w+)\]', t)
                        if cit:
                            b._call("browser_click", {"target": cit.group(2)}); time.sleep(6)
                            r = b.eval_js("() => { const o=[...document.querySelectorAll('div[data-automation-id=menuItem]')].find(x=>x.offsetParent && /Indian Citizen/i.test(x.innerText||'')); if(!o) return 'no'; const cb=o.querySelector('span')||o; cb.click(); return 'yes'; }")
                            log("citizenship: " + str(r.get("result") if isinstance(r, dict) else r))
                    if "birth" in e2.lower() or "date" in e2.lower():
                        # DOB <YOUR_DOB>
                        for f, v in [("Month", "04"), ("Day", "15"), ("Year", "1994")]:
                            i = re.search(rf'personalInfoPerson--dateOfBirth-dateSection{f}-input', snap())
                            if i:
                                b.eval_js("() => { const i=document.getElementById('" + i.group(0) + "'); if(i){ i.focus(); i.value=''; } return 1; }")
                                b._call("browser_type", {"target": "#" + i.group(0), "text": v, "slowly": True}); time.sleep(0.3)
                    if "acknowledge" in e2.lower() or "terms" in e2.lower() or "declar" in e2.lower():
                        b.eval_js("() => { const c=[...document.querySelectorAll('input[type=checkbox]')].find(x=>x.offsetParent && /understand and acknowledge|declar/i.test(x.closest('div')?.innerText||'')); if(c && !c.checked) c.click(); return 1; }")
        b._call("browser_take_screenshot", {}); time.sleep(1)
    print("❌ NOT CONFIRMED after 20 loops")
    sys.exit(1)

if __name__ == "__main__":
    main()
