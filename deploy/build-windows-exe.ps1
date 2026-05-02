param(
    [switch]$Clean
)

if ($PSVersionTable.PSEdition -ne "Desktop" -and $PSVersionTable.PSEdition -ne "Core") {
    throw "PowerShell is required to run this script."
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$pythonExecutable = if (Test-Path $venvPython) { $venvPython } else { "python" }
$versionResolverPath = Join-Path $scriptDir "resolve-release-version.ps1"
$specPath = Join-Path $projectRoot "deploy\ahu-simulator-desktop.spec"
$distPath = Join-Path $projectRoot "dist\windows-exe"
$workPath = Join-Path $projectRoot "build\pyinstaller"

if (-not (Test-Path $specPath)) {
    throw "Spec file not found: $specPath"
}

if (-not (Test-Path $versionResolverPath)) {
    throw "Version resolver script not found: $versionResolverPath"
}

if ($Clean) {
    if (Test-Path $distPath) {
        Remove-Item $distPath -Recurse -Force
    }
    if (Test-Path $workPath) {
        Remove-Item $workPath -Recurse -Force
    }
}

$releaseVersionOverride = $env:AHU_RELEASE_VERSION
$releaseInfo = & $versionResolverPath -ProjectRoot $projectRoot -Version $releaseVersionOverride

if (-not $releaseInfo) {
        throw "Failed to resolve release version."
}

New-Item -ItemType Directory -Path $workPath -Force | Out-Null
$windowsVersionFilePath = Join-Path $workPath "windows-version-info.txt"
$windowsVersionFileContent = @"
# UTF-8
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=($($releaseInfo.major), $($releaseInfo.minor), $($releaseInfo.patch), 0),
        prodvers=($($releaseInfo.major), $($releaseInfo.minor), $($releaseInfo.patch), 0),
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
        ),
    kids=[
        StringFileInfo(
            [
            StringTable(
                u'040904B0',
                [StringStruct(u'CompanyName', u'AHU Diploma Project'),
                StringStruct(u'FileDescription', u'AHU Simulator Desktop Launcher'),
                StringStruct(u'FileVersion', u'$($releaseInfo.normalizedVersion)'),
                StringStruct(u'InternalName', u'AhuSimulator'),
                StringStruct(u'OriginalFilename', u'AhuSimulator.exe'),
                StringStruct(u'ProductName', u'AHU Simulator'),
                StringStruct(u'ProductVersion', u'$($releaseInfo.normalizedVersion)')])
            ]),
        VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
    ]
)
"@
Set-Content -LiteralPath $windowsVersionFilePath -Value $windowsVersionFileContent -Encoding UTF8

$env:AHU_RELEASE_VERSION = $releaseInfo.normalizedVersion
$env:AHU_WINDOWS_VERSION_FILE = $windowsVersionFilePath

Push-Location $projectRoot
try {
        Write-Host "Resolved release version: $($releaseInfo.normalizedVersion)"
    Write-Host "Installing/updating PyInstaller..."
    & $pythonExecutable -m pip install --upgrade pyinstaller

    Write-Host "Building onedir bundle from spec..."
    & $pythonExecutable -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath "$distPath" `
        --workpath "$workPath" `
        "$specPath"

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed with exit code $LASTEXITCODE"
    }

    $bundleDir = Join-Path $distPath "AhuSimulator"
    Write-Host "Windows onedir build is ready: $bundleDir"
    Write-Host "Run smoke checklist: deploy/windows-exe-smoke-checklist.md"
    Write-Host "Run desktop binary: $bundleDir\AhuSimulator.exe"
}
finally {
    Pop-Location
}
