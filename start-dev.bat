@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"
set "BACKEND_PYTHON=%BACKEND_DIR%\.venv\Scripts\python.exe"

if not exist "%BACKEND_PYTHON%" (
  echo [AI Portal] Backend Python was not found:
  echo %BACKEND_PYTHON%
  pause
  exit /b 1
)

if not exist "%FRONTEND_DIR%\package.json" (
  echo [AI Portal] Frontend package.json was not found:
  echo %FRONTEND_DIR%\package.json
  pause
  exit /b 1
)

start "AI Portal Backend" powershell.exe -NoExit -Command "$Host.UI.RawUI.WindowTitle = 'AI Portal Backend'; Set-Location -LiteralPath '%BACKEND_DIR%'; & '%BACKEND_PYTHON%' -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

start "AI Portal Frontend" powershell.exe -NoExit -Command "$Host.UI.RawUI.WindowTitle = 'AI Portal Frontend'; Set-Location -LiteralPath '%FRONTEND_DIR%'; & npm.cmd run dev -- --host 127.0.0.1 --port 5173"

timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:5173"

endlocal
