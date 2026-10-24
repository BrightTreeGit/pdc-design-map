@echo off
rem Every site: seasonal climate drivers (SOI, ENSO, Nino 3.4), the Bureau's long-range outlook text and a 10-day forecast at each block.
rem Run once a month. Overwrites outlook.json and adds one line to outlook_history.jsonl so forecasts can be scored later.
cd /d "%~dp0"
py fetch_outlook.py
echo.
pause
