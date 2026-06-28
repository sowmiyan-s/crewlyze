@echo off
rem -------------------------------------------------
rem Install project dependencies – Windows batch script
rem -------------------------------------------------

echo Updating pip...
python -m pip install --upgrade pip

echo Installing requirements...
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo -------------------------------------------------
    echo Dependency installation failed.
    echo Possible reasons:
    echo   • Missing Rust toolchain (required for tiktoken)
    echo   • Incompatible C compiler for regex
    echo.
    echo To resolve:
    echo   1. Install Rust: https://rustup.rs
    echo   2. Ensure Visual Studio Build Tools are up‑to‑date.
    echo   3. Run this script again.
    echo -------------------------------------------------
    exit /b 1
)
echo.
echo All dependencies installed successfully.
