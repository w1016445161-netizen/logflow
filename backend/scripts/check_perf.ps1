$ErrorActionPreference = "Stop"

$BackendRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $BackendRoot

Write-Host ""
Write-Host "=== LogFlow Performance Check ===" -ForegroundColor Cyan
Write-Host ""

$HealthUrl = "http://localhost:8000/api/health"

Write-Host "Checking health: $HealthUrl" -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri $HealthUrl -Method GET -TimeoutSec 10
    if ($health.success) {
        Write-Host "[OK] Health check passed" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Health check returned success=false" -ForegroundColor Red
        Write-Host ($health | ConvertTo-Json)
        exit 1
    }
} catch {
    Write-Host "[FAIL] Cannot reach $HealthUrl : $_" -ForegroundColor Red
    Write-Host "Make sure Docker (mysql, redis, kafka) and FastAPI are running." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Running Locust quick check (5 users, 1/s, 15s)..." -ForegroundColor Cyan
Write-Host ""

& (Join-Path $BackendRoot ".venv\Scripts\python.exe") -m locust `
    -f (Join-Path $BackendRoot "locustfile.py") `
    --host http://localhost:8000 `
    --headless `
    -u 5 `
    -r 1 `
    --run-time 15s

if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Locust exited with code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== Performance check passed ===" -ForegroundColor Green
Write-Host ""
