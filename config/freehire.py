#!/usr/bin/env python3
"""config/freehire.py — SINGLE source of truth for the freehire integration (DRY).

DATA ONLY — no HTTP, no I/O, no side effects. Mirrors config/answers.py:
change filters / gates / routing here and every consumer updates.

Layout (SoC):
    config/freehire.py       this file — data + vocabulary (no logic)
    core/freehire_client.py  transport — HTTP/SSL/envelope (no business rules)
    find/freehire_sweep.py   use-case — discovery orchestration (thin)

Usage:
    from config.freehire import API_BASE, ROUTING, QA, NON, build_search_params
"""
import re

API_BASE = "https://freehire.me/api/v1"
API_DOCS = "https://freehire.me/docs/api"
REPO_URL = "https://github.com/strelov1/freehire.git"
CLI_REPO_URL = "https://github.com/strelov1/freehire-cli.git"
CLI_INSTALL = "https://freehire.me/install.sh"

# ---------------------------------------------------------------------------
# Search filters (single source of truth)
# ---------------------------------------------------------------------------
QA_CATEGORY = "qa"                # freehire's LLM facet — finds "Test Analyst" etc.
DEFAULT_LIMIT = 100

# Title intent — same spirit as find/prod_sweep.py. SDET query catches roles
# freehire classified outside `category=qa`.
QA = re.compile(r"\b(qa|sdet|quality|test|automation|software development engineer in test)\b", re.I)
NON = re.compile(
    r"\b(recruiter|trainer|sales|marketing|frontend|backend|data scientist|scientist|"
    r"security engineer|devops|sre|hr|talent|firmware|hardware|electrical|"
    r"manufacturing|soc|silicon|verification|support|manager|account|consultant)\b",
    re.I,
)

# ---------------------------------------------------------------------------
# Gates (mirror skills/find/SKILL.md)
# ---------------------------------------------------------------------------
# employer gate: product company OR genuine GCC (inhouse)
GATE_COMPANY_TYPES = {"product", "inhouse"}
# staleness gate
FRESH_CLASSES = {"fresh"}
# excluded employer types (staffing / consulting / outsourcing — never apply)
EXCLUDED_COMPANY_TYPES = {"outstaff", "outsource", "agency"}

# ---------------------------------------------------------------------------
# ATS routing — freehire `source` -> what THIS repo already has to apply
# ---------------------------------------------------------------------------
ROUTING = {
    # covered by an apply script
    "greenhouse":      "apply/fill_gh_fast.py  (+ skills/recipes/greenhouse.md)",
    "ashby":           "apply/ashby_apply.py",
    "workable":        "apply/workable_apply.py",
    "lever":           "skills/recipes/lever.md",
    # covered by a recipe (browser fill, no dedicated script)
    "workday":         "skills/recipes/workday.md",
    "icims":           "skills/recipes/icims.md",
    "breezy":          "skills/recipes/breezy.md",
    "jobvite":         "skills/recipes/jobvite.md",
    "phenom":          "skills/recipes/phenom.md",
    "oraclehcm":       "skills/recipes/oraclehcm.md",
    # no coverage yet — these dominate Bangalore QA (SuccessFactors 16/36)
    "successfactors":  "NO RECIPE YET (needs a new apply script)",
    "zohorecruit":     "NO RECIPE YET",
    "oracle":          "NO RECIPE YET",
    "jibe":            "NO RECIPE YET",
    "smartrecruiters": "NO RECIPE YET",
    "eightfold":       "NO RECIPE YET",
    "comeet":          "NO RECIPE YET",
    "adp":             "NO RECIPE YET",
}
UNKNOWN_ROUTE = "unknown ATS"


def build_search_params(location="bangalore", limit=DEFAULT_LIMIT):
    """Return the list of (label, query-dict) used for discovery.

    Two queries are merged + deduped by public_slug:
      1. category=qa  — freehire's LLM classification (broadest QA coverage)
      2. q=sdet (title) — catches SDET roles classified elsewhere
    """
    loc = {"countries": "IN"} if location == "india" else {"cities": "bangalore"}
    base = {"sort": "posted_at", "order": "desc", "limit": limit}
    return [
        ("category=qa", dict(loc, category=QA_CATEGORY, **base)),
        ("title=sdet", dict(loc, q="sdet", q_fields="title", **base)),
    ]
