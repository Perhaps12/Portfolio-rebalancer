@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Could not find the project virtual environment at .venv\Scripts\python.exe
    echo Create it first, then install dependencies with:
    echo .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

start "Portfolio Rebalancer Backend" cmd /k "cd /d "%~dp0" && .venv\Scripts\python.exe -m uvicorn backend.backend:app --reload"
start "Portfolio Rebalancer Frontend" cmd /k "cd /d "%~dp0" && .venv\Scripts\python.exe -m streamlit run frontend\frontend.py"

endlocal
