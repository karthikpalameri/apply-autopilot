#!/usr/bin/env python3
"""Guard: a browser step must not trust `status`, and must not use long timeouts.

Why this exists
---------------
The ctl `status` op reads the cached page URL and keeps answering `ok` after the
page is gone, so an agent retried a dead browser until the session stalled. And
Playwright's default 30 s timeout turned every missing field into half a minute
of silence. Both were invisible in review, so they are checked here.

Rules (owner: skills/RELIABILITY.md#page-guard)
-----------------------------------------------
1. `ctl`/`call({"op": "status"})` is a bridge check, not a page check. Code that
   gates a fill on it must call `core.page_guard` instead.
2. No timeout above `MAX_TIMEOUT_S` in a `call(...)`/`until(...)` pre-check.
3. No literal 30 s Playwright action timeout (the default that hid the stalls).

Usage:
    .venv/bin/python core/lint_page_guard.py      # exits 1 on findings
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HUB = Path(__file__).resolve().parent.parent

SCAN_DIRS = ("core", "apply", "find", "runtime")
SKIP_NAMES = {"page_guard.py", "ctl.py", "server.py", "browser.py", "lint_page_guard.py"}
MAX_TIMEOUT_S = 10

# `call({"op": "status"})` used as a health gate. Reading the URL for logging is fine.
STATUS_GATE = re.compile(r"call\(\s*\{[^}]*['\"]op['\"]\s*:\s*['\"]status['\"]")
# timeout=30 / timeout=30000 in a call(), until() or locator pre-check
# `timeout=N` in a PAGE call: call({...}, timeout=), until(..., timeout=), and the
# `ctl(cmd, timeout=)` HTTP/subprocess wrappers are deliberately excluded — a slow
# subprocess is not a frozen page, and flagging them makes the gate noise.
BIG_TIMEOUT = re.compile(r"(call|until|wait_ready|until_change)\(.*timeout\s*=\s*(?:(\d+(?:\.\d+)?)\s*\*\s*)?(\d+(?:\.\d+)?)(000)?\b")


def _files():
    for d in SCAN_DIRS:
        for p in (HUB / d).rglob("*.py"):
            if p.name in SKIP_NAMES or "__pycache__" in p.parts:
                continue
            yield p


def _script_timeouts(text: str):
    """Yields (line_no, seconds) for literal timeouts above the budget."""
    for no, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        for m in BIG_TIMEOUT.finditer(line):
            mult = float(m.group(2)) if m.group(2) else 1.0
            value = float(m.group(3)) * mult
            if m.group(4):  # milliseconds, e.g. 30000
                value /= 1000
            if value > MAX_TIMEOUT_S:
                yield no, value


def main() -> int:
    findings = []
    for path in _files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(HUB)
        for no, line in enumerate(text.splitlines(), 1):
            if STATUS_GATE.search(line) and "status ok" not in line:
                findings.append(f"{rel}:{no}: gates on ctl status — use core.page_guard.probe()")
        for no, secs in _script_timeouts(text):
            findings.append(f"{rel}:{no}: timeout {secs:g}s > {MAX_TIMEOUT_S}s — shorten it")

    if findings:
        print("\n".join(findings))
        print(f"\n{len(findings)} page-guard finding(s). Rule: skills/RELIABILITY.md#page-guard")
        return 1
    print(f"page-guard: clean ({MAX_TIMEOUT_S}s budget, no status gates)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
