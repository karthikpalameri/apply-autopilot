#!/usr/bin/env python3
"""moniepoint_selffill.py — fill Moniepoint GH required react-selects via ctl rs_pick."""
import json, socket, time

def ctl(cmd, timeout=120, wait=0.0):
    s = socket.create_connection(("127.0.0.1", 9000), timeout=timeout)
    s.sendall((json.dumps(cmd) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        c = s.recv(65536)
        if not c: break
        buf += c
    s.close()
    time.sleep(wait)
    return json.loads(buf.decode())

def rs_pick(qid, target, retries=4):
    ctl({"op": "eval", "js": f"() => {{ const i = document.getElementById('{qid}'); if (i) i.focus(); return 1; }}"})
    time.sleep(0.4)
    ctl({"op": "keys", "keys": "Meta+A"}); ctl({"op": "keys", "keys": "Backspace"})
    time.sleep(0.3)
    ctl({"op": "htype", "value": target[:6]})
    for _ in range(retries):
        time.sleep(2)
        r = ctl({"op": "eval", "js": f"() => {{ const menus = [...document.querySelectorAll('[class*=select__menu]')]; for (const m of menus) {{ const o = [...m.querySelectorAll('[class*=option]')]; const t = o.find(x => x.innerText.trim().toLowerCase() === '{target.lower()}') || o.find(x => x.innerText.includes('{target}')); if (t) {{ t.click(); return 'ok'; }} }} return 'none'; }}"})
        if r.get("result") == "ok":
            return True
    return False

FILLS = [
    ("question_9290120101", "I consent"),       # NDPA Consent
    ("question_9290121101", "No"),              # previously employed by Moniepoint (re-set)
    ("question_9290123101", "Yes"),             # build custom test frameworks
    ("question_9290124101", "Yes"),             # integrating testing into CI/CD
    ("question_9290125101", "Yes"),             # writing robust automated tests
    ("4006850101", "Male"),                    # gender
]

def main():
    print("filling moniepoint required selects + text…", flush=True)
    # availability is a plain text input
    ctl({"op": "eval", "js": "() => { const i = document.getElementById('question_9290122101'); if (i) { i.focus(); return 1; } return 0; }"})
    time.sleep(0.3)
    ctl({"op": "keys", "keys": "Meta+A"}); ctl({"op": "keys", "keys": "Backspace"})
    ctl({"op": "htype", "value": "Immediate"})
    print("  ℹ️ availability (text) -> Immediate", flush=True)
    for qid, target in FILLS:
        ok = rs_pick(qid, target)
        print(f"  {'✅' if ok else '❌'} {qid} -> {target}", flush=True)
    print("done", flush=True)

if __name__ == "__main__":
    main()
