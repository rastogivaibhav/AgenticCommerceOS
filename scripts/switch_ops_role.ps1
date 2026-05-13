param(
    [ValidateSet("admin", "ops", "analyst")]
    [string]$Role = "admin",
    [string]$BaseUrl = "http://localhost:8001",
    [string]$Redirect = "/ui/agents",
    [string]$Secret = $env:OPS_JWT_SECRET,
    [int]$TtlHours = 24,
    [switch]$NoOpen
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$mintScript = Join-Path $repoRoot "scripts\\mint_dev_jwt.py"

if (-not (Test-Path -LiteralPath $mintScript)) {
    throw "mint_dev_jwt.py not found at $mintScript"
}

if ([string]::IsNullOrWhiteSpace($Secret)) {
    $Secret = "local-dev-secret"
    Write-Warning "OPS_JWT_SECRET not set. Falling back to '$Secret'."
}

$mintArgs = @($mintScript, "--role", $Role, "--secret", $Secret, "--ttl-hours", $TtlHours, "--json")

function Invoke-Minter {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [string[]]$ExtraArgs = @()
    )

    $rawOutput = & $Command @ExtraArgs @mintArgs 2>&1
    if ($LASTEXITCODE -eq 0) {
        return ($rawOutput | Out-String).Trim()
    }
    throw ($rawOutput | Out-String)
}

$pythonCandidates = @(
    @{ Command = (Join-Path $repoRoot ".venv\\Scripts\\python.exe"); ExtraArgs = @() },
    @{ Command = "py"; ExtraArgs = @("-3") },
    @{ Command = "python"; ExtraArgs = @() }
)

$jsonText = $null
$errors = @()
foreach ($candidate in $pythonCandidates) {
    $cmd = $candidate.Command
    $extra = $candidate.ExtraArgs

    $isPath = $cmd.Contains("\") -or $cmd.Contains("/")
    if ($isPath -and -not (Test-Path -LiteralPath $cmd)) {
        continue
    }

    try {
        $jsonText = Invoke-Minter -Command $cmd -ExtraArgs $extra
        break
    } catch {
        $errors += ("{0}: {1}" -f $cmd, $_.Exception.Message)
    }
}

if ([string]::IsNullOrWhiteSpace($jsonText)) {
    throw ("Token mint failed. Tried python launchers:`n{0}" -f ($errors -join "`n"))
}

$tokenMap = $jsonText | ConvertFrom-Json
$token = $tokenMap.$Role
if ([string]::IsNullOrWhiteSpace($token)) {
    throw "Unable to find token for role '$Role' in mint output."
}

$tokenEncoded = [System.Uri]::EscapeDataString($token)
$redirectEncoded = [System.Uri]::EscapeDataString($Redirect)
$bootstrapUrl = "$BaseUrl/dev/auth/bootstrap?token=$tokenEncoded&redirect=$redirectEncoded"

Write-Host "Role token minted: $Role"
Write-Host "Bootstrap URL: $bootstrapUrl"

if (-not $NoOpen) {
    Start-Process $bootstrapUrl
}
