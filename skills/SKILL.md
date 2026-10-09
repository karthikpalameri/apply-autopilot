---
name: apply-autopilot
description: MASTER skill — routes the job-hunt graph. Read me first; follow the edges.
version: 23.4.0
platforms: [macos, linux, win32]
---

# JOB-HUNT GRAPH (master)

**Global execution contract:** read `skills/RELIABILITY.md` (transaction contract) + `skills/REFERENCE.md` (constants · auth · two-tab · browser-call discipline) once before browser work. Every action requires a pre-check, action, and post-check; target 30%-fewer-round-trips without weakening proof.

```
        ┌────────────────────────────────────────────┐
        │  START — read config/user.json (if present) + │
        │  config/answers.py + config/progress.json     │
        └──────────────────┬─────────────────────────┘
                           ▼
                 ┌────────────────────────┐
                 │  RESUME node          │  skills/resume/SKILL.md
                 │  exact file + MD5     │  → PICK/UPLOAD/POST gates
                 └─────────┬──────────────┘
                           ▼
                 ┌──────────────────┐
                 │  FIND  node      │  skills/find/SKILL.md
                 │  product cos QA  │  → live ATS API scan → dedupe vs progress.json
                 └────────┬─────────┘
                          ▼
                 ┌──────────────────┐
                 │  APPLY node      │  skills/apply/SKILL.md
                 │  ATS router      │  → pick recipe by ATS:
                 │                  │     recipes/workday.md · greenhouse.md
                 │                  │     lever.md · icims.md · linkedin.md
                 │                  │     phenom.md · breezy.md · jobvite.md · oraclehcm.md
                 └────────┬─────────┘
                          ▼
                 ┌──────────────────┐
                 │  VERIFY node     │  skills/verify/SKILL.md
                 │  PROOF GATE      │  email/confirmation/thank-you = DONE
                 │  (never infer)   │  → record config/progress.json
                 └────────┬─────────┘
                          ▼
                 ┌──────────────────┐
                 │  EMAIL node      │  skills/email/SKILL.md
                 │  recruiter       │  Gmail DRAFTS (never send) + Found-via
                 └────────┬─────────┘
                          ▼
                 ┌──────────────────┐
                 │  LEARN node      │  skills/learn/SKILL.md
                 │  attach lessons  │  → LESSONS/LESSONS-*.md per concern
                 └────────┬─────────┘
                          ▼
                 ┌──────────────────┐
                 │  TRACK node      │  skills/track/SKILL.md
                 │  applied vs not  │  progress.json + Gmail inbox →
                 │  applied report  │  applied_vs_not_applied.md / APPLIED.md
                 └────────┬─────────┘
                          ▼
                       LOOP → FIND (next company)
```

## DEDUPE (READ FIRST — never apply twice)
- Before every application, check `scratch/APPLIED.md`, `config/progress.json`, LinkedIn's Applied/Job Tracker state, and Gmail for prior submissions or confirmations. These checks are mandatory; never skip them to save time.
- Match normalized company, exact role, LinkedIn/ATS job IDs, employer domain, and prior status. Same role/company already attempted or confirmed = SKIP, even if a repost/new job ID appears. A different role at the same company is eligible only when it is demonstrably a distinct requisition and not already recorded.
- If sources conflict or identity/status is uncertain, do not apply; reconcile first. Fivetran is a known repeat-application failure: verify its existing tracker and Gmail history and never reapply to a role already attempted.
- Keep both trackers authoritative and current: record every attempt/blocker and update status/proof after submissions and Gmail verification; never overwrite historical facts.

## TWO-TAB SESSION (NON-NEGOTIABLE)
→ **`skills/REFERENCE.md#two-tab-session`** (single source). One FORM tab + one persistent GMAIL tab; never restart the browser/MCP while FORM holds data. Browser topology (one owner per channel): **`skills/REFERENCE.md#browser-topology`**.

## SESSION START GATE — FAIL CLOSED
Before any browser navigation, click, or form action:
1. Read `config/progress.json` and `scratch/APPLIED.md`, inspect LinkedIn Applied/Job Tracker, and search Gmail for prior application evidence; cache the next three exact role/company/LinkedIn-ID/ATS-ID/domain tuples.
2. List tabs and ensure one FORM tab plus one persistent GMAIL tab; never begin with only a blank FORM tab.
3. Classify all three as `DUPLICATE`, `MISMATCH`, `READY`, or `BLOCKED`; do not open an ATS for the first two. Apply only to verified high-revenue product companies or genuine GCCs.
4. Use one compact DOM extraction for candidate metadata; do not start with a huge full-page snapshot.
5. Keep a written state `{tab,url,company,role,job_id,phase,last_anchor}` and invalidate it after navigation/rerender/modal/tab changes.
If any item is incomplete, stop browser actions and finish preflight first.

## SESSION READ / CACHE CONTRACT (SPEED)
- Read the master, `RELIABILITY.md`, `REFERENCE.md`, the selected ATS recipe, and the relevant lessons once per session. Do not reread unchanged skill files for every role.
- Read local trackers once, extract the listing page once, and cache the next three candidate tuples. Do not rescan the same pages or reopen the same role unless the URL/status changed or the user explicitly asks to recheck.
- Keep a small state cache: `{tab, url, company, role, ats_job_id, phase, last_verified_anchor}`. Invalidate it only after navigation, rerender, modal transition, tab switch, or failed post-check.
- If a referenced file is absent (for example `config/profile.json`), do not retry it. Use the existing `config/user.json`/`config/answers.py` sources and record the missing-file blocker only when it affects the application.

## ACCOUNT ACCESS (USER-AUTHORIZED)
→ **`skills/REFERENCE.md#auth-priority`** (single source). Agent owns the full flow; user-only pauses are CAPTCHA/biometric and secrets with no approved vault. Never create duplicate accounts or store secrets in repo files.

## VISUAL STATE, IFRAMES, AND OVERLAYS
- An accessibility snapshot can omit a visible social-login control when it is rendered inside a cross-origin iframe. If `Continue with Google` appears missing, take a headed screenshot and inspect the HTML for `iframe[title="Sign in with Google Button"]` before concluding that Google login is unavailable.
- Use the normal iframe button via `page.frameLocator('iframe[title="Sign in with Google Button"]').getByRole('button').click()`. After a popup/redirect, list tabs once, remap by URL/title, select the exact Gmail account, and verify the authenticated page shows the account identity and Logout.
- A click error such as `locator.click: Timeout 30000ms exceeded` with a modal element intercepting pointer events means an overlay is open, not that the job card is broken. Inspect `role=dialog`/modal content, close its visible close control, reacquire the card locator, and retry once.
- For disputed UI state, capture screenshot plus scoped HTML/snapshot after the transition; visually inspect/OCR the screenshot and compare URL, title, account/menu text, and the role-specific anchor. OCR corroborates state but never replaces employer/Gmail proof.

## PI AUDIT CORRECTIONS — 2026-09-24
→ **`skills/REFERENCE.md#pi-audit-corrections`** (single source). Context boundary, navigation post-check, locator discipline, browser health, dynamic Rippling forms, and wait budget.

## EDGES (DRY — nodes point, never duplicate)
- FIND → VERIFY: always live-API check before applying (search indexes STALE fast)
- APPLY → VERIFY: captcha? → user solves (visible browser) → submit → proof
- TRACK → FIND: run find/tracker_reconcile.py before each FIND session (fresh APPLIED.md → dedupe)
- VERIFY → EMAIL: no ATS? recruiter channel
- LEARN → APPLY: read LESSONS/LESSONS-apply.md before every apply session

## CONSTANTS (single source)
→ **`skills/REFERENCE.md`** — identity (name/DOB/history), CTC (**22% → <current CTC> → <expected CTC>**), **last working day <your last working day> (serving notice)**, resume MD5 `<GENERATED_ON_SETUP>` + filename `Firstname_Lastname_Role.pdf`, saved answers. Resume mechanics: `skills/resume/SKILL.md`. Servers/tools: `skills/ops/SKILL.md`. Tracker: `scratch/APPLIED.md`.

## SPEED + TOOL-CALL DISCIPLINE (30% ROUND-TRIP TARGET)
→ **`skills/REFERENCE.md#browser-call-budget`** + **`skills/RELIABILITY.md`** (single source). Key invariants:
- Preflight/dedupe the next 3 roles once; cache the 6-field tuple; classify before opening any ATS.
- One transaction per stable state: scoped discovery → related actions → targeted readback.
- `browser_run_code_unsafe` reserved for power patterns (react-select commit, native-setter batch, `setInputFiles`, real keyboard, multi-field transaction); routine clicks/fills use the dedicated tools.
- `.fill()` replaces; condition waits over fixed sleeps; `browser_wait_for` canonical arg `{timeMs}`; cached tool names only.
- Route by win-rate: **GH embed > Phenom > LinkedIn EasyApply > SuccessFactors > iCIMS**.

## KAIZEN PROCESS (PDCA — continuous improvement, governs ALL sessions)
Every session runs the improvement loop and feeds the next:
- **P LAN** → set batch target (e.g. "5 product co QA/DSE verified").
- **D O** → pick channel by win-rate ORDER: GH embed > Phenom > LinkedIn EasyApply > SuccessFactors > iCIMS; use web_search→portal for roles not cleanly on LinkedIn.
- **C HECK** → hard-proof = success page (GH /confirmation, Phenom /applythankyou, LI "sent", SF "Successfully Applied") AND confirmation email in inbox. Never report from inference; re-read email for date.
- **A CT** → record APPLIED.md + progress.json (exact date + email proof) → standardize the win into skills → next session starts from the improved baseline.
Rules that turned sessions around (standardize, never regress):
- real trusted mouse beats JS .click() on React/custom editors
- ignore stale "blocked" — re-verify live (false-blockers NetApp, AcmeNine)
- web_search/SearXNG finds portal-only product-co QA roles
- GH/GH split-security-code + .email = repeatable hard win
