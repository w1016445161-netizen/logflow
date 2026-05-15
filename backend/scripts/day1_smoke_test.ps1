param(
    [string]$BaseUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"
$RunId = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()

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
Write-Host "=== LogFlow Day 1 Smoke Test ===" -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl"
Write-Host ""

# --------------------------------------------------
# 1. GET /api/health
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
# 2. POST /api/events (api_access)
# --------------------------------------------------
Write-Step "Create event (api_access)"

$body1 = @{
    client_id    = "client-001-$RunId"
    user_id      = "u10001"
    event_type   = "api_access"
    path         = "/api/login"
    method       = "POST"
    status_code  = 200
    duration_ms  = 45
    ip           = "192.168.1.100"
    user_agent   = "Mozilla/5.0"
    service_name = "gateway-service"
    trace_id     = "trace-demo-001"
    extra        = @{ login_type = "password" }
}

try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/events" -Method Post `
        -Body ($body1 | ConvertTo-Json) -ContentType "application/json"
    if (-not $r.success) { throw "success is false" }
    $EventId1 = $r.data.event_id
    if (-not $EventId1) { throw "event_id is empty" }
    Write-Pass
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
# 3. GET /api/events/{event_id}
# --------------------------------------------------
Write-Step "Get event by event_id"

try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/events/$EventId1" -Method Get
    if (-not $r.success) { throw "success is false" }
    if ($r.data.client_id -ne "client-001-$RunId") { throw "client_id mismatch" }
    if ($r.data.event_type -ne "api_access") { throw "event_type mismatch" }
    Write-Pass
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
# 4. POST /api/events (api_error)
# --------------------------------------------------
Write-Step "Create event (api_error)"

$body2 = @{
    client_id    = "client-002-$RunId"
    user_id      = "u10002"
    event_type   = "api_error"
    path         = "/api/orders/create"
    method       = "POST"
    status_code  = 500
    duration_ms  = 360
    ip           = "10.0.0.1"
    user_agent   = "curl/7.68.0"
    service_name = "gateway-service"
    extra        = @{ error = "database timeout" }
}

try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/events" -Method Post `
        -Body ($body2 | ConvertTo-Json) -ContentType "application/json"
    if (-not $r.success) { throw "success is false" }
    $EventId2 = $r.data.event_id
    if (-not $EventId2) { throw "event_id is empty" }
    Write-Pass
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
# 5. POST /api/events (slow_request)
# --------------------------------------------------
Write-Step "Create event (slow_request)"

$body3 = @{
    client_id    = "client-003-$RunId"
    user_id      = "u10003"
    event_type   = "slow_request"
    path         = "/api/payments/callback"
    method       = "POST"
    status_code  = 200
    duration_ms  = 1280
    ip           = "10.0.0.2"
    user_agent   = "python-requests/2.28"
    service_name = "gateway-service"
    extra        = @{ provider = "mock-pay" }
}

try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/events" -Method Post `
        -Body ($body3 | ConvertTo-Json) -ContentType "application/json"
    if (-not $r.success) { throw "success is false" }
    $EventId3 = $r.data.event_id
    if (-not $EventId3) { throw "event_id is empty" }
    Write-Pass
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
# 6. GET /api/stats/overview
# --------------------------------------------------
Write-Step "Stats overview"

try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/stats/overview" -Method Get
    if (-not $r.success) { throw "success is false" }

    $s = $r.data
    Write-Pass

    Write-Host ""
    Write-Host "  total_events     : $($s.total_events)"
    Write-Host "  total_clients    : $($s.total_clients)"
    Write-Host "  total_users      : $($s.total_users)"
    Write-Host "  error_events     : $($s.error_events)"
    Write-Host "  error_rate       : $($s.error_rate)"
    Write-Host "  avg_duration_ms  : $($s.avg_duration_ms)"
    Write-Host "  top_paths        : $($s.top_paths | ConvertTo-Json -Compress)"
    Write-Host "  top_event_types  : $($s.top_event_types | ConvertTo-Json -Compress)"

    # Basic sanity checks
    if ($s.total_events -lt 3) { throw "expected at least 3 total_events" }
    if ($s.error_events -lt 1) { throw "expected at least 1 error_event" }
    if ($s.error_rate -le 0) { throw "error_rate should be > 0" }
    if ($s.avg_duration_ms -le 0) { throw "avg_duration_ms should be > 0" }
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
# 7. GET /api/events/{nonexistent} — expect 404
# --------------------------------------------------
Write-Step "Get nonexistent event (expect error)"

try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/events/nonexistent-id" -Method Get
    # Should not reach here — Invoke-RestMethod throws on 4xx by default
    throw "expected 404 but got success"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 404) {
        Write-Pass
    } else {
        Write-Fail "expected 404, got $statusCode : $($_.Exception.Message)"
    }
}

# --------------------------------------------------
Write-Host ""
Write-Host "=== All Day 1 smoke tests passed ===" -ForegroundColor Green
Write-Host ""
