@echo off
rem Lists every pre-1994 historical aerial photo frame over this site.
cd /d "%~dp0"
py -m pip install --quiet requests
py find_old_photos.py bright-tree
echo.
echo Tell Claude the old photo list is ready.
pause
