@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title AgriORBIT NASA - PHASE 34 EVIDENCE TO DECISIONS - PORT 8034
color 0B
echo.
echo  =====================================================
echo    AGRIORBIT PHASE 34 - BOTOLAN FARMER DECISIONS
 echo  THIS PATCH USES PORT 8034, NOT OLD PORT 8000.
echo  =====================================================
echo  Project: %CD%
echo.
if not exist "requirements.txt" goto missing
if not exist "app\main.py" goto missing
where py >nul 2>&1
if errorlevel 1 goto no_python
if not exist ".venv\Scripts\python.exe" (
 echo Creating environment...
 py -m venv .venv
 if errorlevel 1 goto fail
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail
 echo.
 echo STARTING PHASE 34 ON http://127.0.0.1:8034
 echo BOOT VIEW: http://127.0.0.1:8034/?calibration-hold=1^&force-15=1
 echo.
".venv\Scripts\python.exe" scripts\launch_phase34.py
if errorlevel 1 goto fail
pause
exit /b 0
:missing
 echo Project files missing. Extract the entire ZIP before launching.
pause
exit /b 1
:no_python
 echo Python launcher not found. Run py --version in PowerShell.
pause
exit /b 1
:fail
 echo Startup failed. Read the error above.
pause
exit /b 1
