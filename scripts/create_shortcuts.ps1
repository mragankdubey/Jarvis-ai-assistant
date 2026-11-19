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
    $ShortcutArgs = "`"$MainPy`""
    $WorkDir = $ProjectRoot
} else {
    if (-not (Test-Path -Path $ExePath)) {
        Write-Error "JARVIS.exe not found at: $ExePath. Run build_windows.bat first."
        exit 1
    }
    $ExeFile = Get-Item $ExePath
    $Target = $ExeFile.FullName
    $ShortcutArgs = ""
    $WorkDir = $ExeFile.DirectoryName
    $IconPath = Join-Path $WorkDir "_internal\assets\icons\jarvis.ico"
    if (-not (Test-Path $IconPath)) {
        $IconPath = $ExeFile.FullName
    }
}

function New-JarvisShortcut(
    [string]$ShortcutPath,
    [string]$TargetExe,
    [string]$ArgumentsString,
    [string]$WorkingDirectory,
    [string]$IconFilePath
) {
    $ParentDir = Split-Path -Parent $ShortcutPath
    if (-not [string]::IsNullOrWhiteSpace($ParentDir) -and -not (Test-Path $ParentDir)) {
        New-Item -ItemType Directory -Path $ParentDir -Force | Out-Null
    }
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $TargetExe
    if (-not [string]::IsNullOrWhiteSpace($ArgumentsString)) {
        $Shortcut.Arguments = $ArgumentsString
    } else {
        $Shortcut.Arguments = ""
    }
    $Shortcut.WorkingDirectory = $WorkingDirectory
    $Shortcut.IconLocation = "$IconFilePath,0"
    $Shortcut.Description = "J.A.R.V.I.S. - Just A Rather Very Intelligent System"
    $Shortcut.Save()
}

# 1. Desktop Shortcuts (supports OneDrive Desktop and UserProfile Desktop)
$DesktopDirs = @()
$SystemDesktop = [Environment]::GetFolderPath("Desktop")
if (-not [string]::IsNullOrWhiteSpace($SystemDesktop) -and (Test-Path $SystemDesktop)) {
    $DesktopDirs += $SystemDesktop
}
if ($env:USERPROFILE) {
    $ProfileDesktop = Join-Path $env:USERPROFILE "Desktop"
    if ((Test-Path $ProfileDesktop) -and ($DesktopDirs -notcontains $ProfileDesktop)) {
        $DesktopDirs += $ProfileDesktop
    }
}

foreach ($d in $DesktopDirs) {
    $DesktopShortcutPath = Join-Path $d "J.A.R.V.I.S..lnk"
    New-JarvisShortcut $DesktopShortcutPath $Target $ShortcutArgs $WorkDir $IconPath
    Write-Output "Created Desktop shortcut: $DesktopShortcutPath"
}

# 2. Optional Start Menu Shortcut
if ($IncludeStartMenu) {
    $StartMenuDir = [Environment]::GetFolderPath("Programs")
    if (-not [string]::IsNullOrWhiteSpace($StartMenuDir)) {
        $StartShortcutPath = Join-Path $StartMenuDir "J.A.R.V.I.S..lnk"
        New-JarvisShortcut $StartShortcutPath $Target $ShortcutArgs $WorkDir $IconPath
        Write-Output "Created Start Menu shortcut: $StartShortcutPath"
    }
}
