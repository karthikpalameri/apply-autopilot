#!/usr/bin/env python3
"""find/ledger_guard.py — fail loudly if the dedupe corpus ever shrinks.

The 2026-11 progress.json rewrite destroyed ~111 companies of history with no warning,
which let a blocked role (HighLevel) be re-proposed and re-filled. The ledger is
append-only so it can't lose rows, but a future refactor could point the reader at the
wrong file or truncate it. This guard makes that impossible to miss.

Usage:
    .venv/bin/python find/ledger_guard.py          # verify, exit 1 if shrunk
    .venv/bin/python find/ledger_guard.py --save   # record current count as high-water
"""
import json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
from core.applied_ledger import stats  # noqa: E402

MARK = os.path.join(BASE, "data", "applied_ledger.highwater.json")


def main():
    s = stats()
    save = "--save" in sys.argv
    prev = {}
    if os.path.exists(MARK):
        try:
            prev = json.load(open(MARK))
        except Exception:
            prev = {}

    high = prev.get("rows", 0)
    print(f"ledger rows={s['rows']} companies={s['companies']} pairs={s['pairs']}")
    print(f"high-water  ={high}")

    if s["rows"] < high:
        print(f"❌ LEDGER SHRANK: {high} -> {s['rows']} ({high - s['rows']} rows lost)")
        print("   The dedupe corpus was truncated. Restore it before running any sweep:")
        print("     git checkout data/applied_ledger.jsonl  # or")
        print("     .venv/bin/python find/ledger_backfill_git.py")
        return 1

    if save or s["rows"] > high:
        json.dump(s, open(MARK, "w"), indent=1)
        print(f"✅ high-water updated -> {s['rows']}")
    else:
        print("✅ ledger intact")
    return 0


if __name__ == "__main__":
    sys.exit(main())
