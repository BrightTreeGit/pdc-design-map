@echo off
rem NSW site pack for NAC: boundary, 5 m elevation, aerial plus a close-up aerial, capture date and rainfall.
cd /d "%~dp0"
set SILO_EMAIL=brighttreewellness@gmail.com
py -m pip install --quiet requests pillow
py fetch_nsw_site.py nac --address "142 COVE BOULEVARD NORTH ARM COVE"
echo.
echo Tell Claude the NAC pack is ready.
pause
