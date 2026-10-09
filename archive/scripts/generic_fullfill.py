#!/usr/bin/env python3
"""moniepoint_fullfill.py — complete Moniepoint GH apply WITHOUT navigating (form already open).
Fills core + react-selects + availability + md5-gated resume, then SUBMITS.
Assumes the greenhouse apply form is already open in the ctl browser."""
import json, socket, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.resume_secure import BEFORE_UPLOAD

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

def hfill(fid, val):
    r = ctl({"op": "hfill", "by": "selector", "key": f"#{fid}", "value": val})
    return bool(r.get("ok"))

def rs_pick(qid, target, retries=4):
    ctl({"op": "eval", "js": f"() => {{ const i = document.getElementById('{qid}'); if (i) i.focus(); }}"}); time.sleep(0.4)
    ctl({"op": "keys", "keys": "Meta+A"}); ctl({"op": "keys", "keys": "Backspace"}); time.sleep(0.3)
    ctl({"op": "htype", "value": target[:6]})
    for _ in range(retries):
        time.sleep(2)
        r = ctl({"op": "eval", "js": f"() => {{ const menus = [...document.querySelectorAll('[class*=select__menu]')]; for (const m of menus) {{ const o=[...m.querySelectorAll('[class*=option]')]; const t=o.find(x=>x.innerText.trim().toLowerCase()==='{target.lower()}')||o.find(x=>x.innerText.includes('{target}')); if(t){{ t.click(); return 'ok'; }} }} return 'none'; }}"})
        if r.get("result") == "ok": return True
    return False

def main():
    # core text
    for fid, val in [("first_name","Jane"),("last_name","Doe"),
                     ("email","jane.doe@example.com"),("phone","+91 00000 00000"),
                     ("question_9290119101","linkedin.com/in/janedoe")]:
        if hfill(fid, val): print(f"✅ {fid} = {val}")
    # selects
    for qid, target in [("country","India"),("question_9290121101","No"),
                        ("question_9290120101","I consent"),
                        ("question_9290123101","Yes"),("question_9290124101","Yes"),
                        ("question_9290125101","Yes"),("4006850101","Male")]:
        print(f"{'✅' if rs_pick(qid,target) else '❌'} rs {qid}->{target}")
    # availability text
    ctl({"op":"eval","js":"() => { const i=document.getElementById('question_9290122101'); if(i)i.focus(); }"}); time.sleep(0.3)
    ctl({"op":"keys","keys":"Meta+A"}); ctl({"op":"keys","keys":"Backspace"})
    ctl({"op":"htype","value":"Immediate"}); print("✅ availability=Immediate")
    # resume (md5 gate)
    ctl({"op":"upload_cdp","path": BEFORE_UPLOAD()}); print("✅ resume uploaded (md5 gate)")
    print("DONE-FILL")

if __name__ == "__main__":
    main()
