@echo off
REM run.bat — start the browser stack on Windows (server.py :9000 + cloakbrowser-mcp :3000)
cd /d "%~dp0"
python hub.py start
