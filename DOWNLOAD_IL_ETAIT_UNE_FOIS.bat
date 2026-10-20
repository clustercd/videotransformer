@echo off
call "%~dp0RUN_COMMAND.bat" src.download_il_etait_une_fois %*
exit /b %errorlevel%
