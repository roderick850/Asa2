[Setup]
; Identificador único para tu aplicación. Se recomienda un GUID.
; Puedes generar uno nuevo en línea.
AppId={{b212478c-d5f7-41fd-a25d-4aefda69c075}}
AppName=ArkServerManager
AppVersion=1.0.
AppVerName=ARK ASA Server Manager 1.0
AppPublisher=Roderick Development
AppPublisherURL=https://github.com/roderick850/ArkManager
AppSupportURL=https://github.com/roderick850/ArkManager/issues
AppUpdatesURL=https://github.com/roderick850/ArkManager/releases
AppCopyright=Copyright (C) 2025 Roderick Development
; El archivo de salida del instalador se guardará en la carpeta actual
OutputBaseFilename=ArkServerManager_v1.0_setup
; Directorio de salida donde se guardará el instalador
OutputDir=.\instalador_final
DefaultDirName={autopf}\ArkServerManager
DefaultGroupName=ArkServerManager
SetupIconFile=ico\ArkManager.ico
; Se ha eliminado la línea AppExecutable aquí
; El compilador ya no buscará el ejecutable al compilar
; La referencia al ejecutable se hará directamente en las secciones [Icons] y [Run]
PrivilegesRequired=admin
; Configuraciones para evitar false positives de antivirus
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=no
DisableReadyPage=no
DisableFinishedPage=no
; Información adicional para reducir detecciones de antivirus
VersionInfoVersion=1.0.0
VersionInfoProductName=ARK ASA Server Manager
VersionInfoProductVersion=1.0
VersionInfoCompany=Roderick Development
VersionInfoDescription=Administrador de servidores para ARK Survival Ascended
VersionInfoCopyright=Copyright (C) 2025 Roderick Development
; Configuraciones de seguridad
SignedUninstaller=no

[Files]
; Archivos de la aplicación principal
; Source: "dist\ArkServerManager.exe"
; DestDir: "{app}"
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "ico\ArkManager.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "ArkServerManager.manifest.xml"; DestDir: "{app}"; Flags: ignoreversion
; Agregar archivos de documentación para legitimidad
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "LEEME.txt"
Source: "CHANGELOG_PERSISTENCIA_MODS.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "HISTORIAL_CAMBIOS.txt"

[Registry]
; Registrar la aplicación en el sistema para legitimidad
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ArkServerManager"; ValueType: string; ValueName: "DisplayName"; ValueData: "ARK ASA Server Manager"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ArkServerManager"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "1.0"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ArkServerManager"; ValueType: string; ValueName: "Publisher"; ValueData: "Roderick Development"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ArkServerManager"; ValueType: string; ValueName: "InstallLocation"; ValueData: "{app}"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ArkServerManager"; ValueType: string; ValueName: "UninstallString"; ValueData: "{uninstallexe}"

[UninstallDelete]
; Limpiar archivos creados por la aplicación
Type: filesandordirs; Name: "{app}\config"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\temp"

[Icons]
; Acceso directo en el men� de inicio
Name: "{group}\ArkServerManager"; Filename: "{app}\ArkServerManager.exe"; IconFilename: "{app}\ArkManager.ico"
; Acceso directo para desinstalar
Name: "{group}\Desinstalar ArkServerManager"; Filename: "{uninstallexe}"
; Acceso directo en el escritorio (opcional)
Name: "{commondesktop}\ArkServerManager"; Filename: "{app}\ArkServerManager.exe"; Tasks: desktopicon; IconFilename: "{app}\ArkManager.ico"

[Tasks]
; Permite al usuario elegir si quiere un acceso directo en el escritorio
Name: desktopicon; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Iconos adicionales:";

[Run]
; Permite ejecutar la aplicaci�n despu�s de la instalaci�n
; El instalador buscar� este archivo en el directorio de instalaci�n ({app})
Filename: "{app}\ArkServerManager.exe"; Description: "Ejecutar ArkServerManager"; Flags: postinstall shellexec runmaximized;