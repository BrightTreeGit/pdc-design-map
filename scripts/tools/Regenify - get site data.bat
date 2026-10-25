@echo off
rem Regenify (Koonyum Range, NSW): boundary, 5 m elevation, aerial, capture date and 30 years of rainfall -> Regenify\Site data
cd /d "%~dp0"
set SILO_EMAIL=brighttreewellness@gmail.com
py fetch_nsw_site.py regenify --address "1 BOOGAREM ROAD KOONYUM RANGE" --out "..\Regenify\Site data"
if errorlevel 1 (
  echo.
  echo If the address was not found, right-click the block in Google Maps, copy the two numbers, and tell Claude.
)
echo.
echo Tell Claude: "Regenify site data is ready".
pause
