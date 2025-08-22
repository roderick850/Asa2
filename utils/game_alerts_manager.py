import re
import json
import os
from datetime import datetime
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass

@dataclass
class GameEvent:
    timestamp: datetime
    event_type: str  # 'player_join', 'player_leave', 'player_death', 'dino_death', 'dino_taming'
    player_name: str
    character_name: str
    unique_id: str
    details: Dict  # Información adicional específica del evento
    server_name: str

class GameAlertsManager:
    def __init__(self, logger=None, rcon_panel=None):
        self.logger = logger
        self.rcon_panel = rcon_panel
        self.player_character_map = {}
        
        # Configuración por defecto de alertas
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
                'message': '{character_name} ha muerto',
                'color': 'yellow'
            },
            'dino_death': {
                'enabled': True,
                'message': '{dino_name} (Nivel {dino_level}) de {tribe_name} fue asesinado por {killer_name} (Nivel {killer_level})',
                'color': 'orange'
            },
            'dino_taming': {
                'enabled': True,
                'message': '{character_name} ha tameado un {dino_name} (Nivel {dino_level})',
                'color': 'cyan'
            }
        }
        
        # Patrones regex para detectar eventos
        self.patterns = {
            # Patrones corregidos para conexiones - NUEVO formato con timestamp YYYY.MM.DD_HH.MM.SS
            'player_join': re.compile(r'(\d{4}\.\d{2}\.\d{2}_\d{2}\.\d{2}\.\d{2}):\s*(\w+)\s+\[UniqueNetId:([a-f0-9]+)\s+Platform:(\w+|None)\]\s+joined this ARK!'),
            
            # Patrón corregido para desconexiones con timestamp YYYY.MM.DD_HH.MM.SS
            'player_leave': re.compile(r'(\d{4}\.\d{2}\.\d{2}_\d{2}\.\d{2}\.\d{2}):\s*(\w+)\s+\[UniqueNetId:([a-f0-9]+)\s+Platform:(\w+|None)\]\s+left this ARK!'),
            
            # Patrones para muerte de jugador y dinos (ajustados al formato real)
            'player_death': re.compile(r'\[(\d{2}:\d{2}:\d{2})\].*?Tribe (.+?), ID (\d+): Day \d+, \d{2}:\d{2}:\d{2}: (.+?) was killed!'),
            
            # Patrón para muerte de dino CON asesino - MEJORADO para capturar también el asesino
            'dino_death': re.compile(r'(\d{4}\.\d{2}\.\d{2}_\d{2}\.\d{2}\.\d{2}):\s*(.+?)\s*-\s*Lvl\s+(\d+)\s*\((.+?)\)\s*\((.+?)\)\s*was killed by\s*(?:a\s+)?(.+?)\s*-\s*Lvl\s+(\d+)\s*\(\)'),
            
            # Patrón para muerte de dino SIN asesino (hambre, etc.)
            'dino_death_simple': re.compile(r'(\d{4}\.\d{2}\.\d{2}_\d{2}\.\d{2}\.\d{2}):\s*(.+?)\s*-\s*Lvl\s+(\d+)\s*\((.+?)\)\s*\((.+?)\)\s*was killed!'),
            
            # Patrón para tameo - CORREGIDO para formato 2025.08.21_17.13.43:
            'dino_taming': re.compile(r'(\d{4}\.\d{2}\.\d{2}_\d{2}\.\d{2}\.\d{2}):\s*(.+?)\s+(?:of\s+Tribe\s+.+?\s+)?Tamed\s+(?:a|an)\s+(.+?)\s*-\s*Lvl\s+(\d+)')
        }
        
        # Cargar configuración desde config_manager si está disponible
        self._load_config_from_manager()
        
        # Archivos de configuración
        self.config_file = 'data/game_alerts_config.json'
        self.player_map_file = 'data/player_character_map.json'
        
        # Cargar mapeo de jugadores
        self.load_player_map()
    
    def process_log_line(self, server_name: str, line: str):
        """Procesar una línea de log para detectar eventos"""
        try:
            # Verificar conexión de jugador
            if match := self.patterns['player_join'].search(line):
                timestamp_str, character_name, unique_id, platform = match.groups()
                timestamp = self._parse_timestamp(timestamp_str)
                
                # Actualizar mapeo jugador-personaje
                self.update_player_character_map(unique_id, character_name)
                
                event = GameEvent(
                    timestamp=timestamp,
                    event_type='player_join',
                    player_name='',
                    character_name=character_name,
                    unique_id=unique_id,
                    details={'platform': platform},
                    server_name=server_name
                )
                self._handle_event(event)
            
            # Verificar desconexión de jugador
            elif match := self.patterns['player_leave'].search(line):
                timestamp_str, character_name, unique_id, platform = match.groups()
                timestamp = self._parse_timestamp(timestamp_str)
                
                event = GameEvent(
                    timestamp=timestamp,
                    event_type='player_leave',
                    player_name='',
                    character_name=character_name,
                    unique_id=unique_id,
                    details={'platform': platform},
                    server_name=server_name
                )
                self._handle_event(event)
            
            # Verificar muerte de jugador
            elif match := self.patterns['player_death'].search(line):
                timestamp_str, tribe_name, tribe_id, character_name = match.groups()
                timestamp = self._parse_timestamp(timestamp_str)
                
                event = GameEvent(
                    timestamp=timestamp,
                    event_type='player_death',
                    player_name='',
                    character_name=character_name,
                    unique_id='',
                    details={
                        'tribe_name': tribe_name,
                        'tribe_id': tribe_id
                    },
                    server_name=server_name
                )
                self._handle_event(event)
            
            # Verificar muerte de dino
            elif match := self.patterns['dino_death'].search(line):
                timestamp_str, dino_name, dino_level, dino_species, tribe_name, killer_name, killer_level = match.groups()
                timestamp = self._parse_timestamp(timestamp_str)
                
                event = GameEvent(
                    timestamp=timestamp,
                    event_type='dino_death',
                    player_name='',
                    character_name='Desconocido',  # No hay info de jugador específico en este formato
                    unique_id='',
                    details={
                        'dino_name': dino_name.strip(),
                        'dino_level': int(dino_level),
                        'dino_species': dino_species.strip(),
                        'tribe_name': tribe_name.strip(),
                        'killer_name': killer_name.strip(),
                        'killer_level': int(killer_level),
                        'death_type': 'killed_by'  # Muerte con asesino identificado
                    },
                    server_name=server_name
                )
                self._handle_event(event)
            
            # Verificar muerte de dino SIN asesino (hambre, etc.)
            elif match := self.patterns['dino_death_simple'].search(line):
                timestamp_str, dino_name, dino_level, dino_species, tribe_name = match.groups()
                timestamp = self._parse_timestamp(timestamp_str)
                
                event = GameEvent(
                    timestamp=timestamp,
                    event_type='dino_death',  # Mismo tipo de evento para usar la misma configuración
                    player_name='',
                    character_name='Desconocido',  # No hay info de jugador específico
                    unique_id='',
                    details={
                        'dino_name': dino_name.strip(),
                        'dino_level': int(dino_level),
                        'dino_species': dino_species.strip(),
                        'tribe_name': tribe_name.strip(),
                        'killer_name': 'Desconocido',  # Sin asesino conocido
                        'killer_level': 0,  # Sin nivel de asesino
                        'death_type': 'natural'  # Muerte natural (hambre, etc.)
                    },
                    server_name=server_name
                )
                self._handle_event(event)
            
            # Verificar tameo de dino
            elif match := self.patterns['dino_taming'].search(line):
                timestamp_str, character_name, dino_name, dino_level = match.groups()
                timestamp = self._parse_timestamp(timestamp_str)
                
                event = GameEvent(
                    timestamp=timestamp,
                    event_type='dino_taming',
                    player_name='',
                    character_name=character_name,
                    unique_id='',
                    details={
                        'dino_name': dino_name.strip(),
                        'dino_level': int(dino_level)
                    },
                    server_name=server_name
                )
                self._handle_event(event)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error procesando línea de log: {e}")
                self.logger.debug(f"Línea problemática: {line}")
    
    def update_player_character_map(self, unique_id: str, character_name: str, player_name: str = ''):
        """Actualizar mapeo entre ID único y nombre de personaje"""
        if unique_id and character_name:
            self.player_character_map[unique_id] = {
                'character_name': character_name,
                'player_name': player_name,
                'last_seen': datetime.now().isoformat()
            }
            self.save_player_map()
    
    def get_character_name(self, unique_id: str, fallback_name: str = '') -> str:
        """Obtener nombre de personaje por ID único"""
        if unique_id in self.player_character_map:
            return self.player_character_map[unique_id]['character_name']
        return fallback_name
    
    def _handle_event(self, event: GameEvent):
        """Manejar un evento detectado"""
        try:
            # Verificar si la alerta está habilitada
            if event.event_type in self.alert_config:
                alert_config = self.alert_config[event.event_type]
                enabled = alert_config.get('enabled', False)
                
                if self.logger:
                    self.logger.debug(f"Evento {event.event_type}: enabled={enabled}")
                
                if enabled:
                    # Generar mensaje de alerta
                    message = self._generate_alert_message(event)
                    if message:
                        # Enviar alerta
                        self._send_rcon_alert(message, event.event_type)
                        
                        if self.logger:
                            self.logger.info(f"Alerta enviada: {event.event_type} - {message}")
                else:
                    if self.logger:
                        self.logger.debug(f"Alerta {event.event_type} deshabilitada - no se envía")
                            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error manejando evento {event.event_type}: {e}")
    
    def _generate_alert_message(self, event: GameEvent) -> str:
        """Generar mensaje de alerta basado en el evento"""
        try:
            alert_config = self.alert_config.get(event.event_type, {})
            message_template = alert_config.get('message', '')
            
            if not message_template:
                return ''
            
            # Preparar variables para el formato
            format_vars = {
                'character_name': event.character_name,
                'player_name': event.player_name,
                'server_name': event.server_name,
                'timestamp': event.timestamp.strftime('%H:%M:%S')
            }
            
            # Agregar detalles específicos del evento
            if event.event_type in ['dino_death', 'dino_taming']:
                format_vars.update({
                    'dino_name': event.details.get('dino_name', ''),
                    'dino_level': event.details.get('dino_level', 0)
                })
            
            if event.event_type in ['player_death', 'dino_death']:
                format_vars.update({
                    'tribe_name': event.details.get('tribe_name', ''),
                    'tribe_id': event.details.get('tribe_id', '')
                })
            
            # Para muerte de dino, agregar especies y asesino si está disponible
            if event.event_type == 'dino_death':
                death_type = event.details.get('death_type', 'natural')
                killer_name = event.details.get('killer_name', 'Desconocido')
                killer_level = event.details.get('killer_level', 0)
                
                format_vars.update({
                    'dino_species': event.details.get('dino_species', ''),
                    'killer_name': killer_name,
                    'killer_level': killer_level
                })
                
                # Usar mensaje diferente según el tipo de muerte
                if death_type == 'natural':
                    # Muerte natural (hambre, etc.) - mensaje simplificado
                    message_template = '{dino_name} (Nivel {dino_level}) de {tribe_name} ha muerto'
                # Si es 'killed_by', usar el template original con asesino
            
            # Formatear mensaje
            message = message_template.format(**format_vars)
            return message
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error generando mensaje de alerta: {e}")
            return ''
    
    def _send_rcon_alert(self, message: str, event_type: str):
        """Enviar alerta via RCON"""
        try:
            if not self.rcon_panel:
                if self.logger:
                    self.logger.warning("⚠️ No hay panel RCON disponible para enviar alerta")
                return
            
            # Limpiar cualquier código RichColor del mensaje
            clean_message = self._clean_rich_color_from_message(message)
            
            # Construir comando RCON sin colores
            rcon_command = f'ServerChat {clean_message}'
            
            if self.logger:
                self.logger.info(f"🎮 Intentando enviar alerta {event_type}: {rcon_command}")
            
            # Ejecutar comando
            if hasattr(self.rcon_panel, 'execute_rcon_command'):
                result = self.rcon_panel.execute_rcon_command(rcon_command)
                if result:
                    if self.logger:
                        self.logger.info(f"✅ Alerta {event_type} enviada exitosamente")
                else:
                    if self.logger:
                        self.logger.error(f"❌ Falló el envío de alerta {event_type}")
            else:
                if self.logger:
                    self.logger.warning("Panel RCON no tiene método execute_rcon_command")
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Error enviando alerta RCON {event_type}: {e}")
    
    def _clean_rich_color_from_message(self, message: str) -> str:
        """Limpiar cualquier código RichColor de un mensaje"""
        import re
        # Remover cualquier código RichColor que pueda estar en el mensaje
        cleaned = re.sub(r'<RichColor[^>]*>', '', message)
        cleaned = re.sub(r'</RichColor>', '', cleaned)
        return cleaned.strip()
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parsear timestamp del formato de ARK"""
        try:
            # Formato de timestamp con fecha completa: 2025.08.21_17.13.43
            if len(timestamp_str) == 19 and '_' in timestamp_str:
                return datetime.strptime(timestamp_str, '%Y.%m.%d_%H.%M.%S')
            
            # Formato de timestamp simple: HH:MM:SS (para conexiones/desconexiones)
            elif len(timestamp_str) == 8 and ':' in timestamp_str:
                today = datetime.now().date()
                time_part = datetime.strptime(timestamp_str, '%H:%M:%S').time()
                return datetime.combine(today, time_part)
            
            # Formato alternativo con fecha completa (formato anterior)
            else:
                return datetime.strptime(timestamp_str, '%Y.%m.%d-%H.%M.%S')
        except ValueError:
            return datetime.now()
    
    def set_alert_enabled(self, event_type: str, enabled: bool):
        """Habilitar/deshabilitar alerta"""
        if event_type in self.alert_config:
            self.alert_config[event_type]['enabled'] = enabled
            self.save_config()
    
    def set_alert_message(self, event_type: str, message: str):
        """Establecer mensaje de alerta"""
        if event_type in self.alert_config:
            self.alert_config[event_type]['message'] = message
            self.save_config()
    
    def set_alert_color(self, event_type: str, color: str):
        """Establecer color de alerta"""
        if event_type in self.alert_config:
            self.alert_config[event_type]['color'] = color
            self.save_config()
    
    def get_alert_config(self) -> Dict:
        """Obtener configuración actual de alertas"""
        return self.alert_config.copy()
    
    def update_config(self, config: Dict):
        """Actualizar configuración de alertas desde el panel"""
        try:
            # Mapear los nombres de configuración del panel a los tipos de eventos
            config_mapping = {
                'connection_alerts': 'player_join',
                'disconnection_alerts': 'player_leave', 
                'player_death_alerts': 'player_death',
                'dino_death_alerts': 'dino_death',
                'taming_alerts': 'dino_taming'
            }
            
            color_mapping = {
                'connection_color': 'player_join',
                'disconnection_color': 'player_leave',
                'death_color': 'player_death'
            }
            
            # Actualizar estados de alertas
            for config_key, event_type in config_mapping.items():
                if config_key in config and event_type in self.alert_config:
                    old_value = self.alert_config[event_type]['enabled']
                    new_value = config[config_key]
                    self.alert_config[event_type]['enabled'] = new_value
                    if self.logger:
                        self.logger.debug(f"Switch {config_key} -> {event_type}: {old_value} -> {new_value}")
            
            # Actualizar colores
            for color_key, event_type in color_mapping.items():
                if color_key in config and event_type in self.alert_config:
                    color_value = config[color_key].lower()
                    self.alert_config[event_type]['color'] = color_value
            
            # También aplicar color de muerte a dino_death si no se especifica por separado
            if 'death_color' in config:
                death_color = config['death_color'].lower()
                self.alert_config['dino_death']['color'] = death_color
            
            # Guardar configuración actualizada en config_manager
            self.save_config()
            
            if self.logger:
                self.logger.info("Configuración de alertas actualizada correctamente")
                self.logger.debug(f"Estado actual de alertas: {[(k, v['enabled']) for k, v in self.alert_config.items()]}")
                        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error actualizando configuración de alertas: {e}")
    
    def save_config(self):
        """Guardar configuración de alertas en config_manager"""
        try:
            if hasattr(self, 'rcon_panel') and self.rcon_panel and hasattr(self.rcon_panel, 'config_manager'):
                config_manager = self.rcon_panel.config_manager
                
                # Mapear los tipos de eventos a nombres de configuración del panel
                reverse_mapping = {
                    'player_join': 'connection_alerts',
                    'player_leave': 'disconnection_alerts',
                    'player_death': 'player_death_alerts',
                    'dino_death': 'dino_death_alerts',
                    'dino_taming': 'taming_alerts'
                }
                
                # Guardar estados de alertas en config_manager
                for event_type, config_key in reverse_mapping.items():
                    if event_type in self.alert_config:
                        enabled = self.alert_config[event_type]['enabled']
                        # Usar la sección "game_alerts"
                        config_manager.set("game_alerts", config_key, str(enabled).lower())
                        if self.logger:
                            self.logger.debug(f"Guardado {config_key}: {enabled}")
                
                # Guardar la configuración - CORREGIR: usar save() no save_config()
                config_manager.save()
                
                if self.logger:
                    self.logger.info("✅ Configuración de alertas guardada exitosamente")
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Error guardando configuración: {e}")
    
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
    
    def _load_config_from_manager(self):
        """Cargar configuración de alertas desde config_manager"""
        try:
            if hasattr(self, 'rcon_panel') and self.rcon_panel and hasattr(self.rcon_panel, 'config_manager'):
                config_manager = self.rcon_panel.config_manager
                
                # Mapear los nombres de configuración del panel a los tipos de eventos
                config_mapping = {
                    'connection_alerts': 'player_join',
                    'disconnection_alerts': 'player_leave', 
                    'player_death_alerts': 'player_death',
                    'dino_death_alerts': 'dino_death',
                    'taming_alerts': 'dino_taming'
                }
                
                # Actualizar estados de alertas desde config_manager
                for config_key, event_type in config_mapping.items():
                    if event_type in self.alert_config:
                        # Cargar desde la sección "game_alerts" con conversión correcta
                        enabled_raw = config_manager.get("game_alerts", config_key, True)
                        enabled = self._convert_to_bool(enabled_raw)
                        self.alert_config[event_type]['enabled'] = enabled
                        
                        # Limpiar mensaje de cualquier código RichColor que pueda estar guardado
                        if 'message' in self.alert_config[event_type]:
                            original_message = self.alert_config[event_type]['message']
                            cleaned_message = self._clean_rich_color_from_message(original_message)
                            self.alert_config[event_type]['message'] = cleaned_message
                        
                        if self.logger:
                            self.logger.debug(f"Cargado {event_type}: enabled={enabled} (raw: {enabled_raw})")
                            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Error cargando configuración desde config_manager: {e}")
    
    def _convert_to_bool(self, value):
        """Convertir valor a boolean manejando strings"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'on']
        return bool(value)