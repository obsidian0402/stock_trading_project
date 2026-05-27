@echo off
rem AI worklog: record Goal/Prompt into the latest session prompt.md
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
python "%~dp0scripts\ai_record.py" %*
