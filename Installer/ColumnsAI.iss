; ColumnsAI Inno Setup Installer Script
; Compile with Inno Setup 6+  (https://jrsoftware.org/isinfo.php)
;
; Before compiling, build the solution in Release mode so that both
;   ColumnsAI\bin\Release\net48\ColumnsAI.dll
;   ColumnsAI\bin\Release\net8.0-windows\ColumnsAI.dll
; exist.

#define MyAppName      "ColumnsAI"
#define MyAppVersion   "1.0"
#define MyAppPublisher "AI-Automate-3D"
#define MyAppURL       "https://github.com/AI-Automate-3D/RevitAI"

[Setup]
AppId={{B5A7C9E1-3F42-4D6B-8E1A-2C4F6A8B0D3E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={commonappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=ColumnsAI_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=compiler:SetupClassicIcon.ico
UninstallDisplayName={#MyAppName}
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; ----------------------------------------------------------------
; Component / version selection
; ----------------------------------------------------------------
[Types]
Name: "full";   Description: "All Revit versions (2019-2027)"
Name: "custom"; Description: "Choose Revit versions"; Flags: iscustom

[Components]
Name: "main";      Description: "ColumnsAI Core Files"; Types: full custom; Flags: fixed
Name: "revit2019"; Description: "Revit 2019"; Types: full
Name: "revit2020"; Description: "Revit 2020"; Types: full
Name: "revit2021"; Description: "Revit 2021"; Types: full
Name: "revit2022"; Description: "Revit 2022"; Types: full
Name: "revit2023"; Description: "Revit 2023"; Types: full
Name: "revit2024"; Description: "Revit 2024"; Types: full
Name: "revit2025"; Description: "Revit 2025"; Types: full
Name: "revit2026"; Description: "Revit 2026"; Types: full
Name: "revit2027"; Description: "Revit 2027"; Types: full

; ----------------------------------------------------------------
; Directories – grant write access so the add-in can create logs,
; backups, etc. at run time.
; ----------------------------------------------------------------
[Dirs]
Name: "{app}";                 Permissions: users-modify
Name: "{app}\APIs";            Permissions: users-modify
Name: "{app}\backups";         Permissions: users-modify
Name: "{app}\input_history";   Permissions: users-modify
Name: "{app}\log";             Permissions: users-modify
Name: "{app}\python_scripts";  Permissions: users-modify
Name: "{app}\net48";           Permissions: users-modify; Components: revit2019 revit2020 revit2021 revit2022 revit2023 revit2024
Name: "{app}\net8";            Permissions: users-modify; Components: revit2025 revit2026 revit2027

; ----------------------------------------------------------------
; Files
; ----------------------------------------------------------------
[Files]
; --- .NET Framework 4.8 DLL (Revit 2019-2024) ---
Source: "..\ColumnsAI\bin\Release\net48\ColumnsAI.dll"; DestDir: "{app}\net48"; \
  Flags: ignoreversion; Components: revit2019 revit2020 revit2021 revit2022 revit2023 revit2024

; --- .NET 8 DLL (Revit 2025-2027) ---
Source: "..\ColumnsAI\bin\Release\net8.0-windows\ColumnsAI.dll"; DestDir: "{app}\net8"; \
  Flags: ignoreversion; Components: revit2025 revit2026 revit2027

; --- Python scripts & data (always installed) ---
Source: "..\run_pipeline.py";                       DestDir: "{app}";                Flags: ignoreversion; Components: main
Source: "..\columns.csv";                           DestDir: "{app}";                Flags: ignoreversion; Components: main
Source: "..\python_scripts\ai_parser.py";           DestDir: "{app}\python_scripts"; Flags: ignoreversion; Components: main
Source: "..\python_scripts\populate_column_id.py";  DestDir: "{app}\python_scripts"; Flags: ignoreversion; Components: main

; ----------------------------------------------------------------
; Cleanup on uninstall
; ----------------------------------------------------------------
[UninstallDelete]
Type: files;          Name: "{commonappdata}\Autodesk\Revit\Addins\2019\ColumnsAI.addin"
Type: files;          Name: "{commonappdata}\Autodesk\Revit\Addins\2020\ColumnsAI.addin"
Type: files;          Name: "{commonappdata}\Autodesk\Revit\Addins\2021\ColumnsAI.addin"
Type: files;          Name: "{commonappdata}\Autodesk\Revit\Addins\2022\ColumnsAI.addin"
Type: files;          Name: "{commonappdata}\Autodesk\Revit\Addins\2023\ColumnsAI.addin"
Type: files;          Name: "{commonappdata}\Autodesk\Revit\Addins\2024\ColumnsAI.addin"
Type: files;          Name: "{commonappdata}\Autodesk\Revit\Addins\2025\ColumnsAI.addin"
Type: files;          Name: "{commonappdata}\Autodesk\Revit\Addins\2026\ColumnsAI.addin"
Type: files;          Name: "{commonappdata}\Autodesk\Revit\Addins\2027\ColumnsAI.addin"
Type: files;          Name: "{app}\user_input.txt"
Type: files;          Name: "{app}\debug_pipeline.log"
Type: filesandordirs; Name: "{app}\backups"
Type: filesandordirs; Name: "{app}\input_history"
Type: filesandordirs; Name: "{app}\log"

; ----------------------------------------------------------------
; Pascal script – creates the .addin manifests after install
; ----------------------------------------------------------------
[Code]

procedure CreateAddinManifest(Year, DllSubDir: String);
var
  AddinDir, AddinPath, DllPath, Content: String;
begin
  AddinDir := ExpandConstant('{commonappdata}') + '\Autodesk\Revit\Addins\' + Year;
  ForceDirectories(AddinDir);

  AddinPath := AddinDir + '\ColumnsAI.addin';
  DllPath   := ExpandConstant('{app}') + '\' + DllSubDir + '\ColumnsAI.dll';

  Content :=
    '<?xml version="1.0" encoding="utf-8"?>' + #13#10 +
    '<RevitAddIns>'                            + #13#10 +
    '  <AddIn Type="Application">'             + #13#10 +
    '    <Name>ColumnsAI</Name>'               + #13#10 +
    '    <Assembly>' + DllPath + '</Assembly>'  + #13#10 +
    '    <FullClassName>ColumnsAI.App</FullClassName>'              + #13#10 +
    '    <AddInId>B5A7C9E1-3F42-4D6B-8E1A-2C4F6A8B0D3E</AddInId>' + #13#10 +
    '    <VendorId>AI-Automate-3D</VendorId>'                      + #13#10 +
    '    <VendorDescription>AI-Automate-3D</VendorDescription>'    + #13#10 +
    '  </AddIn>'                               + #13#10 +
    '</RevitAddIns>';

  SaveStringToFile(AddinPath, Content, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if IsComponentSelected('revit2019') then CreateAddinManifest('2019', 'net48');
    if IsComponentSelected('revit2020') then CreateAddinManifest('2020', 'net48');
    if IsComponentSelected('revit2021') then CreateAddinManifest('2021', 'net48');
    if IsComponentSelected('revit2022') then CreateAddinManifest('2022', 'net48');
    if IsComponentSelected('revit2023') then CreateAddinManifest('2023', 'net48');
    if IsComponentSelected('revit2024') then CreateAddinManifest('2024', 'net48');
    if IsComponentSelected('revit2025') then CreateAddinManifest('2025', 'net8');
    if IsComponentSelected('revit2026') then CreateAddinManifest('2026', 'net8');
    if IsComponentSelected('revit2027') then CreateAddinManifest('2027', 'net8');
  end;
end;
