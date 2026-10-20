@echo off
call "%~dp0RUN_COMMAND.bat" src.download_wikimedia %*
exit /b %errorlevel%
