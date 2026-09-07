@echo off
setlocal
cd /d %~dp0

call setup-local.bat
if errorlevel 1 (
  echo.
  echo Setup failed. Application was not started.
  pause
  exit /b 1
)

echo.
echo Starting MedSchedule...
start "MedSchedule Backend" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
start "MedSchedule Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev -- --host 127.0.0.1"

timeout /t 3 /nobreak >nul
start "" http://localhost:5173

echo.
echo Frontend : http://localhost:5173
echo Swagger  : http://localhost:8000/docs
echo Health   : http://localhost:8000/api/health
echo.
pause
