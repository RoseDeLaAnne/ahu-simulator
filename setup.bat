@echo off
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
set "SETUP_EXIT_CODE=%ERRORLEVEL%"

endlocal & exit /b %SETUP_EXIT_CODE%
