#!/usr/bin/env python3
"""prod_sweep.py — Bangalore product companies -> live ATS check for QA/SDET openings.

Board matrix, slug discovery and the fetch/scan loop live in **core/ats_boards.py**
(single owner). This file only picks the company set and the filter.

Before: a hand-maintained GH/LEV/ASH list of ~70 slugs that could never see the
other 430 companies, and drifted from find/listed_sweep.py's own copy of the same
matrix. After: whatever `ats_resolve.py` has resolved for the 500-list, scanned
concurrently through the shared owner.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.dedupe import ROLE_NOT as NON  # single owner of the QA/negative regexes
from config.dedupe import ROLE_QA as QA
from core.ats_boards import scan

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "config", "data", "product_companies.json")

INDIA = re.compile(r"bangal|bengaluru|india|remote", re.I)


def main():
    companies = json.load(open(DATA))
    found = scan(companies, QA, NON, INDIA)
    print(f"QA OPENINGS at Bangalore product companies: {len(found)}")
    for company, prov, title, loc, url in sorted(found):
        print(f"{prov[:4]:4s} {company[:22]:22s} {title[:44]:44s} | {loc[:18]:18s} | {url[-45:]}")


if __name__ == "__main__":
    main()
