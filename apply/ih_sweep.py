#!/usr/bin/env python3
"""ih_sweep.py <url>... — InstaHyre one-click apply: open job -> Apply -> verify 'Application sent'."""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ctl import call
from core.ui import ev, until
from core.logger import log  # single owner (was bare print)

def ctl(cmd, timeout=30):
    return call(cmd, timeout=timeout)


def apply_one(url):
    ctl({"op": "navigate", "url": url})
    # wait for the page to render instead of a flat 8s
    until(lambda: ev("() => document.body.innerText.length > 200"), timeout=8, interval=0.4,
          what="instahyre page")
    # scroll to load content
    ev("() => { window.scrollTo(0, 300); return 1; }")
    until(lambda: ev("() => document.body.innerText.length > 500"), timeout=8, interval=0.3,
          what="instahyre scroll")
    r = ev("() => { const t=document.body.innerText.replace(/\\s+/g,' '); const applied=/Application sent/i.test(t); const bs=[...document.querySelectorAll('button,a')].filter(x=>x.offsetParent&&/^Apply$/.test((x.innerText||'').trim())); return JSON.stringify({applied, applyCount: bs.length, snip:t.slice(0,120)}); }")
    d = json.loads(r or "{}")
    if d.get("applied"):
        return "already-applied"
    snip = d.get("snip", "") or ""
    if re.search(r"captcha|recaptcha|hcaptcha|verify you are human|security check", snip, re.I):
        log.warning("STOP: CAPTCHA/security check on %s; user must solve it in the visible browser", url[:80])
        return "captcha-stop"
    if d.get("applyCount", 0) > 0:
        ev("() => { const bs=[...document.querySelectorAll('button,a')].filter(x=>x.offsetParent&&/^Apply$/.test((x.innerText||'').trim())); if(bs.length) bs[bs.length-1].click(); return 1; }")
        until(lambda: ev("() => /Application sent/i.test(document.body.innerText)"),
              timeout=8, interval=0.4, what="instahyre application sent")
        st = ev("() => { const t=document.body.innerText.replace(/\\s+/g,' '); return JSON.stringify({applied:/Application sent/i.test(t), snip:t.slice(0,150)}); }")
        return st
    return "no-apply"

def main():
    urls = sys.argv[1:]
    for u in urls:
        r = apply_one(u)
        log.info("%s -> %s", u[-45:], r)

main()
