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
            
        self.config = configparser.ConfigParser()
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
        """Cargar configuración desde archivo"""
        try:
            if os.path.exists(self.config_file):
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
            'backup_path': '',
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
        
        self.save()
    
    def save(self):
        """Guardar configuración en archivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
        except Exception as e:
            print(f"Error al guardar configuración: {e}")
    
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
            self.config.set(section, key, str(value))
        except Exception as e:
            print(f"Error al establecer configuración: {e}")
    
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
