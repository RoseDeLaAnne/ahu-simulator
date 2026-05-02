param(
    [switch]$Debug,
    [switch]$ReleaseApk,
    [switch]$ReleaseAab,
    [switch]$SkipBackendProbe
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Import-EnvFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    foreach ($rawLine in Get-Content -Path $Path -Encoding UTF8) {
        $line = $rawLine.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            continue
        }

        $separatorIndex = $line.IndexOf("=")
        if ($separatorIndex -le 0) {
            continue
        }

        $name = $line.Substring(0, $separatorIndex).Trim()
        if (-not $name) {
            continue
        }

        $existing = Get-Item -Path "Env:$name" -ErrorAction SilentlyContinue
        if ($existing -and -not [string]::IsNullOrWhiteSpace($existing.Value)) {
            continue
        }

        $value = $line.Substring($separatorIndex + 1).Trim()
        $isSingleQuoted = $value.Length -ge 2 -and $value.StartsWith("'") -and $value.EndsWith("'")
        $isDoubleQuoted = $value.Length -ge 2 -and $value.StartsWith('"') -and $value.EndsWith('"')
        if ($isSingleQuoted -or $isDoubleQuoted) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        Set-Item -Path "Env:$name" -Value $value
    }
}

function Resolve-MobileBackendUri {
    $rawUrl = $env:MOBILE_BACKEND_HTTPS_URL
    if ([string]::IsNullOrWhiteSpace($rawUrl)) {
        throw "MOBILE_BACKEND_HTTPS_URL is not set. Create mobile/.env or set the environment variable before build."
    }

    $candidateUrl = $rawUrl.Trim()
    $backendUri = $null
    $isValidUri = [Uri]::TryCreate($candidateUrl, [UriKind]::Absolute, [ref]$backendUri)
    if (-not $isValidUri -or $null -eq $backendUri) {
        throw "MOBILE_BACKEND_HTTPS_URL is invalid: $candidateUrl"
    }

    if ($backendUri.Scheme -ne "https") {
        throw "MOBILE_BACKEND_HTTPS_URL must use HTTPS. Current value: $candidateUrl"
    }

    $placeholderHosts = @(
        "api.ahu-simulator.example",
        "ahu-simulator.example",
        "example.com",
        "www.example.com",
        "example.net",
        "www.example.net",
        "example.org",
        "www.example.org"
    )

    $reservedSuffixes = @(
        ".example",
        ".invalid",
        ".test",
        ".localhost"
    )

    $normalizedHost = $backendUri.Host.ToLowerInvariant()
    $isReservedHost = $false
    if ($placeholderHosts -contains $normalizedHost) {
        $isReservedHost = $true
    }
    else {
        foreach ($suffix in $reservedSuffixes) {
            $suffixToken = $suffix.TrimStart(".")
            if ($normalizedHost -eq $suffixToken -or $normalizedHost.EndsWith($suffix)) {
                $isReservedHost = $true
                break
            }
        }
    }

    if ($isReservedHost) {
        throw "MOBILE_BACKEND_HTTPS_URL points to placeholder/reserved host '$($backendUri.Host)'. Set a real backend URL."
    }

    return $backendUri
}

function Test-MobileBackendHealth {
    param(
        [Parameter(Mandatory = $true)]
        [Uri]$BackendUri
    )

    $builder = [UriBuilder]::new($BackendUri)
    $path = $builder.Path.TrimEnd("/")
    if ($path.EndsWith("/dashboard")) {
        $builder.Path = $path.Substring(0, $path.Length - "/dashboard".Length) + "/health"
    }
    elseif ([string]::IsNullOrWhiteSpace($path)) {
        $builder.Path = "/health"
    }
    else {
        $builder.Path = "$path/health"
    }
    $builder.Query = ""
    $healthUrl = $builder.Uri.AbsoluteUri

    try {
        $response = Invoke-WebRequest -Uri $healthUrl -Method Get -TimeoutSec 10
    }
    catch {
        throw "Mobile backend health probe failed for $healthUrl. $($_.Exception.Message)"
    }

    if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 400) {
        throw "Mobile backend health probe returned unexpected status code $($response.StatusCode) for $healthUrl"
    }

    Write-Host "Mobile backend health probe succeeded: $healthUrl (HTTP $($response.StatusCode))"

    $dashboardUrl = $BackendUri.AbsoluteUri
    try {
        $dashboardResponse = Invoke-WebRequest -Uri $dashboardUrl -Method Get -TimeoutSec 10
    }
    catch {
        throw "Mobile backend dashboard probe failed for $dashboardUrl. $($_.Exception.Message)"
    }

    if ($dashboardResponse.StatusCode -lt 200 -or $dashboardResponse.StatusCode -ge 400) {
        throw "Mobile backend dashboard probe returned unexpected status code $($dashboardResponse.StatusCode) for $dashboardUrl"
    }

    Write-Host "Mobile backend dashboard probe succeeded: $dashboardUrl (HTTP $($dashboardResponse.StatusCode))"
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$mobileRoot = Split-Path -Parent $scriptRoot
$projectRoot = Split-Path -Parent $mobileRoot
$androidRoot = Join-Path $mobileRoot "android"
$versionResolverPath = Join-Path $projectRoot "deploy\resolve-release-version.ps1"
$runningOnWindows = $env:OS -eq "Windows_NT"
$gradleWrapper = if ($runningOnWindows) {
    Join-Path $androidRoot "gradlew.bat"
}
else {
    Join-Path $androidRoot "gradlew"
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm is required for Android shell build."
}

$mobileEnvPath = Join-Path $mobileRoot ".env"
if (Test-Path $mobileEnvPath) {
    Import-EnvFile -Path $mobileEnvPath
}
elseif ([string]::IsNullOrWhiteSpace($env:MOBILE_BACKEND_HTTPS_URL)) {
    throw "Missing mobile/.env and MOBILE_BACKEND_HTTPS_URL is not set. Copy mobile/.env.example to mobile/.env and set a real HTTPS endpoint."
}

$mobileBackendUri = Resolve-MobileBackendUri
Write-Host "Using mobile backend URL: $($mobileBackendUri.AbsoluteUri)"
if ($SkipBackendProbe) {
    Write-Warning "SkipBackendProbe is enabled. Backend reachability check is skipped."
}
else {
    Test-MobileBackendHealth -BackendUri $mobileBackendUri
}

if (-not (Test-Path $versionResolverPath)) {
    throw "Version resolver script not found: $versionResolverPath"
}

$releaseVersionOverride = $env:AHU_RELEASE_VERSION
$releaseInfo = & $versionResolverPath -ProjectRoot $projectRoot -Version $releaseVersionOverride
if (-not $releaseInfo) {
    throw "Failed to resolve release version."
}

if (-not $env:AHU_ANDROID_VERSION_NAME) {
    $env:AHU_ANDROID_VERSION_NAME = $releaseInfo.androidVersionName
}
if (-not $env:AHU_ANDROID_VERSION_CODE) {
    $env:AHU_ANDROID_VERSION_CODE = [string]$releaseInfo.androidVersionCode
}

Write-Host "Resolved Android version: name=$($env:AHU_ANDROID_VERSION_NAME), code=$($env:AHU_ANDROID_VERSION_CODE)"

$javaHome = $env:JAVA_HOME
if (-not $javaHome -and $runningOnWindows) {
    $jdk21Candidate = Get-ChildItem "C:\Program Files\Microsoft" -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "jdk-21*" } |
        Sort-Object Name -Descending |
        Select-Object -First 1

    if ($jdk21Candidate) {
        $javaHome = $jdk21Candidate.FullName
    }
}

if ($javaHome) {
    $javaBin = Join-Path $javaHome "bin"
    $javaExecutable = if ($runningOnWindows) {
        Join-Path $javaBin "java.exe"
    }
    else {
        Join-Path $javaBin "java"
    }
    if (Test-Path $javaExecutable) {
        $pathSeparator = if ($runningOnWindows) { ";" } else { ":" }
        $env:JAVA_HOME = $javaHome
        $env:PATH = "$javaBin$pathSeparator$env:PATH"
    }
}

if (-not (Get-Command java -ErrorAction SilentlyContinue)) {
    throw "Java runtime was not found. Install JDK 21+ and set JAVA_HOME."
}

$sdkRoot = $env:ANDROID_SDK_ROOT
if (-not $sdkRoot) {
    $sdkRoot = $env:ANDROID_HOME
}

if (-not $sdkRoot) {
    $sdkCandidates = @()
    if ($runningOnWindows) {
        if ($env:LOCALAPPDATA) {
            $sdkCandidates += (Join-Path $env:LOCALAPPDATA "Android\Sdk")
        }
        $sdkCandidates += "C:\Android\Sdk"
    }
    else {
        if ($HOME) {
            $sdkCandidates += (Join-Path $HOME "Android/Sdk")
        }
        $sdkCandidates += "/usr/local/lib/android/sdk"
        $sdkCandidates += "/opt/android-sdk"
    }

    foreach ($candidatePath in $sdkCandidates) {
        if ($candidatePath -and (Test-Path $candidatePath)) {
            $sdkRoot = $candidatePath
            break
        }
    }
}

if (-not $sdkRoot -or -not (Test-Path $sdkRoot)) {
    throw "Android SDK was not found. Install SDK and set ANDROID_HOME or ANDROID_SDK_ROOT."
}

$env:ANDROID_SDK_ROOT = $sdkRoot
$env:ANDROID_HOME = $sdkRoot

Set-Location $mobileRoot

if (-not (Test-Path $gradleWrapper)) {
    Write-Host "Android project is missing, generating it via Capacitor..."
    & npx cap add android
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Write-Host "Synchronizing Capacitor Android project..."
& npx cap sync android
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$task = "assembleDebug"
if ($ReleaseApk) {
    $task = "assembleRelease"
}
if ($ReleaseAab) {
    $task = "bundleRelease"
}
if ($Debug) {
    $task = "assembleDebug"
}

Push-Location $androidRoot
if ($runningOnWindows) {
    & .\gradlew.bat $task
}
else {
    & ./gradlew $task
}
$exitCode = $LASTEXITCODE
Pop-Location

if ($exitCode -ne 0) {
    exit $exitCode
}

switch ($task) {
    "assembleDebug" {
        Write-Host "Debug APK: android/app/build/outputs/apk/debug/app-debug.apk"
    }
    "assembleRelease" {
        Write-Host "Release APK output: android/app/build/outputs/apk/release/app-release.apk (signed)"
        Write-Host "Release APK output: android/app/build/outputs/apk/release/app-release-unsigned.apk (unsigned)"
    }
    "bundleRelease" {
        Write-Host "Release AAB output: android/app/build/outputs/bundle/release/app-release.aab"
    }
}
