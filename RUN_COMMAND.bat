@echo off
setlocal
cd /d "%~dp0"
if not exist "videotrans\Scripts\python.exe" (
    echo Run INSTALL.bat first.
    exit /b 1
)
"videotrans\Scripts\python.exe" -m %*
exit /b %errorlevel%
