@echo off
cd /d "%~dp0"
python "%~dp0linewinnow.py" --gui
if errorlevel 1 pause
