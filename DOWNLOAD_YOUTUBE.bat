@echo off
call "%~dp0RUN_COMMAND.bat" src.download_youtube_cc %*
exit /b %errorlevel%
