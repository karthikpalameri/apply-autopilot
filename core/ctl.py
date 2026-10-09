#!/usr/bin/env python3
"""ctl.py — send a command to the running CloakBrowser server.

Usage:
  python ctl.py '{"op": "status"}'
  python ctl.py '{"op": "navigate", "url": "https://..."}'
  echo '{"op":"status"}' | python ctl.py
  python ctl.py '{"op": "fill", "by": "name", "key": "email", "value": "x@y.com"}'
"""

import json
import socket
import sys

HOST, PORT = "127.0.0.1", 9000


def main():
    if len(sys.argv) > 1:
        cmd = json.loads(sys.argv[1])
    else:
        cmd = json.loads(sys.stdin.read())

    s = socket.create_connection((HOST, PORT), timeout=120)
    try:
        s.sendall((json.dumps(cmd) + "\n").encode())
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            if len(buf) > 200_000_000:
                break
    finally:
        s.close()
    resp = json.loads(buf.decode() or "{}")

    # Pretty print for humans; keep JSON machine-readable for scripts
    if resp.get("ok") is False:
        print("❌ ERROR:", resp.get("error"))
        if resp.get("trace"):
            print(resp["trace"][-800:])
        sys.exit(1)
    print(json.dumps(resp, indent=1, default=str))


if __name__ == "__main__":
    main()
