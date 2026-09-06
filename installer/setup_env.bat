@echo off
setlocal enabledelayedexpansion

echo ===================================================================
echo   Crewlyze - Automated Environment & Dependency Setup
echo ===================================================================
echo.

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "APP_DIR=%SCRIPT_DIR%"
set "USER_HOME=%USERPROFILE%\.crewlyze"
set "VENV_DIR=%USER_HOME%\venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"
set "REQ_FILE=%APP_DIR%\requirements.txt"
set "LOG_FILE=%USER_HOME%\setup.log"

if not exist "%USER_HOME%" (
    mkdir "%USER_HOME%" >nul 2>&1
)

echo [%DATE% %TIME%] Setup session started >> "%LOG_FILE%"

echo [1/4] Detecting Python 3.9 - 3.13 runtime...

set "FOUND_PYTHON="

REM Check py launcher for versions 3.13 down to 3.9
for %%V in (3.13 3.12 3.11 3.10 3.9) do (
    if not defined FOUND_PYTHON (
        py -%%V -c "import sys" >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            set "FOUND_PYTHON=py -%%V"
            echo       Found Python %%V via Python Launcher (py)
            goto :python_detected
        )
    )
)

REM Check default 'python' command
python -c "import sys; assert (3,9) <= sys.version_info[:2] <= (3,13)" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "FOUND_PYTHON=python"
    echo       Found system Python on PATH
    goto :python_detected
)

REM Check common local python installation paths
set "STD_PATH_1=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
set "STD_PATH_2=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
set "STD_PATH_3=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
set "STD_PATH_4=%ProgramFiles%\Python311\python.exe"
set "STD_PATH_5=%ProgramFiles%\Python310\python.exe"

if exist "%STD_PATH_1%" ( set "FOUND_PYTHON="%STD_PATH_1%"" & goto :python_detected )
if exist "%STD_PATH_2%" ( set "FOUND_PYTHON="%STD_PATH_2%"" & goto :python_detected )
if exist "%STD_PATH_3%" ( set "FOUND_PYTHON="%STD_PATH_3%"" & goto :python_detected )
if exist "%STD_PATH_4%" ( set "FOUND_PYTHON="%STD_PATH_4%"" & goto :python_detected )
if exist "%STD_PATH_5%" ( set "FOUND_PYTHON="%STD_PATH_5%"" & goto :python_detected )

REM If Python is not detected, download and install Python 3.11 64-bit silently
echo [WARN] No compatible Python (3.9 - 3.13) found.
echo        Downloading and installing official Python 3.11 runtime...
echo [%DATE% %TIME%] Attempting automated Python 3.11 install >> "%LOG_FILE%"

set "PY_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
set "PY_INSTALLER=%TEMP%\python-3.11.9-amd64.exe"

powershell -NoProfile -ExecutionPolicy Bypass -Command "Write-Host 'Downloading Python installer...'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%PY_URL%', '%PY_INSTALLER%')" >> "%LOG_FILE%" 2>&1

if exist "%PY_INSTALLER%" (
    echo        Installing Python 3.11 silently (please wait)...
    "%PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 SimpleInstall=1 >> "%LOG_FILE%" 2>&1
    del "%PY_INSTALLER%" >nul 2>&1
    
    REM Refresh PATH in current cmd
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
    if exist "%STD_PATH_1%" (
        set "FOUND_PYTHON="%STD_PATH_1%""
        echo [OK]   Python 3.11 installed successfully.
        goto :python_detected
    )
)

REM Last resort check
python -c "import sys" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "FOUND_PYTHON=python"
    goto :python_detected
)

echo [ERROR] Python could not be installed automatically.
echo         Please install Python 3.10 or 3.11 manually from https://www.python.org
pause
exit /b 1

:python_detected
echo [OK]   Selected Python: %FOUND_PYTHON%
echo [%DATE% %TIME%] Using Python: %FOUND_PYTHON% >> "%LOG_FILE%"

echo.
echo [2/4] Setting up isolated virtual environment in %VENV_DIR%...

if not exist "%VENV_PYTHON%" (
    echo       Creating virtual environment...
    %FOUND_PYTHON% -m venv "%VENV_DIR%" >> "%LOG_FILE%" 2>&1
    if not exist "%VENV_PYTHON%" (
        echo [ERROR] Failed to create virtual environment. See %LOG_FILE%
        pause
        exit /b 1
    )
)
echo [OK]   Virtual environment ready.

echo.
echo [3/4] Upgrading pip, setuptools, and wheel...
"%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel --quiet --no-warn-script-location >> "%LOG_FILE%" 2>&1

echo.
echo [4/4] Installing dependencies from requirements.txt...
echo       This may take a minute or two on first run...

if exist "%REQ_FILE%" (
    "%VENV_PYTHON%" -m pip install --no-input --prefer-binary -r "%REQ_FILE%" >> "%LOG_FILE%" 2>&1
) else (
    "%VENV_PYTHON%" -m pip install --no-input --prefer-binary fastapi uvicorn[standard] crewai pandas plotly python-dotenv requests reportlab >> "%LOG_FILE%" 2>&1
)

echo.
echo ===================================================================
echo [SUCCESS] Crewlyze environment setup complete!
echo ===================================================================
echo [%DATE% %TIME%] Setup completed successfully >> "%LOG_FILE%"
echo.
timeout /t 3 >nul 2>&1
exit /b 0
