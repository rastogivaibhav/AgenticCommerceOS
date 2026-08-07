param(
    [switch]$SkipDocker,
    [switch]$SkipVerify,
    [switch]$Headed,
    [string]$EnvFile = ".env.ecom-demo"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Invoke-Checked {
    param(
        [scriptblock]$Command,
        [string]$Label
    )
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

if (-not (Test-Path $EnvFile)) {
    Copy-Item ".env.ecom-demo.example" $EnvFile
    Write-Host "Created $EnvFile from .env.ecom-demo.example"
}

$composeArgs = @(
    "--env-file", $EnvFile,
    "-f", "docker-compose.yml",
    "-f", "docker-compose.ecom-demo.yml"
)

if (-not $SkipDocker) {
    Write-Host "Checking Docker..."
    try {
        docker info *> $null
    } catch {
        throw "Docker Desktop is not running or the Docker engine is unreachable. Start Docker Desktop, wait until it says it is running, then rerun .\scripts\run_ecom_demo.ps1"
    }

    Write-Host "Starting ACOS + real Spree demo stack..."
    Invoke-Checked { docker compose @composeArgs up --build -d } "Docker compose startup"
}

if (-not $SkipVerify) {
    Write-Host "Verifying real Spree + ACOS integration..."
    Invoke-Checked { python scripts/ecom_demo_verify.py --env-file $EnvFile } "Real ecommerce verifier"
}

Write-Host "Installing Playwright harness dependencies..."
Invoke-Checked { npm --prefix harness/playwright install } "Playwright dependency install"

Write-Host "Ensuring Playwright Chromium is installed..."
Invoke-Checked { npm --prefix harness/playwright exec -- playwright install chromium } "Playwright Chromium install"

$playwrightArgs = @("run", "test:ecom-demo", "--")

if ($Headed) {
    $playwrightArgs += "--headed"
}

Write-Host "Running Playwright browser proof..."
Invoke-Checked { npm --prefix harness/playwright @playwrightArgs } "Playwright browser proof"

Write-Host ""
Write-Host "Demo complete."
Write-Host "ACOS Ops UI: http://localhost:8081/ui/estate"
Write-Host "Spree backend/API: http://localhost:3000"
Write-Host "Screenshots: harness/playwright/output/playwright/ecom-demo"
Write-Host "Videos and report: harness/playwright/test-results and harness/playwright/reports/ecom-demo"
