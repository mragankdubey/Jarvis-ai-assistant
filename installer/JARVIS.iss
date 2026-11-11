; Inno Setup Script for J.A.R.V.I.S. Windows Desktop AI Assistant
; Compile with Inno Setup 6 (ISCC.exe) after building dist\JARVIS via build_windows.bat.
; Note: User data in %LOCALAPPDATA%\JARVIS\ (SQLite database, notes, .env, logs)
; is intentionally preserved on normal uninstall and across application updates.

#define MyAppName "J.A.R.V.I.S."
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Stark Industries OS"
#define MyAppExeName "JARVIS.exe"

[Setup]
AppId={{8F2A91B4-4E2F-4E9B-812A-4D7E91A0C301}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\JARVIS
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist\installer
OutputBaseFilename=JARVIS_Setup_{#MyAppVersion}
SetupIconFile=..\assets\icons\jarvis.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\JARVIS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\_internal\assets\icons\jarvis.ico"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\_internal\assets\icons\jarvis.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
