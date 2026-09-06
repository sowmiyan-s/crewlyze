; Crewlyze Inno Setup Installer Script
; Produces a standalone, globalized Windows Installer for Crewlyze

#define MyAppName "Crewlyze"
#define MyAppVersion "1.2.3"
#define MyAppPublisher "Sowmiyan S"
#define MyAppURL "https://github.com/sowmiyan-s/crewlyze"
#define MyAppExeName "crewlyze.cmd"

[Setup]
; Unique application identifier
AppId={{8B5C032F-E720-4F2A-A142-CEEB9925E840}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppMutex=Crewlyze_Single_Instance_Mutex
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE
OutputDir=dist
OutputBaseFilename=Crewlyze_Setup_v{#MyAppVersion}
SetupIconFile=..\assets\crewlyze.ico
UninstallDisplayIcon={app}\assets\crewlyze.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequiredOverridesAllowed=commandline dialog
ArchitecturesInstallIn64BitMode=x64compatible
ChangesEnvironment=yes
DisableProgramGroupPage=auto

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "addtopath"; Description: "Add Crewlyze to system PATH (allows typing 'crewlyze' in any Command Prompt or PowerShell window)"; GroupDescription: "System Integration:"; Flags: checkedonce
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}:"; Flags: unchecked
Name: "setuppython"; Description: "Prepare Python environment and install required dependencies automatically"; GroupDescription: "Python Environment:"; Flags: checkedonce

[Files]
; Primary application root files
Source: "..\main.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\crew.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\package.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\pyproject.toml"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\index.js"; DestDir: "{app}"; Flags: ignoreversion
Source: "crewlyze.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "crewlyze.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "setup_env.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "updater.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "crewlyze_update.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "check_release.ps1"; Flags: dontcopy

; Directories and assets
Source: "..\agents\*"; DestDir: "{app}\agents"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*__pycache__*,*.pyc,*.pyo"
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*__pycache__*,*.pyc,*.pyo"
Source: "..\data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\tools\*"; DestDir: "{app}\tools"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*__pycache__*,*.pyc,*.pyo"
Source: "..\ui\*"; DestDir: "{app}\ui"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\web\*"; DestDir: "{app}\web"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\workflows\*"; DestDir: "{app}\workflows"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*__pycache__*,*.pyc,*.pyo"
Source: "..\bin\*"; DestDir: "{app}\bin"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
; Clean up any stale python compiled caches from previous installs so latest code runs immediately
Type: filesandordirs; Name: "{app}\agents\__pycache__"
Type: filesandordirs; Name: "{app}\config\__pycache__"
Type: filesandordirs; Name: "{app}\tools\__pycache__"
Type: filesandordirs; Name: "{app}\workflows\__pycache__"
Type: filesandordirs; Name: "{app}\__pycache__"
Type: files; Name: "{app}\*.pyc"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\crewlyze.ico"
Name: "{group}\Check for Updates"; Filename: "{app}\crewlyze_update.bat"; IconFilename: "{app}\assets\crewlyze.ico"
Name: "{group}\Crewlyze Setup & Repair"; Filename: "{app}\setup_env.bat"; IconFilename: "{app}\assets\crewlyze.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\crewlyze.ico"; Tasks: desktopicon

[Run]
; Run environment setup during installation if requested
Filename: "{app}\setup_env.bat"; StatusMsg: "Configuring Python virtual environment and dependencies..."; Tasks: setuppython; Flags: runhidden
; Optional launch at final step
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: shellexec postinstall nowait skipifsilent

[Code]
const
  EnvironmentKey = 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment';
  UserEnvironmentKey = 'Environment';

function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  TempFile: string;
  LatestVer: AnsiString;
  Msg: string;
  CheckScript: string;
begin
  Result := True;
  try
    ExtractTemporaryFile('check_release.ps1');
    CheckScript := ExpandConstant('{tmp}\check_release.ps1');
    if Exec('powershell.exe', '-NoProfile -ExecutionPolicy Bypass -File "' + CheckScript + '" -CurrentVersion "{#MyAppVersion}"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    begin
      if ResultCode = 2 then
      begin
        TempFile := ExpandConstant('{tmp}\..\crewlyze_latest.txt');
        if LoadStringFromFile(TempFile, LatestVer) then
        begin
          Msg := 'A newer version of Crewlyze (v' + Trim(string(LatestVer)) + ') is available online!' + #13#10#13#10 +
                 'Current installer version: v{#MyAppVersion}' + #13#10#13#10 +
                 'Would you like to open the GitHub Releases page to download the latest installer?';
          if MsgBox(Msg, mbConfirmation, MB_YESNO) = IDYES then
          begin
            ShellExec('open', '{#MyAppURL}/releases/latest', '', '', SW_SHOWNORMAL, ewNoWait, ResultCode);
            Result := False;
          end;
        end;
      end;
    end;
  except
    Result := True;
  end;
end;

function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if IsAdminInstallMode then
  begin
    if not RegQueryStringValue(HKEY_LOCAL_MACHINE, EnvironmentKey, 'Path', OrigPath) then
      OrigPath := '';
  end
  else
  begin
    if not RegQueryStringValue(HKEY_CURRENT_USER, UserEnvironmentKey, 'Path', OrigPath) then
      OrigPath := '';
  end;
  Result := Pos(';' + UpperCase(Param) + ';', ';' + UpperCase(OrigPath) + ';') = 0;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  PathRoot: Integer;
  SubKeyName: string;
  CurrentPath: string;
  NewPath: string;
  AppDir: string;
begin
  if CurStep = ssPostInstall then
  begin
    if WizardIsTaskSelected('addtopath') then
    begin
      AppDir := ExpandConstant('{app}');
      if IsAdminInstallMode then
      begin
        PathRoot := HKEY_LOCAL_MACHINE;
        SubKeyName := EnvironmentKey;
      end
      else
      begin
        PathRoot := HKEY_CURRENT_USER;
        SubKeyName := UserEnvironmentKey;
      end;

      if RegQueryStringValue(PathRoot, SubKeyName, 'Path', CurrentPath) then
      begin
        if Pos(';' + UpperCase(AppDir) + ';', ';' + UpperCase(CurrentPath) + ';') = 0 then
        begin
          if (Length(CurrentPath) > 0) and (CurrentPath[Length(CurrentPath)] <> ';') then
            NewPath := CurrentPath + ';' + AppDir
          else
            NewPath := CurrentPath + AppDir;
          RegWriteStringValue(PathRoot, SubKeyName, 'Path', NewPath);
        end;
      end
      else
      begin
        RegWriteStringValue(PathRoot, SubKeyName, 'Path', AppDir);
      end;
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  PathRoot: Integer;
  SubKeyName: string;
  CurrentPath: string;
  NewPath: string;
  AppDir: string;
  P: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    AppDir := ExpandConstant('{app}');
    if IsAdminInstallMode then
    begin
      PathRoot := HKEY_LOCAL_MACHINE;
      SubKeyName := EnvironmentKey;
    end
    else
    begin
      PathRoot := HKEY_CURRENT_USER;
      SubKeyName := UserEnvironmentKey;
    end;

    if RegQueryStringValue(PathRoot, SubKeyName, 'Path', CurrentPath) then
    begin
      P := Pos(';' + UpperCase(AppDir) + ';', ';' + UpperCase(CurrentPath) + ';');
      if P > 0 then
      begin
        NewPath := CurrentPath;
        P := Pos(';' + UpperCase(AppDir), ';' + UpperCase(NewPath));
        if P > 0 then
        begin
          Delete(NewPath, P, Length(AppDir) + 1);
        end
        else
        begin
          P := Pos(UpperCase(AppDir) + ';', UpperCase(NewPath));
          if P > 0 then
            Delete(NewPath, P, Length(AppDir) + 1)
          else
          begin
            P := Pos(UpperCase(AppDir), UpperCase(NewPath));
            if P > 0 then
              Delete(NewPath, P, Length(AppDir));
          end;
        end;
        RegWriteStringValue(PathRoot, SubKeyName, 'Path', NewPath);
      end;
    end;
  end;
end;
