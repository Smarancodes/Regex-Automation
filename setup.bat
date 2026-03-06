@echo off
REM ============================================================
REM  setup.bat - One-click setup for PDF Regex Automation
REM  Run this ONCE before using the project.
REM ============================================================

setlocal
set "ROOT=%~dp0"
set "VENV=%ROOT%venv"

echo.
echo ============================================================
echo   PDF Regex Automation - Environment Setup
echo ============================================================
echo.

REM Step 1: Check Python
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python not found on PATH.
    echo   Install Python 3.9+ from https://www.python.org/downloads/
    echo   Make sure to tick "Add Python to PATH" during install.
    pause
    exit /b 1
)
python --version
echo   OK.
echo.

REM Step 2: Create virtual environment
echo [2/4] Creating virtual environment in venv\...
if exist "%VENV%\Scripts\python.exe" (
    echo   venv already exists, skipping creation.
) else (
    python -m venv "%VENV%"
    if errorlevel 1 (
        echo   ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo   OK.
)
echo.

REM Step 3: Install pip packages
echo [3/4] Installing Python packages (PyMuPDF, pytesseract, Pillow)...
"%VENV%\Scripts\pip" install --upgrade pip --quiet
"%VENV%\Scripts\pip" install -r "%ROOT%requirements.txt" --quiet
if errorlevel 1 (
    echo   ERROR: pip install failed. Check your internet connection.
    pause
    exit /b 1
)
echo   OK - packages installed.
echo.

REM Step 4: Check Tesseract (using Python to avoid batch parser issues)
echo [4/4] Checking Tesseract-OCR...
"%VENV%\Scripts\python" -c "import shutil, sys; t=shutil.which('tesseract'); print('  Tesseract found: '+t) if t else print('  NOTICE: Tesseract not found.\n  For digital PDFs: no action needed (native extraction is used).\n  For scanned PDFs: install from https://github.com/UB-Mannheim/tesseract/wiki')"
echo.

REM Done
echo ============================================================
echo   SETUP COMPLETE
echo   1. Drop your PDF files into:  input_pdfs\
echo   2. Edit regex patterns in:    config\patterns.json
echo   3. Run the pipeline:
echo      venv\Scripts\python src\pipeline.py
echo.
echo   To run the automated tests:
echo      venv\Scripts\python tests\test_pipeline.py
echo ============================================================
echo.
pause
