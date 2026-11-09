#!/usr/bin/env python3
"""li_drive.py <jobid> — drive LinkedIn Easy Apply: click apply, walk steps, fill numerics, submit.

Records through core/applied_ledger.py (the dedupe authority), not progress.json:
this script used to append a fake row with company="Unknown until employer proof"
and gate on string-matching APPLIED.md, which is the same pattern that destroyed
history on 2026-11-04.
"""
import json, os, re, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.logger import log
from core.applied_ledger import has_job_id, is_applied, record
from core.ctl import call
from core.ui import ev, until, until_change
from config.answers import A


def already_applied(jid):
    """Exact LinkedIn job-ID gate, via the ledger (single owner)."""
    return has_job_id(jid)


def record_attempt(jid, proof, company="LinkedIn employer pending", role="LinkedIn job"):
    """Append to the ledger. Idempotent on (company, role, url)."""
    row = record(
        company, role, "submitted-awaiting-email",
        url=f"https://www.linkedin.com/jobs/view/{jid}/",
        job_id=str(jid), proof=proof[-700:], source="linkedin-easy-apply",
    )
    if row:
        log.info("ledger: recorded %s %s (%s)", company, role, row["status"])
    else:
        log.info("ledger: duplicate, not re-recorded (job %s)", jid)
    return bool(row)


def ctl(cmd, timeout=25):
    return call(cmd, timeout=timeout)


READ_STATE = """() => { const t=document.body.innerText.replace(/\\s+/g,' ');
 const m=t.match(/(\\d+)\\/(\\d+)\\s*pages/);
 const submit=/Submit application/.test(t);
 const done=/application sent|you applied|submitted|successful/i.test(t);
 return JSON.stringify({step:m?m[1]+'/'+m[2]:'?', submit, done}); }"""

CONFIRMED = r"application (was )?sent|application submitted|keep track of your application"


def state():
    """Current step/submit state of the apply modal. {} while it is still rendering."""
    try:
        return json.loads(ev(READ_STATE) or "{}")
    except Exception:
        return {}


READ_NUMS = """() => {
  const scope=document.querySelector('dialog[open]')||[...document.querySelectorAll('article')].find(a=>/Apply to/.test(a.innerText))||document.body;
  const els=[...scope.querySelectorAll('input[type=text], input[type=number]')].filter(e=>e.offsetParent);
  return JSON.stringify(els.map(el=>{const r=el.getBoundingClientRect(); return {x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)};}));
}"""

# Numeric screening answers, in the order LinkedIn renders them. Sourced from
# config/answers.py instead of literals so there is ONE owner of "8 yrs / 27 LPA /
# 33 LPA / 32 days notice". Positional filling is inherently fragile — log what was
# used so a wrong-order render is visible in the run log afterwards.
NUMERIC_ANSWERS = [
    str(A["years"]),      # total years of experience
    str(A["years"]),      # years in automation
    str(A["notice"]),     # notice period in days
    str(A["ctc"]),        # current CTC
    str(A["expected"]),   # expected CTC
]


def fill_numbers(vals):
    pts = json.loads(ev(READ_NUMS) or "[]")
    for i, p in enumerate(pts[:len(vals)]):
        ctl({"op": "mouse_click", "x": p["x"], "y": p["y"]})
        time.sleep(0.4)
        ctl({"op": "keys", "keys": "Meta+A"})
        ctl({"op": "keys", "keys": "Backspace"})
        time.sleep(0.3)
        ctl({"op": "htype", "value": vals[i]})
        time.sleep(0.6)

def answer_yes_no():
    """Click radio answers: default No for LLB/law/notice questions, Yes for authorized/experience."""
    ev("""() => {
      const rds=[...document.querySelectorAll('input[type=radio]')].filter(r=>r.offsetParent);
      const groups={};
      for(const rd of rds){ (groups[rd.name]=groups[rd.name]||[]).push(rd); }
      for(const key in groups){
        const g=groups[key]; const rd0=g[0];
        let q=''; let n=rd0.parentElement;
        for(let i=0;i<10&&n;i++){ const t=(n.innerText||'').replace(/\\s+/g,' ').trim(); if(t.length>8&&t.length<130){ q=t; break; } n=n.parentElement; }
        const want = /LLB|LLM|notice|law/i.test(q) ? 'No' : 'Yes';
        for(const rd of g){
          const lab=rd.parentElement&&rd.parentElement.parentElement;
          if(lab&&(lab.innerText||'').trim()===want&&!rd.checked){ lab.click(); break; }
        }
      }
      return 1;
    }""")
    time.sleep(1)

def ready_listing(jid):
    """Require page identity and company/role dedupe before opening Easy Apply."""
    nav = ctl({"op": "navigate", "url": f"https://www.linkedin.com/jobs/view/{jid}/"})
    if not nav.get("ok"):
        log.warning("STOP: navigation failed for %s: %s", jid, nav.get("error"))
        return False
    if not until(lambda: ev("() => document.querySelectorAll('button').length > 3"),
                 timeout=15, interval=0.4, what="job page render"):
        log.warning("STOP: job page did not render for %s", jid)
        return False
    title = ev("() => document.title") or ""
    parts = [part.strip() for part in title.split(" | ")]
    if len(parts) < 3 or parts[-1] != "LinkedIn" or not all(parts[:2]):
        log.warning("STOP: cannot verify company and role from page title for %s", jid)
        return False
    role, company = parts[:2]
    if is_applied(company, role):
        log.info("SKIP duplicate company/role %s | %s (job %s)", company, role, jid)
        return False
    if ev("() => /Application status\\s*Application submitted/i.test(document.body.innerText)"):
        log.info("SKIP LinkedIn already reports submitted for job %s", jid)
        return False
    return True


def advance_step(step, before):
    """Retry one failed page transition with a real keyboard event."""
    if until_change(state, before, timeout=8, interval=0.3, what=f"step {step} advance"):
        return True
    focused = ev("() => { const b=[...document.querySelectorAll('button')].find(x=>x.offsetParent&&/^(Next|Review)$/.test((x.innerText||'').trim())); if(!b) return 0; b.scrollIntoView({block:'center'}); b.focus(); return document.activeElement===b; }")
    if not focused or not ctl({"op": "keys", "keys": "Enter"}).get("ok"):
        return False
    return bool(until_change(state, before, timeout=8, interval=0.3, what=f"step {step} advance (keyboard)"))


def main():
    jid = sys.argv[1]
    if already_applied(jid):
        log.info("SKIP duplicate LinkedIn job ID %s (in ledger)", jid)
        return
    if not ready_listing(jid):
        return
    r = ev("() => { const b=[...document.querySelectorAll('button')].find(x=>x.offsetParent&&/easy apply|apply to this job/i.test((x.getAttribute('aria-label')||'')+' '+(x.innerText||''))); if(b){ b.click(); return 'applied'; } const ext=[...document.querySelectorAll('button')].find(x=>x.offsetParent&&/apply on company/i.test(x.getAttribute('aria-label')||'')); return ext?'external':'no-btn'; }")
    log.info("apply control: %s", r)
    if r != "applied":
        return
    # LinkedIn migrated Easy Apply to a native <dialog> (2026-11); the old
    # selectors matched nothing, so every EA job timed out at 10 s and recorded
    # nothing. Match all three shapes.
    until(lambda: ev("() => !!document.querySelector('dialog[open], div[role=dialog], .jobs-easy-apply-modal')"),
          timeout=10, interval=0.3, what="easy apply modal")
    for step in range(10):
        body = ev("() => document.body.innerText") or ""
        if re.search(r"captcha|recaptcha|hcaptcha|verify you are human|security check", body, re.I):
            log.warning("STOP: CAPTCHA/security check on job %s; user must solve it in the visible browser", jid)
            return
        # fill numeric questions if on a questions step (5+ text inputs in modal)
        pts = json.loads(ev(READ_NUMS) or "[]")
        if 3 <= len(pts) <= 8:
            log.info("filling numeric answers: %s", NUMERIC_ANSWERS)
            fill_numbers(NUMERIC_ANSWERS)
            answer_yes_no()
        # also click any unchecked consent/confirm checkboxes
        ev("() => { const cbs=[...document.querySelectorAll('input[type=checkbox]')].filter(c=>c.offsetParent&&!c.checked); for(const cb of cbs){ const lab=cb.parentElement&&cb.parentElement.parentElement; if(lab) lab.click(); } return 1; }")
        before = state()
        r = ev("() => { const b=[...document.querySelectorAll('button')].find(x=>x.offsetParent&&/^(Next|Review)$/.test((x.innerText||'').trim())); if(!b) return 'no'; b.click(); return 'clicked'; }")
        if r == "clicked" and not advance_step(step, before):
            log.warning("STOP: step %s did not advance after one keyboard retry", step)
            return
        st = ev(READ_STATE)
        d = json.loads(st or "{}")
        log.info("  step %s: %s", step, st)
        if d.get("submit"):
            ev("() => { const b=[...document.querySelectorAll('button')].find(x=>x.offsetParent&&/submit application/i.test((x.innerText||'').trim())); if(b){ b.click(); return 1; } return 0; }")
            until(lambda: re.search(CONFIRMED, ev("() => document.body.innerText") or "", re.I),
                  timeout=15, interval=0.4, what="submit confirmation")
            proof = ev("() => document.body.innerText") or ""
            if re.search(r"application (was )?sent|application submitted|keep track of your application", proof, re.I):
                record_attempt(jid, proof[-700:])
                log.info("RESULT: SUBMITTED ACK job %s; recorded submitted-awaiting-email", jid)
            else:
                log.warning("RESULT: NO POSITIVE ACK for job %s; not recorded as submitted", jid)
            return
        if d.get("done"):
            log.warning("RESULT: SUBMITTED (done) for job %s but no ACK text; not recorded", jid)
            return
    log.warning("RESULT: TIMEOUT for job %s after 10 steps", jid)

main()
