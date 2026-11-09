---
name: pi-setup
description: Set up Pi and pi-jev after cloning apply-autopilot on a new Mac. Covers packages, project trust, skills, browser tool loadout, OpenRouter key, zsh or bash shell, verification and cost checks.
parent: skills/SKILL.md
---

# PI SETUP — one canonical walkthrough

Follow **`docs/INSTALL.md#pi-jev--project-skills`** for the ordered steps and
copyable commands. Do not copy secrets into this file, shell history, agent
messages or repository config. Never edit `~/.pi/agent/settings.json` without
checking existing user packages first.

Use `scripts/pi_jev.sh` (repo root) for Jev tools with automatic routing off;
`PI_JEV_AUTO=1 scripts/pi_jev.sh` explicitly enables it after measurement.
Plain `pi` remains the baseline for comparison. Verify the final skill count and
Jev status in a **new session**, not this session's old tool loadout. For helper
selection use `skills/tool-map/SKILL.md`; for Jev's PII/decision rules use
`skills/jev/SKILL.md`. This skill is a pointer, not a second installation guide.
