@echo off
cd /d "%~dp0"
echo Downloading NSW scanned aerial photos (about 120 MB)...
py get_nsw_scans.py %*
pause
