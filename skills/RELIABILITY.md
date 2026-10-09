# AUTOMATION RELIABILITY + SPEED CONTRACT

Applies to every browser/ATS action in this skills directory. Target: **30% fewer browser/tool round trips** without sacrificing proof. Constants, auth priority, two-tab, and cached tool names live in **`skills/REFERENCE.md`** — this contract covers transaction discipline.

## ONE-PASS SESSION SETUP
- Read the master skill, this contract, the selected ATS recipe, and its lessons once. Do not reread the unchanged skill tree for every role.
- Read `config/progress.json` and `scratch/APPLIED.md` once; extract one listing page once; cache the next three `{company, role, LinkedIn ID, ATS job ID, domain, route}` tuples.
- Classify each tuple before opening its ATS: `DUPLICATE`, `MISMATCH`, `READY`, or `BLOCKED`. Do not spend browser calls on the first two.
- Keep one FORM tab and one reusable GMAIL tab. Do not rescan a listing page or reopen a completed/blocked role unless its URL/status changed or a user explicitly requests a recheck.
- Missing local files are not retry loops: use the configured source (`config/user.json`/`config/answers.py`) and continue only if the needed fact exists.

## ACTION TRANSACTION
Every click, fill, select, upload, navigation, and submit is one transaction:

1. **PRE-CHECK (cheap, same call where possible)**
   - Confirm the intended tab/form URL and page identity.
   - Re-snapshot only the relevant region; locate one unique target by role/label/text.
   - Confirm target is visible, enabled, and not stale; for text fields read the current value before clearing.
   - For submit, confirm required fields/errors are known and the intended role/company is still shown.
2. **ACTION**
   - Click the unique target or clear then fill/type the exact value.
   - Prefer one short `browser_run_code_unsafe` sequence for all related actions on the same stable page. Keep actions sequential on one form; use `Promise.all` only for independent read-only waits/reads.
3. **POST-CHECK (same call)**
   - Click: verify the expected state transition (URL, modal, selected value, button state, or visible message).
   - Text: read the field value back and require exact equality; if it differs, stop and repair.
   - Select/upload: read the selected option or filename back.
   - Navigation: verify URL/title and a role-specific anchor before continuing.

A failed post-check means the action did not happen: re-snapshot, use a fresh locator, retry once, then record the exact blocker. Never continue on an unverified action.

## SPEED PROFILE (30% TARGET)
- Parallelize ONLY independent read-only work; never parallelize actions sharing a tab/form.
- One snapshot per page/state and one DOM extraction for all visible cards/fields; no snapshot after every unchanged read.
- Stable-state budget: **one scoped discovery → one related-action transaction → one targeted readback**. Never a tool call per field.
- Refs are invalid after rerender — reacquire once after a state transition, not preemptively. Cache locators/DOM metadata only inside the current script call.
- Condition waits (`waitForURL`/visible/enabled/expected text) over fixed sleeps; one short settle wait only after a React/navigation transition.
- Use `core/browser.py` ctl fast path for stable selectors; MCP/Playwright only for arbitrary React controls or recovery.
- DOM/text assertions before OCR; OCR/screenshots reserved for click ambiguity and final proof.
- Bounded retries: one action retry after a fresh snapshot; CAPTCHA/OTP/user-only security = stop condition. Loop breaker: never repeat the same failed action/URL/reset-link/discovery twice without new evidence — record the blocker and move on.
- Fast primitives: `.fill()` replaces (no Meta+A); native `selectOption()` for native selects; React selects = click → `pressSequentially` → wait visible exact option → click; uploads = `setInputFiles()` on the existing input + read filename back (never a native picker).

## TOOL-CALL DISCIPLINE
- Use known tool names directly after one discovery — cached list at **`skills/REFERENCE.md#cached-cloak-tool-names`**; `browser_run_code_unsafe` uses `const { page } = cloak;` (never `async (page) => …`); `browser_wait_for` arg = `{timeMs: <int>}`.
- Never alternate malformed wrappers/namespaces to find a working spelling — correct the call shape once, then continue with the known tool.

## SESSION-LOG FINDINGS — 2026-09-25 (fresh .pi audit)
From the latest session logs (2026-09-24 + 2026-09-25), three avoidable costs dominate. Bake these in:
1. **`browser_run_code_unsafe` overuse** — 54% of browser calls (274/506) were run_code_unsafe doing routine work the dedicated tools do cheaper (199 `locator()`, 143 `getByRole`, 136 `.click()`, 127 text reads, 55 `.fill()`, 48 `.count()`). Reserve run_code_unsafe for the 5 power patterns in **`skills/REFERENCE.md#browser-call-budget`**; use `browser_click`/`browser_fill_form`/`browser_select_option`/`browser_snapshot`/`browser_evaluate` otherwise.
2. **Inconsistent `browser_wait_for` arg names** — logs showed 4 spellings (`time`, `timeMs`, `ms`, `condition`/`ms`). Canonical form is **`{timeMs: <int>}`**; use condition waits (`waitForURL`/selector/visible/enabled) over fixed sleeps.
3. **Hallucinated tool names** — garbled names like `browser_run_code_unsafe 合乐 code?`, `browser_press_key_uuid`, `functions.mcp__cloak_browser` were emitted and wasted round trips. The cached name list in **`skills/REFERENCE.md#cached-cloak-tool-names`** is the ONLY valid set — never invent a spelling.

## PI AUDIT GUARDRAILS — 2026-09-24
→ **`skills/REFERENCE.md#pi-audit-corrections`** (single source). Context boundary, navigation post-check, locator discipline, dynamic forms, browser health, wait budget (2,310 `waitForTimeout` / 2,396.725 s).

## QUEUE AND BLOCKER CONTROL
- At session start, perform one read-only batch of tracker/Gmail/listing checks and cache three candidates. Never open an ATS for a role already present in either tracker, even if LinkedIn labels it merely Saved, Viewed, or Applied.
- Before filling, compare LinkedIn company/title/job ID with the ATS title/company/domain. A mismatch is a blocker; preserve the exact URL/text and move to the next cached role.
- Treat required unknown sensitive fields (PAN, Aadhaar, UAN, unknown DOB) like CAPTCHA: stop before submission and never fabricate values.
- For account walls, verify secure credential readiness before starting signup. Store a generated credential in the OS keychain first, retain it through immediate sign-in, and stop after one bounded recovery attempt.
- After a submit, capture employer proof and query Gmail once for all queued roles. Do not convert employer-only success into a verified tracker record.

## FIELD RULES
- Before entering text: Meta+A + Backspace (or `fill`, which replaces) and verify the field is empty/replaced.
- After entering text: read back exact value immediately.
- Never use stale accessibility refs after a rerender; reacquire by role/label.
- Never use broad text clicks when duplicate matches exist; narrow by role, container, or exact text.
- Submit only after the submit pre-check; after submit, follow `skills/verify/SKILL.md` hard proof.

## AUTHENTICATION TRANSACTION (NO LOOPS)
- Treat sign-up, sign-in, password reset, and email verification as a state machine: `FORM → request → Gmail message → fresh link → credential action → post-check`.
- If no existing credential is available, the agent may generate one strong unique password only after confirming an approved password manager or OS keychain is available. Store it in that vault before entering it, keep it in memory through immediate sign-in, and verify the authenticated state. Never generate and lose it. Never put credentials in code, logs, `progress.json`, skill files, or gitignored repository files.
- A reset link is single-use. Before opening one, verify the Gmail message is newer than the request and the link/token is different from the last consumed link. Never reuse a consumed link.
- Maximum: one reset request and one recovery attempt per site/session. If the new message/link is absent or stale, stop and record the exact blocker; do not click Forgot Password repeatedly.
- After account creation/reset, complete sign-in in the same transaction while the credential is still in memory, then verify the authenticated application URL/state. If no approved vault is available for a generated credential, stop and use a user-provided credential or visible user entry.

## PROOF LOGGING
Record only verified outcomes: exact success text/URL for submits, exact blocker for failures, and date/company/role in `config/progress.json`. Do not claim success from a missing button, closed form, or inferred navigation.
