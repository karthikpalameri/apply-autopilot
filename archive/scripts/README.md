# ARCHIVED ATS SCRIPTS — index (caveman)

One-off, per-ATS apply scripts kept as **reference mechanics** (nothing in the live
flow imports them). They are generic templates: company names, job URLs, recruiter
emails, and CTC values have been stripped — personal values load from
`config/user.json` via `from config.answers import A`.

To rerun one: copy it next to `core/`/`config/` (or move it back to `apply/`) so
repo-root is on `sys.path`. Canonical lessons already live in
`skills/LESSONS/LESSONS-apply.md` — prefer the skill over rerunning these.

| Script | ATS / mechanic | Key mechanic kept in skills | Status |
|---|---|---|---|
| `account_wall_apply.py` | account-wall apply | account walls = blocker, never infer | reference |
| `ashby_apply.py` | Ashby | Select2 exact-option; +91 phone | reference |
| `selffill_apply.py` | Greenhouse self-id/ack/right-to-work | inbox-email proof pattern | reference |
| `gh_fill.py` | Greenhouse (generic) | GH fill helpers | reference |
| `gh_spa_embed_apply.py` | Greenhouse embed in an SPA | dispatchEvent on job-application | reference |
| `gh_apply_mcp.py` | Greenhouse via MCP | GH apply via an MCP session | reference |
| `instahyre_click.py` | Instahyre | stale-listings check | reference |
| `workday_full_apply.py` | Workday | Workday selects = exact-option click; textareas = real keys | reference |
| `workday_agentic_apply.py` | Workday agentic loop | verify each target before typing | reference |
| `workday_resume_variants.py` | Workday resume variants | account remembers server-side state | reference |
| `li_apply_mcp.py` | LinkedIn Easy Apply via MCP | two-tab session | reference |
| `phenom_step1_fill.py` | Phenom step-1 | Phenom `.fill()` only | reference |
| `generic_fullfill.py` / `generic_selffill.py` | Greenhouse full self-fill | zero-nav transaction | reference |
| `nested_iframe_apply.py` | nested-iframe form | embed ref pierces rotating iframe | reference |
| `healthcare_ats_drive.py` / `_run.py` / `_probe.py` | healthcare ATS drive/probe | — | reference |
| `generic_rsfiil.py` | react-select fill ×3 | start select = open empty → "Immediately" | reference |
| `workable_apply.py` | Workable ATS | — | reference |
| `generic_form_fill.py` | generic Greenhouse form fill | "errs=0 + form closed" ≠ submitted | reference |

## Keep-forever rule
- Archive over delete: company forms cost hours to rediscover.
- Index over merge: one file per ATS = one readable entry; this README is the merge.
- If an ATS reappears: restore the file, re-verify the live DOM (forms drift), then re-archive.
- Never hardcode a password — use `os.environ["ATS_PW"]` or the OS keychain.
