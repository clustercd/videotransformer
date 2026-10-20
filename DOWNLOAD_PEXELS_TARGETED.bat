@echo off
call "%~dp0RUN_COMMAND.bat" src.download_pexels_targeted %*
exit /b %errorlevel%
