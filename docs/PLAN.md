# PLAN — context-lean rewrite & product direction

Status: draft, 2026-11-08. Decision log from a stack review, not a commit of code.

## Diagnosis

This repo is an LLM-agent-driven browser form-filler. The division of labour is
already correct and is NOT the problem:

- `skills/**/*.md` = the agent's procedural memory (recipes, discipline). Cheap,
  editable, no redeploy. Same pattern as Claude Skills / Cursor rules.
- `core/`, `find/`, `apply/` (Python) = deterministic glue (ledger, fetch, OCR,
  socket bridge, resume gate, dedupe).

What limits it is architecture, not language or framework:

1. Identity is hard-wired to one user (`config/user.json`).
2. It runs locally (socket `ctl.py` ↔ `:9000` browser via MCP).
3. Generalization is hand-rolled per ATS (one recipe per board).

## Decisions

- Do NOT adopt LangChain / LangGraph / LangChain4j for this repo. The core loop
  is a single-shot field mapping, not a multi-step agent. A framework adds a
  layer and increases token use; it cannot shrink a DOM snapshot or a recipe.
- Keep the personal agent in Python, as-is, framework-free.
- The rewrite that matters is knowledge → data (recipes become deterministic
  data, so they stop living in the prompt).
- Product direction (if pursued later): a Chrome MV3 extension with BYOK + a
  thin relay, in TypeScript. Not a server-side browser farm.

## Measured numbers

Knowledge markdown, tokenised at ~4 chars/token:

| Scope | Tokens | Files |
|---|---|---|
| `skills/recipes/*.md` (per-ATS) | 13,209 | 14 |
| `skills/*.md` (procedures) | 27,661 | 6 |
| **Total** | **~40,900** | 20 |

Per-apply recipe cost ranges 324 (breezy) → 2,996 (greenhouse) tokens.
`REFERENCE.md` (10.3K) + `RELIABILITY.md` (7.0K) load once per session and
amortise across applies.

Estimated per-apply context budget (browser/snapshot figures are estimates;
recipe figures measured):

| Cost item | Today | After rewrite | Saved |
|---|---|---|---|
| Recipe text in prompt | ~1,500 | ~0 (JSON data) | ~100% |
| Form info to model | ~3,000 × ~5 turns = ~15,000 | ~300 × ~2 turns = ~600 | ~96% |
| Decision turns (main model) | ~5–8 | ~1–2 | ~75% |
| **Per-run total** | **~20,000–60,000** | **~5,000–15,000** | **~70–85%** |

Cost at ~40K → ~10K tokens/run: DeepSeek ($0.3/M) saves ~$0.009/run (~$9 per
1,000); a frontier model ($3/M) saves ~$0.09/run (~$90–150 per 1,000). The real
payoff is speed + reliability, not the bill — at DeepSeek prices the dollar
saving is pennies.

## The levers (ordered by impact)

1. **Recipes → data.** `skills/recipes/*.md` becomes JSON: `{selector → value,
   quirks}`. A deterministic filler reads the data; the model never sees the
   recipe. Biggest context cut available (~100% of recipe tokens).
2. **Minimal field schema.** Send only `{label, name, type, required}` per
   field to the model, not the accessibility tree. ~96% cut on the dominant,
   re-sent-every-turn line item.
3. **Cheap classifier routing (Jev).** Keep Jev for yes/no and field→answer
   picks; reserve the main model for hard mapping.
4. **One-shot fill + readback.** Single call does discovery + fill + readback,
   then submit once. Fewer turns = fewer snapshot re-sends.

## Packages worth adopting

None of these produce the 70–85% cut — that is architecture. These make the
architecture cheap and reliable.

### Python (pip)

| Package | Why |
|---|---|
| `instructor` | Structured `{field: value}` output with retry/validation. Fewer malformed-JSON retries = fewer turns = less context. High value. |
| `selectolax` | Fast HTML parse for field extraction from raw HTML without a full a11y tree. |
| `tiktoken` | Accurate token metering so the budget is measured, not guessed. |
| `json_repair` | Repair malformed LLM JSON on the rare failure. Cheap reliability. |
| `litellm` | BYOK gateway: 100+ providers, caching, cost tracking, fallbacks. This is the relay for a SaaS. |
| `pydantic-ai` | Lean typed agent framework (lighter than LangChain) — only if a framework is ever warranted. |
| `playwright` (pip) | Direct browser control; could collapse the socket/MCP indirection. Architectural, high-change — evaluate separately. |
| `browser-use` | Anti-recommendation: popular LLM browser automation, but heavier and likely increases context vs the current hand-rolled bridge. |

### Node (npm) — for the TS extension/relay, if built

| Package | Why |
|---|---|
| `@crxjs/vite-plugin` | Vite + TS build for the MV3 extension. |
| `zod` | Validate the `{field: value}` map (TS equivalent of pydantic). |
| `cheerio` / `linkedom` | DOM parsing in content script / server. |
| `hono` | Thin relay on Cloudflare Workers for BYOK LLM calls. |
| `ai` (Vercel AI SDK) | Unified LLM calls in TS with provider/BYOK support. |

## Roadmap

Phase 0 — Measure one real form snapshot live (exact bytes for the ~3,000-token
estimate) before committing to the rewrite.

Phase 1 — Recipes → data for the top-3 ATS by win-rate (greenhouse, workday,
lever). Deterministic filler in `core/`. Gate: recipe tokens out of the prompt,
fill still correct.

Phase 2 — Minimal field schema extraction + `instructor` for the field→value
map. Gate: one-shot fill + readback on one real board.

Phase 3 — (Product, optional) MV3 extension + Hono relay + BYOK. Gate: a second
human can fill their own form with their own key.

## Open questions

- Keep the socket/MCP bridge, or move to direct `playwright` (pip) control?
- Is the product goal still live, or is this repo staying a personal agent?
