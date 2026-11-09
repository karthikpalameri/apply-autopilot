#!/usr/bin/env python3
"""sweep.py — unattended LinkedIn QA sweep: search -> qa_check -> li_drive -> verify -> record.
bigpowers discipline: session-state (progress.json after each), verify-work (done:true gate), diagnose-stall (no blind retries)."""
import json, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from config.dedupe import ROLE_QA as QA_RE, ROLE_NOT as NON_RE  # single owner (DRY)
from core.ctl import call                                   # single owner (:9000)
from core.ui import ev, until                               # single owner (page eval)
from core.logger import log
from core import progress

# progress.json is a human-facing projection, NOT the dedupe authority
# (core/applied_ledger.py is). Resolve it against the repo root, never the CWD —
# running this from find/ used to write a second, silently-diverging copy.
PROGRESS_PATH = os.path.join(ROOT, "config", "progress.json")


def ctl(cmd, timeout=25):
    return call(cmd, timeout=timeout)




def load_progress():
    # single owner: core/progress.py. Non-strict = original behaviour (empty skeleton).
    return progress.load(default={"total_applications": 0, "linkedin": []})


def save_progress(p):
    try:
        progress.save(p)
    except Exception as e:
        log.error("could not persist %s: %s", progress.PROGRESS, e)

def check_job(jid):
    """diagnose-stall + qa guard: navigate, read title, decide."""
    ctl({"op": "navigate", "url": f"https://www.linkedin.com/jobs/view/{jid}/"})
    until(lambda: ev("() => document.body.innerText.length > 300"), timeout=8,
          interval=0.4, what=f"job {jid} body")
    r = ev("() => { const t=document.body.innerText.replace(/\\s+/g,' '); const i=t.indexOf('₹0'); const seg=t.slice(i>0?i+2:0, i>0?i+200:t.length); const b=[...document.querySelectorAll('button')].filter(x=>x.offsetParent&&/apply/i.test((x.getAttribute('aria-label')||'')+' '+(x.innerText||''))); return JSON.stringify({seg, btns:b.map(x=>(x.getAttribute('aria-label')||(x.innerText||'')).trim().slice(0,26))}); }")
    d = json.loads(r or '{"seg":"","btns":[]}')
    m = re.search(r"(.+?)(?:\s+·\s+|\s+(?:Bengaluru|Bangalore|India|Remote|Hybrid)\s+|\s+\d+\s+(?:hrs?|days?)\s+ago)", d["seg"])
    title = (m.group(1).strip() if m else d["seg"][:60])[:60]
    qa = bool(QA_RE.search(title)) and not bool(NON_RE.search(title))
    ea = any("easy apply" in str(b).lower() for b in d["btns"])
    return title, qa, ea, d["btns"]

def main():
    max_jobs = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    # search: fresh 24h QA jobs
    ctl({"op": "navigate", "url": "https://www.linkedin.com/jobs/search?keywords=%22QA%22%20OR%20%22SDET%22%20OR%20%22Quality%20Engineer%22%20OR%20%22Test%20Engineer%22%20OR%20%22Test%20Automation%22&location=Bangalore&f_EA=true&f_TPR=r604800&sortBy=DD"})
    until(lambda: ev("() => document.querySelectorAll('li[data-occludable-job-id]').length > 0"),
          timeout=20, interval=0.5, what="job cards")
    r = ev("() => { const cards=[...document.querySelectorAll('li[data-occludable-job-id]')]; return JSON.stringify(cards.map(c=>c.getAttribute('data-occludable-job-id')).filter(Boolean)); }")
    ids = json.loads(r or "[]")
    log.info("sweep: %d job ids from LinkedIn search", len(ids))
    print(f"SEARCH: {len(ids)} job ids", flush=True)
    p = load_progress()
    done_ids = {j.get("id") for j in p.get("linkedin", [])}
    applied = 0
    for jid in ids:
        if applied >= max_jobs: break
        if jid in done_ids:
            print(f"  {jid}: already applied, skip", flush=True)
            continue
        title, qa, ea, btns = check_job(jid)
        log.debug("  %s: qa=%s easyapply=%s title=%r", jid, qa, ea, title[:60])
        print(f"  {jid}: title={title[:40]} qa={qa} ea={ea}", flush=True)
        if not qa:
            print("    -> not QA, skip", flush=True)
            continue
        # li_drive apply — absolute path so this works from any CWD
        li_drive = os.path.join(ROOT, "apply", "li_drive.py")
        r = subprocess.run([sys.executable, li_drive, jid],
                           capture_output=True, text=True, timeout=280)
        out = (r.stdout or "") + (r.stderr or "")   # never name this `log` — it would shadow the logger
        ok = "RESULT: SUBMITTED" in out
        if not ok:
            log.warning("  %s: drive failed rc=%s — %s", jid, r.returncode, out.strip()[-300:])
        print(f"    -> {'SUBMITTED' if ok else 'blocked/skip'}", flush=True)
        if ok:
            p.setdefault("linkedin", []).append({"id": jid, "title": title, "status": "submitted"})
            p["total_applications"] = p.get("total_applications", 0) + 1
            applied += 1
            save_progress(p)  # session-state: record after each
        time.sleep(2)
    log.info("sweep done: %d new, %d total", applied, p.get("total_applications", 0))
    print(f"DONE: {applied} new apps this sweep | total {p.get('total_applications')}", flush=True)

main()
