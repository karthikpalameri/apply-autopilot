# FIND LESSONS

Sourcing + dedupe rules. Mechanics only — no employer names.

## USER FILTER (set during onboarding)
- Apply only to verified product companies with credible evidence of substantial revenue/scale, or genuine GCCs of established companies. Do not guess revenue/GCC status; if not verifiable, skip.
- Exclude staffing, recruiting, consulting, outsourcing, and service vendors unless the role is demonstrably within a genuine GCC.
- For a batch, source the requested number of jobs from LinkedIn Jobs and apply only to roles passing employer, role-fit, live-status, and duplicate checks. If fewer qualify, report the shortfall; never lower the bar.

## LIVE TRUTH vs STALE INDEX
- ATS APIs (GH/Lever/Ashby) = LIVE truth; search-engine indexes 404/pull within days. ALWAYS verify live.
- GH API: `boards-api.greenhouse.io/v1/boards/{board}/jobs` — fastest board check.
- Lever API: `api.lever.co/v0/postings/{co}?mode=json`.
- Careers sites that are SPAs may 404 on all deep links and not be on GH/Lever → blocked.
- Rebrands/moves: verify the employer domain, not just the company name.

## DEDUPE
- Check `config/progress.json`, `scratch/APPLIED.md`, LinkedIn Applied/Job Tracker, and Gmail BEFORE filling.
- Match `{company, exact role, LinkedIn job ID, ATS job ID, employer domain}`. An already attempted/confirmed exact role is `DUPLICATE` even if reposted under a new ID. Uncertain status = hold/skip until reconciled.
- Company-name-only matching creates false duplicates — include the domain and job ID.
- A LinkedIn Apply URL can resolve to a different ATS/company → verify the employer title, domain, and ATS job ID before filling; classify a mismatch and move on.

## SESSION EFFICIENCY
- Extract the visible listing cards once and cache the next few candidates before opening any ATS. Repeated page rescans and duplicate Gmail checks consume a batch without increasing yield.
- LinkedIn job search is virtualized (1 card in the DOM) — read the body text for the list.
- Timebox stale redirects, moved sites, account walls, CAPTCHA, and missing sensitive fields; preserve the exact URL/text and do not rescan unchanged blockers.
- Prefer direct live GH/Phenom/ATS routes once resolved.

## RELATED
- `skills/find/SKILL.md` · `skills/apply/SKILL.md` · `skills/REFERENCE.md`
- `skills/LESSONS/LESSONS-apply.md`
