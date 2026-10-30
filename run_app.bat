@echo off
title Schema-Validated YANG-Push Telemetry Pipeline
echo ========================================================
echo   Schema-Validated YANG-Push Telemetry Pipeline
echo ========================================================
echo Starting Python Backend Simulation Server on http://localhost:8080...
start "" "http://localhost:8080"
python server.py
pause
