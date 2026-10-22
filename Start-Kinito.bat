@echo off
REM Double-click launcher for Kinito (no terminal/IDE needed).
REM Requires Step 4–5 from docs/INSTALL.md (.venv + dependencies).

cd /d "%~dp0"

if not exist "%~dp0.venv\Scripts\pythonw.exe" (
    echo.
    echo Kinito cannot start: .venv is missing.
    echo Follow docs\INSTALL.md Steps 4 and 5 first.
    echo.
    pause
    exit /b 1
)

start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0Kinito.py"
exit /b 0
