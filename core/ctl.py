#!/usr/bin/env python3
"""ctl.py — the ONE owner of the :9000 ctl socket call.

Eleven scripts used to carry a private copy of the same 9-line
`socket.create_connection(("127.0.0.1", 9000))` block, with drifting timeouts
(2/15/20/30/120 s). Import `call()` instead of pasting it again.

CLI usage:
  python ctl.py '{"op": "status"}'
  python ctl.py '{"op": "navigate", "url": "https://..."}'
  echo '{"op":"status"}' | python ctl.py
"""

import json
import socket
import sys
import time

HOST, PORT = "127.0.0.1", 9000
DEFAULT_TIMEOUT = 120
MAX_RESPONSE_BYTES = 200_000_000


def call(cmd, timeout=DEFAULT_TIMEOUT):
    """Send one command to the ctl server, return the parsed response dict."""
    s = socket.create_connection((HOST, PORT), timeout=timeout)
    try:
        s.sendall((json.dumps(cmd) + "\n").encode())
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            if len(buf) > MAX_RESPONSE_BYTES:
                break
    finally:
        s.close()
    return json.loads(buf.decode() or "{}")


def call_wait(cmd, wait=0.0):
    """call() then optionally sleep — some scripts wait for the page to settle.

    Two files had pasted this same 4-line shim; it lives here so the socket call
    and its settle delay stay in one place.
    """
    resp = call(cmd)
    if wait:
        time.sleep(wait)
    return resp


def main():
    cmd = json.loads(sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read())

    resp = call(cmd)

    # Pretty print for humans; keep JSON machine-readable for scripts
    if resp.get("ok") is False:
        print("\u274c ERROR:", resp.get("error"))
        if resp.get("trace"):
            print(resp["trace"][-800:])
        sys.exit(1)
    print(json.dumps(resp, indent=1, default=str))


if __name__ == "__main__":
    main()
