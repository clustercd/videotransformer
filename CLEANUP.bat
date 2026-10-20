@echo off
call "%~dp0RUN_COMMAND.bat" src.cleanup %*
exit /b %errorlevel%
