@echo off
title DeadlineGremlin Setup
echo ========================================================
echo               👾 DeadlineGremlin Quick Setup
echo       "Because future you is tired of your excuses"
echo ========================================================
echo.
echo 1. Adding DeadlineGremlin to your Windows User PATH...
python "%~dp0taskchecker\main.py" install-path
echo.
echo 2. Enabling autostart for notifications on PC reboot...
python "%~dp0taskchecker\main.py" autostart enable
echo.
echo 3. Starting the background notification service...
python "%~dp0taskchecker\main.py" daemon start
echo.
echo ========================================================
echo Setup Complete!
echo You can now use 'task' from any Command Prompt or PowerShell!
echo.
echo Quick commands:
echo   task add "Review project" "tomorrow 5pm"
echo   task list
echo   task cheatsheet (or open CHEATSHEET.md)
echo ========================================================
pause
