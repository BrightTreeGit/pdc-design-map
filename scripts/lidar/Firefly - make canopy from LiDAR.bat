@echo off
rem Firefly Farm (Nimbin NSW): ground and canopy grids from the ELVIS point clouds (Lismore 2017 and Richmond River 2023, kept apart by year).
rem Reads the zips in Nimbin\Lidar-survey data. Takes roughly 15-45 minutes. You can leave it running.
cd /d "%~dp0"
echo Installing the point-cloud reader (first time only)...
py -m pip install --quiet "laspy[lazrs]" numpy
py make_canopy.py nimbin "%~dp0..\Nimbin\Lidar-survey data"
echo.
echo Tell Claude the Firefly canopy files are ready.
pause
