$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

if (-not $env:AHU_SIMULATOR_RUNTIME_DIR) {
    if ($env:LOCALAPPDATA) {
        $env:AHU_SIMULATOR_RUNTIME_DIR = Join-Path $env:LOCALAPPDATA "AhuSimulator"
    } else {
        $env:AHU_SIMULATOR_RUNTIME_DIR = Join-Path $projectRoot "artifacts"
    }
}

$originalPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = Join-Path $projectRoot "src"
    & $python -m app.desktop_launcher
}
finally {
    $env:PYTHONPATH = $originalPythonPath
}
