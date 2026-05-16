param(
    [string]$BaseDir = "$PSScriptRoot\.."
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== LogFlow Day 5 Engineering Check ===" -ForegroundColor Cyan
Write-Host ""

$PythonExe = Join-Path $BaseDir ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "[FAIL] Python venv not found at $PythonExe" -ForegroundColor Red
    Write-Host "       Create it first: python -m venv .venv" -ForegroundColor Red
    exit 1
}

Write-Host "Running pytest..." -ForegroundColor Cyan
Write-Host ""

Push-Location $BaseDir
try {
    & $PythonExe -m pytest -q
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=== Day 5 engineering check passed ===" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "[FAIL] Some tests failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
        Write-Host ""
        exit 1
    }
} finally {
    Pop-Location
}
