# freehire integration — additive discovery source (SoC)

freehire (https://github.com/strelov1/freehire, MIT) is an open-source,
self-hostable job catalogue that crawls 3.3M+ postings from 124 ATS platforms
and enriches each with LLM facets. Its companion CLI (freehire-cli) is a thin
client + MCP server over the same API.

We use it **additively**: it sits *alongside* `prod_sweep.py`, `listed_sweep.py`
and `sweep.py` as another discovery source. It never replaces them, and it never
touches the apply engine, resume MD5 gate, or tracker.

## Dependencies (URLs)

| Component | URL | Tracked as |
|---|---|---|
| freehire engine (catalogue + API) | https://github.com/strelov1/freehire.git | git submodule `third_party/freehire` |
| freehire-cli (Go CLI + MCP) | https://github.com/strelov1/freehire-cli.git | git submodule `third_party/freehire-cli` |
| freehire public API (keyless) | https://freehire.me/api/v1 | network (no local clone needed) |
| freehire API reference | https://freehire.me/docs/api | docs |
| CLI prebuilt binary | https://freehire.me/install.sh | optional (auth commands only) |

**Fresh clone → working in one step:**
```bash
git clone --recurse-submodules <your-fork> job-apply-hub   # pulls both submodules
# or, if already cloned:
git submodule update --init --recursive
```

Update upstream: `git submodule update --remote`.

## Architecture (SoC / SOLID)

Three layers, one owner each — mirrors the repo's `core/` · `config/` · `find/` split:

```
config/freehire.py        DATA       filters, gates, ROUTING map (single source of truth)
core/freehire_client.py   TRANSPORT  HTTP/SSL/envelope parsing + logging (SRP, no rules)
find/freehire_sweep.py    USE-CASE   discovery orchestration: client → gates → dedupe → route
```

- **Single Responsibility** — the client only talks JSON; the sweep only decides;
  `config/freehire.py` only holds data/vocabulary.
- **Open/Closed** — add an ATS source to `ROUTING` or a filter in
  `build_search_params()` without touching the client or sweep.
- **Logging** — everything goes through `core/logger.py` → `logs/app.log`
  (console + rotating file). The client logs each call (with `@timeit`), the
  sweep logs every decision: `skip (company_type)`, `DUPLICATE`, `pass`.

## Run

```bash
.venv/bin/python find/freehire_sweep.py           # Bangalore QA/SDET, strict gate
.venv/bin/python find/freehire_sweep.py india     # India-wide QA/SDET
.venv/bin/python find/freehire_sweep.py --all     # full annotated pool (type/stale shown)
.venv/bin/python find/freehire_sweep.py --strict  # product companies only (drop inhouse/GCC)
.venv/bin/python find/freehire_sweep.py --json    # machine-readable (agents)
```

Keyless — no auth. Under the hood:
`GET https://freehire.me/api/v1/agent/jobs/search?category=qa&cities=bangalore&sort=posted_at&order=desc`
plus an `q=sdet&q_fields=title` pass, merged and deduped by `public_slug`.

## Gates applied (mirrors skills/find/SKILL.md)

| Gate | freehire field |
|---|---|
| QA/SDET title only | `QA` / `NON` regex (same intent as prod_sweep.py) |
| product company / genuine GCC | `enrichment.company_type ∈ {product, inhouse}` |
| fresh only (skip evergreen) | `reality.class == fresh` + `age_days` |
| already applied | dedupe vs `config/progress.json` + `scratch/APPLIED.md` (company + role) |

## Output → next action

A `✓` line means "passes all gates". The `route:` hint tells you where to apply:

- `greenhouse` → `apply/fill_gh_fast.py`
- `lever` / `ashby` / `workable` / `workday` / `icims` / `breezy` / `jobvite` /
  `phenom` / `oraclehcm` → existing recipes under `skills/recipes/`
- `NO RECIPE YET` → needs a new apply script (SuccessFactors is the biggest gap —
  16 of 36 Bangalore QA postings)

## Optional: authenticated commands (ghost report, market-fit, tracking)

```bash
freehire auth login                                  # opens browser to sign in
freehire ghost report <slug> --applied-on 2026-10-01 # feed back dead applications
freehire market-fit --skills selenium,java,api-testing --category qa --country in
```

These are optional; the sweep needs no auth.
