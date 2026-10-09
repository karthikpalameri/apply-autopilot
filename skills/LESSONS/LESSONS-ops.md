# OPS LESSONS
## 2026-10-02 — LIVE STACK EVAL (fixes)
- `cloakbrowser-mcp@1.14.1` DROPPED `--viewport` — unknown option makes the server print help and die instantly (this was the real 30s startup hang: adapter retrying a dead server). Fix: no viewport flag; healthz proves the port in ~2s.
- `runtime/server.py` was gitignored + never committed — lost the whole ctl :9000 leg. Rebuilt from call-site protocol (ops: status/navigate/eval/snap/keys/htype/hfill/fill/mouse_click/upload_cdp). `.gitignore` now exempts it (`!runtime/server.py`).
- `.venv` was missing → `python3 -m venv .venv && .venv/bin/pip install cloakbrowser pypdf` (first cloakbrowser launch downloads the binary).
- Health baseline: `bash run.sh` → 5/6 green (prod_sweep = external greenhouse API, not local).
- macOS Python SSL: framework python lacks the system CA bundle → external HTTPS (greenhouse/lever/ashby/capsolver/wday) needs certifi. All urllib call sites now pass `context=create_default_context(cafile=certifi.where())`. `certifi` is a venv dep.
- `:3000` viewport: v1.14.1 removed `--viewport` — server default only; resize per page via MCP `browser_resize` when needed.
## 2026-08-12
- browser_run_code_unsafe = full Playwright — the unlock for Workday/GH selects
- browser_press_key = real keyboard tool (browser_keyboard = phantom name, silent fail)
- Workday selectinput commit: getByRole('option', {exact:true}).first().click() — ~20 other methods failed
- GH react-select: pressSequentially + getByRole option click = commits
- MCP type into refs = APPENDS (never replaces) — Ctrl/Cmd+A + delete first
- session: stale sid → 404 → delete config/mcp_session.json
- Authentication/session recovery: keep the credential action atomic; an agent may generate a password only after storing it in an approved OS keychain/password manager and retaining it through immediate sign-in. Never put it in repository/gitignored files or lose it across navigation. Never reuse a consumed reset link. One recovery attempt per site/session, then record the exact blocker and stop.

## 2026-09-22 — 30% browser-call optimization from `.pi` histories
- Session history showed the dominant overhead was repeated transport calls and sleeps: one large session had about 2,024 `browser_run_code_unsafe` calls, 579 fixed waits, and 180 navigations; another had about 746 run-code calls and 341 snapshots. Optimize round trips, not proof checks.
- Use the cached cloak tool names exactly: `browser_navigate`, `browser_tabs`, `browser_click`, `browser_type`, `browser_select_option`, `browser_press_key`, `browser_fill_form`, `browser_snapshot`, `browser_wait_for`, `browser_evaluate`, and `browser_run_code_unsafe`. Invalid wrapper/namespace spellings caused wasted retries.
- Stable-page pattern: one scoped DOM discovery → one transaction for related clear/fill/select/upload actions → one targeted readback. Reacquire only after rerender/navigation/modal transitions.
- `.fill()` replaces ordinary controlled text; Meta/Cmd+A + Backspace is needed only before real keyboard typing. Native `<select>` uses `selectOption`; Workday/GH custom selects require their proven exact-option commit. Do not probe multiple methods on one field.
- Replace stacked `waitForTimeout` calls with one condition wait plus a role-specific anchor. Keep one bounded retry after a fresh locator; CAPTCHA, unknown sensitive data, and credential loss remain hard stops.
- Direct navigation to a cached ATS URL, persistent FORM/GMAIL tab identity, scoped DOM reads, and one final proof capture are faster than LinkedIn intermediate pages or repeated full snapshots. In one-by-one mode, reopen/read Gmail for the current role before moving on; defer a combined search only to explicit batch mode.

## 2026-09-24 — SOCIAL LOGIN, OTP RATE LIMIT, AND TAB SPEED
- Prefer visible Gmail/Google sign-in, then LinkedIn sign-in/apply, before ATS email/password and email OTP.
- OTP state machine is webpage request → one Gmail refresh → enter the fresh code/link. A site returned HTTP 429 after repeated requests; stop on 429 instead of retrying/resending.
- Popup/redirects can reorder or collapse tabs. Create one FORM/VERIFY and one GMAIL tab, re-list once after the transition, map by URL/title, and switch explicitly with `browser_tabs {action:"switch", id}`; close stale duplicates and never navigate FORM to Gmail.
- Batch stable-page discovery, related actions, and readback in one short `browser_run_code_unsafe` transaction; condition-wait only for the next role-specific anchor.

## 2026-09-22 — PI HISTORY CALL-SHAPE AND LOOP CORRECTIONS
- The high-volume session spent most calls in `browser_run_code_unsafe`, snapshots, tabs, waits, and navigations. Use a stable-state budget of one discovery → one action batch → one readback; do not make a tool call per field.
- `mcp__cloak_browser` is a browser-call proxy, not the discovery API: use the MCP gateway for `search/describe`, then call the known `{tool, args}` directly. Never pass `{describe: ...}` to the proxy.
- This server exposes Playwright through the global `cloak` object. Use `const { page } = cloak;` inside `browser_run_code_unsafe`; an `async (page) => ...` wrapper generated evaluation/type errors.
- Ordinary text: `.fill()` replaces in one operation. Real keyboard clearing is only for controls that reject `.fill()`. Native selects use `selectOption`; React selects use real keydown + visible exact-option click; resume uses direct `setInputFiles`.
- Use one condition wait and one role-specific anchor after navigation/rerender. A fixed timeout is a fallback only. Never repeat an unchanged failed action, reset URL, or tool-discovery call without new state evidence.
- Refresh tab identity before switching; keep FORM and reusable GMAIL only, and never restart MCP while FORM contains data or CAPTCHA.

## 2026-09-24 — VISUAL IFRAME AND OVERLAY RECOVERY
- An accessibility snapshot omitted a site's visible `Continue with Google` because it was inside the cross-origin `iframe[title="Sign in with Google Button"]`; inspect a headed screenshot and scoped HTML before concluding that a login provider is unavailable.
- The normal recovery was `page.frameLocator('iframe[title="Sign in with Google Button"]').getByRole('button').click()`, then list/remap the popup tab by URL/title, choose the exact Gmail account, and verify account text plus Dashboard/Profile/Logout.
- A Kestra card click failed with `locator.click: Timeout 30000ms exceeded` because a visible job-search modal intercepted pointer events. Detect the dialog, click its visible close control, reacquire the card locator, and retry once; never force-click through the overlay.
- Screenshot/OCR and HTML are UI-state corroboration only. Submission proof still requires the employer success state and matching Gmail evidence.

## 2026-09-24 — PI SESSION AUDIT: CALLS, CONTEXT, AND WAIT WASTE
- Audit source: `<HOME>/.pi/agent/sessions/<session>.jsonl`; no project-local `.pi` folder existed. Parsed 59 user messages, 7,056 assistant messages, 7,256 tool results; tool calls included 5,530 `mcp__cloak_browser`, 425 `mcpScript`, 377 `mcp`, 342 `bash`, 349 `read`, 69 `edit`, and 140 compression calls.
- Categorized 709 error-like results: timeout 242, strict locator 76, wrong tool args 67, script/serialization 62, modal/overlay 44, wrong JS context 11, browser launch 8, navigation race 3, local command/path 8, and other 188. Do not treat the broader 1,006 generic matches/7,836.41 seconds as all wasted time; benign text and queue latency were included.
- The exact largest avoidable cost was 2,310 `waitForTimeout` calls totaling 2,396.725 seconds (39m56.725s). Replacing 70–80% with condition waits saves approximately **27m58s–31m57s per similarly sized session**, conservatively; timeout/error overhead is additional but not precisely attributable.
- Root causes to prevent: repeated same locator after no new evidence; broad duplicate `Apply`/`Next` matches; using `cloak`/`document`/`location` in the wrong MCP/page context; evaluating immediately after navigation (`Execution context was destroyed`); stacked sleeps; and repeated calls after `[NO_BROWSER] Browser failed to launch...`.
- Standard fix: one scoped discovery → one sequential transaction → one targeted readback; outer `mcpScript` calls `tools.cloak_browser_*`, nested run-code uses `const { page } = cloak`, page globals stay inside `page.evaluate`; navigation gets a settled URL/anchor post-check; one fresh-locator retry only.
- For dynamic Rippling forms, wait for `?step=application`, inspect `__NEXT_DATA__.props.pageProps.apiData.jobPost.activeJobApplication`, map required UUID/test-id fields, fill/read back the group, and verify filename/selected state before advancing. For one-by-one applications, check Gmail immediately after employer proof; do not postpone verification merely for batching speed.
