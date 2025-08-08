import logging
import os
from datetime import datetime
from pathlib import Path

class Logger:
    def __init__(self, log_file="logs/app.log"):
        self.log_file = log_file
        self.setup_logger()
        
    def setup_logger(self):
        """Configurar el sistema de logging"""
        # Crear directorio de logs si no existe
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Configurar formato del log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Configurar logger principal
        self.logger = logging.getLogger('ArkServerManager')
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar duplicación de handlers
        if not self.logger.handlers:
            # Handler para archivo
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # Handler para consola
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def debug(self, message):
        """Registrar mensaje de debug"""
        self.logger.debug(message)
    
    def info(self, message):
        """Registrar mensaje informativo"""
        self.logger.info(message)
    
    def warning(self, message):
        """Registrar mensaje de advertencia"""
        self.logger.warning(message)
    
    def error(self, message):
        """Registrar mensaje de error"""
        self.logger.error(message)
    
    def critical(self, message):
        """Registrar mensaje crítico"""
        self.logger.critical(message)
    
    def log_server_event(self, event_type, details=""):
        """Registrar evento del servidor"""
        message = f"SERVER_EVENT [{event_type}] {details}"
        self.info(message)
    
    def log_player_action(self, player_name, action, details=""):
        """Registrar acción de jugador"""
        message = f"PLAYER_ACTION [{player_name}] {action} {details}"
        self.info(message)
    
    def log_backup_event(self, event_type, details=""):
        """Registrar evento de backup"""
        message = f"BACKUP_EVENT [{event_type}] {details}"
        self.info(message)
    
    def log_config_change(self, section, key, old_value, new_value):
        """Registrar cambio de configuración"""
        message = f"CONFIG_CHANGE [{section}.{key}] {old_value} -> {new_value}"
        self.info(message)
    
    def log_error_with_context(self, error, context=""):
        """Registrar error con contexto"""
        message = f"ERROR [{context}] {str(error)}"
        self.error(message)
    
    def get_recent_logs(self, lines=100):
        """Obtener logs recientes"""
        try:
            if not os.path.exists(self.log_file):
                return []
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            self.error(f"Error al leer logs recientes: {e}")
            return []
    
    def clear_logs(self):
        """Limpiar archivo de logs"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write("")
            self.info("Logs limpiados")
        except Exception as e:
            self.error(f"Error al limpiar logs: {e}")
    
    def rotate_logs(self, max_size_mb=100):
        """Rotar logs cuando excedan el tamaño máximo"""
        try:
            if not os.path.exists(self.log_file):
                return
            
            file_size = os.path.getsize(self.log_file)
            max_size_bytes = max_size_mb * 1024 * 1024
            
            if file_size > max_size_bytes:
                # Crear backup del log actual
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{self.log_file}.{timestamp}"
                
                os.rename(self.log_file, backup_file)
                self.setup_logger()  # Recrear el archivo de log
                
                self.info(f"Logs rotados: {self.log_file} -> {backup_file}")
        except Exception as e:
            self.error(f"Error al rotar logs: {e}")
    
    def get_log_stats(self):
        """Obtener estadísticas de logs"""
        try:
            if not os.path.exists(self.log_file):
                return {
                    'file_size': 0,
                    'total_lines': 0,
                    'error_count': 0,
                    'warning_count': 0,
                    'info_count': 0
                }
            
            file_size = os.path.getsize(self.log_file)
            total_lines = 0
            error_count = 0
            warning_count = 0
            info_count = 0
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    total_lines += 1
                    if 'ERROR' in line:
                        error_count += 1
                    elif 'WARNING' in line:
                        warning_count += 1
                    elif 'INFO' in line:
                        info_count += 1
            
            return {
                'file_size': file_size,
                'total_lines': total_lines,
                'error_count': error_count,
                'warning_count': warning_count,
                'info_count': info_count
            }
        except Exception as e:
            self.error(f"Error al obtener estadísticas de logs: {e}")
            return {}
    
    def search_logs(self, search_term, case_sensitive=False):
        """Buscar en logs"""
        try:
            if not os.path.exists(self.log_file):
                return []
            
            results = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if case_sensitive:
                        if search_term in line:
                            results.append((line_num, line.strip()))
                    else:
                        if search_term.lower() in line.lower():
                            results.append((line_num, line.strip()))
            
            return results
        except Exception as e:
            self.error(f"Error al buscar en logs: {e}")
            return []
