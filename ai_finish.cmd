@echo off
rem AI worklog: finish session - capture diff and generate report
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
python "%~dp0scripts\ai_finish.py" %*
