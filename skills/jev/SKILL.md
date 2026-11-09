---
name: jev
description: JEV node — cheap classifier for decisions, not a writer. Use for field→answer picks and yes/no gates; never for content.
parent: skills/SKILL.md
version: 1.0.0
---

# JEV (cheap decision node — measured 2026-11-07)

TypeSafe Jev = **classifier**, not a writer or repository indexer. It answers typed
questions about sanitized state. Pricing varies; compare provider bills and Pi
session usage instead of assuming a fixed saving. Deterministic code/lookup is
cheaper and more reliable than either model. Use Jev only for a genuine choice
among known options that cannot be resolved from an existing source.

## CALL SHAPE

```text
jev_evaluate({
  state: { label: "Are you legally authorized to work in India?", options: ["Yes","No"] },
  questions: {
    answer:      { type: "choice", instructions: "Which option answers this form field?", criteria: { Yes: "affirmative", No: "negative" } },
    is_required: { type: "noul",   instructions: "Is this field mandatory?" }
  }
})
```

- `choice` → returns the option; `criteria` MUST be a label→description map, not an array. `noul` → probability 0..1. `score` → rubric level.
- **Threshold 0.65.** Below it: do NOT guess. Read the field again, or escalate to
  the main model. Jev is calibrated, not magic — a 0.4 is a real "I don't know".
- Batch many questions in ONE call. Never one call per field.
- Standard PII-free payloads live in `core/decide.py` (`field_question`,
  `gate_questions`, `candidate_fit_question`) — use them, don't hand-roll the call shape.

## USE IT FOR

- Form field label + option list → which answer (source: `config/answers.py`, `config/user.json`).
- Yes/no gates: "is this page a confirmation?", "is this ATS Greenhouse?", "did the value land?"
- Ranking: which recipe (`skills/recipes/*.md`) fits this employer page.
- `jev_find_tools` when a required Pi tool is inactive; it only activates registered
  tools, and does not shrink the current active tool set.
- `jev_find_skill` when the right project skill is unknown. Pi registers the
  project skill descriptions in `.pi/settings.json`; skills are read on demand.
  In pi-jev 0.8.0 recommendations may have a leading `skill:` in the name.
  `/skill:skill:tool-map` is invalid: use `/skill:tool-map` (drop one prefix),
  or read the recommendation's `location` directly.
- For scripts and ATS recipes, route to `skills/tool-map/SKILL.md`. Jev can pick
  that skill from its description; the agent runs deterministic `rg`/`find` to
  discover files. Jev itself does **not** index scripts or read recipe bodies.

## NEVER USE IT FOR

- Writing anything: cover letters, free-text "why this company", résumé bullets.
- Deciding submit. Submit is a proof gate (`skills/verify/SKILL.md`), not a probability.
- **PII.** Everything sent to Jev leaves the machine (OpenRouter → TypeSafe). Never send
  name, email, phone, address, salary, visa status, or `config/user.json` wholesale.
  Send only the **field label + option list + a policy key** ("work_auth_india"), never the value.

## CHEAPER THAN READING, NOT CHEAPER THAN KNOWING

If the answer is already in a table (`config/answers.py`, `skills/REFERENCE.md`), look it
up — 0 tokens. Jev is for the **lookup miss**, not for re-deciding what a file already says.

## WHERE IT PLUGS INTO PI

`pi-jev` registers three Pi tools. `jev-auto` uses **one extra Jev call per prompt**
to classify inactive tools and skill descriptions; `/jev auto on` is session-only
unless `PI_JEV_AUTO=1` is set at launch. `scripts/pi_jev.sh` defaults auto
routing off; enable explicitly with `PI_JEV_AUTO=1 scripts/pi_jev.sh`. A small
read-only test already found the correct skill with auto **off**: 5.42 s /
$0.000688 Pi estimate vs auto **on**: 9.72 s / $0.000720 Pi estimate,
**plus** separate Jev usage. One run is noisy; no savings are established.
Keep `tool-guard` and `auto-model` off until a larger controlled test justifies
them. Jev usage is not included in Pi's model-cost field.
