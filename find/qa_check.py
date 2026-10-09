#!/usr/bin/env python3
"""qa_check.py <jobid> — verify job is QA/SDET before applying. Prints title + QA verdict."""
import json, socket, sys, time, re

def ctl(cmd, timeout=20):
    s = socket.create_connection(("127.0.0.1", 9000), timeout=timeout)
    s.sendall((json.dumps(cmd) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        c = s.recv(65536)
        if not c: break
        buf += c
    s.close()
    return json.loads(buf.decode())

QA_RE = re.compile(r"\b(qa|quality|sdet|test|testing|automation|q[eē])\b", re.I)
NON_QA_RE = re.compile(r"\b(recruiter|trainer|mentor|teacher|sales|marketing|frontend|backend|fullstack|devops|data engineer|data scientist|scientist|security engineer|network engineer|hr|talent|thin films|optics|mechanical|manufacturing|applied scientist|research engineer)\b", re.I)

jid = sys.argv[1]
ctl({"op": "navigate", "url": f"https://www.linkedin.com/jobs/view/{jid}/"})
time.sleep(7)
r = ctl({"op": "eval", "js": "() => { const t=document.body.innerText.replace(/\\s+/g,' '); const i=t.indexOf('₹0'); const seg=t.slice(i>0?i+2:0, i>0?i+220:t.length); const apply=[...document.querySelectorAll('button')].find(x=>x.offsetParent&&/easy apply|apply on company website|^apply$/i.test((x.getAttribute('aria-label')||'')+' '+(x.innerText||'').trim())); return JSON.stringify({seg, apply: apply?(apply.getAttribute('aria-label')||'').slice(0,30):'none'}); }"})
d = json.loads(r.get("result") or '{"seg":"","apply":"none"}')
seg = d["seg"]
# title = text up to first location/time marker
m = re.search(r"(.+?)(?:\s+·\s+|\s+(?:Bengaluru|Bangalore|India|Remote|Hybrid|Karnataka)\s+|\s+\d+\s+(?:hrs?|days?|weeks?)\s+ago)", seg)
title = m.group(1).strip()[:90] if m else seg[:90]
is_qa = bool(QA_RE.search(title)) and not bool(NON_QA_RE.search(title))
print(f"TITLE: {title}", flush=True)
print(f"QA: {is_qa} | apply-btn: {d.get('apply')}", flush=True)
sys.exit(0 if is_qa else 1)
