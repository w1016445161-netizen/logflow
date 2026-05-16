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
Write-Host "=== LogFlow Stats Smoke Test ===" -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl"
Write-Host ""

# --------------------------------------------------
# Helper: POST a single event, return event_id
# --------------------------------------------------
function Post-Event($body) {
    $json = $body | ConvertTo-Json -Depth 10
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/events" -Method Post `
        -Body $json -ContentType "application/json"
    if (-not $r.success) { throw "POST /api/events failed" }
    return $r.data.event_id
}

# --------------------------------------------------
# 1. Insert test data (7 records)
# --------------------------------------------------
Write-Step "Insert test data"

try {
    $null = Post-Event @{
        client_id    = "stats-client-001-$RunId"
        user_id      = "stats-u10001"
        event_type   = "api_access"
        path         = "/api/login"
        method       = "POST"
        status_code  = 200
        duration_ms  = 45
        ip           = "192.168.1.101"
        user_agent   = "Mozilla/5.0"
        service_name = "gateway-service"
        trace_id     = "trace-stats-001"
        extra        = @{ login_type = "password" }
    }

    $null = Post-Event @{
        client_id    = "stats-client-001-$RunId"
        user_id      = "stats-u10001"
        event_type   = "api_access"
        path         = "/api/login"
        method       = "POST"
        status_code  = 200
        duration_ms  = 80
        ip           = "192.168.1.101"
        user_agent   = "Mozilla/5.0"
        service_name = "gateway-service"
        trace_id     = "trace-stats-002"
        extra        = @{ login_type = "sms" }
    }

    $null = Post-Event @{
        client_id    = "stats-client-002-$RunId"
        user_id      = "stats-u10002"
        event_type   = "api_access"
        path         = "/api/users/profile"
        method       = "GET"
        status_code  = 200
        duration_ms  = 120
        ip           = "10.0.1.1"
        user_agent   = "MobileApp/2.0"
        service_name = "gateway-service"
        trace_id     = "trace-stats-003"
        extra        = @{}
    }

    $null = Post-Event @{
        client_id    = "stats-client-003-$RunId"
        user_id      = "stats-u10003"
        event_type   = "api_error"
        path         = "/api/orders/create"
        method       = "POST"
        status_code  = 500
        duration_ms  = 360
        ip           = "10.0.1.2"
        user_agent   = "curl/7.68.0"
        service_name = "gateway-service"
        trace_id     = "trace-stats-004"
        extra        = @{ error = "database timeout" }
    }

    $null = Post-Event @{
        client_id    = "stats-client-004-$RunId"
        user_id      = "stats-u10004"
        event_type   = "api_error"
        path         = "/api/orders/create"
        method       = "POST"
        status_code  = 502
        duration_ms  = 420
        ip           = "10.0.1.3"
        user_agent   = "curl/7.68.0"
        service_name = "gateway-service"
        trace_id     = "trace-stats-005"
        extra        = @{ error = "upstream timeout" }
    }

    $null = Post-Event @{
        client_id    = "stats-client-005-$RunId"
        user_id      = "stats-u10005"
        event_type   = "slow_request"
        path         = "/api/payments/callback"
        method       = "POST"
        status_code  = 200
        duration_ms  = 1280
        ip           = "10.0.1.4"
        user_agent   = "python-requests/2.28"
        service_name = "gateway-service"
        trace_id     = "trace-stats-006"
        extra        = @{ provider = "mock-pay" }
    }

    $null = Post-Event @{
        client_id    = "stats-client-006-$RunId"
        user_id      = "stats-u10006"
        event_type   = "slow_request"
        path         = "/api/products/search"
        method       = "GET"
        status_code  = 200
        duration_ms  = 2500
        ip           = "10.0.1.5"
        user_agent   = "MobileApp/2.0"
        service_name = "gateway-service"
        trace_id     = "trace-stats-007"
        extra        = @{ query = "laptop" }
    }

    Write-Pass
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
# 2. GET /api/stats/overview
# --------------------------------------------------
Write-Step "Stats overview"

try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/stats/overview" -Method Get
    if (-not $r.success) { throw "success is false" }

    $s = $r.data

    # Verify all expected fields exist
    $required = @(
        "total_events", "total_clients", "total_users",
        "error_events", "error_rate", "avg_duration_ms",
        "p95_duration_ms", "slow_request_count",
        "top_paths", "top_event_types"
    )
    foreach ($f in $required) {
        if (-not (Get-Member -InputObject $s -Name $f -MemberType Properties)) {
            throw "missing field: $f"
        }
    }

    # Data sanity
    if ($s.total_events -lt 7) { throw "total_events should be >= 7, got $($s.total_events)" }
    if ($s.error_events -lt 2) { throw "error_events should be >= 2, got $($s.error_events)" }
    if ($s.error_rate -le 0) { throw "error_rate should be > 0" }
    if ($s.avg_duration_ms -le 0) { throw "avg_duration_ms should be > 0" }
    if ($s.p95_duration_ms -le 0) { throw "p95_duration_ms should be > 0" }
    if ($s.slow_request_count -lt 2) { throw "slow_request_count should be >= 2, got $($s.slow_request_count)" }

    Write-Pass
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
# 3. GET /api/stats/top-paths?limit=5
# --------------------------------------------------
Write-Step "Top paths"

try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/stats/top-paths?limit=5" -Method Get
    if (-not $r.success) { throw "success is false" }

    $data = $r.data
    if ($data.Count -lt 1) { throw "expected at least 1 top path" }
    if ($data.Count -gt 5) { throw "expected at most 5 top paths, got $($data.Count)" }

    $first = $data[0]
    $required = @("path", "count", "avg_duration_ms", "error_count", "error_rate")
    foreach ($f in $required) {
        if (-not (Get-Member -InputObject $first -Name $f -MemberType Properties)) {
            throw "missing field in top-paths item: $f"
        }
    }

    if ($first.count -le 0) { throw "count should be > 0" }
    if ($data[0].count -lt $data[-1].count) { throw "results not sorted by count descending" }

    Write-Pass
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
# 4. GET /api/stats/top-event-types?limit=5
# --------------------------------------------------
Write-Step "Top event types"

try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/stats/top-event-types?limit=5" -Method Get
    if (-not $r.success) { throw "success is false" }

    $data = $r.data
    if ($data.Count -lt 1) { throw "expected at least 1 top event type" }

    $first = $data[0]
    $required = @("event_type", "count", "avg_duration_ms")
    foreach ($f in $required) {
        if (-not (Get-Member -InputObject $first -Name $f -MemberType Properties)) {
            throw "missing field in top-event-types item: $f"
        }
    }

    Write-Pass
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
# 5. GET /api/stats/slow-requests?threshold_ms=1000&limit=5
# --------------------------------------------------
Write-Step "Slow requests"

try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/stats/slow-requests?threshold_ms=1000&limit=5" -Method Get
    if (-not $r.success) { throw "success is false" }

    $data = $r.data
    if ($data.Count -lt 2) { throw "expected at least 2 slow requests, got $($data.Count)" }

    $first = $data[0]
    $required = @("event_id", "client_id", "user_id", "event_type", "path",
                  "method", "status_code", "duration_ms", "trace_id", "created_at")
    foreach ($f in $required) {
        if (-not (Get-Member -InputObject $first -Name $f -MemberType Properties)) {
            throw "missing field in slow-request item: $f"
        }
    }

    if ($first.duration_ms -lt 1000) { throw "slowest request duration_ms should be >= 1000" }
    if ($first.duration_ms -lt $data[-1].duration_ms) { throw "results not sorted by duration_ms descending" }

    Write-Pass
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
# 6. GET /api/stats/errors?limit=5
# --------------------------------------------------
Write-Step "Errors"

try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/stats/errors?limit=5" -Method Get
    if (-not $r.success) { throw "success is false" }

    $data = $r.data

    $required = @("total_error_events", "error_rate", "top_error_paths", "recent_errors")
    foreach ($f in $required) {
        if (-not (Get-Member -InputObject $data -Name $f -MemberType Properties)) {
            throw "missing field in errors response: $f"
        }
    }

    if ($data.total_error_events -lt 2) { throw "total_error_events should be >= 2" }
    if ($data.error_rate -le 0) { throw "error_rate should be > 0" }
    if ($data.top_error_paths.Count -lt 1) { throw "expected at least 1 top_error_path" }
    if ($data.recent_errors.Count -lt 1) { throw "expected at least 1 recent_error" }

    Write-Pass
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
# 7. GET /api/stats/slow-requests — lower threshold
# --------------------------------------------------
Write-Step "Slow requests (threshold_ms=300)"

try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/stats/slow-requests?threshold_ms=300&limit=5" -Method Get
    if (-not $r.success) { throw "success is false" }

    $data = $r.data
    if ($data.Count -lt 4) { throw "expected at least 4 events with duration >= 300ms" }

    Write-Pass
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
Write-Host ""
Write-Host "=== All stats smoke tests passed ===" -ForegroundColor Green
Write-Host ""
