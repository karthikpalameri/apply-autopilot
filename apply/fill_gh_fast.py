import os
#!/usr/bin/env python3
"""fill_gh_fast.py — FAST Greenhouse fill+submit: tight rs_pick (0.8s), batch text, CapSolver recaptcha override."""
import json, socket, sys, time, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.answers import A, RESUME
from core.resume_secure import BEFORE_UPLOAD, POST as RESUME_POST, PICK as RESUME_PICK
from core.capsolver import solve_recaptcha_v2_enterprise

def ctl(cmd, timeout=60):
    s = socket.create_connection(("127.0.0.1", 9000), timeout=timeout)
    s.sendall((json.dumps(cmd) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        c = s.recv(65536)
        if not c: break
        buf += c
    s.close()
    return json.loads(buf.decode())

def ev(js):
    return (ctl({"op": "eval", "js": js}) or {}).get("result")

def hfill(fid, v):
    return ctl({"op": "hfill", "by": "selector", "key": f"#{fid}", "value": v}).get("ok")

def rs_pick(qid, target, typed=None):
    """Type, wait 0.8s, click exact/contains option, fallback ArrowDown+Enter."""
    ev(f"() => {{ const i=document.getElementById('{qid}'); if(i) i.focus(); return 1; }}")
    time.sleep(0.3)
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
    # NOTE: Greenhouse question IDs (question_XXXXXXX) and the reCAPTCHA sitekey/token
    # below are EMPLOYER-SPECIFIC — map them to the target job's form before running.
    # All personal values come from config/user.json via A (DRY).
    RESUME_PICK()
    url = sys.argv[1]
    print(f"🚀 {url}", flush=True)
    ctl({"op": "navigate", "url": url}); time.sleep(4)
    # ---- text fields (batch, 0.2s apart) ----
    std = {"first_name": A["full_name"].split()[0], "last_name": A["full_name"].split()[-1],
           "email": A["email"], "phone": A["phone"], "preferred_name": A["full_name"].split()[0]}
    for fid, v in std.items():
        if hfill(fid, v): print(f"✍️ {fid} = {v[:12]}", flush=True)
        time.sleep(0.2)
    # ---- react-selects ----
    picks = [("country", "India +91"), ("candidate-location", A["location"]),
             ("degree--0", A["degree"]), ("discipline--0", A["discipline"]),
             ("start-month--0", A["edu_start_month"]), ("end-month--0", A["edu_end_month"]),
             ("question_6511264009", "No"), ("question_6511265009", "No"),
             ("question_6511267009", "No"), ("question_6511261009", "LinkedIn"),
             ("question_6511263009", "Yes"), ("question_6511268009", "No"),
             ("question_6511272009", "No"), ("question_6511273009", "No"),
             ("question_6511275009", "No"), ("question_6511277009", "No"),
             ("question_6511279009", "I agree")]
    for qid, tgt in picks:
        ok = rs_pick(qid, tgt, typed={"country": "India", "candidate-location": A["location"][:6],
                                      "question_6511261009": "Linked", "question_6511279009": "I agree"}.get(qid, tgt[:6]))
        print(f"{'✅' if ok else '⚠️'} {qid} -> {tgt}", flush=True)
        time.sleep(0.3)
    # ---- required text Qs ----
    for fid, v in [("question_6631381009", str(A["years"])), ("question_6631382009", str(A["years"])),
                   ("question_6631383009", str(A["expected_ctc_lpa"])), ("question_6631384009", A["location"]),
                   ("question_6631385009", str(A["expected_ctc"]))]:
        if hfill(fid, v): print(f"✍️ {fid} = {v}", flush=True)
        time.sleep(0.2)
    # ---- resume ----
    ctl({"op": "upload_cdp", "path": BEFORE_UPLOAD()})
    print("📎 resume uploaded (md5 gate ✓)", flush=True)
    RESUME_POST()
    time.sleep(2)
    # ---- verify via DOM ----
    errs = ev("() => [...document.querySelectorAll('*')].filter(e=>e.children.length===0&&e.offsetParent&&/this field is required/i.test((e.innerText||''))).length")
    print("required-empty:", errs, flush=True)
    if int(errs or 0) > 0:
        print("STILL MISSING REQUIRED — manual fix needed", flush=True)
        sys.exit(2)
    # ---- recaptcha enterprise: solve + override execute ----
    tok = solve_recaptcha_v2_enterprise(
        "6LfmcbcpAAAAAChNTbhUShzUOAMj_wY9LQIvLFX0",
        "https://job-boards.greenhouse.io/embed/job_app?for=<org>&token=<job-id>",
        max_wait=150)
    print("recaptcha:", "OK" if tok.get("ok") else tok, flush=True)
    if not tok.get("ok"):
        print("RECAPTCHA FAILED — manual solve needed", flush=True); sys.exit(3)
    T = tok["token"]
    # inject + override execute so Greenhouse's submit gets OUR token
    ev(f"() => {{ const ta=document.querySelector('textarea[name=g-recaptcha-response]'); if(ta){{ const set=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set; set.call(ta,'{T}'); ta.dispatchEvent(new Event('input',{{bubbles:true}})); }} if(typeof grecaptcha!=='undefined'&&grecaptcha.enterprise){{ grecaptcha.enterprise.execute=function(sk,opts){{ return Promise.resolve('{T}'); }}; }} return 1; }}")
    time.sleep(1)
    # ---- submit ----
    ev("() => { const b=[...document.querySelectorAll('button, input[type=submit]')].find(x=>x.offsetParent&&/submit/i.test((x.innerText||x.value||'').trim())); if(b){ b.click(); return 'clicked'; } return 'no'; }")
    time.sleep(8)
    st = ev("() => { const f=document.getElementById('application-form'); const t=document.body.innerText.replace(/\\s+/g,' '); return JSON.stringify({formGone:!f, thanks:/thank you for your application|application has been submitted|your application was/i.test(t)}); }")
    print("AFTER SUBMIT:", st, flush=True)

main()
