import customtkinter as ctk
import threading
import time
from datetime import datetime

class PlayersPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.players = []
        self.monitoring_active = False
        
        self.create_widgets()
        self.start_monitoring()
        
    def create_widgets(self):
        """Crear todos los widgets del panel"""
        # Título
        title_label = ctk.CTkLabel(
            self, 
            text="Gestión de Jugadores", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(20, 30))
        
        # Frame de estadísticas de jugadores
        stats_frame = ctk.CTkFrame(self)
        stats_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        stats_label = ctk.CTkLabel(
            stats_frame, 
            text="Estadísticas de Jugadores", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        stats_label.grid(row=0, column=0, columnspan=4, pady=10)
        
        # Estadísticas
        self.total_players_label = ctk.CTkLabel(stats_frame, text="Total: 0")
        self.total_players_label.grid(row=1, column=0, padx=20, pady=5)
        
        self.online_players_label = ctk.CTkLabel(stats_frame, text="En línea: 0")
        self.online_players_label.grid(row=1, column=1, padx=20, pady=5)
        
        self.max_players_label = ctk.CTkLabel(stats_frame, text="Máximo: 70")
        self.max_players_label.grid(row=1, column=2, padx=20, pady=5)
        
        self.server_capacity_label = ctk.CTkLabel(stats_frame, text="Capacidad: 0%")
        self.server_capacity_label.grid(row=1, column=3, padx=20, pady=5)
        
        # Frame de lista de jugadores
        players_frame = ctk.CTkFrame(self)
        players_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        players_label = ctk.CTkLabel(
            players_frame, 
            text="Jugadores Conectados", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        players_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Tabla de jugadores
        # Headers
        headers = ["Nombre", "Nivel", "Tiempo", "Acciones"]
        for i, header in enumerate(headers):
            header_label = ctk.CTkLabel(players_frame, text=header, font=ctk.CTkFont(weight="bold"))
            header_label.grid(row=1, column=i, padx=10, pady=5, sticky="w")
        
        # Lista de jugadores (placeholder)
        self.players_listbox = ctk.CTkTextbox(players_frame, height=300)
        self.players_listbox.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        self.players_listbox.insert("1.0", "No hay jugadores conectados")
        
        # Frame de acciones rápidas
        actions_frame = ctk.CTkFrame(self)
        actions_frame.grid(row=2, column=1, padx=20, pady=10, sticky="nsew")
        
        actions_label = ctk.CTkLabel(
            actions_frame, 
            text="Acciones Rápidas", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        actions_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Botones de acciones
        self.kick_all_button = ctk.CTkButton(
            actions_frame,
            text="Expulsar Todos",
            command=self.kick_all_players,
            fg_color="orange",
            hover_color="darkorange"
        )
        self.kick_all_button.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        self.save_world_button = ctk.CTkButton(
            actions_frame,
            text="Guardar Mundo",
            command=self.save_world
        )
        self.save_world_button.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        self.broadcast_button = ctk.CTkButton(
            actions_frame,
            text="Enviar Mensaje",
            command=self.send_broadcast
        )
        self.broadcast_button.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        # Frame de gestión de jugadores
        management_frame = ctk.CTkFrame(self)
        management_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        management_label = ctk.CTkLabel(
            management_frame, 
            text="Gestión de Jugadores", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        management_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Nombre del jugador
        player_name_label = ctk.CTkLabel(management_frame, text="Nombre del jugador:")
        player_name_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.player_name_entry = ctk.CTkEntry(management_frame, placeholder_text="Nombre del jugador")
        self.player_name_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Botones de gestión
        kick_button = ctk.CTkButton(
            management_frame,
            text="Expulsar",
            command=self.kick_player,
            fg_color="red",
            hover_color="darkred"
        )
        kick_button.grid(row=1, column=2, padx=5, pady=5)
        
        ban_button = ctk.CTkButton(
            management_frame,
            text="Banear",
            command=self.ban_player,
            fg_color="darkred",
            hover_color="red"
        )
        ban_button.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        teleport_button = ctk.CTkButton(
            management_frame,
            text="Teletransportar",
            command=self.teleport_player
        )
        teleport_button.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        give_item_button = ctk.CTkButton(
            management_frame,
            text="Dar Item",
            command=self.give_item
        )
        give_item_button.grid(row=2, column=2, padx=10, pady=5, sticky="ew")
        
        # Frame de controles
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=4, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        # Botones de control
        self.refresh_button = ctk.CTkButton(
            controls_frame,
            text="Actualizar Lista",
            command=self.refresh_players
        )
        self.refresh_button.grid(row=0, column=0, padx=10, pady=10)
        
        self.start_monitoring_button = ctk.CTkButton(
            controls_frame,
            text="Iniciar Monitoreo",
            command=self.start_monitoring,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.start_monitoring_button.grid(row=0, column=1, padx=10, pady=10)
        
        self.stop_monitoring_button = ctk.CTkButton(
            controls_frame,
            text="Detener Monitoreo",
            command=self.stop_monitoring,
            fg_color="red",
            hover_color="darkred"
        )
        self.stop_monitoring_button.grid(row=0, column=2, padx=10, pady=10)
        
        # Configurar grid
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        players_frame.grid_columnconfigure(0, weight=1)
        players_frame.grid_columnconfigure(1, weight=1)
        players_frame.grid_columnconfigure(2, weight=1)
        players_frame.grid_columnconfigure(3, weight=1)
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)
        management_frame.grid_columnconfigure(1, weight=1)
        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(1, weight=1)
        controls_frame.grid_columnconfigure(2, weight=1)
        
    def start_monitoring(self):
        """Iniciar monitoreo de jugadores"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.start_monitoring_button.configure(state="disabled")
            self.stop_monitoring_button.configure(state="normal")
            
            # Iniciar hilo de monitoreo
            threading.Thread(target=self.monitoring_loop, daemon=True).start()
            self.logger.info("Monitoreo de jugadores iniciado")
    
    def stop_monitoring(self):
        """Detener monitoreo de jugadores"""
        self.monitoring_active = False
        self.start_monitoring_button.configure(state="normal")
        self.stop_monitoring_button.configure(state="disabled")
        self.logger.info("Monitoreo de jugadores detenido")
    
    def monitoring_loop(self):
        """Bucle principal de monitoreo de jugadores"""
        while self.monitoring_active:
            try:
                self.update_players_list()
                time.sleep(5)  # Actualizar cada 5 segundos
            except Exception as e:
                self.logger.error(f"Error en monitoreo de jugadores: {e}")
                break
    
    def update_players_list(self):
        """Actualizar lista de jugadores"""
        try:
            # Simular datos de jugadores (en una implementación real, leería logs del servidor)
            self.players = [
                {"name": "Player1", "level": 45, "time": "2h 30m", "online": True},
                {"name": "Player2", "level": 32, "time": "1h 15m", "online": True},
                {"name": "Player3", "level": 67, "time": "4h 20m", "online": False}
            ]
            
            # Actualizar estadísticas
            online_count = len([p for p in self.players if p["online"]])
            total_count = len(self.players)
            max_players = 70
            capacity = (online_count / max_players) * 100
            
            self.total_players_label.configure(text=f"Total: {total_count}")
            self.online_players_label.configure(text=f"En línea: {online_count}")
            self.max_players_label.configure(text=f"Máximo: {max_players}")
            self.server_capacity_label.configure(text=f"Capacidad: {capacity:.1f}%")
            
            # Actualizar lista
            self.players_listbox.delete("1.0", "end")
            if online_count > 0:
                for player in self.players:
                    if player["online"]:
                        self.players_listbox.insert("end", 
                            f"{player['name']:<15} {player['level']:<8} {player['time']:<10} [Kick] [Ban]\n")
            else:
                self.players_listbox.insert("1.0", "No hay jugadores conectados")
                
        except Exception as e:
            self.logger.error(f"Error al actualizar lista de jugadores: {e}")
    
    def refresh_players(self):
        """Actualizar lista de jugadores manualmente"""
        self.update_players_list()
        self.logger.info("Lista de jugadores actualizada manualmente")
    
    def kick_all_players(self):
        """Expulsar a todos los jugadores"""
        try:
            # Aquí se implementaría el comando para expulsar a todos
            self.logger.info("Expulsando a todos los jugadores")
            # Comando: kickall
        except Exception as e:
            self.logger.error(f"Error al expulsar jugadores: {e}")
    
    def save_world(self):
        """Guardar el mundo"""
        try:
            # Aquí se implementaría el comando para guardar el mundo
            self.logger.info("Guardando mundo")
            # Comando: saveworld
        except Exception as e:
            self.logger.error(f"Error al guardar mundo: {e}")
    
    def send_broadcast(self):
        """Enviar mensaje a todos los jugadores"""
        try:
            # Crear ventana de diálogo para el mensaje
            dialog = ctk.CTkInputDialog(
                text="Ingrese el mensaje a enviar:",
                title="Enviar Mensaje"
            )
            message = dialog.get_input()
            
            if message:
                self.logger.info(f"Enviando mensaje: {message}")
                # Comando: broadcast "mensaje"
        except Exception as e:
            self.logger.error(f"Error al enviar mensaje: {e}")
    
    def kick_player(self):
        """Expulsar jugador específico"""
        try:
            player_name = self.player_name_entry.get()
            if player_name:
                self.logger.info(f"Expulsando jugador: {player_name}")
                # Comando: kick "nombre"
            else:
                self.logger.warning("Debe especificar un nombre de jugador")
        except Exception as e:
            self.logger.error(f"Error al expulsar jugador: {e}")
    
    def ban_player(self):
        """Banear jugador específico"""
        try:
            player_name = self.player_name_entry.get()
            if player_name:
                self.logger.info(f"Baneando jugador: {player_name}")
                # Comando: ban "nombre"
            else:
                self.logger.warning("Debe especificar un nombre de jugador")
        except Exception as e:
            self.logger.error(f"Error al banear jugador: {e}")
    
    def teleport_player(self):
        """Teletransportar jugador"""
        try:
            player_name = self.player_name_entry.get()
            if player_name:
                # Crear ventana de diálogo para coordenadas
                dialog = ctk.CTkInputDialog(
                    text="Ingrese las coordenadas (X Y Z):",
                    title="Teletransportar Jugador"
                )
                coords = dialog.get_input()
                
                if coords:
                    self.logger.info(f"Teletransportando {player_name} a {coords}")
                    # Comando: teleport "nombre" X Y Z
            else:
                self.logger.warning("Debe especificar un nombre de jugador")
        except Exception as e:
            self.logger.error(f"Error al teletransportar jugador: {e}")
    
    def give_item(self):
        """Dar item a jugador"""
        try:
            player_name = self.player_name_entry.get()
            if player_name:
                # Crear ventana de diálogo para item
                dialog = ctk.CTkInputDialog(
                    text="Ingrese el ID del item y cantidad:",
                    title="Dar Item"
                )
                item_info = dialog.get_input()
                
                if item_info:
                    self.logger.info(f"Dando item a {player_name}: {item_info}")
                    # Comando: giveitem "nombre" ID cantidad
            else:
                self.logger.warning("Debe especificar un nombre de jugador")
        except Exception as e:
            self.logger.error(f"Error al dar item: {e}")
