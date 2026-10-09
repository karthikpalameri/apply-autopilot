---
name: track
description: TRACK node — applied vs not-applied reconciliation. Reads config/progress.json +
  Gmail inbox confirmations → writes config/applied_vs_not_applied.md + scratch/APPLIED.md.
  Trigger: "track applied", "applied vs not applied", "reconcile", "progress".
parent: skills/SKILL.md
version: 1.0.0
---

# TRACK (APPLIED vs NOT-APPLIED)

## THE PROBLEM SOLVED
We record every application in `config/progress.json` (ground truth of what we *attempted*),
and Gmail holds the confirmation emails (ground truth of what *actually landed*). This node
reconciles the two into one authoritative report.

## TAB SAFETY
- Follow `skills/SKILL.md` → **TWO-TAB SESSION**. `--gmail` reads the reusable GMAIL tab and restores FORM; it never navigates the application tab.

## BATCH RECONCILIATION (SPEED + NO REPEATS)
- At session start, reconcile `config/progress.json` and `scratch/APPLIED.md`, inspect LinkedIn Applied/Job Tracker, and search Gmail for prior application evidence before choosing roles. This is a mandatory duplicate gate, especially for repeat-prone employers such as Fivetran.
- After submissions, capture each employer success page immediately and check Gmail for exact company/role/ATS-ID confirmation. Batch searches are fine when results map unambiguously to each role.
- Update both trackers after the batch: record every attempt/blocker, preserve `submitted-awaiting-email` separately from `submitted-confirmed`, and write verified proof/status. Never overwrite historical facts or leave new attempts out.
- Match confirmations by exact company + role/ATS job ID where available. A generic signup/OTP email is not application proof.

## RUN (two modes)
```bash
# fast, no browser — reconciles progress.json only
.venv/bin/python find/tracker_reconcile.py

# full — also reads Gmail inbox confirmations (needs CloakBrowser/MCP running)
.venv/bin/python find/tracker_reconcile.py --gmail --fresh
```

## OUTPUT
- `config/applied_vs_not_applied.md` — README-style report: ✅ APPLIED(verified) / ⏳ SUBMITTED-unverified / ❌ NOT-APPLIED-pending
- `scratch/APPLIED.md` — caveman dedupe tracker (auto-synced with verified apps) — CHECK before every apply

## RAMPS
- `--gmail`           pull Gmail confirmations (via core/gmail_read.py --dump → logs/gmail_inbox.txt)
- `--fresh`           force a fresh inbox read (don't reuse logs/gmail_inbox.txt); use once per batch, not once per role
- (offline default)   no `--gmail` → progress.json only, inbox_confirmation count = 0

## DEFINITIONS
- **APPLIED (verified)**  = recorded submission AND has proof (confirmation page / email / hard-assert).
- **SUBMITTED-unverified**= recorded as sent but no email confirmation yet → likely, but re-check inbox.
- **NOT-APPLIED / pending** = discovered/queued but never submitted (dedupe gate caught it, or blocked).

## LESSONS
- Never re-apply to a company whose URL is in `scratch/APPLIED.md` (dedupe gate).
- Email confirmation is the STRONGEST proof — prefer it over page-state inference.
- Run this at the START of a session and after each apply batch.
```
