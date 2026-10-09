#!/usr/bin/env python3
"""see.py — screenshot + OCR vision. Usage: see.py [name] — prints OCR text (~3s)."""
import json, socket, subprocess, sys
from PIL import Image

def ctl(cmd, timeout=15):
    s = socket.create_connection(("127.0.0.1", 9000), timeout=timeout)
    s.sendall((json.dumps(cmd) + "\n").encode())
    b = b""
    while not b.endswith(b"\n"):
        c = s.recv(65536)
        if not c: break
        b += c
    s.close()
    return json.loads(b.decode())

name = sys.argv[1] if len(sys.argv) > 1 else "view"
ctl({"op": "snap", "name": name, "full": False})
p = f"logs/{name}.png"
txt = subprocess.run(["tesseract", p, "-", "--psm", "6"],
                     capture_output=True, text=True, timeout=15).stdout
print(txt[:2500])
