@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
    py "launcher.py"
    pause
    exit
)

where python >nul 2>&1
if %errorlevel%==0 (
    python "launcher.py"
    pause
    exit
)

where python3 >nul 2>&1
if %errorlevel%==0 (
    python3 "launcher.py"
    pause
    exit
)

echo Python not found. Please install Python and add to PATH.
echo https://www.python.org/downloads/
pause