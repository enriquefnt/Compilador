
; Script básico para instalar app_compilador y Ghostscript portable

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Setup]
AppName=Compilador de PDFs
AppVersion=1.0.1
DefaultDirName={pf}\CompiladorPDFs
DefaultGroupName=CompiladorPDFs
OutputBaseFilename=CompiladorPDFs_Instalador
Compression=lzma
SolidCompression=yes

[Files]
; Copiar el ejecutable principal
Source: "C:\local_web\analisisSAC\DistribucionApp\app_compilador.exe"; DestDir: "{app}"; Flags: ignoreversion

; Copiar la carpeta completa de Ghostscript portable
Source: "C:\local_web\analisisSAC\DistribucionApp\gs*"; DestDir: "{app}\gs"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\Compilador de PDFs"; Filename: "{app}\app_compilador.exe"

[Run]
; Opcional: ejecutar la app al terminar la instalación
Filename: "{app}\app_compilador.exe"; Description: "Ejecutar Compilador de PDFs"; Flags: nowait postinstall skipifsilent