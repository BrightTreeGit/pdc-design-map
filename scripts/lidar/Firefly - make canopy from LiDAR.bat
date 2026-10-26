@echo off
rem Firefly Farm (Nimbin NSW): builds ground and canopy grids from the ELVIS LiDAR point clouds.
rem Put the downloaded ELVIS point-cloud .zip files in:  Firefly Farm\Lidar-survey data
rem Takes roughly 5-30 minutes. You can leave it running.
cd /d "%~dp0"
echo Installing the point-cloud reader (first time only)...
py -m pip install --quiet "laspy[lazrs]" numpy
py make_canopy.py nimbin "%~dp0..\Firefly Farm\Lidar-survey data"
echo.
echo Tell Claude the Firefly canopy files are ready.
pause
