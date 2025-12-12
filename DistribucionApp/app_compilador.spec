# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app_compilador.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ayuda.png', '.'),
        ('ayuda.pdf', '.'),
        ('compilador.ico', '.'),
        ('DejaVuSans.ttf', '.'),
         ('gs', 'gs'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='app_compilador',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # SIN ventana negra
    icon='compilador.ico'
)
