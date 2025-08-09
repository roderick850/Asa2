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
        # Asegurar que el log_file esté en un directorio seguro
        self.log_file = self._get_safe_log_path()
        
        # Crear directorio de logs si no existe
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except PermissionError:
                # Fallback a directorio temporal si no hay permisos
                import tempfile
                self.log_file = os.path.join(tempfile.gettempdir(), "ark_server_manager.log")
                print(f"Warning: Usando archivo de log temporal: {self.log_file}")
        
        # Configurar el logger real
        self._setup_logging()
    
    def _get_safe_log_path(self):
        """Obtener una ruta segura para el archivo de log"""
        # Si el log_file es relativo, asegurar que esté en el directorio del proyecto
        if not os.path.isabs(self.log_file):
            # Obtener directorio del script actual
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_dir = os.path.dirname(script_dir)  # Subir un nivel desde utils/
            safe_path = os.path.join(project_dir, self.log_file)
            return safe_path
        
        # Si es absoluto, verificar que no esté en system32
        if "system32" in self.log_file.lower() or "windows" in self.log_file.lower():
            # Cambiar a directorio local del usuario
            import tempfile
            return os.path.join(tempfile.gettempdir(), "ark_server_manager.log")
        
        return self.log_file
        
    def _setup_logging(self):
        """Configurar el sistema de logging real"""
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
            try:
                # Handler para archivo
                file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception:
                # Si falla el archivo, solo usar consola
                pass
            
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