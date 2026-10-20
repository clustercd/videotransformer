@echo off
call "%~dp0RUN_COMMAND.bat" src.download_cest_pas_sorcier %*
exit /b %errorlevel%
