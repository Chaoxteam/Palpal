[Setup]
AppId=PalPal.LocalStudyBuddy
AppName=PalPal
AppVersion=0.2.0
DefaultDirName={localappdata}\Programs\PalPal
DefaultGroupName=PalPal
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=PalPal-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\PalPal.exe
[Files]
Source: "..\dist\PalPal\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\extension\*"; DestDir: "{app}\extension"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\PalPal"; Filename: "{app}\PalPal.exe"
Name: "{userdesktop}\PalPal"; Filename: "{app}\PalPal.exe"
[Run]
Filename: "{app}\PalPal.exe"; Description: "Open PalPal"; Flags: nowait postinstall skipifsilent
