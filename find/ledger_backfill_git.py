#!/usr/bin/env python3
"""find/ledger_backfill_git.py — USE-CASE: recover history destroyed by schema rewrites.

Owns everything the store must not know about: git, argv, printing, and parsing
`config/progress.json` in any of its historical shapes.

Why: a 2026-11 rewrite replaced a 150-key multi-array progress.json with a 5-key one,
dropping ~111 companies (instahyre[55], linkedin[27], blocked[17], amazon[7], + 64
URL-keyed records) — including HighLevel / QA Automation Engineer, which was then
re-proposed and re-filled by a later sweep.

Usage:
    .venv/bin/python find/ledger_backfill_git.py            # from all git revisions
    .venv/bin/python find/ledger_backfill_git.py --dry-run
    .venv/bin/python find/ledger_backfill_git.py --current  # current config/progress.json
"""
import json, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.applied_ledger import record, stats, co_key  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = "config/progress.json"


def harvest(doc):
    """Yield (company, role, status, url, job_id, date, proof, section) from ANY shape."""
    def walk(o, section=""):
        if isinstance(o, dict):
            company = o.get("company") or o.get("employer") or ""
            if company:
                yield (company, o.get("role") or o.get("title") or "",
                       o.get("status", "imported"), o.get("url", ""), o.get("job_id", ""),
                       o.get("date", ""), o.get("proof", ""), section)
            for k, v in o.items():
                yield from walk(v, k)
        elif isinstance(o, list):
            for i in o:
                yield from walk(i, section)

    yield from walk(doc)


def sources():
    """[(label, raw_json_text)] — every historical revision, newest first."""
    if "--current" in sys.argv:
        p = os.path.join(BASE, TARGET)
        return [("current", open(p, encoding="utf-8").read())]
    shas = subprocess.run(["git", "log", "--all", "--format=%H", "--", TARGET],
                          cwd=BASE, capture_output=True, text=True).stdout.split()
    out = []
    for sha in shas:
        raw = subprocess.run(["git", "show", f"{sha}:{TARGET}"],
                             cwd=BASE, capture_output=True, text=True).stdout
        out.append((sha[:8], raw))
    return out


def main():
    dry = "--dry-run" in sys.argv
    seen, added = set(), 0
    srcs = sources()
    print(f"scanning {len(srcs)} source(s) of {TARGET}")
    for label, raw in srcs:
        if not (raw or "").strip():
            continue
        try:
            doc = json.loads(raw)
        except Exception:
            print(f"  {label}: unparseable, skipped")
            continue
        n = 0
        for company, role, status, url, job_id, date, proof, section in harvest(doc):
            k = (co_key(company), (role or "").lower().strip())
            if k in seen:
                continue
            seen.add(k)
            n += 1
            if not dry and record(company, role, status, url=url, job_id=job_id,
                                  date=date, proof=proof, source=f"{label}:{section}"):
                added += 1
        print(f"  {label}: +{n} unique (company, role)")
    print()
    if dry:
        print(f"DRY RUN — would consider {len(seen)} unique pairs")
    else:
        print(f"appended {added} rows")
        print(json.dumps(stats(), indent=1))


if __name__ == "__main__":
    main()
