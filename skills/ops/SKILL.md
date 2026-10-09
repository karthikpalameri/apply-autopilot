---
name: ops
description: OPS node — servers, tools, session. Caveman.
parent: skills/SKILL.md
---

# OPS

## RELIABILITY + SPEED DEFAULT
- Read `skills/RELIABILITY.md`. Target 30% fewer browser round trips: use ctl for stable selectors, one compact DOM transaction for related reads/fills, condition waits instead of fixed sleeps, and a fresh-target post-check after each transaction.
- **Auth fast path + two-tab fast path:** → **`skills/REFERENCE.md#auth-priority`** + **`skills/REFERENCE.md#two-tab-session`**. One FORM/VERIFY tab + one GMAIL tab; `browser_tabs {action:"switch", id}` to alternate; never navigate FORM to Gmail.
- Use one transport/tool spelling per session — cached tool names + no-invent rule at **`skills/REFERENCE.md#cached-cloak-tool-names`**. `mcp__cloak_browser` takes `{tool, args}`; never pass `{describe: ...}` to it.
- For stable pages use: scoped discovery → related action batch → targeted readback. Do not snapshot or sleep after every field; invalidate the cache only after rerender/navigation/modal transition.
- Keep one short script for related form actions. `browser_run_code_unsafe` uses `const { page } = cloak;` on this server; an `async (page) => ...` wrapper causes avoidable evaluation errors.

## SERVERS
→ **`skills/REFERENCE.md#browser-topology`** (single source). Pi uses the **stdio** `cloak-browser` server; `:3000` is Python-only.
- Pi browser = `cloak-browser` (@devinwangd, stdio) from `~/.pi/agent/mcp-adapter.json` — `mcp__cloak_browser` tools, viewport `1280x800`, profile `runtime/mcp-session`.
- Python `:3000` (upstream Playwright-MCP surface, `core/browser.py`) + ctl `:9000`: start with `bash run.sh`; LinkedIn sweep = `bash run_li.sh` (lock cleanup + VISIBLE browser + fresh session, TTL 1h). Only one owner of the profile at a time; never declare `:3000` to Pi.
- **Viewport setting:** keep CloakBrowser at `1280x800` (`--viewport 1280x800`). This matches the MacBook Air's logical workspace, prevents right/bottom clipping, and is faster than oversized viewports. Override with `CLOAK_VIEWPORT=WxH` when intentionally needed; do not restart while a FORM tab contains entered application data.
- Session reuse: sid in config/mcp_session.json — no restarts between runs. 404 → delete sid.
- Never restart MCP or run `run_li.sh` while FORM contains entered data or a CAPTCHA; restart only after preserving exact blocker evidence.
- Keep at most FORM + GMAIL plus one temporary ATS tab; close completed/duplicate tabs. Refresh tab identity before every switch.
- ctl :9000: `.venv/bin/python runtime/server.py` — dies on profile conflicts; kill via `lsof +D`
- Lock: `rm -f runtime/mcp-session/.cloakbrowser-mcp-profile.lock` before start

## TAB SAFETY
- Follow `skills/SKILL.md` → **TWO-TAB SESSION**. `core/gmail_read.py` reuses GMAIL and restores FORM; do not restart MCP during a filled form.
- **Agent owns Gmail and routine ATS work:** use the persistent Gmail tab for verification links, OTPs, and confirmations, then restore the application tab. Ask the user only for direct password/vault entry or user-only CAPTCHA/security challenges—not for Gmail reading or ordinary form actions.

## VISUAL / OVERLAY RECOVERY
- Use a headed screenshot plus scoped HTML when the accessibility tree contradicts what is visibly rendered. Cross-origin Google sign-in may appear as `iframe[title="Sign in with Google Button"]`; inspect the iframe and click its normal button rather than declaring the provider absent.
- After a social-login popup, list tabs once and remap by URL/title before switching; verify the account identity, Dashboard/Profile links, and Logout.
- If a job-card click returns `locator.click: Timeout 30000ms exceeded` and says modal content intercepted pointer events, inspect `[role=dialog]`/modal selectors, click the visible close control, reacquire the card locator, and retry once. Do not force-click through an overlay.
- For user-requested visual proof, capture the screenshot immediately after the state transition, inspect it/OCR it, and compare it with the HTML URL/title/account text. Keep screenshot/OCR as state corroboration, not submission proof.

## PI AUDIT CORRECTIONS — 2026-09-24
→ **`skills/REFERENCE.md#pi-audit-corrections`** (single source). Context boundary, navigation post-check, locator discipline, browser health, dynamic Rippling forms, wait budget.

## TOOLS
- McpBrowser (core/browser.py): snapshot/eval_js/type(slowly)/click/file_upload/tabs + `ensure_gmail_tab()`
- **browser_run_code_unsafe = FULL PLAYWRIGHT** via the server-global `cloak` object (`const { page } = cloak; ...`) — THE power tool; this MCP build does not accept an `async (page) => {...}` wrapper.
- **browser_press_key = THE keyboard tool** (browser_keyboard = phantom, silently fails)
- tesseract OCR: screenshot = truth
- core/gmail_read.py: read-only confirmations/OTPs
- core/login_linkedin.py, login_naukri.py: ref-based logins
- macOS TCC: copy files into hub (browser can't read ~/Downloads)

## TOOL → FILE MAP (discover any tool by the file that owns it)
| Tool / capability | File |
|---|---|
| Cross-platform CLI (setup/install/start/stop/health/track/doctor) | `hub.py` |
| Guided resume-first onboarding | `onboarding.py` + `resume_parser.py` |
| Identity/credentials wizard | `setup.py` |
| Config loader (single source of truth `A`) | `config/answers.py` |
| Browser abstraction (MCP :3000 + ctl :9000) | `core/browser.py` |
| ctl bridge :9000 (TCP JSONL) | `runtime/server.py` + `core/ctl.py` |
| Resume MD5 gates (PICK/UPLOAD/POST) | `core/resume_secure.py` |
| Gmail OTP/confirmation read | `core/gmail_read.py` (browser) · `core/gmail_otp.py` (IMAP) |
| LinkedIn / Naukri login | `core/login_linkedin.py` · `core/login_naukri.py` |
| CapSolver captcha | `core/capsolver.py` |
| Post-submit proof gate | `core/hard_assert.py` |
| OCR / DOM verify | `core/see.py` · `core/verify.py` |
| Health check (6 tests) | `core/test_hub.py` |
| MCP live probe | `core/mcp_test.py` |
| Workday up/down probe | `core/wday_probe.py` |
| Apply drivers | `apply/li_drive.py` · `apply/ih_sweep.py` · `apply/fill_gh_fast.py` · `apply/li_listed_apply.py` |
| Job discovery | `find/prod_sweep.py` · `find/sweep.py` · `find/product_companies_builder.py` · `find/product_lookup.py` |
| Applied-vs-not report | `find/tracker_reconcile.py` (via `hub.py track`) |

## MCP INDEX (discover every MCP server + who owns it)
| Server | Transport | Port / pipe | Owner | Consumer |
|---|---|---|---|---|
| `cloak-browser` (`@devinwangd/cloak-browser-mcp`) | stdio | — | `~/.pi/agent/mcp-adapter.json` | Pi agent (`mcp__cloak_browser` tools) |
| `cloakbrowser-mcp` (npm) | Streamable HTTP | :3000 | `hub.py start` / `run.sh` | Python (`core/browser.py` McpBrowser) |
| `runtime/server.py` (ctl) | TCP JSONL | :9000 | `hub.py start` / `run.sh` | Python fast-path (`core/ctl.py`) |
| `pi-mcp-adapter` (pi pkg) | — | — | pi package | pi ↔ MCP bridge |

**Rule:** one owner per channel — `:3000` must never be declared to Pi (`.mcp.json` stays `{"mcpServers": {}}`).

## LESSONS
- skills/LESSONS/LESSONS-ops.md
- core/hard_assert.py: assert_applied(b, co) — post-submit proof gate (OCR+DOM). ALWAYS import + call after submit.

## LEAN MODE (token and call discipline)
- ctl :9000 = DEFAULT channel (compact JSON ~0.5KB/call)
- Python fallback = `cloakbrowser-mcp` :3000 (React/custom controls); the Pi agent uses stdio `mcp__cloak_browser` — use short in-call scripts, not one call per field
- No screenshots on vision-billed model (tesseract/DOM instead); use one final proof capture only · new Pi session per task batch
- Do not alternate ctl/MCP for the same field unless the post-check proves failure.
- Probe Workday before apply: `.venv/bin/python core/wday_probe.py`

## DOCKER / SEARXNG (start + persist)
- SearXNG gives pi free/private web search. If Docker daemon is down:
  `open -a Docker` (Docker Desktop GUI) and wait ~30s for daemon.
- If the container is stopped (status `Exited`), just `docker start searxng` (it exits cleanly).
- Make it survive reboots: `docker update --restart unless-stopped searxng`.
- Verify JSON API: `curl -s "http://127.0.0.1:8080/search?q=test&format=json" -H "Accept: application/json"` → HTTP 200.
- Config is already correct in the image: `limiter:false`, `public_instance:false`, `formats:[html,json]`,
  `~/.pi/web-search.json` → `searxngBaseUrl: http://127.0.0.1:8080`.
- Trade-off: pi's `provider: searxng` may report "Blocked internal address for 127.0.0.1" on some calls
  (SearXNG SSRF guard) — use provider "all" or fall back to another provider if that bites.


---

## RELATED (skill graph — every node is one click away)
- **Master:** `skills/SKILL.md` · **Reference:** `skills/REFERENCE.md` · **Reliability:** `skills/RELIABILITY.md`
- **Nodes:** `apply` · `email` · `find` · `learn` · `ops` · `resume` · `track` · `verify` (each `skills/<node>/SKILL.md`)
- **Recipes:** `skills/recipes/` — workday · greenhouse · lever · icims · linkedin · phenom · breezy · jobvite · oraclehcm · email-template-humble
- **Lessons:** `skills/LESSONS/LESSONS-*.md` — apply · find · verify · email · ops · naukri-profile
- **Index:** `skills/README.md` · **Repo entry for agents:** `AGENTS.md`
