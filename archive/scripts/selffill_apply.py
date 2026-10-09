#!/usr/bin/env python3
"""selffill_apply.py — fill GH self-id/ack/right-to-work selects via ctl keys/htype.
Inline rs_pick (the proven greenhouse react-select technique)."""
import sys, os, json, socket, time

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
    ("question_68802923", "I acknowledge"),
    ("gender", "Man"),
    ("hispanic_ethnicity", "No"),
    ("veteran_status", "I am not a protected veteran"),
    ("disability_status", "No, I do not have a disability"),
]

def main():
    print("filling required selects via ctl rs_pick…", flush=True)
    # right-to-work is a plain text input -> type India directly
    ctl({"op": "eval", "js": "() => { const i = document.getElementById('question_68802921'); if (i) { i.focus(); return 1; } return 0; }"})
    time.sleep(0.3)
    ctl({"op": "keys", "keys": "Meta+A"}); ctl({"op": "keys", "keys": "Backspace"})
    ctl({"op": "htype", "value": "India"})
    print("  ℹ️ right-to-work (text) -> typed India", flush=True)
    for qid, target in FILLS:
        ok = rs_pick(qid, target)
        print(f"  {'✅' if ok else '❌'} {qid} -> {target}", flush=True)
    print("done", flush=True)

if __name__ == "__main__":
    main()
