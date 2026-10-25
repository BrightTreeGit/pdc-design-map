@echo off
rem Mangiri: the neighbouring southern lot (register "446 Northangera Road", property id 468883), to check whether the buildings sit on it.
cd /d "%~dp0"
set SILO_EMAIL=brighttreewellness@gmail.com
py fetch_nsw_site.py mangiri --propid 468883 --out "..\Mangiri\Site data lot 2"
echo.
echo Tell Claude: "Mangiri lot 2 is ready".
pause
