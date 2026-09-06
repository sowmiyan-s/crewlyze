@echo off
REM Crewlyze Local Development Launcher
call "%~dp0installer\crewlyze.cmd" %*
exit /b %ERRORLEVEL%
