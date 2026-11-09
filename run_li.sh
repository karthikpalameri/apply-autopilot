#!/usr/bin/env bash
export PYTHONUTF8=1
# run_li.sh — restart the MCP server with a fresh session, then run the LinkedIn
# listed-company apply pipeline.
#
# The launch itself lives in scripts/start_mcp.sh (healthz polling + profile-collision
# fix). Note the longer --ttl: the apply pipeline has gaps of dozens of seconds
# between tool calls, and the default idle TTL would drop the session mid-run.
# Windows: use run_li.bat
set -euo pipefail
cd "$(dirname "$0")"

scripts/start_mcp.sh --restart --ttl 30000

PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
exec "$PY" apply/li_listed_apply.py
