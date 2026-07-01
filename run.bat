@echo off
REM CrewAI requires Python 3.10-3.13 (not 3.14)

REM Try to find a compatible Python version (3.10 to 3.13) via the py launcher
py -3.13 -c "import sys" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3.13 main.py
    exit /b
)

py -3.12 -c "import sys" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3.12 main.py
    exit /b
)

py -3.11 -c "import sys" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3.11 main.py
    exit /b
)

py -3.10 -c "import sys" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3.10 main.py
    exit /b
)

REM Fallback if no specific version launcher worked
python main.py
if %ERRORLEVEL% NEQ 0 (
    py main.py
)

