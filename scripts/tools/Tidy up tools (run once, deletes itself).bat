@echo off
rem One-off clean-up (24 Oct 2026): removes the two retired Annwn elevation tools, the old Python cache, and then this file.
cd /d "%~dp0"
del /q "Annwn - get elevation (ELVIS).bat" 2>nul
del /q "fetch_elvis.py" 2>nul
del /q "Annwn - get placeholder elevation.bat" 2>nul
del /q "fetch_terrain_tiles.py" 2>nul
rmdir /s /q "__pycache__" 2>nul
echo Removed the retired ELVIS and placeholder tools and the Python cache.
echo.
echo This window will close in a moment; the tidy-up file deletes itself.
timeout /t 4 >nul
(goto) 2>nul & del "%~f0"
