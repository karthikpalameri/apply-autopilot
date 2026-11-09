#!/usr/bin/env bash
# scripts/setup_pi.sh — ONE owner of installing Pi + its packages (pi.dev quickstart).
#
# Machine-only steps: npm globals + pi package installs. The human steps (project
# trust, OpenRouter secret, mcp-adapter.json, verification) stay in
# docs/INSTALL.md#pi-jev--project-skills because they need a real terminal and
# echo-less input — this script never handles secrets.
#
# DRY: the package list lives HERE. docs/INSTALL.md points at this script instead
# of repeating the `npm install` / `pi install` commands (that duplication had
# already drifted). Idempotent: skips anything already installed — safe to re-run.
#
# Node minimum is 22.19 (Pi requirement, docs/INSTALL.md); npm globals are the
# user-level installs that `pi` itself does not manage.
set -euo pipefail
cd "$(dirname "$0")/.."

NEED_NODE=22

check_node() {
  if ! command -v node >/dev/null 2>&1; then
    echo "node not found — install with: brew install node" >&2
    exit 2
  fi
  local maj
  maj="$(node -p 'process.versions.node.split(".")[0]')"
  if [ "$maj" -lt "$NEED_NODE" ]; then
    echo "node $maj < $NEED_NODE — upgrade before installing Pi" >&2
    exit 2
  fi
}

# npm_global <installed-name> <install-spec...> — install only if absent
npm_global() {
  local name="$1"; shift
  if npm ls -g --depth=0 "$name" >/dev/null 2>&1; then
    echo "✓ $name already installed"
  else
    echo "▶ installing $name …"
    npm install -g "$@"
  fi
}

# pi_pkg <install-spec> <label> — install only if absent (pi list shows `npm:<label>`)
pi_pkg() {
  local spec="$1" label="$2"
  if pi list 2>/dev/null | grep -q "npm:$label"; then
    echo "✓ $label already installed"
  else
    echo "▶ installing $label …"
    pi install "$spec"
  fi
}

check_node

npm_global @earendil-works/pi-coding-agent @earendil-works/pi-coding-agent --ignore-scripts
npm_global @devinwangd/cloak-browser-mcp @devinwangd/cloak-browser-mcp

pi_pkg npm:pi-mcp-adapter pi-mcp-adapter
pi_pkg npm:pi-jev         pi-jev
pi_pkg npm:context-mode   context-mode   # optional: compact large tool outputs
pi_pkg npm:pi-web-access  pi-web-access  # optional: web research

echo
echo "✓ Pi packages ready — pi $(pi --version)"
echo "Next (human steps — docs/INSTALL.md#pi-jev--project-skills):"
echo "  1. configure ~/.pi/agent/mcp-adapter.json (step 3c.2)"
echo "  2. store the OpenRouter key privately        (step 3c.3)"
echo "  3. /trust this clone, then scripts/pi_jev.sh (step 3c.4-5)"
