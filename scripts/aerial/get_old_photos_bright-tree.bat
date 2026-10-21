@echo off
rem Downloads the best historical aerial photo for every year over this site.
cd /d "%~dp0"
py -m pip install --quiet --disable-pip-version-check requests
py fetch_old_photos.py bright-tree
pause
