import re
import json
import os
from datetime import datetime
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass

@dataclass
class GameEvent:
    timestamp: datetime
    event_type: str  # 'player_join', 'player_leave', 'player_death', 'dino_death'
    player_name: str
    character_name: str
    unique_id: str
    details: Dict  # Información adicional específica del evento
    server_name: str

class GameAlertsManager:
    def __init__(self, logger=None, rcon_panel=None):
        self.logger = logger
        self.rcon_panel = rcon_panel
        
        # Mapeo de UniqueNetId a nombres de personajes
        self.player_character_map = {}  # {unique_id: {'player_name': str, 'character_name': str}}
        
        # Configuración de alertas
        self.alert_config = {
            'player_join': {
                'enabled': True,
                'message': '{character_name} se ha conectado al servidor',
                'color': 'green'
            },
            'player_leave': {
                'enabled': True,
                'message': '{character_name} se ha desconectado del servidor',
                'color': 'red'
            },
            'player_death': {
                'enabled': True,
                'message': '{character_name} fue eliminado por {killer}',
                'color': 'yellow'
            },
            'dino_death': {
                'enabled': True,
                'message': '{dino_name} de {owner} fue eliminado por {killer}',
                'color': 'orange'
            },
            'dino_taming': {
                'enabled': True,
                'message': '{character_name} ha tameado un {dino_name} - Nivel {dino_level}',
                'color': 'blue'
            }
        }
        
        # Patrones regex para detectar eventos
        self.patterns = {
            # Patrón para conexión: Roderick850 [UniqueNetId:000288e061254539979667bfc309d848 Platform:None] joined this ARK!
            'player_join': re.compile(
                r'(\w+)\s+\[UniqueNetId:([a-f0-9]+)\s+Platform:(\w+|None)\]\s+joined this ARK!'
            ),
            
            # Patrón para desconexión: Roderick850 [UniqueNetId:000288e061254539979667bfc309d848 Platform:None] left this ARK!
            'player_leave': re.compile(
                r'(\w+)\s+\[UniqueNetId:([a-f0-9]+)\s+Platform:(\w+|None)\]\s+left this ARK!'
            ),
            
            # Patrón para muerte de jugador: Humano - Lvl 61 () was killed by a Shadowmane - Lvl 55 ()!
            'player_death': re.compile(
                r'(\d{4}\.\d{2}\.\d{2}_\d{2}\.\d{2}\.\d{2}):\s*([^-]+)\s*-\s*Lvl\s*(\d+)\s*\([^)]*\)\s*was killed by\s*(.+?)\s*-\s*Lvl\s*(\d+)\s*\([^)]*\)!'
            ),
            
            # Patrón para muerte de dino: Parasaur - Lvl 66 (Parasaur) () was killed by a Shadowmane - Lvl 55 ()!
            'dino_death': re.compile(
                r'(\d{4}\.\d{2}\.\d{2}_\d{2}\.\d{2}\.\d{2}):\s*([^-]+)\s*-\s*Lvl\s*(\d+)\s*\(([^)]+)\)\s*\([^)]*\)\s*was killed by\s*(.+?)\s*-\s*Lvl\s*(\d+)\s*\([^)]*\)!'
            ),
            
            # Patrón para mapear jugador con personaje: Player: Humano (000288e061254539979667bfc309d848) [535856928]
            'player_character_map': re.compile(
                r'Player:\s*([^(]+)\s*\(([a-f0-9]+)\)\s*\[\d+\]'
            ),
            
            # Patrón para tameo: Humano of Tribe  Tamed a Castoroides - Lvl 7 (Castoroides)!
            'dino_taming': re.compile(
                r'(\d{4}\.\d{2}\.\d{2}_\d{2}\.\d{2}\.\d{2}):\s*([^\s]+)\s+of Tribe\s+.*?Tamed a\s+([^-]+)\s*-\s*Lvl\s*(\d+)\s*\(([^)]+)\)!'
            ),
        }
        
        # Archivo de configuración
        self.config_file = 'data/game_alerts_config.json'
        self.player_map_file = 'data/player_character_map.json'
        
        # Cargar configuración
        self.load_config()
        self.load_player_map()
    
    def process_log_line(self, server_name: str, line: str):
        """Procesar una línea del log para detectar eventos del juego"""
        try:
            # Verificar mapeo de jugador-personaje primero
            map_match = self.patterns['player_character_map'].search(line)
            if map_match:
                character_name = map_match.group(1).strip()
                unique_id = map_match.group(2)
                self.update_player_character_map(unique_id, character_name)
                return
            
            # Verificar conexión de jugador
            join_match = self.patterns['player_join'].search(line)
            if join_match:
                player_name, unique_id, platform = join_match.groups()
                character_name = self.get_character_name(unique_id, player_name)
                
                event = GameEvent(
                    timestamp=datetime.now(),
                    event_type='player_join',
                    player_name=player_name,
                    character_name=character_name,
                    unique_id=unique_id,
                    details={'platform': platform},
                    server_name=server_name
                )
                self._handle_event(event)
                return
            
            # Verificar desconexión de jugador
            leave_match = self.patterns['player_leave'].search(line)
            if leave_match:
                player_name, unique_id, platform = leave_match.groups()
                character_name = self.get_character_name(unique_id, player_name)
                
                event = GameEvent(
                    timestamp=datetime.now(),
                    event_type='player_leave',
                    player_name=player_name,
                    character_name=character_name,
                    unique_id=unique_id,
                    details={'platform': platform},
                    server_name=server_name
                )
                self._handle_event(event)
                return
            
            # Verificar muerte de jugador
            player_death_match = self.patterns['player_death'].search(line)
            if player_death_match:
                timestamp_str, victim_name, victim_level, killer_name, killer_level = player_death_match.groups()
                
                event = GameEvent(
                    timestamp=self._parse_timestamp(timestamp_str),
                    event_type='player_death',
                    player_name='',  # No tenemos el player_name en este log
                    character_name=victim_name.strip(),
                    unique_id='',  # No tenemos unique_id en este log
                    details={
                        'victim_level': victim_level,
                        'killer': killer_name.strip(),
                        'killer_level': killer_level
                    },
                    server_name=server_name
                )
                self._handle_event(event)
                return
            
            # Verificar muerte de dino
            dino_death_match = self.patterns['dino_death'].search(line)
            if dino_death_match:
                timestamp_str, dino_name, dino_level, dino_type, killer_name, killer_level = dino_death_match.groups()
                
                event = GameEvent(
                    timestamp=self._parse_timestamp(timestamp_str),
                    event_type='dino_death',
                    player_name='',
                    character_name='',
                    unique_id='',
                    details={
                        'dino_name': dino_name.strip(),
                        'dino_type': dino_type,
                        'dino_level': dino_level,
                        'killer': killer_name.strip(),
                        'killer_level': killer_level,
                        'owner': 'Desconocido'  # No podemos determinar el dueño del dino desde el log
                    },
                    server_name=server_name
                )
                self._handle_event(event)
                return
            
            # Verificar tameo de dino
            taming_match = self.patterns['dino_taming'].search(line)
            if taming_match:
                player_name, dino_name, dino_level, dino_type = taming_match.groups()
                
                event = GameEvent(
                    timestamp=datetime.now(),
                    event_type='dino_taming',
                    player_name=player_name,
                    character_name=player_name,
                    unique_id='',
                    details={
                        'dino_name': dino_name.strip(),
                        'dino_level': dino_level,
                        'dino_type': dino_type
                    },
                    server_name=server_name
                )
                self._handle_event(event)
                return
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error procesando línea de log para alertas: {e}")
    
    def update_player_character_map(self, unique_id: str, character_name: str, player_name: str = ''):
        """Actualizar el mapeo entre UniqueNetId y nombre de personaje"""
        if unique_id not in self.player_character_map:
            self.player_character_map[unique_id] = {}
        
        self.player_character_map[unique_id]['character_name'] = character_name
        if player_name:
            self.player_character_map[unique_id]['player_name'] = player_name
        
        self.save_player_map()
        
        if self.logger:
            self.logger.info(f"Mapeado jugador: {unique_id} -> {character_name}")
    
    def get_character_name(self, unique_id: str, fallback_name: str = '') -> str:
        """Obtener el nombre del personaje basado en el UniqueNetId"""
        if unique_id in self.player_character_map:
            return self.player_character_map[unique_id].get('character_name', fallback_name)
        return fallback_name
    
    def _handle_event(self, event: GameEvent):
        """Manejar un evento del juego"""
        if not self.alert_config[event.event_type]['enabled']:
            return
        
        # Generar mensaje de alerta
        message = self._generate_alert_message(event)
        
        # Enviar alerta por RCON
        self._send_rcon_alert(message, event.event_type)
        
        if self.logger:
            self.logger.info(f"Alerta enviada: {event.event_type} - {message}")
    
    def _generate_alert_message(self, event: GameEvent) -> str:
        """Generar mensaje de alerta basado en el evento"""
        template = self.alert_config[event.event_type]['message']
        
        if event.event_type in ['player_join', 'player_leave']:
            return template.format(
                character_name=event.character_name or event.player_name,
                player_name=event.player_name
            )
        elif event.event_type == 'player_death':
            return template.format(
                character_name=event.character_name,
                killer=event.details.get('killer', 'Desconocido')
            )
        elif event.event_type == 'dino_death':
            return template.format(
                dino_name=event.details.get('dino_name', 'Dino'),
                owner=event.details.get('owner', 'Desconocido'),
                killer=event.details.get('killer', 'Desconocido')
            )
        
        return template
    
    def _send_rcon_alert(self, message: str, event_type: str):
        """Enviar alerta por RCON"""
        if not self.rcon_panel:
            return
        
        try:
            # Obtener el tipo de mensaje configurado (serverchat o broadcast)
            message_type = self.rcon_panel.get_message_type()
            
            # Construir comando RCON con colores
            color = self.alert_config[event_type]['color']
            colored_message = self._add_color_to_message(message, color)
            
            if message_type == 'serverchat':
                command = f'serverchat {colored_message}'
            else:
                command = f'broadcast {colored_message}'
            
            # Ejecutar comando RCON
            self.rcon_panel.execute_rcon_command(command)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error enviando alerta RCON: {e}")
    
    def _add_color_to_message(self, message: str, color: str) -> str:
        """Aplicar color al mensaje - simplificado sin códigos de color"""
        # Retornar el mensaje sin modificaciones ya que los prefijos están incluidos
        return message
        color_codes = {
            'red': '<RichColor Color="1,0,0,1">',
            'green': '<RichColor Color="0,1,0,1">',
            'blue': '<RichColor Color="0,0,1,1">',
            'yellow': '<RichColor Color="1,1,0,1">',
            'orange': '<RichColor Color="1,0.5,0,1">',
            'purple': '<RichColor Color="1,0,1,1">',
            'white': '<RichColor Color="1,1,1,1">'
        }
        
        if color in color_codes:
            return f'{color_codes[color]}{message}</RichColor>'
        return message
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parsear timestamp del formato del log"""
        try:
            return datetime.strptime(timestamp_str, '%Y.%m.%d_%H.%M.%S')
        except:
            return datetime.now()
    
    def set_alert_enabled(self, event_type: str, enabled: bool):
        """Habilitar/deshabilitar un tipo de alerta"""
        if event_type in self.alert_config:
            self.alert_config[event_type]['enabled'] = enabled
            self.save_config()
    
    def set_alert_message(self, event_type: str, message: str):
        """Configurar mensaje personalizado para un tipo de alerta"""
        if event_type in self.alert_config:
            self.alert_config[event_type]['message'] = message
            self.save_config()
    
    def set_alert_color(self, event_type: str, color: str):
        """Configurar color para un tipo de alerta"""
        if event_type in self.alert_config:
            self.alert_config[event_type]['color'] = color
            self.save_config()
    
    def get_alert_config(self) -> Dict:
        """Obtener configuración actual de alertas"""
        return self.alert_config.copy()
    
    def update_config(self, config: Dict):
        """Actualizar configuración de alertas desde el panel RCON"""
        try:
            # Mapear los nombres de configuración del panel a los tipos de eventos
            config_mapping = {
                'connection_alerts': 'player_join',
                'disconnection_alerts': 'player_leave', 
                'player_death_alerts': 'player_death',
                'dino_death_alerts': 'dino_death'
            }
            
            color_mapping = {
                'connection_color': 'player_join',
                'disconnection_color': 'player_leave',
                'death_color': 'player_death'
            }
            
            # Actualizar estados de alertas
            for config_key, event_type in config_mapping.items():
                if config_key in config and event_type in self.alert_config:
                    self.alert_config[event_type]['enabled'] = config[config_key]
            
            # Actualizar colores
            for color_key, event_type in color_mapping.items():
                if color_key in config and event_type in self.alert_config:
                    color_value = config[color_key].lower()
                    self.alert_config[event_type]['color'] = color_value
            
            # También aplicar color de muerte a dino_death si no se especifica por separado
            if 'death_color' in config:
                death_color = config['death_color'].lower()
                self.alert_config['dino_death']['color'] = death_color
            
            # Guardar configuración actualizada
            self.save_config()
            
            if self.logger:
                self.logger.info("Configuración de alertas actualizada correctamente")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error actualizando configuración de alertas: {e}")
    
    def save_config(self):
        """Guardar configuración de alertas"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.alert_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error guardando configuración de alertas: {e}")
    
    def load_config(self):
        """Cargar configuración de alertas"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Actualizar solo las claves existentes
                    for key, value in loaded_config.items():
                        if key in self.alert_config:
                            self.alert_config[key].update(value)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error cargando configuración de alertas: {e}")
    
    def save_player_map(self):
        """Guardar mapeo de jugadores"""
        try:
            os.makedirs(os.path.dirname(self.player_map_file), exist_ok=True)
            with open(self.player_map_file, 'w', encoding='utf-8') as f:
                json.dump(self.player_character_map, f, indent=2, ensure_ascii=False)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error guardando mapeo de jugadores: {e}")
    
    def load_player_map(self):
        """Cargar mapeo de jugadores"""
        try:
            if os.path.exists(self.player_map_file):
                with open(self.player_map_file, 'r', encoding='utf-8') as f:
                    self.player_character_map = json.load(f)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error cargando mapeo de jugadores: {e}")