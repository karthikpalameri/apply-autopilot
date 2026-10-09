#!/usr/bin/env python3
"""apply/li_apply_mcp.py — LinkedIn Easy Apply via MCP refs. Reuses the open browser session.
Reads config/li_listed_apply_queue.json. DOM dump on failure."""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browser import McpBrowser

b = McpBrowser()
def snap(): return b.snapshot().get("text","")
def ref_of(t, pattern, nth=1):
    ms = list(re.finditer(rf'({pattern})[^\[]*\[ref=(\w+)\]', t))
    return ms[nth-1].group(2) if len(ms) >= nth else None
def btn_ref(t, label):
    return ref_of(t, rf'button "{re.escape(label)}"')

def apply_job(job):
    jid = job["jid"]
    print(f"\n▶ {job['title'][:44]} @ {job['co']} (jid={jid})")
    b.navigate(f"https://www.linkedin.com/jobs/view/{jid}/"); time.sleep(6)
    t = snap()
    easy = btn_ref(t, "Easy Apply")
    if not easy:
        # check already-applied or closed
        msg = "applied" if "Applied" in t[:2000] else "no Easy Apply (closed/not-EA)"
        print(f"    ⏭ {msg}"); return "skip"
    b._call("browser_click", {"target": easy}); time.sleep(4)
    # walk steps
    for step in range(10):
        t = snap()
        submit = btn_ref(t, "Submit application")
        review = btn_ref(t, "Review")
        nxt = btn_ref(t, "Next")
        if submit:
            b._call("browser_click", {"target": submit}); time.sleep(4)
            t2 = snap()
            ok = "application sent" in t2.lower() or "submitted" in t2.lower()
            print(f"    ✅ SUBMITTED" if ok else "    ⚠️ submitted (verify)")
            return "applied" if ok else "verify"
        if review:
            b._call("browser_click", {"target": review}); time.sleep(3); continue
        if nxt:
            # fill required textboxes on the current step first (visibility-limited)
            txts = re.findall(r'textbox "([^"]+)" \[ref=(\w+)\]', t)
            for label, ref in txts:
                if re.search(r"email|phone|first|last|name", label, re.I):
                    continue  # LinkedIn pre-fills profile data
            b._call("browser_click", {"target": nxt}); time.sleep(3); continue
        # stuck — dump what we see
        print("    ⚠️ stuck step", step)
        open("logs/li_stuck_dom.txt","w").write(t[-2500:])
        print("    DOM dumped -> logs/li_stuck_dom.txt")
        return "stuck"
    return "stuck"

if __name__ == "__main__":
    queue = json.load(open("config/li_listed_apply_queue.json"))
    results = []
    for job in queue:
        r = apply_job(job)
        results.append({"jid": job["jid"], "co": job["co"], "title": job["title"][:45], "result": r})
        time.sleep(2)
    json.dump(results, open("config/li_apply_results.json","w"), indent=1)
    print("\n=== RESULTS ===")
    for r in results:
        print(f"  {r['result']:8s} | {r['co'][:22]:22s} | {r['title'][:42]}")
