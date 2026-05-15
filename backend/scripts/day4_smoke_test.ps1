param(
    [string]$BaseUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

function Write-Step($name) {
    Write-Host -NoNewline "[....] $name "
}

function Write-Pass {
    Write-Host "[PASS]" -ForegroundColor Green
}

function Write-Fail($msg) {
    Write-Host "[FAIL]" -ForegroundColor Red
    Write-Host "       $msg" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==============================================" -ForegroundColor Yellow
Write-Host "  IMPORTANT: Before running this test:"         -ForegroundColor Yellow
Write-Host "  1. Set EVENT_WRITE_MODE=kafka in .env"          -ForegroundColor Yellow
Write-Host "  2. Restart FastAPI"                              -ForegroundColor Yellow
Write-Host "  3. Start Consumer in another terminal:"          -ForegroundColor Yellow
Write-Host "     cd D:\projects\logflow\backend"               -ForegroundColor Yellow
Write-Host "     .\.venv\Scripts\python.exe -m app.kafka.consumer" -ForegroundColor Yellow
Write-Host "==============================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "=== LogFlow Day 4 Smoke Test ===" -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl"
Write-Host ""

$RunId = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()

# --------------------------------------------------
# 1. Health Check
# --------------------------------------------------
Write-Step "Health check"

try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/health" -Method Get
    if (-not $r.success) { throw "success is false" }
    if ($r.data.status -ne "ok") { throw "status is not ok" }
    Write-Pass
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
# 2. Send event in Kafka mode
# --------------------------------------------------
Write-Step "Event submitted to Kafka"

$ClientId = "d4-client-$RunId"
$TraceId = "trace-d4-$RunId"

$body = @{
    client_id    = $ClientId
    user_id      = "d4-u10001"
    event_type   = "api_access"
    path         = "/api/day4/kafka-test"
    method       = "POST"
    status_code  = 200
    duration_ms  = 66
    ip           = "10.4.0.1"
    user_agent   = "Day4-Smoke-Test/1.0"
    service_name = "gateway-service"
    trace_id     = $TraceId
    extra        = @{ day = 4; mode = "kafka" }
} | ConvertTo-Json -Depth 10

try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/events" -Method Post `
        -Body $body -ContentType "application/json"
    if (-not $r.success) { throw "success is false" }

    $EventId = $r.data.event_id
    if (-not $EventId) { throw "event_id is empty" }

    $WriteMode = $r.data.write_mode
    if ($WriteMode -eq "sync_fallback") {
        $reason = $r.data.fallback_reason
        throw "write_mode is sync_fallback, not kafka. Reason: $reason"
    }
    if ($WriteMode -ne "kafka") {
        throw "expected write_mode=kafka, got $WriteMode"
    }

    Write-Pass
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
# 3. Verify Consumer wrote to MySQL (poll up to 10s)
# --------------------------------------------------
Write-Step "Event found in MySQL after Kafka consume"

$Found = $false
for ($i = 1; $i -le 10; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-RestMethod -Uri "$BaseUrl/api/events/$EventId" -Method Get
        if ($r.success) {
            if ($r.data.path -eq "/api/day4/kafka-test" -and $r.data.trace_id -eq $TraceId) {
                $Found = $true
                break
            }
        }
    } catch {
        # 404 is expected while consumer hasn't processed yet
    }
}

if (-not $Found) {
    Write-Fail "event not found in MySQL after 10 retries"
}
Write-Pass

# --------------------------------------------------
# 4. Stats overview still works
# --------------------------------------------------
Write-Step "Stats overview still works"

try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/stats/overview" -Method Get
    if (-not $r.success) { throw "success is false" }

    $s = $r.data
    $required = @("total_events", "p95_duration_ms", "slow_request_count")
    foreach ($f in $required) {
        if (-not (Get-Member -InputObject $s -Name $f -MemberType Properties)) {
            throw "missing field: $f"
        }
    }

    Write-Pass
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
Write-Host ""
Write-Host "=== All Day 4 smoke tests passed ===" -ForegroundColor Green
Write-Host ""
