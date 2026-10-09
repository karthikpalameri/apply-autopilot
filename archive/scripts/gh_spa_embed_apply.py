#!/usr/bin/env python3
"""gh_spa_embed_apply.py — Greenhouse SPA-embed apply (any job).
Reuses proven GH helpers (ctl/ev/hfill/rs_pick) from fill_gh_fast.py. KISS."""
import os, json, socket, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.answers import A, RESUME
from core.resume_secure import BEFORE_UPLOAD, POST as RESUME_POST, PICK as RESUME_PICK

def ctl(cmd, timeout=90):
    with socket.create_connection(("127.0.0.1", 9000), timeout=5) as s:
        s.sendall(json.dumps(cmd).encode())
        s.settimeout(timeout)
        try:
            return json.loads(s.recv(1 << 20).decode())
        except socket.timeout:
            return {"ok": False, "error": "timeout"}

def ev(js):
    r = ctl({"op": "eval", "js": js})
    return r.get("result") if isinstance(r, dict) else r

def hfill(fid, v):
    r = ev(f"() => {{ const el=document.getElementById('{fid}'); if(!el) return 'noid'; "
           f"const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set; "
           f"set.call(el,{json.dumps(v)}); el.dispatchEvent(new Event('input',{{bubbles:true}})); "
           f"el.dispatchEvent(new Event('change',{{bubbles:true}})); return el.value; }}")
    return r

def rs_pick(qid, target, typed=None):
    ev(f"() => {{ const el=document.getElementById('{qid}'); if(el){{ el.click(); return 'ok'; }} return 'noid'; }}")
    time.sleep(0.5)
    ctl({"op": "keys", "keys": "Meta+A"}); ctl({"op": "keys", "keys": "Backspace"})
    time.sleep(0.2)
    ctl({"op": "htype", "value": typed or target[:6]})
    time.sleep(0.8)
    r = ev(f"() => {{ const menus=[...document.querySelectorAll('[class*=select__menu]')]; for(const m of menus){{ const o=[...m.querySelectorAll('[class*=option]')]; const t=o.find(x=>x.innerText.trim().toLowerCase()==='{target.lower()}')||o.find(x=>x.innerText.includes('{target}')); if(t){{ t.click(); return 'ok'; }} }} return 'none'; }}")
    if r == "ok":
        return True
    ctl({"op": "keys", "keys": "ArrowDown"}); time.sleep(0.2)
    ctl({"op": "keys", "keys": "Enter"}); time.sleep(0.5)
    return False

def main():
    RESUME_PICK()
    URL = "https://job-boards.greenhouse.io/embed/job_app?for=<org>&token=<job-id>"
    print("🚀 GH SPA apply", flush=True)
    # page already loaded in browser (GH embed keeps network busy — skip navigate)
    for _ in range(10):
        if ev("() => !!document.getElementById('first_name')") == "true":
            break
        time.sleep(2)

    # standard contact
    std = {"first_name": A["full_name"].split()[0], "last_name": A["full_name"].split()[-1],
           "preferred_name": A["full_name"].split()[0], "email": A["email"], "phone": A["phone"]}
    for fid, v in std.items():
        if hfill(fid, v): print(f"✍️ {fid} = {v[:12]}", flush=True)
        time.sleep(0.2)

    # react-selects
    for qid, tgt, typed in [("country", "India +91", "India"), ("candidate-location", "Bengaluru", "Bangal")]:
        print(f"{'✅' if rs_pick(qid, tgt, typed) else '⚠️'} {qid} -> {tgt}", flush=True)
        time.sleep(0.3)

    # text questions
    q = {"question_30299303003": A.get("address1", "Bengaluru, Karnataka, India"),
         "question_30299304003": "",
         "question_30299305003": "Bengaluru",
         "question_30299306003": "Karnataka",
         "question_30299307003": "<postcode>",
         "question_30299308003": "India",
         "question_30299309003": A.get("linkedin", ""),
         "question_30299312003": "LinkedIn",
         "question_30299313003": "",
         "question_30299314003": "No",
         "question_30299315003": "Yes",
         "question_30299316003": "No",
         "question_30299317003": "I agree",
         "4000460003": "Prefer not to say"}
    for fid, v in q.items():
        if hfill(fid, v): print(f"✍️ {fid} = {v[:18]}", flush=True)
        time.sleep(0.2)

    # pronouns: No Preference
    ev("() => { const c=[...document.querySelectorAll('input[type=checkbox]')].find(x=>x.closest('label')&&/No Preference/.test(x.closest('label').innerText)); if(c&&!c.checked){ c.click(); return 'ok'; } return 'none'; }")
    # GDPR consent
    ev("() => { const c=document.getElementById('gdpr_demographic_data_consent_given_1'); if(c&&!c.checked){ c.click(); return 'ok'; } return 'none'; }")
    print("☑️ pronouns + consent", flush=True)

    # resume
    ctl({"op": "upload_cdp", "path": BEFORE_UPLOAD()})
    print("📎 resume uploaded (md5 gate ✓)", flush=True)
    RESUME_POST()

    # verify no required-empty
    errs = ev("() => [...document.querySelectorAll('*')].filter(e=>e.children.length===0&&e.offsetParent&&/this field is required/i.test((e.innerText||''))).length")
    print("required-empty:", errs, flush=True)
    if int(errs or 0) > 0:
        print("STILL MISSING REQUIRED — manual fix needed", flush=True); sys.exit(2)

    # recaptcha sitekey from page + solve
    sk = ev("() => { const el=document.querySelector('[data-sitekey]'); return el?el.getAttribute('data-sitekey'):''; }")
    print("sitekey:", sk, flush=True)
    if sk:
        from core.capsolver import solve_recaptcha_v2_enterprise
        tok = solve_recaptcha_v2_enterprise(sk, URL, max_wait=150)
        print("recaptcha:", "OK" if tok.get("ok") else tok, flush=True)
        if tok.get("ok"):
            T = tok["token"]
            ev(f"() => {{ const ta=document.querySelector('textarea[name=g-recaptcha-response]'); if(ta){{ const set=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set; set.call(ta,'{T}'); ta.dispatchEvent(new Event('input',{{bubbles:true}})); }} if(typeof grecaptcha!=='undefined'&&grecaptcha.enterprise){{ grecaptcha.enterprise.execute=function(sk,opts){{ return Promise.resolve('{T}'); }}; }} return 1; }}")
    else:
        print("⚠️ NO SITEKEY — recaptcha may be invisible; trying submit", flush=True)

    ev("() => { const b=[...document.querySelectorAll('button, input[type=submit]')].find(x=>x.offsetParent&&/submit/i.test((x.innerText||x.value||'').trim())); if(b){ b.click(); return 'clicked'; } return 'no'; }")
    time.sleep(8)
    st = ev("() => { const t=document.body.innerText.replace(/\\s+/g,' '); return JSON.stringify({thanks:/thank you for your application|application has been submitted|your application was/i.test(t), snippet:t.slice(0,160)}); }")
    print("AFTER SUBMIT:", st, flush=True)

main()
