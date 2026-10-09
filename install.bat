@echo off
REM install.bat — install all dependencies on Windows
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
python hub.py install
