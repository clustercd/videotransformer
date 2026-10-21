@echo off
call "%~dp0RUN_COMMAND.bat" copy_to_media_library %*
exit /b %errorlevel%
