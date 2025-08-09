# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Configuración básica
block_cipher = None
base_dir = Path.cwd()

# Archivos de datos necesarios
datas = []

# Agregar archivos esenciales si existen
essential_files = [
    ('config.ini', '.'),
    ('README.md', '.'),
    ('LICENSE', '.'),
]

for src, dst in essential_files:
    if os.path.exists(src):
        datas.append((src, dst))

# Agregar directorios esenciales si existen
essential_dirs = [
    ('data', 'data'),
    ('examples', 'examples'),
    ('rcon', 'rcon'),
    ('ico', 'ico'),
]

for src, dst in essential_dirs:
    if os.path.exists(src):
        datas.append((src, dst))

# Imports ocultos esenciales
hiddenimports = [
    # GUI
    'customtkinter',
    'CTkMessagebox',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    
    # Imágenes
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    
    # Sistema
    'psutil',
    'requests',
    'urllib3',
    'certifi',
    
    # Otros
    'pystray',
    'schedule',
    'configparser',
    'pathlib',
    'json',
    'logging',
    'threading',
    'subprocess',
    'os',
    'sys',
    
    # Módulos de la aplicación
    'gui.main_window',
    'gui.dialogs.initial_setup',
    'gui.dialogs.advanced_settings_dialog',
    'gui.dialogs.custom_dialogs',
    'gui.panels.principal_panel',
    'gui.panels.server_panel',
    'gui.panels.config_panel',
    'gui.panels.monitoring_panel',
    'gui.panels.backup_panel',
    'gui.panels.players_panel',
    'gui.panels.mods_panel',
    'gui.panels.logs_panel',
    'gui.panels.rcon_panel',
    'utils.config_manager',
    'utils.logger',
    'utils.server_manager',
    'utils.app_settings',
    'utils.system_tray',
]

# Exclusiones
excludes = [
    'matplotlib',
    'numpy',
    'scipy',
    'pandas',
    'jupyter',
    'test',
    'tests',
    'unittest',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Determinar icono
icon_path = None
if os.path.exists('ico/ArkManager.ico'):
    icon_path = 'ico/ArkManager.ico'

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ArkServerManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)