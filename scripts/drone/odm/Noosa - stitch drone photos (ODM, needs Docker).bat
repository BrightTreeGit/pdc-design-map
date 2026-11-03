@echo off
rem Noosa Forest Retreat: stitch the 26 Oct 2026 drone photos into an orthophoto and surface model with OpenDroneMap.
rem Needs Docker Desktop running. Uses the NVIDIA GPU if the drivers and Docker's GPU support are in place; falls back to CPU.
rem Output lands in  Noosa Forest Retreat\Drone\odm\  (odm_orthophoto\odm_orthophoto.tif and odm_dem\dsm.tif are the two files Claude needs).
setlocal
set SITE=%~dp0..\Noosa Forest Retreat
set WORK=%SITE%\Drone\odm
if not exist "%WORK%\images" mkdir "%WORK%\images"
echo Copying the straight-down photos into the work folder (the five tilted ones at the end and the videos are left out)...
for %%f in ("%SITE%\Drone\DJI_2026102617*_D.JPG") do (
  copy /y "%%f" "%WORK%\images\" >nul
)
del /q "%WORK%\images\DJI_20261026171924_0301_D.JPG" "%WORK%\images\DJI_20261026171922_0300_D.JPG" "%WORK%\images\DJI_20261026171920_0299_D.JPG" "%WORK%\images\DJI_20261026171918_0298_D.JPG" "%WORK%\images\DJI_20261026171916_0297_D.JPG" 2>nul
copy /y "%~dp0NoosaForestRetreat_boundary.geojson" "%WORK%\boundary.geojson" >nul
docker info >nul 2>&1
if errorlevel 1 (
  echo.
  echo Docker Desktop is not running. Start it, wait for the whale icon to settle, then run this again.
  pause
  exit /b 1
)
echo.
echo Trying the GPU build first (RTX cards). If it refuses, the CPU build runs instead; both give the same result.
docker run --rm --gpus all -v "%WORK%:/datasets/code" opendronemap/odm:gpu --project-path /datasets --dsm --dem-resolution 10 --orthophoto-resolution 5 --boundary /datasets/code/boundary.geojson --auto-boundary-distance 0 --pc-quality medium --feature-quality high --skip-3dmodel
if errorlevel 1 (
  echo GPU run did not work; running on the processor instead (slower).
  docker run --rm -v "%WORK%:/datasets/code" opendronemap/odm --project-path /datasets --dsm --dem-resolution 10 --orthophoto-resolution 5 --boundary /datasets/code/boundary.geojson --auto-boundary-distance 0 --pc-quality medium --feature-quality high --skip-3dmodel
)
echo.
echo Done. Tell Claude "Noosa orthophoto is ready". The files are in:
echo   %WORK%\odm_orthophoto\odm_orthophoto.tif
echo   %WORK%\odm_dem\dsm.tif
pause
