import customtkinter as ctk
import os
import platform
from datetime import datetime
from .panels.principal_panel import PrincipalPanel
from .panels.server_panel import ServerPanel
from .panels.config_panel import ConfigPanel
from .panels.monitoring_panel import MonitoringPanel
from .panels.backup_panel import BackupPanel
from .panels.players_panel import PlayersPanel
from .panels.mods_panel import ModsPanel
from .panels.working_logs_panel import WorkingLogsPanel
from .panels.rcon_panel import RconPanel
from .panels.console_panel import ConsolePanel
from .dialogs.advanced_settings_dialog import AdvancedSettingsDialog
from .dialogs.custom_dialogs import show_info, show_warning, show_error, ask_yes_no, ask_string
from utils.app_settings import AppSettings
from utils.system_tray import SystemTray

class MainWindow:

    APP_VERSION = "1.0"
    
    def __init__(self, root, config_manager, logger):
        """Inicializar la ventana principal"""
        self.root = root
        self.config_manager = config_manager
        self.logger = logger
        
        # Configuración de la ventana
        self.root.title("ARK Server Manager")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # Variables de estado
        self.selected_server = None
        self.selected_map = None
        self.console_panel_managing_startup = False
        
        # Configuración de la aplicación
        self.app_settings = AppSettings(config_manager, logger)
        self.system_tray = None
        self.started_with_windows = False
        
        # Inicializar componentes
        self.server_manager = None
        self.principal_panel = None
        self.server_panel = None
        self.console_panel = None
        self.backup_panel = None
        self.logs_panel = None
        self.rcon_panel = None
        self.mods_panel = None
        self.monitoring_panel = None
        self.players_panel = None
        self.advanced_backup_panel = None
        self.advanced_restart_panel = None
        self.dynamic_config_panel = None
        self.server_config_panel = None
        
        # Configurar la ventana
        self.setup_window()
        
        # Configurar eventos
        self.setup_window_events()
        
        # Aplicar configuraciones de la aplicación
        self.apply_app_settings()
        
        # Cargar última configuración
        self.load_last_configuration()
        
        # Detectar si se inició con Windows
        self.detect_startup_with_windows()
        
        # Configurar auto-inicio si es necesario
        self.check_auto_start_fallback()
    
    def setup_window(self):
        """Configurar la ventana principal"""
        # Configurar el grid principal
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Crear barra superior con menú y estado
        self.create_top_bar()
        
        # Crear pestañas principales
        self.create_tabview()
        
        # Crear barra de logs siempre visible
        self.create_logs_bar()
        
        # Configurar callbacks de botones y eventos de ventana
        self.setup_button_callbacks()
        self.setup_window_events()
        
        # Inicializar bandeja del sistema
        self.start_system_tray()
    
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
        self.tab_console_content = self.tabview.add("Consola")
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
        self.console_panel = ConsolePanel(self.tab_console_content, self.config_manager, self.logger, self)
        self.logs_panel = WorkingLogsPanel(self.tab_logs_content, self.config_manager, self.logger, self)
        
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
        ctk.CTkButton(main_frame, text="🖥️ Consola del Servidor", command=lambda: self.switch_to_tab("Consola")).pack(pady=5, fill="x", padx=20)
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
        ctk.CTkButton(main_frame, text="🗑️ Limpiar Iconos Duplicados", command=self.cleanup_tray_icons).pack(pady=5, fill="x", padx=20)
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
        info_text = f"""
🎮 Ark Server Manager {self.APP_VERSION}
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
        """Agregar mensaje al log del sistema (área inferior)"""
        try:
            # Registrar en el logger principal
            self.logger.info(message)
            
            # Agregar timestamp y formatear el mensaje
            from datetime import datetime
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            formatted_message = f"{timestamp} ℹ️ {message}"
            
            # Escribir en el área de logs inferior si existe
            if hasattr(self, 'logs_text') and self.logs_text:
                # Habilitar escritura temporalmente
                self.logs_text.configure(state="normal")
                
                # Insertar mensaje al final
                self.logs_text.insert("end", formatted_message + "\n")
                
                # Hacer scroll al final para ver el mensaje más reciente
                self.logs_text.see("end")
                
                # Deshabilitar escritura
                self.logs_text.configure(state="disabled")
                
                # Limitar número de líneas para evitar crecimiento excesivo
                content = self.logs_text.get("1.0", "end")
                lines = content.split('\n')
                if len(lines) > 200:  # Mantener solo las últimas 200 líneas
                    self.logs_text.configure(state="normal")
                    # Eliminar las primeras 100 líneas
                    lines_to_keep = lines[-100:]
                    self.logs_text.delete("1.0", "end")
                    self.logs_text.insert("1.0", '\n'.join(lines_to_keep))
                    self.logs_text.configure(state="disabled")
            
            # También agregar al panel superior si está disponible
            if hasattr(self, 'logs_panel') and hasattr(self.logs_panel, 'add_message'):
                self.logs_panel.add_message(message, "info")
                
        except Exception as e:
            # Fallback silencioso para evitar errores en cascada
            self.logger.error(f"Error agregando mensaje a logs GUI: {e}")
    
    # ==================== MÉTODOS DE CONFIGURACIÓN AVANZADA ====================
    
    def apply_app_settings(self):
        """Aplicar configuraciones de la aplicación"""
        try:
            # Aplicar tema de forma segura
            theme = self.app_settings.get_setting("theme_mode", "system")
            self.root.after(50, lambda: self._apply_theme_safely(theme))
            
            # Configurar ventana siempre visible
            if self.app_settings.get_setting("always_on_top"):
                self.root.attributes('-topmost', True)
            
            # Configurar geometría de ventana
            if self.app_settings.get_setting("remember_window_position"):
                geometry = self.app_settings.get_window_geometry()
                self.root.geometry(geometry)
            
            # Detectar tipo de inicio
            self.started_with_windows = self.detect_startup_with_windows()
            
            # Iniciar bandeja del sistema (que manejará el auto-inicio)
            if self.app_settings.get_setting("minimize_to_tray") or self.app_settings.get_setting("close_to_tray"):
                self.start_system_tray()
            else:
                # Si no hay bandeja, usar fallback para auto-inicio
                self.check_auto_start_fallback()
            
            # Auto-backup al iniciar
            if self.app_settings.get_setting("auto_backup_on_start"):
                self.root.after(5000, self.auto_backup_on_start)
            
            # Minimizar al iniciar si está configurado
            if self.app_settings.get_setting("start_minimized"):
                self.root.after(1000, self.minimize_to_tray)
            
            self.logger.info("Configuraciones de aplicación aplicadas")
            
        except Exception as e:
            self.logger.error(f"Error al aplicar configuraciones: {e}")
    
    def _apply_theme_safely(self, theme):
        """Aplicar tema de forma segura sin bloquear la interfaz"""
        try:
            self.logger.info(f"Aplicando tema: {theme}")
            
            # Verificar que el tema sea válido
            valid_themes = ["light", "dark", "system"]
            if theme not in valid_themes:
                self.logger.warning(f"Tema no válido '{theme}', usando 'system'")
                theme = "system"
            
            # Aplicar tema con múltiples intentos para compatibilidad
            for attempt in range(3):
                try:
                    ctk.set_appearance_mode(theme)
                    self.logger.info(f"Tema '{theme}' aplicado exitosamente en intento {attempt + 1}")
                    
                    # Forzar actualización de la interfaz principal
                    try:
                        self.root.update_idletasks()
                        # También actualizar widgets principales si existen
                        if hasattr(self, 'tabview'):
                            self.tabview.update()
                    except Exception as update_e:
                        self.logger.warning(f"Error al actualizar interfaz tras cambio de tema: {update_e}")
                    
                    return  # Éxito, salir de la función
                    
                except Exception as e:
                    self.logger.warning(f"Intento {attempt + 1} de aplicar tema falló: {e}")
                    if attempt < 2:  # No es el último intento
                        import time
                        time.sleep(0.3)  # Esperar un poco más en la ventana principal
                    
            # Si llegamos aquí, todos los intentos fallaron
            self.logger.error(f"No se pudo aplicar el tema '{theme}' después de 3 intentos")
            
        except Exception as e:
            self.logger.error(f"Error crítico al aplicar tema: {e}")
    
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
    
    def update_server_status(self, status):
        """Actualizar el estado del servidor con colores automáticos"""
        # Definir colores según el estado
        if status == "Inactivo":
            color = "red"
        elif status == "Iniciando":
            color = "orange"
        elif status == "Activo":
            color = "green"
        elif status == "Error":
            color = "red"
        elif status == "Verificando...":
            color = "blue"
        else:
            color = "gray"  # Color por defecto para estados desconocidos
        
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
            # Cargar configuraciones existentes de GameUserSettings.ini
            self.principal_panel.load_from_gameusersettings()
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
        if self.logger.should_log_debug():
            self.logger.info(f"DEBUG: Mapa seleccionado en main_window: '{map_name}'")
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
                # Asegurar que guardamos el nombre amigable, no el identificador técnico
                map_to_save = self._get_friendly_map_name(self.selected_map)
                self.config_manager.set("app", "last_map", map_to_save)
                if self.logger.should_log_debug():
                    self.logger.info(f"DEBUG: Guardando mapa: '{self.selected_map}' como '{map_to_save}'")
            
            self.config_manager.save()
            
        except Exception as e:
            self.logger.error(f"Error al guardar última selección: {e}")
    
    def _get_friendly_map_name(self, map_value):
        """Convierte identificador técnico a nombre amigable si es necesario"""
        # Mapeo inverso: identificador técnico -> nombre amigable
        # NOTA: También incluimos variantes sin espacios que pueden aparecer
        tech_to_friendly = {
            "TheIsland_WP": "The Island",
            "TheIsland": "The Island",
            "TheCenter_WP": "The Center",        # ✅ ASA usa _WP
            "TheCenter": "The Center",
            "ScorchedEarth_WP": "Scorched Earth",
            "ScorchedEarth": "Scorched Earth",
            "Ragnarok_WP": "Ragnarok",           # ✅ ASA usa _WP
            "Ragnarok": "Ragnarok",
            "Aberration_P": "Aberration",
            "Extinction": "Extinction",
            "Valguero_P": "Valguero",
            "Genesis": "Genesis: Part 1",
            "Genesis1": "Genesis: Part 1",
            "CrystalIsles": "Crystal Isles",
            "Genesis2": "Genesis: Part 2",
            "LostIsland": "Lost Island",
            "Fjordur": "Fjordur"
        }
        
        # Si es un identificador técnico, convertir a nombre amigable
        if map_value in tech_to_friendly:
            friendly_name = tech_to_friendly[map_value]
            if self.logger.should_log_debug():
                self.logger.info(f"DEBUG: Convertido identificador '{map_value}' a nombre amigable '{friendly_name}'")
            return friendly_name
        
        # Si ya es un nombre amigable, devolverlo tal como está
        return map_value
    
    def restore_map_selection(self, last_map):
        """Restaurar la selección del mapa después de que se hayan cargado los mapas"""
        try:
            self.logger.info(f"Iniciando restauración del mapa: {last_map}")
            if hasattr(self, 'map_dropdown'):
                # Convertir a nombre amigable si es necesario
                friendly_map = self._get_friendly_map_name(last_map)
                if self.logger.should_log_debug():
                    self.logger.info(f"DEBUG: Restaurando mapa - original: '{last_map}', amigable: '{friendly_map}'")
                
                # Intentar hasta 10 veces con un delay de 100ms cada una
                max_attempts = 10
                attempt = 0
                
                def try_restore():
                    nonlocal attempt
                    attempt += 1
                    
                    current_values = self.map_dropdown.cget("values")
                    self.logger.info(f"Intento {attempt}: Valores actuales del dropdown de mapas: {current_values}")
                    if current_values and friendly_map in current_values:
                        self.map_dropdown.set(friendly_map)
                        # Importante: Llamar manualmente a on_map_selected para disparar todas las callbacks
                        self.on_map_selected(friendly_map)
                        self.add_log_message(f"🗺️ Mapa restaurado: {friendly_map}")
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
        """Detener servidor con confirmación y saveworld"""
        try:
            # Confirmar acción
            if not ask_yes_no(self.root, "🛑 Confirmar Detención", 
                             "¿Estás seguro de que quieres DETENER el servidor?\n\n"
                             "• Se guardará el mundo automáticamente\n"
                             "• Los jugadores serán desconectados\n"
                             "• El servidor se detendrá completamente"):
                self.add_log_message("❌ Detención cancelada por el usuario")
                return
            
            self.add_log_message("🛑 Iniciando detención del servidor...")
            
            # Ejecutar saveworld antes de detener
            self.add_log_message("💾 Guardando mundo antes de detener...")
            if hasattr(self, 'server_panel'):
                # Programar detención después del saveworld
                self.root.after(100, self._execute_stop_with_saveworld)
                
        except Exception as e:
            self.logger.error(f"Error al detener servidor: {e}")
            show_error(self.root, "Error", f"Error al detener servidor: {str(e)}")
    
    def _execute_stop_with_saveworld(self):
        """Ejecutar saveworld y luego detener servidor"""
        try:
            self.add_log_message("💾 Ejecutando comando saveworld...")
            
            # Ejecutar saveworld via RCON
            saveworld_success = False
            if hasattr(self, 'rcon_panel') and self.rcon_panel:
                try:
                    result = self.rcon_panel.execute_rcon_command("saveworld")
                    if result and not result.startswith("❌"):
                        saveworld_success = True
                        self.add_log_message("✅ Mundo guardado correctamente")
                    else:
                        self.add_log_message("⚠️ Error al ejecutar saveworld, continuando con detención...")
                except Exception as e:
                    self.add_log_message(f"⚠️ Error RCON saveworld: {e}")
            else:
                self.add_log_message("⚠️ RCON no disponible, continuando con detención...")
            
            # Esperar un momento y luego detener servidor
            self.root.after(2000, lambda: self._complete_server_stop())
            
        except Exception as e:
            self.logger.error(f"Error en saveworld: {e}")
            self.add_log_message(f"⚠️ Error en saveworld: {e}")
            # Continuar con detención aunque falle saveworld
            self._complete_server_stop()
    
    def _complete_server_stop(self):
        """Completar la detención del servidor"""
        try:
            if hasattr(self, 'server_panel'):
                self.server_panel.stop_server()
        except Exception as e:
            self.logger.error(f"Error al completar detención: {e}")
            self.add_log_message(f"❌ Error al detener servidor: {e}")
    
    def restart_server(self):
        """Reiniciar servidor con confirmación, saveworld y opción de actualizar"""
        try:
            # Confirmar acción
            if not ask_yes_no(self.root, "🔄 Confirmar Reinicio", 
                             "¿Estás seguro de que quieres REINICIAR el servidor?\n\n"
                             "• Se guardará el mundo automáticamente\n"
                             "• Los jugadores serán desconectados temporalmente\n"
                             "• El servidor se reiniciará completamente"):
                self.add_log_message("❌ Reinicio cancelado por el usuario")
                return
            
            # Preguntar si quiere actualizar
            update_server = ask_yes_no(self.root, "🔄 Actualizar Servidor", 
                                     "¿Quieres ACTUALIZAR el servidor antes de reiniciar?\n\n"
                                     "• ✅ SÍ: Descargará las últimas actualizaciones (recomendado)\n"
                                     "• ❌ NO: Solo reiniciará sin actualizar\n\n"
                                     "⚠️ La actualización puede tomar varios minutos")
            
            self.add_log_message("🔄 Iniciando reinicio del servidor...")
            if update_server:
                self.add_log_message("🔄 Reinicio CON actualización seleccionado")
            else:
                self.add_log_message("🔄 Reinicio SIN actualización seleccionado")
            
            # Ejecutar saveworld antes de reiniciar
            self.add_log_message("💾 Guardando mundo antes de reiniciar...")
            if hasattr(self, 'server_panel'):
                # Programar reinicio después del saveworld
                self.root.after(100, lambda: self._execute_restart_with_saveworld(update_server))
                
        except Exception as e:
            self.logger.error(f"Error al reiniciar servidor: {e}")
            show_error(self.root, "Error", f"Error al reiniciar servidor: {str(e)}")
    
    def _execute_restart_with_saveworld(self, update_server):
        """Ejecutar saveworld y luego reiniciar servidor"""
        try:
            self.add_log_message("💾 Ejecutando comando saveworld...")
            
            # Ejecutar saveworld via RCON
            saveworld_success = False
            if hasattr(self, 'rcon_panel') and self.rcon_panel:
                try:
                    result = self.rcon_panel.execute_rcon_command("saveworld")
                    if result and not result.startswith("❌"):
                        saveworld_success = True
                        self.add_log_message("✅ Mundo guardado correctamente")
                    else:
                        self.add_log_message("⚠️ Error al ejecutar saveworld, continuando con reinicio...")
                except Exception as e:
                    self.add_log_message(f"⚠️ Error RCON saveworld: {e}")
            else:
                self.add_log_message("⚠️ RCON no disponible, continuando con reinicio...")
            
            # Esperar un momento y luego reiniciar servidor
            self.root.after(2000, lambda: self._complete_server_restart(update_server))
            
        except Exception as e:
            self.logger.error(f"Error en saveworld: {e}")
            self.add_log_message(f"⚠️ Error en saveworld: {e}")
            # Continuar con reinicio aunque falle saveworld
            self._complete_server_restart(update_server)
    
    def _complete_server_restart(self, update_server):
        """Completar el reinicio del servidor"""
        try:
            if update_server:
                self.add_log_message("🔄 Iniciando reinicio con actualización...")
                self.add_log_message("📥 Descargando actualizaciones del servidor...")
                # Ejecutar actualización real
                if hasattr(self, 'server_panel'):
                    self.server_panel.update_server()
                self.root.after(3000, lambda: self._finalize_restart_with_update())
            else:
                self.add_log_message("🔄 Iniciando reinicio sin actualización...")
                if hasattr(self, 'server_panel'):
                    self.server_panel.restart_server()
                
        except Exception as e:
            self.logger.error(f"Error al completar reinicio: {e}")
            self.add_log_message(f"❌ Error al reiniciar servidor: {e}")
    
    def _finalize_restart_with_update(self):
        """Finalizar reinicio después de actualización"""
        try:
            self.add_log_message("✅ Actualización completada")
            if hasattr(self, 'server_panel'):
                self.server_panel.restart_server()
        except Exception as e:
            self.logger.error(f"Error al finalizar reinicio: {e}")
            self.add_log_message(f"❌ Error al reiniciar después de actualización: {e}")
    
    def install_server(self):
        """Instala un servidor"""
        if hasattr(self, 'server_panel'):
            self.server_panel.install_server()
    
    def update_server(self):
        """Actualiza un servidor"""
        if hasattr(self, 'server_panel'):
            self.server_panel.update_server()
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE HERRAMIENTAS
    # ═══════════════════════════════════════════════════════════════
    
    def verify_server_files(self):
        """Verificar integridad de archivos del servidor"""
        try:
            if not self.selected_server:
                show_warning("Sin servidor", "Por favor, selecciona un servidor primero.")
                return
            
            # Obtener ruta del servidor
            root_path = self.config_manager.get("server", "root_path", "")
            if not root_path:
                show_error("Error", "Ruta raíz no configurada.")
                return
            
            server_path = os.path.join(root_path, self.selected_server)
            if not os.path.exists(server_path):
                show_error("Error", f"Servidor no encontrado: {self.selected_server}")
                return
            
            # Iniciar verificación
            self.add_log_message("🔍 Iniciando verificación de archivos del servidor...")
            
            # Verificar archivos críticos
            critical_files = [
                "ArkAscendedServer.exe",
                "ShooterGame/Binaries/Win64/ArkAscendedServer.exe",
                "ShooterGame/Content/Paks/"
            ]
            
            missing_files = []
            for file_path in critical_files:
                full_path = os.path.join(server_path, file_path)
                if not os.path.exists(full_path):
                    missing_files.append(file_path)
            
            if missing_files:
                self.add_log_message(f"❌ Archivos faltantes encontrados: {len(missing_files)}")
                for missing in missing_files:
                    self.add_log_message(f"   📄 {missing}")
                show_warning("Archivos faltantes", f"Se encontraron {len(missing_files)} archivos faltantes. Considera actualizar el servidor.")
            else:
                self.add_log_message("✅ Verificación completada: Todos los archivos críticos están presentes")
                show_info("Verificación completada", "Todos los archivos críticos del servidor están presentes.")
                
        except Exception as e:
            self.logger.error(f"Error al verificar archivos: {e}")
            show_error("Error", f"Error al verificar archivos del servidor:\n{e}")
    
    def clean_old_logs(self):
        """Limpiar logs antiguos"""
        try:
            import datetime
            import glob
            
            if not ask_yes_no("Limpiar logs antiguos", "¿Estás seguro de que quieres eliminar logs antiguos (más de 7 días)?"):
                return
            
            self.add_log_message("🧹 Iniciando limpieza de logs antiguos...")
            
            # Obtener fecha límite (7 días)
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=7)
            
            # Carpetas de logs a limpiar
            log_paths = [
                "logs/*.log",
                "logs/server_events/*.log",
                "exports/*.txt"
            ]
            
            deleted_count = 0
            total_size = 0
            
            for pattern in log_paths:
                files = glob.glob(pattern)
                for file_path in files:
                    try:
                        # Verificar fecha del archivo
                        file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_time < cutoff_date:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_count += 1
                            total_size += file_size
                            self.add_log_message(f"🗑️ Eliminado: {file_path}")
                    except Exception as e:
                        self.logger.warning(f"Error al eliminar {file_path}: {e}")
            
            if deleted_count > 0:
                size_mb = total_size / (1024 * 1024)
                self.add_log_message(f"✅ Limpieza completada: {deleted_count} archivos eliminados ({size_mb:.2f} MB liberados)")
                show_info("Limpieza completada", f"Se eliminaron {deleted_count} archivos antiguos\nEspacio liberado: {size_mb:.2f} MB")
            else:
                self.add_log_message("ℹ️ No se encontraron logs antiguos para eliminar")
                show_info("Sin archivos", "No se encontraron logs antiguos para eliminar.")
                
        except Exception as e:
            self.logger.error(f"Error al limpiar logs: {e}")
            show_error("Error", f"Error al limpiar logs antiguos:\n{e}")
    
    def open_server_folder(self):
        """Abrir carpeta del servidor actual"""
        try:
            if not self.selected_server:
                show_warning("Sin servidor", "Por favor, selecciona un servidor primero.")
                return
            
            # Obtener ruta del servidor
            root_path = self.config_manager.get("server", "root_path", "")
            if not root_path:
                show_error("Error", "Ruta raíz no configurada.")
                return
            
            server_path = os.path.join(root_path, self.selected_server)
            if not os.path.exists(server_path):
                show_error("Error", f"Servidor no encontrado: {self.selected_server}")
                return
            
            # Abrir carpeta según el sistema operativo
            import platform
            import subprocess
            
            if platform.system() == "Windows":
                os.startfile(server_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", server_path])
            else:  # Linux y otros
                subprocess.run(["xdg-open", server_path])
            
            self.add_log_message(f"📁 Carpeta del servidor abierta: {server_path}")
            
        except Exception as e:
            self.logger.error(f"Error al abrir carpeta: {e}")
            show_error("Error", f"Error al abrir carpeta del servidor:\n{e}")
    
    def export_config(self):
        """Exportar configuración del servidor"""
        try:
            if not self.selected_server:
                show_warning("Sin servidor", "Por favor, selecciona un servidor primero.")
                return
            
            from tkinter import filedialog
            import json
            import shutil
            from datetime import datetime
            
            # Seleccionar carpeta de destino
            export_folder = filedialog.askdirectory(
                title="Seleccionar carpeta para exportar configuración",
                initialdir=os.path.expanduser("~/Desktop")
            )
            
            if not export_folder:
                return
            
            self.add_log_message("📦 Iniciando exportación de configuración...")
            
            # Crear carpeta de exportación con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            config_export_folder = os.path.join(export_folder, f"ARK_Config_{self.selected_server}_{timestamp}")
            os.makedirs(config_export_folder, exist_ok=True)
            
            # Obtener ruta del servidor
            root_path = self.config_manager.get("server", "root_path", "")
            server_path = os.path.join(root_path, self.selected_server)
            
            # Archivos y carpetas a exportar
            items_to_export = [
                ("ShooterGame/Saved/Config/WindowsServer/GameUserSettings.ini", "GameUserSettings.ini"),
                ("ShooterGame/Saved/Config/WindowsServer/Game.ini", "Game.ini"),
                ("ShooterGame/Saved/Config/WindowsServer/Engine.ini", "Engine.ini"),
                ("ShooterGame/Saved/SavedArks/", "SavedArks/"),
            ]
            
            exported_items = []
            
            for source_rel, dest_name in items_to_export:
                source_path = os.path.join(server_path, source_rel)
                dest_path = os.path.join(config_export_folder, dest_name)
                
                try:
                    if os.path.isfile(source_path):
                        shutil.copy2(source_path, dest_path)
                        exported_items.append(dest_name)
                        self.add_log_message(f"📄 Exportado: {dest_name}")
                    elif os.path.isdir(source_path):
                        shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                        exported_items.append(dest_name)
                        self.add_log_message(f"📁 Exportado: {dest_name}")
                except Exception as e:
                    self.add_log_message(f"⚠️ Error al exportar {dest_name}: {e}")
            
            # Crear archivo de información
            info_data = {
                "export_timestamp": timestamp,
                "server_name": self.selected_server,
                "exported_items": exported_items,
                "app_version": self.APP_VERSION
            }
            
            info_file = os.path.join(config_export_folder, "export_info.json")
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(info_data, f, indent=2, ensure_ascii=False)
            
            self.add_log_message(f"✅ Exportación completada: {len(exported_items)} elementos exportados")
            
            if ask_yes_no("Exportación completada", f"Configuración exportada exitosamente a:\n{config_export_folder}\n\n¿Quieres abrir la carpeta?"):
                if platform.system() == "Windows":
                    os.startfile(config_export_folder)
                    
        except Exception as e:
            self.logger.error(f"Error al exportar configuración: {e}")
            show_error("Error", f"Error al exportar configuración:\n{e}")
    
    def import_config(self):
        """Importar configuración del servidor"""
        try:
            if not self.selected_server:
                show_warning("Sin servidor", "Por favor, selecciona un servidor primero.")
                return
            
            from tkinter import filedialog
            import json
            import shutil
            
            # Advertencia
            if not ask_yes_no("Importar configuración", "⚠️ ADVERTENCIA: Esta operación sobrescribirá la configuración actual del servidor.\n\n¿Estás seguro de que quieres continuar?"):
                return
            
            # Seleccionar carpeta de configuración exportada
            import_folder = filedialog.askdirectory(
                title="Seleccionar carpeta de configuración a importar",
                initialdir=os.path.expanduser("~/Desktop")
            )
            
            if not import_folder:
                return
            
            # Verificar que es una exportación válida
            info_file = os.path.join(import_folder, "export_info.json")
            if not os.path.exists(info_file):
                show_error("Error", "La carpeta seleccionada no contiene una exportación válida.\nBusca una carpeta que contenga 'export_info.json'.")
                return
            
            self.add_log_message("📥 Iniciando importación de configuración...")
            
            # Leer información de la exportación
            with open(info_file, 'r', encoding='utf-8') as f:
                import_info = json.load(f)
            
            self.add_log_message(f"📋 Importando desde: {import_info.get('server_name', 'Desconocido')} ({import_info.get('export_timestamp', 'Fecha desconocida')})")
            
            # Obtener ruta del servidor actual
            root_path = self.config_manager.get("server", "root_path", "")
            server_path = os.path.join(root_path, self.selected_server)
            
            # Crear backup de la configuración actual
            backup_folder = os.path.join(server_path, "ConfigBackup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
            os.makedirs(backup_folder, exist_ok=True)
            
            # Archivos a importar
            files_to_import = [
                ("GameUserSettings.ini", "ShooterGame/Saved/Config/WindowsServer/GameUserSettings.ini"),
                ("Game.ini", "ShooterGame/Saved/Config/WindowsServer/Game.ini"),
                ("Engine.ini", "ShooterGame/Saved/Config/WindowsServer/Engine.ini"),
            ]
            
            imported_count = 0
            
            for source_name, dest_rel in files_to_import:
                source_path = os.path.join(import_folder, source_name)
                dest_path = os.path.join(server_path, dest_rel)
                backup_path = os.path.join(backup_folder, source_name)
                
                try:
                    if os.path.exists(source_path):
                        # Hacer backup del archivo actual
                        if os.path.exists(dest_path):
                            shutil.copy2(dest_path, backup_path)
                        
                        # Crear directorio de destino si no existe
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        
                        # Copiar nuevo archivo
                        shutil.copy2(source_path, dest_path)
                        imported_count += 1
                        self.add_log_message(f"📄 Importado: {source_name}")
                        
                except Exception as e:
                    self.add_log_message(f"⚠️ Error al importar {source_name}: {e}")
            
            if imported_count > 0:
                self.add_log_message(f"✅ Importación completada: {imported_count} archivos importados")
                self.add_log_message(f"💾 Backup guardado en: {backup_folder}")
                show_info("Importación completada", f"Se importaron {imported_count} archivos de configuración.\n\nBackup guardado en:\n{backup_folder}")
            else:
                show_warning("Sin archivos", "No se encontraron archivos válidos para importar.")
                
        except Exception as e:
            self.logger.error(f"Error al importar configuración: {e}")
            show_error("Error", f"Error al importar configuración:\n{e}")
    
    def update_steamcmd(self):
        """Actualizar SteamCMD"""
        try:
            if ask_yes_no("Actualizar SteamCMD", "¿Quieres actualizar SteamCMD a la última versión?\n\nEsto puede tomar unos minutos."):
                self.add_log_message("🔄 Iniciando actualización de SteamCMD...")
                
                # Usar el ServerManager para actualizar SteamCMD
                if hasattr(self, 'server_panel') and hasattr(self.server_panel, 'server_manager'):
                    # Crear un callback simple para mostrar progreso
                    def update_callback(msg_type, message):
                        if msg_type == "error":
                            self.add_log_message(f"❌ {message}")
                        elif msg_type == "success":
                            self.add_log_message(f"✅ {message}")
                        else:
                            self.add_log_message(f"ℹ️ {message}")
                    
                    # Ejecutar actualización en un hilo separado
                    import threading
                    
                    def run_update():
                        try:
                            # Simular descarga de SteamCMD (normalmente se haría con curl/wget)
                            self.add_log_message("📥 Descargando SteamCMD...")
                            import time
                            import requests
                            import zipfile
                            import tempfile
                            
                            # URL de SteamCMD
                            steamcmd_url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
                            
                            # Descargar a archivo temporal
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                                response = requests.get(steamcmd_url, stream=True)
                                response.raise_for_status()
                                
                                for chunk in response.iter_content(chunk_size=8192):
                                    temp_file.write(chunk)
                                
                                temp_path = temp_file.name
                            
                            self.add_log_message("📦 Extrayendo SteamCMD...")
                            
                            # Determinar carpeta de SteamCMD
                            root_path = self.config_manager.get("server", "root_path", "")
                            if root_path:
                                steamcmd_folder = os.path.join(root_path, "steamcmd")
                            else:
                                steamcmd_folder = "steamcmd"
                            
                            os.makedirs(steamcmd_folder, exist_ok=True)
                            
                            # Extraer archivo
                            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                                zip_ref.extractall(steamcmd_folder)
                            
                            # Limpiar archivo temporal
                            os.unlink(temp_path)
                            
                            self.root.after(0, lambda: self.add_log_message("✅ SteamCMD actualizado exitosamente"))
                            self.root.after(0, lambda: show_info("Actualización completada", "SteamCMD se ha actualizado exitosamente."))
                            
                        except Exception as e:
                            self.root.after(0, lambda: self.add_log_message(f"❌ Error al actualizar SteamCMD: {e}"))
                            self.root.after(0, lambda: show_error("Error", f"Error al actualizar SteamCMD:\n{e}"))
                    
                    # Ejecutar en hilo separado
                    update_thread = threading.Thread(target=run_update, daemon=True)
                    update_thread.start()
                    
                else:
                    show_error("Error", "No se pudo acceder al gestor de servidor.")
                    
        except Exception as e:
            self.logger.error(f"Error al actualizar SteamCMD: {e}")
            show_error("Error", f"Error al actualizar SteamCMD:\n{e}")
    
    def open_user_guide(self):
        """Abrir guía de usuario"""
        try:
            # Buscar archivo de guía local o abrir URL
            guide_files = ["README.md", "GUIA_USUARIO.md", "USER_GUIDE.md"]
            guide_found = False
            
            for guide_file in guide_files:
                if os.path.exists(guide_file):
                    if platform.system() == "Windows":
                        os.startfile(guide_file)
                    else:
                        import subprocess
                        subprocess.run(["xdg-open", guide_file])
                    guide_found = True
                    break
            
            if not guide_found:
                show_info("Guía de usuario", "La guía de usuario no está disponible localmente.\n\nConsulta el archivo README.md en el repositorio del proyecto.")
                
        except Exception as e:
            self.logger.error(f"Error al abrir guía: {e}")
            show_error("Error", f"Error al abrir guía de usuario:\n{e}")
    
    def report_bug(self):
        """Reportar un bug"""
        try:
            import webbrowser
            
            # Información del sistema para el reporte
            import platform
            system_info = f"""
Sistema: {platform.system()} {platform.release()}
Python: {platform.python_version()}
Versión de la app: {self.APP_VERSION}
"""
            
            # Copiar información al portapapeles si es posible
            try:
                import pyperclip
                pyperclip.copy(system_info.strip())
                clipboard_msg = "\n\n(Información del sistema copiada al portapapeles)"
            except:
                clipboard_msg = f"\n\nInformación del sistema:\n{system_info}"
            
            show_info("Reportar Bug", f"Para reportar un bug, por favor incluye la siguiente información:{clipboard_msg}\n\nDescribe el problema detalladamente y los pasos para reproducirlo.")
            
        except Exception as e:
            self.logger.error(f"Error al preparar reporte: {e}")
            show_error("Error", f"Error al preparar reporte de bug:\n{e}")
    
    def cleanup_tray_icons(self):
        """Limpiar iconos duplicados de la bandeja del sistema"""
        try:
            if hasattr(self, 'system_tray') and self.system_tray.is_available():
                if ask_yes_no("Limpiar iconos duplicados", "¿Quieres limpiar los iconos duplicados de la bandeja del sistema?\n\nEsto reiniciará el sistema de bandeja."):
                    self.add_log_message("🗑️ Limpiando iconos duplicados de la bandeja...")
                    
                    # Reiniciar el sistema de bandeja
                    if self.system_tray.restart_tray():
                        self.add_log_message("✅ Iconos de bandeja limpiados correctamente")
                        show_info("Limpieza completada", "Los iconos duplicados han sido eliminados de la bandeja del sistema.")
                    else:
                        self.add_log_message("❌ Error al limpiar iconos de bandeja")
                        show_error("Error", "No se pudieron limpiar los iconos duplicados.")
            else:
                show_warning("Sistema de bandeja no disponible", "El sistema de bandeja no está disponible o no está funcionando.")
                
        except Exception as e:
            self.logger.error(f"Error al limpiar iconos de bandeja: {e}")
            show_error("Error", f"Error al limpiar iconos duplicados:\n{e}")
    
    def auto_start_server(self):
        """Auto-iniciar el servidor al iniciar la aplicación"""
        try:
            self.logger.info("Iniciando auto-inicio del servidor...")
            
            # Verificar que tengamos servidor y mapa seleccionados
            if not self.selected_server:
                # Intentar cargar el último servidor usado
                last_server = self.config_manager.get("app", "last_server", "")
                if last_server:
                    self.selected_server = last_server
                    self.logger.info(f"Usando último servidor: {last_server}")
                else:
                    self.logger.warning("No hay servidor seleccionado para auto-inicio")
                    self.add_log_message("⚠️ Auto-inicio cancelado: No hay servidor seleccionado")
                    return
            
            if not self.selected_map:
                # Intentar cargar el último mapa usado
                last_map = self.config_manager.get("app", "last_map", "")
                if last_map:
                    self.selected_map = last_map
                    self.logger.info(f"Usando último mapa: {last_map}")
                else:
                    self.logger.warning("No hay mapa seleccionado para auto-inicio")
                    self.add_log_message("⚠️ Auto-inicio cancelado: No hay mapa seleccionado")
                    return
            
            # Verificar que el servidor no esté ya ejecutándose
            if hasattr(self, 'server_panel') and hasattr(self.server_panel, 'server_manager'):
                status = self.server_panel.server_manager.get_server_status()
                if status == "Ejecutándose":
                    self.logger.info("El servidor ya está ejecutándose, omitiendo auto-inicio")
                    self.add_log_message("ℹ️ Servidor ya está ejecutándose")
                    return
            
            # Iniciar el servidor
            self.add_log_message(f"🚀 Auto-iniciando servidor: {self.selected_server} con mapa: {self.selected_map}")
            
            if hasattr(self, 'principal_panel'):
                # Usar el método de inicio completo con configuraciones
                self.principal_panel.start_server_with_config()
                self.add_log_message("✅ Auto-inicio del servidor completado")
                
                # Notificar en la bandeja si está disponible
                if hasattr(self, 'system_tray') and self.system_tray.is_available():
                    self.system_tray.show_notification(
                        "ARK Server Manager",
                        f"Servidor '{self.selected_server}' iniciado automáticamente"
                    )
            else:
                self.logger.error("Panel principal no disponible para auto-inicio")
                self.add_log_message("❌ Error: Panel principal no disponible")
                
        except Exception as e:
            self.logger.error(f"Error en auto-inicio del servidor: {e}")
            self.add_log_message(f"❌ Error en auto-inicio: {e}")
            
            # Notificar error en la bandeja si está disponible
            if hasattr(self, 'system_tray') and self.system_tray.is_available():
                self.system_tray.show_notification(
                    "ARK Server Manager - Error",
                    "Error al auto-iniciar el servidor"
                )
    
    def check_auto_start_fallback(self):
        """Verificar auto-inicio cuando no hay bandeja del sistema"""
        try:
            # Solo hacer fallback si la bandeja no está disponible Y auto_start está activado
            should_auto_start = False
            
            if hasattr(self, 'started_with_windows') and self.started_with_windows:
                # Se inició con Windows - usar configuración específica
                should_auto_start = self.app_settings.get_setting("auto_start_server_with_windows")
            else:
                # Se inició manualmente - usar configuración normal
                should_auto_start = self.app_settings.get_setting("auto_start_server")
            
            if (not hasattr(self, 'system_tray') or 
                not self.system_tray.is_available()) and should_auto_start:
                
                self.logger.info("Bandeja no disponible, usando fallback para auto-inicio")
                # Programar auto-inicio con un retraso similar
                self.root.after(2000, self.auto_start_server_if_configured)
                
        except Exception as e:
            self.logger.error(f"Error en check_auto_start_fallback: {e}")
    
    def detect_startup_with_windows(self):
        """Detectar si la aplicación fue iniciada por Windows"""
        try:
            import sys
            import time
            import psutil
            
            # Criterio 1: Argumento --windows-startup (más confiable)
            if "--windows-startup" in sys.argv:
                self.logger.info("✅ Detección: argumento --windows-startup encontrado")
                return True
            
            # Criterio 2: Verificar proceso padre + tiempo de arranque
            try:
                current_process = psutil.Process()
                parent_process = current_process.parent()
                
                if parent_process:
                    parent_name = parent_process.name().lower()
                    self.logger.info(f"🔍 Proceso padre: {parent_name}")
                    
                    # Verificar si el proceso padre es del sistema Windows
                    system_processes = ['explorer.exe', 'winlogon.exe', 'userinit.exe']
                    is_system_parent = parent_name in system_processes
                    
                    # Verificar tiempo de arranque reciente (menos de 10 minutos)
                    boot_time = psutil.boot_time()
                    current_time = time.time()
                    uptime_minutes = (current_time - boot_time) / 60
                    recent_boot = uptime_minutes < 10
                    
                    self.logger.info(f"🔍 Proceso padre del sistema: {is_system_parent}")
                    self.logger.info(f"🔍 Arranque reciente ({uptime_minutes:.1f} min): {recent_boot}")
                    
                    # Ambos criterios deben cumplirse para detectar inicio con Windows
                    if is_system_parent and recent_boot:
                        self.logger.info("✅ Detección: inicio con Windows por proceso padre + arranque reciente")
                        return True
                
            except Exception as e:
                self.logger.warning(f"Error al verificar proceso padre: {e}")
            
            self.logger.info("❌ No se detectó inicio desde Windows")
            return False
            
        except Exception as e:
            self.logger.error(f"Error en detect_startup_with_windows: {e}")
            return False
    
    def load_last_configuration(self):
        """Cargar la última configuración de servidor y mapa"""
        try:
            self.logger.info("🔄 Cargando última configuración...")
            
            # Verificar configuraciones de auto-inicio
            auto_start_manual = self.app_settings.get_setting("auto_start_server")
            auto_start_windows = self.app_settings.get_setting("auto_start_server_with_windows")
            self.logger.info(f"📋 Auto-inicio manual: {auto_start_manual}")
            self.logger.info(f"🖥️ Auto-inicio con Windows: {auto_start_windows}")
            
            # Cargar último servidor
            last_server = self.config_manager.get("app", "last_server", "")
            if last_server:
                self.selected_server = last_server
                self.logger.info(f"🖥️ Último servidor cargado: {last_server}")
            else:
                self.logger.warning("⚠️ No hay servidor guardado en configuración")
            
            # Cargar último mapa
            last_map = self.config_manager.get("app", "last_map", "")
            if last_map:
                self.selected_map = last_map
                self.logger.info(f"🗺️ Último mapa cargado: {last_map}")
            else:
                self.logger.warning("⚠️ No hay mapa guardado en configuración")
            
            # Notificar a los paneles que se cargó la configuración
            if last_server and hasattr(self, 'server_panel'):
                # Programar actualización del panel después de que se inicialice completamente
                self.root.after(500, lambda: self.update_panels_with_config(last_server, last_map))
                
        except Exception as e:
            self.logger.error(f"❌ Error al cargar última configuración: {e}")
    
    def update_panels_with_config(self, server_name, map_name):
        """Actualizar paneles con la configuración cargada"""
        try:
            # Actualizar panel de servidor
            if hasattr(self, 'server_panel') and server_name:
                # Simular selección de servidor (esto debería actualizar las listas)
                if hasattr(self.server_panel, 'on_server_selected'):
                    self.server_panel.on_server_selected(server_name)
                
            # Actualizar panel principal con mapa
            if hasattr(self, 'principal_panel') and server_name and map_name:
                if hasattr(self.principal_panel, 'update_server_info'):
                    self.principal_panel.update_server_info(server_name, map_name)
                    
            self.logger.info(f"Paneles actualizados con servidor: {server_name}, mapa: {map_name}")
            
        except Exception as e:
            self.logger.error(f"Error al actualizar paneles: {e}")
    
    def auto_start_server_if_configured(self):
        """Auto-iniciar el servidor si está configurado para hacerlo"""
        try:
            # Verificar si ya hay un servidor ejecutándose
            if hasattr(self, 'server_manager') and self.server_manager.is_server_running():
                self.logger.info("El servidor ya está ejecutándose, omitiendo auto-inicio")
                self.add_log_message("ℹ️ Servidor ya está ejecutándose")
                return
            
            # Verificar si ConsolePanel ya está manejando el inicio del servidor
            if hasattr(self, 'console_panel_managing_startup') and self.console_panel_managing_startup:
                self.logger.info("ConsolePanel ya está manejando el inicio del servidor, omitiendo auto-inicio desde MainWindow")
                self.add_log_message("ℹ️ ConsolePanel ya está iniciando el servidor")
                return
            
            # Iniciar el servidor
            self.add_log_message(f"🚀 Auto-iniciando servidor: {self.selected_server} con mapa: {self.selected_map}")
            
            if hasattr(self, 'principal_panel'):
                # Usar el método de inicio completo con configuraciones
                self.principal_panel.start_server_with_config()
                self.add_log_message("✅ Auto-inicio del servidor completado")
                
                # Notificar en la bandeja si está disponible
                if hasattr(self, 'system_tray') and self.system_tray.is_available():
                    self.system_tray.show_notification(
                        "ARK Server Manager",
                        f"Servidor '{self.selected_server}' iniciado automáticamente"
                    )
            else:
                self.logger.error("Panel principal no disponible para auto-inicio")
                self.add_log_message("❌ Error: Panel principal no disponible")
                
        except Exception as e:
            self.logger.error(f"Error en auto-inicio del servidor: {e}")
            self.add_log_message(f"❌ Error en auto-inicio: {e}")
            
            # Notificar error en la bandeja si está disponible
            if hasattr(self, 'system_tray') and self.system_tray.is_available():
                self.system_tray.show_notification(
                    "ARK Server Manager - Error",
                    "Error al auto-iniciar el servidor"
                )
    
    def detect_startup_with_windows(self):
        """Detectar si la aplicación se inició automáticamente con Windows"""
        try:
            import sys
            import psutil
            import time
            
            # Método 1: Verificar argumentos de línea de comandos (más rápido y confiable)
            if len(sys.argv) > 1:
                for arg in sys.argv[1:]:
                    if arg.lower() in ['--startup', '--autostart', '--windows-startup']:
                        # Solo log importante: detectado exitosamente
                        self.logger.info("Auto-iniciando servidor desde Windows")
                        return True
            
            # Método 2: Verificar proceso padre (solo si es necesario)
            try:
                current_process = psutil.Process()
                parent_process = current_process.parent()
                
                if not parent_process:
                    return False
                
                parent_name = parent_process.name().lower()
                
                if parent_name in ['explorer.exe', 'winlogon.exe']:
                    # Verificar tiempo de arranque (simplificado)
                    boot_time = psutil.boot_time()
                    process_start_time = current_process.create_time()
                    time_since_boot = process_start_time - boot_time
                    
                    # Si el proceso se creó dentro de los primeros 2 minutos del inicio
                    if time_since_boot < 120:  # 120 segundos = 2 minutos
                        self.logger.info("Auto-iniciando servidor desde Windows")
                        return True
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Error silencioso para no ralentizar el inicio
                pass
            
            # Método 3: Verificar tiempo de arranque del sistema (simplificado)
            try:
                boot_time = psutil.boot_time()
                current_time = time.time()
                time_since_boot = current_time - boot_time
                
                # Si el sistema arrancó hace menos de 5 minutos
                if time_since_boot < 300:  # 300 segundos = 5 minutos
                    self.logger.info("Auto-iniciando servidor desde Windows")
                    return True
                    
            except Exception:
                # Error silencioso para no ralentizar
                pass
            
            # Por defecto: inicio manual (sin log para ser más rápido)
            return False
            
        except Exception as e:
            # Solo registrar errores críticos
            self.logger.error(f"Error crítico en detección de inicio: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # CONFIGURACIÓN DE EVENTOS Y BANDEJA DEL SISTEMA
    # ═══════════════════════════════════════════════════════════════
    
    def setup_button_callbacks(self):
        """Configurar callbacks de botones"""
        # Este método puede expandirse en el futuro para callbacks específicos
        pass
    
    def setup_window_events(self):
        """Configurar eventos de la ventana principal"""
        try:
            # Configurar el protocolo de cierre de ventana
            self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
            
            # Configurar eventos de minimización/iconificación
            self.root.bind('<Unmap>', self.on_window_unmap)
            self.root.bind('<Map>', self.on_window_map)
            
            self.logger.info("Eventos de ventana configurados correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al configurar eventos de ventana: {e}")
    
    def start_system_tray(self):
        """Inicializar el sistema de bandeja"""
        try:
            # Verificar si ya se inicializó
            if hasattr(self, '_tray_initialized') and self._tray_initialized:
                self.logger.info("Sistema de bandeja ya está inicializado")
                return
            
            if hasattr(self, 'system_tray') and self.system_tray.is_available():
                # Iniciar la bandeja del sistema
                if self.system_tray.start_tray():
                    self._tray_initialized = True
                    self.logger.info("Sistema de bandeja iniciado correctamente")
                    
                    # Verificar configuraciones de inicio
                    if self.app_settings.get_setting("start_minimized"):
                        self.root.after(1000, self.minimize_to_tray)  # Esperar 1 segundo antes de minimizar
                    
                    # Verificar si debe auto-iniciar el servidor
                    should_auto_start = False
                    
                    if hasattr(self, 'started_with_windows') and self.started_with_windows:
                        # Se inició con Windows - usar configuración específica
                        should_auto_start = self.app_settings.get_setting("auto_start_server_with_windows")
                        if should_auto_start:
                            self.logger.info("✅ Auto-inicio activado: iniciado con Windows")
                    else:
                        # Se inició manualmente - usar configuración normal
                        should_auto_start = self.app_settings.get_setting("auto_start_server")
                        if should_auto_start:
                            self.logger.info("✅ Auto-inicio activado: iniciado manualmente")
                    
                    if should_auto_start:
                        self.root.after(2000, self.auto_start_server_if_configured)  # Esperar 2 segundos para que se cargue todo
                else:
                    self.logger.warning("No se pudo iniciar el sistema de bandeja")
            else:
                self.logger.warning("Sistema de bandeja no disponible")
                
        except Exception as e:
            self.logger.error(f"Error al inicializar sistema de bandeja: {e}")
    
    def on_window_close(self):
        """Manejar el cierre de la ventana"""
        try:
            # Verificar configuración de minimizar a bandeja al cerrar
            if (hasattr(self, 'app_settings') and 
                self.app_settings.get_setting("close_to_tray") and 
                hasattr(self, 'system_tray') and 
                self.system_tray.is_available()):
                
                # Minimizar a bandeja en lugar de cerrar
                self.minimize_to_tray()
            else:
                # Cerrar normalmente
                self.salir_aplicacion()
                
        except Exception as e:
            self.logger.error(f"Error al manejar cierre de ventana: {e}")
            # En caso de error, cerrar normalmente
            self.salir_aplicacion()
    
    def on_window_unmap(self, event):
        """Manejar cuando la ventana se minimiza o oculta"""
        try:
            # Solo actuar si el evento es de la ventana principal
            if event.widget == self.root:
                # Verificar si debe minimizar a bandeja
                if (hasattr(self, 'app_settings') and 
                    self.app_settings.get_setting("minimize_to_tray") and 
                    hasattr(self, 'system_tray') and 
                    self.system_tray.is_available() and
                    not self.system_tray.is_hidden):
                    
                    # Solo minimizar a bandeja si la ventana está minimizada, no oculta
                    if self.root.state() == 'iconic':
                        self.root.after(100, self.minimize_to_tray)
                        
        except Exception as e:
            self.logger.error(f"Error en on_window_unmap: {e}")
    
    def on_window_map(self, event):
        """Manejar cuando la ventana se restaura"""
        try:
            # Solo actuar si el evento es de la ventana principal
            if event.widget == self.root:
                if hasattr(self, 'system_tray'):
                    self.system_tray.is_hidden = False
                    
        except Exception as e:
            self.logger.error(f"Error en on_window_map: {e}")
    
    def minimize_to_tray(self):
        """Minimizar la aplicación a la bandeja del sistema"""
        try:
            if (hasattr(self, 'system_tray') and 
                self.system_tray.is_available() and 
                self.system_tray.tray_icon):
                
                self.system_tray.hide_to_tray()
                self.logger.info("Aplicación minimizada a la bandeja del sistema")
            else:
                self.logger.warning("Sistema de bandeja no disponible para minimizar")
                
        except Exception as e:
            self.logger.error(f"Error al minimizar a bandeja: {e}")
    
    def restore_from_tray(self):
        """Restaurar la aplicación desde la bandeja del sistema"""
        try:
            if hasattr(self, 'system_tray'):
                self.system_tray.show_window()
                self.logger.info("Aplicación restaurada desde la bandeja del sistema")
                
        except Exception as e:
            self.logger.error(f"Error al restaurar desde bandeja: {e}")
    
    def salir_aplicacion(self):
        """Salir completamente de la aplicación"""
        try:
            self.logger.info("Cerrando aplicación...")
            
            # Detener bandeja del sistema
            if hasattr(self, 'system_tray'):
                self.system_tray.stop_tray()
                self.logger.info("Bandeja del sistema detenida")
            
            # Guardar configuraciones
            if hasattr(self, 'config_manager'):
                self.config_manager.save()
                
            # Cerrar ventana principal
            self.root.quit()
            self.root.destroy()
            
        except Exception as e:
            self.logger.error(f"Error al cerrar aplicación: {e}")
            # Forzar cierre
            import sys
            sys.exit(0)
