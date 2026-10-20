@echo off
echo ======================================================================
echo SmartInsight - AI-Powered Document Search ^& Analytics Engine
echo ======================================================================

echo.
echo Option 1: Run with Docker Compose (Recommended)
echo   docker compose up --build
echo.
echo Option 2: Run Backend Locally
echo   cd backend
echo   python -m venv venv
echo   call venv\Scripts\activate
echo   pip install -r requirements.txt
echo   uvicorn app.main:app --reload --port 8000
echo.
echo Option 3: Run Frontend Locally
echo   cd frontend
echo   npm install
echo   npm run dev
echo.
echo ======================================================================
pause
