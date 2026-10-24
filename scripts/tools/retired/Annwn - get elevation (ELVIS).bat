@echo off
cd /d "%~dp0"
py -m pip install --quiet requests
py fetch_elvis.py --folder Annwn
pause
