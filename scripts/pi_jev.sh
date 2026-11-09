#!/usr/bin/env bash
# Start a fresh Pi process with Jev tools ready; auto routing is opt-in.
# Keep API keys in the
# environment or ~/.pi/agent/secrets/openrouter_api_key; never source repo secrets.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v pi >/dev/null 2>&1; then
  echo "Pi not installed. Follow docs/INSTALL.md#pi-jev--project-skills" >&2
  exit 2
fi
if [ -z "${OPENROUTER_API_KEY:-}" ] && [ ! -s "$HOME/.pi/agent/secrets/openrouter_api_key" ]; then
  echo "OpenRouter key missing. Follow docs/INSTALL.md#pi-jev--project-skills (no key values in shell history)." >&2
  exit 2
fi

export PI_JEV_MODEL="${PI_JEV_MODEL:-typesafe/jev-1.13}"
export PI_JEV_AUTO="${PI_JEV_AUTO:-0}"
export PI_JEV_THINKING="${PI_JEV_THINKING:-0}"
export PI_JEV_COMPACT="${PI_JEV_COMPACT:-0}"
exec pi "$@"
