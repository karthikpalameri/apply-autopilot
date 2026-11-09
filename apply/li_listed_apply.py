#!/usr/bin/env python3
"""apply/li_listed_apply.py — ONE MCP session: login LinkedIn → find QA Easy Apply jobs at
LISTED product companies → apply. Persists login within the run. Usage: python apply/li_listed_apply.py"""
import sys, os, json, time, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)          # before core imports; was inverted and only worked from the hub CWD

from core.logger import log
from core.dom import ref_of                      # single owner (was copy-pasted here)
from core.applied_ledger import job_ids, record as ledger_record  # dedupe authority
from core.ui import text, until, until_change
from core.browser import McpBrowser
from config.answers import A

APPLIED = os.path.join(ROOT, "scratch", "APPLIED.md")
PROGRESS = os.path.join(ROOT, "config", "progress.json")


def _job_id(url):
    m = re.search(r"/jobs/view/(\\d+)", url or "")
    return m.group(1) if m else None


def load_applied_ids():
    """Fail closed: collect job IDs before any LinkedIn action.

    Ledger (core/applied_ledger.py) is the authority for job ids. APPLIED.md and
    progress.json are kept only so pre-ledger history still blocks a re-apply.
    """
    ids = set(job_ids())
    for path in (APPLIED, PROGRESS):
        try:
            raw = open(path, encoding="utf-8").read()
        except FileNotFoundError:
            continue
        ids.update(re.findall(r"(?:jobs/view/|linkedin[_-][^_\s]+[_-])(\d{7,})", raw))
    return ids


def record_attempt(company, title, url, status="submitted-awaiting-email", proof=""):
    """Record via the ledger (append-only authority). Replaces the progress.json
    row-rewrite that invented company/role and could truncate the tracker."""
    jid = _job_id(url)
    row = ledger_record(company, title, status, url=url, job_id=jid or "",
                        proof=(proof or "")[-500:], source="linkedin-easy-apply")
    log.info("ledger: %s | %s -> %s", company, title,
             "recorded " + status if row else "already present, skipped")
    return bool(row)


b = McpBrowser()
b._rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name":"li-apply","version":"0.1"}})
ACK = re.compile(r"application (was )?sent|application submitted|keep track of your application", re.I)


def wait_ref(pattern, timeout=12):
    """Poll the page until an element matching `pattern` shows up; return its ref.

    Replaces both `time.sleep(N)` and the hand-rolled `for _ in range(3): sleep;
    re-read` loop that preceded it — same ceiling, but it returns the moment the
    element exists instead of waiting out the guess.
    """
    return until(lambda: ref_of(text(b), pattern), timeout=timeout, interval=0.4, what=pattern)

LISTED = re.compile(r"cisco|microsoft|adobe|sap|servicenow|netapp|nutanix|oracle|ibm|dell|honeywell|siemens|bosch|swiggy|zomato|delhivery|makemytrip|walmart|shopify|uber|twilio|datadog|crowdstrike|snowflake|zscaler|paypal|ebay|atlassian|vmware|qualcomm|amazon|flipkart|myntra|paytm|freshworks|philips|samsung|intel|sap labs|nvidia|amd|chargerbee|chargebee|postman|zoho", re.I)

def ensure_login():
    b.navigate("https://www.linkedin.com/feed/")
    t = text(b)
    if "Sign in" in t[:1500]:
        log.info("logging in to LinkedIn")
        b.navigate("https://www.linkedin.com/login")
        t = text(b)
        e = p = s = None
        e = wait_ref(r'textbox "Email or phone"', timeout=12)
        p = wait_ref(r'textbox "Password"', timeout=12)
        s = wait_ref(r'button "Sign in"', timeout=12)
        t = text(b)
        if not (e and p and s):
            log.error("login form not found; page text: %s", t[:600]); return False
        b._call("browser_type", {"target": e, "text": A["email"]}); time.sleep(0.3)
        b._call("browser_type", {"target": p, "text": A["linkedin_pass"]}); time.sleep(0.3)
        b._call("browser_click", {"target": s})
        # sign-in used to be followed by a blind 7s; wait for the feed instead
        until(lambda: "/feed" in text(b) or "Feed" in text(b),
              timeout=20, interval=0.5, what="login redirect")
        t = text(b)
        ok = "/feed" in t or "Feed" in t
        log.info("login %s", "ok" if ok else "FAILED")
        return ok
    log.info("already logged in"); return True

def find_jobs(keyword):
    url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location=Bangalore&f_EA=true&f_TPR=r604800"
    b.navigate(url)
    until(lambda: "jobs/view" in text(b), timeout=8, interval=0.4, what="job results")
    t = text(b)
    # job cards: title link + company link + URL
    jobs = []
    import re as _re
    log.info("job links on page: %d", len(_re.findall(r"jobs/view", t)))
    for m in re.finditer(r'link "([^"]+)"[^\[]*\[ref=(\w+)\][^\n]*\n\s*- /url: (https?://[^\s]*jobs/view[^\s]+)', t):
        title, ref, url2 = m.group(1), m.group(2), m.group(3)
        jobs.append((title, ref, url2))
    # companies appear as separate links right after; grab from full text near ref
    return jobs, t

def apply(_job_ref, url):
    """Apply once, with a tracker gate and a CAPTCHA/user-stop gate.

    `_job_ref` is kept for the call-site signature but the body derives the id
    from `url` via `_job_id()`, so the argument is intentionally unused.
    """
    jid = _job_id(url)
    applied_ids = load_applied_ids()
    if not jid or jid in applied_ids:
        log.info("    SKIP duplicate/unknown job id %s", jid or url)
        return False
    b.navigate("https://www.linkedin.com" + url)
    until(lambda: "Easy Apply" in text(b) or "Applied" in text(b), timeout=8, interval=0.4, what="job page")
    t = text(b)
    apply_ref = ref_of(t, r'button "Easy Apply"')
    if not apply_ref:
        log.info("    no Easy Apply (already applied or closed): %s", url[:80]); return False
    b._call("browser_click", {"target": apply_ref})
    until(lambda: ref_of(text(b), r'button "(Submit application|Next)"'), timeout=8, interval=0.4, what="apply dialog")
    # next/submit walking
    for step in range(8):
        t = text(b)
        if re.search(r"captcha|recaptcha|hcaptcha|verify you are human|security check", t, re.I):
            log.warning("    CAPTCHA/security check on %s: user must solve it in the visible browser", url[:80])
            return False
        sub = ref_of(t, r'button "Submit application"')
        nxt = ref_of(t, r'button "Next"')
        if sub:
            b._call("browser_click", {"target": sub})
            until(lambda: ACK.search(text(b)), timeout=8, interval=0.4, what="submit ack")
            t2 = text(b)
            ack = bool(re.search(r"application (was )?sent|application submitted|keep track of your application", t2, re.I))
            if ack:
                record_attempt("LinkedIn employer pending", "LinkedIn job", url, proof=t2[-500:])
            log.info("    SUBMITTED ACK=%s for %s", ack, url[:80])
            return ack
        if nxt:
            snapshot_before = t
            b._call("browser_click", {"target": nxt})
            until_change(lambda: text(b), snapshot_before, timeout=10, interval=0.4,
                         what=f"step {step} advance")
            continue
        log.warning("    stuck at step %s on %s; page tail: %s", step, url[:80], t[-700:]); return False
    return False

def main():
    ensure_login()
    results = []
    for kw in ["SDET", "QA%20Engineer"]:
        jobs, t = find_jobs(kw)
        log.info("%s: %d links found", kw, len(jobs))
        for title, ref, url in jobs:
            if LISTED.search(title):
                log.info("  LISTED: [%s] %s %s", ref, title[:55], url[-30:])
                results.append((title, ref, url))
    log.info("%d listed-company jobs, applying", len(results))
    done = []
    for title, ref, url in results[:8]:
        log.info("applying: %s", title[:50])
        ok = apply(ref, url)
        if ok: done.append({"company": title.split(" at ")[-1][:30], "title": title[:50], "date": "2026-08-12"})
    json.dump(done, open("config/li_listed_applied.json","w"), indent=1)
    log.info("DONE: %d applied -> config/li_listed_applied.json", len(done))

if __name__ == "__main__":
    main()
