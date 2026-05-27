@echo off
rem AI worklog: start a new session
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
python "%~dp0scripts\ai_start.py" %*
