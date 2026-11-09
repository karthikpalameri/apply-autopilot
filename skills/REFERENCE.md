---
name: reference
description: SINGLE SOURCE OF TRUTH — identity, constants, auth, two-tab, browser-call discipline, power recipes.
  Read once per session. Every node POINTS here instead of duplicating (DRY).
parent: skills/SKILL.md
version: 1.0.0
---

# REFERENCE (single source — nodes point here, never duplicate)

## FRESH-START ORDER (run in this order — proven 2026-11-04)
0. **`.venv/bin/python find/preflight.py`** — ONE command, ~11 s, does steps 1-5 below and prints a READY table. **Start here; do not hand-run the steps.** (`--no-sweep` for harvest-only, `--pages 3` to go deeper.)
1. `find/ledger_guard.py` (exit 0)
2. `find/freehire_sweep.py --strict --json` (mandatory first pass)
3. LinkedIn candidate list via the **jobs-guest HTML API** — never the new `/jobs/search-results/` list pane (no scrapeable cards)
4. Batch-print ledger rows per candidate — `is_applied()` alone lies on `blocked` rows
5. Employer gate + stack gate (no C#/Specflow/dotnet core)
6. `PICK()` → apply → `POST()` → proof (employer page **and** Gmail) → `record()` + `scratch/APPLIED.md`
7. **Quality gates:** `scripts/check.sh` — one command, ten gates, exit 1 blocks the batch. Rules and rejected tools: **`#quality-gates`**.
- Route by win-rate: **GH embed > Taleo guest > Phenom > LinkedIn EasyApply > Workday**. Workday/account walls are where sessions die; Taleo "Apply as Guest" needs no account at all.
- Read `skills/LESSONS.md` **newest section first** — that is live ATS knowledge.

## QUALITY GATES

<sub>single source for the RULES; the commands live in `scripts/check.sh`</sub>

**Run one command before every commit:** `scripts/check.sh` (`--fix` applies safe autofixes).
It runs every checker this repo has and prints one line per gate. It is the only place the
commands are written down — do not restate them here or in a second script.

**Enforcement, not advice.** A fresh clone must run this once:
```bash
scripts/check.sh --install     # sets core.hooksPath=.githooks
```
That installs `.githooks/pre-commit`, which runs the gate and **blocks the commit** on any
finding. Verified: a planted unused import produced `GIT COMMIT EXIT = 1` and the commit
did not land. Without this step the gate is documentation — skills are read only if an
agent chooses to read them.

Agent entry point: **`AGENTS.md`** at the repo root (the file harnesses auto-load).

| Gate | Owns (config / code) | Exit 1 means |
|---|---|---|
| python | `pyproject.toml` (ruff) | new DRY/KISS/LOGS finding |
| types | `pyproject.toml` (ty) | new type error — None-unsafe calls |
| dead | vulture | new unused var/import or unsatisfiable branch |
| dupes | `.jscpd.json` + `.jscpd-baseline.json` | a NEW clone, or a copy outside a boundary |
| deps | `.venv` (pip-audit) | known CVE in an installed package |
| upload | `core/lint_upload.py` | a click that opens a native file picker |
| identity | `core/lint_identity.py` | PII in skills/docs, or cache drifted from `config/user.json` |
| pageguard | `core/lint_page_guard.py` | a health gate on ctl `status`, or a page timeout over 10 s |
| shell | shellcheck | quoting / unused-var bug |
| markdown | `.markdownlint-cli2.jsonc` | structure issue (not line length) |
| layering | inline `grep` in `check.sh` | `core/` imported `find/` or `apply/` |

**jscpd rules**
- Config MUST stay at `.jscpd.json` **in the repo root**. Paths resolve from the config file's folder; a copy kept elsewhere reports `protects no code` and **silently exits 0**. A green gate that checks nothing is worse than no gate.
- The `socket-call-single-owner` boundary protects `core/ctl.py#call`. Any copy of that socket loop outside `core/ctl.py` fails. `runtime/server.py` sits in `allow` because it is the *server* end of the same protocol, not a client copy.
- `.jscpd-baseline.json` freezes the known clones: existing duplication passes, NEW duplication fails. Refresh only after deliberately accepting one — `--update-baseline`.
- Reporter is `ai`: compact paths + line ranges, no source dumps (~172 tokens vs ~1 700 for console).

**Layering (one-way, currently clean):** `apply/ -> find/ -> core/`. `core/` must never import `find/` or `apply/`.

**Rejected, with reasons** — do not re-add without new evidence: **ESLint** and **Knip** (no tracked JavaScript; all 230 `.js` files are gitignored `temp/`/`scratch/`), **deptry** (no dependency metadata; hard-fails), **Import Linter** (the layering grep above covers it), **pre-commit** (these gates already run from this section).

## SINGLE-SOURCE INVARIANT (enforced 2026-11-05 — do not break)
- **Company/role identity has ONE implementation: `core.applied_ledger` (`co_key`, `company_matches`, `roles_match`).** Any script needing "have we applied here?" imports those. A private `norm_co()`-style helper in `find/preflight.py` had drifted from `co_key` on 4/10 real names (**Ping Identity, AI Squared, Everpure (formerly Pure Storage), Sony India Software Centre**) and used a 0.4 role overlap instead of `ROLE_OVERLAP_MIN` (0.75) — the exact bug class that lost ~111 companies on 2026-11-04.
- **The match rule is TWO tests, both required to be safe (measured 2026-11-07).** (1) equal after removing spaces — `ai squared` == `aisquared`; (2) one key's tokens are a **subset** of the other — `pure storage` inside `everpure formerly pure storage`, `amazon` inside `amazon web services`. Anything looser is a bug that costs real jobs: any-token overlap made **Qualys ≡ RSA Security** (word *security*) and **dextr ai ≡ zilo ai** (word *ai*); 6-char containment made **elastic ≡ elasticrun** and **dextr ai ≡ dextra**; 3-char containment made **abb ≡ snabbit**. Across 632 ledger companies the loose versions produced **360 false duplicate pairs**, each a live role silently logged as DUPLICATE. A rename that shares no full token belongs in `COMPANY_ALIASES` (`config/dedupe.py`), never in a looser matcher.
- **Short employer spellings are aliases, not new companies.** `COMPANY_ALIASES` maps board text to a canonical key (`hpe`/`hp` → `hewlett packard enterprise`, `qlys` → `qualys`). Alias keys are resolved **after** `SUFFIX_WORDS` stripping, so a key containing `india`/`labs`/`technologies` can never be an alias key — those words are already gone.
- **Never dedupe with raw string matching.** `if name.lower() in applied` missed `AI Squared` (ledger stores it with a space) and left a confirmed 2026-11-05 role one click from being re-applied. Call `is_applied(company, role)` and let the owner decide.
- **QA-title vocabulary has ONE owner: `config/dedupe.py` (`ROLE_QA`, `ROLE_NOT`, `ROLE_STACK_REJECT`, `is_qa_title()`).** Five scripts had carried diverged copies (`qe` accepted in one, `warehouse`/`devops` rejected only in another), so the same job could be READY in one sweep and rejected in the next.
- **Page interaction has ONE owner: `core/ui.py` (`ev`, `text`, `until`, `until_change`, `fill`).** `ev(js)` existed in 4 scripts, three identical and one **missing `or ""`** — so it returned `None` instead of `""` and callers' `re.search()` failed differently for no stated reason. `snap()` was 5 identical copies. `until()` replaces fixed `time.sleep()`: the UI scripts held **45 sleeps = 141 s**, 14 of them inside loops; polling brought that to **11.8 s (-92%)**.
- **Socket call has ONE owner: `core.ctl.call` / `call_wait`.** Eleven scripts had pasted the same 9-line `socket.create_connection(("127.0.0.1", 9000))` loop with timeouts that had drifted to 2/15/20/25/30/60/120 s.
- **HTTP fetch has ONE owner: `core/fetch.py`.** Uses a pooled `httpx.Client` when httpx is installed (optional; falls back to urllib; `PI_FETCH_HTTPX=0` forces urllib).
- **OCR has ONE owner: `core/ocr.py`.** Three scripts called `tesseract` three ways; with tesseract missing, `see.py` **crashed** and `verify.py` silently said `"(ocr fail)"`. `read()` returns `""` and logs `brew install tesseract`.
- **MCP server launch has ONE owner: `scripts/start_mcp.sh`.** `run.sh` and `run_li.sh` each had a copy, already drifted (`sleep 6` vs `15`, different flags).
- **Logging: `print` = program output, `log.*` = diagnostics.** `core/logger.py` sends console to **stderr** so stdout stays pipeable — that is why `freehire_sweep.py --strict --json` feeds `json.load()` directly. **Never `2>&1` into a JSON pipe.** Library code (`core/browser.py`) must `log.*`, never `except: pass`.

## UI PERFORMANCE (measured on a real page, 2026-11-05 — do not re-derive)
- **Never `time.sleep()` before reading the page.** Use `core.ui.until(fn, timeout, interval, what)`. Measured on `automationexercise.com/products`: `until()` **1.1 ms** where the old `sleep(5)` was **5010 ms** — and a real click flow (navigate → click → `until()` → click → `until()` modal) completes in ~3.3 s total.
- **`PLAYWRIGHT_MCP_TIMEOUT_SETTLE` (default 500 ms) is added to EVERY MCP action.** 500 → 512 ms, 250 → 265 ms, 100 → 114 ms, **0 → 7 ms**. `scripts/start_mcp.sh` sets 100. The JS itself is under 1 ms. `browser_snapshot` is unaffected — a snapshot is not an "action".
- **Pi's browser and the `:3000` server must NOT share a profile dir.** Both were on `runtime/mcp-session`; the loser dies with `Browser is already in use` and **every rejected call still burns the 5000 ms action timeout**, which reads as "the UI is slow". Python side owns `runtime/py-session`.
- **`hfill` types at 30 ms/char — 96× `fill`.** 25-char email: 867 ms vs 9 ms; ~7 s per 8-field form. `core.ui.fill()` defaults to the fast path; `PI_HUMAN_FILL=1` restores stealth typing.
- **OCR costs 278 ms versus 1 ms for `innerText`.** Screenshot 75 ms + tesseract 203 ms. Use OCR only for what the DOM cannot show. Screenshots are 5.5× dearer over MCP (440 ms) than the ctl bridge (79 ms).

## THE 6 MISTAKES TO NOT REPEAT (each cost real time — 2026-11-04/05)
1. **A form that `Submit`s and returns to the job list is NOT proof.** Sony returned to listings with zero `mat-error`; the network POST revealed `403 "Profile was earlier uploaded… Cannot upload again."` Always wrap submit in `page.waitForResponse(r=>/apply|career|api/i.test(r.url()) && ['POST','PUT'].includes(r.method()))` and print `status` + body. **DOM silence ≠ success.**
2. **`button.disabled === true` is the only "required field missing" signal on Angular Material.** No `mat-error` renders. Walk every `input[required]`/`mat-select[required]`, then find unticked `input[type=checkbox]` — consent boxes often have **no label text** and are the last blocker (Sony, Zwayam).
3. **A "20 characters" text box that rejects every string is a NUMBER box.** Cloudwick "How soon can you join us?" rejected `28 Nov 2026`, accepted `32`. Type the plain number.
4. **A brand-new-looking LinkedIn card is usually an old requisition re-promoted.** CrowdStrike / HackerRank / Dolby / Amagi / AI Squared all reappeared within 3 days while already in the ledger. `grep -ic "<company>" data/applied_ledger.jsonl` costs nothing.
5. **Never trust a date field you typed.** Zwayam turned `15/04/1994` into `15-Jan-2004`. Use the datepicker widget (period button → year → month → day) and **read the input back** before submit.
6. **Fill 100 % before touching captcha.** Securonix and Neuron7 are both parked at `waiting-user-captcha` with nothing left to do but the grid — that is the correct end state. Never attempt the image grid; record, hand the tab to the user, move to the next target.

## SECRET WEAPONS (use first, every session)
- **`find/preflight.py` — the whole gate in one call.** Guard + sweep + LinkedIn harvest + ledger classification + employer/stack/title gates, printing only `READY <age>d [NEW-CO|new-role] <company> | <title> | <jobId>`. 11 s vs ~10 manual round-trips. Company matching is **normalization-aware** (`AISquared` == `AI Squared` == `ai-squared`; strips inc/ltd/pvt/india/technologies), which is exactly the class of duplicate that used to slip through `is_applied()`.
- **Never** re-grep the ledger by hand for a candidate list — `preflight.py` already prints `duplicate <status> <date>` per rejected card.
- **Email security-code gate instead of captcha** = Greenhouse 8-char code from Gmail → per-char boxes `#security-input-0..7`; Okta confirmed in one shot. Oracle HCM uses 6-digit `pin-code-1..6` + `VERIFY`. When a form says "a verification code was sent", it is a 2-minute win, not a blocker — **procedure and the mandatory Gmail-tab step: `RELIABILITY.md` rule 11**; the rule forbidding abandonment is **rule 10**.
- **Permissions/geolocation are a session-start step, not a mid-form fix.** Pre-grant `geolocation|notifications|camera|microphone|clipboard-read|clipboard-write` + `setGeolocation(Bengaluru)` so **no native prompt ever appears**. `clearPermissions()` before granting — one unknown name poisons all later calls. Full list of working/unusable names: `RELIABILITY.md` rule 12.
- **Employer ATS liveness check before applying:** `boards-api.greenhouse.io/v1/boards/<slug>/jobs` and `api.lever.co/v0/postings/<slug>?mode=json` return `id | title | location | updated_at`. Confirms the requisition is live *and* gives the apply token (Okta `7744555`, Neuron7 `fe2e1697`).
- **LinkedIn Easy Apply** — use scoped DOM readback from `dialog[open]` (new UI; legacy `[role=dialog]` may be absent). Verify the job page shows **Application status — Application submitted**; no screenshot is needed for ordinary text.
- **Avature / `jobsearch.<co>.com` "maintenance" page (HTTP 200, title `Maintenance`)** = employer outage, not a bad URL. Record and move on; do not retry.

## IDENTITY (config/user.json + config/answers.py — never invent)
<!-- identity-ssot:allow — this block IS the one readable mirror of config/user.json.
     Every other file must POINT here (skills/REFERENCE.md#identity), never copy these
     values. core/lint_identity.py enforces that; run it before committing. -->
**The single written source is `config/user.json` (chmod 600, gitignored).** This block is the human-readable mirror; if the two ever disagree, user.json wins.
- Name: **Your Name** · DOB: **<your DOB>** · Location: **<your city, country>**
- Email/phone: `config/user.json` (`email`, `phone`, `phone_national`)
- Work history (parsed rows MUST match these — never let an ATS parser rename a company to e.g. `Test`):
  1. **Bottomline** — Senior QA Engineer — Jan 2022 → Now (payments platform: UPI, cards)
  2. **Meredith** — SDET — May 2020 → Jan 2022
  3. **Cognizant** — Programming Analyst — Aug 2018 → May 2020
- Education: **B.E. Computer Science, BMS College of Engineering, 2017**
<!-- /identity-ssot:allow -->

## COMPENSATION + NOTICE (single source — do not restate elsewhere)
- Current compensation = **₹<your current CTC> fixed + ₹0 variable** (total ₹<your current CTC>). Expected CTC = current × 1.22 (**22% hike**) → **<your expected CTC> / <your expected annual INR> INR**.
- Numeric salary fields: enter **`3300000`** — never decorate (`3300000 INR` / `<your expected CTC>` breaks numeric inputs).
- **Last working day = 27 Nov 2026**. Every form/profile answer: notice period = **"available from 28 Nov 2026; last working day 27 Nov 2026"** (date fields: `27/11/2026` DD/MM, or `11/27/2026` MM/DD per form locale); availability/joining = **available from 28 Nov 2026**. Never answer "60 days", "30 days", or a bare "immediate joiner".
- LinkedIn "How soon can you join (in days)" = **32 (available from 28 Nov 2026; LWD 27 Nov 2026)** · Years of experience = **"8 years - 10 years"**.
- Notice-period negotiability: **Yes** (user confirmed 2026-11-02). This does not change the recorded LWD or availability date.

## RESUME (MD5-GATED — canonical detail lives in skills/resume/SKILL.md)
- Canonical file: `config/Your_Name_Resume.pdf` (from `config/user.json resume_path`)
- Upload name MUST be **`Your_Name_Resume.pdf`** — NEVER `resume.pdf` (recruiters reject generic names)
- Known-good MD5: **`YOUR_RESUME_MD5`** (persisted in `config/resume.md5`)
- 3 gates via `core/resume_secure.py`: **`PICK()`** (before form) → **`BEFORE_UPLOAD()`** (returns verified path, call right before upload) → **`POST()`** (after submit)
- Upload method: **`skills/resume/SKILL.md#upload-method`** (single source — injection only, never a native file-picker popup). Resume bytes still gated by `BEFORE_UPLOAD()`.

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

## PARALLEL MODE — 2 FORM tabs + 1 GMAIL (user-requested, 2026-11-05)
- Slot A and Slot B each own **one** application. Gmail stays the single shared third tab.
- **Never leave a form with unsaved state in the inactive tab and navigate the active one to a different domain before verifying nothing is pending.** Set the whole form on tab A, submit-or-park, *then* switch.
- Interleave at **phase boundaries only** (discovery → fill A → fill B → submit A → submit B → proof A → proof B). Never mid-form: Angular/React re-renders on tab switch and stale ids die.
- Before every switch: `tabs list` → re-resolve the target by URL match (indices shift). Keep a written state `{slot, tabId, url, company, role, reqId, phase}` per slot.
- Statuses are recorded **per slot** the moment that slot's action completes — never batched to the end (a crash would lose both).
- Security codes: Gmail may now hold codes for **two** employers at once. Match by sender + newest timestamp + req/company name in the body, never "the top row".

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
```text
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

## SCREENSHOT BUDGET (measured 2026-11-07 — the single biggest token sink)
Measured over 12 sessions / 3,760 requests: `browser_take_screenshot` was **123 calls and
14.5 MB of results** — 14× everything else in the log combined (bash 904 calls = 887 KB).
Each image stays in the transcript and is **re-sent on every later turn**: one session climbed
from $0.00021 to $0.00152 per request as history grew. Screenshots are the bill.

- **Default = scoped DOM text** (`innerText`, field values, required flags and validation errors). Audit *all* required controls, including off-screen fields, via DOM/scroll-bound probes; do not assume the viewport shows the whole form.
- If the DOM cannot resolve a visual ambiguity, capture **one viewport/cropped image to a local file** and return only `core/ocr.py`/`core/see.py` text to the model. Never attach raw image bytes or full-page screenshots to the model transcript.
- **Never `fullPage: true`.** For canvas-only layout issues, use one small viewport crop; if OCR cannot settle it, stop and hand the visible page to the user (CAPTCHA remains user-only).
- Positive success text/URL and Gmail are proof; a screenshot is optional corroboration, not a substitute. After two unhelpful crops, stop and use scoped DOM or ask.

## JEV (classifier — detail lives in `skills/jev/SKILL.md`)
Use for choices and yes/no gates only after deterministic lookup fails. Never prose,
submit decisions, or applicant PII (it leaves the machine). Threshold 0.65: below it,
stop or escalate. Auto routing adds an extra API call per prompt and only activates
inactive tools; compare total cost before claiming savings.

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

## SAVED USER-PROVIDED ANSWERS
- Saved application answers live in `config/user.json` → `application_answers_india` and are read via
  `config/answers.py::answer_yes_no`. Fill them in `python3 hub.py setup` / `onboard`.
- Never hardcode a name, email, DOB, salary, work-authorization or screening answer here — resolve
  everything at runtime from `config/answers.py` (`A`). Add new saved answers to `config/user.json`,
  not to this file.
- Terms/privacy consent is per-employer and per-requisition: record each consent with a date and exact
  scope in `config/user.json`, and never reuse one employer's consent for another without a fresh user
  confirmation.

## USER-PROVIDED ANSWERS, CONSENTS & PREFERENCES (dated; scope is strict)
- **LSEG, requisition R0124202 — “How did you hear about us?”** (2026-11-02): user authorizes choosing any offered source. Since this role was found on LSEG’s official careers site, choose **LSEG External → LSEG Careers Site**. Role-specific; do not reuse for another posting.
- **Visa, REF089412W — personal-data/background-investigation consent** (2026-11-02): user explicitly authorized the required checkbox for this Visa application. Limited to REF089412W; do not infer consent for another employer, role, or materially different terms.
- **HealthEdge, requisition 8635 — U.S. sponsorship question** (2026-11-02): user answered **No** to whether they currently or will in future require visa sponsorship to work for HealthEdge in the U.S. Use only for this exact question/role; do not substitute the India work-authorization answer or infer broader immigration status.
- **Location preference** (2026-11-02): user is open to five-day in-office roles elsewhere in India, including relocation/commuting from Bengaluru. Verify the actual city and terms before applying.
- **Conga, requisition 5279259007 — application answers** (2026-11-02): user reports no prior Conga history and one current offer. Do not invent the offer package; if required, state “one offer in hand; package not disclosed” unless the user provides the amount. User authorized this draft for the Conga AI-tools question: “I use AI assistants to brainstorm test scenarios and edge cases, draft QA documentation, and investigate failure patterns. I validate suggestions against requirements and test evidence, and avoid sharing confidential data.” Treat as a role-specific, user-authorized draft, not a general fact about experience.
- **Conga, requisition 5279259007 — last working day clarification** (2026-11-02): user clarified that current-employer Bottomline last working day is **27 Nov 2026** (“27 November this month”). Use the canonical date and standard answer “available from 28 Nov 2026; last working day 27 Nov 2026” for Conga. Disregard the earlier “Sep 28” as a mistaken date unless the user corrects it again.
- **Nutanix, requisition 32906 — applicant privacy notice acknowledgment** (2026-11-02): user authorized acknowledging the Job Applicant Privacy Notice for this application. Read the notice before acknowledging; this is role-specific and is not blanket consent for other employers or additional data-processing/background-check terms.
- **Batch target** (2026-11-02): user wants the next three fresh QA/SDET roles at distinct product companies found and verified before applying; prioritize substantial product scale/revenue and do not recycle previously attempted roles to reach three.
- **Memory rule:** consult this section before asking. Reuse an answer only when employer, role/question, and consent scope match. Add new explicit answers here with date and precise scope; never generalize one-time consents.

## SPEED PROFILE (session-log-derived)
- Preflight/dedupe the next 3 roles once; cache `{company, exact role, LinkedIn ID, ATS job ID, employer domain, URL, ATS}`; classify DUPLICATE/MISMATCH/READY/BLOCKED before opening any ATS.
- Route by win-rate: **GH embed > Phenom > LinkedIn EasyApply > SuccessFactors > iCIMS**; timebox account/CAPTCHA walls and record the blocker.
- Read the selected recipe + lessons once per session; do not reread unchanged skill files per role.
- One DOM extraction for all visible cards; DOM assertions before OCR; screenshot/OCR reserved for click ambiguity + final proof.
- Bounded recovery: one fresh-locator retry after a failed post-check; then record the exact blocker.
- **Batch 2026-11-04 (user request: "find 3 product-based companies and apply") — employer-scoped acknowledgments.** Renesas Electronics `744000159112460` applicant privacy notice; Konovo `5281657008` Processing of Personal Data ("Acknowledge and confirm"); HPE `1214372` Recruitment Notice + pre-employment background-screen terms. Each was a required, standard applicant acknowledgment for the role the user asked to apply to. Scope: these three requisitions only — do not reuse for other employers, roles, or materially different terms.
- **HPE Workday credential (2026-11-04).** The prior password was unknown, so the account was recovered via "Forgot your password"; the new password lives ONLY in the macOS Keychain. Look it up with `security find-generic-password -s hpe-workday -a "$(python -c 'import config.answers as a; print(a.A[\"email\"])')" -w`. Never write it into the repo. <!-- identity-ssot:allow -->
- **Batch 2026-11-04 #2 (Oracle / Angel One / TrustGrid).** LinkedIn Easy Apply privacy-notice/privacy-policy acceptance is implied by submitting those three applications on the user's instruction. Scope: these three requisitions only.
- **Scientific Games Workday credential (2026-11-04).** `security find-generic-password -s sg-workday -a "$(python -c 'import config.answers as a; print(a.A[\"email\"])')" -w`. Account created for requisition R505378; the application is parked at step 5 of 6 pending one user fact (passport yes/no). Never write the password into the repo. <!-- identity-ssot:allow -->
- **Stack-fit gate (user instruction 2026-11-04):** do not apply to roles whose core requirement is C#/Specflow/dotnet. Canonical stack = Java, Python, Selenium, Appium, RestAssured, API/CI-CD automation.
- **Passport status (user-confirmed 2026-11-04): user HOLDS a valid passport.** Answer "Do you hold a valid Passport? (for Indian Citizens only)" = **Yes** on any application form. Standing fact — reuse across employers; do not re-ask. Related standing facts: Nationality = **Indian**; work authorization in India = **Yes** (citizen, no sponsorship needed).
- **Scientific Games R505378 (2026-11-04):** all 5 steps filled and saved; the ONLY outstanding item is the required "If Yes, Passport No?" field (user holds a passport; the number itself is deliberately NOT stored in this repo). Hand the visible browser to the user for that field, then submit.
- **Scientific Games R505378 — SUBMITTED 2026-11-04.** User personally filled the required "If Yes, Passport No?" field in the visible browser and the application completed (Workday Candidate Home: "In Process, Under Consideration", Nov 4 2026). The exact value entered is not readable post-submit and is not stored here. No SG confirmation email had arrived ~1 minute after submission.
## STANDING RULE — CAPTCHA HANDLING (user instruction, 2026-11-04)
If a form is captcha-gated (hCaptcha / reCAPTCHA / Cloudflare / "verify you are human"):
1. **Fill every field and attach the canonical resume as normal** — do the whole application up to the challenge.
2. **Stop at the captcha.** Do NOT grind retries, do NOT crash/reload the tab, do NOT hunt for token workarounds.
3. Leave the FORM tab open with the widget on screen, record the attempt as `waiting-user-captcha` in `core/applied_ledger.record(...)` with the exact URL + what is filled. Ledger status vocabulary (canonical): `waiting-user-captcha`, `waiting-user-credentials`, `submitted-awaiting-email`, `submitted-confirmed`/`confirmed-ats`, `blocked`.
4. Tell the user: tab id, what to click (widget + Submit), and that I will capture proof + upgrade the status to `confirmed-ats`/`submitted-confirmed` once they say it went through.

## CAPTCHA — NO SOLVING, NO API KEY (standing rule)
- CAPTCHA is a hard stop. There is **no** third-party CAPTCHA-solving service or API key in
  this repo, and none should be added. Finish safe fields, leave the page open for the user,
  and record `waiting-user-captcha`. The standing rule above governs every driver.

## STANDING RULE — CAVEMAN STYLE ALWAYS (user, 2026-11-04)
User want caveman talk. Always. All reply. All note in repo file (REFERENCE, APPLIED, LESSONS). No long prose. No table if line do. Facts only. Path + result + next. Big word die. Short line win.

## DATA GAPS THAT BLOCK APPLICATIONS (ask once, store forever)
| Fact | Status | Where it blocks |
|---|---|---|
| ~~Date of Birth~~ | **NOT A GAP — resolved.** Value: **`skills/REFERENCE.md#identity`**. Read it from `config/user.json`; **never say "must ask user"**. | Workday Voluntary Disclosures (IQVIA `Date of Birth*`, MM/DD/YYYY) |
| Graduation GPA/CGPA | **8** (user-confirmed 2026-11-04) | Workday education `Overall Result (GPA)` (AVEVA, L&W); rejects `N/A` |
| Valid passport | **Yes** (holder) | Workday/Phenom "Do you hold a valid Passport?" + "If Yes, Passport No?" (Scientific Games) — the NUMBER is user-entry only, never stored |
| PAN card number | **KNOWN — `config/user.json` → `pan_number`** (user-supplied 2026-11-07). That file is gitignored and untracked; the value must never appear in a skill, doc, commit, or log line. Read it at fill time, write it into the field, never echo it. | Bosch SmartRecruiters oneclick-ui screening Q9, and any India ATS with a "PAN card number" field |
| Notice period | <your notice> / LWD 27 Nov 2026, available 28 Nov 2026 | every ATS |
| Expected CTC | <your expected CTC> (3300000) | Workday salary bands, Phenom numeric field |
DOB sits at Workday step "Voluntary Disclosures", last before Review. It is KNOWN — pull it from `config/user.json` (source: resume). Never stall a Workday tenant for it.

## CREDENTIAL VAULT — macOS KEYCHAIN ONLY (canonical service names)
Every password/code lives in the Keychain. `config/user.json` stays a **pointer**, never a secret. Read with `core/gmail_otp.py::keychain(service, account)` — one helper, do not re-implement `security` calls.

```bash
security find-generic-password -s <service> -a <account> -w          # read
security add-generic-password    -s <service> -a <account> -w '<pw>' -U   # add/update
```

| Service | Account | Purpose |
|---|---|---|
| `gmail` | `your.email@gmail.com` | **APP PASSWORD ONLY** — see below |
| `linkedin` | `your.email@gmail.com` | LinkedIn login |
| `hotmail` | `your.secondary@example.com` | secondary inbox |
| `docusign-icims` | `your.email@gmail.com` | iCIMS candidate account |
| `hpe-workday` | — | see USER-PROVIDED ANSWERS |

### Gmail IMAP needs an APP PASSWORD, not the login password (learned 2026-11-06)
`imaplib` login with a normal Google password returns `[AUTHENTICATIONFAILED] Invalid credentials` — **not** a wrong-password error, and not fixable by retrying. Google disabled basic auth for IMAP; only a 16-char app password works, and it requires 2-Step Verification to be on.
- Create: `https://myaccount.google.com/apppasswords`
- Store: `security add-generic-password -s gmail -a your.email@gmail.com -w '<16-char>' -U`
- Same trap on Hotmail/Outlook: `outlook.office365.com` returns **`Basic authentication is disabled`** for normal passwords.

**Consequence for ATS email-code gates:** Greenhouse's `security-input-0..7` 8-char code (Sumo Logic job 8109723, AI Squared) gates submit behind an email round-trip.

### Read codes from the GMAIL *TAB*, never from IMAP alone (corrected 2026-11-06)
**The browser session is already logged into Gmail — no password is needed.** `#inbox` opens to `Inbox (N) - your.email@gmail.com` because the profile holds the cookie. IMAP is the *fallback*, not the primary path; concluding "cannot solve without an app password" was WRONG and cost an application cycle.

Order of attempts, stop at the first that works:
1. **Browser tab** (works now): open `mail.google.com/mail/u/0/`, search, click row, read `.a3s` body.
2. Then `keychain('gmail')` + `core/gmail_otp.py` (needs a 16-char app password).

```js
// search rows, newest first
[...document.querySelectorAll('tr')].map(t=>t.innerText).filter(t=>/Security code/i.test(t))
// read opened message
(document.querySelector('.a3s')||{}).innerText   // -> "...code: 80240858..."
```

**Greenhouse code mechanics (measured):** the code is **single-use and short-lived**. The *same* code is re-sent while the form sits unsubmitted, so a code >10 min old is already dead and returns `Invalid security code`. A hard `page.reload()` clears the stale code + error banner; Greenhouse then issues a fresh code on the next submit. Two codes seen for one form (`88851365` expired → `80240858` valid).

**Do not trust `.helper-text--error` for submit readiness.** A stale `Select a country` banner (phone `#country` widget) persists after the country is set correctly while `aria-invalid="false"` and submit stays enabled. **Submit anyway and read the server result** — the error can be cosmetic.

## STANDING RULE — RESUME IS THE FIRST-RESORT FACT SOURCE (user, 2026-11-05)
**Never mark a candidate fact "UNKNOWN / must ask user" before extracting the resume.** PDF text is searchable; the answer is usually already there and stalling costs a whole application.

Before EVERY apply batch, run this and keep the output as the fact base:
```bash
.venv/bin/python find/resume_facts.py          # prints + writes config/resume_facts.json
```
- Extraction: `pypdf` (already in `.venv`) → `PdfReader('config/<resume>.pdf')`, join `page.extract_text()`.
- Regexes that paid off — DOB, phone, email, LinkedIn, GitHub, employer + month-year ranges.
- Order of truth: `config/user.json` (explicit) → resume text → ask user. Only ask when BOTH sources are silent.
- Resume PDF is the same artifact uploaded to ATS — its values are internally consistent, so ATS cross-checks pass.
- **Date formats to emit** (the values themselves live in `config/user.json` + `#identity`, not here): US `MM/DD/YYYY`; UK/India `DD/MM/YYYY`; long `D Month YYYY`. `find/resume_facts.py` derives all three from `date_of_birth`.
