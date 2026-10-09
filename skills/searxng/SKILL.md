---
name: searxng
description: WEB SEARCH node — private local SearXNG (https://github.com/searxng/searxng).
  Use it whenever you need web research: find portal-only job roles, verify a company/ATS,
  or look up anything. Trigger: "search", "web search", "find role via web", "searxng".
parent: skills/ops/SKILL.md
---

# SEARXNG — private local web search (no API key, free, JSON API)

> **If you need searching, use this.** We have a local SearXNG instance at
> `http://127.0.0.1:8080` — project: **https://github.com/searxng/searxng**

## WHAT it is
SearXNG is a self-hosted **metasearch engine**: it queries many search engines
(Google, Bing, DuckDuckGo, …) and returns merged results — without tracking you,
without API keys, and with a JSON endpoint that any script/agent can call.

## WHY we use it
- **Find portal-only roles** — jobs that are NOT on LinkedIn/ATS boards:
  `"<product> QA SDET Bengaluru greenhouse/lever/icims"`
- **Free + private** — no API key, no rate-limit bills, queries stay on your machine.
- **JSON API** — scripts and the pi agent (`web_search`) can call it directly.

## HOW to bring it up (one command)
```bash
python3 infra/searxng/setup.py          # writes .env + settings.yml + docker compose up
# or manually:
cd infra/searxng && docker compose up -d
```
It runs two containers: `searxng-core` (search, :8080) + `searxng-valkey` (cache/limiter).

## WHEN to use it
- BEFORE applying: find roles that aren't on clean boards (`skills/find/SKILL.md` → web_search).
- To verify a company/product/ATS domain when the job board is ambiguous.
- Any time you need a quick web fact — prefer SearXNG over guessing.

## HOW to query it
```bash
# JSON API (what scripts/agents use):
curl -s 'http://127.0.0.1:8080/search?q=Bengaluru+SDET+Lever+jobs&format=json' -H 'Accept: application/json'

# Human web UI:
open http://127.0.0.1:8080
```
JSON response: `{"results": [{"title": ..., "url": ..., "content": ...}, ...]}`.

## Agent integration (pi)
- `~/.pi/web-search.json` → `{ "provider": "all", "searxngBaseUrl": "http://127.0.0.1:8080" }`
  (written by `python3 hub.py install` / `hub.py mcp-config`). Restart pi after writing.
- In any skill, say **"if you need searching use SearXNG at http://127.0.0.1:8080"**.

## Troubleshooting
```bash
cd infra/searxng
docker compose ps                 # status
docker compose logs -f core       # logs
docker compose down               # stop (keeps data)
docker compose up -d              # start again
python3 infra/searxng/setup.py    # re-run to verify / fix config
```
- JSON 403/empty → `core-config/settings.yml` must have `search.formats: [html, json]`.
- Port already used → `SEARXNG_PORT` in `infra/searxng/.env`.
- Not exposed to the internet — bound to `127.0.0.1` only (private).

## LESSONS
- skills/LESSONS/LESSONS-ops.md (Docker/SearXNG section)

---

## RELATED (skill graph — every node is one click away)
- **Master:** `skills/SKILL.md` · **Reference:** `skills/REFERENCE.md` · **Reliability:** `skills/RELIABILITY.md`
- **Nodes:** `apply` · `email` · `find` · `learn` · `ops` · `resume` · `track` · `verify` · `searxng` (each `skills/<node>/SKILL.md`)
- **Recipes:** `skills/recipes/` — workday · greenhouse · lever · icims · linkedin · phenom · breezy · jobvite · oraclehcm · email-template-humble
- **Lessons:** `skills/LESSONS/LESSONS-*.md` — apply · find · verify · email · ops · naukri-profile
- **Index:** `skills/README.md` · **Repo entry for agents:** `AGENTS.md`
