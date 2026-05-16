$ErrorActionPreference = "Stop"

$BackendRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$ProjectRoot = Resolve-Path (Join-Path $BackendRoot "..")
$PerfDir = Join-Path $ProjectRoot "docs\performance"

New-Item -ItemType Directory -Force -Path $PerfDir | Out-Null

Set-Location $BackendRoot

$CsvPrefix = Join-Path $PerfDir "ingest_500"

Write-Host "Running: ingest-only 500 users, 50/s spawn, 2m runtime" -ForegroundColor Cyan
Write-Host "CSV output: $CsvPrefix*.csv" -ForegroundColor Cyan
Write-Host "NOTE: 500 concurrent users may exceed local Docker Desktop capacity." -ForegroundColor Yellow

& (Join-Path $BackendRoot ".venv\Scripts\python.exe") -m locust `
    -f (Join-Path $BackendRoot "locustfile_ingest_only.py") `
    --host http://localhost:8000 `
    --headless `
    -u 500 `
    -r 50 `
    --run-time 2m `
    --csv $CsvPrefix

if ($LASTEXITCODE -ne 0) {
    Write-Host "Locust exited with code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Done." -ForegroundColor Green
