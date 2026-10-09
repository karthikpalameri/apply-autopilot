@echo off
REM track.bat — applied vs not-applied report on Windows
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
python hub.py track %*
