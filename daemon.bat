@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

REM GitHub Sentinel Daemon Control Script for Windows
REM 设置UTF-8编码以正确显示中文

set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%src\daemon_process.py
set LOG_DIR=%SCRIPT_DIR%logs
set DAEMON_LOG=%LOG_DIR%\daemon.log

REM 检查Python脚本是否存在
if not exist "%PYTHON_SCRIPT%" (
    echo [ERROR] Daemon script not found: %PYTHON_SCRIPT%
    exit /b 1
)

REM 解析命令行参数
set ACTION=%1
if "%ACTION%"=="" (
    echo Usage: daemon.bat [start^|stop^|restart^|status]
    echo.
    echo Commands:
    echo   start   - Start the daemon process
    echo   stop    - Stop the daemon process
    echo   restart - Restart the daemon process
    echo   status  - Show daemon status and recent logs
    exit /b 1
)

REM 执行对应的操作
if "%ACTION%"=="start" goto start_daemon
if "%ACTION%"=="stop" goto stop_daemon
if "%ACTION%"=="restart" goto restart_daemon
if "%ACTION%"=="status" goto show_status
echo [ERROR] Unknown action: %ACTION%
exit /b 1

:start_daemon
echo [INFO] Starting GitHub Sentinel daemon...
python "%PYTHON_SCRIPT%" start
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Daemon started successfully
) else (
    echo [ERROR] Failed to start daemon
    exit /b 1
)
goto end

:stop_daemon
echo [INFO] Stopping GitHub Sentinel daemon...
python "%PYTHON_SCRIPT%" stop
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Daemon stopped successfully
) else (
    echo [ERROR] Failed to stop daemon
    exit /b 1
)
goto end

:restart_daemon
echo [INFO] Restarting GitHub Sentinel daemon...
python "%PYTHON_SCRIPT%" restart
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Daemon restarted successfully
) else (
    echo [ERROR] Failed to restart daemon
    exit /b 1
)
goto end

:show_status
echo [INFO] GitHub Sentinel Daemon Status
echo =====================================
python "%PYTHON_SCRIPT%" status
echo.

REM 显示最近的日志（解决中文乱码问题）
if exist "%DAEMON_LOG%" (
    echo [INFO] Last 10 lines of log:
    echo -------------------------------------
    REM 使用PowerShell读取UTF-8编码的日志文件，避免中文乱码
    powershell -Command "& {Get-Content -Path '%DAEMON_LOG%' -Encoding UTF8 -Tail 10 | ForEach-Object {Write-Host $_}}"
) else (
    echo [INFO] Daemon log file not found: %DAEMON_LOG%
)
goto end

:end
endlocal
