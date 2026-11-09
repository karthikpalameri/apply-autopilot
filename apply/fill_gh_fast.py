#!/usr/bin/env python3
"""apply/fill_gh_fast.py — Greenhouse form fill; stop before submit if a CAPTCHA is present.

Fast-path Greenhouse filler driven by a hardcoded field map (see NOTE below).
For a fully generic, API-driven Greenhouse driver use apply/gh_apply.py.

Personal values come from config/user.json via config/answers.py (A) — DRY.
CAPTCHA is a hard stop: finish safe fields, then leave the page open for the user.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.answers import A
from core.ctl import call
from core.logger import log, say
from core.resume_secure import BEFORE_UPLOAD, POST as RESUME_POST, PICK as RESUME_PICK
from core.ui import ev, exists, until
from core.captcha_guard import page_has_captcha


def ctl(cmd, timeout=60):
    return call(cmd, timeout=timeout)


def hfill(fid, v):
    return ctl({"op": "fill", "by": "selector", "key": f"#{fid}", "value": v}).get("ok")


def rs_pick(qid, target, typed=None):
    """Type, wait for the menu, click exact/contains option, fallback ArrowDown+Enter.

    Returns None when the field is not on this form at all — the ids below belong
    to one employer's Greenhouse form, so on any other form every id used to burn
    its full ~1.7s of sleeps doing nothing.
    """
    if not exists(f"#{qid}"):
        log.warning("rs_pick: #%s not on this form — skipped", qid)
        return None
    ev(f"() => {{ const i=document.getElementById('{qid}'); if(i) i.focus(); return 1; }}")
    time.sleep(0.3)
    ctl({"op": "keys", "keys": "Meta+A"}); ctl({"op": "keys", "keys": "Backspace"})
    time.sleep(0.2)
    ctl({"op": "htype", "value": typed or target[:6]})
    # poll for the menu instead of a flat 0.8s sleep
    until(lambda: ev("() => [...document.querySelectorAll('[class*=select__menu]')]"
                     ".some(m => m.querySelectorAll('[class*=option]').length > 0)"),
          timeout=0.8, interval=0.1, what="select menu options")
    r = ev(f"() => {{ const menus=[...document.querySelectorAll('[class*=select__menu]')]; for(const m of menus){{ const o=[...m.querySelectorAll('[class*=option]')]; const t=o.find(x=>x.innerText.trim().toLowerCase()==='{target.lower()}')||o.find(x=>x.innerText.includes('{target}')); if(t){{ t.click(); return 'ok'; }} }} return 'none'; }}")
    if r == "ok":
        return True
    ctl({"op": "keys", "keys": "ArrowDown"}); time.sleep(0.2)
    ctl({"op": "keys", "keys": "Enter"}); time.sleep(0.5)
    return False


def main():
    # NOTE: Greenhouse question IDs (question_XXXXXXX) below are EMPLOYER-SPECIFIC —
    # map them to the target job's form before running. All personal values come
    # from config/user.json via A (DRY).
    RESUME_PICK()
    url = sys.argv[1]
    say(f"🚀 {url}")
    ctl({"op": "navigate", "url": url})
    until(lambda: ev("() => !!document.getElementById('application-form')"),
          timeout=15, interval=0.3, what="greenhouse form")
    # ---- text fields (batch, 0.2s apart) ----
    std = {"first_name": A["full_name"].split()[0], "last_name": A["full_name"].split()[-1],
           "email": A["email"], "phone": A["phone"], "preferred_name": A["full_name"].split()[0]}
    for fid, v in std.items():
        if hfill(fid, v): say(f"✍️ {fid} = {v[:12]}")
        time.sleep(0.2)
    # ---- react-selects ----
    picks = [("country", "India +91"), ("candidate-location", A["location"]),
             ("degree--0", A.get("degree", "")), ("discipline--0", A.get("discipline", "")),
             ("start-month--0", A.get("edu_start_month", "")), ("end-month--0", A.get("edu_end_month", "")),
             ("question_6511264009", "No"), ("question_6511265009", "No"),
             ("question_6511267009", "No"), ("question_6511261009", "LinkedIn"),
             ("question_6511263009", "Yes"), ("question_6511268009", "No"),
             ("question_6511272009", "No"), ("question_6511273009", "No"),
             ("question_6511275009", "No"), ("question_6511277009", "No"),
             ("question_6511279009", "I agree")]
    for qid, tgt in picks:
        ok = rs_pick(qid, tgt, typed={"country": "India", "candidate-location": A["location"][:6],
                                      "question_6511261009": "Linked", "question_6511279009": "I agree"}.get(qid, tgt[:6]))
        say(f"{'✅' if ok else '⚠️'} {qid} -> {tgt}")
        time.sleep(0.3)
    # ---- required text Qs ----
    for fid, v in [("question_6631381009", str(A["years"])), ("question_6631382009", str(A["years"])),
                   ("question_6631383009", str(A.get("expected_ctc_lpa", ""))), ("question_6631384009", A["location"]),
                   ("question_6631385009", str(A.get("expected_ctc", "")))]:
        if hfill(fid, v): say(f"✍️ {fid} = {v}")
        time.sleep(0.2)
    # ---- resume ----
    ctl({"op": "upload_cdp", "path": BEFORE_UPLOAD()})
    say("📎 resume uploaded (md5 gate ✓)")
    RESUME_POST()
    until(lambda: ev("() => document.querySelectorAll('[class*=file]').length > 0"),
          timeout=10, interval=0.3, what="resume upload")
    # ---- verify via DOM ----
    errs = ev("() => [...document.querySelectorAll('*')].filter(e=>e.children.length===0&&e.offsetParent&&/this field is required/i.test((e.innerText||''))).length")
    say("required-empty:", errs)
    if int(errs or 0) > 0:
        say("STILL MISSING REQUIRED — manual fix needed")
        sys.exit(2)
    # ---- CAPTCHA hard stop: no solving, bypass, or automated submit ----
    if page_has_captcha(ev):
        say("STOP: CAPTCHA detected. No submit was clicked; page left open for you.")
        sys.exit(3)
    # ---- submit only when the page is confirmed clear ----
    ev("() => { const b=[...document.querySelectorAll('button, input[type=submit]')].find(x=>x.offsetParent&&/submit/i.test((x.innerText||x.value||'').trim())); if(b){ b.click(); return 'clicked'; } return 'no'; }")
    until(lambda: ev("() => { const f=document.getElementById('application-form'); "
                     "const t=document.body.innerText; return !f || "
                     "/thank you for your application|application has been submitted|your application was/i.test(t); }"),
          timeout=20, interval=0.4, what="submit confirmation")
    st = ev("() => { const f=document.getElementById('application-form'); const t=document.body.innerText.replace(/\\s+/g,' '); return JSON.stringify({formGone:!f, thanks:/thank you for your application|application has been submitted|your application was/i.test(t)}); }")
    say("AFTER SUBMIT:", st)


if __name__ == "__main__":
    main()
