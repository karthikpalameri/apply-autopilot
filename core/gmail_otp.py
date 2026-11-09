#!/usr/bin/env python3
"""core/gmail_otp.py — READ-ONLY Gmail OTP/code reader via IMAP (stdlib only, no OAuth).
Reads the latest N messages, extracts 6-8 digit verification codes. NEVER writes/sends.
Usage: .venv/bin/python core/gmail_otp.py [count] [--subject KEYWORD]
Config: reads EMAIL/PW from config/user.json (gmail_user / gmail_app_pw) or env GMAIL_USER/GMAIL_PW."""
import sys, os, re, imaplib, email, subprocess
from email.header import decode_header

from core.logger import log

def keychain(service, account=None):
    """Read a secret from the macOS Keychain. Single source for all passwords.
    Passwords must NEVER live in config/user.json (gitignored but still plaintext)."""
    cmd = ["security", "find-generic-password", "-s", service, "-w"]
    if account:
        cmd += ["-a", account]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""

def load_creds():
    """Gmail user + app password. Order: Keychain -> config/user.json -> env.
    NOTE: Gmail IMAP rejects normal account passwords; only a 16-char APP password works."""
    user = os.environ.get("GMAIL_USER", "")
    pw = os.environ.get("GMAIL_PW", "")
    if not pw:
        pw = keychain("gmail", user or None)
    try:
        import json
        _cfgpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "user.json")
        with open(_cfgpath) as f:
            cfg = json.load(f)
        user = user or cfg.get("gmail_user", "")
        pw = pw or cfg.get("gmail_app_pw", "")
    except (OSError, ValueError) as e:
        log.debug("gmail_otp: config/user.json not usable (%s) — using Keychain/env only", e)
    return user, pw

def dec(s):
    if not s: return ""
    parts = decode_header(s)
    return "".join(p.decode(enc or "utf-8") if isinstance(p, bytes) else p for p, enc in parts)

# --- Browser-tab Gmail (primary; no password needed — profile holds the session) ---
GMAIL_URL = "https://mail.google.com/mail/u/0/"

# Run inside the page via MCP browser_run_code_unsafe. Returns row texts, newest first.
JS_LIST_CODES = """
[...document.querySelectorAll('tr')]
  .map(t => t.innerText.replace(/\\s+/g,' ').trim())
  .filter(t => /security code|verification code|otp/i.test(t))
"""

# Run inside the page after clicking the row. Returns the opened message body.
JS_READ_BODY = "(document.querySelector('.a3s') || {}).innerText || ''"

RE_CODE = re.compile(r"\b([A-Z0-9]{8})\b")          # Greenhouse security-input-0..7
RE_DIGITS = re.compile(r"\b(\d{6,8})\b")            # classic OTP

def extract_codes(text):
    """Pull candidate codes from a message body. Pure — no I/O, testable."""
    return {"alnum8": RE_CODE.findall(text or ""), "digits": RE_DIGITS.findall(text or "")}

def read_latest(count=3, subject_kw=None):
    user, pw = load_creds()
    if not user or not pw:
        print("❌ no Gmail creds. Gmail IMAP needs a 16-char APP password, not your login password.")
        print("   Create: https://myaccount.google.com/apppasswords  |  Store: security add-generic-password -s gmail -a <email> -w <app-pw>")
        return []
    M = imaplib.IMAP4_SSL("imap.gmail.com")
    try:
        M.login(user, pw)
    except imaplib.IMAP4.error as e:
        log.error("gmail_otp: login failed for %s — %s", user, e)
        print(f"❌ Gmail rejected the password for {user}.")
        print("   Gmail IMAP does NOT accept normal account passwords — it needs a 16-char APP password.")
        print("   Create one: https://myaccount.google.com/apppasswords (requires 2-Step Verification on)")
        print(f"   Then: security add-generic-password -s gmail -a {user} -w '<16-char-app-pw>' -U")
        return []
    M.select("INBOX")
    typ, data = M.search(None, "ALL")
    ids = data[0].split()[-count:]  # latest N
    out = []
    for mid in reversed(ids):
        typ, msg = M.fetch(mid, "(RFC822)")
        # IMAP returns None (or a bare status tuple) for a message that vanished
        # between SEARCH and FETCH. Slicing it used to raise TypeError and abort
        # the whole OTP read; skip that one message instead.
        if not msg or not isinstance(msg[0], tuple) or len(msg[0]) < 2:
            log.debug("gmail_otp: FETCH returned no body for mid %r — skipped", mid)
            continue
        m = email.message_from_bytes(msg[0][1])
        subj = dec(m.get("Subject"))
        if subject_kw and subject_kw.lower() not in subj.lower():
            continue
        # body
        body = ""
        if m.is_multipart():
            for part in m.walk():
                if part.get_content_type() == "text/plain":
                    # get_payload(decode=True) returns None for a non-simple part;
                    # .decode() on that raised AttributeError and killed the OTP read.
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body += payload.decode("utf-8", "ignore")
        else:
            payload = m.get_payload(decode=True)
            body = payload.decode("utf-8", "ignore") if isinstance(payload, bytes) else ""
        # extract codes: 6-8 digit standalone or "code is XXXX"
        codes = re.findall(r'\b(\d{6,8})\b', body)
        code_ctx = re.findall(r'(?:code|otp|verification)[^.\n]{0,40}?\b(\d{6,8})\b', body, re.I)
        out.append({"from": dec(m.get("From"))[:40], "subject": subj[:60],
                    "codes": codes[:3], "code_ctx": code_ctx[:2],
                    "date": m.get("Date", "")[:22]})
    M.logout()
    return out

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    kw = sys.argv[sys.argv.index("--subject")+1] if "--subject" in sys.argv else None
    for m in read_latest(n, kw):
        print(f"[{m['date']}] {m['from']} | {m['subject']}")
        if m["code_ctx"]: print(f"   ⭐ context code: {m['code_ctx']}")
        if m["codes"]: print(f"   codes: {m['codes']}")
