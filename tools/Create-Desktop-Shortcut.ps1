# Creates/replaces Desktop\Kinito.lnk with the high-res transparent icon.
param(
    [Parameter(Mandatory = $true)][string]$ProjectDir,
    [Parameter(Mandatory = $true)][string]$LauncherPath,
    [Parameter(Mandatory = $true)][string]$IconPath
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $LauncherPath)) {
    throw "Launcher not found: $LauncherPath"
}
if (-not (Test-Path -LiteralPath $IconPath)) {
    throw "Icon not found: $IconPath"
}

$desktop = [Environment]::GetFolderPath("Desktop")
$path = Join-Path $desktop "Kinito.lnk"
if (Test-Path -LiteralPath $path) {
    Remove-Item -LiteralPath $path -Force
}

$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut($path)
$lnk.TargetPath = $LauncherPath
$lnk.WorkingDirectory = $ProjectDir
# ",0" selects the first icon resource; helps Explorer pick up a fresh ICO.
$lnk.IconLocation = "$IconPath,0"
$lnk.Description = "Start Kinito"
$lnk.Save()

Write-Host "Desktop shortcut ready: $path"
Write-Host "Icon: $IconPath"
