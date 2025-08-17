import configparser
import os
import sys
import json
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file="config.ini"):
        # Asegurar que el config esté en el directorio del ejecutable
        if not os.path.isabs(config_file):
            # Si es un path relativo, ponerlo relativo al directorio del script/ejecutable
            if hasattr(sys, '_MEIPASS'):
                # Si estamos en un ejecutable de PyInstaller
                base_dir = os.path.dirname(sys.executable)
            else:
                # Si estamos en desarrollo
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_file = os.path.join(base_dir, config_file)
        else:
            self.config_file = config_file
            
        self.config = configparser.RawConfigParser()
        # Preservar el caso original de las claves
        self.config.optionxform = str
        self.original_file_content = []
        self.base_dir = self._get_base_dir()
        self.load_config()
    
    def _get_base_dir(self):
        """Obtener directorio base de la aplicación"""
        if hasattr(sys, '_MEIPASS'):
            # Si estamos en un ejecutable de PyInstaller
            return os.path.dirname(sys.executable)
        else:
            # Si estamos en desarrollo
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def get_data_file_path(self, filename):
        """Obtener ruta completa para archivos en la carpeta data"""
        data_dir = os.path.join(self.base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, filename)
        
    def load_config(self):
        """Cargar configuración desde archivo preservando formato original"""
        try:
            if os.path.exists(self.config_file):
                # Leer el contenido original del archivo
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.original_file_content = f.readlines()
                
                # Parsear con configparser preservando caso
                # IMPORTANTE: Limpiar config antes de leer para evitar conflictos
                self.config.clear()
                self.config.read(self.config_file, encoding='utf-8')
            else:
                self.create_default_config()
        except Exception as e:
            print(f"Error al cargar configuración: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """Crear configuración por defecto"""
        # Configuración del servidor
        self.config['server'] = {
            'root_path': '',
            'executable_path': '',
            'install_path': '',
            'steamcmd_path': '',
            'port': '7777',
            'max_players': '70',
            'server_name': 'Mi Servidor Ark',
            'additional_params': ''
        }
        
        # Configuración de juego
        self.config['game'] = {
            'xp_multiplier': '1.0',
            'harvest_multiplier': '1.0',
            'taming_multiplier': '1.0',
            'day_night_speed': '1.0'
        }
        
        # Configuración avanzada
        self.config['advanced'] = {
            'data_path': '',
            'logs_path': '',
            'additional_params': ''
        }
        
        # Configuración de backups
        self.config['backup'] = {
            'source_path': '',
            'destination_path': '',
            'frequency_hours': '24',
            'retain_backups': '7'
        }
        
        # Configuración de logs
        self.config['logs'] = {
            'logs_path': '',
            'max_log_size_mb': '100',
            'retain_logs_days': '30'
        }
        
        # Configuración de la aplicación
        self.config['app'] = {
            'theme': 'dark',
            'language': 'es',
            'auto_start_monitoring': 'false',
            'auto_start_backup': 'false'
        }
        
        # Crear contenido original para preservar formato
        self.original_file_content = []
        for section_name in self.config.sections():
            self.original_file_content.append(f"[{section_name}]\n")
            for key, value in self.config[section_name].items():
                self.original_file_content.append(f"{key}={value}\n")
            self.original_file_content.append("\n")  # Línea en blanco entre secciones
        
        # NO llamar a save() aquí para evitar recursión
        # Solo escribir directamente el archivo
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.writelines(self.original_file_content)
        except Exception as e:
            print(f"Error creando configuración por defecto: {e}")
    
    def save(self):
        """Guardar configuración preservando formato original del archivo"""
        try:
            if self.original_file_content:
                # Guardar preservando formato original
                self._save_preserving_format()
            else:
                # Fallback: guardar con formato estándar
                self._save_standard_format()
        except Exception as e:
            print(f"Error al guardar configuración: {e}")
            # Intentar guardar estándar como fallback
            self._save_standard_format()
    
    def _save_preserving_format(self):
        """Guardar preservando el formato original del archivo"""
        try:
            # print(f"🔍 DEBUG: Iniciando preservación de formato para {self.config_file}")
            # print(f"🔍 DEBUG: Contenido original tiene {len(self.original_file_content)} líneas")
            
            modified_lines = []
            current_section = None
            processed_keys = {}  # Rastrear claves procesadas por sección
            
            for i, line in enumerate(self.original_file_content):
                original_line = line
                stripped_line = line.strip()
                
                # Líneas de sección
                if stripped_line.startswith('[') and stripped_line.endswith(']'):
                    # Antes de cambiar de sección, agregar claves nuevas de la sección anterior
                    if current_section and self.config.has_section(current_section):
                        self._add_new_keys_to_section(modified_lines, current_section, processed_keys.get(current_section, set()))
                    
                    current_section = stripped_line[1:-1]
                    processed_keys[current_section] = set()
                    modified_lines.append(original_line)
                    # print(f"🔍 DEBUG: Línea {i+1}: Sección [{current_section}]")
                    continue
                
                # Líneas vacías o comentarios
                if not stripped_line or stripped_line.startswith(';') or stripped_line.startswith('#'):
                    modified_lines.append(original_line)
                    continue
                
                # Líneas key=value
                if '=' in stripped_line and current_section:
                    key_part, value_part = stripped_line.split('=', 1)
                    original_key = key_part.strip()
                    
                    # print(f"🔍 DEBUG: Línea {i+1}: Clave '{original_key}' en sección '{current_section}'")
                    
                    # Buscar si este valor ha sido modificado
                    # Usar búsqueda case-insensitive para encontrar la clave
                    found_key = None
                    found_value = None
                    
                    if self.config.has_section(current_section):
                        # Buscar la clave exacta primero
                        if self.config.has_option(current_section, original_key):
                            found_key = original_key
                            found_value = self.config.get(current_section, original_key)
                            processed_keys[current_section].add(original_key)
                        else:
                            # Buscar case-insensitive
                            for config_key in self.config.options(current_section):
                                if config_key.lower() == original_key.lower():
                                    found_key = config_key
                                    found_value = self.config.get(current_section, config_key)
                                    processed_keys[current_section].add(config_key)
                                    break
                    
                    if found_key and found_value is not None:
                        # Preservar el formato original (espacios, etc.)
                        prefix = line[:line.find('=') + 1]
                        suffix = '\n' if line.endswith('\n') else ''
                        modified_line = f"{prefix}{found_value}{suffix}"
                        modified_lines.append(modified_line)
                        # print(f"🔍 DEBUG: Línea {i+1}: Modificada '{original_key}={found_value}'")
                    else:
                        modified_lines.append(original_line)
                else:
                    modified_lines.append(original_line)
            
            # Agregar claves nuevas de la última sección
            if current_section and self.config.has_section(current_section):
                self._add_new_keys_to_section(modified_lines, current_section, processed_keys.get(current_section, set()))
            
            # Agregar secciones completamente nuevas
            for section_name in self.config.sections():
                if section_name not in processed_keys:
                    modified_lines.append(f"\n[{section_name}]\n")
                    for key, value in self.config.items(section_name):
                        modified_lines.append(f"{key}={value}\n")
            
            # Escribir el archivo modificado
            # print(f"🔍 DEBUG: Escribiendo archivo con {len(modified_lines)} líneas")
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.writelines(modified_lines)
                
            # print("✅ DEBUG: Archivo guardado preservando formato exitosamente")
                
        except Exception as e:
            print(f"❌ Error preservando formato: {e}")
            # Fallback a formato estándar
            self._save_standard_format()
    
    def _add_new_keys_to_section(self, modified_lines, section_name, processed_keys):
        """Agregar claves nuevas al final de una sección"""
        if not self.config.has_section(section_name):
            return
            
        new_keys_added = False
        for key, value in self.config.items(section_name):
            if key not in processed_keys:
                modified_lines.append(f"{key}={value}\n")
                new_keys_added = True
                # print(f"🔍 DEBUG: Agregada clave nueva '{key}={value}' a sección [{section_name}]")
        
        return new_keys_added
    
    def _save_standard_format(self):
        """Guardar con formato estándar (fallback)"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                # Escribir manualmente para evitar espacios alrededor del =
                for section_name in self.config.sections():
                    f.write(f"[{section_name}]\n")
                    for key, value in self.config[section_name].items():
                        f.write(f"{key}={value}\n")
                    f.write("\n")  # Línea en blanco entre secciones
        except Exception as e:
            print(f"Error al guardar configuración estándar: {e}")
    
    def get(self, section, key, default=None):
        """Obtener valor de configuración"""
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
    
    def set(self, section, key, value):
        """Establecer valor de configuración"""
        try:
            if not self.config.has_section(section):
                self.config.add_section(section)
            
            # Verificar si el valor realmente cambió
            old_value = self.config.get(section, key) if self.config.has_option(section, key) else None
            new_value = str(value)
            
            if old_value != new_value:
                self.config.set(section, key, new_value)
                
                # Actualizar el contenido original si existe
                if self.original_file_content:
                    self._update_original_content(section, key, new_value)
                    
        except Exception as e:
            print(f"Error al establecer configuración: {e}")
    
    def _update_original_content(self, section, key, new_value):
        """Actualizar el contenido original con el nuevo valor"""
        try:
            modified_lines = []
            current_section = None
            
            for i, line in enumerate(self.original_file_content):
                original_line = line
                stripped_line = line.strip()
                
                # Líneas de sección
                if stripped_line.startswith('[') and stripped_line.endswith(']'):
                    current_section = stripped_line[1:-1]
                    modified_lines.append(original_line)
                    continue
                
                # Líneas key=value en la sección correcta
                if ('=' in stripped_line and current_section == section and 
                    stripped_line.split('=')[0].strip() == key):
                    # Reemplazar solo el valor, preservando el formato
                    prefix = line[:line.find('=') + 1]
                    suffix = '\n' if line.endswith('\n') else ''
                    modified_line = f"{prefix}{new_value}{suffix}"
                    modified_lines.append(modified_line)
                else:
                    modified_lines.append(original_line)
            
            # Actualizar el contenido original
            self.original_file_content = modified_lines
            
        except Exception as e:
            print(f"❌ Error actualizando contenido original: {e}")
    
    def get_section(self, section):
        """Obtener toda una sección de configuración"""
        try:
            return dict(self.config[section])
        except configparser.NoSectionError:
            return {}
    
    def set_section(self, section, data):
        """Establecer toda una sección de configuración"""
        try:
            if not self.config.has_section(section):
                self.config.add_section(section)
            
            for key, value in data.items():
                self.config.set(section, key, str(value))
                
            # Actualizar el contenido original si existe
            if self.original_file_content:
                for key, value in data.items():
                    self._update_original_content(section, key, str(value))
                    
        except Exception as e:
            print(f"Error al establecer sección de configuración: {e}")
    
    def has_section(self, section):
        """Verificar si existe una sección"""
        return self.config.has_section(section)
    
    def remove_section(self, section):
        """Eliminar una sección de configuración"""
        try:
            return self.config.remove_section(section)
        except Exception as e:
            print(f"Error al eliminar sección: {e}")
            return False
    
    def get_all_sections(self):
        """Obtener todas las secciones"""
        return self.config.sections()
    
    def export_config(self, file_path):
        """Exportar configuración a archivo JSON"""
        try:
            config_dict = {}
            for section in self.config.sections():
                config_dict[section] = dict(self.config[section])
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=4, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error al exportar configuración: {e}")
            return False
    
    def import_config(self, file_path):
        """Importar configuración desde archivo JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            for section, data in config_dict.items():
                self.set_section(section, data)
            
            self.save()
            return True
        except Exception as e:
            print(f"Error al importar configuración: {e}")
            return False
    
    def reset_to_defaults(self):
        """Restablecer configuración por defecto"""
        self.config.clear()
        self.create_default_config()
    
    def validate_config(self):
        """Validar configuración"""
        errors = []
        
        # Validar configuración del servidor
        server_path = self.get('server', 'path', '')
        if server_path and not os.path.exists(server_path):
            errors.append("La ruta del servidor no existe")
        
        try:
            port = int(self.get('server', 'port', '7777'))
            if port < 1 or port > 65535:
                errors.append("El puerto debe estar entre 1 y 65535")
        except ValueError:
            errors.append("El puerto debe ser un número válido")
        
        try:
            max_players = int(self.get('server', 'max_players', '70'))
            if max_players < 1 or max_players > 255:
                errors.append("El máximo de jugadores debe estar entre 1 y 255")
        except ValueError:
            errors.append("El máximo de jugadores debe ser un número válido")
        
        # Validar multiplicadores de juego
        multipliers = ['xp_multiplier', 'harvest_multiplier', 'taming_multiplier', 'day_night_speed']
        for multiplier in multipliers:
            try:
                value = float(self.get('game', multiplier, '1.0'))
                if value < 0:
                    errors.append(f"El multiplicador {multiplier} no puede ser negativo")
            except ValueError:
                errors.append(f"El multiplicador {multiplier} debe ser un número válido")
        
        return errors

    def reload_config(self):
        """Recargar configuración desde archivo y actualizar contenido original"""
        try:
            if os.path.exists(self.config_file):
                # Leer el contenido original del archivo
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.original_file_content = f.readlines()
                
                # Limpiar y recargar config
                self.config.clear()
                self.config.read(self.config_file, encoding='utf-8')
                return True
            else:
                return False
        except Exception as e:
            print(f"Error al recargar configuración: {e}")
            return False
