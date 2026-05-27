@echo off
rem AI worklog: review and git commit
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
python "%~dp0scripts\ai_commit.py" %*
