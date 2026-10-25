@echo off
rem Mangiri (Mongarlowe, NSW): boundary, 5 m elevation, aerial, capture date and 30 years of rainfall -> Mangiri\Site data
cd /d "%~dp0"
set SILO_EMAIL=brighttreewellness@gmail.com
py fetch_nsw_site.py mangiri --address "444 NORTHANGERA ROAD MONGARLOWE" --out "..\Mangiri\Site data"
if errorlevel 1 (
  echo.
  echo If the address was not found, right-click the block in Google Maps, copy the two numbers, and tell Claude.
)
echo.
echo Tell Claude: "Mangiri site data is ready".
pause
