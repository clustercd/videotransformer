@echo off
call "%~dp0RUN_COMMAND.bat" src.video_analyzer_light %*
exit /b %errorlevel%
