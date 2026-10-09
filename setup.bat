@echo off
REM setup.bat — run the interactive setup wizard on Windows
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
python setup.py
