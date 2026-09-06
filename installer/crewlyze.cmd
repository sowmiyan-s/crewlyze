@echo off
setlocal enabledelayedexpansion

REM Crewlyze Global CLI Launcher for Windows
REM Enables running 'crewlyze' from any directory in CMD or PowerShell

set "CREWLYZE_HOME=%~dp0"
if "%CREWLYZE_HOME:~-1%"=="\" set "CREWLYZE_HOME=%CREWLYZE_HOME:~0,-1%"
if not exist "%CREWLYZE_HOME%\main.py" (
    if exist "%CREWLYZE_HOME%\..\main.py" (
        pushd "%CREWLYZE_HOME%\.."
        set "CREWLYZE_HOME=!CD!"
        popd
    )
)

if /i "%~1"=="update" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%CREWLYZE_HOME%\updater.ps1"
    exit /b %ERRORLEVEL%
)
if /i "%~1"=="--update" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%CREWLYZE_HOME%\updater.ps1"
    exit /b %ERRORLEVEL%
)
if /i "%~1"=="check-update" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%CREWLYZE_HOME%\updater.ps1" -CheckOnly
    exit /b %ERRORLEVEL%
)

set "USER_HOME=%USERPROFILE%\.crewlyze"
set "VENV_PYTHON=%USER_HOME%\venv\Scripts\python.exe"

REM Ensure user data and output folders exist
if not exist "%USER_HOME%\data" mkdir "%USER_HOME%\data" >nul 2>&1
if not exist "%USER_HOME%\outputs" mkdir "%USER_HOME%\outputs" >nul 2>&1

REM Check if environment is prepared
if not exist "%VENV_PYTHON%" (
    echo [Crewlyze] First-time setup detected. Initializing Python environment...
    call "%CREWLYZE_HOME%\setup_env.bat"
    if %ERRORLEVEL% NEQ 0 (
        echo [Crewlyze] Setup failed. Please check %USER_HOME%\setup.log
        exit /b %ERRORLEVEL%
    )
)

REM Run Crewlyze through virtual environment Python
if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" "%CREWLYZE_HOME%\main.py" %*
    exit /b %ERRORLEVEL%
)

REM Fallback to py launcher or system python if venv python missing
py -3 "%CREWLYZE_HOME%\main.py" %*
if %ERRORLEVEL% NEQ 0 (
    python "%CREWLYZE_HOME%\main.py" %*
)

exit /b %ERRORLEVEL%
