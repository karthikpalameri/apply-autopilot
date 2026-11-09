#!/usr/bin/env python3
"""config/dedupe.py — DATA ONLY for duplicate matching (mirrors config/freehire.py).

No I/O, no side effects, no logic. Change the vocabulary here and every consumer
(ledger, sweep, reconcile) updates. This is the single owner of "what counts as
the same company / the same role".

Layout (SoC, mirrors docs/FREEHIRE.md):
    config/dedupe.py          DATA       suffix words, role synonyms, statuses, thresholds
    core/applied_ledger.py    STORE      append/read the JSONL, nothing else
    find/ledger_*.py          USE-CASE   backfill / guard / reconciliation
"""
import re

# Legal/geo noise that must not defeat a duplicate match.
# "Bidgely" vs "Bidgely, Inc" once slipped through and cost a full fill cycle.
SUFFIX_WORDS = frozenset({
    "inc", "incorporated", "ltd", "limited", "llc", "pvt", "private", "corp",
    "corporation", "co", "company", "technologies", "technology", "software",
    "systems", "solutions", "group", "labs", "india", "global", "services",
    "platforms", "holdings", "international", "hq", "marketing",
})

# Employers that post under a short name AND a long name. Without this the ledger
# holds "Hewlett Packard Enterprise" while a job board says "hpe", is_applied()
# returns False, and the same role is submitted twice. Key = what boards print,
# value = the canonical key. Both sides go through co_key(), so these are already
# suffix-stripped.
# suffix-stripped.
#
# ONE-TO-ONE ONLY. An alias may rename one spelling of an employer; it must never
# rename an employer into a DIFFERENT employer. `"qlik": "qliktech"` did exactly that:
# co_key("Qlik") became "qliktech" while the ledger stored "qlik", so
# is_applied("Qlik", "Senior QA Automation Engineer (Agentic AI)") returned False for a
# role confirmed on 2026-10-30 — and Qlik's submit API answered 400 "You have already
# applied to this position." after a full form fill (2026-11-07).
COMPANY_ALIASES = {
    "hpe": "hewlett packard enterprise",
    "hp": "hewlett packard enterprise",
    "aws": "amazon web services",
    "jpmc": "jpmorgan chase",
    "jpmorgan": "jpmorgan chase",
    "pwc": "pricewaterhousecoopers",
    "ey": "ernst young",
    "qlys": "qualys",
    "n able": "n able",
    "vmware": "broadcom",
}

# Location vocabulary. prod_sweep/listed_sweep are Bangalore-only by policy
# (skills/find/SKILL.md); the two `deep_sweep` scripts are deliberately India-wide,
# and they each carried their own copy of this pattern — one of them silently lost
# every Pune/Hyderabad role when a rewrite narrowed it to "bangal|india|bengaluru".
INDIA_WIDE_RX = (
    r"bangal|bengaluru|india|hyderabad|pune|chennai|gurgaon|gurugram|noida|mumbai|"
    r"delhi|kolkata|ahmedabad|jaipur|kochi|trivandrum|indore|coimbatore|chandigarh|remote"
)

# SDET is written many ways; collapse the variants so role comparison works.
# (pattern, replacement) — applied in order to a normalized, space-separated string.
ROLE_SYNONYMS = (
    (re.compile(r"\bsoftware\s+development\s+engineer\s+in\s+test\b"), "sdet"),
    (re.compile(r"\bsoftware\s+development\s+test\s+engineer\b"), "sdet"),
    (re.compile(r"\bsoftware\s+engineer\s+in\s+test\b"), "sdet"),
    (re.compile(r"\bsoftware\s+engineer\s+in\s+testing\b"), "sdet"),
    (re.compile(r"\bsoftware\s+test\s+engineer\b"), "sdet"),
    (re.compile(r"\bqa\s+automation\s+engineer\b"), "qa automation"),
    (re.compile(r"\bautomation\s+test\s+engineer\b"), "qa automation"),
    (re.compile(r"\bquality\s+engineer\b"), "qe"),
    # Abbreviations. A re-posted req often shortens the title: the ledger holds
    # "Sr Eng, Test(Automation)" while LinkedIn shows "Sr Engineer, Test-
    # Automation," — 3 of 5 tokens shared = 0.6, under ROLE_OVERLAP_MIN, so it
    # read as a new job and would have been applied to twice.
    (re.compile(r"\beng\b"), "engineer"),
    (re.compile(r"\bengg\b"), "engineer"),
    (re.compile(r"\bsr\b"), "senior"),
    (re.compile(r"\bjr\b"), "junior"),
    (re.compile(r"\bmgr\b"), "manager"),
    (re.compile(r"\bdev\b"), "developer"),
)

# ---------------------------------------------------------------------------
# STATUS VOCABULARY — single owner.
#
# Three scripts each carried a private status set and they had silently diverged:
#   find/tracker_reconcile.py : APPLIED_STATUS   (16 values, reporting view)
#   find/preflight.py         : DONE_STATUS      (14 values, do-not-retry view)
#   config/dedupe.py          : SUBMITTED_STATUSES (7 values, was never imported)
# The gap was real: `submitted-email` counted as applied in the tracker but NOT
# terminal in preflight, so preflight would re-apply to an already-applied role.
# Define statuses here, import everywhere, never inline a literal set again.
# ---------------------------------------------------------------------------

# An application was actually sent to the employer.
SUBMITTED_STATUSES = frozenset({
    "submitted", "submitted-confirmed", "submitted-email", "submitted-awaiting-email",
    "confirmed-ats", "confirmed-email", "confirmed-linkedin",
})

# Credited as an application in human-facing reports (superset of SUBMITTED_STATUSES).
APPLIED_STATUSES = SUBMITTED_STATUSES | frozenset({
    "submitted-awaiting-employer-confirmation", "applied", "done", "verified",
    "email-sent", "sent-by-user", "email-verified", "email-confirmed",
    "duplicate-submitted",
})

# Reached a terminal state: never retry, whatever the outcome was.
#   blocked                   — hard stop, agent cannot proceed (unknown sensitive field, broken widget)
#   waiting-user-captcha      — human must solve a captcha (tab handed over)
#   waiting-user-credentials  — account wall: needs the user's password/OTP to an existing account
#   waiting-user-account      — no account exists; needs the user to authorise creating one
# Keeping these distinct matters: on 2026-11-05 five sites were logged as captcha failures when
# they were really account walls, which sent the next session hunting for a captcha solver.
TERMINAL_STATUSES = APPLIED_STATUSES | frozenset({
    "blocked", "waiting-user-captcha", "waiting-user-credentials", "waiting-user-account",
    "rejected", "interview", "offer", "closed",
})

# Invariants. If someone adds a status to one set and forgets the others, import fails
# loudly here instead of silently double-applying months later.
assert SUBMITTED_STATUSES <= APPLIED_STATUSES, "SUBMITTED must be a subset of APPLIED"
assert APPLIED_STATUSES <= TERMINAL_STATUSES, "APPLIED must be a subset of TERMINAL"


def is_submitted(status):
    return (status or "").strip().lower() in SUBMITTED_STATUSES


def is_applied_status(status):
    return (status or "").strip().lower() in APPLIED_STATUSES


def is_terminal(status):
    return (status or "").strip().lower() in TERMINAL_STATUSES

# Role token-overlap threshold for fuzzy equality ("staff sdet" vs
# "staff sdet database automation" = 2/4 shared => 0.5, but prefix already catches it;
# 0.75 keeps precision high enough that distinct reqs stay distinct).
ROLE_OVERLAP_MIN = 0.75

# ---------------------------------------------------------------------------
# ROLE-SCOPE VOCABULARY — "is this a QA/SDET role worth applying to?"
# Single owner. find/preflight.py, prod_sweep.py, listed_sweep.py, qa_check.py
# and sweep.py each carried a private, silently-diverged copy of these patterns
# (5 different QA_RE, 3 different NON_RE). Add a word here, not in a script.
# ---------------------------------------------------------------------------
ROLE_QA = re.compile(
    r"\b(qa|q[ae]|quality|sdet|test|testing|automation|verification)\b", re.I)

# Titles that are NOT the QA/SDET job we want, even when they say "test"/"automation".
ROLE_NOT = re.compile(
    r"\b(recruiter|trainer|mentor|teacher|sales|marketing|presales|"
    r"frontend|backend|fullstack|full-stack|devops|data engineer|data scientist|"
    r"scientist|security engineer|infosec|network engineer|hr|talent|"
    r"thin films|optics|mechanical|manufacturing|warehouse|auditor|"
    r"research engineer|applied scientist|"
    r"soi|soc|silicon|verification engineer|design verification)\b", re.I)

# Core stack the user refuses (skills/REFERENCE.md#stack-fit-gate).
ROLE_STACK_REJECT = re.compile(r"\bC#|\.NET|Specflow|Cobol|UFT\b", re.I)


def is_qa_title(title):
    """True if `title` is a QA/SDET role inside the user's stack scope."""
    return bool(ROLE_QA.search(title or "")) and not bool(ROLE_NOT.search(title or ""))
