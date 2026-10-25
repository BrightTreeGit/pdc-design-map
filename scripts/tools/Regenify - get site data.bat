@echo off
rem Regenify (Koonyum Range, NSW): boundary, 5 m elevation, aerial, capture date and 30 years of rainfall -> Regenify\Site data
rem Uses a point inside the block from its Google Plus Code (FC7C+RM).
cd /d "%~dp0"
set SILO_EMAIL=brighttreewellness@gmail.com
py fetch_nsw_site.py regenify --pin=-28.535284,153.421493 --out "..\Regenify\Site data"
echo.
echo Tell Claude: "Regenify site data is ready".
pause
