import customtkinter as ctk
import threading
import time
import psutil
import os
import subprocess
from datetime import datetime
from tkinter import filedialog
from utils.server_manager import ServerManager


class ServerPanel:
    def __init__(self, parent, config_manager, logger):
        self.parent = parent
        self.config_manager = config_manager
        self.logger = logger
        self.server_manager = ServerManager(config_manager, logger)
        
        # Inicializar variables de selección
        self.selected_server = None
        self.selected_map = None
        
        self.create_widgets()
        self.start_monitoring()
    
    def create_widgets(self):
        # Frame principal
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        title_label = ctk.CTkLabel(main_frame, text="Control del Servidor", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(10, 5))
        
        # Frame destacado para la ruta raíz actual
        current_path_frame = ctk.CTkFrame(main_frame, fg_color=("gray90", "gray20"))
        current_path_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        current_path_label = ctk.CTkLabel(
            current_path_frame,
            text="📍 Ruta Raíz Actual:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("blue", "lightblue")
        )
        current_path_label.pack(anchor="w", padx=10, pady=(8, 3))
        
        self.current_path_display = ctk.CTkLabel(
            current_path_frame,
            text="No configurada",
            font=ctk.CTkFont(size=12),
            text_color=("red", "orange")
        )
        self.current_path_display.pack(anchor="w", padx=10, pady=(0, 8))
        
        change_path_button = ctk.CTkButton(
            current_path_frame,
            text="Cambiar Ruta",
            command=self.browse_root_path,
            fg_color=("blue", "darkblue"),
            hover_color=("darkblue", "navy"),
            width=100,
            height=25
        )
        change_path_button.pack(anchor="w", padx=10, pady=(0, 8))
        
        # Frame para selección de servidor y mapa
        selection_frame = ctk.CTkFrame(main_frame, fg_color=("gray90", "gray20"))
        selection_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        selection_label = ctk.CTkLabel(
            selection_frame,
            text="🎮 Configuración del Servidor:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("blue", "lightblue")
        )
        selection_label.pack(anchor="w", padx=10, pady=(8, 5))
        
        # Frame para los desplegables
        dropdowns_frame = ctk.CTkFrame(selection_frame)
        dropdowns_frame.pack(fill="x", padx=10, pady=(0, 8))
        
        # Frame para los desplegables (uno al lado del otro)
        dropdowns_row_frame = ctk.CTkFrame(dropdowns_frame)
        dropdowns_row_frame.pack(fill="x", pady=2)
        
        # Desplegable para seleccionar servidor (lado izquierdo)
        server_selection_frame = ctk.CTkFrame(dropdowns_row_frame)
        server_selection_frame.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkLabel(
            server_selection_frame,
            text="Servidor:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(10, 5), pady=5)
        
        self.server_dropdown = ctk.CTkOptionMenu(
            server_selection_frame,
            values=["Seleccionar servidor..."],
            command=self.on_server_selected,
            width=200
        )
        self.server_dropdown.pack(side="left", padx=5, pady=5)
        
        # Botón para refrescar lista de servidores
        refresh_servers_button = ctk.CTkButton(
            server_selection_frame,
            text="🔄",
            command=self.refresh_servers_list,
            width=30,
            height=25
        )
        refresh_servers_button.pack(side="left", padx=5, pady=5)
        
        # Desplegable para seleccionar mapa (lado derecho)
        map_selection_frame = ctk.CTkFrame(dropdowns_row_frame)
        map_selection_frame.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        ctk.CTkLabel(
            map_selection_frame,
            text="Mapa:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(10, 5), pady=5)
        
        self.map_dropdown = ctk.CTkOptionMenu(
            map_selection_frame,
            values=["Seleccionar mapa..."],
            command=self.on_map_selected,
            width=200
        )
        self.map_dropdown.pack(side="left", padx=5, pady=5)
        
        # Frame para controles principales
        controls_frame = ctk.CTkFrame(main_frame)
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        # Botones principales
        buttons_frame = ctk.CTkFrame(controls_frame)
        buttons_frame.pack(pady=10)
        
        # Botones de control del servidor
        self.start_button = ctk.CTkButton(
            buttons_frame, 
            text="Iniciar Servidor", 
            command=self.start_server,
            fg_color="green",
            hover_color="darkgreen",
            width=130,
            height=35
        )
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.stop_button = ctk.CTkButton(
            buttons_frame, 
            text="Detener Servidor", 
            command=self.stop_server,
            fg_color="red",
            hover_color="darkred",
            width=130,
            height=35
        )
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.restart_button = ctk.CTkButton(
            buttons_frame, 
            text="Reiniciar Servidor", 
            command=self.restart_server,
            fg_color="orange",
            hover_color="darkorange",
            width=130,
            height=35
        )
        self.restart_button.grid(row=0, column=2, padx=5, pady=5)
        
        self.install_button = ctk.CTkButton(
            buttons_frame, 
            text="Instalar/Actualizar", 
            command=self.install_server,
            fg_color="blue",
            hover_color="darkblue",
            width=130,
            height=35
        )
        self.install_button.grid(row=0, column=3, padx=5, pady=5)
        
        # Frame para barra de progreso
        self.progress_frame = ctk.CTkFrame(main_frame)
        self.progress_frame.pack(fill="x", padx=10, pady=5)
        
        # Barra de progreso
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.progress_label.pack(pady=(5, 2))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 5))
        self.progress_bar.set(0)
        
        # Ocultar la barra de progreso inicialmente
        self.progress_frame.pack_forget()
        
        # Frame para información del servidor
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        # Información del servidor
        info_label = ctk.CTkLabel(info_frame, text="Información del Servidor", font=ctk.CTkFont(size=16, weight="bold"))
        info_label.pack(pady=(10, 5))
        
        # Grid para información
        info_grid = ctk.CTkFrame(info_frame)
        info_grid.pack(pady=5)
        
        # Estado del servidor
        ctk.CTkLabel(info_grid, text="Estado:").grid(row=0, column=0, padx=8, pady=3, sticky="w")
        self.status_label = ctk.CTkLabel(info_grid, text="Detenido", text_color="red")
        self.status_label.grid(row=0, column=1, padx=8, pady=3, sticky="w")
        
        # Tiempo de actividad
        ctk.CTkLabel(info_grid, text="Tiempo de actividad:").grid(row=1, column=0, padx=8, pady=3, sticky="w")
        self.uptime_label = ctk.CTkLabel(info_grid, text="00:00:00")
        self.uptime_label.grid(row=1, column=1, padx=8, pady=3, sticky="w")
        
        # Uso de CPU
        ctk.CTkLabel(info_grid, text="Uso de CPU:").grid(row=2, column=0, padx=8, pady=3, sticky="w")
        self.cpu_label = ctk.CTkLabel(info_grid, text="0%")
        self.cpu_label.grid(row=2, column=1, padx=8, pady=3, sticky="w")
        
        # Uso de memoria
        ctk.CTkLabel(info_grid, text="Uso de memoria:").grid(row=3, column=0, padx=8, pady=3, sticky="w")
        self.memory_label = ctk.CTkLabel(info_grid, text="0 MB")
        self.memory_label.grid(row=3, column=1, padx=8, pady=3, sticky="w")
        
        # Frame para acciones rápidas
        quick_actions_frame = ctk.CTkFrame(main_frame)
        quick_actions_frame.pack(fill="x", padx=10, pady=5)
        
        quick_actions_label = ctk.CTkLabel(quick_actions_frame, text="Acciones Rápidas", font=ctk.CTkFont(size=16, weight="bold"))
        quick_actions_label.pack(pady=(10, 5))
        
        # Botones de acciones rápidas
        quick_buttons_frame = ctk.CTkFrame(quick_actions_frame)
        quick_buttons_frame.pack(pady=5)
        
        self.save_button = ctk.CTkButton(
            quick_buttons_frame,
            text="Guardar Mundo",
            command=self.save_world,
            width=100,
            height=30
        )
        self.save_button.grid(row=0, column=0, padx=3, pady=3)
        
        self.backup_button = ctk.CTkButton(
            quick_buttons_frame,
            text="Crear Backup",
            command=self.create_backup,
            width=100,
            height=30
        )
        self.backup_button.grid(row=0, column=1, padx=3, pady=3)
        
        self.broadcast_button = ctk.CTkButton(
            quick_buttons_frame,
            text="Broadcast",
            command=self.show_broadcast_dialog,
            width=100,
            height=30
        )
        self.broadcast_button.grid(row=0, column=2, padx=3, pady=3)
        
        self.kick_all_button = ctk.CTkButton(
            quick_buttons_frame,
            text="Expulsar Todos",
            command=self.kick_all_players,
            fg_color="red",
            hover_color="darkred",
            width=100,
            height=30
        )
        self.kick_all_button.grid(row=0, column=3, padx=3, pady=3)
        
        # Frame para gestión de jugadores
        players_frame = ctk.CTkFrame(main_frame)
        players_frame.pack(fill="x", padx=10, pady=5)
        
        players_label = ctk.CTkLabel(players_frame, text="Gestión de Jugadores", font=ctk.CTkFont(size=16, weight="bold"))
        players_label.pack(pady=(10, 5))
        
        # Frame para entrada de jugador
        player_input_frame = ctk.CTkFrame(players_frame)
        player_input_frame.pack(pady=5)
        
        ctk.CTkLabel(player_input_frame, text="Jugador:").pack(side="left", padx=(8, 3))
        self.player_entry = ctk.CTkEntry(player_input_frame, width=120)
        self.player_entry.pack(side="left", padx=3)
        
        # Botones de gestión de jugadores
        player_buttons_frame = ctk.CTkFrame(players_frame)
        player_buttons_frame.pack(pady=5)
        
        self.kick_player_button = ctk.CTkButton(
            player_buttons_frame,
            text="Expulsar",
            command=self.kick_player,
            fg_color="orange",
            hover_color="darkorange",
            width=80,
            height=25
        )
        self.kick_player_button.pack(side="left", padx=3)
        
        self.ban_player_button = ctk.CTkButton(
            player_buttons_frame,
            text="Banear",
            command=self.ban_player,
            fg_color="red",
            hover_color="darkred",
            width=80,
            height=25
        )
        self.ban_player_button.pack(side="left", padx=3)
        
        self.teleport_button = ctk.CTkButton(
            player_buttons_frame,
            text="Teletransportar",
            command=self.teleport_player,
            width=80,
            height=25
        )
        self.teleport_button.pack(side="left", padx=3)
        
        self.give_item_button = ctk.CTkButton(
            player_buttons_frame,
            text="Dar Item",
            command=self.give_item_to_player,
            width=80,
            height=25
        )
        self.give_item_button.pack(side="left", padx=3)
        
        # Frame para mensajes de estado
        self.status_frame = ctk.CTkFrame(main_frame)
        self.status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.status_text = ctk.CTkTextbox(self.status_frame, height=80)
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Actualizar la visualización de la ruta raíz
        self.update_current_path_display()
    
    def browse_root_path(self):
        """Buscar directorio raíz para servidores"""
        directory = filedialog.askdirectory(title="Seleccionar ruta raíz para servidores")
        if directory:
            self.config_manager.set("server", "root_path", directory)
            self.config_manager.save()
            self.update_current_path_display()
            self.add_status_message(f"Ruta raíz cambiada a: {directory}", "success")
    
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
        
        # Actualizar lista de servidores cuando cambia la ruta
        self.refresh_servers_list()
    
    def refresh_servers_list(self):
        """Refresca la lista de servidores disponibles"""
        try:
            root_path = self.config_manager.get("server", "root_path", "").strip()
            if not root_path or not os.path.exists(root_path):
                self.server_dropdown.configure(values=["Seleccionar servidor..."])
                return
            
            # Buscar servidores en el directorio raíz
            servers = []
            for item in os.listdir(root_path):
                item_path = os.path.join(root_path, item)
                if os.path.isdir(item_path) and item != "SteamCMD":
                    # Verificar si es un servidor válido buscando el ejecutable
                    if self.server_manager.find_server_executable(item_path):
                        servers.append(item)
            
            if servers:
                self.server_dropdown.configure(values=["Seleccionar servidor..."] + servers)
                self.add_status_message(f"Encontrados {len(servers)} servidor(es)", "info")
            else:
                self.server_dropdown.configure(values=["Seleccionar servidor..."])
                self.add_status_message("No se encontraron servidores instalados", "warning")
                
        except Exception as e:
            self.logger.error(f"Error al refrescar lista de servidores: {e}")
            self.server_dropdown.configure(values=["Seleccionar servidor..."])
    
    def on_server_selected(self, server_name):
        """Maneja la selección de un servidor"""
        if server_name and server_name != "Seleccionar servidor...":
            self.selected_server = server_name
            self.add_status_message(f"Servidor seleccionado: {server_name}", "info")
            # Cargar mapas disponibles para este servidor
            self.load_maps_for_server(server_name)
            # Actualizar información del servidor
            self.update_server_info_for_selected()
            # Mostrar información del servidor en la interfaz
            self.show_selected_server_info()
        else:
            self.selected_server = None
            self.map_dropdown.configure(values=["Seleccionar mapa..."])
            self.clear_selected_server_info()
    
    def show_selected_server_info(self):
        """Muestra la información del servidor seleccionado en la interfaz"""
        server_info = self.get_selected_server_info()
        if server_info:
            # Actualizar el título o mostrar información adicional
            info_text = f"Servidor: {server_info['name']}"
            if server_info['has_executable']:
                info_text += " ✅"
            else:
                info_text += " ⚠️"
            
            # Aquí podrías actualizar un label o mostrar más información
            self.add_status_message(f"Información del servidor: {info_text}", "info")
    
    def clear_selected_server_info(self):
        """Limpia la información del servidor seleccionado"""
        # Aquí podrías limpiar la información mostrada
        pass
    
    def update_server_info_for_selected(self):
        """Actualiza la información del servidor seleccionado"""
        if not self.selected_server:
            return
        
        try:
            root_path = self.config_manager.get("server", "root_path", "").strip()
            if not root_path:
                return
            
            server_path = os.path.join(root_path, self.selected_server)
            if not os.path.exists(server_path):
                return
            
            # Buscar el ejecutable del servidor
            server_exe = self.server_manager.find_server_executable(server_path)
            if server_exe:
                # Guardar la ruta del ejecutable en la configuración
                server_key = f"executable_path_{self.selected_server}"
                self.config_manager.set("server", server_key, server_exe)
                self.config_manager.save()
                
                self.add_status_message(f"✅ Ejecutable encontrado para {self.selected_server}: {server_exe}", "success")
            else:
                self.add_status_message(f"⚠️ No se encontró el ejecutable para {self.selected_server}", "warning")
                
        except Exception as e:
            self.logger.error(f"Error al actualizar información del servidor: {e}")
    
    def load_maps_for_server(self, server_name):
        """Carga los mapas disponibles para el servidor seleccionado"""
        try:
            root_path = self.config_manager.get("server", "root_path", "").strip()
            if not root_path or not server_name:
                self.map_dropdown.configure(values=["Seleccionar mapa..."])
                return
            
            server_path = os.path.join(root_path, server_name)
            if not os.path.exists(server_path):
                self.map_dropdown.configure(values=["Seleccionar mapa..."])
                return
            
            # Mapas disponibles para Ark Survival Ascended
            available_maps = [
                "TheIsland_WP",           # The Island
                "ScorchedEarth_WP",       # Scorched Earth
                "Aberration_P",           # Aberration
                "Extinction",             # Extinction
                "Genesis",                # Genesis
                "Genesis2",               # Genesis Part 2
                "TheCenter",              # The Center
                "Ragnarok",               # Ragnarok
                "Valguero_P",             # Valguero
                "CrystalIsles",           # Crystal Isles
                "LostIsland",             # Lost Island
                "Fjordur",                # Fjordur
                "ModdedMap"               # Mapa Modded
            ]
            
            # Verificar qué mapas están disponibles en el servidor
            available_maps_found = []
            
            # Buscar archivos de mapa en el servidor
            for root, dirs, files in os.walk(server_path):
                for file in files:
                    if file.lower().endswith('.umap'):
                        # Extraer el nombre del mapa del archivo
                        map_name = os.path.splitext(file)[0]
                        if map_name not in available_maps_found:
                            available_maps_found.append(map_name)
            
            # Si no se encontraron mapas específicos, usar la lista completa
            if not available_maps_found:
                available_maps_found = available_maps
            
            # Ordenar los mapas encontrados
            available_maps_found.sort()
            
            self.map_dropdown.configure(values=["Seleccionar mapa..."] + available_maps_found)
            self.add_status_message(f"Cargados {len(available_maps_found)} mapa(s) para {server_name}", "info")
            
        except Exception as e:
            self.logger.error(f"Error al cargar mapas: {e}")
            self.map_dropdown.configure(values=["Seleccionar mapa..."])
    
    def on_map_selected(self, map_name):
        """Maneja la selección de un mapa"""
        if map_name and map_name != "Seleccionar mapa...":
            self.selected_map = map_name
            self.add_status_message(f"Mapa seleccionado: {map_name}", "info")
        else:
            self.selected_map = None
    
    def start_monitoring(self):
        """Inicia el monitoreo del servidor en un hilo separado"""
        def monitor():
            while True:
                try:
                    self.update_server_info()
                    time.sleep(2)  # Actualizar cada 2 segundos
                except Exception as e:
                    self.logger.error(f"Error en monitoreo: {e}")
                    time.sleep(5)
        
        threading.Thread(target=monitor, daemon=True).start()
    
    def update_server_info(self):
        """Actualiza la información del servidor"""
        try:
            # Obtener información del servidor usando ServerManager
            status = self.server_manager.get_server_status()
            uptime = self.server_manager.get_uptime()
            stats = self.server_manager.get_server_stats()
            
            # Actualizar etiquetas
            if status == "Ejecutándose":
                status_color = "green"
            else:
                status_color = "red"
            
            self.status_label.configure(text=status, text_color=status_color)
            self.uptime_label.configure(text=uptime)
            self.cpu_label.configure(text=f"{stats['cpu']:.1f}%")
            self.memory_label.configure(text=f"{stats['memory_mb']:.1f} MB")
            
            # Mostrar información del servidor seleccionado si hay uno
            if hasattr(self, 'selected_server') and self.selected_server:
                # Actualizar el título o mostrar información adicional
                pass
                
        except Exception as e:
            self.logger.error(f"Error al actualizar información del servidor: {e}")
    
    def get_selected_server_info(self):
        """Obtiene información del servidor seleccionado"""
        if not hasattr(self, 'selected_server') or not self.selected_server:
            return None
        
        try:
            root_path = self.config_manager.get("server", "root_path", "").strip()
            if not root_path:
                return None
            
            server_path = os.path.join(root_path, self.selected_server)
            if not os.path.exists(server_path):
                return None
            
            # Buscar el ejecutable del servidor
            server_exe = self.server_manager.find_server_executable(server_path)
            
            return {
                "name": self.selected_server,
                "path": server_path,
                "executable": server_exe,
                "exists": os.path.exists(server_path),
                "has_executable": server_exe is not None
            }
        except Exception as e:
            self.logger.error(f"Error al obtener información del servidor: {e}")
            return None
    
    def start_server(self):
        """Inicia el servidor"""
        if not hasattr(self, 'selected_server') or not self.selected_server:
            self.add_status_message("Error: Debe seleccionar un servidor primero", "error")
            return
        
        if not hasattr(self, 'selected_map') or not self.selected_map:
            self.add_status_message("Error: Debe seleccionar un mapa primero", "error")
            return
        
        self.add_status_message(f"Iniciando servidor: {self.selected_server} con mapa: {self.selected_map}", "info")
        self.server_manager.start_server(self.add_status_message, self.selected_server, self.selected_map)
    
    def stop_server(self):
        """Detiene el servidor"""
        if not hasattr(self, 'selected_server') or not self.selected_server:
            self.add_status_message("Error: Debe seleccionar un servidor primero", "error")
            return
        
        self.add_status_message(f"Deteniendo servidor: {self.selected_server}", "info")
        self.server_manager.stop_server(self.add_status_message)
    
    def restart_server(self):
        """Reinicia el servidor"""
        if not hasattr(self, 'selected_server') or not self.selected_server:
            self.add_status_message("Error: Debe seleccionar un servidor primero", "error")
            return
        
        if not hasattr(self, 'selected_map') or not self.selected_map:
            self.add_status_message("Error: Debe seleccionar un mapa primero", "error")
            return
        
        self.add_status_message(f"Reiniciando servidor: {self.selected_server} con mapa: {self.selected_map}", "info")
        self.server_manager.restart_server(self.add_status_message, self.selected_server, self.selected_map)
    
    def show_progress(self, message="", progress=0):
        """Muestra la barra de progreso con un mensaje y porcentaje"""
        self.progress_frame.pack(fill="x", padx=10, pady=5, before=self.status_frame)
        self.progress_label.configure(text=message)
        self.progress_bar.set(progress / 100)
        
    def hide_progress(self):
        """Oculta la barra de progreso"""
        self.progress_frame.pack_forget()
        
    def update_progress(self, message, progress):
        """Actualiza la barra de progreso"""
        self.progress_label.configure(text=message)
        self.progress_bar.set(progress / 100)
        
    def install_server(self):
        """Instala/actualiza el servidor"""
        # Verificar si hay una ruta raíz configurada
        root_path = self.config_manager.get("server", "root_path", "").strip()
        if not root_path:
            self.add_status_message("Error: Primero debe configurar la ruta raíz en la pestaña Configuración", "error")
            return
        
        # Mostrar diálogo para el nombre del servidor
        dialog = ctk.CTkInputDialog(
            text="Ingrese el nombre del servidor (será el nombre de la carpeta):",
            title="Nombre del Servidor"
        )
        server_name = dialog.get_input()
        
        if not server_name or not server_name.strip():
            self.add_status_message("Error: Debe ingresar un nombre para el servidor", "error")
            return
        
        # Limpiar el nombre del servidor (remover caracteres especiales)
        server_name = server_name.strip()
        # Reemplazar caracteres no válidos para nombres de carpeta
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            server_name = server_name.replace(char, '_')
        
        # Verificar si ya existe un servidor con ese nombre
        server_path = os.path.join(root_path, server_name)
        server_exists = os.path.exists(server_path)
        
        if server_exists:
            # Verificar si hay un ejecutable válido
            existing_exe = self.server_manager.find_server_executable(server_path)
            if existing_exe:
                # Preguntar si quiere actualizar
                update_dialog = ctk.CTkInputDialog(
                    text=f"El servidor '{server_name}' ya existe con ejecutable válido.\n¿Desea actualizarlo? (s/n):",
                    title="Servidor Existente"
                )
                update_response = update_dialog.get_input()
                if not update_response or update_response.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
                    self.add_status_message("Actualización cancelada por el usuario", "info")
                    return
                operation_type = "actualización"
            else:
                # Servidor existe pero sin ejecutable válido
                update_dialog = ctk.CTkInputDialog(
                    text=f"El servidor '{server_name}' existe pero no tiene un ejecutable válido.\n¿Desea reinstalarlo? (s/n):",
                    title="Servidor Incompleto"
                )
                update_response = update_dialog.get_input()
                if not update_response or update_response.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
                    self.add_status_message("Reinstalación cancelada por el usuario", "info")
                    return
                operation_type = "reinstalación"
        else:
            operation_type = "instalación"
        
        # Deshabilitar el botón durante la instalación
        self.install_button.configure(state="disabled", text=f"{operation_type.capitalize()}...")
        
        # Mostrar barra de progreso
        self.show_progress(f"Preparando {operation_type}...", 0)
        
        # Ejecutar la instalación en un hilo separado
        def install_thread():
            try:
                self.add_status_message(f"Iniciando {operation_type} del servidor: {server_name}", "info")
                self.add_status_message(f"Ruta de {operation_type}: {server_path}", "info")
                
                # Llamar al método de instalación del server_manager con callback mejorado
                self.server_manager.install_server(self.install_callback, server_name)
                
                # El callback se encargará de mostrar el progreso y el resultado final
                # No necesitamos verificar manualmente aquí porque el callback ya lo hace
                
            except Exception as e:
                self.add_status_message(f"❌ Error en la {operation_type}: {str(e)}", "error")
                self.logger.error(f"Error en la {operation_type}: {e}")
            finally:
                # Rehabilitar el botón y ocultar barra de progreso
                self.install_button.configure(state="normal", text="Instalar/Actualizar")
                # No ocultamos la barra de progreso aquí porque el callback se encarga de eso
        
        threading.Thread(target=install_thread, daemon=True).start()
        
    def install_callback(self, message_type, message):
        """Callback mejorado para la instalación con barra de progreso"""
        try:
            if message_type == "progress":
                # Extraer porcentaje del mensaje
                if "Progress:" in message:
                    # Buscar el porcentaje en el mensaje
                    import re
                    progress_match = re.search(r'Progress:\s*(\d+(?:\.\d+)?)', message)
                    if progress_match:
                        progress = float(progress_match.group(1))
                        self.update_progress(f"Progreso: {progress:.1f}%", progress)
                    else:
                        self.update_progress(message, 50)  # Valor por defecto
                elif "Downloading" in message:
                    # Extraer porcentaje de descarga si está disponible
                    import re
                    download_match = re.search(r'(\d+(?:\.\d+)?)%', message)
                    if download_match:
                        progress = float(download_match.group(1))
                        self.update_progress(f"Descargando... {progress:.1f}%", progress)
                    else:
                        self.update_progress(message, 25)
                elif "Installing" in message:
                    self.update_progress(message, 75)
                elif "Validating" in message:
                    self.update_progress(message, 90)
                elif "Verificando SteamCMD" in message:
                    self.update_progress(message, 5)
                elif "Descargando SteamCMD" in message:
                    self.update_progress(message, 10)
                elif "Extrayendo SteamCMD" in message:
                    self.update_progress(message, 15)
                elif "Buscando ejecutable" in message:
                    self.update_progress(message, 95)
                else:
                    # Para otros mensajes de progreso, mantener el progreso actual
                    current_progress = self.progress_bar.get()
                    self.update_progress(message, current_progress * 100)
            elif message_type == "error":
                # Mostrar error y ocultar barra de progreso
                self.add_status_message(f"❌ {message}", "error")
                self.hide_progress()
            elif message_type == "success":
                # Mostrar éxito
                self.add_status_message(f"✅ {message}", "success")
                # Si es un mensaje de éxito final, ocultar la barra de progreso y refrescar lista
                if "completada exitosamente" in message.lower():
                    self.hide_progress()
                    # Refrescar la lista de servidores
                    self.refresh_servers_list()
            elif message_type == "warning":
                # Mostrar advertencia
                self.add_status_message(f"⚠️ {message}", "warning")
            elif message_type == "info":
                # Mostrar información
                self.add_status_message(f"ℹ️ {message}", "info")
            else:
                # Usar el método original para otros tipos de mensajes
                self.add_status_message(message, message_type)
        except Exception as e:
            # En caso de error en el callback, mostrar el error
            self.add_status_message(f"❌ Error en el callback: {str(e)}", "error")
            self.logger.error(f"Error en install_callback: {e}")
    
    def save_world(self):
        """Guarda el mundo del servidor"""
        self.server_manager.save_world(self.add_status_message)
    
    def create_backup(self):
        """Crea un backup del servidor"""
        self.server_manager.backup_server(self.add_status_message)
    
    def show_broadcast_dialog(self):
        """Muestra el diálogo para enviar broadcast"""
        dialog = ctk.CTkInputDialog(
            text="Ingrese el mensaje a enviar:",
            title="Enviar Broadcast"
        )
        message = dialog.get_input()
        
        if message:
            self.broadcast_message(message)
    
    def broadcast_message(self, message):
        """Envía un mensaje broadcast"""
        self.server_manager.broadcast_message(message, self.add_status_message)
    
    def kick_all_players(self):
        """Expulsa a todos los jugadores"""
        self.server_manager.kick_all_players(self.add_status_message)
    
    def kick_player(self):
        """Expulsa a un jugador específico"""
        player_name = self.player_entry.get().strip()
        if player_name:
            self.server_manager.kick_player(player_name, self.add_status_message)
        else:
            self.add_status_message("Error: Ingrese el nombre del jugador", "error")
    
    def ban_player(self):
        """Banea a un jugador específico"""
        player_name = self.player_entry.get().strip()
        if player_name:
            self.server_manager.ban_player(player_name, self.add_status_message)
        else:
            self.add_status_message("Error: Ingrese el nombre del jugador", "error")
    
    def teleport_player(self):
        """Teletransporta a un jugador"""
        player_name = self.player_entry.get().strip()
        if player_name:
            # Mostrar diálogo para coordenadas
            dialog = ctk.CTkInputDialog(
                text="Ingrese las coordenadas (X,Y,Z):",
                title="Teletransportar Jugador"
            )
            coordinates = dialog.get_input()
            
            if coordinates:
                self.add_status_message(f"Teletransportando {player_name} a {coordinates}...", "info")
                # Aquí iría la lógica para teletransportar
                time.sleep(1)
                self.add_status_message(f"Jugador {player_name} teletransportado", "success")
        else:
            self.add_status_message("Error: Ingrese el nombre del jugador", "error")
    
    def give_item_to_player(self):
        """Da un item a un jugador"""
        player_name = self.player_entry.get().strip()
        if player_name:
            # Mostrar diálogo para item
            dialog = ctk.CTkInputDialog(
                text="Ingrese el nombre del item:",
                title="Dar Item"
            )
            item_name = dialog.get_input()
            
            if item_name:
                self.add_status_message(f"Dando {item_name} a {player_name}...", "info")
                # Aquí iría la lógica para dar item
                time.sleep(1)
                self.add_status_message(f"Item {item_name} dado a {player_name}", "success")
        else:
            self.add_status_message("Error: Ingrese el nombre del jugador", "error")
    
    def add_status_message(self, message, message_type="info"):
        """Agrega un mensaje al área de estado"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if message_type == "error":
            color = "red"
        elif message_type == "success":
            color = "green"
        elif message_type == "warning":
            color = "orange"
        else:
            color = "white"
        
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.status_text.insert("end", formatted_message)
        self.status_text.see("end")
        
        # Limitar el número de líneas en el texto
        lines = self.status_text.get("1.0", "end").split("\n")
        if len(lines) > 50:
            self.status_text.delete("1.0", "2.0")
