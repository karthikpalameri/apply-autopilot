#!/usr/bin/env bash
# scripts/start_mcp.sh — the ONE owner of launching the :3000 MCP server.
#
# run.sh and run_li.sh each carried their own copy of this launch, and the copies
# had already drifted: sleep 6 vs sleep 15, one passed
# CLOAK_PLAYWRIGHT_MCP_CONSOLE_FALLBACK, the other passed
# --http-session-idle-ttl-ms. Exactly the "N copies drift apart" pattern that was
# removed eleven times on the Python side.
#
# Usage:
#   scripts/start_mcp.sh              # start if not already healthy
#   scripts/start_mcp.sh --restart    # kill the port first (fresh session)
#   scripts/start_mcp.sh --ttl 30000  # long-lived session for the apply pipeline
#
# Settings that matter, all measured (see docs/QUALITY.md):
#   PLAYWRIGHT_MCP_TIMEOUT_SETTLE  upstream waits this long after EVERY action,
#                                  default 500ms. 500 -> 512ms per call,
#                                  100 -> 114ms, 0 -> 7ms. Default here: 100.
#   --cdp-enabled / 9333           ONE browser, two drivers. MCP owns it; the ctl
#                                  bridge attaches over CDP instead of launching a
#                                  second headed Chromium with a second profile
#                                  (two browsers = two states; measured 2026-11-07,
#                                  fill_report read a stale page while MCP was
#                                  elsewhere). Server side: core/page_guard.
#   profile dir                    runtime/py-session, NOT runtime/mcp-session.
#                                  Pi's own browser owns that one; sharing it means
#                                  "Browser is already in use" and every failed
#                                  call burns the full 5000ms action timeout.
set -euo pipefail
cd "$(dirname "$0")/.."

PORT=3000
PROFILE="$PWD/runtime/py-session"
SETTLE="${PLAYWRIGHT_MCP_TIMEOUT_SETTLE:-100}"
LOG="logs/mcp.out"
# macOS App Nap / Automatic Termination kills an idle, unfocused GUI browser and
# takes the session with it (log: _kLSApplicationWouldBeTerminatedByTALKey=1
# minutes before every dead page, measured 2026-11-07). Same flags as
# runtime/server.py#KEEPALIVE_ARGS — one reason, two transports.
KEEPALIVE_ARGS="--disable-backgrounding-occluded-windows,--disable-renderer-backgrounding,--disable-background-timer-throttling,--disable-features=CalculateNativeWinOcclusion,IntensiveWakeUpThrottling"
RESTART=0
TTL=""

while [ $# -gt 0 ]; do
  case "$1" in
    --restart) RESTART=1; shift ;;
    --ttl)     TTL="${2:?--ttl needs a value}"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$PROFILE" logs

healthy() { curl -sf "http://127.0.0.1:$PORT/healthz" >/dev/null 2>&1; }

if [ "$RESTART" = "1" ]; then
  pid="$(lsof -ti "tcp:$PORT" 2>/dev/null || true)"
  if [ -n "$pid" ]; then
    echo "▶ stopping existing :$PORT (pid $pid)…"
    # shellcheck disable=SC2086  # unquoted on purpose: lsof may return several pids
    kill -9 $pid 2>/dev/null || true
    sleep 2
  fi
elif healthy; then
  echo "▶ :$PORT already healthy — reusing it"
  exit 0
fi

# A stale lock left by a killed process blocks the next launch.
rm -f "$PROFILE/.cloakbrowser-mcp-profile.lock" 2>/dev/null || true

echo "▶ starting cloakbrowser-mcp (:$PORT, settle=${SETTLE}ms)…"
# shellcheck disable=SC2016  # the ${VAR:-default} strings must be literal here
env HEALTHY_URL="http://127.0.0.1:$PORT/healthz" \
    PLAYWRIGHT_MCP_TIMEOUT_SETTLE="$SETTLE" \
    PLAYWRIGHT_MCP_HEADLESS=false \
    PLAYWRIGHT_MCP_USER_DATA_DIR="$PROFILE" \
    PLAYWRIGHT_MCP_SNAPSHOT_BOXES=false \
    CLOAK_PLAYWRIGHT_MCP_CONSOLE_FALLBACK=false \
    PLAYWRIGHT_MCP_EXTRA_ARGS="$KEEPALIVE_ARGS" \
    nohup npx -y cloakbrowser-mcp@1.14.1 --transport streamable-http \
      --http-port "$PORT" ${TTL:+--http-session-idle-ttl-ms "$TTL"} \
      --cdp-enabled --cdp-port-range 9333 \
      > "$LOG" 2>&1 &

# Poll for health instead of guessing. A fixed sleep either wastes time or races.
for _ in $(seq 1 40); do
  if healthy; then
    echo "▶ :$PORT healthy"
    exit 0
  fi
  sleep 0.5
done

echo "❌ :$PORT did not become healthy in 20s — last log lines:" >&2
tail -5 "$LOG" >&2
exit 1
