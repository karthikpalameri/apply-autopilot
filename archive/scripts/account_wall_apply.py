#!/usr/bin/env python3
"""account_wall_apply.py <jobid> — apply behind an account wall: selects=Yes, eligibility, submit."""
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
    return (ctl({"op": "eval", "js": js}) or {}).get("result")

jid = sys.argv[1]
print(f"🚀 Amazon job {jid}", flush=True)
ctl({"op": "navigate", "url": f"https://www.amazon.jobs/en/jobs/{jid}/"})
time.sleep(6)
ev("() => { const b=[...document.querySelectorAll('a,button')].find(x=>x.offsetParent&&/^Apply now$/.test((x.innerText||'').trim())); if(b){ b.click(); return 1; } return 0; }")
time.sleep(9)
# 1) job-specific selects -> Yes
ev("() => { const sels=[...document.querySelectorAll('select')].filter(s=>s.offsetParent); let n=0; for(const s of sels){ const o=[...s.options].find(o=>o.text.trim()==='Yes'); if(o){ const set=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set; set.call(s,o.value); s.dispatchEvent(new Event('change',{bubbles:true})); n++; } } return n; }")
time.sleep(1.5)
# 2) eligibility radios
ev("() => { const radios=[...document.querySelectorAll('input[type=radio]')].filter(r=>r.offsetParent); const byName={}; for(const rd of radios){ (byName[rd.name]=byName[rd.name]||[]).push(rd); } let n=0; for(const name in byName){ const g=byName[name]; const yes=g.find(r=>/^Yes$/i.test((r.labels&&r.labels[0]?r.labels[0].innerText:'').trim())); const no=g.find(r=>/^No$/i.test((r.labels&&r.labels[0]?r.labels[0].innerText:'').trim())); const never=g.find(r=>/^No/i.test((r.labels&&r.labels[0]?r.labels[0].innerText:'').trim())); let rd=null; if(/APPLIED_TO_AMAZON/.test(name)) rd=yes; else if(/GOVERNMENT/.test(name)) rd=never; else rd=no; if(rd&&!rd.checked&&rd.labels&&rd.labels[0]){ rd.labels[0].click(); n++; } } return n; }")
time.sleep(2)
# 3) follow-up text: company + date
ev("() => { const els=[...document.querySelectorAll('input[type=text]')].filter(e=>e.offsetParent); const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set; for(const el of els){ if(/YYYY-MM/.test(el.placeholder||'')){ if(!el.value){ set.call(el,'2025-11'); el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true})); } } else if(!el.value){ set.call(el,'Amazon'); el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true})); } } return 1; }")
time.sleep(1)
# 4) Continue until review, then Submit
for _ in range(6):
    r = ev("() => { const b=[...document.querySelectorAll('button, a[role=button]')].find(x=>x.offsetParent&&/^Continue$/.test((x.innerText||'').trim())); if(!b) return 'no'; b.click(); return 'continue'; }")
    time.sleep(5)
    t = ev("() => { const t=document.body.innerText.replace(/\\s+/g,' '); return JSON.stringify({review:/Review application/.test(t), sub:/^Submit application$/.test([...document.querySelectorAll('button')].filter(x=>x.offsetParent).map(x=>(x.innerText||'').trim()).find(x=>/submit/i.test(x))||'')}); }")
    d = json.loads(t or "{}")
    if d.get("review") or d.get("sub"):
        break
r = ev("() => { const b=[...document.querySelectorAll('button')].find(x=>x.offsetParent&&/^Submit application$/.test((x.innerText||'').trim())); if(!b) return 'no'; b.click(); return 'submitted'; }")
print("submit:", r, flush=True)
time.sleep(10)
u = ev("() => location.href")
ok = "result=success" in (u or "")
print("RESULT:", "SUBMITTED ✓" if ok else f"CHECK {u}", flush=True)
