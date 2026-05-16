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
Write-Host "=== LogFlow Redis Smoke Test ===" -ForegroundColor Cyan
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
# 2. Trigger rate limit (12 requests, expect 429)
# --------------------------------------------------
Write-Step "Rate limit trigger"

$ClientId = "rate-limit-test-$RunId"
$Body = @{
    client_id    = $ClientId
    event_type   = "api_access"
    path         = "/api/health"
    method       = "GET"
    status_code  = 200
    duration_ms  = 5
    ip           = "10.0.0.1"
} | ConvertTo-Json -Depth 10

$Hit429 = $false
for ($i = 1; $i -le 12; $i++) {
    try {
        $null = Invoke-RestMethod -Uri "$BaseUrl/api/events" -Method Post `
            -Body $Body -ContentType "application/json"
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq 429) {
            $Hit429 = $true
        } else {
            throw
        }
    }
}

if (-not $Hit429) {
    Write-Fail "expected at least one 429 response after 12 requests"
}
Write-Pass

# --------------------------------------------------
# 3. Stats overview cache path
# --------------------------------------------------
Write-Step "Stats overview cache path"

try {
    $r1 = Invoke-RestMethod -Uri "$BaseUrl/api/stats/overview" -Method Get
    if (-not $r1.success) { throw "first call failed" }

    $d1 = $r1.data
    $required = @("total_events", "p95_duration_ms", "slow_request_count")
    foreach ($f in $required) {
        if (-not (Get-Member -InputObject $d1 -Name $f -MemberType Properties)) {
            throw "missing field in overview: $f"
        }
    }

    $r2 = Invoke-RestMethod -Uri "$BaseUrl/api/stats/overview" -Method Get
    if (-not $r2.success) { throw "second call failed" }

    Write-Pass
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
# 4. Top paths cache path
# --------------------------------------------------
Write-Step "Top paths cache path"

try {
    $r1 = Invoke-RestMethod -Uri "$BaseUrl/api/stats/top-paths?limit=5" -Method Get
    if (-not $r1.success) { throw "first call failed" }
    if ($r1.data.Count -lt 1) { throw "expected at least 1 top path" }

    $first = $r1.data[0]
    if (-not (Get-Member -InputObject $first -Name "path" -MemberType Properties)) {
        throw "missing 'path' field"
    }
    if (-not (Get-Member -InputObject $first -Name "count" -MemberType Properties)) {
        throw "missing 'count' field"
    }

    $r2 = Invoke-RestMethod -Uri "$BaseUrl/api/stats/top-paths?limit=5" -Method Get
    if (-not $r2.success) { throw "second call failed" }

    Write-Pass
} catch {
    Write-Fail $_.Exception.Message
}

# --------------------------------------------------
Write-Host ""
Write-Host "=== All redis smoke tests passed ===" -ForegroundColor Green
Write-Host ""
