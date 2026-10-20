@echo off
call "%~dp0RUN_COMMAND.bat" src.test_quick %*
exit /b %errorlevel%
