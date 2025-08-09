"""
Script de diagnóstico para detectar problemas de compatibilidad
del Ark Server Manager en diferentes equipos
"""

import sys
import os
import platform
import traceback
from pathlib import Path

def print_header(title):
    """Imprimir encabezado con formato"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_check(description, status, details=""):
    """Imprimir resultado de verificación"""
    status_icon = "✅" if status else "❌"
    print(f"{status_icon} {description}")
    if details:
        print(f"   └─ {details}")

def diagnose_system():
    """Diagnosticar sistema completo"""
    print("🔍 DIAGNÓSTICO DEL SISTEMA - ARK SERVER MANAGER")
    
    # Información del sistema
    print_header("INFORMACIÓN DEL SISTEMA")
    print(f"🖥️  Sistema Operativo: {platform.system()} {platform.release()}")
    print(f"🏗️  Arquitectura: {platform.architecture()[0]}")
    print(f"🐍  Python: {platform.python_version()}")
    print(f"📁  Directorio de trabajo: {os.getcwd()}")
    
    # Verificar Python y módulos críticos
    print_header("VERIFICACIÓN DE DEPENDENCIAS")
    
    # Lista de módulos críticos
    critical_modules = [
        ('customtkinter', 'Interfaz gráfica principal'),
        ('tkinter', 'Biblioteca GUI base'),
        ('PIL', 'Manejo de imágenes'),
        ('psutil', 'Información del sistema'),
        ('requests', 'Conexiones HTTP'),
        ('schedule', 'Programación de tareas'),
        ('pystray', 'Bandeja del sistema'),
        ('win10toast', 'Notificaciones Windows'),
        ('configparser', 'Gestión de configuración'),
        ('pathlib', 'Manejo de rutas'),
        ('threading', 'Hilos de ejecución'),
        ('subprocess', 'Ejecución de procesos'),
        ('json', 'Serialización de datos'),
        ('logging', 'Sistema de logs'),
    ]
    
    for module_name, description in critical_modules:
        try:
            if module_name == 'PIL':
                import PIL
                import PIL.Image
                import PIL.ImageTk
            else:
                __import__(module_name)
            print_check(f"{module_name}: {description}", True)
        except ImportError as e:
            print_check(f"{module_name}: {description}", False, f"Error: {e}")
        except Exception as e:
            print_check(f"{module_name}: {description}", False, f"Error inesperado: {e}")
    
    # Verificar CustomTkinter específicamente
    print_header("VERIFICACIÓN DE CUSTOMTKINTER")
    try:
        import customtkinter as ctk
        print_check("Importación de CustomTkinter", True)
        
        # Probar configuración de tema
        try:
            original_mode = ctk.get_appearance_mode()
            print_check(f"Tema actual", True, f"'{original_mode}'")
            
            # Probar cambios de tema
            for theme in ['light', 'dark', 'system']:
                try:
                    ctk.set_appearance_mode(theme)
                    current = ctk.get_appearance_mode()
                    print_check(f"Cambio a tema '{theme}'", True, f"Actual: '{current}'")
                except Exception as e:
                    print_check(f"Cambio a tema '{theme}'", False, f"Error: {e}")
            
            # Restaurar tema original
            ctk.set_appearance_mode(original_mode)
            
        except Exception as e:
            print_check("Configuración de tema", False, f"Error: {e}")
            
        # Probar creación de ventana básica
        try:
            test_window = ctk.CTk()
            test_window.withdraw()  # Ocultar inmediatamente
            test_window.destroy()
            print_check("Creación de ventana CTk", True)
        except Exception as e:
            print_check("Creación de ventana CTk", False, f"Error: {e}")
            
    except Exception as e:
        print_check("CustomTkinter", False, f"Error crítico: {e}")
    
    # Verificar archivos del proyecto
    print_header("VERIFICACIÓN DE ARCHIVOS DEL PROYECTO")
    
    essential_files = [
        ('main.py', 'Archivo principal'),
        ('main.spec', 'Configuración de PyInstaller'),
        ('requirements.txt', 'Lista de dependencias'),
        ('config.ini', 'Archivo de configuración'),
        ('gui/main_window.py', 'Ventana principal'),
        ('gui/dialogs/initial_setup.py', 'Configuración inicial'),
        ('gui/dialogs/advanced_settings_dialog.py', 'Configuraciones avanzadas'),
        ('utils/config_manager.py', 'Gestor de configuración'),
        ('utils/logger.py', 'Sistema de logging'),
        ('utils/app_settings.py', 'Configuraciones de aplicación'),
    ]
    
    for file_path, description in essential_files:
        exists = os.path.exists(file_path)
        print_check(f"{file_path}: {description}", exists)
        
    # Verificar directorios
    essential_dirs = [
        ('gui', 'Interfaz gráfica'),
        ('utils', 'Utilidades'),
        ('data', 'Datos de aplicación'),
        ('logs', 'Archivos de log'),
        ('ico', 'Iconos'),
    ]
    
    for dir_path, description in essential_dirs:
        exists = os.path.exists(dir_path) and os.path.isdir(dir_path)
        print_check(f"{dir_path}/: {description}", exists)
    
    # Verificar permisos
    print_header("VERIFICACIÓN DE PERMISOS")
    
    current_dir = os.getcwd()
    try:
        # Probar escritura
        test_file = os.path.join(current_dir, "test_write.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print_check("Permisos de escritura en directorio actual", True)
    except Exception as e:
        print_check("Permisos de escritura en directorio actual", False, f"Error: {e}")
    
    # Probar creación de directorios
    try:
        test_dir = os.path.join(current_dir, "test_dir_tmp")
        os.makedirs(test_dir, exist_ok=True)
        os.rmdir(test_dir)
        print_check("Creación de directorios", True)
    except Exception as e:
        print_check("Creación de directorios", False, f"Error: {e}")
    
    # Verificar configuración existente
    print_header("VERIFICACIÓN DE CONFIGURACIÓN")
    
    try:
        from utils.config_manager import ConfigManager
        config = ConfigManager()
        config.load_config()
        
        # Verificar secciones importantes
        sections = ['server', 'app', 'backup', 'logs']
        for section in sections:
            has_section = config.has_section(section)
            print_check(f"Sección [{section}] en config.ini", has_section)
        
        # Verificar configuración del tema
        theme = config.get('app', 'theme', 'dark')
        print_check(f"Tema configurado", True, f"'{theme}'")
        
    except Exception as e:
        print_check("Carga de configuración", False, f"Error: {e}")
    
    # Verificar configuraciones avanzadas
    try:
        from utils.app_settings import AppSettings
        from utils.logger import Logger
        
        logger = Logger()
        app_settings = AppSettings(ConfigManager(), logger)
        
        theme_mode = app_settings.get_setting('theme_mode', 'system')
        print_check(f"Configuraciones avanzadas", True, f"Tema: '{theme_mode}'")
        
    except Exception as e:
        print_check("Configuraciones avanzadas", False, f"Error: {e}")

def main():
    """Función principal"""
    try:
        diagnose_system()
        
        print_header("RESUMEN")
        print("✅ Diagnóstico completado")
        print("📄 Revisa los resultados arriba para identificar problemas")
        print("\n💡 RECOMENDACIONES:")
        print("   • Si hay módulos faltantes: pip install -r requirements.txt")
        print("   • Si CustomTkinter falla: pip install --upgrade customtkinter")
        print("   • Si hay errores de permisos: ejecuta como administrador")
        print("   • Si faltan archivos: verifica la integridad del proyecto")
        
    except Exception as e:
        print(f"\n❌ Error durante el diagnóstico: {e}")
        print(f"Traceback completo:")
        print(traceback.format_exc())
    
    print(f"\n{'='*60}")
    input("Presiona Enter para continuar...")

if __name__ == "__main__":
    main()
