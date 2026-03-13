@echo off
echo Starting AI Agent Battle Royale...
echo.
echo [1/3] Starting backend on http://localhost:8000
start "Battle Royale Backend" cmd /k "cd /d %~dp0 && python -m uvicorn backend.main:app --reload --port 8000"

timeout /t 2 /nobreak >nul

echo [2/3] Starting frontend on http://localhost:3000
start "Battle Royale Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo [3/3] Opening browser...
start http://localhost:3000

echo.
echo To run demo agent servers, open new terminals and run:
echo   python demo_agent_server.py --port 9001 --strategy aggressive
echo   python demo_agent_server.py --port 9002 --strategy survivalist
echo.
echo API docs: http://localhost:8000/docs
