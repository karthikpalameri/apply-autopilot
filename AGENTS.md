# AGENTS.md — read this first

You are working in **apply-autopilot**. This file is the entry point; it does not
repeat the rules, it tells you where the one copy of each lives.

## One rule above all others: NO SECRETS IN THIS REPO

Every personal value lives in **git-ignored local files**, created by the user
(`python3 hub.py onboard` / `setup`):

| File | Contents |
|---|---|
| `config/user.json` | identity, CTC, resume path, credentials |
| `config/profile.json` | grilled skills, achievements, interview answers |
| `config/resume.md5` | resume integrity hash |

These are **never committed**. The tracked template is `config/user.json.example`.
Scripts read personal data through `config/answers.py` (`A` dict) — never hardcode
a name/email/phone/salary/resume path in code or skills.

## Before you write code

Read these two, once per session:

1. `skills/REFERENCE.md` — constants, identity, auth, browser discipline, quality gates
2. `skills/RELIABILITY.md` — the transaction contract (pre-check → action → post-check)

Do not read the whole `skills/` tree per task. Each rule has exactly one owner
file; follow the pointer, never copy the text.

## Commands (cross-platform, via `hub.py`)

| Command | Purpose |
|---|---|
| `onboard` | first-run guided experience (resume → confirm → grill → Gmail consent) |
| `setup` | quick identity/resume/credentials wizard |
| `install` | interactive installer (OS detect → venv → npm MCP → pi packages) |
| `start` / `stop` / `restart` | browser stack (`runtime/server.py` :9000 + `cloakbrowser-mcp` :3000) |
| `health` | 6-test health check (`core/test_hub.py`) |
| `track` | applied-vs-not-applied report |
| `doctor` | environment diagnosis |
| `eval` | readiness evaluation (% success rate + fixes) |
| `test` | full test suite in `tests/` |
| `mcp-config` | regenerate `~/.pi/agent/mcp-adapter.json` + `web-search.json` |

POSIX wrappers: `run.sh`, `run_li.sh`, `track.sh`. Windows: `run.bat`, `run_li.bat`,
`track.bat`, `setup.bat`, `install.bat`.

## Before you commit — MANDATORY

```bash
scripts/check.sh
```

Exit 1 blocks the commit. Ten gates: ruff, ty, vulture, jscpd (duplication +
single-owner boundaries), pip-audit, upload guard, identity guard, page-guard,
shellcheck, markdownlint, layering.

Install the hook once per clone so this cannot be forgotten:

```bash
scripts/check.sh --install
```

## Non-negotiables

| Rule | Owner | If you break it |
|---|---|---|
| Personal data has ONE source | `config/user.json` → `skills/REFERENCE.md#identity` | `lint_identity` fails |
| Resume uploads inject, never click | `skills/resume/SKILL.md#upload-method` | a native OS picker opens and blocks the run |
| Socket call has ONE owner | `core/ctl.py` | the `socket-call-single-owner` boundary fails |
| Scrolling is bounded | `core/ui.py::scroll_until` | the page scrolls for seconds on a miss |
| CAPTCHA: fill everything, then stop | `skills/REFERENCE.md#standing-rule--captcha-handling` | — |
| No full-page images or raw screenshots in model context; DOM first, local OCR if needed | `skills/REFERENCE.md` | images re-sent every turn |
| Jev classifies, never writes; no PII to Jev | `skills/jev/SKILL.md` | third-party leak or a confident wrong answer |
| Layering is one-way | `apply/ → find/ → core/` | the `layering` gate fails |

## When a gate fails

Fix the cause. Never:

- add `# noqa`, `# type: ignore`, or an ignore-list entry to make it green
- delete code to lower a duplication number
- move `.jscpd.json` (paths resolve from its folder — elsewhere it silently passes)
- edit `third_party/`, `temp/`, `scratch/`, or `archive/`

Known debt is recorded in `docs/QUALITY.md`. Do not "fix" debt listed there
without proving behavioural equivalence first.

## Commits

Never `git commit` or `git push` unless the user asks. Never `git checkout --`
or `git reset --hard` on work you did not create.

## Detailed knowledge

| Need | File |
|---|---|
| Which ATS, what it does | `skills/recipes/<ats>.md` |
| Cheap decision instead of a main-model turn | `skills/jev/SKILL.md` |
| Fresh-clone Pi/Jev setup | `docs/INSTALL.md` (via `skills/pi-setup/SKILL.md`) |
| Find existing scripts and ATS recipes | `skills/tool-map/SKILL.md` |
| Live ATS failure history | `skills/LESSONS.md` (newest section first) |
| Tool decisions + measurements | `docs/QUALITY.md` |
| Install / dependencies | `docs/INSTALL.md` |
| Private web search (SearXNG) | `skills/searxng/SKILL.md` → `http://127.0.0.1:8080` |

## Repository map

```text
README.md           ← human overview
hub.py              ← cross-platform CLI (single entry point)
installer.py        ← interactive cross-platform installer
eval.py             ← readiness evaluation (% success rate)
setup.py            ← identity/credentials wizard (also imported by onboarding.py)
onboarding.py       ← resume-first guided setup
resume_parser.py    ← heuristic resume PDF reader

core/               ← browser control, resume gates, ledger, dedupe, OCR, decision layer
apply/              ← apply drivers (li_drive, li_listed_apply, gh_apply, ih_sweep, fill_gh_fast)
find/               ← job discovery (sweeps, preflight, ats_resolve, tracker_reconcile)
config/             ← answers.py (A dict), dedupe.py, user.json.example, pi config templates
runtime/server.py   ← ctl bridge :9000 (the ONLY tracked file under runtime/)
infra/searxng/      ← local private web search (auto-setup + docker-compose)
scripts/            ← check.sh (the gate), start_mcp.sh, clean.sh, cost_report.py, setup_pi.sh
tests/              ← organized test suite (run: python3 hub.py test)
skills/             ← the skill graph (see below)
```
