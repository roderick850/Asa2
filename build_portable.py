#!/usr/bin/env python3
"""
Script de compilación portátil para Ark Server Manager
Crea un ejecutable que funciona en cualquier equipo Windows sin problemas de permisos
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_directories():
    """Limpiar directorios de compilación anteriores"""
    print("🧹 Limpiando directorios de compilación...")
    
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"✅ Eliminado: {dir_name}")
            except Exception as e:
                print(f"⚠️ Error eliminando {dir_name}: {e}")

def ensure_directories_exist():
    """Asegurar que existan los directorios necesarios para la compilación"""
    print("📁 Verificando directorios necesarios...")
    
    required_dirs = [
        'ico',
        'examples', 
        'rcon',
        'config',
        'maps',
        'mods',
        'servers'
    ]
    
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name, exist_ok=True)
                print(f"✅ Creado directorio: {dir_name}")
                
                # Crear archivo placeholder para directorios vacíos
                placeholder_file = os.path.join(dir_name, '.gitkeep')
                with open(placeholder_file, 'w') as f:
                    f.write("# Directorio necesario para la aplicación\n")
                    
            except Exception as e:
                print(f"❌ Error creando directorio {dir_name}: {e}")
        else:
            print(f"✅ Directorio existe: {dir_name}")

def create_portable_spec():
    """Crear un archivo .spec optimizado para compilación portátil"""
    print("📝 Creando configuración portátil...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Configuración básica
block_cipher = None

# Archivos esenciales (siempre incluir)
essential_files = [
    ('config.ini', '.'),
    ('README.md', '.'),
    ('LICENSE', '.'),
]

# Directorios esenciales (siempre incluir)
essential_dirs = [
    ('examples', 'examples'),
    ('rcon', 'rcon'),
    ('ico', 'ico'),
]

# Directorios opcionales (incluir solo si existen y son accesibles)
optional_dirs = [
    'config',
    'maps', 
    'mods',
    'servers',
    'backups',
    'exports'
]

# Construir lista de datos
datas = []

# Agregar archivos esenciales
for src, dst in essential_files:
    if os.path.exists(src):
        datas.append((src, dst))
        print(f"✅ Archivo incluido: {src}")
    else:
        print(f"⚠️ Archivo no encontrado: {src}")

# Agregar directorios esenciales
for src, dst in essential_dirs:
    if os.path.exists(src):
        datas.append((src, dst))
        print(f"✅ Directorio incluido: {src}")
    else:
        print(f"⚠️ Directorio no encontrado: {src}")

# Manejar directorios opcionales de forma segura
for dir_name in optional_dirs:
    if os.path.exists(dir_name):
        try:
            # Verificar permisos de lectura
            if os.access(dir_name, os.R_OK):
                # Verificar si hay archivos accesibles
                accessible_files = []
                try:
                    for root, dirs, files in os.walk(dir_name):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                if os.access(file_path, os.R_OK):
                                    accessible_files.append(file_path)
                            except (OSError, PermissionError):
                                continue
                    
                    if accessible_files:
                        datas.append((dir_name, dir_name))
                        print(f"✅ Directorio opcional incluido: {dir_name} ({len(accessible_files)} archivos)")
                    else:
                        print(f"ℹ️ Directorio {dir_name} existe pero no contiene archivos accesibles")
                except (OSError, PermissionError) as e:
                    print(f"⚠️ Error explorando {dir_name}: {e}")
            else:
                print(f"⚠️ Directorio {dir_name} sin permisos de lectura - omitido")
        except (OSError, PermissionError) as e:
            print(f"⚠️ Error de permisos en {dir_name}: {e}")
    else:
        print(f"ℹ️ Directorio opcional {dir_name} no existe - se creará en tiempo de ejecución")

# Imports ocultos completos
hiddenimports = [
    # Módulos de GUI principales
    'gui.main_window',
    'gui.dialogs.initial_setup',
    'gui.dialogs.advanced_settings_dialog',
    
    # Paneles de GUI
    'gui.panels.principal_panel',
    'gui.panels.server_panel',
    'gui.panels.console_panel',
    'gui.panels.config_panel',
    'gui.panels.logs_panel',
    'gui.panels.rcon_panel',
    'gui.panels.mods_panel',
    'gui.panels.players_panel',
    'gui.panels.cluster_panel',
    'gui.panels.ini_config_panel',
    'gui.panels.monitoring_panel',
    'gui.panels.advanced_backup_panel',
    'gui.panels.server_config_panel',
    'gui.panels.working_logs_panel',
    
    # Utilidades principales
    'utils.config_manager',
    'utils.logger',
    'utils.server_manager',
    'utils.app_settings',
    'utils.system_tray',
    'utils.config_profiles',
    'utils.cluster_manager',
    'utils.scheduled_commands',
    'utils.ini_cleaner',
    'utils.server_logger',
    'utils.dialogs',
    
    # Módulos de terceros críticos
    'customtkinter',
    'CTkMessagebox',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'psutil',
    'schedule',
    'pystray',
    'win10toast',
    
    # Módulos del sistema
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'threading',
    'subprocess',
    'json',
    'configparser',
    'datetime',
    'pathlib',
    'shutil',
    'winreg',
    'ctypes',
    'ctypes.wintypes',
]

# Módulos a excluir para reducir tamaño
excludes = [
    'matplotlib',
    'numpy',
    'scipy',
    'pandas',
    'jupyter',
    'IPython',
    'pytest',
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ico/ArkManager.ico' if os.path.exists('ico/ArkManager.ico') else None,
)
'''
    
    with open('main_portable.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ Archivo main_portable.spec creado")

def build_executable():
    """Compilar el ejecutable usando PyInstaller"""
    print("🔨 Iniciando compilación...")
    
    try:
        # Comando de compilación
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            'main_portable.spec'
        ]
        
        print(f"Ejecutando: {' '.join(cmd)}")
        
        # Ejecutar compilación
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Compilación exitosa!")
            print("\n📁 Archivos generados:")
            
            # Mostrar archivos en dist
            dist_dir = Path('dist')
            if dist_dir.exists():
                for item in dist_dir.iterdir():
                    if item.is_file():
                        size_mb = item.stat().st_size / (1024 * 1024)
                        print(f"   📄 {item.name} ({size_mb:.1f} MB)")
                    elif item.is_dir():
                        print(f"   📁 {item.name}/")
        else:
            print("❌ Error en la compilación:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando PyInstaller: {e}")
        return False
    
    return True

def create_portable_package():
    """Crear paquete portátil con todos los archivos necesarios"""
    print("📦 Creando paquete portátil...")
    
    try:
        # Crear directorio de distribución portátil
        portable_dir = Path('ArkServerManager_Portable')
        if portable_dir.exists():
            shutil.rmtree(portable_dir)
        
        portable_dir.mkdir()
        
        # Copiar ejecutable
        exe_file = Path('dist/ArkServerManager.exe')
        if exe_file.exists():
            shutil.copy2(exe_file, portable_dir / 'ArkServerManager.exe')
            print("✅ Ejecutable copiado")
        
        # Copiar archivos de configuración esenciales
        essential_files = [
            'README.md',
            'LICENSE',
            'config.ini'
        ]
        
        for file_name in essential_files:
            if os.path.exists(file_name):
                shutil.copy2(file_name, portable_dir / file_name)
                print(f"✅ Archivo copiado: {file_name}")
        
        # Crear directorios necesarios en el paquete portátil
        portable_dirs = ['data', 'logs', 'config', 'backups', 'exports', 'servers']
        for dir_name in portable_dirs:
            (portable_dir / dir_name).mkdir(exist_ok=True)
            # Crear archivo README en cada directorio
            readme_file = portable_dir / dir_name / 'README.txt'
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(f"Directorio {dir_name} - Creado automáticamente por Ark Server Manager\\n")
            print(f"✅ Directorio creado: {dir_name}")
        
        # Crear archivo de instrucciones
        instructions = '''# Ark Server Manager - Versión Portátil

## Instrucciones de uso:

1. Ejecuta ArkServerManager.exe
2. La aplicación creará automáticamente todos los directorios necesarios
3. Configura la ruta de tu servidor ARK en la primera ejecución
4. ¡Disfruta gestionando tus servidores!

## Directorios incluidos:

- **data/**: Datos de la aplicación y configuraciones
- **logs/**: Archivos de registro de la aplicación y servidores
- **config/**: Configuraciones adicionales
- **backups/**: Copias de seguridad de tus servidores
- **exports/**: Archivos exportados (configuraciones, listas de jugadores, etc.)
- **servers/**: Aquí se almacenarán los datos de tus servidores

## Soporte:

Si encuentras algún problema, revisa los archivos de log en la carpeta logs/

¡Gracias por usar Ark Server Manager!
'''
        
        with open(portable_dir / 'INSTRUCCIONES.txt', 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        print(f"✅ Paquete portátil creado en: {portable_dir}")
        
        # Crear archivo ZIP del paquete
        shutil.make_archive('ArkServerManager_Portable', 'zip', '.', 'ArkServerManager_Portable')
        print("✅ Archivo ZIP creado: ArkServerManager_Portable.zip")
        
    except Exception as e:
        print(f"❌ Error creando paquete portátil: {e}")
        return False
    
    return True

def main():
    """Función principal del script de compilación"""
    print("🚀 === COMPILACIÓN PORTÁTIL DE ARK SERVER MANAGER ===")
    print()
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('main.py'):
        print("❌ Error: No se encontró main.py. Ejecuta este script desde el directorio raíz del proyecto.")
        return
    
    # Paso 1: Limpiar compilaciones anteriores
    clean_build_directories()
    print()
    
    # Paso 2: Asegurar que existan los directorios necesarios
    ensure_directories_exist()
    print()
    
    # Paso 3: Crear configuración portátil
    create_portable_spec()
    print()
    
    # Paso 4: Compilar ejecutable
    if not build_executable():
        print("❌ Compilación fallida. Revisa los errores anteriores.")
        return
    print()
    
    # Paso 5: Crear paquete portátil
    if create_portable_package():
        print("🎉 ¡Compilación portátil completada exitosamente!")
        print()
        print("📁 Archivos generados:")
        print("   - dist/ArkServerManager.exe (ejecutable)")
        print("   - ArkServerManager_Portable/ (directorio portátil)")
        print("   - ArkServerManager_Portable.zip (paquete comprimido)")
        print()
        print("💡 Puedes distribuir el archivo ZIP o la carpeta ArkServerManager_Portable")
        print("   El ejecutable funcionará en cualquier equipo Windows sin problemas de permisos.")
    else:
        print("❌ Error creando paquete portátil.")

if __name__ == "__main__":
    main()