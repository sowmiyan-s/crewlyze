@echo off
echo ================================================================
echo   Agentic Data Analyst - Web Platform
echo   FastAPI + Vanilla Web UI  (no Streamlit)
echo ================================================================
echo.

cd /d "%~dp0"

echo Starting server on http://localhost:8000
echo Press Ctrl+C to stop.
echo.

REM Try to find a compatible Python version (3.10 to 3.13) via the py launcher
py -3.13 -c "import sys" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3.13 main.py
    goto end
)

py -3.12 -c "import sys" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3.12 main.py
    goto end
)

py -3.11 -c "import sys" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3.11 main.py
    goto end
)

py -3.10 -c "import sys" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3.10 main.py
    goto end
)

REM Fallback if no specific version launcher worked
python main.py
if %ERRORLEVEL% NEQ 0 (
    py main.py
)

:end
pause
