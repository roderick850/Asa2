import customtkinter as ctk
import os
from tkinter import filedialog
from .server_config_panel import ServerConfigPanel

class ConfigPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger, main_window=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        
        # Configurar el layout del frame principal
        self.pack(fill="both", expand=True)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        try:
            # Crear el panel específico por servidor
            self.server_config_panel = ServerConfigPanel(self, config_manager, logger, main_window)
        except Exception as e:
            self.logger.error(f"Error al crear panel de configuración: {e}")
            # Si falla, mostrar mensaje de error
            self.show_error_fallback(str(e))
    
    def show_error_fallback(self, error_msg):
        """Mostrar mensaje de error si falla el panel dinámico"""
        error_frame = ctk.CTkFrame(self)
        error_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        error_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            error_frame,
            text="⚠️ Error en Panel de Configuración",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="orange"
        )
        title_label.grid(row=0, column=0, pady=(20, 10))
        
        error_label = ctk.CTkLabel(
            error_frame,
            text=f"No se pudo cargar el panel dinámico:\n{error_msg}",
            font=ctk.CTkFont(size=12),
            text_color="red"
        )
        error_label.grid(row=1, column=0, pady=10)
        
        info_label = ctk.CTkLabel(
            error_frame,
            text="El panel de configuración dinámica está en desarrollo.\n"
                 "Usa la pestaña 'Principal' para configuraciones básicas.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        info_label.grid(row=2, column=0, pady=10)
        
        retry_button = ctk.CTkButton(
            error_frame,
            text="🔄 Reintentar",
            command=self.retry_dynamic_panel,
            width=150
        )
        retry_button.grid(row=3, column=0, pady=20)
    
    def retry_dynamic_panel(self):
        """Reintentar crear el panel dinámico"""
        # Limpiar contenido actual
        for widget in self.winfo_children():
            widget.destroy()
        
        try:
            self.server_config_panel = ServerConfigPanel(self, self.config_manager, self.logger, self.main_window)
        except Exception as e:
            self.logger.error(f"Error al reintentar panel de configuración: {e}")
            self.show_error_fallback(str(e))
    
    def update_server_selection(self, server_name):
        """Notificar cambio de servidor al panel de configuración"""
        if hasattr(self, 'server_config_panel'):
            self.server_config_panel.update_server_selection(server_name)