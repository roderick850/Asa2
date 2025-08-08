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
        
        # Inicializar configuraciones
        self.config_manager = ConfigManager()
        self.logger = Logger()
        
        # Crear ventana principal
        self.root = ctk.CTk()
        self.root.title("Ark Survival Ascended - Administrador de Servidores")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
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
        self.root.withdraw()  # Ocultar ventana principal
        
        setup_dialog = InitialSetupDialog(self.root, self.config_manager, self.logger)
        
        if setup_dialog.result:
            self.root.deiconify()  # Mostrar ventana principal
        else:
            # Si el usuario canceló, cerrar la aplicación
            self.root.quit()

def main():
    """Función principal"""
    app = ArkServerManager()
    app.run()

if __name__ == "__main__":
    main()
