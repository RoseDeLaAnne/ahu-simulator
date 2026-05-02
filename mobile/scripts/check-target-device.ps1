$adb = Get-Command adb -ErrorAction SilentlyContinue
if (-not $adb) {
    throw "adb was not found. Install Android Platform Tools and add adb to PATH."
}

Write-Host "Connected devices:"
& adb devices -l
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$connectedDevices = (& adb devices) |
    Select-String -Pattern "\tdevice$" |
    ForEach-Object { $_.Line.Split("`t")[0] }

if ($connectedDevices.Count -eq 0) {
    Write-Warning "No Android devices were detected."
    Write-Host "Enable USB debugging and authorize this computer on the phone."
    exit 1
}

foreach ($deviceId in $connectedDevices) {
    $model = (& adb -s $deviceId shell getprop ro.product.model).Trim()
    $androidVersion = (& adb -s $deviceId shell getprop ro.build.version.release).Trim()
    Write-Host "Device $deviceId | Model: $model | Android: $androidVersion"
}
