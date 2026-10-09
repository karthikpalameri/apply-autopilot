# 📦 DEPENDENCIES — complete manifest

## Python (venv: `.venv`, Python 3.10+)

| Package | Why | Type |
|---|---|---|
| `cloakbrowser` | Playwright + stealth Chromium — the browser engine | **direct** |
| `pypdf` | read resume PDF | **direct** |
| `Pillow` | image handling for OCR screenshots | **direct** |
| `pytesseract` | OCR wrapper (`core/see.py`, `core/verify.py`) | **direct** |
| `requests` | HTTP for ATS APIs (`find/prod_sweep.py`) | **direct** |
| `certifi` | TLS certs for API calls | **direct** |

## System tools

| Tool | Why | Check |
|---|---|---|
| python3 (3.10+) | runtime | `python3 --version` |
| node + npx (LTS) | cloakbrowser-mcp server | `node --version` |
| tesseract | OCR engine | `tesseract --version` |
| docker (optional) | local SearXNG search | `docker --version` |
| git | clone/share | `git --version` |
| pi (optional) | coding agent | `pi --version` |

## MCP servers (one owner per channel — never duplicate)

| Server | Transport | Owner | Consumer | Why |
|---|---|---|---|---|
| `cloak-browser` (`@devinwangd/cloak-browser-mcp`) | stdio | `~/.pi/agent/mcp-adapter.json` | Pi agent | interactive browser: `browser_run_code_unsafe` + `cloak` global |
| `cloakbrowser-mcp` (npm) | HTTP :3000 | `hub.py start` / `run.sh` | Python (`core/browser.py`) | upstream Playwright-MCP surface for batch scripts |
| `pi-mcp-adapter` (pi pkg) | — | pi package | — | pi ↔ MCP bridge |

## Servers (hub.py start launches both)

| Server | Port | Profile | Role |
|---|---|---|---|
| `runtime/server.py` (CloakBrowser control) | :9000 | `runtime/session` (logged-in: LinkedIn/Gmail) | fast-path recipes |
| `cloakbrowser-mcp` | :3000 | `runtime/mcp-session` | snapshot-driven unknown sites |

## Pi extensions / packages

`~/.pi/agent/settings.json` → packages: `pi-web-access`, `pi-mcp-adapter`, `context-mode`.
`hub.py install` installs them; `hub.py mcp-config` writes the config files.

## Files to refer (by concern)

| File | Concern |
|---|---|
| `README.md` | architecture overview |
| `docs/INSTALL.md` | setup + run order + troubleshooting |
| `config/user.json.example` | schema for **YOUR data** (real file is git-ignored) |
| `config/answers.py` | the loader (`A` dict) |
| `config/progress.json` | application tracker (git-ignored, personal) |
| `skills/README.md` | skill index |
| `core/test_hub.py` | health check (6 tests) |
| `core/mcp_test.py` | MCP live probe |

## Secrets inventory (NEVER commit)

`config/user.json` (git-ignored, chmod 600) · `core/.env` (CapSolver key) ·
`config/resume.md5` · LinkedIn/Gmail credentials (in `config/user.json` and browser sessions only).
