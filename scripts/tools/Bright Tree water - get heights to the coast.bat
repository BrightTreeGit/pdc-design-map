@echo off
cd /d "%~dp0"
python -m pip install -q requests
python fetch_water_to_coast.py
