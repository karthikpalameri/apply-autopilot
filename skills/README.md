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
| Exact resume + MD5 gates | `skills/resume/SKILL.md` |
| Find product-company roles | `skills/find/SKILL.md` |
| Apply (ATS router → recipe) | `skills/apply/SKILL.md` |
| Verify submission (proof gate) | `skills/verify/SKILL.md` |
| Email recruiters (draft → consent → send) | `skills/email/SKILL.md` |
| Track applied vs not-applied | `skills/track/SKILL.md` |
| Learn / record lessons | `skills/learn/SKILL.md` |
| Servers, tools, lean mode | `skills/ops/SKILL.md` |
| Web search (private SearXNG) | `skills/searxng/SKILL.md` |

## Recipes — per-ATS mechanics (`skills/recipes/`)

`skills/recipes/workday.md` · `skills/recipes/greenhouse.md` · `skills/recipes/lever.md` ·
`skills/recipes/icims.md` · `skills/recipes/linkedin.md` · `skills/recipes/phenom.md` ·
`skills/recipes/breezy.md` · `skills/recipes/jobvite.md` · `skills/recipes/oraclehcm.md` ·
`skills/recipes/email-template-humble.md`

## Web search
- **`skills/searxng/SKILL.md`** — private local SearXNG (https://github.com/searxng/searxng).
  If you need searching, use `http://127.0.0.1:8080`; setup: `python3 infra/searxng/setup.py`.

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
