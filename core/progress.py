#!/usr/bin/env python3
"""core/progress.py — single owner for reading/writing config/progress.json.

`progress.json` is a DERIVED projection for humans. The dedupe authority is
core/applied_ledger.py (append-only JSONL) — read that for decisions, write that
for records. This module exists only so the two copies of load_progress() that
had drifted (find/tracker_reconcile.py exited on failure, find/sweep.py returned
an empty skeleton) share one implementation with an explicit policy.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRESS = os.path.join(ROOT, "config", "progress.json")

EMPTY = {
    "total_applications": 0,
    "verified_applications": [],
    "pending_attempts": [],
}


def exists():
    return os.path.exists(PROGRESS)


def load(default=None, strict=False):
    """Read progress.json.

    default=None, strict=False -> return `default` when unreadable (sweep's behaviour)
    strict=True                -> raise SystemExit(1) when unreadable (reconcile's behaviour)
    """
    try:
        with open(PROGRESS, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        if strict:
            print(f"❌ cannot read {PROGRESS}: {e}")
            raise SystemExit(1) from e
        return default


def save(data):
    """Atomic replace so a crash mid-write cannot truncate the tracker."""
    import tempfile
    d = os.path.dirname(PROGRESS)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".progress.")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, PROGRESS)
