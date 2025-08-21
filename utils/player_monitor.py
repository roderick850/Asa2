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
from .game_alerts_manager import GameAlertsManager

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
    
    def __init__(self, logger=None, rcon_panel=None):
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
        
        # Guardar referencia al rcon_panel para acceder a su GameAlertsManager
        self.rcon_panel = rcon_panel
        self.logger = logger
        
        # GameAlertsManager se obtiene dinámicamente del rcon_panel cuando se necesite
        self.game_alerts = None
        
        # Patrones regex actualizados para detectar eventos (más flexibles)
        self.join_pattern = re.compile(
            r'(?:\[\d{2}:\d{2}:\d{2}\]\s*\[\d{2}:\d{2}:\d{2}\].*?:|\d{4}\.\d{2}\.\d{2}_\d{2}\.\d{2}\.\d{2}:)\s*(\w+)\s+\[UniqueNetId:([a-f0-9]+)\s+Platform:(\w+|None)\]\s+joined this ARK!'
        )
        self.left_pattern = re.compile(
            r'(?:\[\d{2}:\d{2}:\d{2}\]\s*\[\d{2}:\d{2}:\d{2}\].*?:|\d{4}\.\d{2}\.\d{2}_\d{2}\.\d{2}\.\d{2}:)\s*(\w+)\s+\[UniqueNetId:([a-f0-9]+)\s+Platform:(\w+|None)\]\s+left this ARK!'
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
            
        # NUEVO: Procesar todo el log al agregar el servidor
        if enabled:
            self._process_full_log_on_startup(server_name, log_path)
            
        if self.logger:
            self.logger.info(f"Servidor agregado al monitoreo de jugadores: {server_name}")
    
    def _process_full_log_on_startup(self, server_name: str, log_path: str):
        """Procesar todo el archivo de log al inicio para reconstruir el estado actual"""
        if not os.path.exists(log_path):
            if self.logger:
                self.logger.warning(f"Archivo de log no encontrado: {log_path}")
            return
            
        try:
            if self.logger:
                self.logger.info(f"Procesando log completo para {server_name}: {log_path}")
            
            # Leer todo el archivo
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            if not lines:
                if self.logger:
                    self.logger.info(f"Archivo de log vacío para {server_name}")
                return
                
            # Procesar todas las líneas para reconstruir el estado
            join_events = {}
            left_events = {}
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                    
                # Buscar eventos de join
                join_match = self.join_pattern.search(line)
                if join_match:
                    player_name, unique_id, platform = join_match.groups()
                    join_events[player_name] = {
                        'unique_id': unique_id,
                        'platform': platform,
                        'line_num': line_num,
                        'line': line
                    }
                    continue
                    
                # Buscar eventos de left
                left_match = self.left_pattern.search(line)
                if left_match:
                    player_name, unique_id, platform = left_match.groups()
                    left_events[player_name] = {
                        'unique_id': unique_id,
                        'platform': platform,
                        'line_num': line_num,
                        'line': line
                    }
            
            # Determinar jugadores actualmente conectados
            # Un jugador está conectado si su último evento fue 'join'
            currently_online = {}
            
            for player_name in join_events:
                join_line = join_events[player_name]['line_num']
                left_line = left_events.get(player_name, {}).get('line_num', 0)
                
                # Si el join es más reciente que el left (o no hay left), está conectado
                if join_line > left_line:
                    currently_online[player_name] = join_events[player_name]
            
            # Limpiar jugadores actuales del servidor
            self.online_players[server_name] = {}
            
            # Agregar jugadores que están actualmente conectados
            for player_name, player_data in currently_online.items():
                timestamp = datetime.now()  # Usar timestamp actual
                event = PlayerEvent(
                    timestamp=timestamp,
                    player_name=player_name,
                    unique_id=player_data['unique_id'],
                    platform=player_data['platform'],
                    event_type='joined',
                    server_name=server_name
                )
                self.online_players[server_name][player_name] = event
            
            # Establecer posición del archivo al final para monitoreo futuro
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(0, 2)  # Ir al final del archivo
                self.file_positions[server_name] = f.tell()
            
            player_count = len(currently_online)
            if self.logger:
                self.logger.info(f"Procesamiento completo terminado para {server_name}: {player_count} jugadores conectados")
                if currently_online:
                    player_names = list(currently_online.keys())
                    self.logger.info(f"Jugadores conectados: {', '.join(player_names)}")
            
            # Notificar callbacks del conteo inicial
            for callback in self.player_count_callbacks:
                try:
                    callback(server_name, player_count)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error en callback de conteo inicial: {e}")
                        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error procesando log completo de {server_name}: {e}")
    
    def start_monitoring(self):
        """Iniciar monitoreo de logs"""
        if self.monitoring:
            return
            
        # NUEVO: Procesar logs completos de todos los servidores habilitados al iniciar
        for server_name, config in self.monitored_servers.items():
            if config['enabled']:
                self._process_full_log_on_startup(server_name, config['log_path'])
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        if self.logger:
            self.logger.info("Monitoreo de jugadores iniciado")
    
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
        # Procesar línea para alertas del juego usando el GameAlertsManager del rcon_panel
        if (self.rcon_panel and 
            hasattr(self.rcon_panel, 'game_alerts') and 
            self.rcon_panel.game_alerts):
            self.rcon_panel.game_alerts.process_log_line(server_name, line)
        
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