@echo off
cd /d "%~dp0"
py -m pip install --quiet requests
py fetch_terrain_tiles.py --folder Annwn
pause
