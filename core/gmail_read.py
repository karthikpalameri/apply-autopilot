#!/usr/bin/env python3
"""core/gmail_read.py — READ-ONLY Gmail reader via the reused browser session (no IMAP, no OAuth).
Reads latest inbox rows + opens an email to extract OTP/verification codes.
Gmail is always read in one reusable Gmail tab, then the application tab is restored.
Usage: python3 core/gmail_read.py [--code] [--subject KEYWORD]"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browser import McpBrowser

b = McpBrowser()
GMAIL_INBOX = "https://mail.google.com/mail/u/0/#inbox"

def snap(): return b.snapshot().get("text","")

def _activate_gmail():
    """Select the one reusable Gmail tab and return the tab to restore."""
    route = b.ensure_gmail_tab()
    b.select_tab(route["gmail_index"])
    return route

def _restore_form(route):
    if route.get("form_index") is not None:
        b.select_tab(route["form_index"])

def read_inbox():
    route = _activate_gmail()
    try:
        b.navigate(GMAIL_INBOX); time.sleep(6)
        t = snap()
        rows = re.findall(r'row "([^"]{5,400})" \[ref=(\w+)\]', t)
        return rows, t
    finally:
        _restore_form(route)

def open_email(row_ref):
    route = _activate_gmail()
    try:
        b._call("browser_click", {"target": row_ref})
        time.sleep(4)
        t = snap()
        # extract the message body + codes
        codes = re.findall(r'\b(\d{6,8})\b', t)
        return t, codes
    finally:
        _restore_form(route)

if __name__ == "__main__":
    rows, t = read_inbox()
    print(f"INBOX: {len(rows)} rows (top of 2,994)")
    kw = sys.argv[sys.argv.index("--subject")+1] if "--subject" in sys.argv else None
    dump_path = None
    if "--dump" in sys.argv:
        i = sys.argv.index("--dump")
        dump_path = sys.argv[i+1] if len(sys.argv) > i+1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "gmail_inbox.txt")
        os.makedirs(os.path.dirname(dump_path), exist_ok=True)
        with open(dump_path, "w") as fh:
            for label, ref in rows:
                fh.write(label + "\n")
        print(f"📤 dumped {len(rows)} inbox rows -> {dump_path}")
    for i, (label, ref) in enumerate(rows[:10]):
        subj = label.split(",")[-3:-1]
        print(f"  [{i}] {label[:95]}")
        if kw and kw.lower() in label.lower():
            print(f"  → opening match ({ref})")
            body, codes = open_email(ref)
            print(f"  CODES FOUND: {codes[:6]}")
            # snippet around the code
            if codes:
                c = codes[0]
                j = body.find(c)
                print(f"  CONTEXT: {body[max(0,j-120):j+60] if j>0 else 'n/a'}")
            break