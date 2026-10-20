@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>&1
if errorlevel 1 (
    echo Python 3.10 or newer is required.
    exit /b 1
)
if not exist "videotrans\Scripts\python.exe" (
    python -m venv videotrans
    if errorlevel 1 exit /b 1
)
"videotrans\Scripts\python.exe" -m pip install -r requirements-web.txt
if errorlevel 1 exit /b 1
echo Dashboard dependencies installed. Run START.bat.
echo Optional AI analysis: videotrans\Scripts\python.exe -m pip install -r requirements.txt
exit /b 0
