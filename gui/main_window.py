import customtkinter as ctk
from .panels.server_panel import ServerPanel
from .panels.config_panel import ConfigPanel
from .panels.monitoring_panel import MonitoringPanel
from .panels.backup_panel import BackupPanel
from .panels.players_panel import PlayersPanel
from .panels.logs_panel import LogsPanel

class MainWindow:
    def __init__(self, root, config_manager, logger):
        self.root = root
        self.config_manager = config_manager
        self.logger = logger
        
        # Configurar el grid principal
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Crear sidebar
        self.create_sidebar()
        
        # Crear pestañas principales
        self.create_tabview()
        
    def create_sidebar(self):
        """Crear la barra lateral con navegación"""
        self.sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)
        
        # Título
        self.logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="ARK SERVER\nMANAGER", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Botones de navegación
        self.sidebar_button_1 = ctk.CTkButton(
            self.sidebar, 
            text="Servidor", 
            command=self.show_server_panel
        )
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        
        self.sidebar_button_2 = ctk.CTkButton(
            self.sidebar, 
            text="Configuración", 
            command=self.show_config_panel
        )
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)
        
        self.sidebar_button_3 = ctk.CTkButton(
            self.sidebar, 
            text="Monitoreo", 
            command=self.show_monitoring_panel
        )
        self.sidebar_button_3.grid(row=3, column=0, padx=20, pady=10)
        
        self.sidebar_button_4 = ctk.CTkButton(
            self.sidebar, 
            text="Jugadores", 
            command=self.show_players_panel
        )
        self.sidebar_button_4.grid(row=4, column=0, padx=20, pady=10)
        
        self.sidebar_button_5 = ctk.CTkButton(
            self.sidebar, 
            text="Backups", 
            command=self.show_backup_panel
        )
        self.sidebar_button_5.grid(row=5, column=0, padx=20, pady=10)
        
        self.sidebar_button_6 = ctk.CTkButton(
            self.sidebar, 
            text="Logs", 
            command=self.show_logs_panel
        )
        self.sidebar_button_6.grid(row=6, column=0, padx=20, pady=10)
        
        # Botón de configuración de apariencia
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar, text="Apariencia:", anchor="w")
        self.appearance_mode_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_menu = ctk.CTkOptionMenu(
            self.sidebar, 
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode
        )
        self.appearance_mode_menu.grid(row=8, column=0, padx=20, pady=(10, 20))
        self.appearance_mode_menu.set("Dark")
        
    def create_tabview(self):
        """Crear el sistema de pestañas principal"""
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.grid(row=0, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew")
        
        # Crear pestañas
        self.tab_server = self.tabview.add("Servidor")
        self.tab_config = self.tabview.add("Configuración")
        self.tab_monitoring = self.tabview.add("Monitoreo")
        self.tab_players = self.tabview.add("Jugadores")
        self.tab_backup = self.tabview.add("Backups")
        self.tab_logs = self.tabview.add("Logs")
        
        # Inicializar paneles
        self.server_panel = ServerPanel(self.tab_server, self.config_manager, self.logger)
        self.config_panel = ConfigPanel(self.tab_config, self.config_manager, self.logger)
        self.monitoring_panel = MonitoringPanel(self.tab_monitoring, self.config_manager, self.logger)
        self.players_panel = PlayersPanel(self.tab_players, self.config_manager, self.logger)
        self.backup_panel = BackupPanel(self.tab_backup, self.config_manager, self.logger)
        self.logs_panel = LogsPanel(self.tab_logs, self.config_manager, self.logger)
        
    def show_server_panel(self):
        """Mostrar panel de servidor"""
        self.tabview.set("Servidor")
        
    def show_config_panel(self):
        """Mostrar panel de configuración"""
        self.tabview.set("Configuración")
        
    def show_monitoring_panel(self):
        """Mostrar panel de monitoreo"""
        self.tabview.set("Monitoreo")
        
    def show_players_panel(self):
        """Mostrar panel de jugadores"""
        self.tabview.set("Jugadores")
        
    def show_backup_panel(self):
        """Mostrar panel de backups"""
        self.tabview.set("Backups")
        
    def show_logs_panel(self):
        """Mostrar panel de logs"""
        self.tabview.set("Logs")
        
    def change_appearance_mode(self, new_appearance_mode: str):
        """Cambiar modo de apariencia"""
        ctk.set_appearance_mode(new_appearance_mode)
