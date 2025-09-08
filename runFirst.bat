@echo off
REM --- Always run from current folder (where bat file is placed) ---
cd /d "%~dp0"

echo ===================================
echo   🚀 Running First_Run.py
echo ===================================
python "Don't_Touch\First_Run.py"

echo ===================================
echo   ✅ Done!
echo ===================================
pause
