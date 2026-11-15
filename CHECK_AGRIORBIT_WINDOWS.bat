@echo off
setlocal
cd /d "%~dp0"
echo AGRIORBIT PRE-FLIGHT
 echo Current directory: %CD%
if exist requirements.txt (echo [OK] requirements.txt) else (echo [FAIL] requirements.txt missing)
if exist app\main.py (echo [OK] app\main.py) else (echo [FAIL] app\main.py missing)
if exist web\rover3d.js (echo [OK] 3D renderer) else (echo [FAIL] renderer missing)
if exist web\mission-ui.js (echo [OK] Mission UI bridge) else (echo [FAIL] UI bridge missing)
if exist web\hud5.js (echo [OK] Phase 5 HUD) else (echo [FAIL] HUD missing)
if exist web\science-ui.js (echo [OK] Phase 21 science UI) else (echo [FAIL] science UI missing)
if exist app\science_core.py (echo [OK] evidence screening) else (echo [FAIL] scientific core missing)
if exist web\hazards-ui.js (echo [OK] PHIVOLCS Hazard UI (retained from Phase 23)) else (echo [FAIL] hazard UI missing)
if exist app\hazards.py (echo [OK] hazard geometry engine) else (echo [FAIL] hazard engine missing)
if exist web\leaf-cursor.js (echo [OK] Living leaf cursor engine) else (echo [FAIL] Living leaf cursor missing)
if exist app\botolan_demo.py (echo [OK] Botolan NASA comparison API) else (echo [FAIL] Botolan backend missing)
if exist web\botolan-ui.js (echo [OK] Botolan interactive UI) else (echo [FAIL] Botolan UI missing)
where py >nul 2>&1
if errorlevel 1 (echo [FAIL] Python launcher not installed) else (py --version)
echo.
echo If all checks pass, double-click START_AGRIORBIT_WINDOWS.cmd (or use PowerShell fallback)
pause
