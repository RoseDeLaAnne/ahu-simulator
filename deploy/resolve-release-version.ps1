param(
    [string]$ProjectRoot = "",
    [string]$Version = "",
    [switch]$AsJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $ProjectRoot) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$pyprojectPath = Join-Path $ProjectRoot "pyproject.toml"

function Get-VersionFromPyProject {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath
    )

    if (-not (Test-Path $FilePath)) {
        throw "pyproject.toml was not found: $FilePath"
    }

    $inProjectSection = $false
    foreach ($line in Get-Content -LiteralPath $FilePath) {
        if ($line -match "^\s*\[(?<section>[^\]]+)\]\s*$") {
            $inProjectSection = $Matches["section"] -eq "project"
            continue
        }

        if ($inProjectSection -and $line -match '^\s*version\s*=\s*"(?<version>[^"]+)"\s*$') {
            return $Matches["version"]
        }
    }

    throw "Could not resolve [project].version from $FilePath"
}

$resolvedVersion = if ($Version) { $Version } else { Get-VersionFromPyProject -FilePath $pyprojectPath }

if ($resolvedVersion -notmatch '^(?<major>\d+)\.(?<minor>\d+)\.(?<patch>\d+)(?:[-+].*)?$') {
    throw "Version '$resolvedVersion' must start with semantic version 'MAJOR.MINOR.PATCH'."
}

$major = [int]$Matches["major"]
$minor = [int]$Matches["minor"]
$patch = [int]$Matches["patch"]

$normalizedVersion = "$major.$minor.$patch"
$androidVersionCode = ($major * 10000) + ($minor * 100) + $patch

$result = [PSCustomObject]@{
    sourceVersion      = $resolvedVersion
    normalizedVersion  = $normalizedVersion
    major              = $major
    minor              = $minor
    patch              = $patch
    fileVersionTuple   = "$major, $minor, $patch, 0"
    androidVersionName = $normalizedVersion
    androidVersionCode = $androidVersionCode
}

if ($AsJson) {
    $result | ConvertTo-Json -Compress
}
else {
    $result
}