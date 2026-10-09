#!/usr/bin/env bash
# run.sh — start the browser stack (ctl :9000 + cloakbrowser-mcp :3000) then health-check.
# POSIX wrapper around hub.py (the cross-platform entry point). Windows: use run.bat
set -e
cd "$(dirname "$0")"
exec python3 hub.py start
