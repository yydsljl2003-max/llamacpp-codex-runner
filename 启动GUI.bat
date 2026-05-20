@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

:: 自动查找 Python
where py >nul 2>&1
if %errorlevel%==0 (
    py "Codex启动器.py"
    pause
    exit
)

where python >nul 2>&1
if %errorlevel%==0 (
    python "Codex启动器.py"
    pause
    exit
)

where python3 >nul 2>&1
if %errorlevel%==0 (
    python3 "Codex启动器.py"
    pause
    exit
)

echo 未找到 Python，请先安装 Python 并添加到 PATH
echo 下载地址：https://www.python.org/downloads/
pause