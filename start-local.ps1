$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& "$PSScriptRoot\setup-local.bat"
if ($LASTEXITCODE -ne 0) { throw "Local setup failed." }
Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$PSScriptRoot\backend'; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$PSScriptRoot\frontend'; npm run dev -- --host 127.0.0.1"
Start-Sleep -Seconds 3
Start-Process 'http://localhost:5173'
