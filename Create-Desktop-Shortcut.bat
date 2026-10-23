@echo off
REM Creates a Desktop shortcut named "Kinito" with GameAssets\icons\Kinito.ico.
setlocal EnableExtensions
cd /d "%~dp0"

set "KINITO_PROJECT=%~dp0"
if "%KINITO_PROJECT:~-1%"=="\" set "KINITO_PROJECT=%KINITO_PROJECT:~0,-1%"
set "KINITO_LAUNCHER=%KINITO_PROJECT%\Start-Kinito.bat"
set "KINITO_ICON=%KINITO_PROJECT%\GameAssets\icons\Kinito.ico"
set "KINITO_PS1=%KINITO_PROJECT%\tools\Create-Desktop-Shortcut.ps1"

if not exist "%KINITO_LAUNCHER%" (
    echo Start-Kinito.bat not found next to this script.
    pause
    exit /b 1
)
if not exist "%KINITO_ICON%" (
    echo Icon not found:
    echo   %KINITO_ICON%
    echo.
    echo Build it with:
    echo   python tools\build_windows_icon.py
    pause
    exit /b 1
)
if not exist "%KINITO_PS1%" (
    echo Missing helper script:
    echo   %KINITO_PS1%
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%KINITO_PS1%" "%KINITO_PROJECT%" "%KINITO_LAUNCHER%" "%KINITO_ICON%"
if errorlevel 1 (
    echo Could not create the shortcut.
    pause
    exit /b 1
)

echo.
echo Done. Look for "Kinito" on your Desktop.
echo If Windows still shows the old blurry icon: delete the shortcut,
echo run this script again, then right-click the Desktop and choose Refresh.
pause
exit /b 0
