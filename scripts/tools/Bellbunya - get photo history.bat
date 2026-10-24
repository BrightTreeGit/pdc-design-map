@echo off
rem Bellbunya: downloads every aerial photo the state holds (1950s to now) for the map history slider.
cd /d "%~dp0"
py fetch_site_history.py bellbunya
pause
