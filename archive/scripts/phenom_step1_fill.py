#!/usr/bin/env python3
"""phenom_step1_fill.py — full fill of Phenom step 1 (trusted selects + real keystrokes)."""
import json, socket, time, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.answers import A

HOST, PORT = "127.0.0.1", 9000

def ctl(cmd, wait=0.0):
    s = socket.create_connection((HOST, PORT), timeout=90)
    s.sendall((json.dumps(cmd) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        c = s.recv(65536)
        if not c:
            break
        buf += c
    s.close()
    time.sleep(wait)
    return json.loads(buf.decode() or "{}")

def ev(js, wait=0.2):
    return ctl({"op": "eval", "js": js}, wait).get("result")

def type_field(fid, val):
    ev(f"(() => {{ const el=document.getElementById('{fid}'); el.scrollIntoView({{block:'center'}}); const r=el.getBoundingClientRect(); return {{x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)}} }})()", 0.3)
    # clear via JS first (guaranteed), then real typing
    ev(f"(() => {{ const el=document.getElementById('{fid}'); const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set; s.call(el,''); el.dispatchEvent(new Event('input',{{bubbles:true}})); el.dispatchEvent(new Event('change',{{bubbles:true}})); return 1 }})()", 0.2)
    r = ev(f"(() => {{ const el=document.getElementById('{fid}'); el.focus(); const r=el.getBoundingClientRect(); return {{x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)}} }})()", 0.2)
    ctl({"op": "mouse_click", "x": r["x"], "y": r["y"]}, 0.3)
    ctl({"op": "htype", "value": val}, 0.4)
    got = ev(f"(() => document.getElementById('{fid}').value)()", 0.2)
    print(f"{fid}: {'OK' if got == val else 'MISMATCH ' + str(got)[:35]}", flush=True)

# 1) selects via Playwright select_option
for sel, val in [("#country", "India"), ("#deviceType", "Mobile")]:
    r = ctl({"op": "select", "by": "selector", "name": sel, "value": val}, 0.5)
    print(f"{sel}: {r.get('ok')} {r.get('value','')}", flush=True)

# country phone code select — inspect options first
opts = ev("(() => { const s=document.getElementById('phoneWidget.countryPhoneCode'); return s? [...s.options].slice(0,5).map(o=>o.text.trim()) : [] })()", 0.2)
print("ccode options:", opts[:3], flush=True)
r = ctl({"op": "select", "by": "selector", "name": "#phoneWidget.countryPhoneCode", "value": "India"}, 0.5)
print("ccode:", r.get("ok"), r.get("value", ""), flush=True)

# 2) text fields — real keystrokes
type_field("cntryFields.firstName", A["first"])
type_field("cntryFields.lastName", A["last"])
type_field("cntryFields.addressLine1", A["address"])
type_field("cntryFields.city", "Bengaluru")
type_field("cntryFields.postalCode", "<postcode>")
type_field("email", A["email"])
type_field("phoneWidget.phoneNumber", A["phone"])

# 3) radio: previous worker = No
ev("(() => { const r=document.getElementById('previousWorker.No'); if(r && !r.checked && r.labels && r.labels[0]) r.labels[0].click(); return r? r.checked : 'MISSING' })()", 0.3)
# 4) consents
for cid in ["emailAgreement", "smsOptIn", "globalprivacy"]:
    ev(f"(() => {{ const c=document.getElementById('{cid}'); if(c && !c.checked && c.labels && c.labels[0]) c.labels[0].click(); return c? c.checked : 'MISSING' }})()", 0.2)

# 5) final verify
state = ev("(() => { const g=id=>{const el=document.getElementById(id); if(!el) return 'MISSING'; if(el.type==='checkbox'||el.type==='radio') return el.checked?'CHECKED':'UNCHECKED'; return el.value||'EMPTY'}; return JSON.stringify({country:g('country'),device:g('deviceType'),ccode:g('phoneWidget.countryPhoneCode'),first:g('cntryFields.firstName'),last:g('cntryFields.lastName'),city:g('cntryFields.city'),pin:g('cntryFields.postalCode'),email:g('email'),phone:g('phoneWidget.phoneNumber'),prevNo:g('previousWorker.No'),prevYes:g('previousWorker.Yes'),ea:g('emailAgreement'),sms:g('smsOptIn'),privacy:g('globalprivacy')}) })()", 0.2)
print("FINAL:", json.dumps(json.loads(state), indent=1))
