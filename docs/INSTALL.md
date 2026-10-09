# 🔧 INSTALL — complete onboarding (macOS / Linux / Windows)

Everything a NEW user needs: deps, pi settings, MCP servers, local SearXNG,
CapSolver, first run, verification. ~10–15 min.

> **TL;DR:** `python3 hub.py setup && python3 hub.py install && python3 hub.py start`
> (Windows: use `python` and the `.bat` files).

---

## 0. Architecture (mental model)

```
Three browser channels — one owner each (never duplicate):
  Pi agent      ── stdio ──> cloak-browser (@devinwangd/cloak-browser-mcp)      [Pi owns]
  Python batch  ── HTTP :3000 ──> cloakbrowser-mcp (npm)                        [hub.py start owns]
  Python fast   ── TCP :9000 ──> runtime/server.py ──> Chrome (CDP)             [hub.py start owns]

memory/context: context-mode (pi pkg)   search: local SearXNG (docker :8080)   captcha: CapSolver
```

Pi's MCP lives in `~/.pi/agent/mcp-adapter.json`; `:3000` is Python-only and must never be declared to Pi.

---

## 1. Prerequisites

Install these once, per OS:

| Tool | macOS | Linux (Debian/Ubuntu) | Windows |
|---|---|---|---|
| Python 3.10+ | `brew install python@3.12` | `sudo apt install python3 python3-venv` | <https://python.org> (tick "Add to PATH") |
| Node.js + npm (LTS) | `brew install node` | `sudo apt install nodejs npm` (or nvm) | <https://nodejs.org> |
| Tesseract (OCR) | `brew install tesseract` | `sudo apt install tesseract-ocr` | `winget install tesseract` |
| Docker (SearXNG, optional) | Docker Desktop | `sudo apt install docker.io docker-compose-v2` | Docker Desktop |

---

## 2. Get the code + personalize

```bash
git clone <your-fork> apply-autopilot
cd apply-autopilot

python3 setup.py          # step-by-step wizard → writes config/user.json (chmod 600)
python3 setup.py --check  # show what's configured (secrets redacted)
```

`setup.py` asks for: name, email, phone, location, CTC, notice period, LinkedIn/GitHub,
resume path, education, LinkedIn/Gmail credentials, CapSolver key, and India application
answers. It also derives the professional resume filename and writes `config/resume.md5`.

---

## 3. Install dependencies (venv + npm + pi)

```bash
python3 hub.py install
```

This does, in order:

1. Creates `.venv` and installs `requirements.txt` (`cloakbrowser`, `pypdf`, `Pillow`,
   `pytesseract`, `requests`, `certifi`).
2. Verifies Node + npm.
3. Installs `@devinwangd/cloak-browser-mcp` globally (Pi stdio browser).
4. Installs pi packages: `pi-mcp-adapter`, `pi-web-access`, `context-mode`.
5. Writes `~/.pi/agent/mcp-adapter.json` + `~/.pi/web-search.json` (absolute paths for this checkout).
6. Prints OS-specific guidance for tesseract/docker.

---

## 4. pi agent MCP — `~/.pi/agent/mcp-adapter.json`

`hub.py install` writes this for you. Template: `config/pi-mcp.json.example`.
It registers the stdio browser server:

```json
{ "mcpServers": {
  "cloak-browser": { "command": "cloak-browser-mcp",
    "args": ["--caps","all","--headed","--viewport","1280x800","--enable-unsafe-eval",
             "--profile-dir","/ABSOLUTE/PATH/apply-autopilot/runtime/mcp-session",
             "--upload-allow-dir","/ABSOLUTE/PATH/apply-autopilot",
             "--download-dir","/ABSOLUTE/PATH/apply-autopilot/temp","--max-pages","20"] } } }
```

Restart pi after writing. The `:3000` Python server is started by `hub.py start`, never declared to Pi.

---

## 5. pi web search (local SearXNG) — `~/.pi/web-search.json`

```json
{ "provider": "all", "searxngBaseUrl": "http://127.0.0.1:8080" }
```

Start SearXNG first (below), then restart pi.

---

## 6. Local SearXNG (docker) — free + private web search

```bash
cd infra/searxng
cp .env.example .env              # edit SEARXNG_SECRET if you like
docker compose up -d
curl -s "http://127.0.0.1:8080/search?q=test&format=json" -H "Accept: application/json"
```

---

## 7. CapSolver (reCAPTCHA/hCaptcha) — optional

Get a key at <https://dashboard.capsolver.com> and enter it in `setup.py`
(or put `CAPSOLVER_API_KEY=` in `core/.env`).

---

## 8. Start the stack

```bash
python3 hub.py start     # ctl :9000 + cloakbrowser-mcp :3000 + health check
python3 hub.py stop      # stop both
python3 hub.py restart
```

First run: the browser opens → log in manually once to LinkedIn + Gmail
(sessions persist in `runtime/mcp-session/`).

---

## 9. Verification checklist

```bash
python3 hub.py doctor                                   # environment diagnosis
.venv/bin/python core/ctl.py '{"op":"status"}'          # browser up
.venv/bin/python core/wday_probe.py                     # Workday up/down
curl -s "http://127.0.0.1:8080/search?q=test&format=json" | head -c 80   # searxng
.venv/bin/python find/prod_sweep.py                     # sample sweep works
```

---

## 10. Daily flow (lean mode)

1. Fresh pi session per task batch (token cost).
2. Probe Workday → apply via ctl (compact) → cloakbrowser fallback for react-selects.
3. Proof gate: submit → confirmation text → log to `scratch/APPLIED.md`.
4. `cat lean-mode.md` once per session — don't re-read the big docs.

---

## Troubleshooting

- **`.venv` missing** → `python3 hub.py install`
- **Port 9000/3000 busy** → `python3 hub.py stop && python3 hub.py start`
- **`config/user.json` missing** → `python3 setup.py`
- **Browser won't launch** → check tesseract + node versions via `python3 hub.py doctor`
