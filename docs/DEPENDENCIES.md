# 📦 DEPENDENCIES — complete manifest

## Python (venv: `.venv`, Python 3.13)
Single source of truth for `pip install`: **`requirements.txt`** (pinned direct deps).
| Package | Why | Type |
|---|---|---|
| cloakbrowser | Playwright + stealth Chromium — the browser engine (runtime/server.py) | **direct** |
| pypdf | read resume PDF (find/resume_facts.py) | **direct** |
| httpx | connection pooling (core/fetch.py, core/freehire_client.py) | direct (runtime-optional) |
| playwright | imported directly by runtime/server.py (sync_api) | direct (also cloakbrowser dep) |
| cryptography, greenlet, pyee, cffi, pycparser | cloakbrowser's bundled runtime | transitive |

OCR uses the `tesseract` **binary** via subprocess (core/ocr.py) — no pip OCR package.

## System tools
| Tool | Why | Check |
|---|---|---|
| python3 (3.13) | runtime | `python3 --version` |
| node + npx (22.19+; v26 current) | cloakbrowser-mcp server + Pi | `node --version` |
| tesseract | OCR engine (brew binary, not a pip pkg) | `tesseract --version` |
| git | backup/share | `git --version` |

## Upstream repos (freehire — pinned as git submodules)
| Repo | URL | Why | Type |
|---|---|---|---|
| `strelov1/freehire` | <https://github.com/strelov1/freehire.git> | open-source job catalogue; keyless API at <https://freehire.me/api/v1> | **submodule** `third_party/freehire` |
| `strelov1/freehire-cli` | <https://github.com/strelov1/freehire-cli.git> | Go CLI over the same API (auth cmds: ghost/market-fit) | **submodule** `third_party/freehire-cli` |

Init on a fresh clone: `git clone --recurse-submodules …` (or `git submodule update --init --recursive`).
Update upstream: `git submodule update --remote`. Full guide: `docs/FREEHIRE.md`.

## MCPs (one owner per channel — never duplicate)
| Server | Transport | Owner | Consumer | Why |
|---|---|---|---|---|
| `cloak-browser` (`@devinwangd/cloak-browser-mcp`) | stdio | `~/.pi/agent/mcp-adapter.json` | Pi agent | interactive browser: `browser_run_code_unsafe` + `cloak` global |
| `cloakbrowser-mcp` (npm) | HTTP :3000 | `run.sh` / `run_li.sh` | Python (`core/browser.py`) | upstream Playwright-MCP surface for batch scripts |
| `pi-mcp-adapter` (pi pkg) | — | pi package | — | pi ↔ MCP bridge; `/mcp` |

## Servers (run.sh starts both)
| Server | Port | Profile | Role |
|---|---|---|---|
| runtime/server.py (CloakBrowser control) | :9000 | runtime/session (LOGGED IN: LinkedIn/Gmail/InstaHyre) | fast-path recipes |
| cloakbrowser-mcp | :3000 | runtime/mcp-session (fresh) | snapshot-driven unknown sites |

## Pi agents (installed skills)
None at `~/.pi/agent/skills/` — project skills in `./skills/` are the only skill source.
`~/apply-autopilot/skills/`: find · apply · email · ops · li-easy-apply-vision (SOC playbooks)

## Pi extensions
`~/.pi/agent/settings.json` → packages: `pi-web-access`, `pi-mcp-adapter`, `context-mode`; `builtin:mcp` disabled (the adapter replaces it).
Browser MCP for Pi: `~/.pi/agent/mcp-adapter.json` → `cloak-browser` (stdio, `@devinwangd/cloak-browser-mcp`).

## Files to refer (by concern)
| File | Concern |
|---|---|
| `README.md` | architecture overview |
| `docs/INSTALL.md` | setup + run order + troubleshooting |
| `config/user.json` | **YOUR data** (DRY — run setup.py) |
| `config/answers.py` | the loader (A dict) |
| `config/progress.json` | application tracker |
| `skills/README.md` | skill index |
| `core/test_hub.py` | health check (6 tests) |
| `find/freehire_sweep.py` | freehire discovery (additive source) |
| `core/freehire_client.py` | freehire HTTP transport (SRP) |
| `config/freehire.py` | freehire filters/gates/routing (DRY data) |
| `core/mcp_test.py` | MCP live probe |

## Secrets inventory (never commit)
`config/user.json` (git-ignored, chmod 600) · `.env` · LinkedIn/Gmail/InstaHyre logins (browser session only). No CAPTCHA-solving API key exists or is required — CAPTCHA is a hard stop.
