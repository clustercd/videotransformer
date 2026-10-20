@echo off
call "%~dp0RUN_COMMAND.bat" src.organize_videos %*
exit /b %errorlevel%
