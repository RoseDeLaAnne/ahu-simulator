@echo off
setlocal
for %%I in ("%~dp0\..\..\..") do set "PROJECT_ROOT=%%~fI"
cd /d "%PROJECT_ROOT%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\deploy\bootstrap-python.ps1"
if errorlevel 1 goto :end

powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\deploy\run-local.ps1" -OpenDashboard

:end
pause
