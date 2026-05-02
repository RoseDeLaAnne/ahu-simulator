param(
    [string]$BlenderExe = "",
    [string]$OutputGlb = "",
    [string]$OutputBlend = "",
    [string]$OutputPreview = ""
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ScriptPath = Join-Path $ProjectRoot "tooling\scene\build_blender_pvu.py"

if (-not $BlenderExe) {
    if ($env:BLENDER_EXE) {
        $BlenderExe = $env:BLENDER_EXE
    } else {
        $DefaultPath = "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
        if (Test-Path $DefaultPath) {
            $BlenderExe = $DefaultPath
        }
    }
}

if (-not $BlenderExe -or -not (Test-Path $BlenderExe)) {
    throw "Blender executable not found. Pass -BlenderExe or set BLENDER_EXE."
}

if (-not $OutputGlb) {
    $OutputGlb = Join-Path $ProjectRoot "data\visualization\assets\pvu_installation.glb"
}

if (-not $OutputBlend) {
    $OutputBlend = Join-Path $ProjectRoot "3d-references\pvu_parametric_generated.blend"
}

if (-not $OutputPreview) {
    $OutputPreview = Join-Path $ProjectRoot "3d-references\pvu_parametric_preview.png"
}

& $BlenderExe --background --python $ScriptPath -- --output-glb $OutputGlb --output-blend $OutputBlend --output-preview $OutputPreview

if ($LASTEXITCODE -ne 0) {
    throw "Blender build failed with exit code $LASTEXITCODE."
}

Write-Host "3D asset rebuilt:"
Write-Host "  GLB:   $OutputGlb"
Write-Host "  BLEND: $OutputBlend"
Write-Host "  PNG:   $OutputPreview"
