---
name: reference
description: SINGLE SOURCE OF TRUTH — identity, constants, auth, two-tab, browser-call discipline, power recipes.
  Read once per session. Every node POINTS here instead of duplicating (DRY).
parent: skills/SKILL.md
version: 1.0.0
---

# REFERENCE (single source — nodes point here, never duplicate)

## IDENTITY (config/user.json + config/answers.py — never invent)
- All identity values live in `config/user.json` → `config/answers.py` (`A` dict).
  Read them; never hardcode a name/email/phone/salary/resume path in a script or skill.
- Name/DOB/location/email/phone: `A['full_name']`, `A['dob']`, `A['location']`, `A['email']`, `A['phone']`.
- Work history + education: parsed from YOUR resume. Never let an ATS parser rename a company
  to e.g. `Test` — verify each row against the resume before submit.
- Profile summary: `A['summary']`; company/role: `A['current_company']` / `A['current_role']`.

## COMPENSATION + NOTICE (single source — do not restate elsewhere)
- Expected CTC = `A['expected_ctc_lpa']`; current CTC = `A['current_ctc_lpa']` (hike rule configurable in `setup.py`).
- Numeric salary fields: enter **`A['expected_ctc']`** as a bare integer — never decorate
  (`<expected_ctc> INR` / `<expected_ctc_lpa> LPA` breaks numeric inputs).
- Notice: `A['notice_days']` + `A['last_working_day']` + `A['availability']` are the ONLY truth.
  Every form/profile answer: notice period = **"serving notice, last working day <your last working day>"**
  (format the date to the form locale: DD/MM/YYYY or MM/DD/YYYY); availability = `A['availability']`.
  Never answer "60 days" / "30 days" unless that is what `A['notice_days']` says.
- LinkedIn "How soon can you join (in days)" = `A['notice_days']` · Years of experience = `A['years']`.

## RESUME (MD5-GATED — canonical detail lives in skills/resume/SKILL.md)
- Canonical file: `<HUB_ROOT>/config/Firstname_Lastname_Role.pdf` (from `config/user.json resume_path`)
- Upload name MUST be **`Firstname_Lastname_Role.pdf`** — NEVER `resume.pdf` (recruiters reject generic names)
- Known-good MD5: **`<GENERATED_ON_SETUP>`** (persisted in `config/resume.md5`)
- 3 gates via `core/resume_secure.py`: **`PICK()`** (before form) → **`BEFORE_UPLOAD()`** (returns verified path, call right before upload) → **`POST()`** (after submit)
- Upload method: `setInputFiles(BEFORE_UPLOAD())` on the existing `input[type=file]`; NEVER a native file-picker popup.

## AUTH PRIORITY (canonical)
- Order: **`Continue with Google` / `Sign in with Google`** → **`Sign in with LinkedIn` / `Apply with LinkedIn`** → **email/password** → **email OTP** (last resort).
- Use only the visible provider button; never create a duplicate account to work around a failed provider.
- Agent owns the full flow (navigate ATS, Create Account/Sign In, Gmail request/read OTP + reset links, truthful profile, submit, proof, track). User-only pauses: CAPTCHA/biometric and secrets when no approved vault.
- Atomic credential: a generated password is allowed only if retained in an OS keychain/password manager BEFORE entry, kept in memory through immediate sign-in, and verified. Never generate and lose it; a gitignored file is NOT a vault.
- Reset links are single-use: verify a fresh message/link first; one recovery attempt per site/session; stop on stale/consumed links.
- Never write passwords/OTPs/reset links to repo files, `progress.json`, logs, or skills.

## TWO-TAB SESSION (non-negotiable)
- ONE persistent **headed** browser, two working tabs: **FORM** + **GMAIL**.
- FORM owns one application — never navigate/reload/close/reuse it for Gmail after data entry.
- GMAIL is created once and reused for OTPs, security codes, confirmations. Never open a new Gmail tab per code.
- Before Gmail work: re-list tabs → select GMAIL → read → select the saved FORM tab by fresh index/URL (never assume current tab).
- Never restart browser/MCP while FORM holds entered data. If FORM is missing/reset/reloaded → stop and ask, do not refill from memory.
- Implementation: `core/gmail_read.py` → `McpBrowser.ensure_gmail_tab()`; Gmail reads must not `navigate(GMAIL_URL)` on FORM.

## BROWSER TOPOLOGY (single source — never duplicate a server)
| Channel | Server | Transport | Owner | Consumer |
|---|---|---|---|---|
| Pi agent | `cloak-browser` = `@devinwangd/cloak-browser-mcp` | **stdio** | `~/.pi/agent/mcp-adapter.json` | `mcp__cloak_browser` tools |
| Python batch | `cloakbrowser-mcp` (npm) | HTTP **:3000** | `run.sh` / `run_li.sh` | `core/browser.py` `McpBrowser` |
| Python fast-path | `runtime/server.py` | TCP **:9000** | `run.sh` | `core/ctl.py` |

- **The agent's tool names come ONLY from the Pi stdio server** (`browser_run_code_unsafe` + `const { page } = cloak`). The `:3000` server is upstream `@playwright/mcp` and has NO `_unsafe`/`cloak` — never call `:3000` tools from Pi.
- **Never declare the `:3000` server to Pi** (not in `~/.pi/agent/mcp-adapter.json`, not in `.mcp.json`). Doing so spawns a second owner of port 3000 and blocks startup. Project `.mcp.json` stays `{"mcpServers": {}}`; Pi MCP is user-level only.
- **One profile (`runtime/mcp-session`), one browser at a time.** `run.sh`/`run_li.sh` take over the profile from Pi's server — do not run them while Pi holds entered form data; clean `.cloakbrowser-mcp-profile.lock` only as part of an explicit restart.

## CACHED CLOAK TOOL NAMES (exact — the ONLY valid set, never invent spellings)
```
browser_navigate · browser_tabs · browser_click · browser_type · browser_select_option
browser_press_key · browser_fill_form · browser_snapshot · browser_wait_for
browser_evaluate · browser_run_code_unsafe
```
- Discovery belongs to the MCP gateway (`{describe}`); the browser proxy takes **`{tool, args}`** — never send `{describe: ...}` to it.
- Session logs showed hallucinated names (`browser_run_code_unsafe 合乐 code?`, `browser_press_key_uuid`, `functions.mcp__cloak_browser`) = wasted round trips. The list above is canonical.
- `browser_press_key` = THE real keyboard tool (`browser_keyboard` is a phantom name that silently fails).

## BROWSER CALL BUDGET (30% round-trip target)
- One transaction per stable state: **scoped discovery → related actions → targeted readback**.
- `browser_run_code_unsafe` is RESERVED for power patterns (session log: 54% of browser calls were run_code_unsafe doing routine work the dedicated tools do cheaper). Use it ONLY for:
  1. React/custom select commit (below)
  2. Native-setter batch fill (Lever `page.evaluate` `set(name,v)`)
  3. `setInputFiles` resume upload
  4. Real per-char keyboard typing (Workday textareas reject native setters)
  5. Multi-field same-state transaction (fill + readback in one call)
  Otherwise use `browser_click` / `browser_fill_form` / `browser_select_option` / `browser_snapshot` / `browser_evaluate`.
- `browser_wait_for` canonical arg = **`{timeMs: <int>}`** (logs showed 4 spellings — `time` / `timeMs` / `ms` / `condition`). Prefer condition waits (`waitForURL` / selector / visible / enabled) over fixed sleeps; one settle wait only after a real transition.
- `.fill()` replaces (no Meta+A first); Meta/Cmd+A + Backspace ONLY before real keyboard typing; read back changed fields only, not the whole page.
- Parallelism only for independent read-only work; never parallelize actions sharing a form.

## REACT-SELECT COMMIT (universal — GH/Workday/Phenom/Oracle cx-selects)
```js
// browser_run_code_unsafe; use the server-global cloak object (NOT async (page)=>{}).
const { page } = cloak;
const ci = page.locator('#' + id);
await ci.click();
await ci.pressSequentially(text, { delay: 40 });          // real per-char keydowns render options
const option = page.getByRole('option', { name: pat, exact: true }).first();
await option.waitFor({ state: 'visible' });
await option.click();
return await ci.inputValue();                              // read back in the same call
```
- `exact: true` + `.first()` beats strict-violation duplicates (e.g. "Male" ×2).
- Known instances: GH `#country` → option **"India +91"** (NOT "India"); Workday Job Board = CATEGORY → expand → LinkedIn.com; Phenom `select-shell remix-css...-container`; Oracle cx-selects (click → type → click EXACT option; typing alone does not commit the model).

## PI AUDIT CORRECTIONS — 2026-09-24 (canonical)
- **Context boundary:** `mcpScript` outer code → `tools.cloak_browser_*`; nested `browser_run_code_unsafe` string → `const { page } = cloak`; `document`/`location` only inside `page.evaluate`. Never mix `{describe: ...}` with the browser proxy `{tool, args}` shape.
- **Navigation post-check:** a click that can navigate needs a settled URL/title/role-anchor check in a NEW state; do not evaluate the old (destroyed) execution context immediately after submit/navigation.
- **Locator discipline:** one fresh scoped discovery per state; narrow to card/dialog/form + exact text/ID; retry once; then record the blocker.
- **Browser health:** on `[NO_BROWSER] Browser failed to launch...`, check stale Chromium process + profile lock once, reconnect, preserve entered FORM state. No repeated calls against a dead session; no restart over a filled form/CAPTCHA.
- **Dynamic forms (Rippling/React):** wait for the application step, inspect `__NEXT_DATA__.props.pageProps.apiData.jobPost.activeJobApplication`, map required questions by UUID/test-id, fill+readback the group (incl. resume filename + radio `aria-checked`) before advancing. Never guess positional generated IDs.
- **Wait budget:** audit = **2,310 `waitForTimeout` / 2,396.725 s** → condition waits + one short settle, never stacked sleeps.

## SAVED USER-PROVIDED INDIA APPLICATION ANSWERS
- Work authorization without sponsorship: **Yes** · Temporary authorization requiring future sponsorship: **Yes**
- Non-compete / employment restrictions: **No** · Other business/employment if hired: **No**
- Prior Cigna employment / contracting / government-official / employee relationship: **No** (×4)
- Citizenship status: **Citizen (India)** · Gender: **Male**
- Terms/privacy consent: confirmed for the **Cigna** application on 2026-09-14 ONLY — never reuse for another employer without a new user confirmation.

## SPEED PROFILE (session-log-derived)
- Preflight/dedupe the next 3 roles once; cache `{company, exact role, LinkedIn ID, ATS job ID, employer domain, URL, ATS}`; classify DUPLICATE/MISMATCH/READY/BLOCKED before opening any ATS.
- Route by win-rate: **GH embed > Phenom > LinkedIn EasyApply > SuccessFactors > iCIMS**; timebox account/CAPTCHA walls and record the blocker.
- Read the selected recipe + lessons once per session; do not reread unchanged skill files per role.
- One DOM extraction for all visible cards; DOM assertions before OCR; screenshot/OCR reserved for click ambiguity + final proof.
- Bounded recovery: one fresh-locator retry after a failed post-check; then record the exact blocker.
