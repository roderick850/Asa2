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
    ('examples', 'examples'),
    ('rcon', 'rcon'),
    ('ico', 'ico'),
]

# Directorios opcionales (pueden no existir en otros equipos)
optional_dirs = [
    ('config', 'config'),
    ('maps', 'maps'),
    ('mods', 'mods'),
    ('servers', 'servers'),
    ('backups', 'backups'),
    ('exports', 'exports'),
]

# Agregar directorios esenciales
for src, dst in essential_dirs:
    if os.path.exists(src):
        datas.append((src, dst))
    else:
        print(f"⚠️ Directorio esencial no encontrado: {src}")

# Agregar directorios opcionales sin generar errores
for src, dst in optional_dirs:
    try:
        if os.path.exists(src) and os.access(src, os.R_OK):
            datas.append((src, dst))
            print(f"✅ Directorio incluido: {src}")
        else:
            print(f"ℹ️ Directorio opcional omitido: {src}")
    except (OSError, PermissionError) as e:
        print(f"⚠️ Error de permisos en {src}: {e}")

# Manejar carpeta 'data' de forma especial
data_dir = 'data'
if os.path.exists(data_dir):
    try:
        # Verificar permisos de lectura
        if os.access(data_dir, os.R_OK):
            # Verificar si hay archivos accesibles
            accessible_files = []
            try:
                for root, dirs, files in os.walk(data_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            if os.access(file_path, os.R_OK):
                                accessible_files.append(file_path)
                        except (OSError, PermissionError):
                            continue
                
                if accessible_files:
                    datas.append((data_dir, 'data'))
                    print(f"✅ Carpeta 'data' incluida con {len(accessible_files)} archivos accesibles")
                else:
                    print("ℹ️ Carpeta 'data' existe pero no contiene archivos accesibles")
            except (OSError, PermissionError) as e:
                print(f"⚠️ Error al explorar carpeta 'data': {e}")
        else:
            print("⚠️ Carpeta 'data' sin permisos de lectura - omitida")
    except (OSError, PermissionError) as e:
        print(f"⚠️ Error de permisos en carpeta 'data': {e}")
else:
    print("ℹ️ Carpeta 'data' no existe - se creará automáticamente en tiempo de ejecución")

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
    'PIL._tkinter_finder',
    
    # Sistema
    'psutil',
    'requests',
    'urllib3',
    'certifi',
    'ctypes',
    'ctypes.wintypes',
    
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
    'datetime',
    'time',
    're',
    'shutil',
    'zipfile',
    'win10toast',
    'winreg',
    'typing',
    'collections',
    'platform',
    
    # Módulos de la aplicación - GUI
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
    'gui.panels.console_panel',
    'gui.panels.dynamic_config_panel',
    'gui.panels.ini_config_panel',
    'gui.panels.direct_commands_panel',
    'gui.panels.advanced_backup_panel',
    'gui.panels.advanced_restart_panel',
    'gui.panels.server_config_panel',
    'gui.panels.simple_logs_panel',
    'gui.panels.logs_panel_new',
    'gui.panels.working_logs_panel',
    'gui.panels.test_logs_panel',
    'gui.panels.cluster_panel',
    
    # Módulos de la aplicación - Utils
    'utils.config_manager',
    'utils.config_profiles',
    'utils.cluster_manager',
    'utils.logger',
    'utils.server_manager',
    'utils.app_settings',
    'utils.system_tray',
    'utils.server_logger',
    'utils.ini_cleaner',
    'utils.dialogs',
    'utils.scheduled_commands',
    'utils.health_monitor',
    'utils.player_monitor',
    'utils.game_alerts_manager',  # Nuevo módulo agregado
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