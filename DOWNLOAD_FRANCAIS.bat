@echo off
call "%~dp0RUN_COMMAND.bat" src.download_francais %*
exit /b %errorlevel%
