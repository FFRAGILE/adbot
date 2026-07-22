@echo off
title TeamSpeak Bot Launcher
echo Checking dependencies...

:: بررسی اینکه آیا کتابخانه نصب شده است یا خیر، اگر نبود خودکار نصب می‌کند
if not exist node_modules (
    echo Installing ts3-nodejs-library...
    npm install ts3-nodejs-library
)

echo.
echo Starting TeamSpeak Bot...
echo.
node bot.js
pause
