@echo off
cd /d "%~dp0"
py -m pip install --quiet --disable-pip-version-check requests
py fetch_old_wide.py
pause
