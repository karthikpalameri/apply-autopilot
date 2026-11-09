# Quality gates — what to install, what to skip, and why

Everything here was measured on this repo, not copied from a blog post. Run the gate with:

```bash
scripts/check.sh        # ALL checkers, per concern — the ONE gate
scripts/check.sh --fix  # apply safe autofixes first
scripts/check.sh --install  # install the pre-commit hook (once per clone)
```

**`--install` is what makes this enforcement rather than documentation.** It sets
`core.hooksPath=.githooks`, so `.githooks/pre-commit` runs the gate and blocks the
commit. Verified: a planted unused import gave `GIT COMMIT EXIT = 1` and the commit
did not land. Skip once with `git commit --no-verify` — but that is exactly the
case this hook exists to prevent, so fix the cause instead.

`scripts/check.sh` runs ten gates, all via `uvx`/`npx` except the two repo-local
guards, so nothing is installed and nothing is version-pinned:

| Gate | Tool | Config |
|---|---|---|
| python | `ruff` | `pyproject.toml` |
| types | `ty` | `pyproject.toml` |
| dead | `vulture` | none needed |
| dupes | `jscpd` | `.jscpd.json` + `.jscpd-baseline.json` |
| deps | `pip-audit` | reads `.venv` |
| upload | `core/lint_upload.py` | repo-local |
| identity | `core/lint_identity.py` | repo-local |
| shell | `shellcheck` | none needed |
| markdown | `markdownlint-cli2` | `.markdownlint-cli2.jsonc` |
| layering | inline `grep` | `check.sh` |

The `.js` files are all vendored (`runtime/extensions/buster`) or gitignored
(`temp/`, `scratch/`), so no JavaScript linter is wired in.

## Baseline — measured 2026-11-06

Before → after, first full pass against this repo:

| Gate | Before | After | What was actually wrong |
|---|---|---|---|
| deps | **20 CVEs** | 0 | `pypdf` 6.19.0 (18) + `certifi` 2026.7.22 (2) → upgraded to 6.21.4 / 2026.10.23 |
| dead | 4 | 0 | two `X if False else Y` dead branches; two unused parameters |
| types | 25 | 0 | 18 were one cause (`PAGE = None`); 5 were a repeated `(re.search(..) or [None, ..])[1]` idiom; 2 real `.decode()`-on-None bugs in IMAP/email payload handling |
| dupes | 12 clones + 1 boundary breach | 0 breaches | `find/li_premium_scan.py` carried its own socket loop — violated `SINGLE-SOURCE INVARIANT` |
| python | 8 | 0 | 5 unused imports, 2 `raise ... from`, 1 silent `except: pass` |
| markdown | 3 | 0 | one glued heading/list, one double-blank-line, one EOF blank |
| shell | 4 | 0 | unquoted `$t` in `scripts/clean.sh`, one unused var |

The `pypdf` upgrade matters most: it parses the resume, so a bad version silently
breaks DOB/contact extraction and blocks Workday applications.

Known-debt: **11 clone pairs remain** (the four `*_sweep.py` files and the
`login_*`/`gmail_read` overlaps). They are frozen in `.jscpd-baseline.json`.
Do not merge them without proving behavioural equivalence first.

## Cost

| Output | Tokens |
|---|---|
| full gate (`check.sh`) | ~400 |
| `jscpd --reporters ai` | ~172 (vs ~1 700 console, ~4 100 JSON) |
| `ruff --output-format concise` | ~202 (vs ~996 default) |

For scale, `skills/REFERENCE.md` alone is ~7 500 tokens.

Individually:

```bash
uvx ruff check .                                          # python
uvx --from shellcheck-py shellcheck run.sh scripts/*.sh   # shell
npx -y markdownlint-cli2                                  # markdown
```

On 2026-11-05 the repo went from **82 findings to 0** without changing behaviour.

## 1. Python: `ruff` — 1 tool, 0 install

`ruff` replaces flake8 + pyflakes + mccabe + isort in one binary and runs in ~50ms. The rules in
`pyproject.toml` were picked to enforce exactly three properties:

| Property | Rules | What it caught here |
|---|---|---|
| **DRY** | `F` (unused import/var, redefinition, duplicate dict key), `B007`, `B905` | `eval_js` defined **twice** in `core/browser.py` (first was dead); `"segment twilio"` and `"fintech-insurance"` were **duplicate dict keys**; 17 unused imports |
| **KISS** | `C901`, `PLR0912`, `PLR0915`, `SIM` | complexity 20 in `tracker_reconcile.collect_applications`, 16 in `preflight.main`; 15 files opened without a context manager |
| **LOGS** | `S110`, `S112` | "try/except/pass detected, **consider logging the exception**" — caught both silent excepts in `core/freehire_client.py` that a manual audit had found the same day |

That last row is the argument for adding the tool: it found in 50ms what took a hand audit.

**Deliberately NOT enabled** (all would create churn, not value):
`E501` line-too-long — the apply scripts embed minified JS as Python strings; the longest line is 469
chars and must stay on one line. · `I` import sorting — would rewrite every `import json, os, sys`
across 45 files. · `TRY003` long exception messages — this repo raises long diagnostic messages on
purpose.

**Complexity debt is declared, not hidden:** two functions are over budget and are named with their
numbers in `pyproject.toml`. Any *new* violation anywhere else still fails the gate.

## 2. Copy-paste detection: `jscpd` (node) — the one thing ruff cannot see

Ruff finds unused code and duplicated branches inside a function. It cannot see the same helper pasted
into six files, which is what actually happened here (the `ctl()` socket loop existed **11 times**).
`jscpd` does, and it reads `.py`, `.js` **and `.md`**:

```bash
npx jscpd --min-lines 8 --reporters console core config find apply docs skills
```

Use it before a refactor to find the duplication, and after to confirm it is gone.

### Single owners (do not re-inline these)

The 2026-11-05 audit found six helpers copy-pasted across the ATS drivers. Each now has one home;
import it instead of pasting a seventh copy.

| Concept | Owner | Was duplicated in |
|---|---|---|
| accessibility `ref_of()` | `core/dom.py` | `core/login_naukri.py`, `core/login_linkedin.py`, `apply/li_listed_apply.py` |
| failure `dump_dom()` | `core/dom.py` | `core/login_naukri.py`, `core/login_linkedin.py` |
| `progress.json` read/write | `core/progress.py` | `find/tracker_reconcile.py`, `find/sweep.py` |
| status vocabulary | `config/dedupe.py` | 3 divergent sets (see below) |
| "has this job id been tried?" | `core/applied_ledger.has_job_id()` | hand-rolled grep of `APPLIED.md` |
| console line that reaches the log | `core/logger.say()` | bare `print()` in 4 apply scripts |

**Status vocabulary rule.** `SUBMITTED_STATUSES` ⊂ `APPLIED_STATUSES` ⊂ `TERMINAL_STATUSES`, asserted at
import time in `config/dedupe.py`. The three sets had drifted apart in three files; `submitted-email`,
`verified`, `applied` and `done` counted as applied for reporting but **not** terminal for preflight, so
preflight could re-apply to a role already submitted. Add a status to the smallest correct set and the
assertions keep the chain honest.

**Import-order rule.** `sys.path.insert(0, ROOT)` must happen before any `from core…` / `from config…`
import, at module level. A deferred `from core.applied_ledger import co_key, role_key` inside `add()`
was wrapped in `except Exception: identity = None`, which silently degraded dedupe to URL-only and
inflated the collector by **339 phantom records** (reporting 240 applied instead of 234). Never make a
failed import the quiet path — let it raise.

## 3. Markdown: `markdownlint-cli2` (node)

```bash
npx markdownlint-cli2 "docs/**/*.md" "skills/**/*.md"
```

This repo has ~60 markdown files that act as the operator manual (`skills/SKILL.md`, `REFERENCE.md`,
`LESSONS-*.md`). Consistency there matters more than usual because the agent reads them as
instructions. Expect noise on the first run — enable it for *new* files first.

## 4. Dead-code sweep: `vulture`

```bash
uvx vulture core config find apply --min-confidence 80
```

Ruff's `F401`/`F841` are per-file. `vulture` catches a helper kept alive only by another dead helper,
which is how the `snap()` copies survived.

## 4b. Shell: `shellcheck` (and a DRY bug it exposed)

`run.sh` and `run_li.sh` each carried their own copy of the `:3000` launch block — the same
"copies drift" pattern removed eleven times on the Python side, and the copies **had** already drifted:
`sleep 6` vs `sleep 15`, one passed `CLOAK_PLAYWRIGHT_MCP_CONSOLE_FALLBACK`, the other
`--http-session-idle-ttl-ms`. Both now call **`scripts/start_mcp.sh`**, which also polls `/healthz`
instead of sleeping a guessed number of seconds.

Shellcheck then caught `scripts/check.sh` itself: `cd` without `|| exit` (SC2164). The gate checks
every `scripts/*.sh`, so a new script cannot slip past it.

## 5. `pre-commit` — the only way any of this sticks

```bash
uvx pre-commit install
```

Otherwise every gate above is a command someone has to remember.

## What NOT to install, and why

| Package | Verdict | Reason (measured) |
|---|---|---|
| `httpx` | **Yes, optional** | `ats_resolve`: 40 companies **9.94s → 5.80s (1.71x)**, connection reuse across 3 hosts. But `prod_sweep`: **no gain** (6.0s → 4.8–7.5s noise) because its wall time is one slow board at 5.83s, median 0.35s. Keep it in `core/fetch.py` only, where it is optional with a urllib fallback. |
| `tenacity` | No | `core/ui.py::until()` is 20 lines with zero deps and does exactly what the apply scripts need. A dependency for one pattern is not KISS. |
| `loguru` | No | `core/logger.py` already routes console→stderr and file→`logs/app.log`. Replacing it is churn for cosmetics, and stderr routing is load-bearing: it is why `--json` scripts pipe cleanly into `json.load()`. |
| `rich` | No | The one place it would help (the `preflight` READY table) is plain `print` today and is read by the agent, not a human. |
| `pydantic` | No | `config/user.json` is 10 fields read once. |
| `requests` | No | Strictly worse than `httpx` here (no HTTP/2, and it is another dep), and `urllib` is already the fallback. |
| any HTTP/async lib for the MCP path | No | Measured: 200 MCP-style calls over loopback cost **0.24 ms/call** with urllib. Connection setup is 0.24ms of noise next to a Playwright call that takes 10–500ms. **No HTTP package will speed up UI interaction.** |

## Every form element, tested (tests/ui_fixture.html)

`tests/ui_fixture.html` is a self-contained page with one of every control the apply flow meets:
text/email/password/number/tel/textarea, single + multiple `<select>`, `<input type=date>`, the
three-dropdown date split, radio, checkbox, file input, and a div-based dropdown shaped like
react-select. It exists because the live sites hide these behind multi-step flows and change underneath
you — a fixture is deterministic and repeatable.

Measured through the `:9000` bridge:

| Element | Op | Result |
|---|---|---|
| text / email / password / number / tel / textarea | `fill` | 5–41 ms, value read back |
| `<select>` single | `select` | matches by **value or label** (`uk` and `United Kingdom` both work) |
| `<select multiple>` | `select([...])` | 5.6 ms, reports the selected list |
| `<input type=date>` | `fill` | 12 ms, ISO `YYYY-MM-DD` accepted |
| three-dropdown date | `select` ×3 | 2.5–3 ms each |
| radio / checkbox | `check` / `check(state="unchecked")` | 3–46 ms, **idempotent** |
| file input | `upload` | 31 ms, confirms `files.length` |
| missing element | any of the above | fails in **5 s** with a named error, not 30 s of silence |

### Why the native ops beat the JS they replaced

The server had no `select`/`check`/`upload` op, so every call site hand-rolled one:

```js
s.value = "x"; s.dispatchEvent(new Event('change', {bubbles:true}))
```

Three things that costs:
1. **`.click()` on a checkbox is a toggle, not a set.** On the fixture: one click → `true`, two clicks
   → **`false`**. A retry loop that "ensures" a checkbox silently unticks it. Playwright's `check()` is
   a no-op when already in the requested state (measured: two calls, still `true`).
2. **`s.value = …` does not stick on a React-controlled select** — React re-renders from its own state.
   `select_option` drives the real input path.
3. **Multi-select needs one `.selected = true` per option by hand**, and nothing verifies the result.
   `select_option` takes a list and returns what it actually selected.

`gh_apply.py`'s old branch also set `opt.selected = true` on the **radio** fallback — radios have no
`selected` property, so that path could never have worked. It now tries `select()` then `check()`.

### Libraries: none needed, and that is the finding

`playwright 1.63.0` is already installed and already exposes every primitive used above
(`select_option`, `check`, `uncheck`, `set_input_files`, `fill`) with auto-waiting built in. The gap was
never a missing library — it was that `runtime/server.py` did not expose them, so callers re-invented
them in JavaScript.

Rejected for this repo:

| Package | Why not |
|---|---|
| `selenium` | a second browser driver; Playwright already drives the same Chromium |
| `beautifulsoup4` / `lxml` / `selectolax` (the jsoup equivalents) | these parse **static** HTML. We have a live DOM; querying in-page is one ~1 ms eval and reflects the current state, which static parsing cannot. |
| `jsoup` itself | Java |
| `pytest` + `pytest-playwright` | genuinely useful *if* you want `tests/ui_fixture.html` wired into a CI suite — that is the one addition worth considering, and it is optional |

## Where UI speed actually comes from

Not packages. Measured on 2026-11-05:

1. **Stop sleeping** — 45 fixed sleeps = 141s, 14 of them inside loops so the cost multiplied.
   `core/ui.py::until()` polls for readiness with the same ceiling: **141s → 11.8s (-92%)**.
2. **Fewer round trips** — every `ev()` is one socket RPC plus one Playwright evaluation. Batching JS
   into a single `ev()` is worth more than any library.
3. **Avoid `snapshot()` when a targeted `eval_js()` answers the question** — the a11y snapshot
   serialises the whole tree, typically 50–200KB, versus a boolean from one DOM query.

## Measured on a real page (automationexercise.com/products)

Benchmarks against a live page on 2026-11-05, using `core/browser.py` itself:

| Path | Operation | Measured |
|---|---|---|
| MCP `:3000` (`McpBrowser`) | `browser_snapshot` / `text()` | **52 ms**, 38 KB, 681 refs |
| MCP `:3000` | `browser_evaluate` / `eval_js()` | **509 ms** (suspiciously stable: 508, 509, 510) |
| ctl `:9000` (`CtlBrowser`) | `ev()` tiny DOM query | **1.1 ms** |
| ctl `:9000` | `snapshot()` = `innerText.slice(0,4000)` | 1.0 ms |
| either | `time.sleep(5)` that `until()` replaced | 5010 ms |

**The assumption in the previous version of this file was wrong.** It said snapshot-polling should be
replaced with `eval_js` probes. On the MCP path `browser_evaluate` is **~10x more expensive** than
`browser_snapshot`, so that "optimisation" would have made `wait_ref()` slower. Snapshot polling in
`apply/li_listed_apply.py` is correct as written — **leave it alone.** On the `:9000` path the opposite
holds (eval 1.1 ms), which is why the transport must be named whenever a number is quoted.

Three real bugs surfaced only because a live page was used:

1. **`eval_js` echoed the JS source.** Playwright MCP returns
   `### Result\nfalse\n### Ran Playwright code\n...page.evaluate('...includes("foo")')`.
   Any `if "foo" in str(result)` is therefore *always true*, and `str(result) == "404"` is *never*
   true. `core/browser.py::_unwrap()` now returns just the Result value.
2. **`product_companies_builder.probe_linkedin()` was dead logic** — it compared the wrapped string to
   `"404"`, so it returned `"ok"` for every URL including dead ones. Fixed by (1); verified it now
   returns `404`.
3. **Stale session id gave 404, but `_rpc` only recovered from 400.** After any `:3000` restart the
   whole browser abstraction failed until someone manually deleted `config/mcp_session.json`.

## THE 500ms: `PLAYWRIGHT_MCP_TIMEOUT_SETTLE`

The MCP `:3000` path was slow because of an upstream default, not a bug. `@playwright/mcp` waits
after **every action** for triggered work to settle:

```text
--timeout-settle <ms>   how long to wait after each action for triggered work to settle
                        defaults to 500ms            env PLAYWRIGHT_MCP_TIMEOUT_SETTLE
```

It is added to the call, not used as a ceiling. Measured on `about:blank` with `() => 1+1`, so no
page work at all:

| `PLAYWRIGHT_MCP_TIMEOUT_SETTLE` | `browser_evaluate` |
|---|---|
| 500 (default) | **512 ms** |
| 250 | 265 ms |
| 100 | **114 ms** |
| 0 | **7 ms** |

The real JS execution is under 1 ms. `run.sh` and `run_li.sh` now set **100 ms** — a 4.6x saving while
keeping a margin for code that has not been converted to `until()`. Drop to `0` once every action is
followed by a wait.

`browser_snapshot` was never affected (27–52 ms) because it is not an "action".

## The profile collision — why it *felt* slow

`cloakbrowser-mcp` refuses to launch when another process holds the same `--profile-dir`:

```text
Error: Browser is already in use for .../runtime/mcp-session
```

**Every failing tool call still burns the full action timeout (~5010 ms).** So a locked profile does
not look like an error — it looks like "the UI takes 5 seconds for everything".

Pi's own cloak-browser MCP and the repo's `:3000` server were both configured for
`runtime/mcp-session`, so whichever started second was broken. `run.sh` / `run_li.sh` now use a
separate **`runtime/py-session`**, and both servers can run at once — verified: `test_hub` 6/6 with
Pi's browser and `:3000` up simultaneously.

> Corollary for any timing run: check the return value before trusting a number.
> `### Error: Browser is already in use` is not a slow call, it is a failed one.

## Every UI operation, measured on a real page

`automationexercise.com/products`, both transports up, 2026-11-05.

### MCP `:3000` (after `PLAYWRIGHT_MCP_TIMEOUT_SETTLE=100`)

| Tool | Cost |
|---|---|
| `browser_console_messages` | 1.1 ms |
| `browser_network_requests` | 1.8 ms |
| `browser_tabs` list | 4.8 ms |
| `browser_press_key` | 12.8 ms |
| `browser_snapshot` | 28 ms |
| `browser_hover` | 85 ms |
| `browser_evaluate` | 112 ms |
| `browser_click` | 181 ms |
| **`browser_take_screenshot`** | **440 ms** |

### ctl `:9000`

| Op | Cost |
|---|---|
| `status` | 0.6 ms |
| `eval` | 2.3 ms |
| `mouse_click` | 2.7 ms |
| `keys` | 7.3 ms |
| `fill` | **8 ms** |
| `htype` | 17 ms |
| **`snap` (screenshot)** | **79 ms** — 5.5x cheaper than the same screenshot over MCP |
| **`hfill`** | **210 ms** |

### Three real costs found this way

1. **`hfill` vs `fill` — 96x.** `hfill` clicks, selects all, then types at 30 ms/char. On a 25-char
   email: **867 ms vs 9 ms**. A Greenhouse form with ~8 fields spends ~7s typing per application for
   no benefit — an ATS does not fingerprint keystroke timing. `core/ui.fill()` now defaults to the
   fast path and keeps the human one behind **`PI_HUMAN_FILL=1`** (verified: 5 ms default, 891 ms with
   the flag, same `ok=True`). Use it only on sites that actually inspect input.

2. **OCR is the most expensive single operation — 215x the DOM.** screenshot 75 ms + tesseract 203 ms
   = **278 ms**, versus `document.body.innerText` at **1 ms**. `core/see.py`'s "~3s" is the cold font
   cache; warm it is 0.28 s. Read the DOM unless you need what the DOM cannot show (canvas, images,
   rendering bugs).

3. **Screenshots cost 5.5x more over MCP** (440 ms) than over the ctl bridge (79 ms). If a script only
   needs a screenshot, the `:9000` op is the cheap one.

### `tesseract` was not installed

`docs/INSTALL.md` lists it as a prerequisite, but it was missing here — and the three scripts that use
it each failed differently: `hard_assert.py` printed a clear message, **`see.py` crashed with a raw
`FileNotFoundError` traceback**, and `verify.py` swallowed it into `"(ocr fail)"`. Three copies of the
same `subprocess.run(["tesseract", ...])`, three different failure stories.

Now: `core/ocr.py` is the single owner — `available()` checks PATH once and logs `brew install
tesseract`, `read()` returns `""` and says why. `verify.py` now prints
`(OCR unavailable — install tesseract; DOM state above is still valid)` instead of lying.
