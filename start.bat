@echo off
title CareerOS Launcher
cd /d "%~dp0"

echo ==========================================================
echo               Starting CareerOS Job Tracker               
echo ==========================================================
echo.
echo Launching Docker containers...
docker-compose -f docker/docker-compose.yml up -d

echo.
echo Checking service status...
docker-compose -f docker/docker-compose.yml ps

echo.
echo ==========================================================
echo Success! CareerOS is running.
echo Access the dashboard at: http://localhost:8000/dashboard.html
echo ==========================================================
echo.
pause
