@echo off
echo Starting lecturewithkws...

:: Start Backend
start cmd /k "cd backend && venv\Scripts\activate && python -m uvicorn main:app --reload --port 8000"

:: Start Frontend
start cmd /k "cd frontend && npm run dev"

:: Wait a few seconds for servers to initialize
timeout /t 5 /nobreak > nul

:: Start Electron App
start cmd /k "cd electron-app && npm start"

echo.
echo All components are starting! 
echo Please keep the separate windows open while using the app.
echo You can close this window now.
pause
