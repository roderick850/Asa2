# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Definir el directorio base
base_dir = Path.cwd()

# Recopilar archivos de datos necesarios
datas = [
    ('config.ini', '.'),
    ('data', 'data'),
    ('examples', 'examples'),
    ('rcon', 'rcon'),
    ('ico', 'ico'),
    ('README.md', '.'),
    ('LICENSE', '.'),
]

# Solo incluir las dependencias esenciales
hiddenimports = [
    'customtkinter',
    'PIL',
    'PIL._tkinter_finder',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.simpledialog',
    'tkinter.font',
    'tkinter.colorchooser',
    'psutil',
    'requests',
    'pystray',
    'win10toast',
    'six',
    'configparser',
    'schedule',
    'threading',
    'subprocess',
    'pathlib',
    'os',
    'sys',
    'json',
    'datetime',
    'logging',
    'logging.handlers',
    'collections',
    're',
    'platform',
    'shutil',
    'urllib.parse',
    'urllib.request',
    'time',
    'webbrowser',
    
    # Módulos específicos de la aplicación
    'gui.main_window',
    'gui.dialogs.initial_setup',
    'gui.dialogs.advanced_settings_dialog',
    'gui.dialogs.custom_dialogs',
    'gui.panels.server_panel',
    'gui.panels.principal_panel',
    'gui.panels.config_panel',
    'gui.panels.logs_panel',
    'gui.panels.mods_panel',
    'gui.panels.backup_panel',
    'gui.panels.advanced_backup_panel',
    'gui.panels.monitoring_panel',
    'gui.panels.players_panel',
    'gui.panels.rcon_panel',
    'gui.panels.advanced_restart_panel',
    'gui.panels.dynamic_config_panel',
    'utils.config_manager',
    'utils.logger',
    'utils.server_manager',
    'utils.server_logger',
    'utils.ini_cleaner',
    'utils.app_settings',
    'utils.system_tray',
]

# Excluir solo módulos realmente problemáticos
excludes = [
    'matplotlib',
    'numpy',
    'scipy',
    'pandas',
    'jupyter',
    'IPython',
    'tornado',
    'zmq',
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
    noarchive=False,
    optimize=0,  # Sin optimización para evitar problemas
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ArkServerManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Sin UPX para evitar alertas de antivirus
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ico/ArkManager.ico',
    version_file=None,
)
