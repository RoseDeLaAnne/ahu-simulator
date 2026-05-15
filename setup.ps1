param(
    [switch]$Dev,
    [switch]$RunTests,
    [switch]$Start,
    [switch]$OpenDashboard
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
Set-Location $projectRoot

Write-Host "AHU Simulator setup"
Write-Host "Project root: $projectRoot"

$localEnv = Join-Path $projectRoot "config\local.env"
$localEnvExample = Join-Path $projectRoot "config\local.env.example"
if ((-not (Test-Path $localEnv)) -and (Test-Path $localEnvExample)) {
    Copy-Item -Path $localEnvExample -Destination $localEnv
    Write-Host "Created config\local.env from config\local.env.example"
}

$bootstrapArgs = @()
if ($Dev -or $RunTests) {
    $bootstrapArgs += "-InstallDevRequirements"
}

& (Join-Path $projectRoot "deploy\bootstrap-python.ps1") @bootstrapArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Expected virtual environment Python was not found: $python"
}

Write-Host ""
Write-Host "Environment is ready."
Write-Host "Python: $python"
Write-Host ""
Write-Host "Common commands:"
Write-Host "  .\start.bat"
Write-Host "  .\deploy\run-local.ps1 -OpenDashboard"
Write-Host "  .\.venv\Scripts\python.exe -m pytest"

if ($RunTests) {
    Write-Host ""
    Write-Host "Running tests ..."
    & $python -m pytest
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

if ($Start) {
    $runArgs = @()
    if ($OpenDashboard) {
        $runArgs += "-OpenDashboard"
    }

    Write-Host ""
    Write-Host "Starting local server ..."
    & (Join-Path $projectRoot "deploy\run-local.ps1") @runArgs
}
