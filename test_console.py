#!/usr/bin/env python3
"""
Script de prueba para verificar que la consola del servidor funcione correctamente
"""

import customtkinter as ctk
import sys
import os

# Agregar el directorio raíz al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.panels.working_logs_panel import WorkingLogsPanel
from utils.config_manager import ConfigManager
from utils.logger import Logger

def main():
    """Función principal de prueba"""
    # Configurar CustomTkinter
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Crear ventana principal
    root = ctk.CTk()
    root.title("Prueba de Consola del Servidor")
    root.geometry("1200x800")
    
    # Configurar grid de la ventana principal
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)
    
    # Crear instancias necesarias
    config_manager = ConfigManager()
    logger = Logger()
    
    # Crear el panel de logs
    logs_panel = WorkingLogsPanel(root, config_manager, logger, root)
    logs_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    # Botón de prueba
    test_button = ctk.CTkButton(
        root,
        text="🧪 Probar Consola",
        command=lambda: logs_panel.force_console_update(),
        fg_color="green"
    )
    test_button.grid(row=1, column=0, pady=10)
    
    # Botón de debug
    debug_button = ctk.CTkButton(
        root,
        text="🐛 Debug Widgets",
        command=lambda: logs_panel.debug_widgets(),
        fg_color="purple"
    )
    debug_button.grid(row=2, column=0, pady=5)
    
    print("✅ Aplicación de prueba iniciada")
    print("📋 Panel de logs creado")
    print("🎮 Consola del servidor inicializada")
    print("🔍 Usa los botones para probar la funcionalidad")
    
    # Iniciar la aplicación
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error al ejecutar la aplicación de prueba: {e}")
        import traceback
        traceback.print_exc()
