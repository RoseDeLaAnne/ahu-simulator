$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$pythonExecutable = if (Test-Path $venvPython) { $venvPython } else { "python" }
$originalPythonPath = $env:PYTHONPATH

Push-Location $projectRoot
try {
    $env:PYTHONPATH = Join-Path $projectRoot "src"
    @'
from pathlib import Path

from app.infrastructure.settings import get_settings
from app.services.demo_readiness_service import DemoReadinessService

project_root = Path.cwd()
service = DemoReadinessService(
    project_root=project_root,
    dashboard_path=get_settings().dashboard_path,
)
result = service.build_demo_package()
print(result.summary)
print(result.bundle_path)
print(result.manifest_path)
'@ | & $pythonExecutable -
}
finally {
    $env:PYTHONPATH = $originalPythonPath
    Pop-Location
}
