$ErrorActionPreference = "Stop"

$BackendRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$ProjectRoot = Resolve-Path (Join-Path $BackendRoot "..")
$PerfDir = Join-Path $ProjectRoot "docs\performance"

New-Item -ItemType Directory -Force -Path $PerfDir | Out-Null

Set-Location $BackendRoot

$CsvPrefix = Join-Path $PerfDir "locust_100"

Write-Host "Running: locust 100 users, 10/s spawn, 2m runtime" -ForegroundColor Cyan
Write-Host "CSV output: $CsvPrefix*.csv" -ForegroundColor Cyan

& (Join-Path $BackendRoot ".venv\Scripts\python.exe") -m locust `
    -f (Join-Path $BackendRoot "locustfile.py") `
    --host http://localhost:8000 `
    --headless `
    -u 100 `
    -r 10 `
    --run-time 2m `
    --csv $CsvPrefix

if ($LASTEXITCODE -ne 0) {
    Write-Host "Locust exited with code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Done." -ForegroundColor Green
