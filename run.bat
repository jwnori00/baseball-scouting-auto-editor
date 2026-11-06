@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto :setup
where ffmpeg >nul 2>nul
if errorlevel 1 goto :setup
where ffprobe >nul 2>nul
if errorlevel 1 goto :setup
".venv\Scripts\python.exe" -c "import PySide6, cv2, numpy"
if errorlevel 1 goto :setup
".venv\Scripts\python.exe" -m gui
if errorlevel 1 pause
exit /b
:setup
echo Run setup_windows.bat first. FFmpeg and FFprobe must be on PATH.
pause
exit /b 1
