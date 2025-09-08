@echo off
REM --- Always run from current folder (where bat file is placed) ---
cd /d "%~dp0"

echo ===================================
echo    Logging out from Naukri.com
echo ===================================
python "Don't_Touch\Logout.py"

echo ===================================
echo    Logging in to Naukri.com
echo ===================================
python "Don't_Touch\Login.py"

echo ===================================
echo    Done!
echo ===================================
pause
