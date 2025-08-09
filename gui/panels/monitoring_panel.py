import customtkinter as ctk
from .advanced_restart_panel import AdvancedRestartPanel

class MonitoringPanel(ctk.CTkFrame):
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
            # Crear el panel avanzado de reinicios
            self.advanced_restart_panel = AdvancedRestartPanel(self, config_manager, logger, main_window)
        except Exception as e:
            self.logger.error(f"Error al crear panel de reinicios avanzado: {e}")
            # Si falla, mostrar mensaje de error
            self.show_error_fallback(str(e))
    
    def show_error_fallback(self, error_msg):
        """Mostrar mensaje de error si falla el panel avanzado"""
        error_frame = ctk.CTkFrame(self)
        error_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        error_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            error_frame,
            text="⚠️ Error en Panel de Reinicios",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="orange"
        )
        title_label.grid(row=0, column=0, pady=(20, 10))
        
        error_label = ctk.CTkLabel(
            error_frame,
            text=f"No se pudo cargar el panel de reinicios:\n{error_msg}",
            font=ctk.CTkFont(size=12),
            text_color="red"
        )
        error_label.grid(row=1, column=0, pady=10)
        
        info_label = ctk.CTkLabel(
            error_frame,
            text="El panel de reinicios avanzado está en desarrollo.\n"
                 "Por favor verifica las dependencias.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        info_label.grid(row=2, column=0, pady=10)
        
        retry_button = ctk.CTkButton(
            error_frame,
            text="🔄 Reintentar",
            command=self.retry_advanced_panel,
            width=150
        )
        retry_button.grid(row=3, column=0, pady=20)
    
    def retry_advanced_panel(self):
        """Reintentar crear el panel avanzado"""
        # Limpiar contenido actual
        for widget in self.winfo_children():
            widget.destroy()
        
        try:
            self.advanced_restart_panel = AdvancedRestartPanel(self, self.config_manager, self.logger, self.main_window)
        except Exception as e:
            self.logger.error(f"Error al reintentar panel de reinicios: {e}")
            self.show_error_fallback(str(e))
    
    def update_server_selection(self, server_name):
        """Notificar cambio de servidor al panel de reinicios"""
        if hasattr(self, 'advanced_restart_panel'):
            self.advanced_restart_panel.update_server_selection(server_name)