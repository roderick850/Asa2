import customtkinter as ctk
import os
import threading
import requests
import configparser
from datetime import datetime

class PrincipalPanel:
    def __init__(self, parent, config_manager, logger, main_window=None):
        self.parent = parent
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        self.server_manager = None
        
        # Inicializar server_manager si está disponible
        try:
            from utils.server_manager import ServerManager
            self.server_manager = ServerManager(config_manager, logger)
        except ImportError:
            self.logger.warning("ServerManager no disponible")
        
        # Variables para el servidor seleccionado
        self.selected_server = None
        self.selected_map = None
        
        # Crear widgets
        self.create_widgets()
        
        # Cargar configuración guardada
        self.load_saved_config()
    
    def create_widgets(self):
        """Crear todos los widgets de la pestaña principal"""
        # Frame principal con scroll
        main_frame = ctk.CTkScrollableFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Título principal
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Configuración Principal del Servidor", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Frame para parámetros básicos
        basic_frame = ctk.CTkFrame(main_frame)
        basic_frame.pack(fill="x", padx=5, pady=5)
        
        # Título de parámetros básicos
        ctk.CTkLabel(
            basic_frame, 
            text="Parámetros Básicos", 
            font=("Arial", 13, "bold")
        ).pack(pady=5)
        
        # Crear layout en múltiples columnas
        columns_frame = ctk.CTkFrame(basic_frame, fg_color="transparent")
        columns_frame.pack(fill="x", padx=5, pady=5)
        
        # Configurar columnas (3 columnas)
        columns_frame.grid_columnconfigure(0, weight=1)
        columns_frame.grid_columnconfigure(1, weight=1)
        columns_frame.grid_columnconfigure(2, weight=1)
        
        # Primera columna
        col1_frame = ctk.CTkFrame(columns_frame, fg_color="transparent")
        col1_frame.grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        
        # SessionName
        ctk.CTkLabel(col1_frame, text="SessionName:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.session_name_entry = ctk.CTkEntry(col1_frame, placeholder_text="Nombre del servidor", width=200, height=28)
        self.session_name_entry.pack(fill="x", pady=(0, 6))
        
        # MaxPlayers
        ctk.CTkLabel(col1_frame, text="MaxPlayers:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.max_players_entry = ctk.CTkEntry(col1_frame, placeholder_text="70", width=200, height=28)
        self.max_players_entry.pack(fill="x", pady=(0, 6))
        
        # QueryPort
        ctk.CTkLabel(col1_frame, text="QueryPort:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.query_port_entry = ctk.CTkEntry(col1_frame, placeholder_text="27015", width=200, height=28)
        self.query_port_entry.pack(fill="x", pady=(0, 6))
        
        # Segunda columna
        col2_frame = ctk.CTkFrame(columns_frame, fg_color="transparent")
        col2_frame.grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        
        # ServerPassword
        ctk.CTkLabel(col2_frame, text="ServerPassword:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.server_password_entry = ctk.CTkEntry(col2_frame, placeholder_text="Contraseña del servidor", show="*", width=200, height=28)
        self.server_password_entry.pack(fill="x", pady=(0, 6))
        
        # Port
        ctk.CTkLabel(col2_frame, text="Port:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.port_entry = ctk.CTkEntry(col2_frame, placeholder_text="7777", width=200, height=28)
        self.port_entry.pack(fill="x", pady=(0, 6))
        
        # MultiHome
        multihome_label_frame = ctk.CTkFrame(col2_frame, fg_color="transparent")
        multihome_label_frame.pack(fill="x", pady=(0, 2))
        
        ctk.CTkLabel(multihome_label_frame, text="MultiHome:", font=("Arial", 11, "bold")).pack(side="left")
        
        self.ip_auto_button = ctk.CTkButton(
            multihome_label_frame,
            text="🌐 IP Pública",
            command=self.get_public_ip,
            width=80,
            height=20,
            font=("Arial", 9)
        )
        self.ip_auto_button.pack(side="right")
        
        self.multihome_entry = ctk.CTkEntry(col2_frame, placeholder_text="127.0.0.1", width=200, height=28)
        self.multihome_entry.pack(fill="x", pady=(0, 6))
        
        # Tercera columna
        col3_frame = ctk.CTkFrame(columns_frame, fg_color="transparent")
        col3_frame.grid(row=0, column=2, padx=3, pady=3, sticky="ew")
        
        # AdminPassword
        ctk.CTkLabel(col3_frame, text="AdminPassword:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.admin_password_entry = ctk.CTkEntry(col3_frame, placeholder_text="Contraseña de admin", show="*", width=200, height=28)
        self.admin_password_entry.pack(fill="x", pady=(0, 6))
        
        # Frame para argumentos personalizados
        custom_frame = ctk.CTkFrame(main_frame)
        custom_frame.pack(fill="x", padx=5, pady=5)
        
        # Título de argumentos personalizados
        ctk.CTkLabel(
            custom_frame, 
            text="Argumentos de Inicio Personalizados", 
            font=("Arial", 13, "bold")
        ).pack(pady=5)
        
        # Descripción
        ctk.CTkLabel(
            custom_frame, 
            text="Agregue argumentos adicionales para el servidor (uno por línea):",
            font=("Arial", 10)
        ).pack(pady=(0, 5))
        
        # Texto para argumentos personalizados
        self.custom_args_text = ctk.CTkTextbox(custom_frame, height=80)
        self.custom_args_text.pack(fill="x", padx=5, pady=5)
        
        # Frame para botones de acción
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", padx=5, pady=8)
        
        # Botones
        ctk.CTkButton(
            buttons_frame,
            text="Guardar Configuración",
            command=self.save_configuration,
            fg_color="green",
            hover_color="darkgreen",
            height=30
        ).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="Cargar Configuración",
            command=self.load_configuration,
            fg_color="blue",
            hover_color="darkblue",
            height=30
        ).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="Ver Argumentos",
            command=self.preview_arguments,
            fg_color="orange",
            hover_color="darkorange",
            height=30
        ).pack(side="left", padx=5, pady=5)
    
    def load_saved_config(self):
        """Cargar configuración guardada"""
        try:
            # Cargar valores guardados
            self.session_name_entry.insert(0, self.config_manager.get("server", "session_name", ""))
            self.server_password_entry.insert(0, self.config_manager.get("server", "server_password", ""))
            self.admin_password_entry.insert(0, self.config_manager.get("server", "admin_password", ""))
            self.max_players_entry.insert(0, self.config_manager.get("server", "max_players", "70"))
            self.query_port_entry.insert(0, self.config_manager.get("server", "query_port", "27015"))
            self.port_entry.insert(0, self.config_manager.get("server", "port", "7777"))
            self.multihome_entry.insert(0, self.config_manager.get("server", "multihome", "127.0.0.1"))
            
            # Cargar argumentos personalizados
            custom_args = self.config_manager.get("server", "custom_args", "")
            if custom_args:
                self.custom_args_text.insert("1.0", custom_args)
                
        except Exception as e:
            self.logger.error(f"Error al cargar configuración: {e}")
    
    def save_configuration(self):
        """Guardar la configuración actual"""
        try:
            # Guardar parámetros básicos
            self.config_manager.set("server", "session_name", self.session_name_entry.get())
            self.config_manager.set("server", "server_password", self.server_password_entry.get())
            self.config_manager.set("server", "admin_password", self.admin_password_entry.get())
            self.config_manager.set("server", "max_players", self.max_players_entry.get())
            self.config_manager.set("server", "query_port", self.query_port_entry.get())
            self.config_manager.set("server", "port", self.port_entry.get())
            self.config_manager.set("server", "multihome", self.multihome_entry.get())
            
            # Guardar argumentos personalizados
            custom_args = self.custom_args_text.get("1.0", "end-1c")
            self.config_manager.set("server", "custom_args", custom_args)
            
            # Guardar en archivo
            self.config_manager.save()
            
            # Guardar en GameUserSettings.ini
            self.save_to_gameusersettings()
            
            # Notificar al panel RCON para actualizar password
            if hasattr(self.main_window, 'rcon_panel'):
                self.main_window.rcon_panel.refresh_password_from_config()
            
            # Mostrar mensaje de éxito
            self.show_message("✅ Configuración guardada correctamente", "success")
            
        except Exception as e:
            self.logger.error(f"Error al guardar configuración: {e}")
            self.show_message(f"❌ Error al guardar: {str(e)}", "error")
    
    def save_to_gameusersettings(self):
        """Guardar ServerPassword, AdminPassword y SessionName en GameUserSettings.ini PRESERVANDO CONTENIDO EXISTENTE"""
        try:
            # Obtener servidor actual desde main_window si está disponible
            if not self.main_window or not hasattr(self.main_window, 'selected_server'):
                return
            
            selected_server = self.main_window.selected_server
            if not selected_server:
                return
            
            # Construir ruta al archivo GameUserSettings.ini
            server_path = self.config_manager.get("server", "root_path", "")
            if not server_path:
                return
            
            gameusersettings_path = os.path.join(
                server_path, 
                selected_server, 
                "ShooterGame", 
                "Saved", 
                "Config", 
                "WindowsServer", 
                "GameUserSettings.ini"
            )
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(gameusersettings_path), exist_ok=True)
            
            # Obtener valores a guardar
            server_password = self.server_password_entry.get()
            admin_password = self.admin_password_entry.get()
            session_name = self.session_name_entry.get()
            max_players = self.max_players_entry.get()
            
            # Usar método personalizado para preservar el archivo existente
            self._update_ini_file_preserving_content(
                gameusersettings_path,
                {
                    'ServerSettings': {
                        'ServerPassword': server_password if server_password else None,
                        'ServerAdminPassword': admin_password if admin_password else None
                    },
                    'SessionSettings': {
                        'SessionName': session_name if session_name else None
                    },
                    '/Script/Engine.GameSession': {
                        'MaxPlayers': max_players if max_players else None
                    }
                }
            )
            
            if self.logger:
                self.logger.info(f"✅ Configuración guardada preservando contenido en GameUserSettings.ini: {gameusersettings_path}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al guardar en GameUserSettings.ini: {e}")
            print(f"Error al guardar en GameUserSettings.ini: {e}")
    
    def _update_ini_file_preserving_content(self, file_path, sections_to_update):
        """Actualizar archivo INI preservando contenido existente y agregando secciones si no existen"""
        lines = []
        current_section = None
        sections_found = set()
        
        # Leer archivo existente línea por línea si existe
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # Procesar líneas existentes
        updated_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].rstrip('\n\r')
            original_line = line
            
            # Detectar secciones
            if line.strip().startswith('[') and line.strip().endswith(']'):
                current_section = line.strip()[1:-1]
                sections_found.add(current_section)
                updated_lines.append(original_line + '\n')
                i += 1
                continue
            
            # Si estamos en una sección que queremos actualizar
            if current_section in sections_to_update:
                section_data = sections_to_update[current_section]
                
                # Buscar si esta línea contiene una clave que queremos actualizar
                if '=' in line:
                    key = line.split('=', 1)[0].strip()
                    if key in section_data:
                        # Actualizar el valor si no es None, o eliminar si es None
                        new_value = section_data[key]
                        if new_value is not None:
                            updated_lines.append(f"{key} = {new_value}\n")
                            if self.logger:
                                self.logger.info(f"DEBUG: Actualizado {current_section}.{key} = {new_value}")
                        else:
                            # Valor None = eliminar línea
                            if self.logger:
                                self.logger.info(f"DEBUG: Eliminado {current_section}.{key}")
                        # Marcar como procesado
                        section_data[key] = 'PROCESSED'
                        i += 1
                        continue
            
            # Línea normal, mantener tal como está
            updated_lines.append(original_line + '\n')
            i += 1
        
        # Agregar secciones nuevas que no existían
        for section_name, section_data in sections_to_update.items():
            if section_name not in sections_found:
                updated_lines.append(f"\n[{section_name}]\n")
                if self.logger:
                    self.logger.info(f"DEBUG: Agregada nueva sección [{section_name}]")
                
                # Agregar todas las claves de esta sección
                for key, value in section_data.items():
                    if value is not None and value != 'PROCESSED':
                        updated_lines.append(f"{key} = {value}\n")
                        if self.logger:
                            self.logger.info(f"DEBUG: Agregado {section_name}.{key} = {value}")
            else:
                # Sección existía, agregar claves que no se encontraron
                for key, value in section_data.items():
                    if value is not None and value != 'PROCESSED':
                        # Buscar dónde termina esta sección para insertar la clave
                        section_end = len(updated_lines)
                        for j, line in enumerate(updated_lines):
                            if line.strip() == f"[{section_name}]":
                                # Encontrar el final de esta sección
                                for k in range(j + 1, len(updated_lines)):
                                    if updated_lines[k].strip().startswith('['):
                                        section_end = k
                                        break
                                break
                        
                        # Insertar la nueva clave antes del final de la sección
                        updated_lines.insert(section_end, f"{key} = {value}\n")
                        if self.logger:
                            self.logger.info(f"DEBUG: Agregado a sección existente {section_name}.{key} = {value}")
        
        # Escribir archivo actualizado
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
    
    def load_from_gameusersettings(self):
        """Cargar ServerPassword, AdminPassword y SessionName desde GameUserSettings.ini"""
        try:
            # Obtener servidor actual desde main_window si está disponible
            if not self.main_window or not hasattr(self.main_window, 'selected_server'):
                return
            
            selected_server = self.main_window.selected_server
            if not selected_server:
                return
            
            # Construir ruta al archivo GameUserSettings.ini
            server_path = self.config_manager.get("server", "root_path", "")
            if not server_path:
                return
            
            gameusersettings_path = os.path.join(
                server_path, 
                selected_server, 
                "ShooterGame", 
                "Saved", 
                "Config", 
                "WindowsServer", 
                "GameUserSettings.ini"
            )
            
            if not os.path.exists(gameusersettings_path):
                return
            
            # Leer archivo
            config = configparser.ConfigParser()
            config.optionxform = str  # Preservar mayúsculas/minúsculas
            try:
                config.read(gameusersettings_path, encoding='utf-8')
            except configparser.DuplicateOptionError as e:
                if self.logger:
                    self.logger.warning(f"Error leyendo GameUserSettings.ini: {e}")
                return
            
            # Cargar valores en los campos
            if config.has_section('ServerSettings'):
                # ServerPassword
                if config.has_option('ServerSettings', 'ServerPassword'):
                    self.server_password_entry.delete(0, "end")
                    self.server_password_entry.insert(0, config.get('ServerSettings', 'ServerPassword'))
                
                # ServerAdminPassword
                if config.has_option('ServerSettings', 'ServerAdminPassword'):
                    self.admin_password_entry.delete(0, "end")
                    self.admin_password_entry.insert(0, config.get('ServerSettings', 'ServerAdminPassword'))
            
            if config.has_section('SessionSettings'):
                # SessionName
                if config.has_option('SessionSettings', 'SessionName'):
                    self.session_name_entry.delete(0, "end")
                    self.session_name_entry.insert(0, config.get('SessionSettings', 'SessionName'))
            
            if config.has_section('/Script/Engine.GameSession'):
                # MaxPlayers
                if config.has_option('/Script/Engine.GameSession', 'MaxPlayers'):
                    self.max_players_entry.delete(0, "end")
                    self.max_players_entry.insert(0, config.get('/Script/Engine.GameSession', 'MaxPlayers'))
            
            if self.logger:
                self.logger.info(f"Configuración cargada desde GameUserSettings.ini: {gameusersettings_path}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al cargar desde GameUserSettings.ini: {e}")
    
    def load_configuration(self):
        """Cargar configuración desde archivo"""
        try:
            # Limpiar campos
            self.session_name_entry.delete(0, "end")
            self.server_password_entry.delete(0, "end")
            self.admin_password_entry.delete(0, "end")
            self.max_players_entry.delete(0, "end")
            self.query_port_entry.delete(0, "end")
            self.port_entry.delete(0, "end")
            self.multihome_entry.delete(0, "end")
            self.custom_args_text.delete("1.0", "end")
            
            # Cargar valores
            self.load_saved_config()
            
            # Cargar también desde GameUserSettings.ini
            self.load_from_gameusersettings()
            
            self.show_message("✅ Configuración cargada correctamente", "success")
            
        except Exception as e:
            self.logger.error(f"Error al cargar configuración: {e}")
            self.show_message(f"❌ Error al cargar: {str(e)}", "error")
    
    def start_server_with_config(self):
        """Iniciar servidor con la configuración actual"""
        # Obtener servidor y mapa desde main_window
        selected_server = None
        selected_map = None
        
        if self.main_window and hasattr(self.main_window, 'selected_server'):
            selected_server = self.main_window.selected_server
            selected_map = self.main_window.selected_map
        
        # Fallback a las variables locales si no están disponibles en main_window
        if not selected_server:
            selected_server = self.selected_server
        if not selected_map:
            selected_map = self.selected_map
        
        # Verificar si hay un servidor seleccionado
        if not selected_server:
            self.show_message("❌ Debe seleccionar un servidor primero", "error")
            return
        
        # Verificar si hay un mapa seleccionado
        if not selected_map:
            self.show_message("❌ Debe seleccionar un mapa primero", "error")
            return
        
        # Guardar configuración antes de iniciar
        self.save_configuration()
        
        # Construir argumentos del servidor
        server_args = self.build_server_arguments()
        
        # Iniciar servidor con argumentos personalizados
        try:
            self.show_message(f"🚀 Iniciando servidor {selected_server} con mapa {selected_map}", "info")
            
            # Llamar al método de inicio del servidor con argumentos personalizados
            if self.server_manager:
                self.server_manager.start_server_with_args(
                    self.add_status_message, 
                    selected_server, 
                    selected_map, 
                    server_args
                )
                
                # También notificar al main window si hay uno
                if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'server_panel'):
                    self.main_window.server_panel.update_server_status("Iniciando...", "orange")
            
        except Exception as e:
            self.logger.error(f"Error al iniciar servidor: {e}")
            self.show_message(f"❌ Error al iniciar servidor: {str(e)}", "error")
    
    def restart_server_with_config(self):
        """Reiniciar servidor con la configuración actual"""
        # Obtener servidor y mapa desde main_window
        selected_server = None
        selected_map = None
        
        if self.main_window and hasattr(self.main_window, 'selected_server'):
            selected_server = self.main_window.selected_server
            selected_map = self.main_window.selected_map
        
        # Fallback a las variables locales si no están disponibles en main_window
        if not selected_server:
            selected_server = self.selected_server
        if not selected_map:
            selected_map = self.selected_map
        
        # Verificar si hay un servidor seleccionado
        if not selected_server:
            self.show_message("❌ Debe seleccionar un servidor primero", "error")
            return
        
        # Verificar si hay un mapa seleccionado
        if not selected_map:
            self.show_message("❌ Debe seleccionar un mapa primero", "error")
            return
        
        # Guardar configuración antes de reiniciar
        self.save_configuration()
        
        # Construir argumentos del servidor
        server_args = self.build_server_arguments()
        
        # Reiniciar servidor con argumentos personalizados
        try:
            self.show_message(f"🔄 Reiniciando servidor {selected_server} con mapa {selected_map}", "info")
            
            # Llamar al método de reinicio del servidor con argumentos personalizados
            if self.server_manager:
                self.server_manager.restart_server(
                    self.add_status_message, 
                    selected_server, 
                    selected_map, 
                    server_args
                )
                
                # También notificar al main window si hay uno
                if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'server_panel'):
                    self.main_window.server_panel.update_server_status("Reiniciando...", "orange")
            
        except Exception as e:
            self.logger.error(f"Error al reiniciar servidor: {e}")
            self.show_message(f"❌ Error al reiniciar servidor: {str(e)}", "error")
    
    def build_server_arguments(self):
        """Construir argumentos del servidor basados en la configuración"""
        # 1. Obtener el mapa seleccionado (desde el dropdown de la ventana principal)
        selected_map = None
        if hasattr(self.main_window, 'selected_map') and self.main_window.selected_map:
            selected_map = self.main_window.selected_map
        elif self.selected_map:
            selected_map = self.selected_map
        
        # Mapear nombres de mapas a sus identificadores técnicos
        # NOTA: Incluimos todas las variantes posibles para máxima compatibilidad
        map_identifiers = {
            # IDENTIFICADORES CORRECTOS PARA ARK SURVIVAL ASCENDED:
            "The Island": "TheIsland_WP",        # ✅ SÍ necesita _WP
            "TheIsland": "TheIsland_WP",
            "TheIsland_WP": "TheIsland_WP",
            "The Center": "TheCenter_WP",        # ✅ SÍ necesita _WP (ASA)
            "TheCenter": "TheCenter_WP",
            "TheCenter_WP": "TheCenter_WP",
            "Scorched Earth": "ScorchedEarth_WP", # ✅ SÍ necesita _WP
            "ScorchedEarth": "ScorchedEarth_WP",
            "ScorchedEarth_WP": "ScorchedEarth_WP",
            "Ragnarok": "Ragnarok_WP",           # ✅ SÍ necesita _WP (ASA)
            "Ragnarok_WP": "Ragnarok_WP",
            "Aberration": "Aberration_P",        # ✅ Usa _P
            "Aberration_P": "Aberration_P",
            "Extinction": "Extinction",          # ✅ NO necesita _WP
            "Valguero": "Valguero_P",           # ✅ Usa _P
            "Valguero_P": "Valguero_P",
            "Genesis: Part 1": "Genesis",        # ✅ NO necesita _WP
            "Genesis1": "Genesis",
            "Genesis": "Genesis",
            "Crystal Isles": "CrystalIsles",     # ✅ NO necesita _WP
            "CrystalIsles": "CrystalIsles",
            "Genesis: Part 2": "Gen2",          # ✅ Abreviado a Gen2
            "Genesis2": "Gen2",
            "Gen2": "Gen2",
            "Lost Island": "LostIsland",         # ✅ NO necesita _WP
            "LostIsland": "LostIsland",
            "Fjordur": "Fjordur",               # ✅ NO necesita _WP
            "Modded Map": "ModdedMap",
            "ModdedMap": "ModdedMap"
        }
        
        # Construir el argumento base del mapa siguiendo el formato correcto
        self.logger.info(f"DEBUG: Mapa seleccionado: '{selected_map}' (tipo: {type(selected_map)}, len: {len(selected_map) if selected_map else 'N/A'})")
        self.logger.info(f"DEBUG: Mapas disponibles: {list(map_identifiers.keys())}")
        self.logger.info(f"DEBUG: ¿Mapa es None?: {selected_map is None}")
        self.logger.info(f"DEBUG: ¿Mapa en diccionario?: {selected_map in map_identifiers if selected_map else 'N/A'}")
        
        # Debug más específico: comparar caractér por caractér
        if selected_map:
            for key in map_identifiers.keys():
                if key == selected_map:
                    self.logger.info(f"DEBUG: ✅ Coincidencia exacta encontrada con '{key}'")
                elif key.strip() == selected_map.strip():
                    self.logger.info(f"DEBUG: ⚠️ Coincidencia con espacios: '{key}' vs '{selected_map}'")
                
        if selected_map and selected_map in map_identifiers:
            map_identifier = map_identifiers[selected_map]
            map_arg = f"{map_identifier}?listen"
            self.logger.info(f"DEBUG: ✅ Mapa encontrado. Usando identificador: {map_identifier}")
        else:
            # Mapa por defecto si no hay selección
            map_arg = "TheIsland_WP?listen"
            self.logger.warning(f"DEBUG: ❌ Mapa no encontrado o vacío. Razón: selected_map='{selected_map}', en diccionario={selected_map in map_identifiers if selected_map else False}. Usando por defecto: TheIsland_WP")
        
        # 2. Agregar parámetros básicos en el orden correcto
        # Port
        port = self.port_entry.get() or "7777"
        map_arg += f"?Port={port}"
        
        # QueryPort
        query_port = self.query_port_entry.get() or "27015"
        map_arg += f"?QueryPort={query_port}"
        
        # MultiHome (usar valor del campo o por defecto)
        multihome = self.multihome_entry.get() or "127.0.0.1"
        map_arg += f"?MultiHome={multihome}"
        
        # 3. Procesar argumentos personalizados antes del final
        custom_args = self.custom_args_text.get("1.0", "end-1c").strip()
        if custom_args:
            for line in custom_args.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):  # Ignorar líneas vacías y comentarios
                    # Si la línea ya comienza con ?, la agregamos tal como está
                    if line.startswith('?'):
                        map_arg += line
                    else:
                        # Si no, agregamos el ? al principio
                        map_arg += f"?{line}"
        
        # 4. Agregar argumentos RCON si está habilitado
        if hasattr(self.main_window, 'rcon_panel') and self.main_window.rcon_panel.get_rcon_enabled():
            rcon_port = self.main_window.rcon_panel.get_rcon_port()
            map_arg += f"?RCONEnable=True?RCONPort={rcon_port}"
        
        # 5. Obtener mods configurados (buscar por servidor/mapa específico primero)
        # Obtener servidor seleccionado
        selected_server = None
        if hasattr(self.main_window, 'selected_server') and self.main_window.selected_server:
            selected_server = self.main_window.selected_server
        elif self.selected_server:
            selected_server = self.selected_server
            
        server_map_key = f"{selected_server}_{selected_map}" if selected_server and selected_map else "default"
        mod_ids = self.config_manager.get("server", f"mod_ids_{server_map_key}", "").strip()
        
        # Fallback a la configuración general si no hay específica
        if not mod_ids:
            mod_ids = self.config_manager.get("server", "mod_ids", "").strip()
        
        # 6. Construir la lista final con un solo argumento y los flags del servidor
        args = [map_arg, "-server", "-log"]
        
        # 7. Agregar mods si existen
        if mod_ids:
            args.append(f"-mods={mod_ids}")
        
        self.logger.info(f"DEBUG: Argumentos finales generados: {args}")
        
        return args
    
    def update_server_info(self, server_name, map_name):
        """Actualizar información del servidor seleccionado"""
        self.selected_server = server_name
        self.selected_map = map_name
        
        # Cargar configuración específica del servidor desde GameUserSettings.ini
        self.load_from_gameusersettings()
    
    def get_public_ip(self):
        """Obtener IP pública automáticamente"""
        def _get_ip():
            try:
                self.ip_auto_button.configure(text="🔄 Obteniendo...", state="disabled")
                
                # Intentar varios servicios para obtener la IP pública
                services = [
                    "https://api.ipify.org",
                    "https://ipecho.net/plain",
                    "https://icanhazip.com",
                    "https://ident.me"
                ]
                
                for service in services:
                    try:
                        response = requests.get(service, timeout=5)
                        if response.status_code == 200:
                            public_ip = response.text.strip()
                            # Validar que sea una IP válida
                            if self.is_valid_ip(public_ip):
                                # Actualizar campo en el hilo principal
                                self.parent.after(0, lambda: self.update_multihome_ip(public_ip))
                                return
                    except:
                        continue
                        
                # Si no se pudo obtener IP
                self.parent.after(0, lambda: self.show_ip_error())
                
            except Exception as e:
                self.logger.error(f"Error al obtener IP pública: {e}")
                self.parent.after(0, lambda: self.show_ip_error())
            finally:
                self.parent.after(0, lambda: self.ip_auto_button.configure(text="🌐 IP Pública", state="normal"))
        
        threading.Thread(target=_get_ip, daemon=True).start()
    
    def is_valid_ip(self, ip):
        """Validar si una cadena es una IP válida"""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False
    
    def update_multihome_ip(self, ip):
        """Actualizar campo MultiHome con la IP obtenida"""
        self.multihome_entry.delete(0, "end")
        self.multihome_entry.insert(0, ip)
        self.show_message(f"✅ IP pública obtenida: {ip}", "success")
    
    def show_ip_error(self):
        """Mostrar error al no poder obtener IP"""
        self.show_message("❌ No se pudo obtener la IP pública. Usando IP local.", "error")
    
    def refresh_rcon_args(self):
        """Refrescar vista previa cuando cambian configuraciones RCON"""
        # Este método puede ser llamado desde el panel RCON
        # Para futuras implementaciones de vista previa en tiempo real
        pass
    
    def preview_arguments(self):
        """Mostrar una vista previa de los argumentos que se generarán"""
        try:
            # Construir argumentos
            server_args = self.build_server_arguments()
            
            # Crear ventana de vista previa
            import customtkinter as ctk
            
            preview_window = ctk.CTkToplevel()
            preview_window.title("Vista Previa de Argumentos del Servidor")
            preview_window.geometry("800x400")
            preview_window.resizable(True, True)
            
            # Centrar la ventana
            preview_window.transient(self.parent)
            preview_window.grab_set()
            
            # Título
            ctk.CTkLabel(
                preview_window, 
                text="Argumentos que se pasarán al servidor:",
                font=("Arial", 14, "bold")
            ).pack(pady=10)
            
            # Área de texto para mostrar los argumentos
            args_text = ctk.CTkTextbox(preview_window, height=300)
            args_text.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Formatear argumentos para mejor visualización
            args_formatted = ""
            for i, arg in enumerate(server_args):
                args_formatted += f"Argumento {i+1}: {arg}\n"
            
            # Comando completo
            args_formatted += f"\n--- COMANDO COMPLETO ---\n"
            args_formatted += f"ArkAscendedServer.exe {' '.join(server_args)}\n"
            
            # Insertar texto
            args_text.insert("1.0", args_formatted)
            args_text.configure(state="disabled")
            
            # Botón cerrar
            ctk.CTkButton(
                preview_window,
                text="Cerrar",
                command=preview_window.destroy,
                height=30
            ).pack(pady=10)
            
        except Exception as e:
            self.logger.error(f"Error al generar vista previa: {e}")
            self.show_message(f"❌ Error al generar vista previa: {str(e)}", "error")
    
    def show_message(self, message, message_type="info"):
        """Mostrar mensaje en el log principal"""
        if self.main_window and hasattr(self.main_window, 'add_log_message'):
            self.main_window.add_log_message(message)
        else:
            # Fallback: mostrar en consola
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")
    
    def add_status_message(self, message, message_type="info"):
        """Agregar mensaje de estado"""
        self.show_message(message, message_type)
