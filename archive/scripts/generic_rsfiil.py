#!/usr/bin/env python3
"""acme-select_rsfiil.py — set AcmeSelect GH react-selects (country/location/start) via ctl rs_pick."""
import json, socket, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def ctl(cmd, timeout=120, wait=0.0):
    s = socket.create_connection(("127.0.0.1", 9000), timeout=timeout)
    s.sendall((json.dumps(cmd) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        c = s.recv(65536)
        if not c: break
        buf += c
    s.close(); time.sleep(wait)
    return json.loads(buf.decode())

def rs_pick(qid, target, retries=4):
    ctl({"op": "eval", "js": f"() => {{ const i = document.getElementById('{qid}'); if (i) i.focus(); }}"}, wait=0.4)
    ctl({"op": "keys", "keys": "Meta+A"}); ctl({"op": "keys", "keys": "Backspace"}); time.sleep(0.3)
    ctl({"op": "htype", "value": target[:6]})
    for _ in range(retries):
        time.sleep(2)
        r = ctl({"op": "eval", "js": f"() => {{ const menus=[...document.querySelectorAll('[class*=select__menu]')]; for(const m of menus){{ const o=[...m.querySelectorAll('[class*=option]')]; const t=o.find(x=>x.innerText.trim().toLowerCase()==='{target.lower()}')||o.find(x=>x.innerText.includes('{target}')); if(t){{ t.click(); return 'ok'; }} }} return 'none:'+menus.length; }}"})
        if r.get("result") == "ok":
            return True
    return False

for qid, target in [("country","India"), ("candidate-location","Bengaluru, Karnataka, India")]:
    print(f"{'OK' if rs_pick(qid,target) else 'FAIL'} {qid} -> {target}")

# text fields via htype
def hfill(qid, val):
    ctl({"op":"eval","js":f"() => {{ const i=document.getElementById('{qid}'); if(i) i.focus(); }}"}, wait=0.3)
    ctl({"op":"keys","keys":"Meta+A"}); ctl({"op":"keys","keys":"Backspace"})
    ctl({"op":"htype","value":val})
    return True
for qid, val in [("phone","0000000000"), ("candidate-location-0","")]:
    pass
print("done")
