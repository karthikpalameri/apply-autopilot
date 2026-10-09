@echo off
REM track.bat — applied vs not-applied report on Windows
cd /d "%~dp0"
python hub.py track %*
