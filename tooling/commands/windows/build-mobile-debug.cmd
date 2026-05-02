@echo off
setlocal
for %%I in ("%~dp0\..\..\..") do set "PROJECT_ROOT=%%~fI"
cd /d "%PROJECT_ROOT%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\deploy\bootstrap-mobile.ps1"
if errorlevel 1 goto :end

powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\mobile\scripts\build-android.ps1" -Debug

:end
pause
