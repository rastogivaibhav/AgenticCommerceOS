param(
    [string]$BaseUrl = "http://localhost:8082",
    [string]$ApiKey = "test-key-1",
    [int]$SingleTenantRequests = 60,
    [int]$MixedTenantRequests = 120,
    [int]$InterScenarioCooldownSeconds = 65,
    [string]$OutputDir = "deploy/k8s/performance/evidence"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-Percentile {
    param(
        [double[]]$Values,
        [double]$Percentile
    )

    if (-not $Values -or $Values.Count -eq 0) {
        return 0.0
    }

    $sorted = $Values | Sort-Object
    $index = [math]::Ceiling(($Percentile / 100.0) * $sorted.Count) - 1
    if ($index -lt 0) {
        $index = 0
    }
    if ($index -ge $sorted.Count) {
        $index = $sorted.Count - 1
    }
    return [math]::Round([double]$sorted[$index], 3)
}

function Invoke-JourneyRequest {
    param(
        [string]$TenantId,
        [string]$BaseUrl,
        [string]$ApiKey
    )

    $headers = @{
        "X-API-Key"    = $ApiKey
        "Content-Type" = "application/json"
    }
    $payload = @{
        message     = "week10 baseline request for $TenantId"
        tenant_id   = $TenantId
        customer_id = "week10perf"
    } | ConvertTo-Json -Depth 4 -Compress

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $statusCode = 0
    $success = $false

    try {
        $response = Invoke-WebRequest -Uri "$BaseUrl/journey" -Method Post -Headers $headers -Body $payload -UseBasicParsing -TimeoutSec 20
        $statusCode = [int]$response.StatusCode
        $success = ($statusCode -ge 200 -and $statusCode -lt 300)
    } catch {
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $statusCode = [int]$_.Exception.Response.StatusCode.value__
        }
    }

    $sw.Stop()
    return [pscustomobject]@{
        tenant_id    = $TenantId
        status_code  = $statusCode
        success      = $success
        duration_ms  = [math]::Round($sw.Elapsed.TotalMilliseconds, 3)
    }
}

function Run-Scenario {
    param(
        [string]$Name,
        [int]$Count,
        [scriptblock]$TenantSelector,
        [string]$BaseUrl,
        [string]$ApiKey
    )

    $results = New-Object System.Collections.Generic.List[object]
    $scenarioTimer = [System.Diagnostics.Stopwatch]::StartNew()
    for ($i = 0; $i -lt $Count; $i++) {
        $tenantId = & $TenantSelector $i
        $result = Invoke-JourneyRequest -TenantId $tenantId -BaseUrl $BaseUrl -ApiKey $ApiKey
        $results.Add($result)
    }
    $scenarioTimer.Stop()

    $durations = @($results | ForEach-Object { [double]$_.duration_ms })
    $successCount = @($results | Where-Object { $_.success }).Count
    $errorCount = $Count - $successCount
    $errorRate = if ($Count -eq 0) { 0.0 } else { [math]::Round(($errorCount / [double]$Count) * 100.0, 3) }
    $throughput = if ($scenarioTimer.Elapsed.TotalSeconds -le 0) { 0.0 } else { [math]::Round($Count / $scenarioTimer.Elapsed.TotalSeconds, 3) }

    $statusBreakdown = @(
        $results |
            Group-Object -Property status_code |
            Sort-Object Name |
            ForEach-Object {
                [pscustomobject]@{
                    status_code = [int]$_.Name
                    count       = $_.Count
                }
            }
    )

    $tenantBreakdown = @(
        $results |
            Group-Object -Property tenant_id |
            Sort-Object Name |
            ForEach-Object {
                $tenantSuccess = @($_.Group | Where-Object { $_.success }).Count
                [pscustomobject]@{
                    tenant_id   = $_.Name
                    count       = $_.Count
                    success     = $tenantSuccess
                    failures    = $_.Count - $tenantSuccess
                    p95_ms      = Get-Percentile -Values (@($_.Group | ForEach-Object { [double]$_.duration_ms })) -Percentile 95
                }
            }
    )

    return [pscustomobject]@{
        scenario_name      = $Name
        request_count      = $Count
        success_count      = $successCount
        error_count        = $errorCount
        error_rate_percent = $errorRate
        throughput_rps     = $throughput
        latency_ms         = [pscustomobject]@{
            p50 = Get-Percentile -Values $durations -Percentile 50
            p95 = Get-Percentile -Values $durations -Percentile 95
            p99 = Get-Percentile -Values $durations -Percentile 99
            min = if ($durations.Count -eq 0) { 0.0 } else { [math]::Round((($durations | Measure-Object -Minimum).Minimum), 3) }
            max = if ($durations.Count -eq 0) { 0.0 } else { [math]::Round((($durations | Measure-Object -Maximum).Maximum), 3) }
        }
        status_breakdown   = $statusBreakdown
        tenant_breakdown   = $tenantBreakdown
    }
}

try {
    $health = Invoke-WebRequest -Uri "$BaseUrl/health" -UseBasicParsing -TimeoutSec 10
    if ($health.StatusCode -ne 200) {
        throw "Health check returned status code $($health.StatusCode)."
    }
} catch {
    throw "Shopper API health check failed at $BaseUrl/health. $($_.Exception.Message)"
}

$singleTenant = Run-Scenario -Name "single_tenant_default" -Count $SingleTenantRequests -TenantSelector { param($i) "default" } -BaseUrl $BaseUrl -ApiKey $ApiKey

if ($InterScenarioCooldownSeconds -gt 0) {
    Write-Host "Cooling down between scenarios for $InterScenarioCooldownSeconds seconds..."
    Start-Sleep -Seconds $InterScenarioCooldownSeconds
}

$mixedTenant = Run-Scenario -Name "mixed_tenant_default_eu_store" -Count $MixedTenantRequests -TenantSelector { param($i) if (($i % 2) -eq 0) { "default" } else { "eu-store" } } -BaseUrl $BaseUrl -ApiKey $ApiKey

$overallPassed = ($singleTenant.error_rate_percent -lt 2.0) -and ($mixedTenant.error_rate_percent -lt 2.0)

$artifact = [pscustomobject]@{
    timestamp_utc = [DateTime]::UtcNow.ToString("o")
    week          = 10
    phase         = "performance_baseline"
    base_url      = $BaseUrl
    configuration = [pscustomobject]@{
        single_tenant_requests = $SingleTenantRequests
        mixed_tenant_requests  = $MixedTenantRequests
        inter_scenario_cooldown_seconds = $InterScenarioCooldownSeconds
    }
    scenarios     = @($singleTenant, $mixedTenant)
    overall       = [pscustomobject]@{
        pass                 = $overallPassed
        pass_rule            = "Each scenario error_rate_percent < 2.0"
        single_tenant_p95_ms = $singleTenant.latency_ms.p95
        mixed_tenant_p95_ms  = $mixedTenant.latency_ms.p95
        single_tenant_rps    = $singleTenant.throughput_rps
        mixed_tenant_rps     = $mixedTenant.throughput_rps
    }
}

$resolvedOutputDir = Join-Path (Get-Location) $OutputDir
New-Item -Path $resolvedOutputDir -ItemType Directory -Force | Out-Null

$timestampForFile = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss")
$outputFile = Join-Path $resolvedOutputDir "week10-performance-baseline-$timestampForFile.json"
$artifact | ConvertTo-Json -Depth 8 | Set-Content -Path $outputFile -Encoding UTF8

Write-Host "Week 10 performance baseline artifact written:"
Write-Host $outputFile
Write-Host ""
Write-Host "Single-tenant p95 (ms): $($singleTenant.latency_ms.p95)"
Write-Host "Mixed-tenant p95 (ms):  $($mixedTenant.latency_ms.p95)"
Write-Host "Single-tenant RPS:      $($singleTenant.throughput_rps)"
Write-Host "Mixed-tenant RPS:       $($mixedTenant.throughput_rps)"
Write-Host "Overall pass:           $overallPassed"
