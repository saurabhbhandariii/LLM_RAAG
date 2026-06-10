@echo off
echo ========================================
echo   Multi-PDF RAG - Quick Start (Windows)
echo ========================================
echo.


python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://python.org
    pause
    exit /b
)


if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate


echo Installing dependencies...
pip install -r requirements.txt --quiet

echo.
echo Starting app at http://localhost:8501
echo Press Ctrl+C to stop.
echo.
streamlit run app.py
