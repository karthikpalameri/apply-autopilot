#!/usr/bin/env python3
"""ih_sweep.py <url>... — InstaHyre one-click apply: open job -> Apply -> verify 'Application sent'."""
import json, socket, sys, time

def ctl(cmd, timeout=30):
    s = socket.create_connection(("127.0.0.1", 9000), timeout=timeout)
    s.sendall((json.dumps(cmd) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        c = s.recv(65536)
        if not c: break
        buf += c
    s.close()
    return json.loads(buf.decode())

def ev(js):
    return (ctl({"op": "eval", "js": js}) or {}).get("result") or ""

def apply_one(url):
    ctl({"op": "navigate", "url": url})
    time.sleep(8)
    # scroll to load content
    ev("() => { window.scrollTo(0, 300); return 1; }")
    time.sleep(2)
    r = ev("() => { const t=document.body.innerText.replace(/\\s+/g,' '); const applied=/Application sent/i.test(t); const bs=[...document.querySelectorAll('button,a')].filter(x=>x.offsetParent&&/^Apply$/.test((x.innerText||'').trim())); return JSON.stringify({applied, applyCount: bs.length, snip:t.slice(0,120)}); }")
    d = json.loads(r or "{}")
    if d.get("applied"):
        return "already-applied"
    if d.get("applyCount", 0) > 0:
        ev("() => { const bs=[...document.querySelectorAll('button,a')].filter(x=>x.offsetParent&&/^Apply$/.test((x.innerText||'').trim())); if(bs.length) bs[bs.length-1].click(); return 1; }")
        time.sleep(8)
        st = ev("() => { const t=document.body.innerText.replace(/\\s+/g,' '); return JSON.stringify({applied:/Application sent/i.test(t), snip:t.slice(0,150)}); }")
        return st
    return "no-apply"

def main():
    urls = sys.argv[1:]
    for u in urls:
        r = apply_one(u)
        print(f"{u[-45:]} -> {r}", flush=True)

main()
