; Inno Setup 7 installer template for PyQt5 desktop apps
; Place this file alongside your app build output.
; Compile: ISCC.exe setup.iss
; Download Inno Setup: https://jrsoftware.org/isdl.php

#define MyAppName "你的应用名"
#define MyAppVersion "1.1"
#define MyAppPublisher "你的公司/团队名"
#define MyAppExeName "你的应用_v1.1.exe"

[Setup]
AppId={{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName=D:\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=.\安装包输出
OutputBaseFilename={#MyAppName}_v{#MyAppVersion}_安装程序
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
; lowest = 不需要管理员权限，用户可装到任意目录
PrivilegesRequired=lowest

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; Flags: checkedonce

[Files]
; 主程序
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; 配置文件（仅首次安装时创建，避免覆盖用户修改）
Source: "..\config.json"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
; 资源目录（全部文件）
Source: "..\资源库\*"; DestDir: "{app}\资源库"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}"; Permissions: users-modify
Name: "{app}\资源库"; Permissions: users-modify
Name: "{app}\输出"; Permissions: users-modify

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\资源库文件夹"; Filename: "{app}\资源库"
Name: "{group}\卸载"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "运行 {#MyAppName}"; Flags: nowait postinstall skipifsilent
