import logging
import os
import sys
from datetime import datetime
from pathlib import Path

def is_compiled():
    """Detectar si la aplicación está corriendo como ejecutable compilado"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

class Logger:
    def __init__(self, log_file="logs/app.log"):
        self.log_file = log_file
        self.setup_logger()
        
    def setup_logger(self):
        """Configurar el sistema de logging"""
        # Asegurar que el log_file esté en un directorio seguro
        self.log_file = self._get_safe_log_path()
        
        # Determinar nivel de logging según si es ejecutable o desarrollo
        if is_compiled():
            # En ejecutable: Solo ERROR y WARNING para inicio rápido
            self.log_level = logging.WARNING
            try:
                print("🚀 Modo ejecutable: Logs de debug deshabilitados para inicio rápido")
            except UnicodeEncodeError:
                print("Modo ejecutable: Logs de debug deshabilitados para inicio rapido")
        else:
            # En desarrollo: Todos los logs incluido DEBUG
            self.log_level = logging.INFO
            try:
                print("🔧 Modo desarrollo: Logs de debug habilitados")
            except UnicodeEncodeError:
                print("Modo desarrollo: Logs de debug habilitados")
        
        # Crear directorio de logs si no existe
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except PermissionError:
                # Fallback a directorio temporal si no hay permisos
                import tempfile
                self.log_file = os.path.join(tempfile.gettempdir(), "ark_server_manager.log")
                if not is_compiled():  # Solo mostrar warning en desarrollo
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
        
        # Configurar logger principal con nivel dinámico
        self.logger = logging.getLogger('ArkServerManager')
        self.logger.setLevel(self.log_level)  # Usar nivel dinámico (WARNING en exe, INFO en dev)
        
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
        # En ejecutable, omitir debug para rendimiento
        if not is_compiled():
            self.logger.debug(message)
    
    def info(self, message):
        """Registrar mensaje informativo"""
        # En ejecutable, filtrar mensajes: solo los críticos para el usuario
        if is_compiled():
            # Solo mostrar mensajes críticos del usuario (no debug técnico)
            critical_keywords = [
                "Auto-iniciando servidor", "Servidor iniciado", "Servidor detenido",
                "Error en auto-inicio", "Auto-inicio cancelado", "Conectado", "Desconectado",
                "Backup completado", "Error crítico", "Instalación completada",
                "✅ Aplicación iniciada", "❌ Error crítico"
            ]
            
            # Filtrar mensajes de inicio verbosos
            startup_noise = [
                "Sistema de configuración inicializado", "Configuraciones de aplicación aplicadas",
                "Cargando última configuración", "Auto-inicio manual:", "Auto-inicio con Windows:",
                "Último servidor cargado:", "Último mapa cargado:", "Panel de", "inicializado",
                "Diagnóstico fallback", "started_with_windows:", "system_tray disponible:",
                "Configuración manual:", "Inicio manual detectado", "Ruta de backup configurada:",
                "No se encontró archivo de mods", "Iniciando hilo de bandeja"
            ]
            
            # Si es ruido de inicio, omitir completamente
            if any(noise in message for noise in startup_noise):
                return
            
            # Verificar si es un mensaje importante para el usuario
            if any(keyword in message for keyword in critical_keywords):
                self.logger.warning(message)  # Usar WARNING para asegurar que se muestre
        else:
            # En desarrollo, mostrar todos los mensajes info
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
    
    def debug(self, message):
        """Registrar mensaje de debug (solo en desarrollo)"""
        if hasattr(self, 'logger'):
            self.logger.debug(message)
        elif not is_compiled():  # Solo mostrar en consola si es desarrollo
            print(f"DEBUG: {message}")
    
    def is_debug_enabled(self):
        """Verificar si los logs de debug están habilitados"""
        return not is_compiled()
    
    def should_log_debug(self):
        """Alias para verificar si se deben mostrar logs de debug"""
        return self.is_debug_enabled()