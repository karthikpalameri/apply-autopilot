# FIND LESSONS
## CURRENT USER FILTER — 2026-10-06
- Apply only to verified product companies with credible evidence of substantial revenue/scale, or genuine GCCs of established companies. Do not guess revenue/GCC status; if not verifiable, skip.
- Exclude staffing, recruiting, consulting, outsourcing, and service vendors unless the role is demonstrably within a genuine GCC.
- For the requested batch, source three jobs from LinkedIn Jobs and apply only to roles passing employer, role-fit, live-status, and duplicate checks. If fewer than three qualify, report the shortfall; never lower the bar.
- This replaces the prior broader employer filter for future searches; historical decisions remain unchanged.

## 2026-08-12
- ATS APIs (GH/Lever) = LIVE truth; search indexes 404/pull within days (AcmeEight, AcmeSix, AcmeSeven all stale)
- Lever API: api.lever.co/v0/postings/{co}?mode=json — found AcmeTwo ×2 + AcmeThree ×3 live
- GH API: boards-api.greenhouse.io/v1/boards/{board}/jobs — AKKO ×2 live (Senior SDET + SDET BLR)
- AcmeSix careers = SPA 404 on all deep links; not on GH/Lever → blocked
- AcmeEight rebranded "Everpure"; BLR = hardware/SAP QA only → skip
- Dup-gate check BEFORE filling: page says "previous application" → record + skip

## RETRO 2026-08-12
- Search-index URLS go STALE in days (AcmeTwentySix/AcmeSix/Moody's/Neo/Dialpad-852 all 404'd) — ALWAYS verify live (GH API / ATS page)
- LinkedIn job search = only 1 card in DOM (virtualized) — read body text for the list
- The ATS-discovery = the bottleneck: GH/Lever/Ashby API checks = fast; Workday = slow; obscure ATSes (Neo/Experity/Moody's SF) = skip after 2 probes
- Dup-gate before filling: check `progress.json`, `scratch/APPLIED.md`, LinkedIn Applied/Job Tracker, and Gmail. Fivetran repeated applications are a warning: an already attempted exact role must always be skipped, including reposts/new IDs.

## SESSION 2026-08-12 PART-2
- LinkedIn QA search (Bengaluru) = 99+ results; read body text blocks (virtualized list, 1 card in DOM)
- Fresh finds: AcmeTwentyFive (8h), Carra (10h), Candescent (1d), AcmeSmartRecruiters (11h), McKesson (1w retry), AcmeTwentyTwo (1w retry), AcmeFourteen (1d retry)
- ATS-discovery bottleneck: smartrecruiters = external redirect; obscure = skip after 2 probes

## 2026-09-22 — QUEUE AND REDIRECT LESSONS FROM PI HISTORY
- Extract the visible listing cards once and cache the next three candidates before opening an ATS. Repeated page 1–8 rescans and duplicate Gmail checks consumed the batch without increasing yield.
- Dedupe with exact role/job ID and employer domain, not company name alone. AcmeTwenty/AcmeTwentyOne showed that company-only matching creates false duplicate/blocker decisions.
- A LinkedIn Apply URL can resolve to a different ATS/company (for example an Eightfold route to another domain). Verify employer title, domain, and ATS job ID before filling; classify mismatch and move on.
- Prefer direct live GH/Phenom/ATS routes once resolved. Timebox stale redirects, moved sites, account walls, CAPTCHA, and missing sensitive fields; preserve the exact URL/text and do not rescan unchanged blockers.
## SESSION 2026-08-12 PART-3
- AcmeFourteen GH = school-db block (school combo no options) — same class as AcmeThirteen
- AcmeTwentyTwo easy-apply = 6-page modal, Review button stuck (radios+consent done) — user 1-click
- N-able = Workday (already applied another req via InstaHyre)
- AcmeSmartRecruiters = SR → external careers; McKesson = Workday maintenance; FIS = Workday maintenance
