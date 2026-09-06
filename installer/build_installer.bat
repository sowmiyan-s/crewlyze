@echo off
setlocal

echo ===================================================================
echo   Crewlyze - Windows Inno Setup Package Builder
echo ===================================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "ISS_FILE=%SCRIPT_DIR%crewlyze_installer.iss"

where node >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Ensuring installer and codebase versions are synchronized...
    node "%SCRIPT_DIR%..\bin\sync-version.js"
    echo.
)

if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" goto :found_x86
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" goto :found_pf

where iscc.exe >nul 2>&1
if not errorlevel 1 goto :found_path

echo [ERROR] Inno Setup 6 compiler (ISCC.exe) not found!
echo         Please install Inno Setup 6 from https://jrsoftware.org/isdl.php
exit /b 1

:found_x86
set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
goto :compile

:found_pf
set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
goto :compile

:found_path
set "ISCC=iscc.exe"
goto :compile

:compile
echo [INFO] Using Inno Setup compiler: "%ISCC%"
echo [INFO] Compiling installer script: "%ISS_FILE%"...
echo.

"%ISCC%" "%ISS_FILE%"

if errorlevel 1 (
    echo.
    echo [ERROR] Inno Setup compilation failed!
    exit /b 1
)

echo.
echo ===================================================================
echo [SUCCESS] Installer successfully built!
echo           Installer executable: %SCRIPT_DIR%dist\Crewlyze_Setup_v1.2.3.exe
echo ===================================================================

exit /b 0
