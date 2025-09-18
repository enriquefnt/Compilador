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
; Icono del instalador
SetupIconFile=C:\local_web\Compilador\DistribucionApp\compilador.ico

[Tasks]
Name: "desktopicon"; Description: "Crear un icono en el escritorio"; GroupDescription: "Opciones adicionales"

[Files]
Source: "C:\local_web\Compilador\DistribucionApp\app_compilador.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\local_web\Compilador\DistribucionApp\gs\*"; DestDir: "{app}\gs"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "C:\local_web\Compilador\DistribucionApp\ayuda.pdf"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\local_web\Compilador\DistribucionApp\compilador.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Compilador de PDFs"; Filename: "{app}\app_compilador.exe"; IconFilename: "{app}\compilador.ico"
Name: "{userdesktop}\Compilador de PDFs"; Filename: "{app}\app_compilador.exe"; IconFilename: "{app}\compilador.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\app_compilador.exe"; Description: "Ejecutar Compilador de PDFs"; Flags: nowait postinstall skipifsilent
Filename: "{app}\ayuda.pdf"; Description: "Abrir archivo de ayuda"; Flags: postinstall shellexec skipifsilent
