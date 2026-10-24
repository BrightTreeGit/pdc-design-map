@echo off
rem Noosa Forest Retreat: downloads every aerial photo the state holds (1950s to now) for the map history slider.
cd /d "%~dp0"
py fetch_site_history.py noosa-forest-retreat
pause
