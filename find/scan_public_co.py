#!/usr/bin/env python3
"""scan_public_co.py <name> <companyId> — QA/SDET roles at one public co (live LinkedIn session)."""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ctl import call_wait

ctl = call_wait  # shared wrapper: call() + settle delay (core.ctl)

name = sys.argv[1]
cid = sys.argv[2]
url = f"https://www.linkedin.com/jobs/search/?keywords=QA%20SDET&location=Bengaluru&f_C={cid}&geoId=102713980&f_TPR=r604800"
ctl({"op": "navigate", "url": url}, 6.5)
js = """(() => {
  const cards=[...document.querySelectorAll('.job-card-container--clickable')];
  const out=[];
  for (const c of cards) {
    const lines=c.innerText.split("\\n").filter(Boolean);
    const a=c.querySelector("a[href*='/jobs/view/']");
    const m=(a&&a.href)? a.href.match(/jobs\\/view\\/(\\d+)/) : null;
    const owned = lines.some(l => l && l.indexOf(NAME) >= 0);
    if (owned && /qa|sdet|test|quality|automation/i.test(lines[0]||'')) {
      out.push({title: lines[0].slice(0,50), loc: (lines.find(l=>l.indexOf('India')>=0)||'').slice(0,30), id: m?m[1]:null});
    }
  }
  return {n: cards.length, cards: out.slice(0,10)};
})()""".replace("NAME", json.dumps(name))
r = ctl({"op": "eval", "js": js}, 0.3)
print(json.dumps(r.get("result"), indent=1))
