#!/usr/bin/env bash
export PYTHONUTF8=1
# run_li.sh — restart the MCP server (fresh session) + run the LinkedIn listed-company apply pipeline.
# POSIX only. Windows: use run_li.bat
set -e
cd "$(dirname "$0")"
CLOAKBROWSER_MCP_VERSION="${CLOAKBROWSER_MCP_VERSION:-latest}"
rm -f runtime/mcp-session/.cloakbrowser-mcp-profile.lock 2>/dev/null || true
CLOAK_VIEWPORT="${CLOAK_VIEWPORT:-1280x800}"

kill -9 $(lsof -ti tcp:3000) 2>/dev/null || true
sleep 2
nohup env PLAYWRIGHT_MCP_HEADLESS=false PLAYWRIGHT_MCP_USER_DATA_DIR="$PWD/runtime/mcp-session" \
  npx -y "cloakbrowser-mcp@${CLOAKBROWSER_MCP_VERSION}" --transport streamable-http --http-port 3000 \
  --http-session-idle-ttl-ms 30000 > logs/mcp.out 2>&1 &
sleep 15

PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
exec "$PY" apply/li_listed_apply.py
