---
name: tool-map
description: Find existing project Python scripts, browser helpers, ATS recipes and verification methods for job search, dedupe, LinkedIn, Greenhouse, Gmail, resume, OCR, cost and Pi tools. Use before creating a new script.
parent: skills/SKILL.md
---

# TOOL MAP — discover, do not duplicate

Jev sees **this description**, not repository contents. Load this file on a match;
then use deterministic file search. Never send applicant data or browser DOM to Jev.
Run commands from the repo root. Read only the selected owner's file/skill.

| Task | Existing owner / route |
|---|---|
| One-pass search + dedupe | `find/preflight.py` → `find/freehire_sweep.py` (paginated) → `core/applied_ledger.py` |
| Bounded parallel fetching | `core/fetch.py::fetch_many` (asyncio + hard deadline) — never `asyncio.run` |
| Employer/role QA gate | `config/dedupe.py` → `find/qa_check.py` / `find/product_lookup.py` |
| ATS detection / discovery | `core/ats_boards.py` (ONE board matrix + slug discovery + `scan`) → `find/ats_resolve.py` (resolve) / `find/prod_sweep.py` / `find/listed_sweep.py` (scan) |
| LinkedIn Easy Apply | `skills/recipes/linkedin.md` → `apply/li_drive.py` (check current limitations first) |
| Greenhouse | `skills/recipes/greenhouse.md` → `apply/gh_apply.py` / `apply/fill_gh_fast.py` |
| Other ATS | `skills/apply/SKILL.md` → one file in `skills/recipes/` |
| Browser calls | `core/ctl.py` (socket) → `core/ui.py` (state/actions) → `core/browser.py` (MCP fallback) |
| Resume integrity | `core/resume_secure.py` → `skills/resume/SKILL.md` |
| Gmail confirmation / OTP | `core/gmail_read.py` (browser primary) → `core/gmail_otp.py` (IMAP fallback) |
| OCR / proof | `core/ocr.py` → `core/see.py` → `skills/verify/SKILL.md` |
| Applied/not-applied | `core/applied_ledger.py` → `find/tracker_reconcile.py` → `skills/track/SKILL.md` |
| Quality / cost / launch | `scripts/check.sh` / `scripts/cost_report.py` / `scripts/pi_jev.sh` → `skills/pi-setup/SKILL.md` |

Unknown capability: use `rg -l -i 'keyword' core/ find/ apply/ scripts/ skills/recipes/`
then read only a few matching files. To locate a method use
`rg -n '^def |^class ' core/ui.py` (replace path with the chosen file). This is
**file lookup**, not automatic Jev indexing. Never execute an apply script just
to discover what it does: read its header and gates first.
