---
name: apply-autopilot
description: MASTER skill — routes the job-hunt graph. Read me first; follow the edges.
version: 23.4.0
platforms: [macos]
---

# JOB-HUNT GRAPH (master)

**Global execution contract:** read `skills/RELIABILITY.md` (transaction contract) + `skills/REFERENCE.md` (constants · auth · two-tab · browser-call discipline) once before browser work. Every action requires a pre-check, action, and post-check; target 30%-fewer-round-trips without weakening proof. **Page health is a pre-check, not an assumption** — `core/page_guard.probe()` before a fill pass and after any timeout (rule: `skills/RELIABILITY.md#page-guard`).

```text
        ┌────────────────────────────────────────────┐
        │  START — read config/user.json (if present) + │
        │  config/answers.py + applied ledger     │
        └──────────────────┬─────────────────────────┘
                           ▼
                 ┌────────────────────────┐
                 │  RESUME node          │  skills/resume/SKILL.md
                 │  exact file + MD5     │  → PICK/UPLOAD/POST gates
                 └─────────┬──────────────┘
                           ▼
                 ┌──────────────────┐
                 │  FIND  node      │  skills/find/SKILL.md
                 │  product cos QA  │  → live ATS API scan → dedupe vs LEDGER
                 └────────┬─────────┘
                          ▼
                 ┌──────────────────┐
                 │  APPLY node      │  skills/apply/SKILL.md
                 │  ATS router      │  → pick recipe by ATS:
                 │                  │     recipes/workday.md · greenhouse.md
                 │                  │     lever.md · icims.md · linkedin.md
                 │                  │     phenom.md · breezy.md · jobvite.md · oraclehcm.md
                 │                  │     ashby.md  ← submit-proof trap: tab look
                 │                  │                 blank after success
                 └────────┬─────────┘
                          ▼
                 ┌──────────────────┐
                 │  VERIFY node     │  skills/verify/SKILL.md
                 │  PROOF GATE      │  email/confirmation/thank-you = DONE
                 │  (never infer)   │  → record to LEDGER (append)
                 └────────┬─────────┘
                          ▼
                 ┌──────────────────┐
                 │  EMAIL node      │  skills/email/SKILL.md
                 │  recruiter       │  Gmail DRAFTS (never send) + Found-via
                 └────────┬─────────┘
                          ▼
                 ┌──────────────────┐
                 │  LEARN node      │  skills/learn/SKILL.md
                 │  attach lessons  │  → skills/LESSONS.md
                 └────────┬─────────┘
                          ▼
                 ┌──────────────────┐
                 │  TRACK node      │  skills/track/SKILL.md
                 │  applied vs not  │  LEDGER + Gmail inbox →
                 │  applied report  │  applied_vs_not_applied.md / APPLIED.md
                 └────────┬─────────┘
                          ▼
                       LOOP → FIND (next company)
```

## DEDUPE (READ FIRST — never apply twice)
→ **AUTHORITY: `core/applied_ledger.py`** — append-only JSONL at `data/applied_ledger.jsonl`. `config/progress.json` is a derived projection for humans, **NOT** the dedupe source.
- Before every application, ask the ledger: `python -c "from core.applied_ledger import is_applied; print(is_applied('Co','Role'))"`. Also check `scratch/APPLIED.md`, LinkedIn's Applied/Job Tracker state, and Gmail. These checks are mandatory; never skip them to save time.
- Run `find/ledger_guard.py` before each session; exit 1 = the corpus shrank → restore before searching.
- Match normalized company, exact role, LinkedIn/ATS job IDs, employer domain, and prior status. Same role/company already attempted or confirmed = SKIP, even if a repost/new job ID appears. A different role at the same company is eligible only when it is demonstrably a distinct requisition and not already recorded.
- If sources conflict or identity/status is uncertain, do not apply; reconcile first. Fivetran is a known repeat-application failure: verify its existing tracker and Gmail history and never reapply to a role already attempted.
- Record EVERY attempt (submitted, blocked, in-progress) to the ledger immediately after the form action; a blocked role is still a duplicate. Never rewrite, dedupe, or delete ledger rows. Do not overwrite historical facts.

## TWO-TAB SESSION (NON-NEGOTIABLE)
→ **`skills/REFERENCE.md#two-tab-session`** (single source). One FORM tab + one persistent GMAIL tab; never restart the browser/MCP while FORM holds data. Browser topology (one owner per channel): **`skills/REFERENCE.md#browser-topology`**.

## DISCOVERY SOURCE GATE — FAIL CLOSED
At the start of every new job-search batch, run the mandatory keyless Freehire public-catalogue first pass defined in `skills/find/SKILL.md` before web, LinkedIn, Naukri, or ATS discovery. Use `--strict --json` for product-only requests and `--json` when the user also permits genuine GCC/in-house roles. If the scan errors or returns no candidates, record that explicitly before using supplemental sources. Freehire discovery does not replace official-ATS verification or duplicate checks.

## SESSION START GATE — FAIL CLOSED
**Step 0 (one command, ~11 s, replaces 1 below):**
```text
.venv/bin/python find/preflight.py        # guard + sweep + harvest + classify -> READY table
```
Then for each READY row: pick 2, open the LinkedIn job view, decode `/safety/go/?url=` for the employer ATS, apply.

Before any browser navigation, click, or form action:
1. Run `find/ledger_guard.py` (must pass), then the mandatory Freehire first pass above, then read the **ledger** (`core.applied_ledger.is_applied`), `scratch/APPLIED.md`, inspect LinkedIn Applied/Job Tracker, and search Gmail for prior application evidence; cache the next three exact role/company/LinkedIn-ID/ATS-ID/domain tuples.
2. List tabs and ensure one FORM tab plus one persistent GMAIL tab; never begin with only a blank FORM tab.
3. Classify all three as `DUPLICATE`, `MISMATCH`, `READY`, or `BLOCKED`; do not open an ATS for the first two. Apply only to verified high-revenue product companies or genuine GCCs.
4. Use one compact DOM extraction for candidate metadata; do not start with a huge full-page snapshot.

### PICKING PRODUCT COMPANIES FAST (proven 2026-11-05)
The search listing is full of staffing/consulting decoys. Cheap 3-step filter:
1. **Bulk-dedupe first, then pick.** Diff the 500-row `product_companies.md` master against the whole ledger in one script (~404 never-tried). Pick from that set, not from whatever the search page shows.
2. **Search → product master.** Lift `{id, company, role}` for all cards, then check each company against the master list + ledger. Anything absent from both is likely a body-shop (Arohana, Maven, Live Connections, Trigent, ACL Digital, QAAgility).
3. **Confirm on the job page, not the card.** Read the "About the company" block: real product signals are `Software Development` / `Financial Services` / `Technology, Information and Internet` plus a concrete product story. `IT Services and IT Consulting` = consulting = skip for a product-company request. Also sanity-check the level and pay band — a `3-6 years` req at `5 INR/yr` is a MISMATCH for an 8-year senior, even without a ledger hit.
4. **Re-check status before applying.** Old delisted cards still render. The job page shows `Application status | Application submitted | <age>` when already done (found Angel One 18h, Ping Identity 1mo this way) — that is a `DUPLICATE` even with no ledger row.
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
- An accessibility snapshot can omit a social-login control inside a cross-origin iframe. First inspect the DOM for `iframe[title="Sign in with Google Button"]`; if that cannot settle the state, use the local cropped OCR procedure in `skills/REFERENCE.md#screenshot-budget-measured-2026-11-07--the-single-biggest-token-sink`.
- Use the normal iframe button via `page.frameLocator('iframe[title="Sign in with Google Button"]').getByRole('button').click()`. After a popup/redirect, list tabs once, remap by URL/title, select the exact Gmail account, and verify the authenticated page shows the account identity and Logout.
- A click error such as `locator.click: Timeout 30000ms exceeded` with a modal element intercepting pointer events means an overlay is open, not that the job card is broken. Inspect `role=dialog`/modal content, close its visible close control, reacquire the card locator, and retry once.
- For disputed UI state, read scoped DOM/URL/title first, then local cropped OCR only if necessary. OCR corroborates state but never replaces employer/Gmail proof; never send an image into model context.

## PI AUDIT CORRECTIONS — 2026-09-24
→ **`skills/REFERENCE.md#pi-audit-corrections`** (single source). Context boundary, navigation post-check, locator discipline, browser health, dynamic Rippling forms, and wait budget.

## EDGES (DRY — nodes point, never duplicate)
- FIND → VERIFY: always live-API check before applying (search indexes STALE fast)
- APPLY → VERIFY: captcha? → user solves (visible browser) → submit → proof
- TRACK → FIND: run find/tracker_reconcile.py before each FIND session (fresh APPLIED.md → dedupe)
- VERIFY → EMAIL: no ATS? recruiter channel
- LEARN → APPLY: read skills/LESSONS.md before every apply session

## CONSTANTS (single source)
→ **`skills/REFERENCE.md`** — identity (name/DOB/history), CTC (**22% → <your current CTC> → <your expected annual INR>**), **last working day 27 Nov 2026**, resume MD5 `YOUR_RESUME_MD5` + filename `Your_Name_Resume.pdf`, saved answers plus dated, strictly scoped user consents/preferences. Resume mechanics: `skills/resume/SKILL.md`. Servers/tools: `skills/ops/SKILL.md`. Tracker: `scratch/APPLIED.md`.

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
- **A CT** → record to **ledger** (`core.applied_ledger.record`) + mirror APPLIED.md (exact date + email proof) → standardize the win into skills → next session starts from the improved baseline.
Rules that turned sessions around (standardize, never regress):
- real trusted mouse beats JS .click() on React/custom editors
- ignore stale "blocked" — re-verify live (false-blockers NetApp, StoneX)
- web_search/SearXNG finds portal-only product-co QA roles
- GH/GH split-security-code + .email = repeatable hard win

## CAVEMAN STYLE — ALWAYS (hard rule, all nodes)
Talk caveman. Always. Every reply, every note, every ledger proof.
- Short line. Fact only. No prose. No big word. No essay.
- Format: `Path — result — next`. One line per item.
- Table only if >2 rows. Else line.
- Never pad. Never repeat ask. Never say "I will now".
- Skill/doc/lesson files: write caveman-terse too (KISS, low token).
- Captcha: fill all first, park, user solve, me take proof.
Applies to: SKILL.md, REFERENCE.md, APPLIED.md, LESSONS-*.md, scratch notes, chat.
