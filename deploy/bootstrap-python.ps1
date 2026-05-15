param(
    [switch]$InstallDevRequirements
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

function Resolve-SystemPython {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        foreach ($versionSelector in @("-3.12", "-3")) {
            try {
                & $pyLauncher.Source $versionSelector -c "import sys; print(sys.executable)"
                if ($LASTEXITCODE -eq 0) {
                    return @{
                        Command = $pyLauncher.Source
                        Arguments = @($versionSelector)
                    }
                }
            }
            catch {
            }
        }
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return @{
            Command = $pythonCommand.Source
            Arguments = @()
        }
    }

    throw "Python 3.12+ was not found. Install Python and ensure 'py' or 'python' is available in PATH."
}

function Test-PythonModules {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonExe,

        [Parameter(Mandatory = $true)]
        [string[]]$Modules
    )

    foreach ($module in $Modules) {
        & $PythonExe -c "import $module" 2>$null
        if ($LASTEXITCODE -ne 0) {
            return $false
        }
    }

    return $true
}

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $bootstrapPython = Resolve-SystemPython
    Write-Host "Creating virtual environment in .venv ..."
    & $bootstrapPython.Command @($bootstrapPython.Arguments + @("-m", "venv", ".venv"))
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create virtual environment."
    }
}

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment bootstrap failed: $venvPython was not created."
}

$runtimeModules = @(
    "a2wsgi",
    "dash",
    "fastapi",
    "numpy",
    "plotly",
    "pydantic",
    "reportlab",
    "uvicorn",
    "yaml"
)

if (-not (Test-PythonModules -PythonExe $venvPython -Modules $runtimeModules)) {
    Write-Host "Installing Python dependencies from requirements.txt ..."
    & $venvPython -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install Python dependencies."
    }
}

if ($InstallDevRequirements) {
    $devModules = @("httpx", "PyInstaller", "pytest")
    if (-not (Test-PythonModules -PythonExe $venvPython -Modules $devModules)) {
        Write-Host "Installing development dependencies ..."
        & $venvPython -m pip install ".[dev]"
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install development dependencies."
        }
    }
}

Write-Host "Python environment is ready: $venvPython"
