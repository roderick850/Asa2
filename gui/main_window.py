import customtkinter as ctk
from .panels.principal_panel import PrincipalPanel
from .panels.server_panel import ServerPanel
from .panels.config_panel import ConfigPanel
from .panels.monitoring_panel import MonitoringPanel
from .panels.backup_panel import BackupPanel
from .panels.players_panel import PlayersPanel
from .panels.mods_panel import ModsPanel
from .panels.logs_panel import LogsPanel
from .panels.rcon_panel import RconPanel

class MainWindow:
    def __init__(self, root, config_manager, logger):
        self.root = root
        self.config_manager = config_manager
        self.logger = logger
        
        # Importar ServerEventLogger aquí para evitar problemas de importación circular
        from utils.server_logger import ServerEventLogger
        self.server_event_logger = ServerEventLogger("default")
        
        # Variables para el servidor y mapa seleccionados
        self.selected_server = None
        self.selected_map = None
        
        # Configurar el grid principal
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        
        # Crear barra superior con menú y estado
        self.create_top_bar()
        
        # Crear barra de pestañas principales
        self.create_tabs_bar()
        
        # Crear pestañas principales
        self.create_tabview()
        
        # Crear barra de logs siempre visible
        self.create_logs_bar()
        
        # Configurar callbacks de botones
        self.setup_button_callbacks()
        
    def create_top_bar(self):
        """Crear la barra superior con menú, administración y estado del servidor"""
        # Frame principal de la barra superior
        self.top_bar = ctk.CTkFrame(self.root, height=120, corner_radius=0)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.top_bar.grid_columnconfigure(1, weight=1)  # Espacio flexible para el estado
        
        # Frame para botones de menú pequeños (fila 0)
        menu_buttons_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        menu_buttons_frame.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Botones de menú pequeños (tamaño igual a las pestañas)
        self.menu_button = ctk.CTkButton(
            menu_buttons_frame, 
            text="Menu", 
            command=self.show_menu,
            width=100,
            height=25
        )
        self.menu_button.grid(row=0, column=0, padx=2, pady=2)
        
        self.herramientas_button = ctk.CTkButton(
            menu_buttons_frame, 
            text="Herramientas", 
            command=self.show_herramientas,
            width=100,
            height=25
        )
        self.herramientas_button.grid(row=0, column=1, padx=2, pady=2)
        
        self.ayuda_button = ctk.CTkButton(
            menu_buttons_frame, 
            text="Ayuda", 
            command=self.show_ayuda,
            width=100,
            height=25
        )
        self.ayuda_button.grid(row=0, column=2, padx=2, pady=2)
        
        self.configuracion_button = ctk.CTkButton(
            menu_buttons_frame, 
            text="Configuración", 
            command=self.show_configuracion,
            width=100,
            height=25
        )
        self.configuracion_button.grid(row=0, column=3, padx=2, pady=2)
        
        self.salir_button = ctk.CTkButton(
            menu_buttons_frame, 
            text="Salir", 
            command=self.salir_aplicacion,
            width=100,
            height=25
        )
        self.salir_button.grid(row=0, column=4, padx=2, pady=2)
        
        # Frame para botones de administración grandes (fila 1)
        admin_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        admin_frame.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        # Botones de administración del servidor (tamaño grande)
        self.start_button = ctk.CTkButton(
            admin_frame, 
            text="Iniciar Servidor", 
            command=self.start_server,
            fg_color="green",
            hover_color="darkgreen",
            width=120,
            height=30
        )
        self.start_button.grid(row=0, column=0, padx=2, pady=2)
        
        self.stop_button = ctk.CTkButton(
            admin_frame, 
            text="Detener Servidor", 
            command=self.stop_server,
            fg_color="red",
            hover_color="darkred",
            width=120,
            height=30
        )
        self.stop_button.grid(row=0, column=1, padx=2, pady=2)
        
        self.restart_button = ctk.CTkButton(
            admin_frame, 
            text="Reiniciar Servidor", 
            command=self.restart_server,
            fg_color="orange",
            hover_color="darkorange",
            width=120,
            height=30
        )
        self.restart_button.grid(row=0, column=2, padx=2, pady=2)
        
        self.install_button = ctk.CTkButton(
            admin_frame, 
            text="Instalar Servidor", 
            command=self.install_server,
            fg_color="blue",
            hover_color="darkblue",
            width=120,
            height=30
        )
        self.install_button.grid(row=0, column=3, padx=2, pady=2)
        
        self.update_button = ctk.CTkButton(
            admin_frame, 
            text="Actualizar Servidor", 
            command=self.update_server,
            fg_color="#8B00FF",
            hover_color="#6B00CC",
            width=120,
            height=30
        )
        self.update_button.grid(row=0, column=4, padx=2, pady=2)
        
        # Frame para ruta raíz (fila 2)
        path_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        path_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        
        # Etiqueta y botón para cambiar ruta raíz
        ctk.CTkLabel(path_frame, text="Ruta Raíz:").grid(row=0, column=0, padx=(0, 5), pady=2, sticky="w")
        
        self.current_path_display = ctk.CTkLabel(
            path_frame, 
            text=self.config_manager.get("server", "root_path", "No configurada"),
            fg_color=("gray90", "gray20"),
            corner_radius=5,
            padx=10,
            pady=5
        )
        self.current_path_display.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        self.browse_button = ctk.CTkButton(
            path_frame, 
            text="Cambiar", 
            command=self.browse_root_path,
            width=80,
            height=25
        )
        self.browse_button.grid(row=0, column=2, padx=(5, 0), pady=2)
        
        # Configurar peso de columna para que la ruta ocupe el espacio disponible
        #.grid_columnconfigure(1, weight=1)
        
        # Frame para selección de servidor y mapa (fila 3)
        selection_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        selection_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        
        # Etiqueta y dropdown para servidor
        ctk.CTkLabel(selection_frame, text="Servidor:").grid(row=0, column=0, padx=(0, 5), pady=2, sticky="w")
        
        self.server_dropdown = ctk.CTkOptionMenu(
            selection_frame,
            values=["Seleccionar servidor..."],
            command=self.on_server_selected,
            width=200
        )
        self.server_dropdown.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        # Botón para recargar lista de servidores
        self.refresh_servers_button = ctk.CTkButton(
            selection_frame,
            text="🔄",
            command=self.refresh_servers_list,
            width=30,
            height=25
        )
        self.refresh_servers_button.grid(row=0, column=2, padx=5, pady=2, sticky="w")
        
        # Etiqueta y dropdown para mapa
        ctk.CTkLabel(selection_frame, text="Mapa:").grid(row=0, column=3, padx=(20, 5), pady=2, sticky="w")
        
        self.map_dropdown = ctk.CTkOptionMenu(
            selection_frame,
            values=["The Island", "The Center", "Scorched Earth", "Ragnarok", "Aberration", "Extinction", "Valguero", "Genesis: Part 1", "Crystal Isles", "Genesis: Part 2", "Lost Island", "Fjordur"],
            command=self.on_map_selected,
            width=200
        )
        self.map_dropdown.grid(row=0, column=4, padx=5, pady=2, sticky="w")
        
        # Frame para estado del servidor (lado derecho, abarca todas las filas)
        status_frame = ctk.CTkFrame(self.top_bar, fg_color=("gray90", "gray20"))
        status_frame.grid(row=0, column=2, rowspan=4, padx=10, pady=5, sticky="ne")
        
        # Panel de estado del servidor
        status_panel = ctk.CTkFrame(status_frame, fg_color="transparent")
        status_panel.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título del panel de estado
        ctk.CTkLabel(status_panel, text="Estado del Servidor", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        # Estado del servidor
        status_container = ctk.CTkFrame(status_panel, fg_color="transparent")
        status_container.pack(fill="x", pady=2)
        
        ctk.CTkLabel(status_container, text="Estado:").pack(side="left")
        self.status_label = ctk.CTkLabel(status_container, text="Detenido", fg_color="red", corner_radius=5, padx=10, pady=2)
        self.status_label.pack(side="right", padx=(5, 0))
        
        # Tiempo activo
        uptime_container = ctk.CTkFrame(status_panel, fg_color="transparent")
        uptime_container.pack(fill="x", pady=2)
        
        ctk.CTkLabel(uptime_container, text="Tiempo Activo:").pack(side="left")
        self.uptime_label = ctk.CTkLabel(uptime_container, text="00:00:00", fg_color=("gray90", "gray20"), corner_radius=5, padx=10, pady=2)
        self.uptime_label.pack(side="right", padx=(5, 0))
        
        # Uso de CPU
        cpu_container = ctk.CTkFrame(status_panel, fg_color="transparent")
        cpu_container.pack(fill="x", pady=2)
        
        ctk.CTkLabel(cpu_container, text="CPU:").pack(side="left")
        self.cpu_label = ctk.CTkLabel(cpu_container, text="0%", fg_color=("gray90", "gray20"), corner_radius=5, padx=10, pady=2)
        self.cpu_label.pack(side="right", padx=(5, 0))
        
        # Uso de memoria
        memory_container = ctk.CTkFrame(status_panel, fg_color="transparent")
        memory_container.pack(fill="x", pady=2)
        
        ctk.CTkLabel(memory_container, text="Memoria:").pack(side="left")
        self.memory_label = ctk.CTkLabel(memory_container, text="0 MB", fg_color=("gray90", "gray20"), corner_radius=5, padx=10, pady=2)
        self.memory_label.pack(side="right", padx=(5, 0))
        
        # La lista de servidores se inicializará después de crear el server_panel
        
    def create_tabs_bar(self):
        """Crear la barra de pestañas principales - completamente independiente del menú"""
        # Frame principal de la barra de pestañas
        self.tabs_bar = ctk.CTkFrame(self.root, height=40, corner_radius=0)
        self.tabs_bar.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        self.tabs_bar.grid_columnconfigure(6, weight=1)  # Espacio flexible al final
        
        # Frame para pestañas
        tabs_frame = ctk.CTkFrame(self.tabs_bar, fg_color="transparent")
        tabs_frame.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Pestañas principales - completamente independientes del menú
        self.tab_principal = ctk.CTkButton(
            tabs_frame,
            text="Principal",
            command=lambda: self.show_tab("Principal"),
            fg_color="blue",
            hover_color="darkblue",
            width=100,
            height=25
        )
        self.tab_principal.grid(row=0, column=0, padx=2, pady=2)
        
        self.tab_configuraciones = ctk.CTkButton(
            tabs_frame,
            text="Configuraciones",
            command=lambda: self.show_tab("Configuraciones"),
            fg_color="gray",
            hover_color="darkgray",
            width=100,
            height=25
        )
        self.tab_configuraciones.grid(row=0, column=1, padx=2, pady=2)
        
        self.tab_mods = ctk.CTkButton(
            tabs_frame,
            text="Mods",
            command=lambda: self.show_tab("Mods"),
            fg_color="gray",
            hover_color="darkgray",
            width=100,
            height=25
        )
        self.tab_mods.grid(row=0, column=2, padx=2, pady=2)
        
        self.tab_backup = ctk.CTkButton(
            tabs_frame,
            text="Backup",
            command=lambda: self.show_tab("Backup"),
            fg_color="gray",
            hover_color="darkgray",
            width=100,
            height=25
        )
        self.tab_backup.grid(row=0, column=3, padx=2, pady=2)
        
        self.tab_reinicios = ctk.CTkButton(
            tabs_frame,
            text="Reinicios",
            command=lambda: self.show_tab("Reinicios"),
            fg_color="gray",
            hover_color="darkgray",
            width=100,
            height=25
        )
        self.tab_reinicios.grid(row=0, column=4, padx=2, pady=2)
        
        self.tab_rcon = ctk.CTkButton(
            tabs_frame,
            text="RCON",
            command=lambda: self.show_tab("RCON"),
            fg_color="gray",
            hover_color="darkgray",
            width=100,
            height=25
        )
        self.tab_rcon.grid(row=0, column=5, padx=2, pady=2)
        
        self.tab_logs = ctk.CTkButton(
            tabs_frame,
            text="Logs",
            command=lambda: self.show_tab("Logs"),
            fg_color="gray",
            hover_color="darkgray",
            width=100,
            height=25
        )
        self.tab_logs.grid(row=0, column=6, padx=2, pady=2)
        
    def create_tabview(self):
        """Crear el sistema de pestañas principal"""
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.grid(row=2, column=0, padx=2, pady=1, sticky="nsew")
        
        # Crear pestañas
        self.tab_principal_content = self.tabview.add("Principal")
        self.tab_configuraciones_content = self.tabview.add("Configuraciones")
        self.tab_mods_content = self.tabview.add("Mods")
        self.tab_backup_content = self.tabview.add("Backup")
        self.tab_reinicios_content = self.tabview.add("Reinicios")
        self.tab_rcon_content = self.tabview.add("RCON")
        self.tab_logs_content = self.tabview.add("Logs")
        
        # Crear paneles
        self.principal_panel = PrincipalPanel(self.tab_principal_content, self.config_manager, self.logger, self)
        # El ServerPanel ya no se muestra en la interfaz, pero se mantiene para funcionalidad backend
        self.server_panel = ServerPanel(None, self.config_manager, self.logger, self)
        self.config_panel = ConfigPanel(self.tab_configuraciones_content, self.config_manager, self.logger, self)
        self.mods_panel = ModsPanel(self.tab_mods_content, self.config_manager, self.logger, self)
        self.monitoring_panel = MonitoringPanel(self.tab_reinicios_content, self.config_manager, self.logger, self)
        self.backup_panel = BackupPanel(self.tab_backup_content, self.config_manager, self.logger, self)
        self.rcon_panel = RconPanel(self.tab_rcon_content, self.config_manager, self.logger, self)
        self.logs_panel = LogsPanel(self.tab_logs_content, self.config_manager, self.logger, self)
        
        # Configurar callbacks para los botones
        self.setup_button_callbacks()
        
        # Inicializar la lista de servidores después de crear el server_panel
        self.refresh_servers_list()
        
        # Cargar la última selección de servidor/mapa con un pequeño delay
        self.root.after(200, self.load_last_server_map_selection)
        
        # Registrar evento de inicio de la aplicación
        if hasattr(self, 'server_event_logger'):
            self.log_server_event("custom_event", 
                event_name="Aplicación iniciada", 
                details="Ark Server Manager se ha iniciado correctamente")
        
        # Mostrar la pestaña inicial
        self.show_tab("Principal")
        
    def create_logs_bar(self):
        """Crear barra de logs siempre visible en la parte inferior"""
        # Frame para la barra de logs
        logs_frame = ctk.CTkFrame(self.root, height=85, corner_radius=0)
        logs_frame.grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        
        # Título de la barra de logs
        logs_title = ctk.CTkLabel(logs_frame, text="Logs del Sistema", font=("Arial", 11, "bold"))
        logs_title.pack(pady=(3, 0))
        
        # Área de texto para los logs
        self.logs_text = ctk.CTkTextbox(logs_frame, height=60, state="disabled")
        self.logs_text.pack(fill="both", expand=True, padx=5, pady=3)
        
        # Mensaje inicial
        self.add_log_message("🚀 Aplicación iniciada correctamente")
    
    def show_tab(self, tab_name):
        """Muestra la pestaña seleccionada - completamente independiente del menú"""
        # Actualizar colores de los botones de pestañas
        self.tab_principal.configure(fg_color="gray")
        self.tab_configuraciones.configure(fg_color="gray")
        self.tab_mods.configure(fg_color="gray")
        self.tab_backup.configure(fg_color="gray")
        self.tab_reinicios.configure(fg_color="gray")
        self.tab_rcon.configure(fg_color="gray")
        self.tab_logs.configure(fg_color="gray")
        
        if tab_name == "Principal":
            self.tab_principal.configure(fg_color="blue")
            self.tabview.set("Principal")
        elif tab_name == "Configuraciones":
            self.tab_configuraciones.configure(fg_color="blue")
            self.tabview.set("Configuraciones")
        elif tab_name == "Mods":
            self.tab_mods.configure(fg_color="blue")
            self.tabview.set("Mods")
        elif tab_name == "Backup":
            self.tab_backup.configure(fg_color="blue")
            self.tabview.set("Backup")
        elif tab_name == "Reinicios":
            self.tab_reinicios.configure(fg_color="blue")
            self.tabview.set("Reinicios")
        elif tab_name == "RCON":
            self.tab_rcon.configure(fg_color="blue")
            self.tabview.set("RCON")
        elif tab_name == "Logs":
            self.tab_logs.configure(fg_color="blue")
        self.tabview.set("Logs")
        
    def setup_button_callbacks(self):
        """Configurar callbacks de los botones"""
        # Los botones ya tienen sus comandos configurados en create_top_bar
        pass
    
    def show_menu(self):
        """Mostrar menú principal"""
        self.add_log_message("📋 Menú principal abierto")
    
    def show_herramientas(self):
        """Mostrar herramientas"""
        self.add_log_message("🔧 Herramientas abiertas")
    
    def show_ayuda(self):
        """Mostrar ayuda"""
        self.add_log_message("❓ Ayuda abierta")
    
    def show_configuracion(self):
        """Mostrar configuración"""
        self.add_log_message("⚙️ Configuración abierta")
    
    def salir_aplicacion(self):
        """Salir de la aplicación"""
        self.add_log_message("🚪 Cerrando aplicación...")
        self.root.quit()
    
    def add_log_message(self, message):
        """Agregar mensaje al log del sistema"""
        # Ahora usamos el logger principal en lugar del widget de logs
        self.logger.info(message)
        
        # También actualizar el panel de logs si existe
        if hasattr(self, 'logs_panel') and hasattr(self.logs_panel, 'load_content'):
            # Programar la actualización para el siguiente ciclo de la GUI
            self.root.after(100, self.logs_panel.load_content)
        
    def browse_root_path(self):
        """Buscar directorio raíz para servidores"""
        from tkinter import filedialog
        directory = filedialog.askdirectory(title="Seleccionar ruta raíz para servidores")
        if directory:
            self.config_manager.set("server", "root_path", directory)
            self.config_manager.save()
            self.update_current_path_display()
            # Refrescar la lista de servidores
            if hasattr(self, 'server_panel'):
                self.server_panel.refresh_servers_list()
    
    def update_current_path_display(self):
        """Actualizar la visualización de la ruta actual"""
        current_path = self.config_manager.get("server", "root_path", "").strip()
        if current_path:
            self.current_path_display.configure(
                text=current_path,
                text_color=("green", "lightgreen")
            )
        else:
            self.current_path_display.configure(
                text="No configurada",
                text_color=("red", "orange")
            )
    
    def update_server_status(self, status, color="red"):
        """Actualizar el estado del servidor"""
        self.status_label.configure(text=status, fg_color=color)
    
    def update_uptime(self, uptime):
        """Actualizar el tiempo activo del servidor"""
        self.uptime_label.configure(text=uptime)
    
    def update_cpu_usage(self, cpu_percent):
        """Actualizar el uso de CPU del servidor"""
        self.cpu_label.configure(text=f"{cpu_percent}%")
    
    def update_memory_usage(self, memory_mb):
        """Actualizar el uso de memoria del servidor"""
        self.memory_label.configure(text=f"{memory_mb} MB")
    
    def on_server_selected(self, server_name):
        """Maneja la selección de un servidor"""
        self.selected_server = server_name
        
        # Actualizar el logger del servidor
        if hasattr(self, 'server_event_logger'):
            self.server_event_logger.update_server_name(server_name)
        
        if hasattr(self, 'server_panel'):
            self.server_panel.on_server_selected(server_name)
        if hasattr(self, 'principal_panel'):
            self.principal_panel.update_server_info(server_name, self.selected_map)
        # Actualizar contexto de mods
        if hasattr(self, 'mods_panel'):
            self.mods_panel.update_server_map_context(server_name, self.selected_map)
        # Actualizar panel de configuración
        if hasattr(self, 'config_panel'):
            self.config_panel.update_server_selection(server_name)
        # Actualizar panel de backup
        if hasattr(self, 'backup_panel'):
            self.backup_panel.update_server_selection(server_name)
        # Actualizar panel de reinicios
        if hasattr(self, 'monitoring_panel'):
            self.monitoring_panel.update_server_selection(server_name)
        # Guardar última selección
        self.save_last_server_map_selection()
    
    def log_server_event(self, event_type, **kwargs):
        """Registrar eventos del servidor y mostrar en logs"""
        try:
            if not hasattr(self, 'server_event_logger'):
                return
            
            # Registrar en el archivo de eventos
            message = ""
            if event_type == "server_start":
                message = self.server_event_logger.log_server_start(
                    kwargs.get('server_path', ''), 
                    kwargs.get('map_name', ''),
                    kwargs.get('additional_info', '')
                )
            elif event_type == "server_stop":
                message = self.server_event_logger.log_server_stop(
                    kwargs.get('reason', 'Manual'),
                    kwargs.get('additional_info', '')
                )
            elif event_type == "server_restart":
                message = self.server_event_logger.log_server_restart(
                    kwargs.get('reason', 'Manual'),
                    kwargs.get('additional_info', '')
                )
            elif event_type == "update_start":
                message = self.server_event_logger.log_server_update_start(
                    kwargs.get('method', 'SteamCMD')
                )
            elif event_type == "update_complete":
                message = self.server_event_logger.log_server_update_complete(
                    kwargs.get('success', True),
                    kwargs.get('details', '')
                )
            elif event_type == "automatic_restart_start":
                message = self.server_event_logger.log_automatic_restart_start(
                    kwargs.get('restart_info', {})
                )
            elif event_type == "automatic_restart_complete":
                message = self.server_event_logger.log_automatic_restart_complete(
                    kwargs.get('restart_info', {})
                )
            elif event_type == "backup_event":
                message = self.server_event_logger.log_backup_event(
                    kwargs.get('event_type', 'manual'),
                    kwargs.get('success', True),
                    kwargs.get('details', '')
                )
            elif event_type == "rcon_command":
                message = self.server_event_logger.log_rcon_command(
                    kwargs.get('command', ''),
                    kwargs.get('success', True),
                    kwargs.get('result', '')
                )
            elif event_type == "mod_operation":
                message = self.server_event_logger.log_mod_operation(
                    kwargs.get('operation', ''),
                    kwargs.get('mod_name', ''),
                    kwargs.get('mod_id', ''),
                    kwargs.get('success', True)
                )
            elif event_type == "config_change":
                message = self.server_event_logger.log_config_change(
                    kwargs.get('config_type', ''),
                    kwargs.get('setting_name', ''),
                    kwargs.get('old_value', ''),
                    kwargs.get('new_value', '')
                )
            elif event_type == "server_crash":
                message = self.server_event_logger.log_server_crash(
                    kwargs.get('error_details', '')
                )
            elif event_type == "custom_event":
                message = self.server_event_logger.log_custom_event(
                    kwargs.get('event_name', ''),
                    kwargs.get('details', ''),
                    kwargs.get('level', 'info')
                )
            
            # Mostrar también en el log de la aplicación y en la UI
            if message:
                self.add_log_message(message)
                
        except Exception as e:
            self.logger.error(f"Error registrando evento del servidor: {e}")
    
    def get_server_events(self, hours=24):
        """Obtener eventos recientes del servidor"""
        try:
            if hasattr(self, 'server_event_logger'):
                return self.server_event_logger.get_recent_events(hours)
            return []
        except Exception as e:
            self.logger.error(f"Error obteniendo eventos del servidor: {e}")
            return []
    
    def on_map_selected(self, map_name):
        """Maneja la selección de un mapa"""
        self.selected_map = map_name
        if hasattr(self, 'server_panel'):
            self.server_panel.on_map_selected(map_name)
        if hasattr(self, 'principal_panel'):
            self.principal_panel.update_server_info(self.selected_server, map_name)
        # Actualizar contexto de mods
        if hasattr(self, 'mods_panel'):
            self.mods_panel.update_server_map_context(self.selected_server, map_name)
    
    def refresh_servers_list(self):
        """Refresca la lista de servidores"""
        if hasattr(self, 'server_panel'):
            self.server_panel.refresh_servers_list()
    
    def load_last_server_map_selection(self):
        """Cargar la última selección de servidor y mapa"""
        try:
            last_server = self.config_manager.get("app", "last_server", "")
            last_map = self.config_manager.get("app", "last_map", "")
            
            self.logger.info(f"Intentando cargar última selección - Servidor: {last_server}, Mapa: {last_map}")
            
            if last_server and hasattr(self, 'server_dropdown'):
                # Verificar si el servidor existe en la lista
                try:
                    current_values = self.server_dropdown.cget("values")
                    self.logger.info(f"Valores actuales del dropdown de servidores: {current_values}")
                    if current_values and last_server in current_values:
                        self.server_dropdown.set(last_server)
                        self.selected_server = last_server
                        self.add_log_message(f"📂 Servidor restaurado: {last_server}")
                        self.logger.info(f"Servidor {last_server} establecido correctamente")
                        
                        # Simular la selección del servidor para cargar mapas
                        self.on_server_selected(last_server)
                    else:
                        self.logger.warning(f"Servidor {last_server} no encontrado en la lista: {current_values}")
                except Exception as e:
                    self.logger.error(f"Error al establecer servidor: {e}")
            
            # Restaurar el mapa después de un pequeño delay para permitir que se carguen los mapas
            if last_map and hasattr(self, 'map_dropdown'):
                self.logger.info(f"Programando restauración del mapa {last_map} con delay")
                self.root.after(500, lambda: self.restore_map_selection(last_map))
            else:
                self.logger.warning(f"No se puede restaurar mapa - last_map: {last_map}, tiene map_dropdown: {hasattr(self, 'map_dropdown')}")
                    
        except Exception as e:
            self.logger.error(f"Error al cargar última selección: {e}")
    
    def save_last_server_map_selection(self):
        """Guardar la última selección de servidor y mapa"""
        try:
            if hasattr(self, 'selected_server') and self.selected_server:
                self.config_manager.set("app", "last_server", self.selected_server)
            
            if hasattr(self, 'selected_map') and self.selected_map:
                self.config_manager.set("app", "last_map", self.selected_map)
            
            self.config_manager.save()
            
        except Exception as e:
            self.logger.error(f"Error al guardar última selección: {e}")
    
    def restore_map_selection(self, last_map):
        """Restaurar la selección del mapa después de que se hayan cargado los mapas"""
        try:
            self.logger.info(f"Iniciando restauración del mapa: {last_map}")
            if hasattr(self, 'map_dropdown'):
                # Intentar hasta 10 veces con un delay de 100ms cada una
                max_attempts = 10
                attempt = 0
                
                def try_restore():
                    nonlocal attempt
                    attempt += 1
                    
                    current_values = self.map_dropdown.cget("values")
                    self.logger.info(f"Intento {attempt}: Valores actuales del dropdown de mapas: {current_values}")
                    if current_values and last_map in current_values:
                        self.map_dropdown.set(last_map)
                        # Importante: Llamar manualmente a on_map_selected para disparar todas las callbacks
                        self.on_map_selected(last_map)
                        self.add_log_message(f"🗺️ Mapa restaurado: {last_map}")
                        return True
                    elif attempt < max_attempts:
                        # Intentar de nuevo después de 100ms
                        self.root.after(100, try_restore)
                        return False
                    else:
                        self.logger.warning(f"No se pudo restaurar el mapa {last_map} después de {max_attempts} intentos")
                        return False
                
                try_restore()
                
        except Exception as e:
            self.logger.error(f"Error al restaurar selección de mapa: {e}")
    
    def start_server(self):
        """Inicia el servidor"""
        if hasattr(self, 'server_panel'):
            self.server_panel.start_server()
    
    def stop_server(self):
        """Detiene el servidor"""
        if hasattr(self, 'server_panel'):
            self.server_panel.stop_server()
    
    def restart_server(self):
        """Reinicia el servidor"""
        if hasattr(self, 'server_panel'):
            self.server_panel.restart_server()
    
    def install_server(self):
        """Instala un servidor"""
        if hasattr(self, 'server_panel'):
            self.server_panel.install_server()
    
    def update_server(self):
        """Actualiza un servidor"""
        if hasattr(self, 'server_panel'):
            self.server_panel.update_server()
