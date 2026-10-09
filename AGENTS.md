# 🤖 AGENTS.md — how to work in this repository

This file is the entry point for **any** coding agent, AI model, or human.
Read it first, then follow the pointers. It is intentionally short — details live
in the referenced files (DRY).

---

## 1. What this repository does

**Apply Autopilot** automates the repetitive parts of a job hunt for one candidate
(the user):

```
FIND openings → VERIFY they match → APPLY with the user's tailored resume
             → VERIFY submission proof → EMAIL recruiters → TRACK everything
```

- **Why:** job applications are 80% repetitive form-filling; the user's energy should
  go into choosing roles and talking to recruiters, not re-typing their address.
- **How:** browser automation (CloakBrowser / Playwright) drives ATS forms
  (Greenhouse, Lever, Workday, LinkedIn Easy Apply, Phenom, iCIMS, …), reads Gmail
  for OTPs + confirmations, and enforces a proof gate before anything is counted as
  "applied".

---

## 2. One rule above all others: NO SECRETS IN THIS REPO

Every personal value lives in **git-ignored local files**, created by the user:

| File | Contents | Created by |
|---|---|---|
| `config/user.json` | identity, CTC, resume path, credentials | `python3 hub.py onboard` / `setup` |
| `config/profile.json` | grilled skills, achievements, interview answers | `onboard` |
| `config/resume.md5` | resume integrity hash | `onboard` / `setup` |
| `core/.env` | CapSolver key (optional) | `onboard` / `setup` |

These are **never committed**. The tracked template is `config/user.json.example`.
Scripts read personal data through `config/answers.py` (`A` dict) — never hardcode a
name/email/phone/salary/resume path in code or skills.

---

## 3. Commands (cross-platform)

All entry points are in `hub.py` — use `python3 hub.py <command>` (Windows: `python`).

| Command | Purpose |
|---|---|
| `onboard` | **first-run guided experience** — explains, grills skills, configures everything |
| `setup` | quick identity/resume/credentials wizard only |
| `install` | create `.venv` + install Python deps + npm MCP + pi packages + pi config |
| `start` / `stop` / `restart` | start/stop the browser stack (`runtime/server.py` :9000 + `cloakbrowser-mcp` :3000) |
| `health` | 6-test health check (`core/test_hub.py`) |
| `track` | applied-vs-not-applied report |
| `doctor` | environment diagnosis |
| `mcp-config` | regenerate `~/.pi/agent/mcp-adapter.json` + `web-search.json` |

POSIX wrappers: `run.sh`, `run_li.sh`, `track.sh`. Windows: `run.bat`, `run_li.bat`,
`track.bat`, `setup.bat`, `install.bat`.

---

## 4. Repository map (for navigation)

```
README.md           ← human overview
AGENTS.md           ← this file (agent navigation)
PRIVACY.md          ← what was stripped + how to stay clean
docs/INSTALL.md     ← full onboarding + troubleshooting (cross-platform)
docs/DEPENDENCIES.md← complete dependency manifest
lean-mode.md        ← token/cost runbook (read once per session)

hub.py              ← cross-platform CLI (single entry point)
setup.py            ← identity/credentials wizard (also imported by onboarding.py)
onboarding.py       ← GUIDED setup: explain → grill → Gmail consent → generate profile

core/               ← browser control, resume gates, gmail read, OCR, capsolver, verify
apply/              ← apply drivers (li_drive, ih_sweep, fill_gh_fast, li_listed_apply)
find/               ← job discovery (prod_sweep, sweep, product_companies_builder, tracker_reconcile)
config/             ← answers.py (A dict), user.json.example, data/ (company seed), pi config templates
runtime/server.py   ← ctl bridge :9000 (the ONLY tracked file under runtime/)
infra/searxng/      ← local private web search (docker compose)
archive/scripts/    ← one-off per-company apply scripts (legacy reference; read its README)
skills/             ← the skill graph (see below)
product_companies.md← 500-company product list (websites + LinkedIn)
```

---

## 5. The skills graph — how to pick up skills

`skills/` is organized as a **directed graph**. Read in this order:

1. **`skills/SKILL.md`** — the MASTER. Routes the job-hunt graph
   (RESUME → FIND → APPLY → VERIFY → EMAIL → LEARN → TRACK) + dedupe gate.
2. **`skills/RELIABILITY.md`** — transaction contract (pre-check → action → post-check).
3. **`skills/REFERENCE.md`** — single source of truth (identity, auth priority,
   two-tab session, browser topology, cached tool names, react-select commit).

Then, per concern (read only the one you need):

| Task | Read |
|---|---|
| Resume + MD5 gates | `skills/resume/SKILL.md` |
| Find jobs | `skills/find/SKILL.md` |
| Apply (ATS router) | `skills/apply/SKILL.md` + the matching `skills/recipes/<ats>.md` |
| Verify submission | `skills/verify/SKILL.md` |
| Email recruiters | `skills/email/SKILL.md` + `skills/recipes/email-template-humble.md` |
| Track applications | `skills/track/SKILL.md` |
| Learn / record lessons | `skills/learn/SKILL.md` → `skills/LESSONS/LESSONS-*.md` |
| Ops (servers/tools) | `skills/ops/SKILL.md` |

**Recipes** (`skills/recipes/`): per-ATS mechanics — `workday`, `greenhouse`, `lever`,
`icims`, `linkedin`, `phenom`, `breezy`, `jobvite`, `oraclehcm`, `email-template-humble`.

**Lessons** (`skills/LESSONS/`): accumulated hard-won learnings, one file per concern.

**Index:** `skills/README.md` (graph summary).

---

## 6. Skill frontmatter convention

Each `skills/*/SKILL.md` has YAML frontmatter with `name`, `description` (triggers),
and `parent` (graph edge). When a task matches a node's description, read that node +
its `parent` chain once per session — do not re-read unchanged files repeatedly.

---

## 7. Session-start checklist (any agent)

1. Read `AGENTS.md` (this file) + `skills/SKILL.md` + `skills/REFERENCE.md` once.
2. Load `config/user.json` + `config/progress.json` (if present) via `config/answers.py`.
3. Confirm the browser stack is up (`python3 hub.py health`) before any browser work.
4. Never invent personal data — resolve everything from `config/answers.py` (`A`).
5. Proof gate: no success message (DOM/OCR) + confirmation email = NOT "applied".

---

## 8. User-consent boundaries

- **Gmail** is used ONLY with explicit consent (recorded as `gmail_consent` in
  `config/user.json`): read OTPs, read confirmations, register/log into ATS accounts,
  and draft/send cold emails (drafts by default; sending requires a fresh user approval).
- **CAPTCHA / biometrics / secrets** are user-only pauses — never bypass.
- Never create duplicate accounts; never store passwords in logs/skills/progress files.
