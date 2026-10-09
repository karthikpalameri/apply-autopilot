#!/usr/bin/env bash
export PYTHONUTF8=1
# track.sh — one-shot applied vs not-applied reconcile. Optional: pass --gmail to also read inbox.
# POSIX wrapper around hub.py (cross-platform). Windows: use track.bat
set -e
cd "$(dirname "$0")"
exec python3 hub.py track "$@"
