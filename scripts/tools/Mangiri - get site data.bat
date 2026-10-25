@echo off
rem Mangiri (Mongarlowe, NSW): boundary, 5 m elevation, aerial, capture date and 30 years of rainfall -> Mangiri\Site data
rem The NSW register has no match for the street address, so this uses a point inside the block (from its Google Plus Code).
cd /d "%~dp0"
set SILO_EMAIL=brighttreewellness@gmail.com
py fetch_nsw_site.py mangiri --pin=-35.430938,149.939188 --out "..\Mangiri\Site data"
echo.
echo Tell Claude: "Mangiri site data is ready".
pause
