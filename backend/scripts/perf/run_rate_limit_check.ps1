$ErrorActionPreference = "Stop"

$BackendRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$ProjectRoot = Resolve-Path (Join-Path $BackendRoot "..")
$PerfDir = Join-Path $ProjectRoot "docs\performance"

New-Item -ItemType Directory -Force -Path $PerfDir | Out-Null

Set-Location $BackendRoot

$CsvPrefix = Join-Path $PerfDir "rate_limit_check"

Write-Host "Running: rate limit check, 50 users, 10/s spawn, 1m runtime" -ForegroundColor Cyan
Write-Host "Fixed client_id: rate-limit-load-test (429 is expected)" -ForegroundColor Yellow
Write-Host "CSV output: $CsvPrefix*.csv" -ForegroundColor Cyan

& (Join-Path $BackendRoot ".venv\Scripts\python.exe") -m locust `
    -f (Join-Path $BackendRoot "locustfile_rate_limit.py") `
    --host http://localhost:8000 `
    --headless `
    -u 50 `
    -r 10 `
    --run-time 1m `
    --csv $CsvPrefix

if ($LASTEXITCODE -ne 0) {
    Write-Host "Locust exited with code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Done." -ForegroundColor Green
