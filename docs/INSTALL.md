# 🔧 INSTALL — complete onboarding (KISS/DRY/SOC)

Everything a NEW user needs: deps, pi settings, MCP servers, local SearXNG,
first run, verification. ~10 min.

## 0. Architecture (mental model)
```text
Three browser channels — one owner each (never duplicate):
  Pi agent      ── stdio ──> cloak-browser (@devinwangd/cloak-browser-mcp)          [Pi owns, fast]
  Python batch  ── HTTP :3000 ──> cloakbrowser-mcp (npm, upstream @playwright/mcp)  [run.sh owns]
  Python fast   ── TCP :9000 ──> runtime/server.py ──> Chrome (CDP)                [run.sh owns]
memory/context: context-mode (pi pkg)   search: local SearXNG (docker :8080)   captcha: hard stop (no API)
```
Pi's MCP lives in `~/.pi/agent/mcp-adapter.json`; `:3000` is Python-only and must never be declared to Pi.

## 1. Prerequisites (macOS)
```bash
brew install python@3.13 node tesseract docker        # tesseract = OCR (screenshots→text)
# Docker Desktop app (GUI) — start once, keeps daemon alive
```

## 2. Project install
```bash
git clone --recurse-submodules <your-fork> apply-autopilot && cd apply-autopilot
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt   # ONE source of truth for Python deps (see docs/DEPENDENCIES.md)
# httpx (in requirements.txt) is runtime-OPTIONAL: measured 1.71x faster on
# find/ats_resolve.py (40 companies: 9.94s -> 5.80s). Without it the repo still
# runs, on urllib. Set PI_FETCH_HTTPX=0 to force urllib.
python3 setup.py          # wizard → writes config/user.json (YOUR resume/creds; chmod 600)
cp <your-resume>.pdf config/Your_Name_Resume.pdf   # or point user.json (resume_path) at your own; kEEP professional filename, never config/resume.pdf
```
`--recurse-submodules` pulls `third_party/freehire` + `third_party/freehire-cli`
(see docs/FREEHIRE.md). If you already cloned without it:
`git submodule update --init --recursive`.

### Required Freehire authentication bootstrap

Complete this immediately after cloning and before any Freehire search, tracking,
market-fit, or application workflow. The local sweep uses a keyless API, but the
repository workflow still requires a validated CLI session first.

```bash
curl -fsSL https://freehire.me/install.sh | sh        # installs `freehire` on PATH
if ! freehire auth status; then
  freehire auth login                                  # browser sign-in + any 2FA
fi
freehire auth status                                   # must confirm the account
```

Run this block from a real interactive terminal: the installer may require `sudo`,
and browser/2FA callbacks cannot complete in a non-interactive pipe. Do not commit
or copy `~/.freehire/creds.json` into the repository. If login fails, stop and have
the operator complete the browser sign-in before continuing.

After login, open `https://freehire.me/my/profile`, upload
`config/Your_Name_Resume.pdf` under **Your CV**, wait for parsing, and
click **Create profile**. Verify with `freehire profile --json`; it must show a QA
specialization and a populated `cv` object before any search or application work.

## 3. Pi browser MCP — `~/.pi/agent/mcp-adapter.json`
`pi-mcp-adapter` reads the user-level adapter config; the `:3000` Python server is
started by `run.sh` and must **never** be declared to Pi. The ONE browser template
is `config/pi-mcp.json.example` (12 direct tools; other browser tools remain
reachable via the `mcp` proxy/Jev). Install the stdio server, then copy the
template in **step 3c**; do not paste a second, drifting JSON example here.

## 3b. Quality gate (one command, nothing to install)

```bash
scripts/check.sh        # runs every checker below
```

| File type | Checker | Catches |
|---|---|---|
| `.py` (48 files) | `ruff` | unused/dead code, duplicate dict keys, redefinitions (DRY); complexity (KISS); `try/except/pass` (LOGS) |
| `.sh` (5 files) | `shellcheck` | quoting, word-splitting, `cd` without `|| exit` |
| `.md` (37 files) | `markdownlint` | heading structure, code fences without a language, bare URLs |
| `.js` | *none needed* | the only JS is vendored (`runtime/extensions/buster`) |

All three run through `uvx` / `npx`, so there is nothing to install and no version
to pin. `scripts/check.sh --fix` applies the safe autofixes.

See `docs/QUALITY.md` for what each rule enforces, the measured cost of every UI
operation, and which packages were benchmarked and **rejected**.

<a id="pi-jev--project-skills"></a>

## 3c. Pi-Jev + project skills (fresh clone)

Run from the repository root on macOS. Pi itself requires Node 22.19+ for npm;
follow the [Pi quickstart](https://pi.dev/docs/latest/quickstart) if `pi` is
missing. Your **main-model** account (`/login` in Pi) and Jev's OpenRouter key
are separate. Never paste an API key into a shell command, project file, or chat.

1. Install Pi + its packages once at user level (idempotent — safe to re-run;
   the package list lives in the script, not here):

   ```bash
   scripts/setup_pi.sh
   ```

2. Configure the Pi browser. **If `~/.pi/agent/mcp-adapter.json` already exists,
   review/merge it rather than overwriting other servers.** On a new machine:

   ```bash
   mkdir -p ~/.pi/agent
   python3 - <<'PY'
   import json
   from pathlib import Path
   root = Path.cwd().resolve()
   template = Path('config/pi-mcp.json.example').read_text()
   config = json.loads(template.replace('/ABSOLUTE/PATH/TO/apply-autopilot', str(root)))
   dest = Path.home() / '.pi/agent/mcp-adapter.json'
   if dest.exists():
       raise SystemExit(f'{dest} exists; merge by hand, do not overwrite')
   dest.write_text(json.dumps(config, indent=2) + '\n')
   print(f'created {dest} (12 direct browser tools)')
   PY
   ```

3. Store Jev's OpenRouter key privately. This prompts without echo and writes
   `~/.pi/agent/secrets/openrouter_api_key` with mode 600. If you already set
   `OPENROUTER_API_KEY`, skip this step; **never overwrite** an existing secret.

   ```bash
   python3 - <<'PY'
   from pathlib import Path
   from getpass import getpass
   p = Path.home() / '.pi/agent/secrets/openrouter_api_key'
   p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
   if p.exists():
       raise SystemExit(f'{p} exists; leave it unchanged')
   p.write_text(getpass('OpenRouter key (hidden): ').strip() + '\n')
   p.chmod(0o600)
   print('Jev key saved (value hidden)')
   PY
   ```

4. Trust **this** clone interactively. Pi only loads `.pi/settings.json` after
   project trust; its `skills` list contains the project skills (including
   `pi-setup`, `tool-map`, `jev`). Start `pi` from the repo root, accept the
   project-trust prompt, then `/trust` to save that choice. Run `/reload` after
   editing skills/settings during an open session. Never copy someone else's
   `~/.pi/agent/trust.json` into a new clone.

5. Start a **fresh** session with `scripts/pi_jev.sh`. It loads Jev tools,
   pins `PI_JEV_MODEL=typesafe/jev-1.13` unless overridden, but defaults
   `PI_JEV_AUTO=0`, `PI_JEV_THINKING=0`, `PI_JEV_COMPACT=0` to avoid extra calls
   or changes to the model without evidence. To test automatic routing, run
   `PI_JEV_AUTO=1 scripts/pi_jev.sh` instead. A single read-only test found
   the right skill in **both** modes: auto off 5.42 s / $0.000688 Pi estimate;
   auto on 9.72 s / $0.000720 Pi estimate **plus Jev**. Network variability
   makes one test inconclusive, so auto remains opt-in. This launcher works in
   zsh and bash; no `.zshrc`/`.bash_profile` edits or plaintext keys are
   required. `/jev auto on` changes **only the current process**. If you
   prefer plain `pi`, put non-secret `export PI_JEV_AUTO=1` in `~/.zshrc`
   (zsh) or `~/.bash_profile` (bash), then restart the shell. Never put API
   keys in shell profiles.

6. Verify in the **new** session: `/jev status` (key source + model + intended Auto setting),
   `/jev skills` (the project skill list), `/jev test` (one tiny API request),
   `/mcp-adapter` (browser connected; 12 direct tools). Pi's skill descriptions
   are lazy: Jev selects skills/tools; it does **not** read every recipe or
   script. See `skills/tool-map/SKILL.md` for deterministic code lookup.

7. Measure with one **sanitized, read-only** prompt repeated in fresh sessions,
   same main model and tool loadout. Compare `PI_JEV_AUTO=0 scripts/pi_jev.sh`
   to `PI_JEV_AUTO=1 scripts/pi_jev.sh`. Run
   `scripts/cost_report.py --last 2` for Pi's **estimated main-model** cost,
   plus OpenRouter's usage page for Jev's separate bill. Compare wall time and
   error/answer quality too. One run per mode is noise; repeat before claiming
   savings. Do not use a real job submission as a benchmark.

## 4. pi web search (local SearXNG) — `~/.pi/web-search.json`
Template: `config/pi-web-search.json.example` → `{ "provider": "all", "searxngBaseUrl": "http://127.0.0.1:8080" }`
(tool picks config at startup — restart pi after writing).

## 5. Local SearXNG (docker) — free + private web search
```bash
docker rm -f searxng 2>/dev/null
docker run -d --name searxng -p 8080:8080 \
  -e SEARXNG_BASE_URL=http://127.0.0.1:8080 -e SEARXNG_SECRET=<random> searxng/searxng
# JSON API + no limiter (default image blocks it):
docker exec searxng sh -c 'cat > /etc/searxng/settings.yml << "EOF"
use_default_settings: true
server:
  secret_key: "<random>"
  limiter: false
  public_instance: false
search:
  formats: [html, json]
EOF'
docker restart searxng
curl -s "http://127.0.0.1:8080/search?q=test&format=json" -H "Accept: application/json"   # expect JSON
```

## 6. CAPTCHA — hard stop (no solving, no API key)
CAPTCHA pages are a hard stop. Automation never solves or bypasses a challenge: it fills
safe fields, leaves the headed page open for the user, and records `waiting-user-captcha`.
No external CAPTCHA-solving service or API key is used or required.

## 7. Start the stack (servers)
```bash
./run.sh                 # ctl :9000 (browser, visible) + health check
# or manually: .venv/bin/python runtime/server.py &   (log: logs/server.out)
```
First run: browser opens blank → log in manually once to LinkedIn + Gmail
(sessions persist in `runtime/mcp-session/`).

## 8. Verification checklist
```bash
.venv/bin/python core/ctl.py '{"op":"status"}'              # browser up
.venv/bin/python core/wday_probe.py                         # Workday up/down (outage-aware)
.venv/bin/python core/ctl.py '{"op":"navigate","url":"https://www.linkedin.com/feed/"}'  # logged in?
curl -s "http://127.0.0.1:8080/search?q=test&format=json" | head -c 80   # searxng up
.venv/bin/python find/prod_sweep.py                         # sample sweep works
.venv/bin/python find/freehire_sweep.py                     # freehire sweep works (keyless)
```

## 9. Daily flow (lean mode — read lean-mode.md)
1. Fresh pi session per task batch (token cost)
2. Probe Workday → apply via ctl (compact) → cloakbrowser fallback for react-selects
3. Proof gate: submit → confirmation text → log to scratch/APPLIED.md
4. `cat lean-mode.md` once per session (2KB), never re-read big docs

## 10. Costs / tokens
- The current model bills INPUT tokens per turn = full history re-sent every turn.
- Rules: new session per batch · no screenshot tools (image tokens) · ctl-first · no doc re-reads.
- context-mode MCP auto-captures memory (saver, keep).
