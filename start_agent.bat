@echo off
REM P2P Agent 启动脚本 (Windows)

cd /d "%~dp0"

REM 检查虚拟环境
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM 检查参数
if "%~1"=="" (
    echo 用法: start_agent.bat ^<Agent名称^> [端口] [连接地址]
    echo.
    echo 示例:
    echo   start_agent.bat Alice
    echo   start_agent.bat Alice 9001
    echo   start_agent.bat Bob 9002 192.168.1.100:9000
    exit /b 1
)

set NAME=%~1
set PORT=%~2
set CONNECT=%~3

if "%PORT%"=="" set PORT=9000

echo 🚀 启动 P2P Agent: %NAME%
echo    端口: %PORT%
if not "%CONNECT%"=="" (
    echo    连接到: %CONNECT%
)
echo.

REM 启动
if "%CONNECT%"=="" (
    python p2p_agent.py --name %NAME% --port %PORT%
) else (
    python p2p_agent.py --name %NAME% --port %PORT% --connect %CONNECT% --no-discover
)
