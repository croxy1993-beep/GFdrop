; GF Drop kurulum paketi (Inno Setup). Yonetici izni gerekmez, kullanici klasorune kurar.
#define AppVer GetEnv("APP_VERSION")
[Setup]
AppId={{B7E2F3A1-5C4D-4E8A-9F10-6A2D8C3B9E11}
AppName=GF Drop
AppVersion={#AppVer}
AppPublisher=GF
DefaultDirName={localappdata}\Programs\GFDrop
DefaultGroupName=GF Drop
PrivilegesRequired=lowest
OutputDir=..\Output
OutputBaseFilename=GFDrop-Setup
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\GFDrop.exe
DisableProgramGroupPage=yes

[Tasks]
Name: desktopicon; Description: "Masaüstü kısayolu oluştur"

[Files]
Source: "..\dist\GFDrop.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\GF Drop"; Filename: "{app}\GFDrop.exe"
Name: "{autodesktop}\GF Drop"; Filename: "{app}\GFDrop.exe"; Tasks: desktopicon

[Run]
; sessiz guncellemede de calisir: kurulum bitince uygulama yeniden acilir
Filename: "{app}\GFDrop.exe"; Flags: nowait

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var R: Integer;
begin
  Exec('taskkill.exe', '/f /im GFDrop.exe', '', SW_HIDE, ewWaitUntilTerminated, R);  // eski surum arka planda aciksa kapat
  Result := '';
end;
