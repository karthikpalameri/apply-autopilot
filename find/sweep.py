#!/usr/bin/env python3
"""sweep.py — unattended LinkedIn QA sweep: search -> qa_check -> li_drive -> verify -> record.
bigpowers discipline: session-state (progress.json after each), verify-work (done:true gate), diagnose-stall (no blind retries)."""
import json, socket, subprocess, sys, time, re

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

def load_progress():
    try:
        return json.load(open("progress.json"))
    except Exception:
        return {"total_applications": 0, "linkedin": []}

def save_progress(p):
    json.dump(p, open("progress.json", "w"), indent=1)

QA_RE = re.compile(r"\b(qa|sdet|quality|test|testing|automation)\b", re.I)
NON_RE = re.compile(r"\b(recruiter|trainer|sales|marketing|frontend|backend|data scientist|scientist|security engineer|hr|talent|thin films|optics|mechanical|hardware|firmware|electrical|soi|soc|verification|silicon|auditor|warehouse)\b|firmware|zFirmware", re.I)

def check_job(jid):
    """diagnose-stall + qa guard: navigate, read title, decide."""
    ctl({"op": "navigate", "url": f"https://www.linkedin.com/jobs/view/{jid}/"})
    time.sleep(4)
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
    time.sleep(8)
    r = ev("() => { const cards=[...document.querySelectorAll('li[data-occludable-job-id]')]; return JSON.stringify(cards.map(c=>c.getAttribute('data-occludable-job-id')).filter(Boolean)); }")
    ids = json.loads(r or "[]")
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
        print(f"  {jid}: title={title[:40]} qa={qa} ea={ea}", flush=True)
        if not qa:
            print("    -> not QA, skip", flush=True)
            continue
        # li_drive apply
        r = subprocess.run([sys.executable, "li_drive.py", jid], capture_output=True, text=True, timeout=280)
        log = r.stdout + r.stderr
        ok = "RESULT: SUBMITTED" in log
        print(f"    -> {'SUBMITTED' if ok else 'blocked/skip'}", flush=True)
        if ok:
            p.setdefault("linkedin", []).append({"id": jid, "title": title, "status": "submitted"})
            p["total_applications"] = p.get("total_applications", 0) + 1
            applied += 1
            save_progress(p)  # session-state: record after each
        time.sleep(2)
    print(f"DONE: {applied} new apps this sweep | total {p.get('total_applications')}", flush=True)

main()
