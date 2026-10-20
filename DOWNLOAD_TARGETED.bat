@echo off
call "%~dp0RUN_COMMAND.bat" src.download_targeted %*
exit /b %errorlevel%
