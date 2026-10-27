@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv
  if errorlevel 1 goto fail
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
if not exist frontend\dist\index.html (
  pushd frontend
  call npm ci
  if errorlevel 1 (popd & goto fail)
  call npm run build
  if errorlevel 1 (popd & goto fail)
  popd
)
echo.
echo Open http://localhost:8000 in your browser. Press Ctrl+C to stop.
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
exit /b
:fail
echo Setup failed. Check that Python 3.12 or later and, if building, Node.js 22 are installed.
pause
exit /b 1
