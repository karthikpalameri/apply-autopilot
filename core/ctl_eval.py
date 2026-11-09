#!/usr/bin/env python3
"""ctl_eval.py — send JS from a file to the CloakBrowser ctl server (:9000)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ctl import call_wait  # single owner (:9000 socket) — DRY

ctl = call_wait  # shared wrapper: call() + settle delay (core.ctl)

if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        js = f.read()
    wait = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    print(json.dumps(ctl({"op": "eval", "js": js}, wait), indent=1, default=str))
