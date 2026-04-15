@echo off
echo =============================================
echo   ValuAI - Setup Script
echo =============================================
echo.

REM Check Python
python --version 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.12 from https://python.org
    echo After installing, re-run this script.
    pause
    exit /b 1
)

echo [1/4] Creating Python virtual environment...
cd valuai-backend
python -m venv .venv

echo [2/4] Installing backend dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt
cd ..

echo [3/4] Installing frontend dependencies...
cd valuai-frontend
npm install
cd ..

echo [4/4] Setup complete!
echo.
echo =============================================
echo   To start the application:
echo   Run start.bat
echo =============================================
pause
