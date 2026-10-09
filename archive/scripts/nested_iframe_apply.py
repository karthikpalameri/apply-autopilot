#!/usr/bin/env python3
"""apply/netskope_agentic.py — Netskope Sr SDET (Greenhouse) via the full toolkit + agentic loop.
Loops until the confirmation page / submitted marker. ONE session, error-driven."""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browser import McpBrowser
from config.answers import A
from core.resume_secure import BEFORE_UPLOAD, POST as RESUME_POST, PICK as RESUME_PICK

JOB = "https://boards.greenhouse.io/<org>/jobs/<job-id>"
b = McpBrowser()
def snap(): return b.snapshot().get("text","")
def log(m): print(f"  [{time.strftime('%H:%M:%S')}] {m}", flush=True)

def click_leaf(want):
    mq = json.dumps(want.lower())
    r = b.eval_js("() => { const all=[...document.querySelectorAll('div, li, span')].filter(x=>x.offsetParent && x.children.length===0); const o=all.find(x=>(x.innerText||'').trim().toLowerCase()===" + mq + " && (x.innerText||'').trim().length<45); if(!o) return 'no'; o.click(); return 'yes'; }")
    time.sleep(1)
    return "yes" in str(r.get("result") if isinstance(r, dict) else r or "")

def combo_pick(btn_ref, want):
    b._call("browser_click", {"target": btn_ref}); time.sleep(6)
    if click_leaf(want): return True
    # fallback: DOM click + Enter-key search-combo
    b.eval_js("() => { const b=[...document.querySelectorAll('button, input')].find(x=>x.offsetParent && x.getAttribute('aria-haspopup')==='listbox'); if(b) b.click(); return 1; }")
    time.sleep(3)
    mq = json.dumps(want.lower())
    r = b.eval_js("() => { const i=document.activeElement; if(i && i.value!==undefined){ i.value=''; } return 1; }")
    b._call("browser_type", {"target": "input:focus", "text": want[:6], "slowly": True})
    time.sleep(1.5)
    b.eval_js("() => { const i=document.activeElement; if(i) i.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true})); return 1; }")
    time.sleep(1.5)
    return click_leaf(want)

def ocr_errors():
    b._call("browser_take_screenshot", {}); time.sleep(2)
    import subprocess
    pngs = os.popen("ls -t .playwright-mcp/*.png").read().split()
    return subprocess.run(["tesseract", pngs[0], "-"], capture_output=True, text=True).stdout if pngs else ""

def success():
    t = snap()
    return re.search(r'(Application received|Thank you for applying|Your application has been submitted|/confirmation)', t, re.I)

def main():
    RESUME_PICK()
    log("=== Netskope agentic (toolkit loop) ===")
    b.navigate(JOB); time.sleep(7)
    for loop in range(12):
        t = snap()
        m = success()
        if m or "/confirmation" in t:
            RESUME_POST();
            log("✅✅ CONFIRMED"); sys.exit(0)
        ap = re.search(r'button "Apply[^"]*" \[ref=(\w+)\]', t) or re.search(r'link "Apply[^"]*" \[ref=(\w+)\]', t)
        if ap:
            b._call("browser_click", {"target": ap.group(1)}); time.sleep(5)
            log("apply clicked"); continue
        # resume attach
        at = re.search(r'button "Attach" \[ref=(\w+)\]', t)
        if at:
            RESUME = BEFORE_UPLOAD()
            b._call("browser_click", {"target": at.group(1)}); time.sleep(2)
            b._call("browser_file_upload", {"paths": [RESUME]}); time.sleep(4)
            log("resume attached (md5 gate ✓)")
            continue
        # textboxes
        txts = re.findall(r'textbox "([^"]+)" \[ref=(\w+)\]', t)
        fills = {"Last Name": A["last"], "First Name": A["first"], "Preferred First Name": A["first"],
                 "Email": A["email"], "Phone": A["phone"].replace("+91 ","").replace(" ",""),
                 "LinkedIn": "https://" + A["linkedin"], "Website": "https://" + A["github"], "How did you hear": "LinkedIn"}
        for label, val in fills.items():
            rf = [r for l,r in txts if label.lower() in l.lower()]
            if rf:
                b._call("browser_type", {"target": rf[0], "text": val, "slowly": True}); time.sleep(0.3)
        # combos: Country/City/School/Degree via the toolkit
        t = snap()
        for lbl, want in [("Country", "India"), ("Location (City)", "Bengaluru")]:
            btn = re.search(rf'combobox "({re.escape(lbl)}[^"]*)" \[ref=(\w+)\]', t)
            if btn:
                combo_pick(btn.group(2), want); t = snap()
        # submit
        t = snap()
        sub = re.search(r'button "Submit application" \[ref=(\w+)\]', t)
        if sub:
            b._call("browser_click", {"target": sub.group(1)}); time.sleep(8)
            t = snap()
            m = success()
            if m or "/confirmation" in t:
                RESUME_POST();
                log("✅✅ CONFIRMED"); sys.exit(0)
            errs = re.findall(r'([A-Za-z][^"\n]{2,35})\[invalid\]', t)
            log("errors: " + str(errs[:5]))
        # OCR errors -> report
        err = ocr_errors()
        req = re.findall(r'([A-Za-z][^\n]{2,40}) is required', err)
        if req: log("OCR-required: " + str(list(set(req))[:5]))
        b._call("browser_take_screenshot", {}); time.sleep(1)
    print("❌ NOT CONFIRMED after 12 loops")
    sys.exit(1)

if __name__ == "__main__":
    main()
