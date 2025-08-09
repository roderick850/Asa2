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

def main():
    """Función principal"""
    app = ArkServerManager()
    app.run()

if __name__ == "__main__":
    main()
