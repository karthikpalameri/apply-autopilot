---
name: find
description: FIND node — locate QA/SDET jobs at product companies. Caveman.
parent: skills/SKILL.md
---

# FIND

## RELIABILITY + SPEED
- Read `skills/RELIABILITY.md` once before browser work. Extract all visible cards and metadata with one DOM call per page, and batch independent live ATS checks in parallel.
- Build a three-role queue before opening any ATS. Cache `{company, exact role, LinkedIn ID, ATS ID, employer domain, URL, ATS}` and classify duplicate/mismatch/ready/blocker once.
- Cache results for the current session; never rescan the same LinkedIn pages or reopen a completed/blocked URL unless it is stale, changed, or explicitly requested. Each navigation/click still requires target pre-check and URL/content post-check.
- Prefer direct live ATS/API routes once the employer URL is known; LinkedIn detail-page revisits are discovery waste.

## SOURCES (live-first)
1. **ATS APIs** (concurrent, 3s timeouts): `find/prod_sweep.py` + `find/listed_sweep.py`
   - GH: `boards-api.greenhouse.io/v1/boards/{board}/jobs`
   - Lever: `api.lever.co/v0/postings/{co}?mode=json`
   - Always verify LIVE — search indexes 404/pull within days
2. LinkedIn: a11y 1 card → jobs-guest API; verify POSTING company (staffing re-tags)
3. Naukri SRP: product-heavy only (slice/cashfree/cred/groww...)
4. **Web search** for portal-only roles — use local SearXNG (`skills/searxng/SKILL.md`):
   `curl 'http://127.0.0.1:8080/search?q=<product>+QA+SDET+Bengaluru+greenhouse/lever&format=json'`

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
- The user's next batch is **three eligible LinkedIn jobs**. Source these from LinkedIn Jobs; if fewer than three pass the employer, role-fit, availability, and duplicate gates, report the shortfall rather than lowering the bar.
- Location: Bangalore/India only (skip Hyderabad/Pune unless remote ok).
- Closed/410 listings and duplicate applications are non-actionable. CAPTCHA/authentication blockers stop automation; finish all other safe form work first, then ask the user to solve CAPTCHA.

## DEDUPE
- Before queueing, check `config/progress.json`, `scratch/APPLIED.md`, LinkedIn's Applied/Job Tracker, and Gmail for existing submissions/confirmations. Cache results for the session.
- Match normalized company + exact role + LinkedIn/ATS IDs + employer domain and status. An already attempted/confirmed exact role is `DUPLICATE` even if reposted under a new ID; uncertain status means hold/skip until reconciled. This stricter rule prevents repeat applications.
- A LinkedIn apply URL resolving to another ATS/company domain is `MISMATCH`, never a valid apply route.
- Dup gate: "already submitted / previous application" = NOT new → update the tracker and skip.

## LESSONS
- skills/LESSONS/LESSONS-find.md (append learnings here)

---

## RELATED (skill graph — every node is one click away)
- **Master:** `skills/SKILL.md` · **Reference:** `skills/REFERENCE.md` · **Reliability:** `skills/RELIABILITY.md`
- **Nodes:** `apply` · `email` · `find` · `learn` · `ops` · `resume` · `searxng` · `track` · `verify` (each `skills/<node>/SKILL.md`)
- **Recipes:** `skills/recipes/` — workday · greenhouse · lever · icims · linkedin · phenom · breezy · jobvite · oraclehcm · email-template-humble
- **Lessons:** `skills/LESSONS/LESSONS-*.md` — apply · find · verify · email · ops · naukri-profile
- **Index:** `skills/README.md` · **Repo entry for agents:** `AGENTS.md`
