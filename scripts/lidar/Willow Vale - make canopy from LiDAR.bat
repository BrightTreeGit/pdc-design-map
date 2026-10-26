@echo off
rem Willow Vale (Bowman NSW): builds ground and canopy grids from the ELVIS LiDAR point clouds.
rem Put the downloaded ELVIS point-cloud .zip files in:  Willow Vale\Lidar-survey data
cd /d "%~dp0"
echo Installing the point-cloud reader (first time only)...
py -m pip install --quiet "laspy[lazrs]" numpy
py make_canopy.py willow-vale "%~dp0..\Willow Vale\Lidar-survey data"
echo.
echo Tell Claude the Willow Vale canopy files are ready.
pause
