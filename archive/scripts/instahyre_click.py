#!/usr/bin/env python3
"""instahyre_click.py — InstaHyre recommended-list click-through apply: card -> overlay -> Apply -> verify."""
import json, socket, time

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

def main():
    ctl({"op": "navigate", "url": "https://www.instahyre.com/candidate/opportunities/?matching=true"})
    time.sleep(9)
    for i in range(20):
        # read the current card (first visible unapplied QA card)
        r = ev("""() => {
          const cards=[...document.querySelectorAll('[class*=job]')].filter(c=>c.offsetParent&&/QA|SDET|Test|Quality|Automation/i.test(c.innerText||''));
          const applied=/Application sent/.test(document.body.innerText);
          return JSON.stringify({cards: cards.length, applied});
        }""")
        d = json.loads(r or "{}")
        if d.get("applied"):
            print(f"[{i}] already applied state", flush=True)
            break
        # click the first QA card
        r = ev("""() => {
          const cards=[...document.querySelectorAll('[class*=job]')].filter(c=>c.offsetParent&&/QA|SDET|Test|Quality|Automation/i.test(c.innerText||''));
          if(!cards.length) return 'no-cards';
          const t=cards[0];
          const title=(t.innerText||'').replace(/\\s+/g,' ').trim().slice(0,50);
          t.click();
          return title;
        }""")
        print(f"[{i}] card: {r}", flush=True)
        time.sleep(4)
        # click Apply in the overlay
        r = ev("""() => {
          const b=[...document.querySelectorAll('button,a')].find(x=>x.offsetParent&&/^Apply$|^Apply now$/.test((x.innerText||'').trim()));
          if(!b) return 'no-apply';
          b.click(); return 'clicked';
        }""")
        print(f"   apply: {r}", flush=True)
        time.sleep(8)
        # verify
        st = ev("() => { const t=document.body.innerText.replace(/\\s+/g,' '); return JSON.stringify({sent:/Application sent/.test(t), t:t.slice(0,100)}); }")
        print(f"   {st}", flush=True)
        # close the overlay if not applied
        ev("""() => {
          const t=document.body.innerText;
          if(!/Application sent/.test(t)){
            const close=[...document.querySelectorAll('[class*=close], [class*=times], [aria-label=Close]')].filter(x=>x.offsetParent);
            if(close.length) close[0].click();
          }
          return 1;
        }""")
        time.sleep(3)
    print("DONE", flush=True)

main()
