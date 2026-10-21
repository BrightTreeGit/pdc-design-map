@echo off
rem Downloads every historical aerial photo the state holds over this site, for the map history slider.
cd /d "%~dp0"
py -m pip install --quiet requests pillow
py fetch_history.py bright-tree
echo.
echo Tell Claude the history photos are ready.
pause
