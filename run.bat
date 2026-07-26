@echo off
setlocal enabledelayedexpansion

echo =========================================================
echo   Crewlyze - Autonomous Multi-Agent BI Platform Launcher
echo =========================================================
echo.

set "USER_HOME=%USERPROFILE%\.crewlyze"
set "VENV_PYTHON=%USER_HOME%\venv\Scripts\python.exe"

if exist "%VENV_PYTHON%" (
    echo [INFO] Found virtual environment Python: %VENV_PYTHON%
    "%VENV_PYTHON%" main.py
    exit /b %ERRORLEVEL%
)

REM Try Python 3.13 down to 3.9 via py launcher
for %%V in (3.13 3.12 3.11 3.10 3.9) do (
    py -%%V -c "import sys" >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo [INFO] Launching Crewlyze using Python %%V...
        py -%%V main.py
        exit /b !ERRORLEVEL!
    )
)

REM Fallback if no specific version launcher worked
echo [INFO] Launching Crewlyze using default system Python...
python main.py
if %ERRORLEVEL% NEQ 0 (
    py main.py
)
