param(
    [switch]$Apply,
    [string]$Date = ""
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $Date) {
    $Date = (Get-Date).ToString("yyyy-MM-dd")
}

function Resolve-TargetPath {
    param(
        [System.IO.FileInfo]$File
    )

    $name = $File.Name

    if ($name -match "(?i)^playwright-.*\.(png|jpg|jpeg|webp)$") {
        return Join-Path $projectRoot (Join-Path "artifacts\screenshots\playwright" (Join-Path $Date $name))
    }

    if ($name -match "(?i)(mobile|android|device).*\.(png|jpg|jpeg|webp)$") {
        return Join-Path $projectRoot (Join-Path "artifacts\screenshots\mobile" (Join-Path $Date $name))
    }

    if ($name -match "(?i)\.(png|jpg|jpeg|webp)$") {
        return Join-Path $projectRoot (Join-Path "artifacts\screenshots\manual" (Join-Path $Date $name))
    }

    if ($name -match "(?i)\.(err\.log|out\.log|log)$") {
        if ($name -match "(?i)cloudflare|tunnel") {
            return Join-Path $projectRoot (Join-Path "artifacts\logs\tunnel" (Join-Path $Date $name))
        }
        if ($name -match "(?i)mobile") {
            return Join-Path $projectRoot (Join-Path "artifacts\logs\mobile" (Join-Path $Date $name))
        }
        return Join-Path $projectRoot (Join-Path "artifacts\logs\local" (Join-Path $Date $name))
    }

    if ($name -match "(?i)\.cmd$") {
        return Join-Path $projectRoot (Join-Path "tooling\commands\windows" $name)
    }

    if ($name -match "(?i)\.exe$") {
        if ($name -match "(?i)cloudflared") {
            return Join-Path $projectRoot (Join-Path "tooling\bin\cloudflared" $name)
        }
        return Join-Path $projectRoot (Join-Path "tooling\bin\windows" $name)
    }

    return $null
}

$rootFiles = Get-ChildItem -Path $projectRoot -File
$plannedMoves = @()

foreach ($file in $rootFiles) {
    $targetPath = Resolve-TargetPath -File $file
    if ($null -eq $targetPath) {
        continue
    }

    $plannedMoves += [PSCustomObject]@{
        Source = $file.FullName
        Target = $targetPath
    }
}

if ($plannedMoves.Count -eq 0) {
    Write-Host "No root files matching migration rules were detected."
    exit 0
}

Write-Host "Planned root artifact moves: $($plannedMoves.Count)"
$plannedMoves |
    Group-Object {
        if ($_.Target -match "artifacts\\screenshots\\playwright") {
            "playwright"
        } elseif ($_.Target -match "artifacts\\screenshots\\mobile") {
            "screenshots-mobile"
        } elseif ($_.Target -match "artifacts\\screenshots") {
            "screenshots"
        } elseif ($_.Target -match "artifacts\\logs") {
            "logs"
        } elseif ($_.Target -match "tooling\\commands") {
            "commands"
        } elseif ($_.Target -match "tooling\\bin") {
            "binaries"
        } else {
            "other"
        }
    } |
    Select-Object Name, Count |
    Format-Table -AutoSize

$plannedMoves |
    Select-Object -First 30 Source, Target |
    Format-Table -AutoSize

if (-not $Apply) {
    Write-Host "Dry-run only. Re-run with -Apply to perform file moves."
    exit 0
}

foreach ($move in $plannedMoves) {
    $targetDir = Split-Path -Parent $move.Target
    if (-not (Test-Path $targetDir)) {
        New-Item -Path $targetDir -ItemType Directory -Force | Out-Null
    }

    Move-Item -Path $move.Source -Destination $move.Target -Force
}

Write-Host "Moved $($plannedMoves.Count) files from root into artifacts/tooling subfolders."
