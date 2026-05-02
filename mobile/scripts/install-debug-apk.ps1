param(
    [string]$DeviceId,
    [switch]$Build,
    [switch]$NoLaunch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$mobileRoot = Split-Path -Parent $scriptRoot
$apkPath = Join-Path $mobileRoot "android\app\build\outputs\apk\debug\app-debug.apk"
$packageId = "com.ahusimulator.mobile"

if ($Build) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $scriptRoot "build-android.ps1") -Debug
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

if (-not (Test-Path $apkPath)) {
    throw "Debug APK was not found: $apkPath. Run build first or pass -Build."
}

$adb = Get-Command adb -ErrorAction SilentlyContinue
if (-not $adb) {
    throw "adb was not found. Install Android Platform Tools and add adb to PATH."
}

$connectedDevices = (& $adb.Source devices) |
    Select-String -Pattern "\tdevice$" |
    ForEach-Object { $_.Line.Split("`t")[0] }

if ($connectedDevices.Count -eq 0) {
    throw "No Android devices are connected. Enable USB debugging and authorize this computer."
}

$selectedDevice = $DeviceId
if ([string]::IsNullOrWhiteSpace($selectedDevice)) {
    if ($connectedDevices.Count -gt 1) {
        $deviceList = $connectedDevices -join ", "
        throw "More than one Android device is connected: $deviceList. Re-run with -DeviceId <serial>."
    }

    $selectedDevice = $connectedDevices[0]
}
elseif ($connectedDevices -notcontains $selectedDevice) {
    $deviceList = $connectedDevices -join ", "
    throw "Requested device '$selectedDevice' is not connected. Connected devices: $deviceList"
}

$model = (& $adb.Source -s $selectedDevice shell getprop ro.product.model).Trim()
Write-Host "Installing debug APK on $selectedDevice ($model) ..."
& $adb.Source -s $selectedDevice install -r $apkPath
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if (-not $NoLaunch) {
    Write-Host "Launching $packageId on $selectedDevice ..."
    & $adb.Source -s $selectedDevice shell monkey -p $packageId -c android.intent.category.LAUNCHER 1 | Out-Null
}

Write-Host "Installed APK: $apkPath"
