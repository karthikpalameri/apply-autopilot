#!/usr/bin/env bash
# scripts/check.sh — the ONE gate. Runs every checker the repo has, per concern.
#
#   .py        ruff          DRY (unused/duplicate/redefinition), KISS (complexity),
#                            LOGS (try/except/pass) — config in pyproject.toml
#   .py        ty            type errors: None-unsafe calls, bad payload.py usage,
#                            wrong overloads. Catches what ruff cannot see.
#   .py        vulture       dead code: unused vars/imports, unsatisfiable branches
#   .py        jscpd         duplication + single-owner boundaries — .jscpd.json
#   .venv      pip-audit     known CVEs in installed dependencies
#   repo       lint_upload   a click that would open a native file picker
#   repo       lint_identity one source for PII; cache must match config/user.json
#   repo       lint_page_guard  no ctl-status health gates, page timeouts <= 10s
#   .sh        shellcheck    quoting, word-splitting, unused vars
#   .md        markdownlint  structure, code fences, bare URLs — .markdownlint-cli2.jsonc
#   .js/.mjs   (none)        the only JS here is vendored: runtime/extensions/buster
#
# Everything runs through `uvx` / `npx`, so there is nothing to install and no
# version to pin in requirements: uvx fetches the tool on demand.
#
# Usage:
#   scripts/check.sh          # gate; non-zero exit on any finding
#   scripts/check.sh --fix    # apply the safe autofixes first
#   scripts/check.sh --install  # install the pre-commit hook (once per clone)
#
# Why these and not more: docs/QUALITY.md records what was measured and rejected.
# A gate nobody can pass is a gate everybody ignores — an unfiltered markdownlint
# run reported 3243 findings here, of which ~99% were line-length and table-padding
# preferences on documents that are deliberately long single lines.
#
# NOTE on jscpd: its config MUST stay at .jscpd.json in the repo root. Paths
# resolve from the config file's folder, so a copy kept elsewhere protects no
# code and silently exits 0 — a green gate that checks nothing.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

FIX=0
[ "${1:-}" = "--fix" ] && FIX=1

if [ "${1:-}" = "--install" ]; then
  cd "$(dirname "$0")/.." || exit 1
  chmod +x .githooks/pre-commit
  git config core.hooksPath .githooks
  echo "pre-commit hook installed (core.hooksPath=.githooks)"
  echo "It runs scripts/check.sh and blocks the commit on any finding."
  echo "Skip once with: git commit --no-verify"
  exit 0
fi

# tests/ is excluded from ty: test code monkeypatches (os.path.relpath, spec.loader)
# and reads loosely-typed dicts by design — a static type checker cannot verify it.
PY_EXCLUDES=(--exclude third_party --exclude archive --exclude temp
             --exclude scratch --exclude .venv --exclude tests)

fail=0
run() {  # run <label> <command...>
  local label="$1"; shift
  printf '▶ %-12s ' "$label"
  if out="$("$@" 2>&1)"; then
    echo "✅ clean"
  else
    echo "❌ findings"
    echo "$out" | sed 's/^/    /' | head -40
    fail=1
  fi
}

echo "GATE  $(date -u '+%Y-%m-%dT%H:%M:%SZ')"

if [ "$FIX" = "1" ]; then
  echo "▶ applying safe autofixes…"
  uvx ruff check --fix --quiet . >/dev/null 2>&1 || true
fi

# --- Python source ---
run "python"   uvx ruff check . --output-format concise
run "types"    uvx ty check "${PY_EXCLUDES[@]}"
run "dead"     uvx vulture core/ find/ apply/ config/ runtime/server.py --min-confidence 80

# --- duplication + architecture ---
# Baseline: known clones pass, NEW ones fail. Refresh only after accepting one:
#   uvx jscpd . --baseline .jscpd-baseline.json --update-baseline
run "dupes"    uvx jscpd . --baseline .jscpd-baseline.json --fail-on-new-clones

# --- dependencies ---
run "deps"     uvx pip-audit --path .venv/lib/python3.13/site-packages

# --- repo-local guards ---
run "upload"   .venv/bin/python core/lint_upload.py
run "identity" .venv/bin/python core/lint_identity.py
run "pageguard" .venv/bin/python core/lint_page_guard.py

# --- other file types ---
run "shell"    uvx --from shellcheck-py shellcheck run.sh run_li.sh track.sh scripts/*.sh
run "markdown" npx -y markdownlint-cli2

# --- layering: apply/ -> find/ -> core/ must stay one-way ---
printf '▶ %-12s ' "layering"
if out="$(grep -rn '^from find\|^from apply' core/ 2>/dev/null)" && [ -n "$out" ]; then
  echo "❌ findings"
  echo "$out" | sed 's/^/    /' | head -20
  echo "    core/ must not import find/ or apply/"
  fail=1
else
  echo "✅ clean"
fi

echo
[ "$fail" = "0" ] && echo "ALL GATES PASS" || echo "GATE FAILED"
exit "$fail"
