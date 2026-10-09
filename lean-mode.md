# LEAN MODE — token runbook (apply from next session)

Goal: cut the input-token bill. Every tool call's input+output
is re-sent to the model on EVERY turn. Save 3KB once = save 3KB × remaining turns.

## 1. NEW SESSION PER TASK BATCH  (biggest lever)
- One pi session = one batch (e.g., "scan+apply round", "park mine").
- Finished a batch? Start a new session. ~0 tokens vs ~150K-token history.
- Start: `pi` fresh; job state lives in `scratch/APPLIED.md` + `config/progress.json` (survives sessions).

## 2. COMPRESS MEMORY
- Trackers already caveman-terse (APPLIED.md, progress.json). Keep them that way.
- context-mode auto-captures decisions/errors — useful, keep. Purge only if it grows huge:
  `ctx_purge` (project scope) — read-only check first: `ctx_stats`.

## 3. DON'T RE-READ BIG DOCS
- Pi READMEs / skill SKILL.md files = 5–30 KB EACH read, re-sent every turn.
- Read a skill/doc ONCE per session, or use `ctx_index` (index → tiny previews, full text on demand).
- Never re-open the pi docs for the same topic twice in one session.

## 4. CTL-FIRST AUTOMATION  (dual-mode)
- DEFAULT: job-apply-hub `core/ctl.py` (:9000) — compact JSON, ~0.5 KB/call.
  - navigate / eval / click-by-selector / type / htype / upload_cdp / select / mouse_click / snap
  - text selectors work: `op_click "[role=option]:text-is('Yes')"` (Playwright trusted clicks)
- FALLBACK (only after 2 ctl failures): Pi stdio `cloak-browser` → `browser_run_code_unsafe` (the `:3000` server is Python-only)
  - load logic from a FILE via ctx_execute_file / `.js` on disk → ONE-LINE call, no big inline scripts
  - use for: react-select commits, arbitrary JS, shadow/portal DOM
- PROOF GATE unchanged: fill → verify value → submit → confirmation text.

## 5. NO SCREENSHOTS ON THE VISION-BILLED MODEL
- The vision-billed model bills image tokens (even when displayed "omitted").
- Use `tesseract` OCR on a crop, or DOM `innerText` — not full-page screenshots.
- If a screenshot is required: capture SMALL (viewport, downscaled), never fullPage.

## Session-start checklist
1. `pgrep -f runtime/server.py` (ctl up) + LinkedIn logged in (li_at cookie)
2. Read `scratch/APPLIED.md` tail + `config/progress.json` (state, no re-reading docs)
3. Check `config/targets.json` queue
4. Go — ctl first, cloakbrowser fallback, no screenshots, no big doc reads.
