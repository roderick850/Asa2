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
                
        except Exception as e:
            self.logger.error(f"Error al actualizar información del servidor: {e}")
    
    def start_server(self):
        """Inicia el servidor"""
        self.server_manager.start_server(self.add_status_message)
    
    def stop_server(self):
        """Detiene el servidor"""
        self.server_manager.stop_server(self.add_status_message)
    
    def restart_server(self):
        """Reinicia el servidor"""
        self.server_manager.restart_server(self.add_status_message)
    
    def install_server(self):
        """Instala/actualiza el servidor"""
        self.server_manager.install_server(self.add_status_message)
    
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
