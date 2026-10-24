@echo off
rem Daily SILO rain for every site, Queensland regional ecosystems, Atlas of Living Australia species, and a check whether the LiDAR server is back.
cd /d "%~dp0"
py -m pip install --quiet requests
py fetch_site_extras.py
echo.
pause
