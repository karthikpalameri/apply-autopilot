---
name: find
description: FIND node — locate QA/SDET jobs at product companies. Caveman.
parent: skills/SKILL.md
---

# FIND

## RELIABILITY + SPEED
- Check `skills/REFERENCE.md` for the current batch target; user preference is three fresh, distinct product-company QA/SDET roles verified before opening forms, then apply.
- Read `skills/RELIABILITY.md` once before browser work. Extract all visible cards and metadata with one DOM call per page, and batch independent live ATS checks in parallel.
- Build a three-role queue before opening any ATS. Cache `{company, exact role, LinkedIn ID, ATS ID, employer domain, URL, ATS}` and classify duplicate/mismatch/ready/blocker once.
- Cache results for the current session; never rescan the same LinkedIn pages or reopen a completed/blocked URL unless it is stale, changed, or explicitly requested. Each navigation/click still requires target pre-check and URL/content post-check.
- Prefer direct live ATS/API routes once the employer URL is known; LinkedIn detail-page revisits are discovery waste.

## MANDATORY FACT PREFLIGHT (resume first — NEVER ask what the resume already says)
- **`.venv/bin/python find/resume_facts.py`** before ANY apply batch. Writes `config/resume_facts.json`.
- **The resume is the first-resort fact source.** Do not write/park a fact as "UNKNOWN — must ask user" until the resume PDF has been text-extracted and searched. DOB, phone, email, LinkedIn, GitHub, employers, titles, dates, school, degree are all in there.
- Order of truth: `config/user.json` (explicit) → resume text → **only then** ask the user. Values live in ONE place: **`skills/REFERENCE.md#identity`** + `config/user.json`; never copy them into a recipe.
- Proven failure (2026-11-05): DOB was declared unknown and blocked three Workday tenants (MKS/Experity/Proofpoint). The resume carries it; one `pypdf` call was the whole fix.
- Extract with `pypdf` (present in `.venv`): `"\n".join(p.extract_text() or "" for p in PdfReader(path).pages)`.
- Emit dates in the format the form wants: US `MM/DD/YYYY` · EU/India `DD/MM/YYYY` · long `D Month YYYY`. The values are in `config/user.json`; never type them into a skill file.
- The resume is the same artifact uploaded to the ATS, so its values stay internally consistent — ATS cross-checks (work history vs. resume) pass when you use them.

## MANDATORY LEDGER GUARD (run BEFORE any sweep)
- `.venv/bin/python find/ledger_guard.py` — exits 1 if the dedupe corpus shrank. If it fails, STOP and restore (`find/ledger_backfill_git.py`) before searching; never sweep against a truncated history.
- **Upload guard (same session, once):** `.venv/bin/python core/lint_upload.py` — exits 1 if any live script clicks an upload control (that opens the OS file picker the harness cannot close). Uploads inject via `setInputFiles` only; full procedure at **`skills/resume/SKILL.md#upload-method`**.
- **The ONLY authority for "have we applied here?" is `core/applied_ledger.py`** (append-only JSONL at `data/applied_ledger.jsonl`). `progress.json` is a derived projection for humans, NOT the dedupe source. A 2026-11 schema rewrite (150 keys → 5) silently deleted ~111 companies; `HighLevel / QA Automation Engineer` was among them and got re-applied.
- Never rewrite, dedupe, or "clean up" the ledger by hand. Add rows with `record(...)`; never delete.
- Record EVERY attempt (submitted, blocked, in-progress) immediately after the form action — a blocked role is still a duplicate.

## MANDATORY FREEHIRE FIRST PASS
- **Freehire preflight is mandatory after every fresh clone and before every new search:** this repository uses Freehire's keyless public catalogue API through `core/freehire_client.py`; no `freehire` CLI, login, or candidate profile is required for discovery.
- Run `.venv/bin/python find/freehire_sweep.py --strict --json` once before each new product-company search. If the request also permits genuine GCC/in-house employers, use `.venv/bin/python find/freehire_sweep.py --json` instead. Use the `india` argument only when the user permits India-wide roles.
- **PAGINATE — one page is 2% of the catalogue (measured 2026-11-07).** India QA holds **5,378** postings; the server caps `limit` at 100, so a single `search()` reads 100 and the sweep then reports "no new roles", which is false. `FreehireClient.search_paged(params, pages=N)` (`core/freehire_client.py`) fetches N pages of 100 **concurrently on one event loop** (12 pages ≈ 1.8 s) and dedupes by `public_slug`. `offset` is the only way past the cap; `limit` values above 100 are silently truncated.
- **How many pages: `PAGES = 12` in `find/freehire_sweep.py`, plus `STALE_STREAK = 40`.** Results are newest-first, so 40 consecutive `stale` rows means the fresh window is over and the loop breaks. Do not raise `PAGES` to "read everything" — the tail is old postings nobody should apply to. Override per call with `search_paged(params, pages=...)` only while debugging.
- Measured on the Bangalore QA pair: 1 page → **193** postings / **7** product-gated; 12 pages → **1,252** postings / **36** product-gated, in **2.9 s**. Treat the 30 s budget as the cap, not the target.
- `find/freehire_sweep.py` stops early via `STALE_STREAK`: results are newest-first, so 40 consecutive `stale` rows means the fresh window is over. Do not raise `PAGES` to "read everything" — the tail is old postings nobody should apply to.
- Treat output as discovery leads only: independently verify the exact role on the official employer ATS and run the complete employer, fit, and duplicate gates. A Freehire `pass` is not application authorization.
- If the sweep errors or returns no candidates, record that result and then continue with other sources. Never silently skip or repeat an unchanged scan in the same session.

## SOURCES (supplemental, live-first)
1. **ATS APIs** (concurrent, 3s timeouts): `find/prod_sweep.py` + `find/listed_sweep.py`
   - GH: `boards-api.greenhouse.io/v1/boards/{board}/jobs`
   - Lever: `api.lever.co/v0/postings/{co}?mode=json`
   - Always verify LIVE — search indexes 404/pull within days
2. LinkedIn: a11y 1 card → jobs-guest API; verify POSTING company (staffing re-tags)
   - **Harvest = jobs-guest HTML API, never the new UI list pane** (`/jobs/search-results/` has no scrapeable cards): `curl -sk -A "<desktop UA>" "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=SDET&location=Bengaluru%2C%20Karnataka%2C%20India&f_TPR=r604800&start=0"` → parse `<li>` (`urn:li:jobPosting:(\d+)`, `base-search-card__title/__subtitle`, `job-search-card__location`). 40 cards / 4 requests, no login.
   - Detail + apply target: `.../jobs-guest/jobs/api/jobPosting/<id>` (`topcard__title`, `show-more-less-html__markup`, apply anchor). Save under `scratch/li/` and parse with `ctx_execute_file` — never dump raw HTML into context.
   - MISMATCH gate: unquote the `/safety/go/?url=` param to get the real employer ATS before opening anything.
3. Naukri SRP: product-heavy only (slice/cashfree/cred/groww...)

## PRODUCT-COMPANY MASTER LIST (500)
- `product_companies.md` (hub root, human-readable) + `config/data/product_companies.json` (structured)
- 500 product companies w/ sector + city + **website** + **LinkedIn URL** + known ATS board.
- REGENERATE / re-resolve:
  ```bash
  .venv/bin/python find/product_companies_builder.py            # websites + LinkedIn URLs
  .venv/bin/python find/product_companies_builder.py --linkedin-verify  # confirm each LI URL resolves (needs CloakBrowser)
  ```
- To add companies: append to `config/data/product_seed.py` (name, website, sector, city, ats).
- Drive ATS scans from this list (`prod_sweep.py`) for QA/SDET openings at every one.

## GUARDS
- **Strict employer gate:** apply only to (a) a product company with credible, verifiable evidence of substantial revenue/scale, or (b) a genuine Global Capability Center (GCC) of an established company. Verify the company and role; do not infer revenue or GCC status from branding. If evidence is unclear, skip it. Staffing, recruiting, consulting, outsourcing, and service vendors do not qualify unless the role is demonstrably within a genuine GCC.
- **Batch source follows the user request.** For product-company searches, use the mandatory Freehire first pass above; do not force LinkedIn when the user asks for roles across distinct company/ATS portals. Use LinkedIn when requested or as a supplemental source. If fewer than three pass the employer, role-fit, availability, and duplicate gates, report the shortfall rather than lowering the bar.
- Location: Bangalore/India only (skip Hyderabad/Pune unless remote ok).
- Closed/410 listings and duplicate applications are non-actionable. CAPTCHA/authentication blockers stop automation; finish all other safe form work first, then ask the user to solve CAPTCHA.

## DEDUPE
- **Identity rules live in ONE place: `config/dedupe.py`** (data) → `core/applied_ledger.py` (pure functions). Never re-implement company/role matching in a sweep, a recipe, or a script; `find/freehire_sweep.py` delegates to the ledger for exactly this reason.
- **A single shared word is NOT the same employer** — the matcher used to say so and hid 360 real roles. Rule, aliases and the measured false-positive list live in **`skills/REFERENCE.md#single-source-invariant`**; call `is_applied()` / `company_matches()`, never re-implement them here.
- **Never dedupe with raw string matching.** `if name.lower() in applied_set` missed `AI Squared` (stored with a space) and nearly re-applied a role confirmed 2026-11-05. Import the owner: `from core.applied_ledger import is_applied, company_matches, co_key`.
- **Identity vocabulary (suffixes, role synonyms, aliases, India-wide location regex) is DATA in `config/dedupe.py`.** Add a word there, not in a sweep.
- **Source of truth = `core/applied_ledger.py`** (append-only JSONL). Query it first: `.venv/bin/python -c "from core.applied_ledger import is_applied; print(is_applied('Company','Role'))"`. Also check `scratch/APPLIED.md`, LinkedIn's Applied/Job Tracker, and Gmail. Cache results for the session.
- **Print the rows, not the boolean.** `is_applied` is company-wide and counts `blocked`/`stale` attempts (Netskope SDET, SASE → `True` from a `blocked` row). One batch dump keeps the whole candidate set honest:
  ```python
  rows=[json.loads(l) for l in open('data/applied_ledger.jsonl')]
  [ (r['role'],r['status'],r['date']) for r in rows if name in (r['company']+' '+r['c']).lower() ]
  ```
- `config/progress.json` is a derived projection for humans; never treat it as the dedupe authority (a 2026-11 rewrite of it silently deleted ~111 companies).
- **Match BOTH ledger company fields.** Rows carry a full `company` and a short `c` key, and importers populate them unequally, so compare the normalised **union of both**; keep 3-letter keys (many employers abbreviate to three letters) and prefix-match names ≥6 chars so a short form and its legal name collide. Filtering one field with a `len>=4` guard silently re-applies a live duplicate.
- Match normalized company + role + LinkedIn/ATS IDs + employer domain and status. An already attempted/confirmed exact role is `DUPLICATE` even if reposted under a new ID; uncertain status means hold/skip until reconciled. This stricter rule prevents repeated applications such as Fivetran.
- A LinkedIn apply URL resolving to another ATS/company domain is `MISMATCH`, never a valid apply route.
- Dup gate (Acceldata): "already submitted / previous application" = NOT new → record the attempt and skip.

## LESSONS
- skills/LESSONS.md (append learnings here)
