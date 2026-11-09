#!/usr/bin/env python3
"""cost_report.py — what a session cost, and who spent it.

Pi records `usage.cost.total` per request and every tool result in the session
transcript. This reports Pi's main-model **cost estimate**, not the provider bill.
Separate Jev/OpenRouter API requests are not included.

Usage:
  scripts/cost_report.py                 # last 5 sessions, summary + tool ranking
  scripts/cost_report.py --last 20
  scripts/cost_report.py --tools-only
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from collections import defaultdict
from typing import Any

SESSION_GLOB = os.path.expanduser("~/.pi/agent/sessions/**/*.jsonl")


def read_entries(path: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if isinstance(entry, dict):
                out.append(entry)
    return out


def summarize(path: str) -> dict[str, Any]:
    requests = 0
    tokens_in = tokens_cached = tokens_out = 0
    cost = 0.0
    first_cost: float | None = None
    last_cost: float | None = None
    images = 0
    image_bytes = 0
    per_tool: dict[str, list[int]] = defaultdict(lambda: [0, 0])

    for entry in read_entries(path):
        message = entry.get("message") or {}
        usage = message.get("usage") or {}
        if usage:
            requests += 1
            tokens_in += int(usage.get("input") or 0)
            tokens_cached += int(usage.get("cacheRead") or 0)
            tokens_out += int(usage.get("output") or 0)
            request_cost = float((usage.get("cost") or {}).get("total") or 0.0)
            cost += request_cost
            first_cost = request_cost if first_cost is None else first_cost
            last_cost = request_cost

        content = message.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") in ("image", "image_url"):
                    images += 1
                    image_bytes += len(json.dumps(block))

        role = message.get("role")
        if role in ("toolResult", "tool"):
            name = str(message.get("toolName") or "?")
            per_tool[name][0] += 1
            per_tool[name][1] += len(json.dumps(message))

    return {
        "path": path,
        "requests": requests,
        "tokens_in": tokens_in,
        "tokens_cached": tokens_cached,
        "tokens_out": tokens_out,
        "cost": cost,
        "first_cost": first_cost or 0.0,
        "last_cost": last_cost or 0.0,
        "images": images,
        "image_bytes": image_bytes,
        "per_tool": per_tool,
    }


def print_summary(rows: list[dict[str, Any]]) -> None:
    print(f"{'session':<26}{'req':>5}{'in':>9}{'cached':>9}{'out':>7}{'imgs':>6}{'imgKB':>7}{'$':>9}")
    for row in rows:
        name = os.path.basename(row["path"])[11:24]
        print(
            f"{name:<26}{row['requests']:>5}{row['tokens_in']:>9}{row['tokens_cached']:>9}"
            f"{row['tokens_out']:>7}{row['images']:>6}{row['image_bytes'] // 1024:>7}{row['cost']:>9.4f}"
        )
    total = sum(row["cost"] for row in rows)
    reqs = sum(row["requests"] for row in rows)
    print(f"\ntotal ${total:.4f} over {reqs} requests  (avg ${total / reqs:.5f}/request)" if reqs else "no requests")


def print_tools(rows: list[dict[str, Any]]) -> None:
    merged: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in rows:
        for name, (calls, size) in row["per_tool"].items():
            merged[name][0] += calls
            merged[name][1] += size
    print(f"\n{'tool result payload':<40}{'calls':>7}{'KB':>9}{'~tok':>8}")
    for name, (calls, size) in sorted(merged.items(), key=lambda kv: -kv[1][1])[:12]:
        print(f"{name[:39]:<40}{calls:>7}{size // 1024:>9}{size // 4096:>8}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Pi main-model cost estimate (excludes Jev)")
    parser.add_argument("--last", type=int, default=5, help="how many recent sessions (default 5)")
    parser.add_argument("--tools-only", action="store_true", help="skip the session table")
    args = parser.parse_args()

    files = sorted(glob.glob(SESSION_GLOB, recursive=True), key=os.path.getmtime)[-args.last:]
    if not files:
        print(f"no sessions under {SESSION_GLOB}")
        return 1

    rows = [summarize(path) for path in files]
    if not args.tools_only:
        print_summary(rows)
    print_tools(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
