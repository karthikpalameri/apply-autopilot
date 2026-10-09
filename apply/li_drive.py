#!/usr/bin/env python3
"""li_drive.py <jobid> — drive LinkedIn Easy Apply: click apply, walk steps, fill numerics, submit."""
import json, socket, sys, time, re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from config.answers import A
APPLIED = os.path.join(ROOT, "scratch", "APPLIED.md")
PROGRESS = os.path.join(ROOT, "config", "progress.json")


def already_applied(jid):
    """Exact LinkedIn job-ID gate across both existing trackers."""
    needles = (str(jid), f"/jobs/view/{jid}", f"_{jid}_")
    for path in (APPLIED, PROGRESS):
        try: text = open(path, encoding="utf-8").read()
        except FileNotFoundError: continue
        if any(n in text for n in needles): return True
    return False


def record_attempt(jid, proof):
    try: data = json.load(open(PROGRESS, encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError): return
    rows = data.setdefault("verified_applications", [])
    if any(str(r.get("job_id")) == str(jid) for r in rows): return
    rows.append({"record_id": f"linkedin_job_{jid}", "company": "Unknown until employer proof", "role": "Unknown until employer proof", "date": time.strftime("%Y-%m-%d"), "status": "submitted-awaiting-email", "url": f"https://www.linkedin.com/jobs/view/{jid}/", "via": "linkedin-easy-apply", "job_id": str(jid), "proof": proof})
    with open(PROGRESS, "w", encoding="utf-8") as f: json.dump(data, f, indent=2)

def ctl(cmd, timeout=25):
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
    return (ctl({"op": "eval", "js": js}) or {}).get("result") or ""

READ_NUMS = """() => {
  const scope=[...document.querySelectorAll('article')].find(a=>/Apply to/.test(a.innerText))||document.body;
  const els=[...scope.querySelectorAll('input[type=text], input[type=number]')].filter(e=>e.offsetParent);
  return JSON.stringify(els.map(el=>{const r=el.getBoundingClientRect(); return {x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)};}));
}"""

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

def main():
    jid = sys.argv[1]
    if already_applied(jid):
        print(f"SKIP duplicate LinkedIn job ID {jid}", flush=True)
        return
    ctl({"op": "navigate", "url": f"https://www.linkedin.com/jobs/view/{jid}/"})
    time.sleep(6)
    r = ev("() => { const b=[...document.querySelectorAll('button')].find(x=>x.offsetParent&&/easy apply|apply to this job/i.test((x.getAttribute('aria-label')||'')+' '+(x.innerText||''))); if(b){ b.click(); return 'applied'; } const ext=[...document.querySelectorAll('button')].find(x=>x.offsetParent&&/apply on company/i.test(x.getAttribute('aria-label')||'')); return ext?'external':'no-btn'; }")
    print("apply:", r, flush=True)
    if r != "applied":
        return
    time.sleep(5)
    for step in range(10):
        body = ev("() => document.body.innerText") or ""
        if re.search(r"captcha|recaptcha|hcaptcha|verify you are human|security check", body, re.I):
            print("STOP: CAPTCHA/security check; user must solve it in the visible browser", flush=True)
            return
        # fill numeric questions if on a questions step (5+ text inputs in modal)
        pts = json.loads(ev(READ_NUMS) or "[]")
        if 3 <= len(pts) <= 8:
            # Order-sensitive heuristic for LinkedIn Easy Apply numeric questions —
            # [years, years, current_ctc_lpa, expected_ctc_lpa, notice_days].
            # Verify against the actual questions before relying on it.
            fill_numbers([str(A["years"]), str(A["years"]),
                          str(A["current_ctc_lpa"]), str(A["expected_ctc_lpa"]),
                          str(A["notice"])])
            answer_yes_no()
        # also click any unchecked consent/confirm checkboxes
        ev("() => { const cbs=[...document.querySelectorAll('input[type=checkbox]')].filter(c=>c.offsetParent&&!c.checked); for(const cb of cbs){ const lab=cb.parentElement&&cb.parentElement.parentElement; if(lab) lab.click(); } return 1; }")
        time.sleep(1)
        r = ev("() => { const b=[...document.querySelectorAll('button')].find(x=>x.offsetParent&&/^(Next|Review)$/.test((x.innerText||'').trim())); if(!b) return 'no'; b.click(); return 'clicked'; }")
        time.sleep(5)
        st = ev("() => { const t=document.body.innerText.replace(/\\s+/g,' '); const m=t.match(/(\\d+)\\/(\\d+)\\s*pages/); const submit=/Submit application/.test(t); const done=/application sent|you applied|submitted|successful/i.test(t); return JSON.stringify({step:m?m[1]+'/'+m[2]:'?', submit, done}); }")
        d = json.loads(st or "{}")
        print(f"  step {step}: {st}", flush=True)
        if d.get("submit"):
            ev("() => { const b=[...document.querySelectorAll('button')].find(x=>x.offsetParent&&/submit application/i.test((x.innerText||'').trim())); if(b){ b.click(); return 1; } return 0; }")
            time.sleep(8)
            proof = ev("() => document.body.innerText") or ""
            if re.search(r"application (was )?sent|application submitted|keep track of your application", proof, re.I):
                record_attempt(jid, proof[-700:])
                print("RESULT: SUBMITTED ACK; recorded submitted-awaiting-email", flush=True)
            else:
                print("RESULT: NO POSITIVE ACK; not recorded as submitted", flush=True)
            return
        if d.get("done"):
            print("RESULT: SUBMITTED (done)", flush=True)
            return
    print("RESULT: TIMEOUT", flush=True)

main()
