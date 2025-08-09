# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Definir el directorio base
base_dir = Path.cwd()

# Recopilar todos los archivos de datos necesarios
datas = [
    # Archivos de configuración
    ('config.ini', '.'),
    
    # Directorio de datos JSON
    ('data', 'data'),
    
    # Directorio de RCON
    ('rcon', 'rcon'),
    
    # Directorio de iconos
    ('ico', 'ico'),
    
    # Archivos de documentación principales
    ('README.md', '.'),
    ('LICENSE', '.'),
]

# Paquetes ocultos necesarios - versión completa para debug
hiddenimports = [
    # Core de la aplicación
    'customtkinter',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL._tkinter_finder',
    
    # Tkinter completo
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.simpledialog',
    'tkinter.font',
    'tkinter.colorchooser',
    
    # Sistema y utilidades
    'psutil',
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
    'time',
    'webbrowser',
    'zipfile',
    'base64',
    'functools',
    'traceback',
    'queue',
    'signal',
    'socket',
    'ssl',
    
    # Requests y dependencias HTTP completas
    'requests',
    'requests.adapters',
    'requests.auth',
    'requests.cookies',
    'requests.exceptions',
    'requests.models',
    'requests.packages',
    'requests.packages.urllib3',
    'requests.sessions',
    'requests.utils',
    'requests.structures',
    'requests.hooks',
    'requests.status_codes',
    'requests.compat',
    'requests.help',
    
    # urllib3 completo
    'urllib3',
    'urllib3.util',
    'urllib3.util.retry',
    'urllib3.util.ssl_',
    'urllib3.util.timeout',
    'urllib3.util.url',
    'urllib3.exceptions',
    'urllib3.connection',
    'urllib3.connectionpool',
    'urllib3.poolmanager',
    'urllib3.response',
    'urllib3.fields',
    'urllib3.filepost',
    'urllib3.packages',
    'urllib3.packages.ssl_match_hostname',
    
    # Certificados y encoding
    'certifi',
    'charset_normalizer',
    'charset_normalizer.api',
    'charset_normalizer.legacy',
    'charset_normalizer.models',
    'charset_normalizer.utils',
    'idna',
    'idna.core',
    'idna.codec',
    
    # URL parsing
    'urllib.parse',
    'urllib.request',
    'urllib.error',
    'urllib.response',
    
    # HTTP
    'http',
    'http.client',
    'http.server',
    'http.cookies',
    
    # Email (usado por algunos módulos)
    'email',
    'email.utils',
    'email.mime',
    
    # Módulos específicos de la aplicación
    'gui.main_window',
    'gui.dialogs.initial_setup',
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
]

# Módulos a excluir para reducir tamaño
excludes = [
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
    'django',
    'flask',
    'tornado',
    'twisted',
    'docutils',
    'pydoc',
    'xml',
    'xmlrpc',
    'unicodedata',
    'test',
    'tests',
    'distutils',
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
    optimize=0,  # Sin optimización para mejor debug
)

# Recopilar automáticamente todo de estos paquetes
a.binaries = a.binaries + [
    ('api-ms-win-crt-runtime-l1-1-0.dll', None, 'BINARY'),
    ('api-ms-win-crt-stdio-l1-1-0.dll', None, 'BINARY'),
    ('api-ms-win-crt-heap-l1-1-0.dll', None, 'BINARY'),
]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ArkServerManager_DEBUG',
    debug=True,  # Habilitar debug
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # No usar UPX para debug
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Mostrar consola para debug
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ico/ArkManager.ico',
    version_file=None,
)

# Información adicional para el ejecutable
exe.name = 'ArkServerManager_DEBUG.exe'
