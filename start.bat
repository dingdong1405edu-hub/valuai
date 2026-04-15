@echo off
echo =============================================
echo   ValuAI - Starting Services
echo =============================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.

REM Start backend in a new window
start "ValuAI Backend" cmd /k "cd /d %~dp0valuai-backend && .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

REM Wait a moment then start frontend
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
start "ValuAI Frontend" cmd /k "cd /d %~dp0valuai-frontend && npm run dev"

echo.
echo Both services started in separate windows.
echo Press any key to exit this window...
pause >nul
