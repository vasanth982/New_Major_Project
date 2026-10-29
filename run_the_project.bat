@echo off
setlocal enabledelayedexpansion

title Checkup Buddy — Multi-Disease Health Analytics v2.1
echo =====================================================================
echo   Checkup Buddy - Multi-Disease Health Analytics  (v2.1)
echo   Standalone Launch & Environment Setup
echo =====================================================================
echo.

:: 1. Navigate to script directory
cd /d "%~dp0"

:: 2. Check for Virtual Environment
echo [1/3] Checking Python virtual environment...
set "VENV_DIR="

if exist ".venv\Scripts\activate.bat" (
    set "VENV_DIR=.venv"
) else if exist "venv\Scripts\activate.bat" (
    set "VENV_DIR=venv"
) else if exist "env\Scripts\activate.bat" (
    set "VENV_DIR=env"
)

if defined VENV_DIR (
    echo [+] Activating virtual environment '!VENV_DIR!'...
    call "!VENV_DIR!\Scripts\activate.bat"
) else (
    echo [!] No existing virtual environment found.
    echo [*] Checking for system Python...
    where python >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python is not installed or not in your PATH.
        echo Please install Python 3.10+ from https://python.org and add it to PATH.
        pause
        exit /b 1
    )
    
    echo [*] Creating local virtual environment in .venv...
    python -m venv .venv
    if exist ".venv\Scripts\activate.bat" (
        set "VENV_DIR=.venv"
        call ".venv\Scripts\activate.bat"
        echo [+] Created and activated .venv successfully.
    ) else (
        echo [!] Failed to create .venv; proceeding with system Python.
    )
)

echo.
:: 3. Check and Install Requirements
echo [2/3] Verifying dependencies from requirements.txt...
set "REQ_FILE="
if exist "requirements.txt" (
    set "REQ_FILE=requirements.txt"
) else if exist "Requirements.txt" (
    set "REQ_FILE=Requirements.txt"
)

if defined REQ_FILE (
    echo [*] Installing / updating dependencies from !REQ_FILE!...
    python -m pip install --quiet --upgrade pip
    python -m pip install --quiet -r "!REQ_FILE!"
    if errorlevel 1 (
        echo [WARNING] Some dependencies had warnings during installation.
    ) else (
        echo [+] Dependencies verified.
    )
) else (
    echo [!] Requirements file not found; skipping package check.
)

echo.
:: 4. Launch Streamlit Application
echo [3/3] Launching Checkup Buddy Web App...
echo [*] Starting Streamlit server on http://localhost:8501...
echo [*] Open your browser at: http://localhost:8501
echo.

python -m streamlit run app.py --server.port=8501

if errorlevel 1 (
    echo.
    echo [ERROR] The application exited with an error.
    pause
)
