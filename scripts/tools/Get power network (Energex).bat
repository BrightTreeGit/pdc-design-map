@echo off
rem Downloads the public Energex power network (poles, pillars, street lines) for the Queensland design-map sites.
cd /d "%~dp0"
py fetch_services.py
echo.
pause
