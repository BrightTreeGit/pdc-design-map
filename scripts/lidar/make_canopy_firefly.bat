@echo off
rem Firefly Farm (Nimbin NSW): builds canopy and ground grids from the ELVIS LiDAR point clouds.
rem First put the downloaded ELVIS .zip files (point clouds, not just the DEM) in a folder called
rem "Firefly Point Clouds" next to this file. Takes roughly 5-30 minutes.
cd /d "%~dp0"
echo Installing the point-cloud reader (first time only)...
py -m pip install --quiet "laspy[lazrs]" numpy
py make_canopy.py nimbin "%~dp0Firefly Point Clouds"
echo.
echo Tell Claude the Firefly canopy files are ready.
pause
