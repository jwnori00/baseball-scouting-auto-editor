@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_LAUNCH=py -3.12"
%PYTHON_LAUNCH% -V >nul 2>nul
if errorlevel 1 set "PYTHON_LAUNCH=py -3"
%PYTHON_LAUNCH% -c "import sys; assert (3,11) <= sys.version_info[:2] <= (3,13), 'Install Python 3.12 (supported: 3.11-3.13)'"
if errorlevel 1 goto :fail
where ffmpeg >nul 2>nul
if errorlevel 1 goto :ffmpeg
where ffprobe >nul 2>nul
if errorlevel 1 goto :ffmpeg
if not exist ".venv\Scripts\python.exe" %PYTHON_LAUNCH% -m venv .venv
if errorlevel 1 goto :fail
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :fail
".venv\Scripts\python.exe" -m pip check
if errorlevel 1 goto :fail
echo Setup complete. Run run.bat.
pause
exit /b 0
:ffmpeg
echo Install FFmpeg and FFprobe, add their bin directory to PATH, then retry.
goto :fail
:fail
echo Setup failed. Install Python 3.12 from python.org and review the error above.
pause
exit /b 1
