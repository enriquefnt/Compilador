[Setup]
AppName=Compilador de PDFs
AppVersion=1.0
DefaultDirName={pf}\CompiladorPDF
DefaultGroupName=Compilador PDF
OutputDir=OutputInstaller
OutputBaseFilename=CompiladorPDF_Setup
Compression=lzma
SolidCompression=yes

[Files]
Source="dist\app_compilador.exe"; DestDir="{app}"; Flags: ignoreversion
Source="dist\app_compilador.exe"; DestDir="{app}"; Flags: ignoreversion

[Icons]
Name="{group}\Compilador PDF"; Filename="{app}\app_compilador.exe"; IconFilename="{app}\compilador.ico"
Name="{userdesktop}\Compilador PDF"; Filename="{app}\app_compilador.exe"; IconFilename="{app}\compilador.ico"

[Run]
Filename="{app}\app_compilador.exe"; Description="Iniciar Compilador de PDF"; Flags: nowait postinstall skipifsilent
