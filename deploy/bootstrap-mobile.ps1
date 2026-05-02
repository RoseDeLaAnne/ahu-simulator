Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$mobileRoot = Join-Path $projectRoot "mobile"
$packageJson = Join-Path $mobileRoot "package.json"
$packageLock = Join-Path $mobileRoot "package-lock.json"
$nodeModules = Join-Path $mobileRoot "node_modules"
$hashMarker = Join-Path $nodeModules ".ahu-lock.sha256"

if (-not (Test-Path $packageJson)) {
    throw "mobile/package.json was not found."
}

$npmCommand = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npmCommand) {
    throw "npm was not found. Install Node.js 20+ and ensure npm is available in PATH."
}

$installRequired = -not (Test-Path $nodeModules)
$currentLockHash = $null
if (Test-Path $packageLock) {
    $currentLockHash = (Get-FileHash -Path $packageLock -Algorithm SHA256).Hash
    if (-not $installRequired -and (Test-Path $hashMarker)) {
        $savedLockHash = (Get-Content -Path $hashMarker -Raw -Encoding UTF8).Trim()
        if ($savedLockHash -ne $currentLockHash) {
            $installRequired = $true
        }
    }
    elseif (-not $installRequired) {
        $installRequired = $true
    }
}

if ($installRequired) {
    Write-Host "Installing mobile npm dependencies ..."
    Push-Location $mobileRoot
    & $npmCommand.Source install
    $exitCode = $LASTEXITCODE
    Pop-Location

    if ($exitCode -ne 0) {
        throw "npm install failed in mobile/."
    }

    if ($currentLockHash) {
        Set-Content -Path $hashMarker -Value $currentLockHash -Encoding UTF8
    }
}

Write-Host "Mobile npm dependencies are ready: $mobileRoot"
