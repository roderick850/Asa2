import customtkinter as ctk
import os
from datetime import datetime
import threading
import time
import subprocess
from pathlib import Path

class WorkingLogsPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger, main_window=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        
        # Asegurar que este frame se expanda
        self.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configurar grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Variables de estado para la consola
        self.console_active = False
        self.console_buffer = []
        self.max_buffer_lines = 1000
        self.auto_scroll = True
        self.start_time = datetime.now()
        self.monitoring_thread = None
        
        # Variables para conexión RCON real
        self.rcon_ip = "127.0.0.1"
        self.rcon_port = "27020"
        self.rcon_password = ""
        self.is_connected = False
        
        # Variables para monitoreo directo de logs
        self.log_files = {}
        self.log_file_positions = {}
        self.server_logs_path = None
        self.ark_process = None
        
        self.create_interface()
        self.load_initial_content()
        
        # Debug: verificar estado de widgets después de la inicialización
        if hasattr(self, 'after'):
            self.after(1000, self.debug_widgets)  # Ejecutar después de 1 segundo
        else:
            # Fallback: ejecutar directamente
            self.debug_widgets()
        
        # Cargar configuración RCON
        if hasattr(self, 'after'):
            self.after(2000, self.load_rcon_config)
        else:
            # Fallback: cargar directamente
            self.load_rcon_config()
    
    def load_rcon_config(self):
        """Cargar configuración RCON desde el config manager"""
        try:
            # Obtener configuración RCON desde la sección [rcon]
            rcon_ip = self.config_manager.get("rcon", "ip", "127.0.0.1")
            rcon_port = self.config_manager.get("rcon", "port", "27030")
            
            # Obtener password desde la sección [server] usando AdminPassword
            admin_password = self.config_manager.get("server", "admin_password", "")
            
            # Si hay un servidor seleccionado, usar su IP específica si está disponible
            if hasattr(self.main_window, 'selected_server') and self.main_window.selected_server:
                # Intentar obtener IP específica del servidor desde multihome
                multihome = self.config_manager.get("server", "multihome", "")
                if multihome and multihome != "127.0.0.1":
                    rcon_ip = multihome
                    self.logger.info(f"Usando IP del servidor: {rcon_ip}")
                    
                    # Debug: verificar si es un hostname y resolverlo
                    try:
                        import socket
                        resolved_ip = socket.gethostbyname(multihome)
                        self.logger.info(f"Hostname {multihome} resuelto a IP: {resolved_ip}")
                        if resolved_ip != multihome:
                            rcon_ip = resolved_ip
                    except Exception as e:
                        self.logger.warning(f"No se pudo resolver hostname {multihome}: {e}")
            
            if admin_password:
                self.rcon_ip = rcon_ip
                self.rcon_port = str(rcon_port)
                self.rcon_password = admin_password
                
                self.logger.info(f"Configuración RCON cargada: {self.rcon_ip}:{self.rcon_port}")
                
                # Intentar conectar automáticamente
                if hasattr(self, 'after'):
                    self.after(1000, self.auto_connect_to_server)
                else:
                    # Fallback: conectar directamente
                    self.auto_connect_to_server()
            else:
                self.logger.warning("No se encontró AdminPassword para conexión RCON")
                
                # Solo mostrar mensaje de configuración en consola, no errores RCON
                self.add_console_line("⚠️ Configuración RCON incompleta", "warning")
                self.add_console_line("💡 Verifica la configuración del servidor", "info")
                
        except Exception as e:
            self.logger.error(f"Error al cargar configuración RCON: {e}")
            # Solo log, no mostrar en consola
    
    def auto_connect_to_server(self):
        """Conectar automáticamente al servidor si está disponible"""
        try:
            if not self.is_connected:
                # Solo log, no mostrar en consola
                self.logger.info("Conectando automáticamente al servidor...")
                
                # Intentar RCON primero si hay password
                if self.rcon_password:
                    self.connect_to_server_console(self.rcon_ip, self.rcon_port, self.rcon_password)
                else:
                    # Si no hay RCON, intentar conexión directa
                    self.logger.info("No hay password RCON, intentando conexión directa...")
                    if self.connect_to_server_direct():
                        self.is_connected = True
                        self.set_console_active(True)
                        self.add_console_line("🎮 Consola del servidor ARK activa (Captura directa)", "success")
                        self.start_direct_monitoring()
                        
        except Exception as e:
            self.logger.error(f"Error en conexión automática: {e}")

    def create_interface(self):
        """Crear la interfaz con sistema de pestañas"""
        # Título principal
        title = ctk.CTkLabel(
            self, 
            text="📋 Panel de Logs y Consola del Servidor", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.grid(row=0, column=0, pady=10, sticky="w")
        
        # Crear sistema de pestañas
        self.create_tabview()
        
    def create_tabview(self):
        """Crear el sistema de pestañas interno"""
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", pady=5)
        
        # Configurar expansión del tabview
        self.tabview.grid_columnconfigure(0, weight=1)
        self.tabview.grid_rowconfigure(0, weight=1)
        
        # Crear pestañas
        self.tab_system = self.tabview.add("📋 Sistema")
        self.tab_console = self.tabview.add("🎮 Consola")
        self.tab_events = self.tabview.add("📊 Eventos")
        self.tab_app = self.tabview.add("📱 Aplicación")
        
        # Configurar expansión de cada pestaña
        self.tab_system.grid_columnconfigure(0, weight=1)
        self.tab_system.grid_rowconfigure(1, weight=1)
        
        self.tab_console.grid_columnconfigure(0, weight=1)
        self.tab_console.grid_rowconfigure(1, weight=1)
        
        self.tab_events.grid_columnconfigure(0, weight=1)
        self.tab_events.grid_rowconfigure(1, weight=1)
        
        self.tab_app.grid_columnconfigure(0, weight=1)
        self.tab_app.grid_rowconfigure(1, weight=1)
        
        # Crear contenido para cada pestaña
        self.create_system_tab()
        self.create_console_tab()
        self.create_events_tab()
        self.create_app_tab()
        
    def create_system_tab(self):
        """Crear pestaña de logs del sistema"""
        # Frame de botones
        button_frame = ctk.CTkFrame(self.tab_system)
        button_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        button_frame.grid_columnconfigure(0, weight=1)
        
        # Botones
        ctk.CTkButton(
            button_frame,
            text="🔄 Actualizar",
            command=self.refresh_system_logs,
            width=100,
            fg_color="orange"
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        ctk.CTkButton(
            button_frame,
            text="🗑️ Limpiar",
            command=self.clear_system_logs,
            width=100,
            fg_color="red"
        ).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Área de texto
        self.system_text = ctk.CTkTextbox(
            self.tab_system,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.system_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
    def create_console_tab(self):
        """Crear pestaña de consola del servidor"""
        # Frame superior con controles
        control_frame = ctk.CTkFrame(self.tab_console)
        control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        control_frame.grid_columnconfigure(1, weight=1)
        
        # Frame de botones
        button_frame = ctk.CTkFrame(control_frame)
        button_frame.grid(row=0, column=0, padx=10, pady=5, sticky="e")
        
        # Botón de conexión
        self.connect_btn = ctk.CTkButton(
            button_frame, 
            text="🔌 Conectar", 
            command=self.manual_connect,
            width=80,
            fg_color="green"
        )
        self.connect_btn.grid(row=0, column=0, padx=5, pady=5)
        
        # Botón de desconexión
        self.disconnect_btn = ctk.CTkButton(
            button_frame, 
            text="🔌 Desconectar", 
            command=self.disconnect_from_server,
            width=80,
            fg_color="red"
        )
        self.disconnect_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # Botones de control
        self.console_clear_btn = ctk.CTkButton(
            button_frame, 
            text="🧹 Limpiar", 
            command=self.clear_console,
            width=80
        )
        self.console_clear_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.console_export_btn = ctk.CTkButton(
            button_frame, 
            text="📁 Exportar", 
            command=self.export_console,
            width=80
        )
        self.console_export_btn.grid(row=0, column=3, padx=5, pady=5)
        
        # Checkbox auto-scroll
        self.auto_scroll_var = ctk.BooleanVar(value=True)
        self.auto_scroll_check = ctk.CTkCheckBox(
            button_frame,
            text="📜 Auto-scroll",
            variable=self.auto_scroll_var,
            command=self.toggle_auto_scroll
        )
        self.auto_scroll_check.grid(row=0, column=4, padx=10, pady=5)
        
        # Botón de estadísticas de consola
        self.debug_btn = ctk.CTkButton(
            button_frame,
            text="📊 Stats",
            command=self.show_console_stats,
            width=60,
            fg_color="purple"
        )
        self.debug_btn.grid(row=0, column=5, padx=5, pady=5)
        
        # Botón de actualización forzada
        self.force_update_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Forzar",
            command=self.force_console_update,
            width=60,
            fg_color="blue"
        )
        self.force_update_btn.grid(row=0, column=6, padx=5, pady=5)
        
        # Botón de expansión forzada
        self.expand_btn = ctk.CTkButton(
            button_frame,
            text="📏 Expandir",
            command=self.open_console_window,
            width=70,
            fg_color="green"
        )
        self.expand_btn.grid(row=0, column=7, padx=5, pady=5)
        
        # Frame de filtros de consola
        filter_frame = ctk.CTkFrame(self.tab_console)
        filter_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        filter_frame.grid_columnconfigure(1, weight=1)
        
        # Título de filtros
        filter_title = ctk.CTkLabel(
            filter_frame,
            text="🔍 Filtros de Consola:",
            font=("Arial", 10, "bold")
        )
        filter_title.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")
        
        # Checkbox para mostrar mensajes internos de la app
        self.show_app_messages_var = ctk.BooleanVar(value=False)
        self.show_app_messages_check = ctk.CTkCheckBox(
            filter_frame,
            text="Mostrar mensajes internos de la app",
            variable=self.show_app_messages_var,
            command=self.toggle_app_messages_filter
        )
        self.show_app_messages_check.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Checkbox para mostrar mensajes de estado del servidor
        self.show_status_messages_var = ctk.BooleanVar(value=False)
        self.show_status_messages_check = ctk.CTkCheckBox(
            filter_frame,
            text="Mostrar mensajes de estado del servidor",
            variable=self.show_status_messages_var,
            command=self.toggle_status_messages_filter
        )
        self.show_status_messages_check.grid(row=0, column=2, padx=10, pady=5, sticky="w")
        
        # Checkbox para mostrar solo mensajes del juego
        self.show_game_only_var = ctk.BooleanVar(value=True)
        self.show_game_only_check = ctk.CTkCheckBox(
            filter_frame,
            text="Solo mensajes del juego ARK",
            variable=self.show_game_only_var,
            command=self.toggle_game_only_filter
        )
        self.show_game_only_check.grid(row=0, column=3, padx=10, pady=5, sticky="w")
        
        # Botón para limpiar filtros
        self.clear_filters_btn = ctk.CTkButton(
            filter_frame,
            text="🧹 Limpiar Filtros",
            command=self.clear_filters,
            width=120,
            fg_color="orange"
        )
        self.clear_filters_btn.grid(row=0, column=4, padx=10, pady=5, sticky="e")
        
        # Área de la consola
        console_frame = ctk.CTkFrame(self.tab_console)
        console_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        # Texto de la consola - usar pack para asegurar expansión
        self.console_text = ctk.CTkTextbox(
            console_frame,
            font=("Consolas", 10),
            wrap="word"
        )
        self.console_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar - usar pack también
        self.console_scrollbar = ctk.CTkScrollbar(console_frame, command=self.console_text.yview)
        self.console_scrollbar.pack(side="right", fill="y")
        self.console_text.configure(yscrollcommand=self.console_scrollbar.set)
        
        # Frame inferior con información
        info_frame = ctk.CTkFrame(self.tab_console)
        info_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        info_frame.grid_columnconfigure(1, weight=1)
        
        # Información de líneas
        self.console_lines_label = ctk.CTkLabel(
            info_frame, 
            text="Líneas: 0", 
            font=("Arial", 10)
        )
        self.console_lines_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Estado de conexión
        self.connection_status_label = ctk.CTkLabel(
            info_frame,
            text="Estado: Desconectado",
            font=("Arial", 10),
            fg_color=("lightcoral", "darkred"),
            corner_radius=5,
            padx=8,
            pady=2
        )
        self.connection_status_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Última actualización
        self.last_update_label = ctk.CTkLabel(
            info_frame, 
            text="Última actualización: Nunca", 
            font=("Arial", 10)
        )
        self.last_update_label.grid(row=0, column=2, padx=10, pady=5, sticky="w")
        
        # Tamaño del buffer
        self.buffer_size_label = ctk.CTkLabel(
            info_frame, 
            text=f"Buffer: 0/{self.max_buffer_lines}", 
            font=("Arial", 10)
        )
        self.buffer_size_label.grid(row=0, column=3, padx=10, pady=5, sticky="w")
        
        # Tiempo de ejecución
        self.uptime_label = ctk.CTkLabel(
            info_frame, 
            text="Tiempo: 00:00:00", 
            font=("Arial", 10)
        )
        self.uptime_label.grid(row=0, column=4, padx=10, pady=5, sticky="w")
        
        # Inicializar estado de botones
        self.update_connection_buttons()
        
        # Configurar expansión específica para la pestaña de consola
        self.tab_console.grid_columnconfigure(0, weight=1)
        self.tab_console.grid_rowconfigure(1, weight=1)  # La fila del console_frame
        
        # Forzar actualización del layout
        self.tab_console.update_idletasks()
        
    def open_console_window(self):
        """Abrir la consola en una ventana independiente"""
        try:
            # Crear ventana independiente
            console_window = ctk.CTkToplevel(self)
            console_window.title("🎮 Consola del Servidor ARK - Ventana Independiente")
            console_window.geometry("900x600")
            console_window.resizable(True, True)
            
            # Centrar la ventana
            console_window.update_idletasks()
            x = (console_window.winfo_screenwidth() // 2) - (900 // 2)
            y = (console_window.winfo_screenheight() // 2) - (600 // 2)
            console_window.geometry(f"900x600+{x}+{y}")
            
            # Frame principal
            main_frame = ctk.CTkFrame(console_window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Título
            title_label = ctk.CTkLabel(
                main_frame, 
                text="🎮 Consola del Servidor ARK", 
                font=("Arial", 18, "bold")
            )
            title_label.pack(pady=(0, 10))
            
            # Frame de controles
            control_frame = ctk.CTkFrame(main_frame)
            control_frame.pack(fill="x", pady=(0, 10))
            
            # Botones de control
            ctk.CTkButton(
                control_frame,
                text="🧹 Limpiar",
                command=lambda: self.clear_console_window(console_text),
                width=100
            ).pack(side="left", padx=5, pady=5)
            
            ctk.CTkButton(
                control_frame,
                text="📁 Exportar",
                command=lambda: self.export_console_window(console_text),
                width=100
            ).pack(side="left", padx=5, pady=5)
            
            # Checkbox auto-scroll
            auto_scroll_var = ctk.BooleanVar(value=True)
            auto_scroll_check = ctk.CTkCheckBox(
                control_frame,
                text="📜 Auto-scroll",
                variable=auto_scroll_var
            )
            auto_scroll_check.pack(side="left", padx=10, pady=5)
            
            # Área de texto de la consola
            console_text = ctk.CTkTextbox(
                main_frame,
                font=("Consolas", 11),
                wrap="word"
            )
            console_text.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Copiar contenido actual de la consola
            if self.console_text:
                current_content = self.console_text.get("1.0", "end-1c")
                console_text.insert("1.0", current_content)
                console_text.see("end")
            
            # Configurar auto-scroll
            def auto_scroll():
                if auto_scroll_var.get():
                    console_text.see("end")
                console_window.after(100, auto_scroll)
            
            auto_scroll()
            
            # Función para limpiar la consola de la ventana
            def clear_console_window(text_widget):
                text_widget.delete("1.0", "end")
                text_widget.insert("1.0", "🧹 Consola limpiada\n")
                text_widget.see("end")
            
            # Función para exportar la consola de la ventana
            def export_console_window(text_widget):
                try:
                    from tkinter import filedialog
                    import os
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"console_window_{timestamp}.txt"
                    
                    file_path = filedialog.asksaveasfilename(
                        defaultextension=".txt",
                        filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
                        initialname=filename
                    )
                    
                    if file_path:
                        content = text_widget.get("1.0", "end-1c")
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write("=== CONSOLA DEL SERVIDOR ARK ===\n")
                            f.write(f"Exportado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write("=" * 50 + "\n\n")
                            f.write(content)
                        
                        self.logger.info(f"Consola de ventana exportada a: {file_path}")
                        
                        # Mostrar mensaje de éxito
                        success_dialog = ctk.CTkToplevel(console_window)
                        success_dialog.title("✅ Exportación Exitosa")
                        success_dialog.geometry("300x150")
                        success_dialog.resizable(False, False)
                        
                        ctk.CTkLabel(
                            success_dialog,
                            text="✅ Consola exportada exitosamente",
                            font=("Arial", 14, "bold")
                        ).pack(pady=(20, 10))
                        
                        ctk.CTkButton(
                            success_dialog,
                            text="Cerrar",
                            command=success_dialog.destroy,
                            width=100
                        ).pack(pady=20)
                        
                        success_dialog.transient(console_window)
                        success_dialog.grab_set()
                        
                except Exception as e:
                    self.logger.error(f"Error al exportar consola de ventana: {e}")
            
            # Hacer la ventana modal
            console_window.transient(self)
            console_window.grab_set()
            console_window.focus_set()
            
            self.logger.info("Ventana independiente de consola abierta")
            
        except Exception as e:
            self.logger.error(f"Error al abrir ventana de consola: {e}")
    
    def show_console_stats(self):
        """Mostrar estadísticas de la consola"""
        try:
            # Crear ventana de estadísticas
            stats_window = ctk.CTkToplevel(self)
            stats_window.title("📊 Estadísticas de la Consola")
            stats_window.geometry("400x300")
            stats_window.resizable(False, False)
            
            # Centrar la ventana
            stats_window.update_idletasks()
            x = (stats_window.winfo_screenwidth() // 2) - (400 // 2)
            y = (stats_window.winfo_screenheight() // 2) - (300 // 2)
            stats_window.geometry(f"400x300+{x}+{y}")
            
            # Frame principal
            main_frame = ctk.CTkFrame(stats_window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Título
            title_label = ctk.CTkLabel(
                main_frame, 
                text="📊 Estadísticas de la Consola", 
                font=("Arial", 16, "bold")
            )
            title_label.pack(pady=(0, 20))
            
            # Obtener estadísticas
            stats = self.get_console_statistics()
            
            # Mostrar estadísticas
            stats_text = f"""
📈 ESTADÍSTICAS DE LA CONSOLA:
═══════════════════════════════

📝 Líneas totales: {stats.get('total_lines', 0)}
💾 Tamaño del buffer: {stats.get('buffer_size', 0)}/{self.max_buffer_lines}
🕐 Última actualización: {stats.get('last_update', 'Nunca')}
📊 Líneas por tipo:
  • ℹ️ Info: {stats.get('info_lines', 0)}
  • ✅ Éxito: {stats.get('success_lines', 0)}
  • ⚠️ Advertencia: {stats.get('warning_lines', 0)}
  • ❌ Error: {stats.get('error_lines', 0)}
  • 📝 Normal: {stats.get('normal_lines', 0)}

🔧 ESTADO ACTUAL:
• Consola activa: {'Sí' if self.console_active else 'No'}

🔍 FILTROS ACTIVOS:
• Mensajes internos de la app: {'Sí' if self.show_app_messages_var.get() else 'No'}
• Mensajes de estado del servidor: {'Sí' if self.show_status_messages_var.get() else 'No'}
• Solo mensajes del juego ARK: {'Sí' if self.show_game_only_var.get() else 'No'}
• Auto-scroll: {'Sí' if self.auto_scroll_var.get() else 'No'}
• Conectado al servidor: {'Sí' if hasattr(self, 'is_connected') and self.is_connected else 'No'}
"""
            
            # Área de texto para estadísticas
            stats_text_widget = ctk.CTkTextbox(
                main_frame,
                font=("Consolas", 11),
                wrap="word"
            )
            stats_text_widget.pack(fill="both", expand=True, padx=5, pady=5)
            stats_text_widget.insert("1.0", stats_text)
            stats_text_widget.configure(state="disabled")
            
            # Botón cerrar
            ctk.CTkButton(
                main_frame,
                text="Cerrar",
                command=stats_window.destroy,
                width=100
            ).pack(pady=20)
            
            # Hacer la ventana modal
            stats_window.transient(self)
            stats_window.grab_set()
            stats_window.focus_set()
            
        except Exception as e:
            self.logger.error(f"Error al mostrar estadísticas: {e}")
    
    def force_widget_expansion(self):
        """Forzar la expansión de todos los widgets"""
        try:
            # Forzar actualización del layout principal
            self.update_idletasks()
            
            # Forzar actualización del tabview
            if self.tabview:
                self.tabview.update_idletasks()
                
            # Forzar actualización de cada pestaña
            if hasattr(self, 'tab_system'):
                self.tab_system.update_idletasks()
            if hasattr(self, 'tab_console'):
                self.tab_console.update_idletasks()
            if hasattr(self, 'tab_events'):
                self.tab_events.update_idletasks()
            if hasattr(self, 'tab_app'):
                self.tab_app.update_idletasks()
                
            # Forzar actualización de los textboxes
            if self.console_text:
                self.console_text.update_idletasks()
            if self.system_text:
                self.system_text.update_idletasks()
            if self.events_text:
                self.events_text.update_idletasks()
            if self.app_text:
                self.app_text.update_idletasks()
                
            self.logger.info("Expansión de widgets forzada")
            
        except Exception as e:
            self.logger.error(f"Error al forzar expansión: {e}")
            
    def create_events_tab(self):
        """Crear pestaña de eventos del servidor"""
        # Frame de botones
        button_frame = ctk.CTkFrame(self.tab_events)
        button_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        button_frame.grid_columnconfigure(0, weight=1)
        
        # Botones
        ctk.CTkButton(
            button_frame,
            text="🎮 Eventos Servidor",
            command=self.show_server_events,
            width=130
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        ctk.CTkButton(
            button_frame,
            text="🔄 Actualizar",
            command=self.refresh_events,
            width=100,
            fg_color="orange"
        ).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkButton(
            button_frame,
            text="🗑️ Limpiar",
            command=self.clear_events,
            width=100,
            fg_color="red"
        ).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Área de texto
        self.events_text = ctk.CTkTextbox(
            self.tab_events,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.events_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
    def create_app_tab(self):
        """Crear pestaña de log de la aplicación"""
        # Frame de botones
        button_frame = ctk.CTkFrame(self.tab_app)
        button_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        button_frame.grid_columnconfigure(0, weight=1)
        
        # Botones
        ctk.CTkButton(
            button_frame,
            text="📋 Log App",
            command=self.show_app_log,
            width=100
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        ctk.CTkButton(
            button_frame,
            text="🔄 Actualizar",
            command=self.refresh_app_log,
            width=100,
            fg_color="orange"
        ).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkButton(
            button_frame,
            text="🗑️ Limpiar",
            command=self.clear_app_log,
            width=100,
            fg_color="red"
        ).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Área de texto
        self.app_text = ctk.CTkTextbox(
            self.tab_app,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.app_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
    def load_initial_content(self):
        """Cargar contenido inicial en la pestaña del sistema"""
        content = f"""📋 LOGS DEL SISTEMA ARK - {datetime.now().strftime('%H:%M:%S')}
{'='*60}

✅ Panel de logs inicializado correctamente
✅ Sistema funcionando con consola integrada

🔍 PESTAÑAS DISPONIBLES:
• 📋 Sistema - Logs generales del sistema
• 🎮 Consola - Consola en tiempo real del servidor ARK
• 📊 Eventos - Eventos y actividad del servidor
• 📱 Aplicación - Registro de la aplicación

💡 La consola del servidor se actualiza automáticamente
💡 Puedes exportar y limpiar la consola según necesites

🚀 ¡Sistema listo para usar!
"""
        
        try:
            self.system_text.delete("1.0", "end")
            self.system_text.insert("1.0", content)
        except Exception as e:
            self.logger.error(f"Error al cargar contenido inicial: {e}")
            
        # Inicializar consola
        self.init_console()
        
    def init_console(self):
        """Inicializar la consola del servidor"""
        console_content = f"""🎮 CONSOLA DEL SERVIDOR ARK - {datetime.now().strftime('%H:%M:%S')}
{'='*60}

✅ Consola inicializada correctamente
⏸️ Estado: Inactiva (esperando conexión)

💡 FUNCIONALIDADES:
• 📜 Auto-scroll automático activado
• 🧹 Botón para limpiar la consola
• 📁 Exportar contenido a archivo
• 📊 Información en tiempo real del servidor ARK

🔄 La consola se conectará automáticamente cuando:
• El servidor esté ejecutándose
• La configuración RCON esté disponible
• Se reciban comandos del servidor

🚀 ¡Consola lista para monitorear el servidor ARK real!
"""
        
        try:
            # Asegurar que el textbox esté habilitado
            self.console_text.configure(state="normal")
            
            # Limpiar contenido existente
            self.console_text.delete("1.0", "end")
            
            # Insertar contenido inicial
            self.console_text.insert("1.0", console_content)
            
            # Deshabilitar edición
            self.console_text.configure(state="disabled")
            
            # Actualizar información
            self.update_console_info()
            
            # Debug: verificar que el contenido se haya insertado
            content_length = len(self.console_text.get("1.0", "end"))
            self.logger.info(f"Consola inicializada con {content_length} caracteres")
            
        except Exception as e:
            self.logger.error(f"Error al inicializar consola: {e}")
            
        # NO iniciar simulación - esperar conexión real
        # self.start_console_simulation()

    def debug_widgets(self):
        """Método de debug para verificar el estado de los widgets"""
        try:
            # Verificar que los widgets existan
            widgets_status = {
                "system_text": self.system_text is not None,
                "console_text": self.console_text is not None,
                "events_text": self.events_text is not None,
                "app_text": self.app_text is not None,
                "tabview": self.tabview is not None
            }
            
            # Verificar contenido de los textboxes
            content_status = {}
            if self.system_text:
                content_status["system"] = len(self.system_text.get("1.0", "end"))
            if self.console_text:
                content_status["console"] = len(self.console_text.get("1.0", "end"))
            if self.events_text:
                content_status["events"] = len(self.events_text.get("1.0", "end"))
            if self.app_text:
                content_status["app"] = len(self.app_text.get("1.0", "end"))
            
            # Log del estado
            self.logger.info(f"Estado de widgets: {widgets_status}")
            self.logger.info(f"Contenido de textboxes: {content_status}")
            
            # Verificar geometría
            if self.tabview:
                self.logger.info(f"Tabview geometry: {self.tabview.winfo_geometry()}")
                self.logger.info(f"Tabview width: {self.tabview.winfo_width()}, height: {self.tabview.winfo_height()}")
            if self.console_text:
                self.logger.info(f"Console text geometry: {self.console_text.winfo_geometry()}")
                self.logger.info(f"Console text width: {self.console_text.winfo_width()}, height: {self.console_text.winfo_height()}")
                self.logger.info(f"Console text sticky: {self.console_text.grid_info()}")
            
            # Verificar configuración del grid
            if hasattr(self, 'tab_console'):
                self.logger.info(f"Tab console grid config: column 0 weight: {self.tab_console.grid_columnconfigure(0)}")
                self.logger.info(f"Tab console grid config: row 1 weight: {self.tab_console.grid_rowconfigure(1)}")
                
        except Exception as e:
            self.logger.error(f"Error en debug_widgets: {e}")
            import traceback
            traceback.print_exc()
        
    def force_console_update(self):
        """Forzar actualización de la consola"""
        try:
            if self.console_text:
                # Habilitar edición
                self.console_text.configure(state="normal")
                
                # Agregar línea de prueba
                test_line = f"[{datetime.now().strftime('%H:%M:%S')}] 🔧 Actualización forzada de consola\n"
                self.console_text.insert("end", test_line)
                
                # Auto-scroll
                self.console_text.see("end")
                
                # Deshabilitar edición
                self.console_text.configure(state="disabled")
                
                # Actualizar información
                self.update_console_info()
                
                self.logger.info("Actualización forzada de consola completada")
            else:
                self.logger.error("console_text no está disponible para actualización forzada")
                
        except Exception as e:
            self.logger.error(f"Error en actualización forzada: {e}")
    
    def start_console_simulation(self):
        """Iniciar simulación de consola para demostración"""
        def simulate_console():
            try:
                time.sleep(3)  # Esperar 3 segundos
                self.add_console_line("🔄 Iniciando simulación de consola...", "info")
                time.sleep(2)
                self.add_console_line("✅ Servidor ARK detectado", "success")
                time.sleep(2)
                self.add_console_line("👥 0 jugadores conectados", "info")
                time.sleep(2)
                self.add_console_line("🌍 Mapa: TheIsland", "info")
                time.sleep(2)
                self.add_console_line("⏰ Tiempo: Día 45, 12:30", "info")
                time.sleep(2)
                self.add_console_line("💾 Guardando mundo...", "warning")
                time.sleep(1)
                self.add_console_line("✅ Mundo guardado correctamente", "success")
                
                # Agregar línea final de simulación
                self.add_console_line("🎯 Simulación de consola completada", "success")
                
            except Exception as e:
                self.logger.error(f"Error en simulación de consola: {e}")
            
        # Ejecutar en hilo separado
        threading.Thread(target=simulate_console, daemon=True).start()
        
    def add_console_line(self, line, line_type="info"):
        """Agregar una línea a la consola del servidor ARK"""
        try:
            # Filtrar mensajes internos de la aplicación
            if self._should_skip_line(line):
                return
                
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_line = f"[{timestamp}] {line}\n"
            
            # Agregar al buffer
            self.console_buffer.append((formatted_line, line_type))
            
            # Mantener tamaño del buffer
            if len(self.console_buffer) > self.max_buffer_lines:
                self.console_buffer.pop(0)
            
            # Detectar estado del servidor automáticamente
            self.detect_server_state(line)
            
            # Actualizar UI usando el método correcto de customtkinter
            if hasattr(self, 'after'):
                self.after(0, lambda: self._update_console_ui(formatted_line, line_type))
            else:
                # Fallback: actualizar directamente
                self._update_console_ui(formatted_line, line_type)
            
        except Exception as e:
            self.logger.error(f"Error al agregar línea a consola: {e}")
            
    def _should_skip_line(self, line):
        """Determinar si una línea debe ser omitida de la consola del servidor ARK"""
        line_lower = line.lower()
        
        # Patrones de mensajes internos de la aplicación (siempre omitir)
        app_patterns = [
            "estado del servidor actualizado",
            "ark server manager",
            "info -",
            "warning -", 
            "error -",
            "logger",
            "configurando",
            "iniciando",
            "detenido",
            "listo para conectar",
            "en funcionamiento",
            "error crítico",
            "advertencia",
            "servidor detenido exitosamente",
            "servidor detenido",
            "buscando procesos",
            "verificando procesos",
            "enviando señal",
            "esperando que el servidor termine",
            "servidor detenido correctamente",
            "verificando que el proceso se cerró",
            "no se encontraron procesos",
            "servidor completamente detenido",
            "configuración guardada correctamente",
            "debug:",
            "conectando automáticamente",
            "conectando a",
            "rcon falló",
            "intentando captura directa",
            "no se encontró proceso",
            "no se pudo conectar",
            "iniciando servidor",
            "configuración guardada",
            "archivo actualizado",
            "mapa seleccionado",
            "argumentos finales generados",
            "comando final del servidor",
            "parámetros recibidos",
            "usando argumentos personalizados"
        ]
        
        # Patrones de mensajes de estado del servidor (siempre omitir)
        status_patterns = [
            "estado del servidor actualizado",
            "configurando",
            "iniciando",
            "detenido",
            "listo para conectar",
            "en funcionamiento",
            "error crítico",
            "advertencia"
        ]
        
        # Patrones de mensajes del juego ARK (siempre mostrar si no son internos)
        game_patterns = [
            "player connected", "jugador conectado", "player joined", "jugador se unió",
            "player disconnected", "jugador desconectado", "world saved", "mundo guardado",
            "player spawned", "jugador apareció", "player died", "jugador murió",
            "tribe log", "log de tribu", "chat", "mensaje", "server has completed startup",
            "startup complete", "ready for connections", "listening", "escuchando",
            "advertising for join", "server is ready", "world loaded", "mundo cargado",
            "map loaded", "mapa cargado", "mod loaded", "plugin loaded", "world save",
            "backup", "shutting down", "stopping", "server stopped", "exit", "shutdown",
            "fatal error", "failed to start", "crash", "exception", "critical error",
            "startup failed", "launch failed"
        ]
        
        # Aplicar filtros según configuración
        if not getattr(self, 'show_app_messages_var', None) or not self.show_app_messages_var.get():
            if any(pattern in line_lower for pattern in app_patterns):
                return True
                
        if not getattr(self, 'show_status_messages_var', None) or not self.show_status_messages_var.get():
            if any(pattern in line_lower for pattern in status_patterns):
                return True
                
        if getattr(self, 'show_game_only_var', None) and self.show_game_only_var.get():
            # Si solo mostrar mensajes del juego, verificar que sea un mensaje del juego
            if not any(pattern in line_lower for pattern in game_patterns):
                return True
        
        return False
    
    def toggle_app_messages_filter(self):
        """Alternar filtro de mensajes internos de la aplicación"""
        try:
            if self.show_app_messages_var.get():
                self.logger.info("Filtro de mensajes internos de la app: ACTIVADO")
            else:
                self.logger.info("Filtro de mensajes internos de la app: DESACTIVADO")
            # Aplicar filtros al buffer existente
            self.apply_filters_to_buffer()
        except Exception as e:
            self.logger.error(f"Error alternando filtro de mensajes de app: {e}")
            
    def toggle_status_messages_filter(self):
        """Alternar filtro de mensajes de estado del servidor"""
        try:
            if self.show_status_messages_var.get():
                self.logger.info("Filtro de mensajes de estado: ACTIVADO")
            else:
                self.logger.info("Filtro de mensajes de estado: DESACTIVADO")
            # Aplicar filtros al buffer existente
            self.apply_filters_to_buffer()
        except Exception as e:
            self.logger.error(f"Error alternando filtro de mensajes de estado: {e}")
            
    def toggle_game_only_filter(self):
        """Alternar filtro de solo mensajes del juego"""
        try:
            if self.show_game_only_var.get():
                self.logger.info("Filtro de solo mensajes del juego: ACTIVADO")
            else:
                self.logger.info("Filtro de solo mensajes del juego: DESACTIVADO")
            # Aplicar filtros al buffer existente
            self.apply_filters_to_buffer()
        except Exception as e:
            self.logger.error(f"Error alternando filtro de mensajes de solo juego: {e}")
            
    def clear_filters(self):
        """Limpiar todos los filtros y mostrar todos los mensajes"""
        try:
            self.show_app_messages_var.set(True)
            self.show_status_messages_var.set(True)
            self.show_game_only_var.set(False)
            self.logger.info("Todos los filtros han sido limpiados")
            # Aplicar filtros al buffer existente
            self.apply_filters_to_buffer()
        except Exception as e:
            self.logger.error(f"Error limpiando filtros: {e}")
            
    def apply_filters_to_buffer(self):
        """Aplicar filtros actuales al buffer existente y actualizar la consola"""
        try:
            # Limpiar consola actual
            self.console_text.configure(state="normal")
            self.console_text.delete("1.0", "end")
            self.console_text.configure(state="disabled")
            
            # Filtrar buffer existente
            filtered_buffer = []
            for formatted_line, line_type in self.console_buffer:
                # Extraer la línea original del formato [timestamp] line
                if formatted_line.startswith('[') and '] ' in formatted_line:
                    original_line = formatted_line.split('] ', 1)[1].rstrip('\n')
                else:
                    original_line = formatted_line.rstrip('\n')
                
                # Aplicar filtros
                if not self._should_skip_line(original_line):
                    filtered_buffer.append((formatted_line, line_type))
            
            # Actualizar buffer filtrado
            self.console_buffer = filtered_buffer
            
            # Redibujar consola con contenido filtrado
            for formatted_line, line_type in self.console_buffer:
                self._update_console_ui(formatted_line, line_type)
                
            self.logger.info(f"Filtros aplicados. Buffer: {len(filtered_buffer)}/{len(self.console_buffer)} líneas")
            
        except Exception as e:
            self.logger.error(f"Error aplicando filtros al buffer: {e}")
             
    def _update_console_ui(self, formatted_line, line_type):
        """Actualizar la UI de la consola"""
        try:
            # Verificar que el widget exista y esté configurado
            if not self.console_text:
                self.logger.error("console_text no está disponible")
                return
                
            # Habilitar edición
            self.console_text.configure(state="normal")
            
            # Insertar línea
            self.console_text.insert("end", formatted_line)
            
            # Aplicar color según tipo
            if line_type == "error":
                self.console_text.tag_add("error", f"end-{len(formatted_line)+1}c", "end-1c")
                self.console_text.tag_config("error", foreground="red")
            elif line_type == "warning":
                self.console_text.tag_add("warning", f"end-{len(formatted_line)+1}c", "end-1c")
                self.console_text.tag_config("warning", foreground="orange")
            elif line_type == "success":
                self.console_text.tag_add("success", f"end-{len(formatted_line)+1}c", "end-1c")
                self.console_text.tag_config("success", foreground="green")
            
            # Auto-scroll si está activado
            if self.auto_scroll:
                self.console_text.see("end")
            
            # Deshabilitar edición
            self.console_text.configure(state="disabled")
            
            # Actualizar información
            self.update_console_info()
            
            # Debug: verificar que la línea se haya insertado
            current_content = self.console_text.get("1.0", "end")
            if formatted_line in current_content:
                self.logger.debug(f"Línea insertada correctamente: {formatted_line.strip()}")
            else:
                self.logger.warning(f"Línea no se insertó correctamente: {formatted_line.strip()}")
            
        except Exception as e:
            self.logger.error(f"Error al actualizar UI de consola: {e}")
            # Intentar habilitar el textbox en caso de error
            try:
                self.console_text.configure(state="normal")
            except:
                pass
            
    def clear_console(self):
        """Limpiar la consola"""
        try:
            self.console_text.configure(state="normal")
            self.console_text.delete("1.0", "end")
            self.console_text.configure(state="disabled")
            
            # Limpiar buffer
            self.console_buffer.clear()
            
            # Reinicializar
            self.init_console()
            
        except Exception as e:
            self.logger.error(f"Error al limpiar consola: {e}")
            
    def export_console(self):
        """Exportar contenido de la consola"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"consola_servidor_{timestamp}.txt"
            
            # Crear directorio exports si no existe
            if not os.path.exists("exports"):
                os.makedirs("exports")
                
            filepath = os.path.join("exports", filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"CONSOLA DEL SERVIDOR ARK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")
                f.write(self.console_text.get("1.0", "end"))
                
            # Mostrar mensaje de éxito
            self.show_export_success(filepath)
            
        except Exception as e:
            self.logger.error(f"Error al exportar consola: {e}")
            
    def show_export_success(self, filepath):
        """Mostrar mensaje de exportación exitosa"""
        try:
            # Crear ventana de éxito
            success_window = ctk.CTkToplevel(self)
            success_window.title("✅ Exportación Exitosa")
            success_window.geometry("400x200")
            success_window.transient(self)
            success_window.grab_set()
            
            # Centrar en pantalla
            success_window.geometry("+400+200")
            
            # Contenido
            ctk.CTkLabel(
                success_window, 
                text="✅ Consola exportada correctamente", 
                font=("Arial", 16, "bold")
            ).pack(pady=20)
            
            ctk.CTkLabel(
                success_window, 
                text=f"📁 Archivo: {os.path.basename(filepath)}", 
                font=("Arial", 12)
            ).pack(pady=10)
            
            ctk.CTkLabel(
                success_window, 
                text=f"📍 Ubicación: {filepath}", 
                font=("Arial", 10)
            ).pack(pady=5)
            
            # Botón cerrar
            ctk.CTkButton(
                success_window,
                text="Cerrar",
                command=success_window.destroy,
                width=100
            ).pack(pady=20)
            
        except Exception as e:
            self.logger.error(f"Error al mostrar ventana de éxito: {e}")
            
    def toggle_auto_scroll(self):
        """Alternar auto-scroll"""
        self.auto_scroll = self.auto_scroll_var.get()
        
    def update_console_info(self):
        """Actualizar información de la consola"""
        try:
            # Actualizar contador de líneas
            if self.console_text:
                content = self.console_text.get("1.0", "end")
                lines = len(content.split('\n')) - 1
                self.console_lines_label.configure(text=f"Líneas: {lines}")
            
            # Actualizar tamaño del buffer
            buffer_size = len(self.console_buffer)
            self.buffer_size_label.configure(text=f"Buffer: {buffer_size}/{self.max_buffer_lines}")
            
            # Actualizar tiempo de ejecución
            uptime = datetime.now() - self.start_time
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.uptime_label.configure(text=f"Tiempo: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Actualizar última actualización
            current_time = datetime.now().strftime("%H:%M:%S")
            self.last_update_label.configure(text=f"Última actualización: {current_time}")
            
            # Actualizar información de filtros en el estado de conexión
            if hasattr(self, 'connection_status_label'):
                filter_info = []
                if not self.show_app_messages_var.get():
                    filter_info.append("App")
                if not self.show_status_messages_var.get():
                    filter_info.append("Estado")
                if self.show_game_only_var.get():
                    filter_info.append("Solo ARK")
                
                if filter_info:
                    filter_text = f"Filtros: {', '.join(filter_info)}"
                    self.connection_status_label.configure(text=filter_text)
                else:
                    self.connection_status_label.configure(text="Sin filtros")
            
        except Exception as e:
            self.logger.error(f"Error actualizando información de consola: {e}")
            
    def set_console_active(self, active):
        """Establecer estado activo de la consola"""
        self.console_active = active
        
        if active:
            self.console_status.configure(text="✅ Consola activa")
        else:
            self.console_status.configure(text="⏸️ Consola inactiva")
            
        # Actualizar botones de conexión
        self.update_connection_buttons()
        
    def get_console_content(self):
        """Obtener contenido de la consola"""
        try:
            return self.console_text.get("1.0", "end")
        except:
            return ""
            
    def add_server_output(self, output, output_type="info"):
        """Agregar salida del servidor a la consola"""
        self.add_console_line(output, output_type)
        
    def add_server_event(self, event_type, message):
        """Agregar evento del servidor a la consola"""
        self.add_console_line(f"[{event_type.upper()}] {message}", "info")
    
    def detect_server_state(self, line):
        """Detectar automáticamente el estado del servidor basándose en los mensajes de la consola"""
        try:
            line_lower = line.lower()
            
            # Solo procesar líneas que son del servidor ARK, no logs internos de la aplicación
            if any(skip_pattern in line_lower for skip_pattern in [
                "estado del servidor actualizado", "ark server manager", "info -", "warning -", "error -",
                "logger", "configurando", "iniciando", "detenido", "listo para conectar"
            ]):
                return
            
            # Estados de inicio del servidor ARK (solo patrones específicos del juego)
            if any(keyword in line_lower for keyword in [
                "server has completed startup", "startup complete", "ready for connections",
                "listening", "escuchando", "advertising for join", "server is ready",
                "world loaded", "mundo cargado", "map loaded", "mapa cargado"
            ]):
                self.update_server_status("✅ Listo para conectar", "green")
                
            # Servidor en funcionamiento (solo eventos reales del juego)
            elif any(keyword in line_lower for keyword in [
                "player connected", "jugador conectado", "player joined", "jugador se unió",
                "player disconnected", "jugador desconectado", "world saved", "mundo guardado",
                "player spawned", "jugador apareció", "player died", "jugador murió",
                "tribe log", "log de tribu", "chat", "mensaje"
            ]):
                self.update_server_status("🟢 En funcionamiento", "green")
                
            # Servidor detenido o cerrando (solo mensajes reales del servidor)
            elif any(keyword in line_lower for keyword in [
                "shutting down", "cerrando", "stopping", "deteniendo", "server stopped",
                "exit", "salida", "shutdown", "apagado", "closing", "terminating"
            ]):
                self.update_server_status("🔴 Detenido", "red")
                
            # Errores críticos del servidor ARK
            elif any(keyword in line_lower for keyword in [
                "fatal error", "failed to start", "crash", "exception", "critical error",
                "startup failed", "launch failed"
            ]):
                self.update_server_status("💥 Error crítico", "red")
                
            # Estados específicos de ARK (solo cuando son relevantes)
            elif any(keyword in line_lower for keyword in [
                "mod loaded", "plugin loaded", "world save", "backup"
            ]):
                # Solo actualizar si no estamos ya en estado de configuración
                self.update_server_status("🔧 Configurando", "blue")
                
        except Exception as e:
            self.logger.error(f"Error detectando estado del servidor: {e}")
    
    def update_server_status(self, status_text, color):
        """Actualizar el estado del servidor en la ventana principal"""
        try:
            # Mapear colores a colores de customtkinter
            color_map = {
                "green": "green",
                "red": "red", 
                "orange": "orange",
                "blue": "blue",
                "purple": "purple"
            }
            
            # Actualizar el estado en la ventana principal si está disponible
            if self.main_window and hasattr(self.main_window, 'update_server_status'):
                # Mapear estados a colores apropiados para la ventana principal
                main_window_color = color_map.get(color, "red")
                
                # Actualizar el estado en la ventana principal
                self.main_window.update_server_status(status_text, main_window_color)
                
                # Log del cambio de estado
                self.logger.debug(f"Estado del servidor actualizado en ventana principal: {status_text}")
                
        except Exception as e:
            self.logger.error(f"Error actualizando estado del servidor: {e}")
    
    # Métodos de integración con RCON
    def connect_to_server_console(self, server_ip, rcon_port, rcon_password):
        """Conectar la consola al servidor ARK via RCON REAL o captura directa"""
        try:
            # Solo log, no mostrar en consola
            self.logger.info(f"Conectando a {server_ip}:{rcon_port}...")
            
            # Actualizar variables
            self.rcon_ip = server_ip
            self.rcon_port = rcon_port
            self.rcon_password = rcon_password
            
            # Intentar conexión RCON primero
            test_result = self.test_rcon_connection()
            
            if test_result:
                self.is_connected = True
                self.set_console_active(True)
                
                # Establecer estado inicial en la ventana principal
                self.update_server_status("🔍 Conectando...", "blue")
                
                # Iniciar monitoreo en tiempo real
                self.start_real_time_monitoring()
                
                # Obtener información inicial del servidor
                self.get_initial_server_info()
            else:
                # Si RCON falla, intentar captura directa del servidor
                self.logger.warning("RCON falló, intentando captura directa del servidor...")
                if self.connect_to_server_direct():
                    self.is_connected = True
                    self.set_console_active(True)
                    
                    # Establecer estado inicial en la ventana principal
                    self.update_server_status("🔍 Conectando...", "blue")
                    
                    # Iniciar monitoreo directo
                    self.start_direct_monitoring()
                else:
                    self.logger.error("No se pudo conectar ni por RCON ni por captura directa")
                    self.set_console_active(False)
                
        except Exception as e:
            # Solo log, no mostrar en consola
            self.logger.error(f"Error conectando: {e}")
            self.set_console_active(False)
    
    def test_rcon_connection(self):
        """Probar conexión RCON real al servidor"""
        try:
            # Buscar ejecutable RCON
            rcon_exe = self.find_rcon_executable()
            if not rcon_exe:
                # Solo log, no mostrar en consola
                self.logger.error("No se encontró ejecutable RCON")
                return False
            
            # Comando de prueba simple
            cmd = [
                str(rcon_exe),
                "-a", f"{self.rcon_ip}:{self.rcon_port}",
                "-p", self.rcon_password,
                "GetServerInfo"
            ]
            
            # Ejecutar comando de prueba
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(rcon_exe.parent),
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Solo log, no mostrar en consola
                self.logger.info("Conexión RCON verificada exitosamente")
                return True
            else:
                error_msg = result.stderr.strip() if result.stderr else "Sin respuesta del servidor"
                # Solo log, no mostrar en consola
                self.logger.error(f"Error RCON: {error_msg}")
                return False
                
        except subprocess.TimeoutExpired:
            # Solo log, no mostrar en consola
            self.logger.error("Timeout en conexión RCON")
            return False
        except Exception as e:
            # Solo log, no mostrar en consola
            self.logger.error(f"Error de conexión: {e}")
            return False
    
    def find_rcon_executable(self):
        """Buscar el ejecutable RCON en el sistema"""
        search_paths = [
            Path("rcon"),
            Path(__file__).parent.parent.parent / "rcon",
            Path.cwd() / "rcon",
            Path(__file__).parent.parent.parent,
            Path.cwd(),
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                for file in search_path.glob("*.exe"):
                    if "rcon" in file.name.lower():
                        return file
        return None

    def connect_to_server_direct(self):
        """Conectar directamente al servidor ARK capturando su salida"""
        try:
            if not hasattr(self, 'main_window') or not self.main_window:
                self.logger.warning("No hay ventana principal disponible para captura directa")
                return False
            
            # Obtener información del servidor seleccionado
            server_name = getattr(self.main_window, 'selected_server', None)
            if not server_name:
                self.logger.warning("No hay servidor seleccionado")
                return False
            
            # Buscar proceso del servidor ARK
            ark_process = self.find_ark_server_process(server_name)
            if ark_process:
                self.logger.info(f"Proceso del servidor ARK encontrado: PID {ark_process.pid}")
                self.ark_process = ark_process
                
                # Buscar y configurar ruta de logs del servidor
                if self.find_server_logs_path(server_name):
                    self.logger.info(f"Ruta de logs del servidor configurada: {self.server_logs_path}")
                    return True
                else:
                    self.logger.warning("No se pudo encontrar la ruta de logs del servidor")
                    return False
            else:
                self.logger.warning("No se encontró proceso del servidor ARK ejecutándose")
                return False
                
        except Exception as e:
            self.logger.error(f"Error en conexión directa: {e}")
            return False

    def find_server_logs_path(self, server_name):
        """Buscar la ruta de logs del servidor ARK"""
        try:
            # Obtener la ruta del ejecutable del servidor
            server_key = f"executable_path_{server_name}"
            executable_path = self.config_manager.get("server", server_key)
            
            if not executable_path:
                self.logger.warning(f"No se encontró ruta del ejecutable para {server_name}")
                return False
            
            # Construir la ruta de logs típica de ARK
            # De: D:/ASA\Prueba\ShooterGame\Binaries\Win64\ArkAscendedServer.exe
            # A:  D:/ASA\Prueba\ShooterGame\Saved\Logs
            executable_path = Path(executable_path)
            logs_path = executable_path.parent.parent.parent / "Saved" / "Logs"
            
            if logs_path.exists():
                self.server_logs_path = str(logs_path)
                self.logger.info(f"Ruta de logs encontrada: {self.server_logs_path}")
                return True
            else:
                # Intentar con ruta alternativa
                logs_path = executable_path.parent.parent.parent.parent / "Saved" / "Logs"
                if logs_path.exists():
                    self.server_logs_path = str(logs_path)
                    self.logger.info(f"Ruta de logs encontrada (alternativa): {self.server_logs_path}")
                    return True
                else:
                    self.logger.warning(f"Ruta de logs no encontrada: {logs_path}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error buscando ruta de logs: {e}")
            return False

    def find_ark_server_process(self, server_name):
        """Buscar proceso del servidor ARK por nombre"""
        try:
            import psutil
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'ArkAscendedServer' in proc.info['name']:
                        # Verificar si es el servidor correcto por argumentos de línea de comandos
                        cmdline = proc.info['cmdline']
                        if cmdline and any(server_name.lower() in arg.lower() for arg in cmdline):
                            self.logger.info(f"Servidor ARK encontrado: {server_name} (PID: {proc.info['pid']})")
                            return proc
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return None
            
        except ImportError:
            self.logger.warning("psutil no está disponible, no se puede buscar proceso del servidor")
            return None
        except Exception as e:
            self.logger.error(f"Error buscando proceso del servidor: {e}")
            return None

    def start_direct_monitoring(self):
        """Iniciar monitoreo directo del servidor ARK leyendo logs reales"""
        if not hasattr(self, 'ark_process') or not self.ark_process:
            return
            
        if not hasattr(self, 'server_logs_path') or not self.server_logs_path:
            self.add_console_line("❌ No se pudo configurar la ruta de logs del servidor", "error")
            return
            
        def monitor_direct():
            try:
                self.add_console_line("🔄 Iniciando monitoreo directo del servidor...", "info")
                self.add_console_line(f"📁 Monitoreando logs en: {self.server_logs_path}", "info")
                
                # Establecer estado de monitoreo
                self.update_server_status("🔍 Monitoreando...", "blue")
                
                # No mostrar información del sistema en la consola
                pass
                
                # Inicializar seguimiento de archivos de log
                self.log_files = {}
                self.log_file_positions = {}
                
                # Monitoreo continuo
                while self.console_active and self.is_connected:
                    try:
                        time.sleep(2)  # Actualizar cada 2 segundos para logs en tiempo real
                        
                        if self.console_active and self.is_connected:
                            # Verificar si el proceso sigue vivo
                            if not self.ark_process.is_running():
                                self.add_console_line("⚠️ El servidor ARK se ha detenido", "warning")
                                self.update_server_status("🔴 Detenido", "red")
                                break
                            
                            # Leer logs del servidor
                            self.read_server_logs()
                            
                            # No mostrar información del sistema en la consola
                            pass
                                
                    except Exception as e:
                        if self.console_active and self.is_connected:
                            self.add_console_line(f"❌ Error en monitoreo directo: {e}", "error")
                        break
                        
            except Exception as e:
                self.logger.error(f"Error en monitoreo directo: {e}")
        
        # Ejecutar monitoreo en hilo separado
        self.direct_monitoring_thread = threading.Thread(target=monitor_direct, daemon=True)
        self.direct_monitoring_thread.start()

    def read_server_logs(self):
        """Leer logs del servidor ARK en tiempo real"""
        try:
            if not hasattr(self, 'server_logs_path') or not self.server_logs_path:
                self.logger.debug("read_server_logs: No hay server_logs_path configurado")
                return
                
            logs_dir = Path(self.server_logs_path)
            if not logs_dir.exists():
                self.logger.debug(f"read_server_logs: Directorio de logs no existe: {self.server_logs_path}")
                return
                
            self.logger.debug(f"read_server_logs: Buscando archivos de log en: {self.server_logs_path}")
            
            # Buscar archivos de log del servidor (incluyendo archivos sin extensión)
            log_files = []
            for file_path in logs_dir.iterdir():
                if file_path.is_file():
                    # Incluir archivos .log y archivos que contengan "log" en el nombre
                    if (file_path.suffix.lower() == '.log' or 
                        'log' in file_path.name.lower() or
                        'shootergame' in file_path.name.lower()):
                        log_files.append(file_path)
                        self.logger.debug(f"read_server_logs: Archivo de log encontrado: {file_path.name}")
            
            self.logger.debug(f"read_server_logs: Total de archivos de log encontrados: {len(log_files)}")
            
            for log_file in log_files:
                try:
                    # Inicializar seguimiento del archivo si es nuevo
                    if log_file.name not in self.log_files:
                        self.log_files[log_file.name] = log_file
                        self.log_file_positions[log_file.name] = 0
                        self.add_console_line(f"📄 Monitoreando archivo de log: {log_file.name}", "info")
                        self.logger.debug(f"read_server_logs: Iniciando monitoreo de: {log_file.name}")
                    
                    # Leer nuevas líneas del archivo
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        # Ir a la posición anterior
                        f.seek(self.log_file_positions[log_file.name])
                        
                        # Leer nuevas líneas
                        new_lines = f.readlines()
                        
                        if new_lines:
                            # Actualizar posición
                            self.log_file_positions[log_file.name] = f.tell()
                            
                            self.logger.debug(f"read_server_logs: {len(new_lines)} nuevas líneas leídas de {log_file.name}")
                            
                            # Procesar y mostrar nuevas líneas
                            for line in new_lines:
                                line = line.strip()
                                if line and len(line) > 5:  # Filtrar líneas vacías o muy cortas
                                    # Determinar tipo de línea basado en contenido
                                    line_type = self.classify_log_line(line)
                                    
                                    # Mostrar en consola
                                    self.add_console_line(f"�� {line}", line_type)
                                    
                except Exception as e:
                    self.logger.warning(f"Error leyendo archivo {log_file.name}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error leyendo logs del servidor: {e}")

    def classify_log_line(self, line):
        """Clasificar el tipo de línea de log basado en su contenido"""
        line_lower = line.lower()
        
        # Errores
        if any(keyword in line_lower for keyword in ['error', 'exception', 'failed', 'crash', 'fatal']):
            return "error"
        
        # Advertencias
        if any(keyword in line_lower for keyword in ['warning', 'warn', 'caution']):
            return "warning"
        
        # Conexiones de jugadores
        if any(keyword in line_lower for keyword in ['player', 'connected', 'disconnected', 'joined', 'left']):
            return "success"
        
        # Información del servidor
        if any(keyword in line_lower for keyword in ['server', 'world', 'map', 'level', 'time']):
            return "info"
        
        # Por defecto
        return "info"
    
    def get_initial_server_info(self):
        """Obtener información inicial del servidor"""
        try:
            if not self.is_connected:
                return
                
            # Obtener información básica del servidor
            commands = [
                ("GetServerInfo", "Información del servidor"),
                ("ListPlayers", "Jugadores conectados"),
                ("GetWorldTime", "Tiempo del mundo")
            ]
            
            for command, description in commands:
                self.add_console_line(f"📡 Obteniendo {description}...", "info")
                result = self.execute_rcon_command(command)
                if result:
                    self.add_console_line(f"📊 {description}: {result}", "success")
                else:
                    self.add_console_line(f"⚠️ No se pudo obtener {description}", "warning")
                    
        except Exception as e:
            self.add_console_line(f"❌ Error obteniendo información inicial: {e}", "error")

    def disconnect_from_server(self):
        """Desconectar de la consola del servidor"""
        try:
            self.add_console_line("🔄 Desconectando del servidor...", "info")
            self.set_console_active(False)
            self.add_console_line("⏸️ Desconectado del servidor", "info")
            
            # Resetear estado del servidor
            self.update_server_status("⏸️ Inactivo", "orange")
            
        except Exception as e:
            self.add_console_line(f"❌ Error desconectando: {e}", "error")
    
    def start_real_time_monitoring(self):
        """Iniciar monitoreo en tiempo real del servidor via RCON"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
        
        def monitor_server():
            try:
                # Primera ejecución inmediata
                if self.console_active and self.is_connected:
                    # Obtener información inicial del servidor
                    try:
                        # Obtener jugadores conectados
                        players_result = self.execute_rcon_command("ListPlayers")
                        if players_result and players_result != "Comando ejecutado sin respuesta":
                            self.add_console_line(f"👥 {players_result}", "info")
                        
                        # Obtener tiempo del mundo
                        time_result = self.execute_rcon_command("GetWorldTime")
                        if time_result and time_result != "Comando ejecutado sin respuesta":
                            self.add_console_line(f"⏰ {time_result}", "info")
                        
                        # Obtener estadísticas del servidor
                        stats_result = self.execute_rcon_command("GetServerInfo")
                        if stats_result and stats_result != "Comando ejecutado sin respuesta":
                            # Parsear información básica
                            if "Players:" in stats_result:
                                self.add_console_line(f"📊 {stats_result}", "info")
                    except Exception as e:
                        # Solo log, no mostrar en consola
                        self.logger.error(f"Error en monitoreo inicial: {e}")
            except Exception as e:
                # Solo log, no mostrar en consola
                self.logger.error(f"Error en monitoreo inicial: {e}")
            
            # Monitoreo continuo cada 30 segundos
            while self.console_active and self.is_connected:
                try:
                    time.sleep(30)
                    
                    if self.console_active and self.is_connected:
                        # Obtener jugadores conectados
                        players_result = self.execute_rcon_command("ListPlayers")
                        if players_result and players_result != "Comando ejecutado sin respuesta":
                            self.add_console_line(f"👥 {players_result}", "info")
                        
                        # Obtener tiempo del mundo
                        time_result = self.execute_rcon_command("GetWorldTime")
                        if time_result and time_result != "Comando ejecutado sin respuesta":
                            self.add_console_line(f"⏰ {time_result}", "info")
                        
                        # Obtener estadísticas del servidor
                        stats_result = self.execute_rcon_command("GetServerInfo")
                        if stats_result and stats_result != "Comando ejecutado sin respuesta":
                            # Parsear información básica
                            if "Players:" in stats_result:
                                self.add_console_line(f"📊 {stats_result}", "info")
                        
                except Exception as e:
                    # Solo log, no mostrar en consola
                    self.logger.error(f"Error en monitoreo: {e}")
                    break
        
        # Ejecutar monitoreo en hilo separado
        self.monitoring_thread = threading.Thread(target=monitor_server, daemon=True)
        self.monitoring_thread.start()
    
    def execute_rcon_command(self, command):
        """Ejecutar comando RCON REAL al servidor"""
        try:
            if not self.is_connected:
                # Solo log, no mostrar en consola
                self.logger.error("No hay conexión activa al servidor")
                return None
            
            rcon_exe = self.find_rcon_executable()
            if not rcon_exe:
                return None
            
            # Ejecutar comando
            cmd = [
                str(rcon_exe),
                "-a", f"{self.rcon_ip}:{self.rcon_port}",
                "-p", self.rcon_password,
                command
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(rcon_exe.parent),
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                if response:
                    return response
                else:
                    return "Comando ejecutado sin respuesta"
            else:
                error_msg = result.stderr.strip() if result.stderr else "Error desconocido"
                # Solo log, no mostrar en consola
                self.logger.error(f"Error RCON '{command}': {error_msg}")
                return None
                
        except subprocess.TimeoutExpired:
            # Solo log, no mostrar en consola
            self.logger.error(f"Timeout en comando '{command}'")
            return None
        except Exception as e:
            # Solo log, no mostrar en consola
            self.logger.error(f"Error ejecutando '{command}': {e}")
            return None
    
    def get_server_status(self):
        """Obtener estado actual del servidor REAL"""
        try:
            if not self.is_connected:
                return "Desconectado"
            
            # Probar conexión con comando simple
            result = self.execute_rcon_command("GetServerInfo")
            if result:
                return "Conectado y funcionando"
            else:
                return "Conectado pero sin respuesta"
                
        except Exception as e:
            return f"Error: {e}"
    
    def export_console_with_timestamp(self, include_timestamp=True):
        """Exportar consola con opción de timestamp"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"consola_servidor_{timestamp}.txt"
            
            # Crear directorio exports si no existe
            if not os.path.exists("exports"):
                os.makedirs("exports")
                
            filepath = os.path.join("exports", filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                if include_timestamp:
                    f.write(f"CONSOLA DEL SERVIDOR ARK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*60 + "\n\n")
                
                f.write(self.console_text.get("1.0", "end"))
                
            # Mostrar mensaje de éxito
            self.show_export_success(filepath)
            
        except Exception as e:
            self.logger.error(f"Error al exportar consola: {e}")
    
    def clear_console_buffer(self):
        """Limpiar solo el buffer de la consola"""
        try:
            self.console_buffer.clear()
            self.update_console_info()
            self.add_console_line("🧹 Buffer de consola limpiado", "info")
        except Exception as e:
            self.logger.error(f"Error limpiando buffer: {e}")
    
    def set_max_buffer_lines(self, max_lines):
        """Establecer número máximo de líneas en el buffer"""
        try:
            self.max_buffer_lines = max_lines
            self.update_console_info()
            self.add_console_line(f"📊 Buffer máximo establecido en {max_lines} líneas", "info")
        except Exception as e:
            self.logger.error(f"Error estableciendo buffer: {e}")
    
    def get_console_statistics(self):
        """Obtener estadísticas de la consola"""
        try:
            total_lines = len(self.console_text.get("1.0", "end").splitlines())
            buffer_size = len(self.console_buffer)
            uptime = datetime.now() - self.start_time if hasattr(self, 'start_time') else None
            
            # Contar líneas por tipo
            info_lines = 0
            success_lines = 0
            warning_lines = 0
            error_lines = 0
            normal_lines = 0
            
            for entry in self.console_buffer:
                line_type = entry.get('type', 'normal')
                if line_type == 'info':
                    info_lines += 1
                elif line_type == 'success':
                    success_lines += 1
                elif line_type == 'warning':
                    warning_lines += 1
                elif line_type == 'error':
                    error_lines += 1
                else:
                    normal_lines += 1
            
            # Obtener última actualización
            last_update = "Nunca"
            if self.console_buffer:
                last_entry = self.console_buffer[-1]
                last_update = last_entry.get('timestamp', 'Nunca')
            
            stats = {
                "total_lines": total_lines,
                "buffer_size": buffer_size,
                "max_buffer": self.max_buffer_lines,
                "auto_scroll": self.auto_scroll,
                "console_active": self.console_active,
                "uptime": uptime,
                "info_lines": info_lines,
                "success_lines": success_lines,
                "warning_lines": warning_lines,
                "error_lines": error_lines,
                "normal_lines": normal_lines,
                "last_update": last_update
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def show_server_events(self):
        """Mostrar eventos del servidor"""
        try:
            self.events_text.delete("1.0", "end")
            
            content = f"""🎮 EVENTOS DEL SERVIDOR ARK - {datetime.now().strftime('%H:%M:%S')}
{'='*60}

"""
            
            # Buscar archivo de eventos de hoy
            today = datetime.now().strftime('%Y-%m-%d')
            events_file = f"logs/server_events/server_events_{today}.log"
            
            if os.path.exists(events_file):
                try:
                    with open(events_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    if lines:
                        content += f"📂 Archivo: {events_file}\n"
                        content += f"📊 Total de eventos: {len(lines)}\n\n"
                        
                        # Mostrar últimos 20 eventos
                        recent = lines[-20:] if len(lines) > 20 else lines
                        content += "🔄 EVENTOS RECIENTES:\n\n"
                        content += "".join(recent)
                    else:
                        content += "📝 El archivo existe pero está vacío"
                        
                except Exception as e:
                    content += f"❌ Error leyendo archivo: {e}"
            else:
                content += f"📂 Buscando: {events_file}\n"
                content += "❌ No se encontró archivo de eventos para hoy\n\n"
                content += "💡 Los eventos aparecerán cuando:\n"
                content += "  • Inicies/detengas el servidor\n"
                content += "  • Realices backups\n"
                content += "  • Ejecutes comandos RCON\n"
                content += "  • Ocurran reinicios automáticos\n"
            
            self.events_text.insert("1.0", content)
            
        except Exception as e:
            self.events_text.delete("1.0", "end")
            self.events_text.insert("1.0", f"❌ Error mostrando eventos: {e}")
    
    def show_app_log(self):
        """Mostrar log de la aplicación"""
        try:
            self.app_text.delete("1.0", "end")
            
            content = f"""📋 LOG DE LA APLICACIÓN - {datetime.now().strftime('%H:%M:%S')}
{'='*60}

"""
            
            log_file = "logs/app.log"
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    if lines:
                        content += f"📂 Archivo: {log_file}\n"
                        content += f"📊 Total de líneas: {len(lines)}\n\n"
                        
                        # Mostrar últimas 30 líneas
                        recent = lines[-30:] if len(lines) > 30 else lines
                        content += "🔄 ENTRADAS RECIENTES:\n\n"
                        content += "".join(recent)
                    else:
                        content += "📝 El archivo existe pero está vacío"
                        
                except Exception as e:
                    content += f"❌ Error leyendo archivo: {e}"
            else:
                content += f"❌ No se encontró: {log_file}\n"
                content += "💡 El archivo se creará automáticamente cuando la app registre eventos"
            
            self.app_text.insert("1.0", content)
            
        except Exception as e:
            self.app_text.delete("1.0", "end")
            self.app_text.insert("1.0", f"❌ Error mostrando log: {e}")
    
    def refresh_current(self):
        """Actualizar la vista actual"""
        # This method is now redundant with the new tabview structure.
        # It might need to be re-evaluated based on how the user intends to use this.
        # For now, it will just reload the initial content for the system tab.
        self.load_initial_content()
    
    def clear_logs(self):
        """Limpiar pantalla"""
        # This method is now redundant with the new tabview structure.
        # It might need to be re-evaluated based on how the user intends to use this.
        # For now, it will just clear the system text area.
        self.clear_system_logs()
    
    def add_message(self, message, msg_type="info"):
        """Agregar mensaje al área de logs del sistema"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Emoji según tipo de mensaje
            emoji_map = {
                "info": "ℹ️",
                "success": "✅", 
                "warning": "⚠️",
                "error": "❌"
            }
            emoji = emoji_map.get(msg_type, "ℹ️")
            
            full_msg = f"[{timestamp}] {emoji} {message}\n"
            
            # Si no hay contenido o es el welcome, limpiar primero
            current = self.system_text.get("1.0", "end").strip()
            if not current or "✅ Panel de logs inicializado correctamente" in current:
                header = f"📋 LOGS DEL SISTEMA ARK - {datetime.now().strftime('%H:%M:%S')}\n{'='*60}\n\n"
                self.system_text.delete("1.0", "end")
                self.system_text.insert("1.0", header + full_msg)
            else:
                self.system_text.insert("end", full_msg)
            
            # Scroll al final
            self.system_text.see("end")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error agregando mensaje: {e}")
    
    # Métodos para la pestaña del sistema
    def refresh_system_logs(self):
        """Actualizar logs del sistema"""
        try:
            self.load_initial_content()
            self.add_message("Logs del sistema actualizados", "success")
        except Exception as e:
            self.add_message(f"Error actualizando logs: {e}", "error")
    
    def clear_system_logs(self):
        """Limpiar logs del sistema"""
        try:
            self.system_text.delete("1.0", "end")
            self.system_text.insert("1.0", f"🗑️ Logs del sistema limpiados - {datetime.now().strftime('%H:%M:%S')}\n\nHaz clic en 'Actualizar' para recargar.")
        except Exception as e:
            self.add_message(f"Error limpiando logs: {e}", "error")
    
    # Métodos para la pestaña de eventos
    def refresh_events(self):
        """Actualizar eventos del servidor"""
        try:
            self.show_server_events()
            self.add_message("Eventos del servidor actualizados", "success")
        except Exception as e:
            self.add_message(f"Error actualizando eventos: {e}", "error")
    
    def clear_events(self):
        """Limpiar eventos del servidor"""
        try:
            self.events_text.delete("1.0", "end")
            self.events_text.insert("1.0", f"🗑️ Eventos del servidor limpiados - {datetime.now().strftime('%H:%M:%S')}\n\nHaz clic en 'Eventos Servidor' para recargar.")
        except Exception as e:
            self.add_message(f"Error limpiando eventos: {e}", "error")
    
    # Métodos para la pestaña de aplicación
    def refresh_app_log(self):
        """Actualizar log de la aplicación"""
        try:
            self.show_app_log()
            self.add_message("Log de la aplicación actualizado", "success")
        except Exception as e:
            self.add_message(f"Error actualizando log de app: {e}", "error")
    
    def clear_app_log(self):
        """Limpiar log de la aplicación"""
        try:
            self.app_text.delete("1.0", "end")
            self.app_text.insert("1.0", f"🗑️ Log de la aplicación limpiado - {datetime.now().strftime('%H:%M:%S')}\n\nHaz clic en 'Log App' para recargar.")
        except Exception as e:
            self.add_message(f"Error limpiando log de app: {e}", "error")
    
    # Métodos de compatibilidad (mantener para retrocompatibilidad)
    def refresh_current(self):
        """Actualizar la vista actual (compatibilidad)"""
        self.refresh_system_logs()
    
    def clear_logs(self):
        """Limpiar pantalla (compatibilidad)"""
        self.clear_system_logs()

    def on_server_selection_changed(self, server_name):
        """Método llamado cuando cambia la selección del servidor"""
        try:
            if server_name != getattr(self, '_current_server', None):
                self._current_server = server_name
                
                # Desconectar del servidor anterior si está conectado
                if self.is_connected:
                    self.disconnect_from_server()
                
                # Limpiar consola
                self.clear_console()
                
                # Cargar nueva configuración
                self.load_rcon_config()
                
                # Mostrar mensaje de cambio
                self.add_console_line(f"🔄 Servidor cambiado a: {server_name}", "info")
                
        except Exception as e:
            self.logger.error(f"Error en cambio de servidor: {e}")

    def manual_connect(self):
        """Conectar manualmente al servidor"""
        try:
            if self.is_connected:
                self.add_console_line("ℹ️ Ya estás conectado al servidor", "info")
                return
                
            self.add_console_line("🔄 Iniciando conexión manual...", "info")
            
            # Intentar conexión RCON si hay password
            if self.rcon_password:
                self.connect_to_server_console(self.rcon_ip, self.rcon_port, self.rcon_password)
            else:
                # Si no hay RCON, intentar conexión directa
                self.add_console_line("⚠️ No hay password RCON, intentando conexión directa...", "warning")
                if self.connect_to_server_direct():
                    self.is_connected = True
                    self.set_console_active(True)
                    self.add_console_line("🎮 Consola del servidor ARK activa (Captura directa)", "success")
                    self.start_direct_monitoring()
                else:
                    self.add_console_line("❌ No se pudo conectar al servidor", "error")
            
        except Exception as e:
            self.add_console_line(f"❌ Error en conexión manual: {e}", "error")
    
    def update_connection_buttons(self):
        """Actualizar estado de los botones de conexión"""
        try:
            if self.is_connected:
                self.connect_btn.configure(text="🔌 Conectado", fg_color="gray", state="disabled")
                self.disconnect_btn.configure(state="normal")
                self.connection_status_label.configure(
                    text="Estado: Conectado",
                    fg_color=("lightgreen", "darkgreen")
                )
            else:
                self.connect_btn.configure(text="🔌 Conectar", fg_color="green", state="normal")
                self.disconnect_btn.configure(state="disabled")
                self.connection_status_label.configure(
                    text="Estado: Desconectado",
                    fg_color=("lightcoral", "darkred")
                )
        except Exception as e:
            self.logger.error(f"Error actualizando botones: {e}")

    def execute_custom_command(self):
        """Ejecutar comando personalizado ingresado por el usuario"""
        try:
            command = self.command_entry.get().strip()
            if not command:
                self.add_console_line("❌ Por favor ingresa un comando", "error")
                return
                
            if not self.is_connected:
                self.add_console_line("❌ No hay conexión al servidor", "error")
                return
                
            # Mostrar comando que se va a ejecutar
            self.add_console_line(f"📤 Ejecutando comando: {command}", "info")
            
            # Ejecutar comando RCON
            result = self.execute_rcon_command(command)
            
            if result:
                self.add_console_line(f"📥 Respuesta: {result}", "success")
            else:
                self.add_console_line(f"⚠️ Comando ejecutado pero sin respuesta", "warning")
                
            # Limpiar campo de entrada
            self.command_entry.delete(0, "end")
            
        except Exception as e:
            self.add_console_line(f"❌ Error ejecutando comando: {e}", "error")
    
    def clear_command_entry(self):
        """Limpiar el campo de entrada de comandos"""
        self.command_entry.delete(0, "end")
        self.add_console_line("🧹 Campo de comando limpiado", "info")
