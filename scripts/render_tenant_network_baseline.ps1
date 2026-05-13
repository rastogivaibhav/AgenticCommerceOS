param(
    [Parameter(Mandatory = $true)]
    [string]$TenantId,
    [string]$TenantNamespace = ""
)

if (-not $TenantNamespace) {
    $TenantNamespace = "acos-tenant-$TenantId"
}

$sourceDir = "deploy/k8s/multi-tenant"
$outputDir = Join-Path $sourceDir "rendered/$TenantNamespace"

New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

$files = @(
    "namespace-template.yaml",
    "networkpolicy-default-deny.yaml",
    "networkpolicy-allow-dns.yaml",
    "networkpolicy-allow-acos-control-plane.yaml",
    "peer-authentication-strict.yaml"
)

foreach ($file in $files) {
    $sourcePath = Join-Path $sourceDir $file
    if (-not (Test-Path $sourcePath)) {
        Write-Error "Missing template: $sourcePath"
        exit 1
    }
    $content = Get-Content $sourcePath -Raw
    $rendered = $content.Replace('${TENANT_NAMESPACE}', $TenantNamespace).Replace('${TENANT_ID}', $TenantId)
    $targetPath = Join-Path $outputDir $file
    Set-Content -Path $targetPath -Value $rendered
}

Write-Host "Rendered tenant baseline manifests:"
Write-Host "  tenant_id=$TenantId"
Write-Host "  namespace=$TenantNamespace"
Write-Host "  output=$outputDir"
