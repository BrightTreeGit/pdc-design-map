@echo off
rem Run this once on a new computer (or after a Python update). It installs the three packages every tool here uses.
cd /d "%~dp0"
py --version || (echo Python is not installed. Get it from python.org, tick "Add to PATH", then run this again. & pause & exit /b 1)
py -m pip install --quiet --disable-pip-version-check --upgrade requests pillow numpy
echo.
echo Done. The other files in this folder can now run without installing anything.
pause
