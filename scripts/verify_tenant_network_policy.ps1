param(
    [Parameter(Mandatory = $true)]
    [string]$TenantId,
    [string]$TenantNamespace = "",
    [string]$ControlPlaneProbeHost = "",
    [string]$EvidencePath = "",
    [switch]$SkipRender
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $TenantNamespace) {
    $TenantNamespace = "acos-tenant-$TenantId"
}

if (-not $EvidencePath) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $EvidencePath = "deploy/k8s/multi-tenant/evidence/$TenantNamespace-$stamp.json"
}

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' is not installed or not on PATH."
    }
}

function Run-Probe {
    param(
        [string]$Namespace,
        [string]$Name,
        [string]$Script
    )
    $podName = "probe-$Name-" + (Get-Random -Minimum 1000 -Maximum 9999)
    & kubectl run $podName -n $Namespace --image=busybox:1.36 --restart=Never --command -- sh -c $Script | Out-Null

    $phase = "Unknown"
    $logs = ""
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline) {
        try {
            $phase = (& kubectl get pod $podName -n $Namespace -o jsonpath='{.status.phase}').Trim()
        } catch {
            $phase = "Missing"
        }
        if ($phase -in @("Succeeded", "Failed")) {
            break
        }
        Start-Sleep -Seconds 2
    }
    try {
        $phase = (& kubectl get pod $podName -n $Namespace -o jsonpath='{.status.phase}').Trim()
    } catch {
        $phase = "Missing"
    }
    try {
        $logs = (& kubectl logs $podName -n $Namespace) | Out-String
    } catch {
        $logs = ""
    }
    try {
        & kubectl delete pod $podName -n $Namespace --ignore-not-found=true | Out-Null
    } catch {}

    return @{
        name = $Name
        phase = $phase
        logs = $logs.Trim()
    }
}

function Supports-PeerAuthentication {
    try {
        $resource = & kubectl api-resources --api-group=security.istio.io -o name 2>$null
        if (-not $resource) {
            return $false
        }
        return ($resource -split "`n" | ForEach-Object { $_.Trim() }) -contains "peerauthentications"
    } catch {
        return $false
    }
}

Require-Command "kubectl"

if (-not $SkipRender) {
    $renderScript = "scripts/render_tenant_network_baseline.ps1"
    if (-not (Test-Path $renderScript)) {
        throw "Render script not found: $renderScript"
    }
    & powershell -ExecutionPolicy Bypass -File $renderScript -TenantId $TenantId -TenantNamespace $TenantNamespace
}

$manifestDir = "deploy/k8s/multi-tenant/rendered/$TenantNamespace"
if (-not (Test-Path $manifestDir)) {
    throw "Rendered manifest directory not found: $manifestDir"
}

$coreManifests = @(
    (Join-Path $manifestDir "namespace-template.yaml"),
    (Join-Path $manifestDir "networkpolicy-default-deny.yaml"),
    (Join-Path $manifestDir "networkpolicy-allow-dns.yaml"),
    (Join-Path $manifestDir "networkpolicy-allow-acos-control-plane.yaml")
)

foreach ($manifest in $coreManifests) {
    & kubectl apply -f $manifest | Out-Null
}

$peerAuthManifest = Join-Path $manifestDir "peer-authentication-strict.yaml"
$peerAuthApplied = $false
if (Test-Path $peerAuthManifest) {
    if (Supports-PeerAuthentication) {
        & kubectl apply -f $peerAuthManifest | Out-Null
        $peerAuthApplied = $true
    }
}

$dnsProbe = Run-Probe -Namespace $TenantNamespace -Name "dns-allowed" -Script "nslookup kubernetes.default.svc.cluster.local >/tmp/out 2>&1; code=`$?; cat /tmp/out; exit `$code"
$egressProbe = Run-Probe -Namespace $TenantNamespace -Name "internet-denied" -Script "wget -T 3 -O- http://example.com >/tmp/out 2>&1; code=`$?; cat /tmp/out; if [ `$code -eq 0 ]; then exit 1; else exit 0; fi"

$controlPlaneProbe = $null
if ($ControlPlaneProbeHost) {
    $controlPlaneProbe = Run-Probe -Namespace $TenantNamespace -Name "control-plane-allowed" -Script "wget -T 3 -O- http://$ControlPlaneProbeHost >/tmp/out 2>&1; code=`$?; cat /tmp/out; exit `$code"
}

$checks = @(
    @{
        name = "dns_allowed"
        passed = ($dnsProbe.phase -eq "Succeeded")
        details = $dnsProbe
    },
    @{
        name = "internet_denied"
        passed = ($egressProbe.phase -eq "Succeeded")
        details = $egressProbe
    }
)

if ($controlPlaneProbe) {
    $checks += @{
        name = "control_plane_allowed"
        passed = ($controlPlaneProbe.phase -eq "Succeeded")
        details = $controlPlaneProbe
    }
}

$overallPass = -not ($checks | Where-Object { -not $_.passed })
$report = @{
    tenant_id = $TenantId
    namespace = $TenantNamespace
    timestamp = (Get-Date).ToUniversalTime().ToString("o")
    overall_pass = [bool]$overallPass
    peer_authentication_applied = $peerAuthApplied
    checks = $checks
    manifests = (Get-ChildItem $manifestDir -File | Select-Object -ExpandProperty Name)
}

$evidenceDir = Split-Path -Parent $EvidencePath
if ($evidenceDir -and -not (Test-Path $evidenceDir)) {
    New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
}

$report | ConvertTo-Json -Depth 6 | Set-Content -Path $EvidencePath -Encoding utf8

if (-not $overallPass) {
    Write-Error "Network policy verification failed. Evidence: $EvidencePath"
    exit 1
}

Write-Host "Network policy verification passed. Evidence: $EvidencePath"
