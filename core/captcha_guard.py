"""Fail-closed CAPTCHA detection for application flows.

A detected challenge is a hard stop: leave the headed page open for the user and
never solve, bypass, or submit the application from automation.
"""
import re

CAPTCHA_TEXT = re.compile(
    r"captcha|re\s*-?\s*captcha|h\s*-?\s*captcha|"
    r"verify\s+you\s+are\s+human|are\s+you\s+a\s+robot|security\s+check",
    re.IGNORECASE,
)

CAPTCHA_PROBE_JS = r"""() => {
  const markers = [
    'iframe[src*="recaptcha" i]', 'iframe[src*="hcaptcha" i]',
    'iframe[src*="arkoselabs" i]', 'iframe[title*="captcha" i]',
    '[id*="captcha" i]', '[class*="captcha" i]', '[data-testid*="captcha" i]',
    '[data-sitekey]', 'textarea[name*="captcha" i]', 'textarea[id*="captcha" i]',
    '[aria-label*="captcha" i]', '[title*="captcha" i]'
  ].join(',');
  const text = document.body ? document.body.innerText : '';
  return document.querySelector(markers) ||
    /captcha|re\s*-?\s*captcha|h\s*-?\s*captcha|verify\s+you\s+are\s+human|are\s+you\s+a\s+robot|security\s+check/i.test(text)
    ? 'CAPTCHA' : 'CLEAR';
}"""


def text_has_captcha(text):
    """Return True when accessible/visible page text indicates a challenge."""
    return bool(CAPTCHA_TEXT.search(str(text or "")))


def page_has_captcha(evaluate, visible_text=""):
    """Detect page text/DOM markers; fail closed if the browser probe fails.

    ``evaluate`` must accept a JavaScript function string and return its result.
    Only the exact ``CLEAR`` result permits the caller to continue.
    """
    if text_has_captcha(visible_text):
        return True
    try:
        result = evaluate(CAPTCHA_PROBE_JS)
    except Exception:
        return True
    return str(result or "").strip().upper() != "CLEAR"
