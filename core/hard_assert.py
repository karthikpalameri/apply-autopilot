"""hard_assert.py — AFTER EVERY SUBMIT: verify the positive message or FAIL.

Usage:
    from core.hard_assert import assert_applied
    proof = assert_applied(b, "AcmeOne")   # raises AssertionError if no positive msg

Positive patterns (per ATS):
    LinkedIn EA:  "Your application was sent to <Co>", "Applied tab of My Jobs"
    Greenhouse:   "Thank you for applying", "Thank you for your interest", "We have successfully received"
    Lever:        "/thanks" page
    Workday:      "/jobTasks/completed/application", "Application Submitted"
    Generic:      "application has been received", "application was submitted"
"""
import sys, os, re, time, json

POSITIVE = [
    r"Your application was sent to",
    r"Your application was successfully submitted",
    r"Applied tab of My Jobs",
    r"Thank you for applying",
    r"Thank you for your interest",
    r"We have successfully received",
    r"application (has been|was) (received|submitted)",
    r"Application Submitted",
    r"/jobTasks/completed/application",
]

def ocr_text(b, shot=None):
    """Screenshot + tesseract = the ground truth."""
    b._call("browser_take_screenshot", {})
    time.sleep(2)
    import glob
    shots = sorted(glob.glob(".playwright-mcp/*.png"), key=os.path.getmtime)
    if not shots:
        return ""
    import subprocess
    r = subprocess.run(["tesseract", shots[-1], "-"], capture_output=True, text=True)
    return r.stdout

def assert_applied(b, company, read_dom=True):
    """HARD ASSERT: read the page (DOM + OCR) → must find the positive message.
    Returns the exact proof text. Raises AssertionError otherwise (NOT applied)."""
    body = ""
    if read_dom:
        try:
            r = b._call("browser_run_code_unsafe", {"code": "async (page) => { return await page.locator('body').innerText(); }"})
            res = r.get("result") if isinstance(r, dict) else r
            body = res if isinstance(res, str) else "".join(c.get("text", "") for c in res.get("content", []) if isinstance(c, dict)) if isinstance(res, dict) else ""
        except Exception:
            body = ""
    ocr = ocr_text(b)
    combined = body + "\n" + ocr
    for pat in POSITIVE:
        m = re.search(pat, combined, re.I)
        if m:
            proof = m.group(0).strip()
            print(f"[HARD-ASSERT] {company}: PASS — proof='{proof}'")
            return proof
    print(f"[HARD-ASSERT] {company}: FAIL — no positive message found (NOT counted)")
    print("  DOM tail:", body[-200:].replace("\n", " ") if body else "?")
    print("  OCR tail:", ocr[-200:].replace("\n", " ") if ocr else "?")
    raise AssertionError(f"{company}: no positive confirmation message (application NOT submitted)")
