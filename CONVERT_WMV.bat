@echo off
call "%~dp0RUN_COMMAND.bat" src.convert_wmv %*
exit /b %errorlevel%
