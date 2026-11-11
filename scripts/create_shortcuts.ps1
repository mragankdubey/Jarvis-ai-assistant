param(
    [string]$ExePath = "",
    [switch]$IncludeStartMenu = $true,
    [switch]$UseSignedLauncher = $false
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($ExePath)) {
    $ExePath = Join-Path $ProjectRoot "dist\JARVIS\JARVIS.exe"
}

$WshShell = New-Object -ComObject WScript.Shell

if ($UseSignedLauncher) {
    $PythonW = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
    $MainPy = Join-Path $ProjectRoot "main.py"
    $IconPath = Join-Path $ProjectRoot "assets\icons\jarvis.ico"
    if (-not (Test-Path $PythonW)) {
        Write-Error "Signed pythonw.exe not found at: $PythonW"
        exit 1
    }
    $Target = $PythonW
    $Args = "`"$MainPy`""
    $WorkDir = $ProjectRoot
} else {
    if (-not (Test-Path -Path $ExePath)) {
        Write-Error "JARVIS.exe not found at: $ExePath. Run build_windows.bat first."
        exit 1
    }
    $ExeFile = Get-Item $ExePath
    $Target = $ExeFile.FullName
    $Args = ""
    $WorkDir = $ExeFile.DirectoryName
    $IconPath = Join-Path $WorkDir "_internal\assets\icons\jarvis.ico"
    if (-not (Test-Path $IconPath)) {
        $IconPath = $ExeFile.FullName
    }
}

function New-JarvisShortcut([string]$ShortcutPath) {
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $Target
    if (-not [string]::IsNullOrWhiteSpace($Args)) {
        $Shortcut.Arguments = $Args
    }
    $Shortcut.WorkingDirectory = $WorkDir
    $Shortcut.IconLocation = "$IconPath,0"
    $Shortcut.Description = "J.A.R.V.I.S. - Just A Rather Very Intelligent System"
    $Shortcut.Save()
}

# 1. Desktop Shortcut
$DesktopDir = [Environment]::GetFolderPath("Desktop")
$DesktopShortcutPath = Join-Path $DesktopDir "J.A.R.V.I.S..lnk"
New-JarvisShortcut $DesktopShortcutPath
Write-Output "Created Desktop shortcut: $DesktopShortcutPath"

# 2. Optional Start Menu Shortcut
if ($IncludeStartMenu) {
    $StartMenuDir = [Environment]::GetFolderPath("Programs")
    $StartShortcutPath = Join-Path $StartMenuDir "J.A.R.V.I.S..lnk"
    New-JarvisShortcut $StartShortcutPath
    Write-Output "Created Start Menu shortcut: $StartShortcutPath"
}
