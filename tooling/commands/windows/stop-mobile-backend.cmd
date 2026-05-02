@echo off
setlocal
for %%I in ("%~dp0\..\..\..") do set "PROJECT_ROOT=%%~fI"
cd /d "%PROJECT_ROOT%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\deploy\run-mobile-backend.ps1" -Down

pause
