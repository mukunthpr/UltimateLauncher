[Setup]
AppName=Ultimate Launcher
AppVersion=1.0.0
AppPublisher=Mukunth P.R
AppPublisherURL=https://github.com/mukunthpr/UltimateLauncher
DefaultDirName={localappdata}\UltimateLauncher
DefaultGroupName=Ultimate Launcher
OutputDir=dist\setup
OutputBaseFilename=UltimateLauncher_Setup
UninstallDisplayIcon={app}\UltimateLauncher.exe
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
DisableProgramGroupPage=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startup"; Description: "Automatically start Ultimate Launcher at login"; GroupDescription: "System Requirements"

[Files]
Source: "dist\UltimateLauncher\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Ultimate Launcher"; Filename: "{app}\UltimateLauncher.exe"
Name: "{autodesktop}\Ultimate Launcher"; Filename: "{app}\UltimateLauncher.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Ultimate Launcher"; ValueData: """{app}\UltimateLauncher.exe"""; Tasks: startup

[Run]
Filename: "{app}\UltimateLauncher.exe"; Description: "Launch Ultimate Launcher now"; Flags: nowait postinstall skipifsilent
