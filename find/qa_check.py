#!/usr/bin/env python3
"""qa_check.py <jobid> — verify job is QA/SDET before applying. Prints title + QA verdict."""
import json, os, sys, re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.dedupe import ROLE_QA as QA_RE, ROLE_NOT as NON_QA_RE  # single owner (DRY)
from core.ctl import call
from core.ui import ev, until


def ctl(cmd, timeout=20):
    return call(cmd, timeout=timeout)

jid = sys.argv[1]
ctl({"op": "navigate", "url": f"https://www.linkedin.com/jobs/view/{jid}/"})
until(lambda: ev("() => document.body.innerText.length > 300",
                 timeout=20), timeout=15, interval=0.4, what="job body")
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
