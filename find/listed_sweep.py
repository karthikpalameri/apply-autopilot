#!/usr/bin/env python3
"""listed_sweep.py — QA openings at PUBLICLY LISTED product companies.

Board matrix and the concurrent scan live in **core/ats_boards.py** (single owner).
This file keeps only the listed-company set (ticker-backed, revenue-verified) and
merges it with any listed company already resolved in the 500-list.

Before: its own GH/LEV/ASH arrays, a fourth copy of the board matrix that drifted
from find/prod_sweep.py. Usage: .venv/bin/python find/listed_sweep.py
"""
import contextlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.dedupe import ROLE_NOT as NON
from config.dedupe import ROLE_QA as QA
from core.ats_boards import scan

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "config", "data", "product_companies.json")

# Listed product companies (ticker) -> ATS board. Curated; the 500-list adds the rest.
LISTED = [
    ("freshworks", "greenhouse"), ("snowflakecomputing", "greenhouse"), ("crowdstrike", "greenhouse"),
    ("twilio", "greenhouse"), ("uber", "greenhouse"), ("datadoghq", "greenhouse"),
    ("cloudflare", "greenhouse"), ("zscaler", "greenhouse"), ("n-able", "greenhouse"),
    ("gitlab", "greenhouse"), ("servicenow", "greenhouse"), ("netskope", "greenhouse"),
    ("cohesity", "greenhouse"), ("yugabyte", "greenhouse"), ("oracle", "greenhouse"),
    ("adobe", "greenhouse"), ("atlassian", "greenhouse"), ("instructure", "greenhouse"),
    ("swiggy", "lever"), ("zomato", "lever"), ("delhivery", "lever"), ("makemytrip", "lever"),
    ("netapp", "lever"), ("cisco", "lever"), ("microsoft", "lever"), ("sap", "lever"),
    ("paloaltonetworks", "ashby"), ("vercel", "ashby"),
]

LOC = re.compile(r"bangal|bengaluru|india", re.I)


def companies():
    out = [{"company": b, "ats_slug": b, "ats": p} for b, p in LISTED]
    with contextlib.suppress(OSError, ValueError):   # missing/corrupt data file: listed set still works
        for c in json.load(open(DATA)):
            if (c.get("ats_slug") or "").strip():
                out.append(c)
    seen, uniq = set(), []
    for c in out:
        key = (c.get("ats"), c["ats_slug"])
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    return uniq


def main():
    found = scan(companies(), QA, NON, LOC)
    print(f"QA OPENINGS @ LISTED PRODUCT COS: {len(found)}")
    for company, prov, title, loc, url in sorted(found):
        print(f"{prov[:4]:4s} {company[:18]:18s} {title[:42]:42s} | {loc[:20]:20s} | {url[-44:]}")


if __name__ == "__main__":
    main()
