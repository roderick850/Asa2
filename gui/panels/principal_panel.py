import customtkinter as ctk
import os
import threading
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
        ctk.CTkLabel(col2_frame, text="MultiHome:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
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
            
            # Mostrar mensaje de éxito
            self.show_message("✅ Configuración guardada correctamente", "success")
            
        except Exception as e:
            self.logger.error(f"Error al guardar configuración: {e}")
            self.show_message(f"❌ Error al guardar: {str(e)}", "error")
    
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
            
            self.show_message("✅ Configuración cargada correctamente", "success")
            
        except Exception as e:
            self.logger.error(f"Error al cargar configuración: {e}")
            self.show_message(f"❌ Error al cargar: {str(e)}", "error")
    
    def start_server_with_config(self):
        """Iniciar servidor con la configuración actual"""
        # Verificar si hay un servidor seleccionado
        if not self.selected_server:
            self.show_message("❌ Debe seleccionar un servidor primero", "error")
            return
        
        # Verificar si hay un mapa seleccionado
        if not self.selected_map:
            self.show_message("❌ Debe seleccionar un mapa primero", "error")
            return
        
        # Guardar configuración antes de iniciar
        self.save_configuration()
        
        # Construir argumentos del servidor
        server_args = self.build_server_arguments()
        
        # Iniciar servidor con argumentos personalizados
        try:
            self.show_message(f"🚀 Iniciando servidor {self.selected_server} con mapa {self.selected_map}", "info")
            
            # Llamar al método de inicio del servidor con argumentos personalizados
            if self.server_manager:
                self.server_manager.start_server_with_args(
                    self.add_status_message, 
                    self.selected_server, 
                    self.selected_map, 
                    server_args
                )
                
                # También notificar al main window si hay uno
                if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'server_panel'):
                    self.main_window.server_panel.update_server_status("Iniciando...", "orange")
            
        except Exception as e:
            self.logger.error(f"Error al iniciar servidor: {e}")
            self.show_message(f"❌ Error al iniciar servidor: {str(e)}", "error")
    
    def build_server_arguments(self):
        """Construir argumentos del servidor basados en la configuración"""
        # 1. Obtener el mapa seleccionado (desde el dropdown de la ventana principal)
        selected_map = None
        if hasattr(self.main_window, 'selected_map') and self.main_window.selected_map:
            selected_map = self.main_window.selected_map
        
        # Mapear nombres de mapas a sus identificadores técnicos
        map_identifiers = {
            "The Island": "TheIsland_WP",
            "The Center": "TheCenter",
            "Scorched Earth": "ScorchedEarth_WP", 
            "Ragnarok": "Ragnarok",
            "Aberration": "Aberration_P",
            "Extinction": "Extinction",
            "Valguero": "Valguero_P",
            "Genesis: Part 1": "Genesis",
            "Crystal Isles": "CrystalIsles",
            "Genesis: Part 2": "Genesis2",
            "Lost Island": "LostIsland",
            "Fjordur": "Fjordur"
        }
        
        # Construir el argumento base del mapa siguiendo el formato correcto
        if selected_map and selected_map in map_identifiers:
            map_arg = f"{map_identifiers[selected_map]}?listen"
        else:
            # Mapa por defecto si no hay selección
            map_arg = "TheIsland_WP?listen"
        
        # 2. Agregar parámetros básicos en el orden correcto
        # ServerPassword (si existe)
        if self.server_password_entry.get():
            map_arg += f"?ServerPassword={self.server_password_entry.get()}"
        
        # Port
        port = self.port_entry.get() or "7777"
        map_arg += f"?Port={port}"
        
        # QueryPort
        query_port = self.query_port_entry.get() or "27015"
        map_arg += f"?QueryPort={query_port}"
        
        # MaxPlayers
        if self.max_players_entry.get():
            map_arg += f"?MaxPlayers={self.max_players_entry.get()}"
        
        # MultiHome (usar valor del campo o por defecto)
        multihome = self.multihome_entry.get() or "127.0.0.1"
        map_arg += f"?MultiHome={multihome}"
        
        # SessionName (si existe)
        if self.session_name_entry.get():
            map_arg += f"?SessionName={self.session_name_entry.get()}"
        
        # AdminPassword (si existe)
        if self.admin_password_entry.get():
            map_arg += f"?AdminPassword={self.admin_password_entry.get()}"
        
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
        
        # 4. Agregar ServerPVE por defecto (como en tu script)
        map_arg += "?ServerPVE=true"
        
        # 5. Construir la lista final con un solo argumento y los flags del servidor
        args = [map_arg, "-server", "-log"]
        
        return args
    
    def update_server_info(self, server_name, map_name):
        """Actualizar información del servidor seleccionado"""
        self.selected_server = server_name
        self.selected_map = map_name
    
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
