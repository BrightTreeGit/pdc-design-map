@echo off
rem Noosa Forest Retreat TEST: stitch only every 2nd photo, to see if half the photos is enough.
rem Run this AFTER the full stitch has finished (running both at once makes each twice as slow).
rem Output lands in  Noosa Forest Retreat\Drone\odm_half\  so it does not overwrite the full run.
setlocal enabledelayedexpansion
set SITE=%~dp0..\Noosa Forest Retreat
set WORK=%SITE%\Drone\odm_half
if not exist "%WORK%\images" mkdir "%WORK%\images"
echo Copying every 2nd straight-down photo...
set /a N=0
for %%f in ("%SITE%\Drone\DJI_2026102617*_D.JPG") do (
  set /a N+=1
  set /a R=!N! %% 2
  if !R!==0 copy /y "%%f" "%WORK%\images\" >nul
)
del /q "%WORK%\images\DJI_20261026171924_0301_D.JPG" "%WORK%\images\DJI_20261026171922_0300_D.JPG" "%WORK%\images\DJI_20261026171920_0299_D.JPG" "%WORK%\images\DJI_20261026171918_0298_D.JPG" "%WORK%\images\DJI_20261026171916_0297_D.JPG" 2>nul
copy /y "%~dp0NoosaForestRetreat_boundary.geojson" "%WORK%\boundary.geojson" >nul
docker info >nul 2>&1
if errorlevel 1 (
  echo Docker Desktop is not running. Start it, wait for the whale icon to settle, then run this again.
  pause
  exit /b 1
)
docker run --rm -v "%WORK%:/datasets/code" opendronemap/odm --project-path /datasets --dsm --dem-resolution 10 --orthophoto-resolution 5 --boundary /datasets/code/boundary.geojson --auto-boundary-distance 0 --pc-quality medium --feature-quality high --skip-3dmodel
echo.
echo Done. Tell Claude "Noosa half test is ready" and I will compare it with the full run.
pause
