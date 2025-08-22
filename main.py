import customtkinter as ctk
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent))

# SOLUCIÓN FINAL: Sistema global de directorios seguros con caché
import os
import tempfile

class SafeDirectoryManager:
    """Gestor global de directorios con fallback automático"""
    
    def __init__(self):
        self.temp_directories = {}  # Cache de directorios temporales
        self.original_makedirs = os.makedirs
        
    def safe_makedirs(self, path, mode=0o777, exist_ok=False):
        """Versión segura con fallback automático a directorios temporales"""
        try:
            # Intentar crear directorio normalmente
            result = self.original_makedirs(path, mode=mode, exist_ok=exist_ok)
            return result
        except (OSError, PermissionError) as e:
            # Verificar si es un directorio de la aplicación
            path_str = str(path).lower()
            app_dirs = ['data', 'logs', 'config', 'backups', 'exports']
            
            if any(app_dir in path_str for app_dir in app_dirs):
                # Crear directorio temporal y guardarlo en caché
                normalized_path = os.path.normpath(path)
                
                if normalized_path not in self.temp_directories:
                    dir_name = os.path.basename(path) or "app_data"
                    temp_dir = tempfile.mkdtemp(prefix=f"ArkSM_{dir_name}_")
                    self.temp_directories[normalized_path] = temp_dir
                    print(f"⚠️ Permisos: {dir_name} → {temp_dir}")
                
                # No lanzar error, dejar que continúe con el directorio temporal
                return None
            else:
                # Si no es directorio de la app, relanzar error original
                raise e
    
    def get_safe_path(self, original_path):
        """Obtener ruta segura (temporal si es necesario)"""
        normalized_path = os.path.normpath(original_path)
        return self.temp_directories.get(normalized_path, original_path)

# Crear instancia global
_safe_dir_manager = SafeDirectoryManager()

# Parchar os.makedirs
os.makedirs = _safe_dir_manager.safe_makedirs

print("🔧 Sistema de directorios globalmente seguro activado")

from gui.main_window import MainWindow
from gui.dialogs.initial_setup import InitialSetupDialog
from utils.config_manager import ConfigManager
from utils.logger import Logger

class ArkServerManager:
    def __init__(self):
        # Configurar CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        print("🚀 Iniciando Ark Server Manager...")
        
        # Obtener directorio base
        if hasattr(sys, '_MEIPASS'):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        print(f"📁 Directorio base: {base_dir}")
        
        # Crear carpetas esenciales (ahora usando el sistema seguro)
        self._ensure_essential_directories_simple()
        
        # Inicializar configuraciones con manejo de errores robusto
        try:
            self.config_manager = ConfigManager()
            self.config_manager.load_config()  # Cargar explícitamente
            self.logger = Logger()
            self.logger.info("Sistema de configuración inicializado correctamente")
            print("✅ Sistema de configuración inicializado")
        except Exception as e:
            # Crear logger básico para reportar error
            import logging
            logging.basicConfig(level=logging.ERROR)
            logging.error(f"Error crítico al inicializar configuración: {e}")
            print(f"⚠️ Error en configuración, usando valores por defecto: {e}")
            # Continuar con configuración por defecto
            try:
                self.config_manager = ConfigManager()
                self.logger = Logger()
                print("✅ Sistema de configuración inicializado en modo fallback")
            except Exception as fallback_error:
                print(f"❌ Error crítico en modo fallback: {fallback_error}")
                # Crear configuración mínima para que la app pueda continuar
                self.config_manager = None
                self.logger = None
        
        # Crear ventana principal
        self.root = ctk.CTk()
        self.root.title("Ark Survival Ascended - Administrador de Servidores")
        self.root.geometry("1200x900")
        self.root.minsize(800, 500)
        
        # Configurar icono de la ventana
        try:
            icon_path = Path(__file__).parent / "ico" / "ArkManager.ico"
            if icon_path.exists():
                self.root.wm_iconbitmap(str(icon_path))
            else:
                self.logger.warning(f"Icono no encontrado en: {icon_path}")
        except Exception as e:
            self.logger.warning(f"Error al configurar icono: {e}")
        
        # Verificar si es la primera vez que se ejecuta
        if not self.check_initial_setup():
            self.show_initial_setup()
        
        # Inicializar la interfaz principal
        self.main_window = MainWindow(self.root, self.config_manager, self.logger)
        
    def run(self):
        """Ejecutar la aplicación"""
        try:
            self.logger.info("Iniciando Ark Server Manager...")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Error al ejecutar la aplicación: {e}")
            sys.exit(1)
    
    def check_initial_setup(self):
        """Verificar si ya se ha configurado la ruta raíz"""
        root_path = self.config_manager.get("server", "root_path")
        return bool(root_path and root_path.strip())
    
    def show_initial_setup(self):
        """Mostrar diálogo de configuración inicial"""
        try:
            self.logger.info("=== INICIANDO CONFIGURACIÓN INICIAL ===")
            self.root.withdraw()  # Ocultar ventana principal
            self.logger.info("Ventana principal ocultada")
            
            # Dar tiempo a que la ventana se oculte
            self.root.update()
            
            self.logger.info("Creando diálogo de configuración inicial...")
            setup_dialog = InitialSetupDialog(self.root, self.config_manager, self.logger)
            self.logger.info(f"Diálogo creado. Resultado: {setup_dialog.result}")
            
            # Verificar el resultado después de que el diálogo se cierre
            if setup_dialog.result:
                self.logger.info("Configuración inicial completada exitosamente")
                # Verificar que realmente se guardó la configuración
                root_path = self.config_manager.get("server", "root_path")
                if root_path and root_path.strip():
                    self.logger.info(f"Ruta configurada: {root_path}")
                    self.root.deiconify()  # Mostrar ventana principal
                    self.logger.info("Ventana principal mostrada")
                else:
                    self.logger.warning("La configuración no se guardó correctamente")
                    self._handle_failed_setup()
            else:
                self.logger.warning("Configuración inicial cancelada por el usuario")
                # Si el usuario canceló, cerrar la aplicación
                self.logger.info("Cerrando aplicación por cancelación de usuario")
                self.root.quit()
                
        except Exception as e:
            self.logger.error(f"Error crítico durante la configuración inicial: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self._handle_failed_setup()
    
    def _handle_failed_setup(self):
        """Manejar fallo en la configuración inicial"""
        try:
            # Mostrar ventana principal de todas formas
            self.root.deiconify()
            
            # Mostrar mensaje de error al usuario después de un momento
            self.root.after(1000, lambda: self._show_setup_error())
            
        except Exception as e:
            self.logger.error(f"Error crítico al manejar fallo de configuración: {e}")
            # Último recurso: salir de la aplicación
            self.root.quit()
    
    def _show_setup_error(self):
        """Mostrar error de configuración al usuario"""
        try:
            import tkinter.messagebox as msgbox
            response = msgbox.askretrycancel(
                "Error de Configuración", 
                "Error durante la configuración inicial.\n\n"
                "La aplicación continuará, pero necesitarás configurar "
                "la ruta del servidor manualmente desde el menú.\n\n"
                "¿Quieres continuar?"
            )
            
            if not response:
                self.root.quit()
                
        except Exception as e:
            self.logger.error(f"Error al mostrar mensaje de configuración: {e}")
    
    def _ensure_essential_directories(self):
        """Crear directorios esenciales al inicio para evitar errores de permisos"""
        success = True
        failed_dirs = []
        
        try:
            # Obtener directorio base de la aplicación
            if hasattr(sys, '_MEIPASS'):
                # Si estamos en un ejecutable de PyInstaller
                base_dir = os.path.dirname(sys.executable)
            else:
                # Si estamos en desarrollo
                base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Lista de directorios esenciales
            essential_dirs = [
                'data',
                'logs',
                'config',
                'backups',
                'exports'
            ]
            
            print(f"📁 Verificando directorios esenciales en: {base_dir}")
            
            # Crear cada directorio si no existe
            for dir_name in essential_dirs:
                dir_path = os.path.join(base_dir, dir_name)
                try:
                    # Crear directorio con permisos específicos para Windows
                    if os.name == 'nt':  # Windows
                        self._create_directory_with_windows_permissions(dir_path)
                    else:
                        os.makedirs(dir_path, exist_ok=True)
                    
                    # Verificar que el directorio es accesible
                    if os.access(dir_path, os.W_OK):
                        print(f"✅ Directorio OK: {dir_name}")
                    else:
                        print(f"⚠️ Sin permisos de escritura: {dir_name}")
                        # Intentar corregir permisos en Windows
                        if os.name == 'nt':
                            if self._fix_windows_permissions(dir_path):
                                print(f"✅ Permisos corregidos: {dir_name}")
                            else:
                                failed_dirs.append(dir_name)
                                success = False
                        else:
                            failed_dirs.append(dir_name)
                            success = False
                            
                except (OSError, PermissionError) as e:
                    print(f"❌ Error con directorio {dir_name}: {e}")
                    failed_dirs.append(dir_name)
                    success = False
                    
                    # Mostrar mensaje de ayuda específico para Windows
                    if os.name == 'nt':
                        self._show_windows_permission_help(dir_name, str(e))
            
            if failed_dirs:
                print(f"⚠️ Directorios con problemas: {', '.join(failed_dirs)}")
                        
        except Exception as e:
            print(f"❌ Error general creando directorios esenciales: {e}")
            success = False
        
        return success
    
    def _create_directory_with_windows_permissions(self, dir_path):
        """Crear directorio con permisos específicos para Windows"""
        try:
            os.makedirs(dir_path, exist_ok=True)
            
            # En Windows, intentar establecer permisos completos para el usuario actual
            if os.name == 'nt':
                import subprocess
                import getpass
                
                username = getpass.getuser()
                # Comando para dar permisos completos al usuario actual
                cmd = f'icacls "{dir_path}" /grant "{username}":F /T'
                
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"✅ Permisos establecidos para {dir_path}")
                    else:
                        print(f"⚠️ No se pudieron establecer permisos automáticamente para {dir_path}")
                except Exception as perm_error:
                    print(f"⚠️ Error estableciendo permisos: {perm_error}")
                    
        except Exception as e:
            raise e
    
    def _fix_windows_permissions(self, dir_path):
        """Intentar corregir permisos en Windows"""
        try:
            import subprocess
            import getpass
            
            username = getpass.getuser()
            # Comando para dar permisos completos al usuario actual
            cmd = f'icacls "{dir_path}" /grant "{username}":F /T'
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Permisos corregidos para {dir_path}")
                return True
            else:
                print(f"❌ No se pudieron corregir permisos para {dir_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error corrigiendo permisos: {e}")
            return False
    
    def _show_windows_permission_help(self, dir_name, error_msg):
        """Mostrar ayuda específica para problemas de permisos en Windows"""
        help_message = f"""
        ❌ ERROR DE PERMISOS EN WINDOWS - {dir_name.upper()}
        
        Error: {error_msg}
        
        SOLUCIONES POSIBLES:
        
        1. EJECUTAR COMO ADMINISTRADOR:
           - Cierra la aplicación
           - Haz clic derecho en el ejecutable
           - Selecciona "Ejecutar como administrador"
        
        2. CAMBIAR UBICACIÓN:
           - Mueve la aplicación a una carpeta como:
             • C:\\ArkServerManager\\
             • Documentos\\ArkServerManager\\
        
        3. CONFIGURAR PERMISOS MANUALMENTE:
           - Haz clic derecho en la carpeta de la aplicación
           - Propiedades → Seguridad → Editar
           - Dar "Control total" a tu usuario
        
        4. DESACTIVAR ANTIVIRUS TEMPORALMENTE:
           - Algunos antivirus bloquean la creación de carpetas
           - Agrega la aplicación a las excepciones
        """
        
        print(help_message)
        
        # También intentar crear un archivo de ayuda
        try:
            help_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SOLUCION_PERMISOS_WINDOWS.txt")
            with open(help_file, 'w', encoding='utf-8') as f:
                f.write(help_message)
            print(f"📄 Archivo de ayuda creado: {help_file}")
        except:
            pass
    
    def _ensure_essential_directories_simple(self):
        """Crear directorios esenciales usando el sistema seguro"""
        essential_dirs = ['data', 'logs', 'config', 'backups', 'exports']
        
        print("📁 Creando directorios esenciales...")
        
        # Obtener directorio base
        if hasattr(sys, '_MEIPASS'):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        for dir_name in essential_dirs:
            try:
                # El sistema global manejará automáticamente los errores
                dir_path = os.path.join(base_dir, dir_name)
                os.makedirs(dir_path, exist_ok=True)
                
                # Verificar si se usó un directorio temporal
                safe_path = _safe_dir_manager.get_safe_path(dir_path)
                if safe_path != dir_path:
                    print(f"⚠️ {dir_name}: Usando directorio temporal")
                else:
                    print(f"✅ {dir_name}: OK")
                    
            except Exception as e:
                print(f"❌ Error crítico con directorio {dir_name}: {e}")
        
        print("✅ Directorios esenciales procesados")
    
    def _show_permission_warning(self):
        """Mostrar advertencia sobre problemas de permisos"""
        print("\n" + "="*60)
        print("⚠️  ADVERTENCIA: PROBLEMAS DE PERMISOS DETECTADOS")
        print("="*60)
        print("La aplicación puede no funcionar correctamente.")
        print("Se intentará usar directorios temporales alternativos.")
        print("Para una experiencia óptima, considera:")
        print("  1. Ejecutar como administrador")
        print("  2. Mover la aplicación a una ubicación con permisos")
        print("  3. Verificar configuración del antivirus")
        print("="*60 + "\n")

def main():
    """Función principal"""
    app = ArkServerManager()
    app.run()

if __name__ == "__main__":
    main()
