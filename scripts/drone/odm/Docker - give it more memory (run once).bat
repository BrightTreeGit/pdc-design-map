@echo off
rem One-off: let Docker use more of this computer's memory (Windows gives it only half by default).
rem OpenDroneMap needs about 12-16 GB for the Noosa photos; this laptop has 32 GB. Run this once, after installing Docker Desktop.
(
echo [wsl2]
echo memory=20GB
echo swap=16GB
) > "%USERPROFILE%\.wslconfig"
wsl --shutdown
echo.
echo Done. Docker can now use up to 20 GB of memory plus 16 GB of swap.
echo This leaves 12 GB for Windows.
echo Start Docker Desktop again (it closes when WSL restarts), then run the stitch.
pause
