param(
	[switch]$OpenDashboard
)

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

function Import-EnvironmentFile {
	param(
		[string]$Path
	)

	if (-not (Test-Path $Path)) {
		return
	}

	Get-Content $Path | ForEach-Object {
		$line = $_.Trim()
		if (-not $line -or $line.StartsWith("#")) {
			return
		}
		if ($line.StartsWith("export ")) {
			$line = $line.Substring(7).Trim()
		}

		$separatorIndex = $line.IndexOf("=")
		if ($separatorIndex -le 0) {
			throw "Invalid env line in $Path. Expected KEY=VALUE."
		}

		$key = $line.Substring(0, $separatorIndex).Trim()
		$value = $line.Substring($separatorIndex + 1).Trim()
		if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
			$value = $value.Substring(1, $value.Length - 2)
		}
		if (-not [Environment]::GetEnvironmentVariable($key, "Process")) {
			[Environment]::SetEnvironmentVariable($key, $value, "Process")
		}
	}
}

$environmentFile = Join-Path $projectRoot "config\local.env"
if ($env:AHU_SIMULATOR_ENV_FILE) {
	$environmentFile = $env:AHU_SIMULATOR_ENV_FILE
	if (-not [System.IO.Path]::IsPathRooted($environmentFile)) {
		$environmentFile = Join-Path $projectRoot $environmentFile
	}
}
Import-EnvironmentFile -Path $environmentFile

function Test-PortAvailable {
	param(
		[int]$Port
	)

	$listener = $null

	try {
		$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
		$listener.Start()
		return $true
	} catch {
		return $false
	} finally {
		if ($null -ne $listener) {
			$listener.Stop()
		}
	}
}

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
	$python = "python"
}

$preferredPort = 8000
if ($env:AHU_SIMULATOR_PORT) {
	$port = [int]$env:AHU_SIMULATOR_PORT
	if (-not (Test-PortAvailable -Port $port)) {
		throw "Requested port $port is unavailable. Set AHU_SIMULATOR_PORT to another port."
	}
} elseif ($env:PORT) {
	$port = [int]$env:PORT
	if (-not (Test-PortAvailable -Port $port)) {
		throw "Requested port $port is unavailable. Set PORT to another port."
	}
} else {
	$maxAttempts = 100
	$port = $null

	for ($candidate = $preferredPort; $candidate -lt ($preferredPort + $maxAttempts); $candidate++) {
		if (Test-PortAvailable -Port $candidate) {
			$port = $candidate
			break
		}
	}

	if ($null -eq $port) {
		throw "Unable to find a free port starting at $preferredPort."
	}

	if ($port -ne $preferredPort) {
		Write-Host "Port $preferredPort is unavailable, using $port instead."
	}
}

Write-Host "Starting Uvicorn server on http://127.0.0.1:$port"
$dashboardUrl = "http://127.0.0.1:$port/dashboard"
if ($OpenDashboard) {
	$launcherCode = "Start-Sleep -Seconds 2; Start-Process '$dashboardUrl'"
	Start-Process powershell -ArgumentList @(
		"-NoProfile"
		"-ExecutionPolicy"
		"Bypass"
		"-WindowStyle"
		"Hidden"
		"-Command"
		$launcherCode
	) | Out-Null
	Write-Host "Dashboard will open automatically: $dashboardUrl"
}

& $python -m uvicorn app.main:app --app-dir src --host 127.0.0.1 --port $port --reload
