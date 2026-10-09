# SKILLS (graph — read `SKILL.md` first)

## Entry points
- **`SKILL.md`** — MASTER: routes the job-hunt graph (RESUME → FIND → APPLY → VERIFY → EMAIL → LEARN → TRACK), dedupe gate, session-start gate, edges, Kaizen PDCA.
- **`RELIABILITY.md`** — transaction contract: pre-check → action → post-check for every browser action + 30%-fewer-round-trips speed profile.
- **`REFERENCE.md`** — SINGLE SOURCE OF TRUTH (DRY): identity, CTC/notice, resume MD5, auth priority, two-tab session, browser topology (one owner per channel), cached cloak tool names, browser-call budget, react-select commit recipe, PI audit corrections, saved answers.

## Nodes (one concern each)
- `find/SKILL.md` — locate product-company QA/SDET roles (live ATS APIs, LinkedIn, Naukri; 500-company master list)
- `apply/SKILL.md` — ATS router → recipe; fill/upload/submit order; saved answers
- `verify/SKILL.md` — proof gate (employer success page + Gmail email = DONE; never infer)
- `email/SKILL.md` — recruiter outreach (Gmail DRAFTS, never send)
- `learn/SKILL.md` — attach lessons to `LESSONS/LESSONS-*.md`
- `ops/SKILL.md` — servers (Pi stdio `cloak-browser` · Python `:3000` · ctl `:9000`), tools, lean mode, Docker/SearXNG
- `resume/SKILL.md` — exact resume + MD5 integrity gates (PICK/BEFORE_UPLOAD/POST)
- `track/SKILL.md` — applied-vs-not-applied reconciliation

## Recipes (per-ATS mechanics — single dir `recipes/`)
`workday.md` · `greenhouse.md` · `lever.md` · `icims.md` · `linkedin.md` · `phenom.md` · `breezy.md` · `jobvite.md` · `oraclehcm.md` · `email-template-humble.md`

## Lessons (per-concern learnings — append, never duplicate)
`LESSONS/LESSONS-apply.md` · `-find.md` · `-verify.md` · `-email.md` · `-ops.md` · `-naukri-profile.md`

## Maintenance rules
- **DRY:** every constant/protocol has ONE home (REFERENCE.md). Nodes point, never restate.
- **SOC:** one concern per node; per-ATS mechanics only in `recipes/`; history only in `LESSONS/`.
- **KISS:** a node states the rule once; the rationale lives in the relevant LESSONS file.
- **Archived scripts:** one-off company scripts live in `archive/scripts/` with a one-page index (`archive/scripts/README.md`). Archive over delete; never merge scripts into one file.
