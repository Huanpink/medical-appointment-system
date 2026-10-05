@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d %~dp0

echo ===============================================
echo  MedSchedule - Windows Local Setup
 echo  PostgreSQL + FastAPI + React/Vite (No Docker)
echo ===============================================

echo.
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python was not found in PATH.
  echo Install Python 3.11+ and enable "Add Python to PATH".
  exit /b 1
)
where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js was not found in PATH.
  echo Install Node.js LTS and reopen this terminal.
  exit /b 1
)

if not exist "backend\.venv\Scripts\python.exe" (
  echo [1/5] Creating Python virtual environment...
  python -m venv backend\.venv
  if errorlevel 1 exit /b 1
)

echo [2/5] Installing backend dependencies...
call "backend\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if errorlevel 1 (
  echo [ERROR] pip install failed. Check Internet access or your Python package mirror.
  exit /b 1
)

if not exist "backend\.env" (
  echo [3/5] Creating backend\.env from example...
  copy /Y "backend\.env.example" "backend\.env" >nul
) else (
  echo [3/5] backend\.env already exists - keeping it.
)

set "PSQL_EXE="
where psql >nul 2>nul
if not errorlevel 1 set "PSQL_EXE=psql.exe"

if not defined PSQL_EXE (
  for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "$p=Get-ChildItem 'C:\Program Files\PostgreSQL' -Filter psql.exe -Recurse -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1; if($p){$p.FullName}"`) do set "PSQL_EXE=%%P"
)

if not defined PSQL_EXE (
  echo.
  echo [ERROR] PostgreSQL client (psql.exe) was not found.
  echo Install PostgreSQL for Windows, then run setup-local.bat again.
  echo Common installer: https://www.postgresql.org/download/windows/
  exit /b 1
)

echo [4/5] Preparing PostgreSQL database and meduser...
echo Enter the password for the PostgreSQL admin user "postgres" when prompted.
"%PSQL_EXE%" -h localhost -U postgres -d postgres -v ON_ERROR_STOP=1 -f "tools\setup_postgres.sql"
if errorlevel 1 (
  echo [ERROR] PostgreSQL bootstrap failed.
  echo Check that PostgreSQL service is running and the postgres password is correct.
  exit /b 1
)

echo [5/5] Applying Alembic migrations...
pushd backend
call .venv\Scripts\alembic.exe upgrade head
if errorlevel 1 (
  popd
  exit /b 1
)
call .venv\Scripts\python.exe -c "from app.seed import seed_data; seed_data()"
if errorlevel 1 (
  popd
  exit /b 1
)
popd

echo.
echo Setup completed successfully.
echo Run run-local.bat to start the application.
exit /b 0
