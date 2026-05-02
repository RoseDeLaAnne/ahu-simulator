param(
    [string]$IsccPath = "",
    [switch]$SkipExeBuild
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path
$versionResolverPath = Join-Path $scriptDir "resolve-release-version.ps1"
$specPath = Join-Path $projectRoot "deploy\installer\ahu-simulator.iss"
$bundleExe = Join-Path $projectRoot "dist\windows-exe\AhuSimulator\AhuSimulator.exe"

if (-not (Test-Path $versionResolverPath)) {
    throw "Version resolver script not found: $versionResolverPath"
}

$releaseVersionOverride = $env:AHU_RELEASE_VERSION
$releaseInfo = & $versionResolverPath -ProjectRoot $projectRoot -Version $releaseVersionOverride
$releaseVersion = $releaseInfo.normalizedVersion

if (-not $SkipExeBuild) {
    & (Join-Path $projectRoot "deploy\build-windows-exe.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "Windows EXE build failed."
    }
}

if (-not (Test-Path $bundleExe)) {
    throw "Onedir bundle is missing: $bundleExe"
}

$resolvedIscc = $IsccPath
if (-not $resolvedIscc) {
    $candidatePaths = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )
    $resolvedIscc = $candidatePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $resolvedIscc) {
    throw "ISCC.exe was not found. Install Inno Setup 6 or pass -IsccPath."
}

Push-Location $projectRoot
try {
    Write-Host "Building installer version: $releaseVersion"
    & "$resolvedIscc" "/DMyAppVersion=$releaseVersion" "$specPath"
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup build failed with exit code $LASTEXITCODE"
    }

    Write-Host "Installer build completed."
    Write-Host "Output directory: dist/installer"
}
finally {
    Pop-Location
}
