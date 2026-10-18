@echo off
setlocal
cd /d "%~dp0"
title Torrent Downloader Pro

echo ========================================================
echo         Launching Torrent Downloader Pro...
echo ========================================================
echo.

uv run torrent-downloader

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with code %errorlevel%.
    echo Please check if 'uv' is installed and your environment is ready.
    echo.
    pause
)
