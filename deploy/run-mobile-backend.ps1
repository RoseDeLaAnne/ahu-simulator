param(
    [switch]$Build,
    [switch]$Detached,
    [switch]$Down
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $PSScriptRoot "mobile-backend/docker-compose.mobile.yml"
$envFile = Join-Path $PSScriptRoot "mobile-backend/.env"

if (-not (Test-Path $composeFile)) {
    throw "Compose file was not found: $composeFile"
}

if (-not (Test-Path $envFile)) {
    throw "Missing env file: $envFile. Copy mobile-backend/.env.example to mobile-backend/.env and fill real values."
}

Set-Location $projectRoot

$composeArgs = @(
    "compose"
    "--env-file"
    $envFile
    "-f"
    $composeFile
)

if ($Down) {
    & docker @composeArgs "down"
    exit $LASTEXITCODE
}

$upArgs = @("up")
if ($Detached.IsPresent -or -not $PSBoundParameters.ContainsKey("Detached")) {
    $upArgs += "-d"
}
if ($Build) {
    $upArgs += "--build"
}

& docker @composeArgs @upArgs
exit $LASTEXITCODE
