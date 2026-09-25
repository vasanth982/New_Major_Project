#!/usr/bin/env bash
# =====================================================================
#  Checkup Buddy — Multi-Disease Health Analytics
#  Standalone Launch & Environment Setup  (v2.1)
# =====================================================================

set -e

# Change directory to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================================================="
echo "          Checkup Buddy - Multi-Disease Health Analytics"
echo "               Unix / macOS Launch & Environment Setup"
echo "====================================================================="
echo ""

# 1. Virtual Environment Check
echo "[1/3] Checking Python virtual environment..."
VENV_DIR=""

if [ -f ".venv/bin/activate" ]; then
    VENV_DIR=".venv"
elif [ -f "venv/bin/activate" ]; then
    VENV_DIR="venv"
elif [ -f "env/bin/activate" ]; then
    VENV_DIR="env"
fi

if [ -n "$VENV_DIR" ]; then
    echo "[+] Activating virtual environment '$VENV_DIR'..."
    # shellcheck disable=SC1090
    source "$VENV_DIR/bin/activate"
else
    echo "[!] No active virtual environment found."
    if command -v python3 >/dev/null 2>&1; then
        echo "[*] Creating local virtual environment in .venv..."
        python3 -m venv .venv || true
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
            echo "[+] Activated .venv successfully."
        fi
    elif command -v python >/dev/null 2>&1; then
        echo "[*] Creating local virtual environment in .venv..."
        python -m venv .venv || true
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
            echo "[+] Activated .venv successfully."
        fi
    else
        echo "[ERROR] Python 3 is not installed or not in PATH."
        exit 1
    fi
fi

echo ""
# 2. Verify and Install Requirements
echo "[2/3] Checking dependencies from requirements.txt..."
REQ_FILE=""
if [ -f "Requirements.txt" ]; then
    REQ_FILE="Requirements.txt"
elif [ -f "requirements.txt" ]; then
    REQ_FILE="requirements.txt"
fi

if [ -n "$REQ_FILE" ]; then
    echo "[*] Installing / verifying dependencies from $REQ_FILE..."
    pip install --quiet --upgrade pip || true
    pip install --quiet -r "$REQ_FILE"
    echo "[+] Dependencies verified."
fi

echo ""
# 3. Launch Streamlit Application
echo "[3/3] Launching Checkup Buddy Web App..."
echo "[*] Starting Streamlit server on http://localhost:8501..."
echo "[*] Open your browser and go to: http://localhost:8501"
echo ""

# Use python -m streamlit for maximum portability across venvs
if command -v python3 > /dev/null 2>&1; then
    python3 -m streamlit run app.py --server.port=8501
elif command -v python > /dev/null 2>&1; then
    python -m streamlit run app.py --server.port=8501
else
    streamlit run app.py --server.port=8501
fi
