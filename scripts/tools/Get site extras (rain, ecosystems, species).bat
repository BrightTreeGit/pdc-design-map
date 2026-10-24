@echo off
rem Every site: SILO daily rain and full weather (ETo), soil grid, design rainfall (IFD), surface geology, bushfire and vegetation-rule mapping,
rem Queensland regional ecosystems, Atlas of Living Australia species, and a check whether the LiDAR server is back. Safe to re-run: fetches only what is missing.
cd /d "%~dp0"
py fetch_site_extras.py
echo.
pause
