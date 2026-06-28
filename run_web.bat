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

python main.py
pause
