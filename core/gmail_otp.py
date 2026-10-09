#!/usr/bin/env python3
"""core/gmail_otp.py — READ-ONLY Gmail OTP/code reader via IMAP (stdlib only, no OAuth).
Reads the latest N messages, extracts 6-8 digit verification codes. NEVER writes/sends.
Usage: .venv/bin/python core/gmail_otp.py [count] [--subject KEYWORD]
Config: reads EMAIL/PW from config/user.json (gmail_user / gmail_app_pw) or env GMAIL_USER/GMAIL_PW."""
import sys, os, re, imaplib, email
from email.header import decode_header

def load_creds():
    try:
        import json
        cfg = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "user.json")))
        user = cfg.get("gmail_user") or os.environ.get("GMAIL_USER", "")
        pw = cfg.get("gmail_app_pw") or os.environ.get("GMAIL_PW", "")
        return user, pw
    except Exception:
        return os.environ.get("GMAIL_USER", ""), os.environ.get("GMAIL_PW", "")

def dec(s):
    if not s: return ""
    parts = decode_header(s)
    return "".join(p.decode(enc or "utf-8") if isinstance(p, bytes) else p for p, enc in parts)

def read_latest(count=3, subject_kw=None):
    user, pw = load_creds()
    if not user or not pw:
        print("❌ no Gmail creds (config/user.json gmail_user/gmail_app_pw or GMAIL_USER/GMAIL_PW)"); return []
    M = imaplib.IMAP4_SSL("imap.gmail.com")
    M.login(user, pw)
    M.select("INBOX")
    typ, data = M.search(None, "ALL")
    ids = data[0].split()[-count:]  # latest N
    out = []
    for mid in reversed(ids):
        typ, msg = M.fetch(mid, "(RFC822)")
        m = email.message_from_bytes(msg[0][1])
        subj = dec(m.get("Subject"))
        if subject_kw and subject_kw.lower() not in subj.lower():
            continue
        # body
        body = ""
        if m.is_multipart():
            for part in m.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode("utf-8", "ignore")
        else:
            body = m.get_payload(decode=True).decode("utf-8", "ignore")
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
