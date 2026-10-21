@echo off
rem Downloads the Bright Tree aerial photo, lined up with the design map.
cd /d "%~dp0"
py fetch_aerial.py bright-tree
echo.
echo Done. Tell Claude the aerial photo is ready.
pause
