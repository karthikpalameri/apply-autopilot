# SKILLS — navigation index

> Agents start at the repo root **`AGENTS.md`**, then come here. This index maps the
> skill graph so any model can find the right skill for the right task quickly.

## Read first (once per session)

| File | Role |
|---|---|
| `skills/SKILL.md` | **MASTER** — routes the job-hunt graph (RESUME → FIND → APPLY → VERIFY → EMAIL → LEARN → TRACK), dedupe gate, session-start gate, Kaizen loop |
| `skills/RELIABILITY.md` | transaction contract: pre-check → action → post-check for every browser action |
| `skills/REFERENCE.md` | single source of truth (DRY): identity, auth priority, two-tab session, browser topology, cached tool names, react-select commit, saved answers |

## Nodes — one concern each (pick by task)

| Task | Read |
|---|---|
| Exact resume + MD5 gates | `resume/SKILL.md` |
| Find product-company roles | `find/SKILL.md` |
| Apply (ATS router → recipe) | `apply/SKILL.md` |
| Verify submission (proof gate) | `verify/SKILL.md` |
| Email recruiters (draft → consent → send) | `email/SKILL.md` |
| Track applied vs not-applied | `track/SKILL.md` |
| Learn / record lessons | `learn/SKILL.md` |
| Servers, tools, lean mode, SearXNG | `ops/SKILL.md` |

## Recipes — per-ATS mechanics (`recipes/`)

`workday.md` · `greenhouse.md` · `lever.md` · `icims.md` · `linkedin.md` ·
`phenom.md` · `breezy.md` · `jobvite.md` · `oraclehcm.md` · `email-template-humble.md`

## Lessons — accumulated learnings (`LESSONS/`)

`LESSONS-apply.md` · `LESSONS-find.md` · `LESSONS-verify.md` · `LESSONS-email.md` ·
`LESSONS-ops.md` · `LESSONS-naukri-profile.md`

## Profile & onboarding (personal data — git-ignored, never committed)

| File | What it holds | Created by |
|---|---|---|
| `config/user.json` | identity + credentials + Gmail consent | `python3 hub.py onboard` |
| `config/profile.json` | grilled skills, achievements, interview answers | `python3 hub.py onboard` |
| `config/profile.md` | human-readable profile + interview cheat sheet | `python3 hub.py onboard` |
| `config/resume.md5` | resume integrity hash | `onboard` / `setup` |

## Maintenance rules

- **DRY:** every constant/protocol has ONE home (`REFERENCE.md`); nodes point, never restate.
- **SOC:** one concern per node; per-ATS mechanics only in `recipes/`; history only in `LESSONS/`.
- **KISS:** a node states the rule once; rationale lives in the relevant LESSONS file.
- **Archived scripts:** one-off company scripts live in `archive/scripts/` with a one-page
  index (`archive/scripts/README.md`). Archive over delete; never merge scripts into one file.
