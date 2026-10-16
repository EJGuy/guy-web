@echo off
rem ===== API quota server launcher =====
where python >nul 2>nul
if errorlevel 1 (
  echo [Error] Python not found. Install Python and add it to PATH first.
  pause
  exit /b
)
start "QuotaServer" /min python "%~dp0quota_server.py"
echo Quota server started (http://127.0.0.1:8720)
timeout /t 2 >nul
exit
