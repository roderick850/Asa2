#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PlayerMonitor - Sistema de monitoreo de jugadores en línea

Este módulo proporciona funcionalidad para:
- Monitorear logs del servidor ARK para detectar eventos de join/left
- Mantener conteo en tiempo real de jugadores en línea
- Notificar cambios de estado de jugadores
- Soportar múltiples servidores
"""

import os
import re
import threading
import time
from datetime import datetime
from typing import Dict, List, Callable, Optional, Set
from dataclasses import dataclass

@dataclass
class PlayerEvent:
    """Representa un evento de jugador (join/left)"""
    timestamp: datetime
    player_name: str
    unique_id: str
    platform: str
    event_type: str  # 'joined' or 'left'
    server_name: str

class PlayerMonitor:
    """Monitor de jugadores en línea basado en logs del servidor"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.monitoring = False
        self.monitor_thread = None
        
        # Diccionario de servidores monitoreados: {server_name: config}
        self.monitored_servers = {}
        
        # Jugadores en línea por servidor: {server_name: {player_name: PlayerEvent}}
        self.online_players = {}
        
        # Callbacks para notificaciones
        self.player_join_callbacks = []
        self.player_left_callbacks = []
        self.player_count_callbacks = []
        
        # Patrones regex para detectar eventos
        # Formato: [16:24:46] [16:24:46] [2025.08.19-19.24.45:849][105]2025.08.19_19.24.45: Roderick850 [UniqueNetId:000288e061254539979667bfc309d848 Platform:None] joined this ARK!
        self.join_pattern = re.compile(
            r'\[\d{2}:\d{2}:\d{2}\]\s*\[\d{2}:\d{2}:\d{2}\].*?:\s*(\w+)\s+\[UniqueNetId:([a-f0-9]+)\s+Platform:(\w+|None)\]\s+joined this ARK!'
        )
        self.left_pattern = re.compile(
            r'\[\d{2}:\d{2}:\d{2}\]\s*\[\d{2}:\d{2}:\d{2}\].*?:\s*(\w+)\s+\[UniqueNetId:([a-f0-9]+)\s+Platform:(\w+|None)\]\s+left this ARK!'
        )
        
        # Posiciones de archivo para cada servidor
        self.file_positions = {}
        
    def add_server(self, server_name: str, log_path: str, enabled: bool = True):
        """Agregar servidor para monitoreo"""
        self.monitored_servers[server_name] = {
            'log_path': log_path,
            'enabled': enabled,
            'last_modified': 0
        }
        
        if server_name not in self.online_players:
            self.online_players[server_name] = {}
            
        if server_name not in self.file_positions:
            self.file_positions[server_name] = 0
            
        if self.logger:
            self.logger.info(f"Servidor agregado al monitoreo de jugadores: {server_name}")
    
    def remove_server(self, server_name: str):
        """Remover servidor del monitoreo"""
        if server_name in self.monitored_servers:
            del self.monitored_servers[server_name]
        if server_name in self.online_players:
            del self.online_players[server_name]
        if server_name in self.file_positions:
            del self.file_positions[server_name]
            
        if self.logger:
            self.logger.info(f"Servidor removido del monitoreo de jugadores: {server_name}")
    
    def enable_server(self, server_name: str, enabled: bool = True):
        """Habilitar/deshabilitar monitoreo de un servidor"""
        if server_name in self.monitored_servers:
            self.monitored_servers[server_name]['enabled'] = enabled
            
    def add_player_join_callback(self, callback: Callable[[PlayerEvent], None]):
        """Agregar callback para eventos de join"""
        self.player_join_callbacks.append(callback)
        
    def add_player_left_callback(self, callback: Callable[[PlayerEvent], None]):
        """Agregar callback para eventos de left"""
        self.player_left_callbacks.append(callback)
        
    def add_player_count_callback(self, callback: Callable[[str, int], None]):
        """Agregar callback para cambios en el conteo de jugadores"""
        self.player_count_callbacks.append(callback)
    
    def register_callback(self, event_type: str, callback: Callable):
        """Registrar callback para eventos específicos"""
        if event_type == 'join':
            self.add_player_join_callback(callback)
        elif event_type == 'left':
            self.add_player_left_callback(callback)
        elif event_type == 'count_changed':
            self.add_player_count_callback(callback)
        else:
            if self.logger:
                self.logger.warning(f"Tipo de evento desconocido: {event_type}")
    
    def get_online_players_count(self, server_name: str = None) -> int:
        """Obtener conteo de jugadores en línea"""
        if server_name:
            return len(self.online_players.get(server_name, {}))
        else:
            # Conteo total de todos los servidores
            total = 0
            for players in self.online_players.values():
                total += len(players)
            return total
    
    def get_online_players_list(self, server_name: str) -> List[str]:
        """Obtener lista de nombres de jugadores en línea"""
        return list(self.online_players.get(server_name, {}).keys())
    
    def get_all_online_players(self) -> Dict[str, List[str]]:
        """Obtener todos los jugadores en línea por servidor"""
        result = {}
        for server_name, players in self.online_players.items():
            result[server_name] = list(players.keys())
        return result
    
    def start_monitoring(self):
        """Iniciar monitoreo de logs"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        if self.logger:
            self.logger.info("Monitoreo de jugadores iniciado")
    
    def stop_monitoring(self):
        """Detener monitoreo de logs"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
            
        if self.logger:
            self.logger.info("Monitoreo de jugadores detenido")
    
    def _monitor_loop(self):
        """Loop principal de monitoreo"""
        while self.monitoring:
            try:
                for server_name, config in self.monitored_servers.items():
                    if not config['enabled']:
                        continue
                        
                    self._check_server_log(server_name, config)
                    
                time.sleep(1)  # Verificar cada segundo
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error en loop de monitoreo de jugadores: {e}")
                time.sleep(5)  # Esperar más tiempo si hay error
    
    def _check_server_log(self, server_name: str, config: dict):
        """Verificar log de un servidor específico"""
        log_path = config['log_path']
        
        if not os.path.exists(log_path):
            return
            
        try:
            # Verificar si el archivo ha sido modificado
            current_mtime = os.path.getmtime(log_path)
            if current_mtime <= config['last_modified']:
                return
                
            config['last_modified'] = current_mtime
            
            # Leer nuevas líneas desde la última posición
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(self.file_positions.get(server_name, 0))
                new_lines = f.readlines()
                self.file_positions[server_name] = f.tell()
                
            # Procesar nuevas líneas
            for line in new_lines:
                self._process_log_line(server_name, line.strip())
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error leyendo log de {server_name}: {e}")
    
    def process_log_line(self, server_name: str, line: str):
        """Procesar una línea del log (método público)"""
        self._process_log_line(server_name, line)
    
    def _process_log_line(self, server_name: str, line: str):
        """Procesar una línea del log"""
        # Buscar eventos de join
        join_match = self.join_pattern.search(line)
        if join_match:
            player_name, unique_id, platform = join_match.groups()
            # Usar timestamp actual ya que el formato del log es complejo
            timestamp_str = datetime.now().strftime('%H:%M:%S')
            self._handle_player_join(server_name, timestamp_str, player_name, unique_id, platform)
            return
            
        # Buscar eventos de left
        left_match = self.left_pattern.search(line)
        if left_match:
            player_name, unique_id, platform = left_match.groups()
            # Usar timestamp actual ya que el formato del log es complejo
            timestamp_str = datetime.now().strftime('%H:%M:%S')
            self._handle_player_left(server_name, timestamp_str, player_name, unique_id, platform)
            return
    
    def _handle_player_join(self, server_name: str, timestamp_str: str, player_name: str, unique_id: str, platform: str):
        """Manejar evento de jugador que se une"""
        try:
            # Crear timestamp (usar fecha actual con hora del log)
            today = datetime.now().date()
            time_obj = datetime.strptime(timestamp_str, '%H:%M:%S').time()
            timestamp = datetime.combine(today, time_obj)
            
            # Crear evento
            event = PlayerEvent(
                timestamp=timestamp,
                player_name=player_name,
                unique_id=unique_id,
                platform=platform,
                event_type='joined',
                server_name=server_name
            )
            
            # Agregar jugador a la lista de en línea
            if server_name not in self.online_players:
                self.online_players[server_name] = {}
                
            self.online_players[server_name][player_name] = event
            
            # Notificar callbacks
            for callback in self.player_join_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error en callback de join: {e}")
            
            # Notificar cambio de conteo
            count = len(self.online_players[server_name])
            for callback in self.player_count_callbacks:
                try:
                    callback(server_name, count)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error en callback de conteo: {e}")
            
            if self.logger:
                self.logger.info(f"Jugador se unió a {server_name}: {player_name} (Total: {count})")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error procesando join de {player_name}: {e}")
    
    def _handle_player_left(self, server_name: str, timestamp_str: str, player_name: str, unique_id: str, platform: str):
        """Manejar evento de jugador que se va"""
        try:
            # Crear timestamp
            today = datetime.now().date()
            time_obj = datetime.strptime(timestamp_str, '%H:%M:%S').time()
            timestamp = datetime.combine(today, time_obj)
            
            # Crear evento
            event = PlayerEvent(
                timestamp=timestamp,
                player_name=player_name,
                unique_id=unique_id,
                platform=platform,
                event_type='left',
                server_name=server_name
            )
            
            # Remover jugador de la lista de en línea
            if server_name in self.online_players and player_name in self.online_players[server_name]:
                del self.online_players[server_name][player_name]
            
            # Notificar callbacks
            for callback in self.player_left_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error en callback de left: {e}")
            
            # Notificar cambio de conteo
            count = len(self.online_players.get(server_name, {}))
            for callback in self.player_count_callbacks:
                try:
                    callback(server_name, count)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error en callback de conteo: {e}")
            
            if self.logger:
                self.logger.info(f"Jugador se fue de {server_name}: {player_name} (Total: {count})")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error procesando left de {player_name}: {e}")
    
    def reset_server_players(self, server_name: str):
        """Resetear conteo de jugadores de un servidor (útil cuando se reinicia)"""
        if server_name in self.online_players:
            self.online_players[server_name] = {}
            
            # Notificar cambio de conteo
            for callback in self.player_count_callbacks:
                try:
                    callback(server_name, 0)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error en callback de conteo: {e}")
    
    def get_player_count(self, server_name: str) -> int:
        """Obtener conteo de jugadores de un servidor específico"""
        return len(self.online_players.get(server_name, {}))
    
    def get_all_servers(self) -> List[str]:
        """Obtener lista de todos los servidores monitoreados"""
        return list(self.monitored_servers.keys())
    
    def get_server_log_path(self, server_name: str) -> Optional[str]:
        """Obtener ruta del log de un servidor"""
        config = self.monitored_servers.get(server_name)
        return config['log_path'] if config else None
    
    def is_monitoring_server(self, server_name: str) -> bool:
        """Verificar si un servidor está siendo monitoreado"""
        config = self.monitored_servers.get(server_name)
        return config is not None and config['enabled']