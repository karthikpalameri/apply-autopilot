# ARCHIVED COMPANY SCRIPTS — index (caveman)

One-off per-company apply scripts, moved here 2026-10-02 because nothing references them.
Knowledge kept; files kept. NOT merged into one .py — each has its own entrypoint/imports.
To rerun one: move it back to its old location (`apply/` or repo root) — imports assume repo-root on sys.path.
Canonical lessons already extracted to `skills/LESSONS/LESSONS-apply.md` — prefer the skill over rerunning these.

| Script | Company / ATS | What it did | Key mechanic kept in skills | Status |
|---|---|---|---|---|
| amz_apply.py | Amazon | apply via account wall | account walls = blocker, never infer | blocked |
| ashby_apply.py | Ashby (AcmeEighteen) | register + apply | Select2 exact-option; +91 phone | superseded |
| elastic_selffill.py | Elastic.co | self-fill form | inbox-email proof pattern | superseded |
| fill_gh.py | Greenhouse (generic) | GH fill | superseded by apply/fill_gh_fast.py (still live) | superseded |
| fivetran_gh.py | Fivetran | GH embed in Webflow SPA | dispatchEvent on job-application; uses apply/fill_gh_fast.py helpers | done |
| gh_apply_mcp.py | Greenhouse via MCP | GH apply via MCP session | superseded by agent-side flow | superseded |
| ih_click.py | Instahyre | click helper | stale listings check | superseded |
| acme-workday_full.py / _agentic.py / _resume.py | AcmeWorkday Workday | full Workday battle + resume variants | Workday selects = exact-option click; textareas = real keys | done |
| li_apply_mcp.py | LinkedIn via MCP | EA via MCP | superseded by apply/li_drive.py (still live) | superseded |
| acme-phenom_phenom_step1.py | AcmePhenom (Phenom) | Phenom step-1 fill | Phenom .fill() only | done |
| moniepoint_fullfill.py / _selffill.py | Moniepoint | apply variants | — | done |
| netskope_agentic.py | Netskope | nested-iframe form | embed ref pierces rotating iframe | done |
| acme-employer_drive.py / _run.py / _probe.py | AcmeEmployer | healthcare ATS apply + probe | — | unknown |
| acme-select_rsfiil.py | AcmeSelect | SDET apply ×3 | start select = open empty → "Immediately" | done |
| workable_apply.py | Workable ATS | apply | — | superseded |
| zscaler_apply.py | Zscaler | form fill | "errs=0 + form closed" ≠ submitted (sin #1) | superseded |

## Keep-forever rule
- Archive over delete: company forms cost hours to rediscover.
- Index over merge: one file per company = one readable entry; this README is the merge.
- If a company reappears: restore the file to `apply/`, re-verify the live ATS DOM (forms drift), then re-archive.
