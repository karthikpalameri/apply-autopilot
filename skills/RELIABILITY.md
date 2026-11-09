# AUTOMATION RELIABILITY + SPEED CONTRACT

Applies to every browser/ATS action in this skills directory. Target: **30% fewer browser/tool round trips** without sacrificing proof. Constants, auth priority, two-tab, and cached tool names live in **`skills/REFERENCE.md`** — this contract covers transaction discipline.

## BOUNDED ASYNC I/O (measured 2026-11-07)
- **Probing many DIFFERENT hosts is not a pooling problem, it is a scheduling problem.** 410 company careers pages x 2 paths = 820 GETs; a thread pool parks workers on dead domains (3.2 s per company, 242 s for the batch, zero results). Use `core/fetch.py::fetch_many(urls, timeout=2.0, deadline=15.0)` — one event loop, hard wall-clock deadline, returns whatever answered. Same module owns `get_json`, `get_text`, `post_json`.
- **`asyncio.run()` breaks your deadline.** It calls `shutdown_default_executor()`, which JOINS the DNS worker threads; httpx resolves names through anyio threads that a cancel cannot kill, so a 3 s deadline measured **30 s**. Build the loop yourself, `run_until_complete(wait_for(...))`, then `loop.close()` without joining. `core.fetch.fetch_many` documents this inline — do not "simplify" it back to `asyncio.run`.
- **Prefilter before regex.** One regex sweep over a 449 KB careers page took 8.5 s; `if ".greenhouse.io/" not in html.lower()` is O(n) and rejects the ~90% of pages that embed no ATS, dropping it to 0.2 s. Cheapest test first, always.
- **Bound the batch, not each item.** One shared deadline for the whole set beats a per-item timeout multiplied by 400.

## ONE-PASS SESSION SETUP
- Read the master skill, this contract, the selected ATS recipe, and its lessons once. Do not reread the unchanged skill tree for every role.
- Read the **ledger** (`core/applied_ledger.py` → `data/applied_ledger.jsonl`) and `scratch/APPLIED.md` once; extract one listing page once; cache the next three `{company, role, LinkedIn ID, ATS job ID, domain, route}` tuples. `config/progress.json` is a derived projection, not the dedupe authority.
- Classify each tuple before opening its ATS: `DUPLICATE`, `MISMATCH`, `READY`, or `BLOCKED`. Do not spend browser calls on the first two.
- Keep one FORM tab and one reusable GMAIL tab. Do not rescan a listing page or reopen a completed/blocked role unless its URL/status changed or a user explicitly requests a recheck.
- **Grant permissions + geolocation once at session start (2026-11-05).** A permission prompt left unanswered *blocks the apply*; a denied one is worse — it is scored against the candidate. Do it before the first form, not after a hang. `RELIABILITY.md` rule 12.
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
- Fast primitives: `.fill()` replaces (no Meta+A); native `selectOption()` for native selects; React selects = click → `pressSequentially` → wait visible exact option → click; uploads → **`skills/resume/SKILL.md#upload-method`** (injection only, never a native picker).
- **Uploads: `browser_file_upload` is a trap.** The chooser-based tool times out (5s) on Greenhouse/SmartRecruiters/Workday because the native dialog never fires. `setInputFiles` on the input directly — one call, no chooser, works even when the input is `visually-hidden` behind a styled wrapper. Full procedure + measured proof: **`skills/resume/SKILL.md#upload-method`**.
- **A vanished file input does NOT mean the upload failed.** Greenhouse replaces `input[type=file]` with a preview chip after a successful upload. `!!document.getElementById('resume')` returns `false` on success. Verify by reading the wrapper text / body text for the filename instead.

## BOUNDED SCROLLING

<sub>single source — measured 2026-11-05</sub>

**Symptom users report: "the page scrolls up and down for many seconds."** Cause: hand-written scroll loops that always run to the end of the list, even after the target is found or when it was never there.

Measured on this build's Chromium:
| Recipe | Loop | Cost |
|---|---|---|
| `recipes/workday.md` | `grid.scrollTop += 600` ×40 + 120 ms | **4.87 s**, 24 000 px |
| `recipes/linkedin.md` | `ul.scrollTop += 2000` ×14 + 250 ms | **3.53 s**, 28 000 px |
| `recipes/naukri.md` | `mouse.wheel(0,3500)` ×5 + 1.4 s | **7.03 s** |

- **ONE owner: `core.ui.scroll_until(predicate_js, container=None, max_ms=3000)`.** Never hand-write a scroll loop.
- It stops on four conditions, whichever comes first: **predicate true**, **container at its real bottom**, **`scrollTop` stopped moving** (stuck), or **`max_ms` budget spent**. On a miss it returns `False` in one step, not forty.
- Two traps it eliminates: scrolling the **document** when the target lives inside a scroll **container**, and adding to `scrollTop` past `scrollHeight - clientHeight` (which silently does nothing but keeps the loop spinning).
- For page-load scrolling, poll the condition you actually want (`cards >= 20`) instead of a fixed wheel count.
- Do not use `mouse.wheel` for content that lives in a container — wheel targets whatever is under the cursor.

## TOOL-CALL DISCIPLINE
- **Never reach for Node internals in `browser_run_code_unsafe`.** `process.binding(...)` is off-limits: one
  `process.binding('spawn_sync')` call killed the browser server and every open form with it (2026-11-07).
  There is no `require`; a secret reaches a form only through the user's own hands or a tool argument.
- Use known tool names directly after one discovery — cached list at **`skills/REFERENCE.md#cached-cloak-tool-names`**; `browser_run_code_unsafe` uses `const { page } = cloak;` (never `async (page) => …`); `browser_wait_for` arg = `{timeMs: <int>}`.
- Never alternate malformed wrappers/namespaces to find a working spelling — correct the call shape once, then continue with the known tool.

## SESSION-LOG FINDINGS — 2026-09-25 (fresh .pi audit)
From the latest session logs (2026-09-24 + 2026-09-25), three avoidable costs dominate. Bake these in:
1. **`browser_run_code_unsafe` overuse** — 54% of browser calls (274/506) were run_code_unsafe doing routine work the dedicated tools do cheaper (199 `locator()`, 143 `getByRole`, 136 `.click()`, 127 text reads, 55 `.fill()`, 48 `.count()`). Reserve run_code_unsafe for the 5 power patterns in **`skills/REFERENCE.md#browser-call-budget`**; use `browser_click`/`browser_fill_form`/`browser_select_option`/`browser_snapshot`/`browser_evaluate` otherwise.
   **REGRESSED 2026-11-06: 305/798 = 38%** again (2 applies cost $1.02 / 794 turns). It was the *only* tool with double-digit errors — 20 of 27 failures, 14 of them `Timeout` — i.e. the expensive tool is also the unreliable one. Hard budget: **if a plain MCP op exists, run_code_unsafe is disallowed.** Reach for it only for the 5 power patterns, and give every call a single action (a 30s tool timeout kills the page handle and cascades).
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

## PAGE GUARD — ONE CHECK BEFORE ANY FILL, AND AFTER ANY UNEXPLAINED TIMEOUT

<sub>the check that would have prevented 2026-11-07's dead-browser loop; owner: `core/page_guard.py`</sub>

**Why a status check is not enough.** The ctl server's `status` reads the cached `PAGE.url`, which
still answers after the page is gone: measured `{"ok": true, "status": "ok"}` while every real
op returned `Target page, context or browser has been closed`. The agent retried into a dead
browser and the run stalled with no message. `core/page_guard.probe()` is the only truthful health
check; `status` is the bridge, `probe` is the page.

| Call | Answers | Use when |
|---|---|---|
| `probe()` | `{state: ok\|dead\|frozen, dialogs}` — never raises, bounded | before a fill pass; after any timeout |
| `require()` | same, but raises `PageDead`/`PageFrozen` | start of an apply step |
| `fill_report()` | `[{kind, label, id}]` of **empty required fields** | before Next/Submit |
| `wait_ready(js)` | bool, polls `core.ui.until` | after a click that changes step |

```python
from core.page_guard import require, fill_report, PageFrozen, PageDead
try:
    require("step2")
    ...fill...
    missing = fill_report("step2")      # read errors BEFORE clicking Next
    if missing:
        raise PageFrozen(f"{len(missing)} required fields empty")
except PageDead as e:
    ...reopen a tab, never retry the same page...
except PageFrozen as e:
    ...dialog/picker: see the owner section below, retry ONCE...
```

- **All timeouts are short by default.** `PROBE_TIMEOUT = 3.0` s; healthy pages answer in ms. Waiting
  longer only hides a frozen page behind silence. Never pass 30 s to a pre-check.
- **One round-trip per question.** `fill_report` is a single JS expression, so field count does not
  change the cost. It returns field names, so a failed Next is never diagnosed by guessing.
- **Never retry a dead page.** `PageDead` means the page or browser is gone: re-open and re-navigate,
  or stop and record `blocked`. Retrying the same handle is the loop that wastes a session.
- **Dialogs are accepted once, at launch**, by the server (`runtime/server.py:_arm_dialog_handler`),
  which keeps their text in `DIALOGS` and reports the count in `probe()`. Scripts no longer need to
  register `page.on('dialog')` — that was per-form boilerplate. Do NOT auto-accept destructive
  confirms; if `probe()` reports dialogs and the action still fails, read `DIALOGS` before continuing.

## NATIVE DIALOGS (alert/confirm/prompt) — ACCEPT, THEN VERIFY

<sub>one `alert()` on a live ATS form stalls every later action; measured 2026-11-07</sub>

- **A native dialog freezes the page.** Symptom set: `locator.click/setInputFiles: Timeout 30000ms exceeded`, `page.evaluate: document is not defined`, `This operation was aborted`, MCP snapshots returning only a footer. The page is not broken — a modal JS dialog is waiting for a human. Confirm with `page_guard.probe()` → `state: frozen` (the round-trip times out), which distinguishes it from `dead`.
- **One owner in scripts: `browser_handle_dialog({accept:true})`.** It resolves the *pending or next* dialog and returns its text (`Accepted dialog: alert — <text>`). Call it the moment two consecutive actions time out on the same page; read the text back to know what happened (e.g. `You have Uploaded Resume Successfully.` = the upload already succeeded). The launch-time handler above covers dialogs that appear later; this tool covers the one already blocking.
- **Accept only after reading.** Confirm the dialog text is a benign status/permission prompt, never a destructive confirm ("discard changes", "delete application"). Destructive = dismiss (`accept:false`) or stop.
- **Post-check after accept:** re-read URL + one anchor (resume filename, step name) before the next action; a dialog accept does not prove the action committed.
- A dialogs-blocked call must be retried ONCE after the accept. Do not re-run the same fill/upload blindly — the blocked action usually committed before the dialog appeared.
- Cousin blockers, one owner each: HTML overlay intercepting pointer events → `skills/ops/SKILL.md`; native OS file picker → `skills/resume/SKILL.md`; permission/geolocation prompt → rule 12.

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
Record only verified outcomes: exact success text/URL for submits, exact blocker for failures, and date/company/role via `core.applied_ledger.record(...)` (append-only — the authority). Mirror into `config/progress.json` only as a human-readable projection. Do not claim success from a missing button, closed form, or inferred navigation.

## STOP RULES (added 2026-11-05 — each of these cost 5+ wasted calls)

**1. Silent submit no-op = captcha, not a field.**
Valid form + zero errors + no navigation + submit still enabled, 2 attempts → reCAPTCHA/hCaptcha token. Screenshot, hand to user, move to the next company in the same turn. Do **not** re-fill.

**2. Value committed ≠ value correct.**
After every select/radio, **read the committed label back and assert the expected string**. `ArrowDown`-indexing silently lands one option off (recorded ₹55–65 LPA when the answer was ₹40–55 LPA). One readback beats one apology.

**3. Gmail beats the ledger for dedupe.**
Before submitting any form, search Gmail for the company in the same pass as the ledger check. The ledger is lossy — Genea was missing from it but had a "Thank you for applying" email from the prior day.

**4. Audit off-screen required fields before declaring a form complete.**
Greenhouse embeds and SmartRecruiters hide questions above and below the viewport. Inspect the form's required inputs, custom controls and validation flags through scoped DOM reads and bounded scrolling; read back all answers before submit. For truly visual ambiguity, use the local cropped OCR path in **`skills/REFERENCE.md#screenshot-budget-measured-2026-11-07--the-single-biggest-token-sink`**. Never send a full-page image to the model.

**5. The job pool is now the bottleneck.**
After several in-session applies, board sweeps return mostly duplicates. Reuse `find/freehire_sweep.py india --all`, `find/deep_sweep.py`, `find/deep_sweep2.py` — don't invent new slug lists (a 500-board guess-wave produced 0 new roles).

**6. "Account wall" is not "captcha" — classify before filling (added 2026-11-05).**
Of 7 blocked sites in one session, 5 were account walls, not captchas. Check the landing page for `Sign In` / `Create an account` **before** entering any data. Record ledger status `waiting-user-credentials`, never `waiting-user-captcha` (both join the canonical status vocabulary with `waiting-user-captcha` from `REFERENCE.md#standing-rule--captcha-handling`). Real blockers seen: Workday step 1/6 create-account, SuccessFactors login gate, Amazon passport (account exists, no stored password).
→ Resolve the wall via **`REFERENCE.md#auth-priority`**, not by parking it.
→ Search the ATS for a **guest path first**: Avature's `Without Resume` / `From Device` submits with no account at all. Saves the whole credential dance.

**7. Zero-height captcha wrapper ≠ no captcha (added 2026-11-05).**
`.h-captcha { height: 0 }` is a **layout** artifact, not an absence. Enumerate `page.frames()` for `hcaptcha` / `recaptcha` URLs and read each frame's `body.innerText`: `Find the THREE tiles…` or `Please try again. ⚠️ Verify` = live challenge → stop per `REFERENCE.md#standing-rule--captcha-handling`. Reporting "no captcha" from a DOM query alone is a false negative that costs a wasted submit cycle.

**8. Re-verify ALL fields immediately before submit — forms silently reset (added 2026-11-05).**
Two confirmed resets in one session: Greenhouse wipes the resume input + text answers after a custom-question re-render; Avature clears **all 9 `<select>` answers** when `Next` is clicked, and the error banner then reports them as untouched though you set them. Mitigation: set values and click Next in the **same tick**, and re-read every required value right before submit. In one case (`#school--0`) the typed label showed in the input while no valid option was committed — read the committed label, not the input value.

**9. Enterprise reCAPTCHA is a hard stop — no CAPTCHA-solving API here (standing rule).**
→ **`REFERENCE.md#captcha--no-solving-no-api-key-standing-rule`** (single source). CAPTCHA
is never auto-solved: finish safe fields, leave the page for the user, record
`waiting-user-captcha`. Do not restate the mechanism here.

**10. "Finish the goal" enforcement — never abandon mid-goal (added 2026-11-05, user-mandated).**
The user sets a goal (e.g. "apply 3"). It stays open until **all** of it is done. Abandoning early to report a blocker is a failure, not a status update. Before ever saying "blocked"/"can't":
- Re-read `skills/` for an existing tool for that exact obstacle. **Email OTP was the case here**: `core/gmail_read.py` reads the live Gmail tab and `core/gmail_otp.py` reads IMAP — both existed, both were ignored, and the goal was declared blocked. `REFERENCE.md:50` already said a code-gate is *"a 2-minute win, not a blocker"*.
- Loop: diagnose → tool → verify → continue. Only two things justify stopping: **(a)** a real CAPTCHA (per `REFERENCE.md#standing-rule--captcha-handling`), or **(b)** data only the user holds (PAN/Aadhaar/DOB) — and even then, fill **everything up to the submit button** first, so the remaining work is one click.
- Never trade a completed goal for an explanation. Do the work, then report.

**11. Email-code gates are the cheapest win in the ATS maze (added 2026-11-05).**
Oracle HCM / Ralliant / Greenhouse send a 6-8 digit code. Procedure: keep the **Gmail tab already open** (never "Gmail isn't logged in" without opening `mail.google.com` first — it usually is), search the sender, open the newest match, regex `\b\d{4,8}\b`, then fill per-char boxes (`pin-code-1..6` on Oracle, `#security-input-0..7` on Greenhouse) via native setter + `input`/`change`/`keyup`, and click `VERIFY`. Cached Oracle profiles auto-fill name/email/country/address from a **prior** Oracle application — re-verify, don't retype. Upload with `setInputFiles`; `browser_file_upload` times out on hidden inputs (`#attachment-upload-7` is `display:none`).

**11b. VIOLATED AGAIN 2026-11-06 — the IMAP-only trap.** Rule 11 was already correct and was still broken: `imaplib` returned `AUTHENTICATIONFAILED`, the agent concluded *"cannot be solved without an app password"*, and declared the goal blocked — **while Gmail was already logged in in the browser**. Opening `mail.google.com` required no password and the code was readable in seconds. Hard ordering, do not re-derive:
```text
1. browser tab  mail.google.com/mail/u/0/   <- ALWAYS FIRST (profile holds the cookie)
2. keychain('gmail') + core/gmail_otp.py   <- fallback only, needs 16-char app password
3. NEVER conclude "blocked" from an IMAP failure alone
```
Mechanics that cost calls: the code is **single-use and short-lived**, and Greenhouse **re-sends the same code** while the form sits unsubmitted — so re-reading the inbox returns the *same dead* code (`Invalid security code`). A hard `page.reload()` clears the stale code+banner and the next submit issues a fresh one (`88851365` dead → `80240858` live). Details: `REFERENCE.md#credential-vault--macos-keychain-only`.

**13. PARK, NEVER TERMINATE (user-mandated 2026-11-06).**
When a submit cannot complete, the deliverable is a **fully-filled tab left open**, not a closed browser and not a report. Measured this session: **798 tool calls, 0 `close` calls, 3 tabs alive at end** — that is the target behaviour, match it.
- Fill **everything** first (all fields, all selects, résumé attached), verify `gaps: []`, then hand over.
- Ledger status reflects the parked state (`waiting-user-captcha`, `waiting-user-email-code`, `waiting-user-credentials`), never `blocked`.
- Only after the tab is filled and parked may you move to the next company **in the same turn**.
- **REGISTRY — the handover must carry an address.** A parked form is a deliverable, so its ledger row states `tab=<tN>`, the full URL incl. `step`, and the **one** remaining action; the same three facts go to the user in that turn. The field-level state schema itself is owned by `skills/SKILL.md#session-start-gate` step 5 — do not restate it here.
- **Reserve the tab id** for the parked form: discovery, LinkedIn and proof work use a different tab; never navigate a parked tab to another domain, never reuse its slot. Re-list tabs before every switch and resolve by URL, not index.
- **End-of-session inventory**, printed as a table: `tab · company · role · step · one remaining action`. A park nobody can locate costs the same as a closed tab.
- Never `close` a tab holding entered data; if a tab must be freed, park it and say so.
- **SCREEN-OUT ≠ PARK.** A form opened only to *read* the gate carries no state, so it needs no parked tab — but it does need evidence and a notice:
  1. record the `skipped-*` ledger row (vocabulary owned by the classification step in `skills/apply/SKILL.md`) with the **gate evidence quoted** and the form URL — a skip with no evidence is indistinguishable from a silent failure;
  2. state it to the user **in the same turn**, in the running list, not only in the end table;
  3. reusing that tab is allowed only after proving zero entered fields (no `input` with a non-empty value, no uploaded file); one typed field makes it a PARK.

**12. Grant permissions + geolocation BEFORE the first form (added 2026-11-05, user-mandated).**
Location/camera/notification prompts are not neutral: an unanswered prompt **stalls the apply**, and a denied one is recorded against the candidate — some forms use location to prove genuine local presence, so granting it raises ranking. Never let a native popup appear; pre-grant at context level so there is no prompt to accept:
```js
await ctx.clearPermissions();            // clears any half-applied earlier grant
await ctx.grantPermissions(['geolocation','notifications','camera','microphone','clipboard-read','clipboard-write']);
await ctx.setGeolocation({ latitude: 12.9716, longitude: 77.5946, accuracy: 50 }); // Bengaluru
// verify: navigator.geolocation.getCurrentPosition must resolve <1s, not time out
```
**Gotcha that cost two calls:** one unknown permission name **aborts the whole `grantPermissions` call AND poisons later calls** with the same stale error (`Unknown permission: accessibility-events`). `clearPermissions()` first, then grant only verified names. Unknown ones verified unusable: `accessibility-events`, `idle-detection`, `screen-wake-lock`, `storage-access`, `window-management`, `local-fonts`, `display-capture`. Working: the six above plus `background-sync`, `payment-handler`, `midi`, `accelerometer`, `gyroscope`, `magnetometer`.
For popups that still appear (social-login, cookie/consent, "are these results helpful?"): list tabs → remap by URL/title → dismiss consent with the accept/allow button, never `Close` where an `Allow` exists. Dismiss once at session start, not per apply.
