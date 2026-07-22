@echo off
title TeamSpeak 3 Query Support Bot
echo ==============================================
echo   Initializing Python Environment...
echo ==============================================
python bot.py
if %errorlevel% neq 0 (
    echo.
    echo [!] Python is either not installed or not in your system environment PATH.
    echo Please make sure Python 3.x is installed correctly.
    echo.
    pause
)
