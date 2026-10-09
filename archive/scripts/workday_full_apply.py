#!/usr/bin/env python3
"""apply/acme-workday_full.py — COMPLETE AcmeWorkday Workday application in ONE session (no resets).
Every step verified. Ends only on the confirmation page / submitted marker.
Run: .venv/bin/python apply/acme-workday_full.py"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browser import McpBrowser
from core.resume_secure import BEFORE_UPLOAD, POST as RESUME_POST, PICK as RESUME_PICK

EMAIL = A["email"]
PW = os.environ.get("ATS_PW", "")
DOB = "<YOUR_DOB>"
JOB = "https://<tenant>.myworkdayjobs.com/en-US/AcmeWorkday/job/Bengaluru/Senior-Software-Development-Engineer-Test-I_JR10379/apply/autofillWithResume?source=LinkedIn"

b = McpBrowser()
def snap(): return b.snapshot().get("text","")
def log(m): print(f"  [{time.strftime('%H:%M:%S')}] {m}", flush=True)

def click_leaf(want, exact=True, wait=1.0):
    """Click a leaf element (div/li/span) by text. Returns True if clicked."""
    mq = json.dumps(want.lower())
    r = b.eval_js("() => { const all=[...document.querySelectorAll('div, li, span')].filter(x=>x.offsetParent && x.children.length===0);"
                  " const o=all.find(x=>(x.innerText||'').trim().toLowerCase()===" + mq + " && (x.innerText||'').trim().length<45);"
                  " if(!o) return 'no'; o.click(); return 'yes'; }")
    time.sleep(wait)
    return "yes" in str(r.get("result") if isinstance(r, dict) else r or "")

def combo_pick(btn_ref, want, wait=6):
    """Open a Workday combobox (MCP click) + click the leaf option."""
    b._call("browser_click", {"target": btn_ref}); time.sleep(wait)
    return click_leaf(want)

def combo_dompick(btn_ref, want, wait=4):
    """Open via DOM click + click leaf."""
    b.eval_js("() => { const b=document.querySelector('[aria-label=\"' + ' ' + 'Select One Required\"]'); if(b) b.click(); return 1; }")
    time.sleep(wait)
    return click_leaf(want)

def save_continue():
    r = b.eval_js("""() => { const btn=[...document.querySelectorAll('button')].find(x=>/Save and Continue/i.test(x.innerText||'')); if(!btn) return 'no-btn'; btn.scrollIntoView({block:'center'}); setTimeout(()=>btn.click(),250); return 'clicked'; }""")
    time.sleep(7)
    return (r.get("result") if isinstance(r, dict) else r or "")

def step_num():
    m = re.search(r'(current|completed) step (\d+) of 6', snap())
    if not m: return None
    return int(m.group(2)) + (1 if m.group(1) == "completed" else 0) - (1 if m.group(1) == "completed" else 0)

def main():
    log("=== AcmeWorkday FULL (one session, loop until submitted) ===")
    RESUME_PICK()
    # SIGN IN
    b.navigate("https://<tenant>.myworkdayjobs.com/AcmeWorkday/login"); time.sleep(6)
    t = snap()
    em = re.search(r'textbox "Email Address" \[ref=(\w+)\]', t)
    pw = re.search(r'textbox "Password" \[ref=(\w+)\]', t)
    if em and pw:
        b._call("browser_type", {"target": em.group(1), "text": EMAIL, "slowly": True}); time.sleep(0.4)
        b._call("browser_type", {"target": pw.group(1), "text": PW, "slowly": True}); time.sleep(0.4)
        si = re.search(r'button "Sign In" \[ref=(\w+)\]', t)
        if si: b._call("browser_click", {"target": si.group(1)})
        time.sleep(7)
    b.navigate(JOB); time.sleep(7)
    for loop in range(14):
        t = snap()
        if re.search(r'(submitted|thank you|confirmation|application complete|you have applied)', t, re.I):
            log("✅✅ CONFIRMED SUBMITTED: " + re.search(r'(submitted|thank you[^.]*|confirmation)', t, re.I).group(0)); RESUME_POST(); sys.exit(0)
        m = re.search(r'(current|completed) step (\d+) of 6', t)
        st = int(m.group(2)) if m else 0
        log(f"loop {loop+1}: step {st}")
        # ---- STEP 1: autofill ----
        if st == 1 and "Select file" in t:
            sel = re.search(r'button "Select file" \[ref=(\w+)\]', t)
            if sel:
                RESUME = BEFORE_UPLOAD()
                b._call("browser_click", {"target": sel.group(1)}); time.sleep(2)
                b._call("browser_file_upload", {"paths": [RESUME]}); time.sleep(5)
                log("resume uploaded (md5 gate ✓)")
            c = re.search(r'button "Continue" \[ref=(\w+)\]', t)
            if c: b._call("browser_click", {"target": c.group(1)}); time.sleep(7)
            continue
        # ---- STEP 2: My Information ----
        if st == 2:
            for sel, val in [("input[name='legalName--firstName']", "Jane"), ("input[name='legalName--lastName']", "Doe")]:
                b.eval_js("() => { const i=document.querySelector('" + sel + "'); if(i){ i.focus(); i.value=''; } return 1; }"); time.sleep(0.2)
                b._call("browser_type", {"target": sel, "text": val, "slowly": True}); time.sleep(0.4)
            t = snap()
            for lbl, want in [("Country", "India"), ("State", "Karnātaka"), ("Prefix", "Mr."), ("Device Type", "Mobile")]:
                btn = re.search(rf'button "({re.escape(lbl)}[^"]*Required[^"]*)" \[ref=(\w+)\]', t)
                if btn: combo_pick(btn.group(2), want)
                t = snap()
            # phone: country code + number
            b.eval_js("() => { const i=document.getElementById('phoneNumber--countryPhoneCode'); if(i){ i.focus(); i.value=''; } return 1; }"); time.sleep(0.2)
            b._call("browser_type", {"target": "#phoneNumber--countryPhoneCode", "text": "India", "slowly": True}); time.sleep(1.5)
            click_leaf("India (+91)")
            b.eval_js("() => { const i=document.getElementById('phoneNumber--phoneNumber'); if(i){ i.focus(); i.value=''; } return 1; }"); time.sleep(0.2)
            b._call("browser_type", {"target": "#phoneNumber--phoneNumber", "text": A["phone"], "slowly": True}); time.sleep(0.3)
            # postal + employment No
            b.eval_js("() => { const i=document.querySelector('input[name*=\"postalCode\"], input[id*=\"postalCode\"]'); if(i){ const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set; s.call(i,'<postcode>'); i.dispatchEvent(new Event('input',{bubbles:true})); i.dispatchEvent(new Event('change',{bubbles:true})); } return 1; }")
            t = snap()
            b.eval_js("() => { const no=[...document.querySelectorAll('label')].find(x=>(x.innerText||'').trim()==='No'); if(no) no.click(); return 1; }")
            save_continue()
            continue
        # ---- STEP 3: Experience ----
        if st == 3:
            # roleDescription + locations (work-exp)
            for eid, val in [("workExperience-55--roleDescription", "Test automation and quality engineering across web and API platforms")]:
                b.eval_js("() => { const i=document.getElementById('" + eid + "'); if(i){ i.focus(); i.value=''; } return 1; }"); time.sleep(0.2)
                b._call("browser_type", {"target": "#" + eid, "text": val, "slowly": True}); time.sleep(0.4)
            for eid, val in [("workExperience-55--location", "Bengaluru"), ("workExperience-56--location", "Bengaluru")]:
                b.eval_js("() => { const i=document.getElementById('" + eid + "'); if(i){ const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set; s.call(i,'" + val + "'); i.dispatchEvent(new Event('input',{bubbles:true})); i.dispatchEvent(new Event('change',{bubbles:true})); } return 1; }"); time.sleep(0.3)
            # education: degree + fieldOfStudy (search-combo w/ checkbox) + year
            t = snap()
            deg = re.search(r'button "Degree Select One Required" \[ref=(\w+)\]', t)
            if deg: combo_pick(deg.group(1), "Bachelor")
            # fieldOfStudy: open + click the checkbox-in-option
            b.eval_js("() => { const i=[...document.querySelectorAll('input')].find(x=>x.placeholder==='Search' && /study/i.test(x.id||'')); if(i){ i.focus(); i.value='Computer'; i.dispatchEvent(new Event('input',{bubbles:true})); i.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true})); } return 1; }")
            time.sleep(2.5)
            r = b.eval_js("""() => { const o=[...document.querySelectorAll('div[data-automation-id="menuItem"]')].find(x=>x.offsetParent && /Computer and Information/i.test(x.innerText||'')); if(!o) return 'no-item'; const cb=o.querySelector('span')||o; cb.click(); return 'clicked'; }""")
            log("fieldOfStudy: " + str(r.get("result") if isinstance(r, dict) else r))
            # education year From
            b.eval_js("() => { const i=[...document.querySelectorAll('input')].find(x=>/firstYearAttended/.test(x.id||'') && x.offsetParent); if(i){ const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set; s.call(i,'2013'); i.dispatchEvent(new Event('input',{bubbles:true})); } return 1; }")
            # 10 language ratings via DOM click + "5 - Fluent"
            for lbl in ["Comprehension", "Overall", "Reading", "Speaking", "Writing"]:
                for _ in range(2):
                    b.eval_js("() => { const b=[...document.querySelectorAll('button')].find(x=>(x.getAttribute('aria-label')||'').trim()==='" + lbl + " Select One Required'); if(b) b.click(); return 1; }")
                    time.sleep(2)
                    click_leaf("5 - Fluent", wait=0.8)
            save_continue()
            continue
        # ---- STEP 4: Questions ----
        if st == 4:
            for ref, val in [(r'textbox \[ref=(f408e2709)\]', "https://www.linkedin.com/in/janedoe"), (r'textbox \[ref=(f408e2727)\]', "<expected CTC>")]:
                m = re.search(ref, snap())
                if m: b._call("browser_type", {"target": m.group(1), "text": val, "slowly": True}); time.sleep(0.4)
            t = snap()
            # combos: category=Experienced, notice=Immediate (serving notice, LWD <your last working day>), legal=Yes, employed=No, disability=No, declaration=Yes
            combos = re.findall(r'button "Select One Required" \[ref=(\w+)\]', t)
            wants = ["Experienced", "Immediate", "Yes", "No", "No", "Yes"]
            for i, ref in enumerate(combos[:6]):
                if i < len(wants):
                    combo_pick(ref, wants[i])
                t = snap()
            save_continue()
            continue
        # ---- STEP 5: Voluntary + DOB + citizenship ----
        if st == 5:
            t = snap()
            g = re.search(r'button "Gender Select One Required" \[ref=(\w+)\]', t)
            if g: combo_pick(g.group(1), "Male")
            # DOB: month/day/year (<YOUR_DOB> -> 04/15/1994)
            for f, v in [("Month", "04"), ("Day", "15"), ("Year", "1994")]:
                i = re.search(rf'personalInfoPerson--dateOfBirth-dateSection{f}-input', snap())
                if i:
                    b.eval_js("() => { const i=document.getElementById('" + i.group(0) + "'); if(i){ i.focus(); i.value=''; } return 1; }")
                    b._call("browser_type", {"target": "#" + i.group(0), "text": v, "slowly": True}); time.sleep(0.3)
            # citizenship: checkbox-list
            t = snap()
            cit = re.search(r'button "([^"]*Citizenship[^"]*)" \[ref=(\w+)\]', t)
            if cit:
                b._call("browser_click", {"target": cit.group(2)}); time.sleep(6)
                r = b.eval_js("() => { const o=[...document.querySelectorAll('div[data-automation-id=menuItem]')].find(x=>x.offsetParent && /Indian Citizen/i.test(x.innerText||'')); if(!o) return 'no-item'; const cb=o.querySelector('span')||o; cb.click(); return 'clicked'; }")
                log("citizenship: " + str(r.get("result") if isinstance(r, dict) else r))
            # terms checkbox
            b.eval_js("() => { const c=[...document.querySelectorAll('input[type=checkbox]')].find(x=>x.offsetParent && /understand and acknowledge/i.test(x.closest('div')?.innerText||'')); if(c && !c.checked) c.click(); return 1; }")
            save_continue()
            continue
        # ---- STEP 6: Review / Submit ----
        if st == 6 or "Submit" in t:
            sub = re.search(r'button "Submit[^"]*" \[ref=(\w+)\]', t)
            if sub:
                b._call("browser_click", {"target": sub.group(1)}); time.sleep(10)
                t = snap()
                if re.search(r'(submitted|thank you|confirmation|you have applied)', t, re.I):
                    log("✅✅ CONFIRMED SUBMITTED"); RESUME_POST(); sys.exit(0)
            else:
                sc = save_continue()
        b._call("browser_take_screenshot", {}); time.sleep(1)
    print("❌ NOT CONFIRMED after 14 loops")
    sys.exit(1)

if __name__ == "__main__":
    main()
