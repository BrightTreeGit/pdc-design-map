@echo off
rem Builds small canopy and vegetation-structure files from the Bright Tree point clouds (2008, 2014, 2022).
rem Takes about 20-40 minutes. You can leave it running.
cd /d "%~dp0"
echo Installing the point-cloud reader (first time only)...
py -m pip install --quiet "laspy[lazrs]" numpy
py make_canopy.py bright-tree "%~dp0QLD Government\Point Clouds"
echo.
echo Tell Claude the canopy files are ready.
pause
