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
from .dialogs.advanced_settings_dialog import AdvancedSettingsDialog
from .dialogs.custom_dialogs import show_info, show_warning, show_error, ask_yes_no, ask_string
from utils.app_settings import AppSettings
from utils.system_tray import SystemTray

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
        
        # Inicializar configuraciones avanzadas
        self.app_settings = AppSettings(config_manager, logger)
        
        # Inicializar bandeja del sistema
        self.system_tray = SystemTray(self, self.app_settings, logger)
        
        # Variables para diálogos
        self.settings_dialog = None
        
        # Configurar el grid principal
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Crear barra superior con menú y estado
        self.create_top_bar()
        
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
        
        
    def create_tabview(self):
        """Crear el sistema de pestañas principal"""
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.grid(row=1, column=0, padx=2, pady=1, sticky="nsew")
        
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
        
        # Aplicar configuraciones de la aplicación
        self.apply_app_settings()
        
        # Registrar evento de inicio de la aplicación
        if hasattr(self, 'server_event_logger'):
            self.log_server_event("custom_event", 
                event_name="Aplicación iniciada", 
                details="Ark Server Manager se ha iniciado correctamente")
        
        # Mostrar la pestaña inicial
        # Inicializar con la pestaña Principal activa
        self.tabview.set("Principal")
        
    def create_logs_bar(self):
        """Crear barra de logs siempre visible en la parte inferior"""
        # Frame para la barra de logs
        logs_frame = ctk.CTkFrame(self.root, height=85, corner_radius=0)
        logs_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        
        # Título de la barra de logs
        logs_title = ctk.CTkLabel(logs_frame, text="Logs del Sistema", font=("Arial", 11, "bold"))
        logs_title.pack(pady=(3, 0))
        
        # Área de texto para los logs
        self.logs_text = ctk.CTkTextbox(logs_frame, height=60, state="disabled")
        self.logs_text.pack(fill="both", expand=True, padx=5, pady=3)
        
        # Mensaje inicial
        self.add_log_message("🚀 Aplicación iniciada correctamente")
    

    def setup_button_callbacks(self):
        """Configurar callbacks de los botones"""
        # Los botones ya tienen sus comandos configurados en create_top_bar
        pass
    
    def show_menu(self):
        """Mostrar menú principal con opciones avanzadas"""
        menu = ctk.CTkToplevel(self.root)
        menu.title("📋 Menú Principal")
        menu.geometry("300x400")
        menu.transient(self.root)
        menu.grab_set()
        
        # Centrar en pantalla
        menu.geometry("+400+200")
        
        # Frame principal
        main_frame = ctk.CTkFrame(menu)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        ctk.CTkLabel(main_frame, text="📋 Menú Principal", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Botones del menú
        ctk.CTkButton(main_frame, text="🎮 Estado del Servidor", command=lambda: self.switch_to_tab("Principal")).pack(pady=5, fill="x", padx=20)
        ctk.CTkButton(main_frame, text="💾 Realizar Backup", command=self.quick_backup).pack(pady=5, fill="x", padx=20)
        ctk.CTkButton(main_frame, text="🔄 Reiniciar Servidor", command=self.quick_restart).pack(pady=5, fill="x", padx=20)
        ctk.CTkButton(main_frame, text="📊 Monitoreo", command=lambda: self.switch_to_tab("Reinicios")).pack(pady=5, fill="x", padx=20)
        ctk.CTkButton(main_frame, text="📝 Ver Logs", command=lambda: self.switch_to_tab("Logs")).pack(pady=5, fill="x", padx=20)
        
        # Separador
        ctk.CTkFrame(main_frame, height=2).pack(pady=10, fill="x", padx=20)
        
        # Opciones de ventana
        ctk.CTkButton(main_frame, text="📌 Siempre Visible", command=self.toggle_always_on_top).pack(pady=5, fill="x", padx=20)
        ctk.CTkButton(main_frame, text="📮 Minimizar a Bandeja", command=self.minimize_to_tray).pack(pady=5, fill="x", padx=20)
        
        # Cerrar
        ctk.CTkButton(main_frame, text="❌ Cerrar", command=menu.destroy).pack(pady=10, fill="x", padx=20)
    
    def show_herramientas(self):
        """Mostrar herramientas del sistema"""
        menu = ctk.CTkToplevel(self.root)
        menu.title("🔧 Herramientas")
        menu.geometry("350x450")
        menu.transient(self.root)
        menu.grab_set()
        
        menu.geometry("+450+200")
        
        main_frame = ctk.CTkFrame(menu)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(main_frame, text="🔧 Herramientas del Sistema", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Herramientas
        ctk.CTkButton(main_frame, text="🔍 Verificar Archivos del Servidor", command=self.verify_server_files).pack(pady=5, fill="x", padx=20)
        ctk.CTkButton(main_frame, text="🧹 Limpiar Logs Antiguos", command=self.clean_old_logs).pack(pady=5, fill="x", padx=20)
        ctk.CTkButton(main_frame, text="📁 Abrir Carpeta del Servidor", command=self.open_server_folder).pack(pady=5, fill="x", padx=20)
        ctk.CTkButton(main_frame, text="💾 Exportar Configuración", command=self.export_config).pack(pady=5, fill="x", padx=20)
        ctk.CTkButton(main_frame, text="📥 Importar Configuración", command=self.import_config).pack(pady=5, fill="x", padx=20)
        ctk.CTkButton(main_frame, text="🔄 Actualizar SteamCMD", command=self.update_steamcmd).pack(pady=5, fill="x", padx=20)
        ctk.CTkButton(main_frame, text="📊 Información del Sistema", command=self.show_system_info).pack(pady=5, fill="x", padx=20)
        
        ctk.CTkButton(main_frame, text="❌ Cerrar", command=menu.destroy).pack(pady=20, fill="x", padx=20)
    
    def show_ayuda(self):
        """Mostrar ayuda y acerca de"""
        menu = ctk.CTkToplevel(self.root)
        menu.title("❓ Ayuda")
        menu.geometry("400x500")
        menu.transient(self.root)
        menu.grab_set()
        
        menu.geometry("+500+150")
        
        main_frame = ctk.CTkFrame(menu)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(main_frame, text="❓ Ayuda y Soporte", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Info de la aplicación
        info_text = """
🎮 Ark Server Manager v2.0
📅 Desarrollado en 2025
🔧 Para Ark Survival Ascended

✨ Características:
• Gestión completa de servidores
• Sistema de mods integrado
• Backups automáticos y programados
• Sistema de reinicios programados
• Configuración avanzada
• Monitoreo del sistema
• RCON integrado

🔧 Funcionalidades avanzadas:
• Inicio con Windows
• Minimización a bandeja
• Auto-inicio de servidor
• Backups automáticos
• Tema personalizable
        """.strip()
        
        text_widget = ctk.CTkTextbox(main_frame, height=300)
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert("1.0", info_text)
        text_widget.configure(state="disabled")
        
        # Botones de ayuda
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkButton(buttons_frame, text="📖 Guía de Usuario", command=self.open_user_guide).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="🐛 Reportar Bug", command=self.report_bug).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="❌ Cerrar", command=menu.destroy).pack(side="right", padx=5)
    
    def show_configuracion(self):
        """Mostrar configuración avanzada"""
        if self.settings_dialog is None:
            self.settings_dialog = AdvancedSettingsDialog(self.root, self.app_settings, self.logger)
        self.settings_dialog.show()
    
    def salir_aplicacion(self):
        """Salir de la aplicación con confirmación"""
        if self.app_settings.get_setting("confirm_exit"):
            if ask_yes_no(self.root, "Confirmar salida", "¿Estás seguro de que quieres salir de Ark Server Manager?"):
                self.cleanup_and_exit()
        else:
            self.cleanup_and_exit()
    
    def cleanup_and_exit(self):
        """Limpiar recursos y salir"""
        try:
            # Guardar configuraciones
            if hasattr(self, 'app_settings'):
                self.save_window_position()
                self.app_settings.save_settings()
            
            # Detener bandeja del sistema
            if hasattr(self, 'system_tray'):
                self.system_tray.stop_tray()
            
            self.add_log_message("🚪 Cerrando aplicación...")
            self.root.quit()
        except Exception as e:
            self.logger.error(f"Error al cerrar aplicación: {e}")
            self.root.quit()
    
    def add_log_message(self, message):
        """Agregar mensaje al log del sistema"""
        # Ahora usamos el logger principal en lugar del widget de logs
        self.logger.info(message)
        
        # También actualizar el panel de logs si existe
        if hasattr(self, 'logs_panel') and hasattr(self.logs_panel, 'load_content'):
            # Programar la actualización para el siguiente ciclo de la GUI
            self.root.after(100, self.logs_panel.load_content)
    
    # ==================== MÉTODOS DE CONFIGURACIÓN AVANZADA ====================
    
    def apply_app_settings(self):
        """Aplicar configuraciones de la aplicación"""
        try:
            # Aplicar tema
            theme = self.app_settings.get_setting("theme_mode", "system")
            ctk.set_appearance_mode(theme)
            
            # Configurar ventana siempre visible
            if self.app_settings.get_setting("always_on_top"):
                self.root.attributes('-topmost', True)
            
            # Configurar geometría de ventana
            if self.app_settings.get_setting("remember_window_position"):
                geometry = self.app_settings.get_window_geometry()
                self.root.geometry(geometry)
            
            # Iniciar bandeja del sistema si está configurada
            if self.app_settings.get_setting("minimize_to_tray") or self.app_settings.get_setting("close_to_tray"):
                self.system_tray.start_tray()
            
            # Auto-iniciar servidor si está configurado
            if self.app_settings.get_setting("auto_start_server"):
                self.root.after(3000, self.auto_start_server_if_configured)
            
            # Auto-backup al iniciar
            if self.app_settings.get_setting("auto_backup_on_start"):
                self.root.after(5000, self.auto_backup_on_start)
            
            # Minimizar al iniciar si está configurado
            if self.app_settings.get_setting("start_minimized"):
                self.root.after(1000, self.minimize_to_tray)
            
            self.logger.info("Configuraciones de aplicación aplicadas")
            
        except Exception as e:
            self.logger.error(f"Error al aplicar configuraciones: {e}")
    
    def save_window_position(self):
        """Guardar posición actual de la ventana"""
        try:
            if self.app_settings.get_setting("remember_window_position"):
                geometry = self.root.geometry()
                # Parsear geometría: WIDTHxHEIGHT+X+Y
                parts = geometry.replace('x', '+').replace('-', '+-').split('+')
                if len(parts) >= 4:
                    width = int(parts[0])
                    height = int(parts[1])
                    x = int(parts[2])
                    y = int(parts[3])
                    self.app_settings.save_window_position(x, y, width, height)
        except Exception as e:
            self.logger.error(f"Error al guardar posición de ventana: {e}")
    
    # ==================== MÉTODOS DEL MENÚ ====================
    
    def switch_to_tab(self, tab_name):
        """Cambiar a una pestaña específica"""
        try:
            if hasattr(self, 'tabview'):
                self.tabview.set(tab_name)
        except Exception as e:
            self.logger.error(f"Error al cambiar a pestaña {tab_name}: {e}")
    
    def quick_backup(self):
        """Realizar backup rápido"""
        try:
            if hasattr(self, 'backup_panel'):
                # El backup_panel es AdvancedBackupPanel que tiene handle_manual_backup
                if hasattr(self.backup_panel, 'handle_manual_backup'):
                    self.backup_panel.handle_manual_backup()
                    self.add_log_message("💾 Backup manual iniciado")
                elif hasattr(self.backup_panel, 'manual_backup'):
                    self.backup_panel.manual_backup()
                    self.add_log_message("💾 Backup manual iniciado")
                else:
                    show_warning(self.root, "Backup", "El panel de backup no tiene método manual disponible")
        except Exception as e:
            self.logger.error(f"Error en backup rápido: {e}")
            show_error(self.root, "Error de Backup", f"Error al realizar backup: {str(e)}")
    
    def quick_restart(self):
        """Reinicio rápido del servidor"""
        try:
            if hasattr(self, 'server_panel'):
                if ask_yes_no(self.root, "Confirmar reinicio", "¿Quieres reiniciar el servidor ahora?"):
                    self.server_panel.restart_server()
                    self.add_log_message("🔄 Reinicio de servidor iniciado")
        except Exception as e:
            self.logger.error(f"Error en reinicio rápido: {e}")
            show_error(self.root, "Error de Reinicio", f"Error al reiniciar servidor: {str(e)}")
    
    def toggle_always_on_top(self):
        """Alternar ventana siempre visible"""
        try:
            current = self.app_settings.get_setting("always_on_top")
            new_value = not current
            self.app_settings.set_setting("always_on_top", new_value)
            self.root.attributes('-topmost', new_value)
            
            status = "activado" if new_value else "desactivado"
            self.add_log_message(f"📌 Siempre visible {status}")
        except Exception as e:
            self.logger.error(f"Error al alternar siempre visible: {e}")
    
    def minimize_to_tray(self):
        """Minimizar a la bandeja del sistema"""
        try:
            if self.system_tray.is_available():
                self.system_tray.hide_to_tray()
            else:
                self.root.iconify()
                self.add_log_message("📦 Aplicación minimizada")
        except Exception as e:
            self.logger.error(f"Error al minimizar: {e}")
    
    def auto_start_server_if_configured(self):
        """Auto-iniciar servidor si está configurado"""
        try:
            if self.selected_server and self.selected_map:
                if hasattr(self, 'server_panel'):
                    self.server_panel.start_server()
                    self.add_log_message("🚀 Servidor iniciado automáticamente")
        except Exception as e:
            self.logger.error(f"Error en auto-inicio: {e}")
    
    def auto_backup_on_start(self):
        """Realizar backup automático al iniciar"""
        try:
            if hasattr(self, 'backup_panel'):
                # El backup_panel es AdvancedBackupPanel que tiene handle_manual_backup
                if hasattr(self.backup_panel, 'handle_manual_backup'):
                    self.backup_panel.handle_manual_backup()
                    self.add_log_message("💾 Backup automático al iniciar")
                elif hasattr(self.backup_panel, 'manual_backup'):
                    self.backup_panel.manual_backup()
                    self.add_log_message("💾 Backup automático al iniciar")
        except Exception as e:
            self.logger.error(f"Error en backup automático: {e}")
    
    # ==================== MÉTODOS DE HERRAMIENTAS ====================
    
    def verify_server_files(self):
        """Verificar integridad de archivos del servidor"""
        self.add_log_message("🔍 Verificando archivos del servidor...")
        show_info(self.root, "Verificación", "Funcionalidad de verificación en desarrollo")
    
    def clean_old_logs(self):
        """Limpiar logs antiguos"""
        self.add_log_message("🧹 Limpiando logs antiguos...")
        show_info(self.root, "Limpieza", "Logs antiguos limpiados")
    
    def open_server_folder(self):
        """Abrir carpeta del servidor"""
        try:
            import os
            import subprocess
            if self.selected_server:
                server_path = self.config_manager.get_server_path(self.selected_server)
                if os.path.exists(server_path):
                    subprocess.Popen(f'explorer "{server_path}"')
                    self.add_log_message(f"📁 Abriendo carpeta: {server_path}")
                else:
                    show_error(self.root, "Error", "Carpeta del servidor no encontrada")
            else:
                show_warning(self.root, "Advertencia", "Selecciona un servidor primero")
        except Exception as e:
            self.logger.error(f"Error al abrir carpeta: {e}")
    
    def export_config(self):
        """Exportar configuración"""
        try:
            import tkinter.filedialog as fd
            file_path = fd.asksaveasfilename(
                title="Exportar configuración",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")]
            )
            if file_path:
                self.app_settings.export_settings(file_path)
                self.add_log_message(f"💾 Configuración exportada: {file_path}")
        except Exception as e:
            self.logger.error(f"Error al exportar: {e}")
    
    def import_config(self):
        """Importar configuración"""
        try:
            import tkinter.filedialog as fd
            file_path = fd.askopenfilename(
                title="Importar configuración",
                filetypes=[("JSON files", "*.json")]
            )
            if file_path:
                self.app_settings.import_settings(file_path)
                self.add_log_message(f"📥 Configuración importada: {file_path}")
        except Exception as e:
            self.logger.error(f"Error al importar: {e}")
    
    def update_steamcmd(self):
        """Actualizar SteamCMD"""
        self.add_log_message("🔄 Actualizando SteamCMD...")
        show_info(self.root, "Actualización", "Actualización de SteamCMD en desarrollo")
    
    def show_system_info(self):
        """Mostrar información del sistema"""
        try:
            import platform
            import psutil
            
            info = f"""
🖥️ Sistema: {platform.system()} {platform.release()}
🏗️ Arquitectura: {platform.architecture()[0]}
💾 RAM: {round(psutil.virtual_memory().total / (1024**3), 1)} GB
💽 Espacio libre: {round(psutil.disk_usage('.').free / (1024**3), 1)} GB
🐍 Python: {platform.python_version()}
            """.strip()
            
            show_info(self.root, "Información del Sistema", info)
            
        except Exception as e:
            self.logger.error(f"Error al obtener info del sistema: {e}")
    
    def open_user_guide(self):
        """Abrir guía de usuario"""
        try:
            import webbrowser
            webbrowser.open("https://github.com/tu-usuario/ark-server-manager/wiki")
        except:
            show_info(self.root, "Guía", "Guía de usuario disponible en el repositorio del proyecto")
    
    def report_bug(self):
        """Reportar un bug"""
        try:
            import webbrowser
            webbrowser.open("https://github.com/tu-usuario/ark-server-manager/issues")
        except:
            show_info(self.root, "Reportar Bug", "Puedes reportar bugs en el repositorio del proyecto")
        
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
