@echo off
rem Noosa Forest Retreat: FULL overnight stitch of all 270 straight-down drone photos (26 Oct 2026) with OpenDroneMap.
rem One click: gives Docker 20 GB of this laptop's 32 GB, starts Docker Desktop if needed, keeps the laptop
rem awake until the stitch finishes, and writes a log Claude can read: Noosa Forest Retreat\Drone\odm\run_log.txt
rem Same settings as the half-photo test, so the two can be compared. Takes about 2-3 hours.
setlocal
set SITE=%~dp0..\Noosa Forest Retreat
set WORK=%SITE%\Drone\odm
if not exist "%WORK%\images" mkdir "%WORK%\images"
echo.
echo  Noosa overnight stitch. Leave the laptop plugged in with the lid OPEN (closing the lid can still sleep it).
echo.

rem ---- 1. Docker memory: 20 GB (rewritten only if it is set to something else)
findstr /c:"memory=20GB" "%USERPROFILE%\.wslconfig" >nul 2>&1
if not errorlevel 1 goto memok
echo Giving Docker 20 GB of memory (Docker Desktop will restart)...
> "%USERPROFILE%\.wslconfig" echo [wsl2]
>> "%USERPROFILE%\.wslconfig" echo memory=20GB
>> "%USERPROFILE%\.wslconfig" echo swap=16GB
taskkill /im "Docker Desktop.exe" /f >nul 2>&1
wsl --shutdown
timeout /t 10 /nobreak >nul
:memok

rem ---- 2. Start Docker Desktop if it is not running, then wait for it (up to 5 minutes)
docker info >nul 2>&1
if not errorlevel 1 goto dockerok
echo Starting Docker Desktop...
start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
set /a T=0
:waitdocker
timeout /t 5 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto dockerok
set /a T+=5
if %T% GEQ 300 goto dockerfail
goto waitdocker
:dockerfail
echo.
echo Docker did not start within 5 minutes. Open Docker Desktop yourself, wait for the whale icon to settle, then run this again.
pause
exit /b 1
:dockerok
echo Docker is running.

rem ---- 3. Photos: all straight-down photos except the 5 tilted ones at the end (already-copied ones are skipped)
echo Copying the photos...
for %%f in ("%SITE%\Drone\DJI_2026102617*_D.JPG") do if not exist "%WORK%\images\%%~nxf" copy /y "%%f" "%WORK%\images\" >nul
del /q "%WORK%\images\DJI_20261026171924_0301_D.JPG" "%WORK%\images\DJI_20261026171922_0300_D.JPG" "%WORK%\images\DJI_20261026171920_0299_D.JPG" "%WORK%\images\DJI_20261026171918_0298_D.JPG" "%WORK%\images\DJI_20261026171916_0297_D.JPG" 2>nul
copy /y "%~dp0NoosaForestRetreat_boundary.geojson" "%WORK%\boundary.geojson" >nul

rem ---- 4. Stitch (processor build; this laptop has no NVIDIA card) while keeping the laptop awake
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0noosa_overnight.ps1" -Work "%WORK%"
echo.
echo Finished. Tell Claude "Noosa orthophoto is ready". The files are in:
echo   %WORK%\odm_orthophoto\odm_orthophoto.tif
echo   %WORK%\odm_dem\dsm.tif
pause
