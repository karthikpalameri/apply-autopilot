---
name: apply
description: APPLY node — ATS router. Pick the recipe, run it, never re-open the form. Caveman.
parent: skills/SKILL.md
---

# APPLY (router)

```text
ATS detected → recipe:
  Workday      → skills/recipes/workday.md (probe 1st: core/wday_probe.py)
  Greenhouse   → skills/recipes/greenhouse.md
  Lever        → skills/recipes/lever.md
  SmartRecruiters → skills/recipes/smartrecruiters.md (spl-* custom elements)
  iCIMS        → skills/recipes/icims.md
  Phenom       → skills/recipes/phenom.md
  Oracle HCM   → skills/recipes/oraclehcm.md
  Jobvite      → skills/recipes/jobvite.md
  Breezy HR    → skills/recipes/breezy.md
  Avature      → skills/recipes/avature.md (guest path, select2, CLEARS selects on Next)
  SAP SuccessFactors → skills/recipes/sapsf.md (juic/rcm; resume upload = the "+" icon, NOT the label)
  BambooHR     → LESSONS-apply#bamboohr-securonix--full-recipe (Fabric fields: native-setter, getElementById, no id caching)
  Taleo (UHG)  → LESSONS-apply#taleo-uhg--optum--full-recipe (guest apply, no account wall)
  LinkedIn     → skills/recipes/linkedin.md (easy-apply)
  No ATS       → EMAIL node (recruiter draft)
```

## BROWSER STATE
- Follow `skills/SKILL.md` → **TWO-TAB SESSION**. FORM stays on the application; GMAIL is the only OTP/confirmation tab.
- Before any fill pass and after any unexplained timeout: `core/page_guard` — `require()` / `fill_report()` / short timeouts. Rule: **`skills/RELIABILITY.md#page-guard`** (single source; do not restate it here).

## SESSION START GATE — DO NOT SKIP
→ **`skills/SKILL.md#session-start-gate`** (single source). Cache three tuples, classify `DUPLICATE`/`MISMATCH`/`READY`/`BLOCKED` before opening any ATS; incomplete gate ⇒ next action is preflight.

## RELIABILITY + SPEED
- Read `skills/RELIABILITY.md` once before the session. Every click/fill/select/upload/submit needs a pre-check and same-call post-check.
- **Visual-control recovery:** an a11y snapshot may omit a Google/LinkedIn control inside an iframe. Inspect the HTML/iframe first; for genuine visual ambiguity follow `skills/REFERENCE.md#screenshot-budget-measured-2026-11-07--the-single-biggest-token-sink` (local cropped OCR). If a modal intercepts a click, inspect/close it, reacquire the target and retry once.
- **Speed:** → **`skills/RELIABILITY.md#speed-profile-30-target`** — three-role preflight, one transaction per stable page, condition waits, Gmail after each employer success (combined search only in explicit batch mode).
- Do not reread every skill/recipe or rescan the same LinkedIn pages for each role. Read the selected recipe once and reuse its proven selectors until a rerender invalidates them.
- Never parallelize actions sharing a form. Reacquire locators after rerenders and avoid repeated full-body snapshots when a scoped field/anchor check is sufficient.
- **No guessing at a failed Next/Submit.** Call `core/page_guard.fill_report()` first — it names the empty required fields in one round-trip (rule: `skills/RELIABILITY.md#page-guard`).
- **Typed decisions live in `core/decide.py`.** Field→answer planning (`plan_field`,
  `field_question`), submit-blocker classification (`gate_questions`, `gate_from`), and
  work-history validation (`validate_work_history`) — deterministic first, Jev second,
  main model last. Never re-implement these in the apply loop.
- Before submit, validate company/role/ATS ID, phone, **last working day 27 Nov 2026**, canonical resume filename, required selections, and all parsed work-history rows (Bottomline, Meredith, Cognizant).

## BROWSER CALL BUDGET (MANDATORY 30% SPEED GATE)
- Use the cached cloak tool names exactly — full list + no-invent rule at **`skills/REFERENCE.md#cached-cloak-tool-names`**.
- Do not retry an invalid namespace/tool spelling. Do not alternate ctl, MCP wrappers, and direct Playwright for the same field unless the post-check proves the first primitive failed.
- On a stable page: one scoped discovery call → one transaction call for related actions → one targeted post-check. A full-body snapshot is reserved for a state transition or final proof.
- Use `.fill()` to replace ordinary text; use Meta/Cmd+A + Backspace only before real keyboard typing. For selects, identify native versus custom once and use the proven commit method; do not probe several methods.
- After tool discovery, call cached names directly. Do not send `{describe: ...}` to `mcp__cloak_browser`; that proxy accepts `{tool, args}`. `browser_run_code_unsafe` must use `const { page } = cloak;` and not an `async (page) => ...` wrapper.
- Keep all same-page related actions in one short script, sequentially. Use parallelism only for independent read-only work; never parallelize fills, clicks, navigation, or submit on one form.
- **Context boundary:** inside `mcpScript` use `tools.cloak_browser_*`; inside the nested `browser_run_code_unsafe` string use `const { page } = cloak`; use `document`/`location` only inside `page.evaluate`. A navigation-inducing click gets a separate settled URL/anchor post-check.
- **Dynamic-form audit fix:** for Rippling/React forms, wait for the `?step=application` state, inspect `__NEXT_DATA__.props.pageProps.apiData.jobPost.activeJobApplication`, map required custom questions by UUID/test-id, then fill and read back the complete group (including resume filename and radio `aria-checked`) before advancing. Do not guess generated positional IDs or use an obsolete path.
- Replace arbitrary sleeps with one condition wait plus a role-specific anchor assertion. Retry at most once after a fresh locator; a second identical timeout or duplicate match is a blocker until new DOM evidence exists.

## THREE-ROLE PREFLIGHT (MANDATORY SPEED GATE)
For any requested multi-role batch, build the candidate queue from the mandatory Freehire first pass in `skills/find/SKILL.md` (supplement other sources only when the scan errors or yields too few matches), then check each role against the **ledger** (`core.applied_ledger.is_applied`), `scratch/APPLIED.md`, LinkedIn Applied/Job Tracker, and Gmail before opening any application. Mark each `DUPLICATE`, `MISMATCH`, `READY`, or `BLOCKED-PENDING-USER`. Apply only when the employer is verified as a substantial-revenue product company or a genuine GCC. Compare `{company, exact role, LinkedIn job ID, ATS job ID, employer domain}`; an already attempted/confirmed exact role is a duplicate even if reposted under a new ID. Fivetran is a known repeat-application warning: check all sources and skip any role already attempted. A LinkedIn card whose Apply URL resolves to a different employer/domain is a mismatch. Missing sensitive identity data such as PAN/Aadhaar/DOB is a blocker; never invent it. For `READY`, cache the exact ATS job ID and route, confirm credential/keychain readiness, then use one FORM tab and the persistent GMAIL tab.

## ACCOUNT ACCESS (AUTHORIZED — DO NOT SKIP ELIGIBLE ROLES)
→ **`skills/REFERENCE.md#auth-priority`** (single source). Auth order = Google → LinkedIn → email/password → email OTP. Keep FORM + GMAIL tabs; OTP sequence = webpage-request → Gmail refresh → return → enter fresh code. Agent owns the full flow; pause only for CAPTCHA/biometric or a generated password with no approved vault.

## ORDER (never skip)
1. Read `skills/RELIABILITY.md` and `skills/LESSONS.md` once (memory of this ATS); read only the selected recipe, not the full skill tree again for each role.
2. **`PICK()`** (from `core.resume_secure`) — verifies the exact resume + MD5 before opening the form
3. Fill basics → resume (`BEFORE_UPLOAD()` returns the verified path; setInputFiles that). Copy to hub handled by module.
4. Questions → error-driven (submit → read errors → fix ONE at a time)
5. Complete and verify all other safe required fields first (target ~99% of the application); at CAPTCHA, stop per **`skills/REFERENCE.md#standing-rule--captcha-handling`** (single source). Never bypass or solve CAPTCHA. Resume only after the user completes it.
6. **`POST()`** (from `core.resume_secure`) after submit — post-verify the uploaded resume still matches the known-good MD5
7. → VERIFY node (proof gate): employer success/confirmation page **and Gmail confirmation** required

## RESUME (MD5-GATED + PROFESSIONAL FILENAME — every apply, non-negotiable)
→ **`skills/resume/SKILL.md`** + **`skills/REFERENCE.md#resume`** (single source). Upload name `Your_Name_Resume.pdf` (never `resume.pdf`); MD5 `YOUR_RESUME_MD5`; gates `PICK()` → `BEFORE_UPLOAD()` → `POST()`; upload via `setInputFiles(BEFORE_UPLOAD())`, never a native picker.

## COMPLETENESS GATE — SCRAPE, THEN DECIDE (user instruction 2026-11-07)
Before parking a captcha-gated form, fill EVERY field, not "the ones I saw":

1. **Scrape the whole form first.** Dump every visible + shadow-DOM `input, select, textarea` with its label, type, required flag and current value. Shadow-DOM ATS (SmartRecruiters oneclick-ui, Keka, Eightfold) hide fields from `document.querySelector` — traverse `el.shadowRoot`, and target inner inputs as `input#id` (the host element `spl-input#id` shares the id, so a bare `#id` raises a Playwright *strict mode violation*).
2. **Count**: `filled/total`, and list every empty required field. A form is only "done" when `emptyRequired == []` and every custom select shows a chosen value (not its placeholder).
3. **Ask Jev** whether the form is ready to submit and whether the entered values match the user facts. Two `choice` questions, one call. Jev confirms/denies; it never writes a value.
4. **Only then park.** A parked tab must be *submit-ready*: captcha is the single remaining click. Set `document.title = 'PARKED-<Company>-CAPTCHA | 100% FILLED'` and scroll the widget into view.
5. **Re-verify after any failed submit.** A failed POST resets consent checkboxes and custom-select text fields (measured on Brivo: tools answer + consent both cleared). Re-read, refill, re-verify — never assume the form still holds.

Optional-but-present fields count. If the label carries no `*` it is still filled when the answer is known (equality monitoring, personal summary, tool lists). Leaving a known answer blank is a miss, not a shortcut.

## POWER TOOLS (work when nothing else does)
- `browser_run_code_unsafe` = FULL Playwright via the server-global `cloak` object: `const { page } = cloak; await page.getByRole(...).click(); await page.locator('input[type=file]').setInputFiles(path);` (do not wrap the code as `async (page) => {...}` on this MCP build). Clicking an Attach/Upload button is NOT the equivalent — it opens an OS dialog the harness cannot close; use `setInputFiles` (**`skills/resume/SKILL.md#upload-method`**).
- `browser_press_key` = the real keyboard tool (browser_keyboard is a phantom name)
- One-call sequencing: set related fields + read them back in ONE script; submit in that same transaction only when the submit pre-check passes (re-render wipes).

## CTC (always)
→ **`skills/REFERENCE.md#compensation`**: 22% hike = <your current CTC> → **<your expected annual INR>** (numeric fields: `3300000`); notice = **available from 28 Nov 2026 — last working day 27 Nov 2026**.

## SAVED USER-PROVIDED ANSWERS, CONSENTS & PREFERENCES
→ **`skills/REFERENCE.md`** (single source; see `SAVED USER-PROVIDED INDIA APPLICATION ANSWERS` and `USER-PROVIDED ANSWERS, CONSENTS & PREFERENCES`). Consult before asking a question or seeking consent. Reuse an answer when the employer, role/question, and consent scope match; do not ask again for that same scope unless wording or terms materially change. Employer-specific consent never generalizes. Record new explicit answers in REFERENCE with date and exact scope.

## LESSONS
- skills/LESSONS.md — **read the newest section first**; it is the freshest ATS knowledge (BambooHR Fabric, Taleo/UHG guest apply, LinkedIn new UI).
- SmartRecruiters → external careers site (Eurofins) → timebox + skip
- SmartRecruiters oneclick-ui → has its own recipe now (custom elements + shadow DOM); do NOT treat as "unknown ATS"
- GH school-db combo (no options) = block (Tekion/Edelman) → skip

## AFTER SUBMIT (mandatory)
- CAPTCHA handling: → **`skills/REFERENCE.md#standing-rule--captcha-handling`** (single source). After user resolution, resume, submit if still valid, and capture proof. Never claim success without the proof gate.
- Capture the positive employer final message and URL immediately in the same FORM state; do not navigate away and try to recover proof later.
- Check Gmail for prior application evidence during dedupe, and check Gmail after submission for confirmation. For this three-role batch, search once after each submission or use a clearly mapped batch search; never use LinkedIn/ATS acknowledgement alone as email proof.
- Update the **ledger** via `core.applied_ledger.record(...)` and `scratch/APPLIED.md` for every attempt, blocker, and verified outcome (mirror to `config/progress.json` only as a projection). Preserve historical entries; never silently omit or rewrite them.
- If page/email proof is absent, record `blocked` or `submitted-awaiting-email`, never `submitted-confirmed`.
- Easy-apply stuck-Review fix: use one bounded retry with a fresh locator and a condition wait; do not stack repeated clicks/sleeps.

## DO-NOT (typing sins)
- ❌ NEVER browser_type into a field with existing text — ALWAYS Meta+A + Backspace first.
- ❌ NEVER use stale refs (fields re-render — refs churn; re-snapshot before typing).
- ❌ NEVER guess field identity (a11y labels lie; verify the field has the value after typing).
- ✅ After every fill step → read the value back (evaluate) → confirm exact.
