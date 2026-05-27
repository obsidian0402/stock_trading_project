@echo off
rem Run the PowerShell PATH installer with a one-shot policy bypass.
rem No permanent change to the system-wide execution policy.
rem
rem Usage:
rem   install_ai_path             - add project root to user PATH
rem   install_ai_path -Remove     - remove it
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_ai_path.ps1" %*
