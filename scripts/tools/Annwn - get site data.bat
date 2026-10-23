@echo off
cd /d "%~dp0"
py -m pip install --quiet requests pillow
py fetch_qld_site.py annwn --folder Annwn --address "26 CHURCHILL STREET CAPALABA"
pause
