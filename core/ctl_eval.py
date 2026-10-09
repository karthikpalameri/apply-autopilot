#!/usr/bin/env python3
"""ctl_eval.py — send JS from a file to the CloakBrowser ctl server (:9000)."""
import json, socket, sys, time

def ctl(cmd, wait=0.0):
    s = socket.create_connection(("127.0.0.1", 9000), timeout=120)
    s.sendall((json.dumps(cmd) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        chunk = s.recv(65536)
        if not chunk:
            break
        buf += chunk
    s.close()
    time.sleep(wait)
    return json.loads(buf.decode() or "{}")

if __name__ == "__main__":
    js = open(sys.argv[1]).read()
    wait = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    print(json.dumps(ctl({"op": "eval", "js": js}, wait), indent=1, default=str))
