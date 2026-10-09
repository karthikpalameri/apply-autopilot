@echo off
REM run_li.bat — run the LinkedIn listed-company apply pipeline on Windows
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" apply\li_listed_apply.py
