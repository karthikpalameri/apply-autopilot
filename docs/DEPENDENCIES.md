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

## Upstream repos (freehire — pinned as git submodules)

| Repo | URL | Why | Type |
|---|---|---|---|
| `strelov1/freehire` | https://github.com/strelov1/freehire.git | open-source job catalogue; keyless API at https://freehire.me/api/v1 | **submodule** `third_party/freehire` |
| `strelov1/freehire-cli` | https://github.com/strelov1/freehire-cli.git | Go CLI over the same API (auth cmds: ghost/market-fit) | **submodule** `third_party/freehire-cli` |

Init on a fresh clone: `git clone --recurse-submodules …` (or `git submodule update --init --recursive`).
Update upstream: `git submodule update --remote`. Full guide: `docs/FREEHIRE.md`.

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

### Skills (shipped by `npm:context-mode`)
`context-mode` · `ctx-doctor` · `ctx-index` · `ctx-insight` · `ctx-purge` ·
`ctx-search` · `ctx-stats` · `ctx-upgrade`

### Extensions
`context-mode:build/adapters/pi/extension.js` · `pi-mcp-adapter` · `pi-web-access:dist`

These are installed automatically by `python3 hub.py install` and verified by
`python3 hub.py eval` + `python3 hub.py test`.

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
| `find/freehire_sweep.py` | freehire discovery (additive source) |
| `core/freehire_client.py` | freehire HTTP transport (SRP) |
| `config/freehire.py` | freehire filters/gates/routing (DRY data) |
| `docs/FREEHIRE.md` | freehire integration guide |

## Secrets inventory (NEVER commit)

`config/user.json` (git-ignored, chmod 600) · `core/.env` (CapSolver key) ·
`config/resume.md5` · LinkedIn/Gmail credentials (in `config/user.json` and browser sessions only).
