@echo off
cd /d D:\MyPersonalPensieve\frontend
start "Vite" cmd /k "npx vite --host 0.0.0.0"
cd /d D:\MyPersonalPensieve\backend
start "Uvicorn" cmd /k ".venv\Scripts\uvicorn.exe app.main:app --port 8000"
exit
