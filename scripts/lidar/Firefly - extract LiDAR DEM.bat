@echo off
rem Firefly Farm: pulls the elevation-model files (not the point clouds) out of the ELVIS zips into "DEM only".
cd /d "%~dp0"
py extract_dem.py "%~dp0..\Nimbin\Lidar-survey data"
echo.
echo Tell Claude the Firefly DEM files are ready.
pause
