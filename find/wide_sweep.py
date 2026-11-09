#!/usr/bin/env python3
"""find/wide_sweep.py — shared runner for the curated slug-list sweeps.

`deep_sweep.py` and `deep_sweep2.py` differ ONLY in their slug sets. Their preamble,
India-wide location policy, scan call and report block were byte-identical (jscpd
flagged them as clones), so they live here once.

Provider knowledge stays in `core/ats_boards.py`; this module adds nothing to it.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.dedupe import INDIA_WIDE_RX  # single owner of location + QA vocabulary
from config.dedupe import ROLE_NOT as NON
from config.dedupe import ROLE_QA as QA
from core.ats_boards import format_found, scan_slugs

INDIA = re.compile(INDIA_WIDE_RX, re.I)


def run(provider_slugs):
    """Scan {provider: [slug]} and print the India QA/SDET hits."""
    boards, found = scan_slugs(provider_slugs, QA, NON, INDIA)
    print(f"boards checked: {boards}  |  India QA/SDET: {len(found)}")
    for line in format_found(found):
        print(line)
    return found
