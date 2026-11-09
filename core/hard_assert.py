"""hard_assert.py — AFTER EVERY SUBMIT: verify the positive message or FAIL.

Usage:
    from core.hard_assert import assert_applied
    proof = assert_applied(b, "Karix")   # raises AssertionError if no positive msg

Positive patterns (per ATS):
    LinkedIn EA:  "Your application was sent to <Co>", "Applied tab of My Jobs"
    Greenhouse:   "Thank you for applying", "Thank you for your interest", "We have successfully received"
    Lever:        "/thanks" page
    Workday:      "/jobTasks/completed/application", "Application Submitted"
    Generic:      "application has been received", "application was submitted"
"""
import glob, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ocr import available as ocr_available, read as ocr  # single owner (tesseract)
from core.ui import until                                  # single owner (polling)

POSITIVE = [
    r"Your application was sent to",
    r"Your application was successfully submitted",
    r"Applied tab of My Jobs",
    r"Thank you for applying",
    r"Thank you for your application",
    r"Thank you for your interest",
    r"We have successfully received",
    r"application (has been|was) (received|submitted)",
    r"Application Submitted",
    r"/jobTasks/completed/application",
]

def ocr_text(b):
    """Screenshot + OCR = the ground truth for "did the confirmation really render"."""
    if not ocr_available():
        print("[HARD-ASSERT] OCR unavailable (install tesseract); using DOM confirmation")
        return ""
    b._call("browser_take_screenshot", {})
    # the screenshot lands on disk asynchronously; poll instead of a blind 2s
    shots = sorted(glob.glob(".playwright-mcp/*.png"), key=os.path.getmtime)
    until(lambda: sorted(glob.glob(".playwright-mcp/*.png"), key=os.path.getmtime) != shots,
          timeout=5, interval=0.2, what="screenshot file")
    shots = sorted(glob.glob(".playwright-mcp/*.png"), key=os.path.getmtime)
    if not shots:
        return ""
    return ocr(shots[-1])

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
