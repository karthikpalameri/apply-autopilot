#!/usr/bin/env python3
"""apply/li_listed_apply.py — ONE MCP session: login LinkedIn → find QA Easy Apply jobs at
LISTED product companies → apply. Persists login within the run. Usage: python apply/li_listed_apply.py"""
import sys, os, json, time, re, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browser import McpBrowser
from config.answers import A

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLIED = os.path.join(ROOT, "scratch", "APPLIED.md")
PROGRESS = os.path.join(ROOT, "config", "progress.json")


def _job_id(url):
    m = re.search(r"/jobs/view/(\\d+)", url or "")
    return m.group(1) if m else None


def load_applied_ids():
    """Fail closed: collect IDs from both trackers before any LinkedIn action."""
    ids = set()
    for path in (APPLIED, PROGRESS):
        try:
            text = open(path, encoding="utf-8").read()
        except FileNotFoundError:
            continue
        ids.update(re.findall(r"(?:jobs/view/|linkedin[_-][^_\\s]+[_-])(\\d{7,})", text))
        if path.endswith("progress.json"):
            try:
                data = json.loads(text)
                for row in data.get("verified_applications", []):
                    if row.get("job_id"): ids.add(str(row["job_id"]))
            except (json.JSONDecodeError, AttributeError):
                pass
    return ids


def record_attempt(company, title, url, status="submitted-awaiting-email", proof=""):
    """Record an attempt immediately; Gmail reconciliation can promote it later."""
    try:
        data = json.load(open(PROGRESS, encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"policy": "Only applications with explicit success proof or an explicit confirmed-success status are retained.", "success_statuses": [], "count": 0, "verified_applications": []}
    rows = data.setdefault("verified_applications", [])
    jid = _job_id(url)
    if any(str(r.get("job_id")) == str(jid) for r in rows if jid):
        return False
    rows.append({"record_id": f"linkedin_{re.sub(r'[^a-z0-9]+','_',company.lower()).strip('_')}_{jid}", "company": company, "role": title, "date": time.strftime('%Y-%m-%d'), "status": status, "url": url, "via": "linkedin-easy-apply", "job_id": jid, "proof": proof})
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(PROGRESS), prefix=".progress.")
    with os.fdopen(fd, "w", encoding="utf-8") as f: json.dump(data, f, indent=2)
    os.replace(tmp, PROGRESS)
    return True

b = McpBrowser()
b._rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name":"li-apply","version":"0.1"}})
def snap(): return b.snapshot().get("text","")
def ref_of(t, pattern):
    m = re.search(rf'({pattern})[^\[]*\[ref=(\w+)\]', t)
    return m.group(2) if m else None

LISTED = re.compile(r"cisco|microsoft|adobe|sap|servicenow|netapp|nutanix|oracle|ibm|dell|honeywell|siemens|bosch|swiggy|zomato|delhivery|makemytrip|walmart|shopify|uber|twilio|datadog|crowdstrike|snowflake|zscaler|paypal|ebay|atlassian|vmware|qualcomm|amazon|flipkart|myntra|paytm|freshworks|philips|samsung|intel|sap labs|nvidia|amd|chargerbee|chargebee|postman|zoho", re.I)

def ensure_login():
    b.navigate("https://www.linkedin.com/feed/"); time.sleep(4)
    t = snap()
    if "Sign in" in t[:1500]:
        print("🔐 logging in…")
        b.navigate("https://www.linkedin.com/login"); time.sleep(5)
        t = snap()
        e = p = s = None
        for _ in range(3):
            e = ref_of(t, r'textbox "Email or phone"')
            p = ref_of(t, r'textbox "Password"')
            s = ref_of(t, r'button "Sign in"')
            if e and p and s: break
            time.sleep(3); t = snap()
        if not (e and p and s):
            print("❌ login form not found:"); print(t[:600]); return False
        b._call("browser_type", {"target": e, "text": A["email"]}); time.sleep(0.3)
        b._call("browser_type", {"target": p, "text": A["linkedin_pass"]}); time.sleep(0.3)
        b._call("browser_click", {"target": s}); time.sleep(7)
        t = snap()
        ok = "/feed" in t or "Feed" in t
        print(f"  {'✅ logged in' if ok else '❌ login failed'}")
        return ok
    print("  already logged in"); return True

def find_jobs(keyword):
    url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location=Bangalore&f_EA=true&f_TPR=r604800"
    b.navigate(url); time.sleep(6)
    t = snap()
    # job cards: title link + company link + URL
    jobs = []
    import re as _re
    print("  all jobs/view urls:", len(_re.findall(r"jobs/view", t)))
    for m in re.finditer(r'link "([^"]+)"[^\[]*\[ref=(\w+)\][^\n]*\n\s*- /url: (https?://[^\s]*jobs/view[^\s]+)', t):
        title, ref, url2 = m.group(1), m.group(2), m.group(3)
        jobs.append((title, ref, url2))
    # companies appear as separate links right after; grab from full text near ref
    return jobs, t

def apply(job_ref, url):
    """Apply once, with a tracker gate and a CAPTCHA/user-stop gate."""
    jid = _job_id(url)
    applied_ids = load_applied_ids()
    if not jid or jid in applied_ids:
        print(f"    ⏭️ SKIP duplicate/unknown job ID: {jid or url}")
        return False
    b.navigate("https://www.linkedin.com" + url); time.sleep(4)
    t = snap()
    apply_ref = ref_of(t, r'button "Easy Apply"')
    if not apply_ref:
        print(f"    no Easy Apply (maybe Applied already/closed): {url[:50]}"); return False
    b._call("browser_click", {"target": apply_ref}); time.sleep(3)
    # next/submit walking
    for step in range(8):
        t = snap()
        if re.search(r"captcha|recaptcha|hcaptcha|verify you are human|security check", t, re.I):
            print("    🛑 CAPTCHA/security check: user must solve it in the visible browser")
            return False
        sub = ref_of(t, r'button "Submit application"')
        nxt = ref_of(t, r'button "Next"')
        if sub:
            b._call("browser_click", {"target": sub}); time.sleep(3)
            t2 = snap()
            ack = bool(re.search(r"application (was )?sent|application submitted|keep track of your application", t2, re.I))
            if ack:
                record_attempt("LinkedIn employer pending", "LinkedIn job", url, proof=t2[-500:])
            print(f"    {'✅' if ack else '⚠️'} SUBMITTED ACK: {ack}; tracker updated only as awaiting-email")
            return ack
        if nxt:
            b._call("browser_click", {"target": nxt}); time.sleep(3)
            continue
        print("    stuck at step", step); print(t[-700:]); return False
    return False

def main():
    ensure_login()
    results = []
    for kw in ["SDET", "QA%20Engineer"]:
        jobs, t = find_jobs(kw)
        print(f"\n=== {kw}: {len(jobs)} links ===")
        for title, ref, url in jobs:
            if LISTED.search(title):
                print(f"  LISTED: [{ref}] {title[:55]} {url[-30:]}")
                results.append((title, ref, url))
    print(f"\n🎯 {len(results)} listed-company jobs — applying…")
    done = []
    for title, ref, url in results[:8]:
        print(f"\n▶ {title[:50]}")
        ok = apply(ref, url)
        if ok: done.append({"company": title.split(" at ")[-1][:30], "title": title[:50], "date": "2026-08-12"})
    json.dump(done, open("config/li_listed_applied.json","w"), indent=1)
    print(f"\nDONE: {len(done)} applied -> config/li_listed_applied.json")

if __name__ == "__main__":
    main()
