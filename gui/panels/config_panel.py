import customtkinter as ctk
import os
from tkinter import filedialog

class ConfigPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        
        self.create_widgets()
        self.load_config()
        
    def create_widgets(self):
        """Crear todos los widgets del panel"""
        # Título
        title_label = ctk.CTkLabel(
            self, 
            text="Configuración del Servidor", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(20, 10))
        
        # Frame destacado para la ruta raíz actual
        current_path_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"))
        current_path_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")
        
        current_path_label = ctk.CTkLabel(
            current_path_frame,
            text="📍 Ruta Raíz Actual:",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("blue", "lightblue")
        )
        current_path_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        self.current_path_display = ctk.CTkLabel(
            current_path_frame,
            text="No configurada",
            font=ctk.CTkFont(size=14),
            text_color=("red", "orange")
        )
        self.current_path_display.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")
        
        change_path_button = ctk.CTkButton(
            current_path_frame,
            text="Cambiar Ruta",
            command=self.browse_root_path,
            fg_color=("blue", "darkblue"),
            hover_color=("darkblue", "navy"),
            width=120
        )
        change_path_button.grid(row=2, column=0, padx=15, pady=(0, 10), sticky="w")
        
        # Frame de configuración del servidor
        server_config_frame = ctk.CTkFrame(self)
        server_config_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        server_config_label = ctk.CTkLabel(
            server_config_frame, 
            text="Configuración del Servidor", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        server_config_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Ruta del ejecutable del servidor
        server_path_label = ctk.CTkLabel(server_config_frame, text="Ruta del servidor:")
        server_path_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.server_path_entry = ctk.CTkEntry(server_config_frame, width=300)
        self.server_path_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        browse_button = ctk.CTkButton(
            server_config_frame,
            text="Buscar",
            command=self.browse_server_path,
            width=80
        )
        browse_button.grid(row=1, column=2, padx=5, pady=5)
        
        # Puerto del servidor
        port_label = ctk.CTkLabel(server_config_frame, text="Puerto:")
        port_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.port_entry = ctk.CTkEntry(server_config_frame, placeholder_text="7777")
        self.port_entry.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        
        # Máximo de jugadores
        max_players_label = ctk.CTkLabel(server_config_frame, text="Máximo de jugadores:")
        max_players_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        
        self.max_players_entry = ctk.CTkEntry(server_config_frame, placeholder_text="70")
        self.max_players_entry.grid(row=3, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        
        # Nombre del servidor
        server_name_label = ctk.CTkLabel(server_config_frame, text="Nombre del servidor:")
        server_name_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        
        self.server_name_entry = ctk.CTkEntry(server_config_frame, placeholder_text="Mi Servidor Ark")
        self.server_name_entry.grid(row=4, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        
        # Frame de configuración de juego
        game_config_frame = ctk.CTkFrame(self)
        game_config_frame.grid(row=2, column=1, padx=20, pady=10, sticky="nsew")
        
        game_config_label = ctk.CTkLabel(
            game_config_frame, 
            text="Configuración de Juego", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        game_config_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Multiplicador de experiencia
        xp_multiplier_label = ctk.CTkLabel(game_config_frame, text="Multiplicador XP:")
        xp_multiplier_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.xp_multiplier_entry = ctk.CTkEntry(game_config_frame, placeholder_text="1.0")
        self.xp_multiplier_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Multiplicador de cosecha
        harvest_multiplier_label = ctk.CTkLabel(game_config_frame, text="Multiplicador cosecha:")
        harvest_multiplier_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.harvest_multiplier_entry = ctk.CTkEntry(game_config_frame, placeholder_text="1.0")
        self.harvest_multiplier_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # Multiplicador de taming
        taming_multiplier_label = ctk.CTkLabel(game_config_frame, text="Multiplicador taming:")
        taming_multiplier_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        
        self.taming_multiplier_entry = ctk.CTkEntry(game_config_frame, placeholder_text="1.0")
        self.taming_multiplier_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        # Velocidad de día/noche
        day_night_speed_label = ctk.CTkLabel(game_config_frame, text="Velocidad día/noche:")
        day_night_speed_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        
        self.day_night_speed_entry = ctk.CTkEntry(game_config_frame, placeholder_text="1.0")
        self.day_night_speed_entry.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        
        # Frame de configuración avanzada
        advanced_config_frame = ctk.CTkFrame(self)
        advanced_config_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        advanced_config_label = ctk.CTkLabel(
            advanced_config_frame, 
            text="Configuración Avanzada", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        advanced_config_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Ruta de datos del servidor
        data_path_label = ctk.CTkLabel(advanced_config_frame, text="Ruta de datos:")
        data_path_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.data_path_entry = ctk.CTkEntry(advanced_config_frame, width=300)
        self.data_path_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        data_browse_button = ctk.CTkButton(
            advanced_config_frame,
            text="Buscar",
            command=self.browse_data_path,
            width=80
        )
        data_browse_button.grid(row=1, column=2, padx=5, pady=5)
        
        # Ruta de logs
        logs_path_label = ctk.CTkLabel(advanced_config_frame, text="Ruta de logs:")
        logs_path_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.logs_path_entry = ctk.CTkEntry(advanced_config_frame, width=300)
        self.logs_path_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        logs_browse_button = ctk.CTkButton(
            advanced_config_frame,
            text="Buscar",
            command=self.browse_logs_path,
            width=80
        )
        logs_browse_button.grid(row=2, column=2, padx=5, pady=5)
        
        # Parámetros adicionales
        additional_params_label = ctk.CTkLabel(advanced_config_frame, text="Parámetros adicionales:")
        additional_params_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        
        self.additional_params_text = ctk.CTkTextbox(advanced_config_frame, height=100)
        self.additional_params_text.grid(row=3, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        
        # Frame de botones
        buttons_frame = ctk.CTkFrame(self)
        buttons_frame.grid(row=4, column=0, columnspan=2, padx=20, pady=20, sticky="ew")
        
        # Botones de acción
        save_button = ctk.CTkButton(
            buttons_frame,
            text="Guardar Configuración",
            command=self.save_config,
            fg_color="green",
            hover_color="darkgreen"
        )
        save_button.grid(row=0, column=0, padx=10, pady=10)
        
        load_button = ctk.CTkButton(
            buttons_frame,
            text="Cargar Configuración",
            command=self.load_config
        )
        load_button.grid(row=0, column=1, padx=10, pady=10)
        
        reset_button = ctk.CTkButton(
            buttons_frame,
            text="Restablecer",
            command=self.reset_config,
            fg_color="orange",
            hover_color="darkorange"
        )
        reset_button.grid(row=0, column=2, padx=10, pady=10)
        
        # Configurar grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        current_path_frame.grid_columnconfigure(0, weight=1)
        server_config_frame.grid_columnconfigure(1, weight=1)
        game_config_frame.grid_columnconfigure(1, weight=1)
        advanced_config_frame.grid_columnconfigure(1, weight=1)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        buttons_frame.grid_columnconfigure(2, weight=1)
        
        # Campo oculto para mantener la ruta raíz
        self.root_path_entry = ctk.CTkEntry(self)
        self.root_path_entry.grid_remove()  # Oculto pero funcional
        
    def browse_root_path(self):
        """Buscar directorio raíz para servidores"""
        directory = filedialog.askdirectory(title="Seleccionar ruta raíz para servidores")
        if directory:
            self.root_path_entry.delete(0, "end")
            self.root_path_entry.insert(0, directory)
            self.update_current_path_display()
        
    def update_current_path_display(self):
        """Actualizar la visualización de la ruta actual"""
        current_path = self.root_path_entry.get().strip()
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
        
    def browse_server_path(self):
        """Buscar archivo ejecutable del servidor"""
        filename = filedialog.askopenfilename(
            title="Seleccionar ejecutable del servidor",
            filetypes=[("Executables", "*.exe"), ("All files", "*.*")]
        )
        if filename:
            self.server_path_entry.delete(0, "end")
            self.server_path_entry.insert(0, filename)
    
    def browse_data_path(self):
        """Buscar directorio de datos"""
        directory = filedialog.askdirectory(title="Seleccionar directorio de datos")
        if directory:
            self.data_path_entry.delete(0, "end")
            self.data_path_entry.insert(0, directory)
    
    def browse_logs_path(self):
        """Buscar directorio de logs"""
        directory = filedialog.askdirectory(title="Seleccionar directorio de logs")
        if directory:
            self.logs_path_entry.delete(0, "end")
            self.logs_path_entry.insert(0, directory)
    
    def save_config(self):
        """Guardar configuración"""
        try:
            # Guardar configuración del servidor
            self.config_manager.set("server", "root_path", self.root_path_entry.get())
            self.config_manager.set("server", "executable_path", self.server_path_entry.get())
            self.config_manager.set("server", "port", self.port_entry.get())
            self.config_manager.set("server", "max_players", self.max_players_entry.get())
            self.config_manager.set("server", "server_name", self.server_name_entry.get())
            
            # Guardar configuración de juego
            self.config_manager.set("game", "xp_multiplier", self.xp_multiplier_entry.get())
            self.config_manager.set("game", "harvest_multiplier", self.harvest_multiplier_entry.get())
            self.config_manager.set("game", "taming_multiplier", self.taming_multiplier_entry.get())
            self.config_manager.set("game", "day_night_speed", self.day_night_speed_entry.get())
            
            # Guardar configuración avanzada
            self.config_manager.set("advanced", "data_path", self.data_path_entry.get())
            self.config_manager.set("advanced", "logs_path", self.logs_path_entry.get())
            self.config_manager.set("advanced", "additional_params", self.additional_params_text.get("1.0", "end-1c"))
            
            self.config_manager.save()
            self.update_current_path_display()
            self.logger.info("Configuración guardada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al guardar configuración: {e}")
    
    def load_config(self):
        """Cargar configuración"""
        try:
            # Cargar configuración del servidor
            self.root_path_entry.delete(0, "end")
            self.root_path_entry.insert(0, self.config_manager.get("server", "root_path", ""))
            self.update_current_path_display()
            
            self.server_path_entry.delete(0, "end")
            self.server_path_entry.insert(0, self.config_manager.get("server", "executable_path", ""))
            
            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, self.config_manager.get("server", "port", "7777"))
            
            self.max_players_entry.delete(0, "end")
            self.max_players_entry.insert(0, self.config_manager.get("server", "max_players", "70"))
            
            self.server_name_entry.delete(0, "end")
            self.server_name_entry.insert(0, self.config_manager.get("server", "server_name", "Mi Servidor Ark"))
            
            # Cargar configuración de juego
            self.xp_multiplier_entry.delete(0, "end")
            self.xp_multiplier_entry.insert(0, self.config_manager.get("game", "xp_multiplier", "1.0"))
            
            self.harvest_multiplier_entry.delete(0, "end")
            self.harvest_multiplier_entry.insert(0, self.config_manager.get("game", "harvest_multiplier", "1.0"))
            
            self.taming_multiplier_entry.delete(0, "end")
            self.taming_multiplier_entry.insert(0, self.config_manager.get("game", "taming_multiplier", "1.0"))
            
            self.day_night_speed_entry.delete(0, "end")
            self.day_night_speed_entry.insert(0, self.config_manager.get("game", "day_night_speed", "1.0"))
            
            # Cargar configuración avanzada
            self.data_path_entry.delete(0, "end")
            self.data_path_entry.insert(0, self.config_manager.get("advanced", "data_path", ""))
            
            self.logs_path_entry.delete(0, "end")
            self.logs_path_entry.insert(0, self.config_manager.get("advanced", "logs_path", ""))
            
            self.additional_params_text.delete("1.0", "end")
            self.additional_params_text.insert("1.0", self.config_manager.get("advanced", "additional_params", ""))
            
            self.logger.info("Configuración cargada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al cargar configuración: {e}")
    
    def reset_config(self):
        """Restablecer configuración por defecto"""
        try:
            # Limpiar todos los campos
            self.root_path_entry.delete(0, "end")
            self.update_current_path_display()
            
            self.server_path_entry.delete(0, "end")
            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, "7777")
            self.max_players_entry.delete(0, "end")
            self.max_players_entry.insert(0, "70")
            self.server_name_entry.delete(0, "end")
            self.server_name_entry.insert(0, "Mi Servidor Ark")
            
            self.xp_multiplier_entry.delete(0, "end")
            self.xp_multiplier_entry.insert(0, "1.0")
            self.harvest_multiplier_entry.delete(0, "end")
            self.harvest_multiplier_entry.insert(0, "1.0")
            self.taming_multiplier_entry.delete(0, "end")
            self.taming_multiplier_entry.insert(0, "1.0")
            self.day_night_speed_entry.delete(0, "end")
            self.day_night_speed_entry.insert(0, "1.0")
            
            self.data_path_entry.delete(0, "end")
            self.logs_path_entry.delete(0, "end")
            self.additional_params_text.delete("1.0", "end")
            
            self.logger.info("Configuración restablecida")
            
        except Exception as e:
            self.logger.error(f"Error al restablecer configuración: {e}")
