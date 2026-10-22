@echo off
REM Creates a Desktop shortcut named "Kinito" with the project Icon.ico.
setlocal
cd /d "%~dp0"

set "KINITO_PROJECT=%~dp0"
if "%KINITO_PROJECT:~-1%"=="\" set "KINITO_PROJECT=%KINITO_PROJECT:~0,-1%"
set "KINITO_LAUNCHER=%KINITO_PROJECT%\Start-Kinito.bat"
set "KINITO_ICON=%KINITO_PROJECT%\GameAssets\icons\Icon.ico"

if not exist "%KINITO_LAUNCHER%" (
    echo Start-Kinito.bat not found next to this script.
    pause
    exit /b 1
)
if not exist "%KINITO_ICON%" (
    echo Icon not found:
    echo   %KINITO_ICON%
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "$desktop = [Environment]::GetFolderPath('Desktop');" ^
  "$path = Join-Path $desktop 'Kinito.lnk';" ^
  "$lnk = $ws.CreateShortcut($path);" ^
  "$lnk.TargetPath = $env:KINITO_LAUNCHER;" ^
  "$lnk.WorkingDirectory = $env:KINITO_PROJECT;" ^
  "$lnk.IconLocation = $env:KINITO_ICON;" ^
  "$lnk.Description = 'Start Kinito';" ^
  "$lnk.Save();" ^
  "Write-Host ('Desktop shortcut ready: ' + $path)"

if errorlevel 1 (
    echo Could not create the shortcut.
    pause
    exit /b 1
)

echo.
echo Done. Look for "Kinito" on your Desktop.
pause
exit /b 0
