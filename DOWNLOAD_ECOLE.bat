@echo off
call "%~dp0RUN_COMMAND.bat" src.download_ecole %*
exit /b %errorlevel%
