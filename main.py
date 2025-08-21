import customtkinter as ctk
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent))

from gui.main_window import MainWindow
from gui.dialogs.initial_setup import InitialSetupDialog
from utils.config_manager import ConfigManager
from utils.logger import Logger

class ArkServerManager:
    def __init__(self):
        # Configurar CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Crear carpetas esenciales temprano para evitar errores de permisos
        self._ensure_essential_directories()
        
        # Inicializar configuraciones con manejo de errores
        try:
            self.config_manager = ConfigManager()
            self.config_manager.load_config()  # Cargar explícitamente
            self.logger = Logger()
            self.logger.info("Sistema de configuración inicializado correctamente")
        except Exception as e:
            # Crear logger básico para reportar error
            import logging
            logging.basicConfig(level=logging.ERROR)
            logging.error(f"Error crítico al inicializar configuración: {e}")
            # Continuar con configuración por defecto
            self.config_manager = ConfigManager()
            self.logger = Logger()
        
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
                        print(f"✅ Directorio creado/verificado: {dir_name}")
                    else:
                        print(f"⚠️ Directorio sin permisos de escritura: {dir_name}")
                        # Intentar corregir permisos en Windows
                        if os.name == 'nt':
                            self._fix_windows_permissions(dir_path)
                            
                except (OSError, PermissionError) as e:
                    print(f"❌ Error creando directorio {dir_name}: {e}")
                    # Mostrar mensaje de ayuda específico para Windows
                    if os.name == 'nt':
                        self._show_windows_permission_help(dir_name, str(e))
                        
        except Exception as e:
            print(f"❌ Error general creando directorios esenciales: {e}")
    
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

def main():
    """Función principal"""
    app = ArkServerManager()
    app.run()

if __name__ == "__main__":
    main()
