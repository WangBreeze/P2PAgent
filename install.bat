@echo off
REM P2P Agent 安装脚本 (Windows)

setlocal

set SCRIPT_DIR=%~dp0
set BINARY=%SCRIPT_DIR%dist\p2p-agent.exe

REM 检查可执行文件
if not exist "%BINARY%" (
    echo ❌ 未找到可执行文件，请先运行打包命令:
    echo    python build.py
    exit /b 1
)

REM 安装目录
set INSTALL_DIR=%USERPROFILE%\p2p-agent

REM 创建目录
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM 复制文件
echo 📦 安装 P2P Agent 到 %INSTALL_DIR%...
copy "%BINARY%" "%INSTALL_DIR%\p2p-agent.exe" >nul

echo.
echo ✅ 安装完成！
echo.
echo 使用方法:
echo   %INSTALL_DIR%\p2p-agent.exe --name Alice
echo   %INSTALL_DIR%\p2p-agent.exe --name Bob --connect 192.168.1.100:9000
echo.
echo 建议将 %INSTALL_DIR% 添加到 PATH 环境变量
echo.
echo 卸载方法:
echo   rmdir /s /q %INSTALL_DIR%

endlocal
