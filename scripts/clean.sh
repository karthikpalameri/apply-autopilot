#!/usr/bin/env bash
# scripts/clean.sh — retention for local artifacts. Nothing here is source.
#
#   ./scripts/clean.sh            show what would be removed (safe default)
#   ./scripts/clean.sh --apply    actually remove
#   ./scripts/clean.sh --profile  ALSO remove runtime/mcp-session (logs you out of
#                                 LinkedIn/Naukri — you must log in again by hand)
#
# Why: logs/ has no rotation policy (16 files / 2.2M) and runtime/ holds a 1.7G
# Chromium profile, but the profile is NOT safe to delete blindly — it carries the
# authenticated LinkedIn session the apply recipes depend on.
set -euo pipefail
cd "$(dirname "$0")/.."

APPLY=0; PROFILE=0
for a in "$@"; do
  case "$a" in
    --apply)   APPLY=1 ;;
    --profile) PROFILE=1 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown arg: $a" >&2; exit 2 ;;
  esac
done

human() { du -sh "$1" 2>/dev/null | cut -f1; }

# Always-safe targets: regenerable per-run artifacts.
TARGETS=(
  "logs/*.png"          # proof screenshots (keep if you need evidence)
  "logs/*.out"
  "logs/app.log.*"      # rotated log copies (live app.log is kept)
  "temp/*"
  "scratch/li/*"        # raw HTML scrapes, one session old
  "scratch/li2/*"
  "scratch/li3/*"
  "scratch/preflight/*"
  "scratch/tmp/old/*"
  "**/__pycache__"
)

echo "== removable =="
for t in "${TARGETS[@]}"; do
  n=$(find "$t" -type f 2>/dev/null | wc -l | tr -d ' ') || n=0
  [ "$n" = "0" ] && continue
  sz=$(du -ch "$t" 2>/dev/null | tail -1 | cut -f1) || sz="?"
  echo "  ${sz:-?}  ${n} files  $t"
  if [ "$APPLY" = "1" ]; then rm -rf "$t" 2>/dev/null || true; fi
done

echo
echo "== kept on purpose =="
echo "  $(human runtime/mcp-session 2>/dev/null || echo 0)  runtime/mcp-session  (browser profile = live LinkedIn login)"
echo "  $(human logs 2>/dev/null || echo 0)  logs/                (app.log is the audit trail)"
echo "  $(human data  2>/dev/null || echo 0)  data/                (applied_ledger.jsonl = dedupe authority)"

if [ "$PROFILE" = "1" ]; then
  echo
  echo "!! removing runtime/mcp-session — you will need to log in to LinkedIn again"
  [ "$APPLY" = "1" ] && rm -rf runtime/mcp-session || echo "   (dry run, pass --apply to remove)"
fi

[ "$APPLY" = "0" ] && echo && echo "dry run — re-run with --apply to remove"
exit 0
