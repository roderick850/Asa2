"""
Sistema de logging especializado para eventos del servidor ARK
"""
import os
import logging
from datetime import datetime
from pathlib import Path


class ServerEventLogger:
    """Logger especializado para eventos importantes del servidor"""
    
    def __init__(self, server_name="default"):
        self.server_name = server_name
        self.setup_logger()
    
    def setup_logger(self):
        """Configurar el logger para eventos del servidor"""
        # Obtener directorio seguro para logs
        logs_dir = self._get_safe_logs_dir()
        
        # Nombre del archivo con fecha
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = logs_dir / f"server_events_{today}.log"
    
    def _get_safe_logs_dir(self):
        """Obtener directorio seguro para logs de servidor"""
        try:
            # Intentar crear en directorio local
            logs_dir = Path("logs/server_events")
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Probar escritura
            test_file = logs_dir / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
            
            return logs_dir
            
        except (PermissionError, OSError) as e:
            # Si falla, usar directorio temporal del usuario
            import tempfile
            user_temp = Path(tempfile.gettempdir()) / "ArkServerManager" / "logs" / "server_events"
            try:
                user_temp.mkdir(parents=True, exist_ok=True)
                return user_temp
            except Exception:
                # Último recurso: directorio temporal del sistema
                sys_temp = Path(tempfile.gettempdir()) / "arkserver_logs"
                sys_temp.mkdir(parents=True, exist_ok=True)
                return sys_temp
        
        # Configurar logger
        self.logger = logging.getLogger(f"ServerEvents_{self.server_name}")
        self.logger.setLevel(logging.INFO)
        
        # Remover handlers existentes para evitar duplicados
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Handler para archivo
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # No propagar al logger padre para evitar duplicados
        self.logger.propagate = False
    
    def log_server_start(self, server_path, map_name, additional_info=""):
        """Registrar inicio del servidor"""
        msg = f"🚀 SERVIDOR INICIADO | Servidor: {self.server_name} | Mapa: {map_name}"
        if additional_info:
            msg += f" | {additional_info}"
        self.logger.info(msg)
        return msg
    
    def log_server_stop(self, reason="Manual", additional_info=""):
        """Registrar detención del servidor"""
        msg = f"⏹️ SERVIDOR DETENIDO | Servidor: {self.server_name} | Motivo: {reason}"
        if additional_info:
            msg += f" | {additional_info}"
        self.logger.info(msg)
        return msg
    
    def log_server_restart(self, reason="Manual", additional_info=""):
        """Registrar reinicio del servidor"""
        msg = f"🔄 SERVIDOR REINICIADO | Servidor: {self.server_name} | Motivo: {reason}"
        if additional_info:
            msg += f" | {additional_info}"
        self.logger.info(msg)
        return msg
    
    def log_server_update_start(self, method="SteamCMD"):
        """Registrar inicio de actualización"""
        msg = f"📥 ACTUALIZACIÓN INICIADA | Servidor: {self.server_name} | Método: {method}"
        self.logger.info(msg)
        return msg
    
    def log_server_update_complete(self, success=True, details=""):
        """Registrar finalización de actualización"""
        status = "✅ EXITOSA" if success else "❌ FALLIDA"
        msg = f"📥 ACTUALIZACIÓN {status} | Servidor: {self.server_name}"
        if details:
            msg += f" | {details}"
        self.logger.info(msg)
        return msg
    
    def log_automatic_restart_start(self, restart_info):
        """Registrar inicio de reinicio automático"""
        msg = f"🕐 REINICIO AUTOMÁTICO INICIADO | Servidor: {self.server_name}"
        if restart_info.get("update_requested"):
            msg += " | Con actualización"
        if restart_info.get("backup_before_restart"):
            msg += " | Con backup"
        if restart_info.get("saveworld_before_restart"):
            msg += " | Con saveworld"
        if restart_info.get("warnings_sent"):
            msg += " | Con avisos RCON"
        self.logger.info(msg)
        return msg
    
    def log_automatic_restart_complete(self, restart_info):
        """Registrar finalización de reinicio automático"""
        success = restart_info.get("success", False)
        status = "✅ EXITOSO" if success else "❌ FALLIDO"
        msg = f"🕐 REINICIO AUTOMÁTICO {status} | Servidor: {self.server_name}"
        
        # Agregar detalles de lo que se ejecutó
        actions = []
        if restart_info.get("update_done"):
            actions.append("Actualización")
        if restart_info.get("backup_done"):
            actions.append("Backup")
        if restart_info.get("saveworld_done"):
            actions.append("Saveworld")
        if restart_info.get("warnings_sent"):
            actions.append("Avisos RCON")
        
        if actions:
            msg += f" | Acciones: {', '.join(actions)}"
        
        self.logger.info(msg)
        return msg
    
    def log_backup_event(self, event_type, success=True, details=""):
        """Registrar eventos de backup"""
        status = "✅ EXITOSO" if success else "❌ FALLIDO"
        msg = f"💾 BACKUP {status} | Servidor: {self.server_name} | Tipo: {event_type}"
        if details:
            msg += f" | {details}"
        self.logger.info(msg)
        return msg
    
    def log_rcon_command(self, command, success=True, result=""):
        """Registrar comandos RCON"""
        status = "✅ EXITOSO" if success else "❌ FALLIDO"
        msg = f"🎮 RCON {status} | Servidor: {self.server_name} | Comando: {command}"
        if result and len(result) < 100:  # Solo mostrar resultados cortos
            msg += f" | Resultado: {result.strip()}"
        self.logger.info(msg)
        return msg
    
    def log_mod_operation(self, operation, mod_name, mod_id="", success=True):
        """Registrar operaciones con mods"""
        status = "✅ EXITOSO" if success else "❌ FALLIDO"
        msg = f"🔧 MOD {operation.upper()} {status} | Servidor: {self.server_name} | Mod: {mod_name}"
        if mod_id:
            msg += f" | ID: {mod_id}"
        self.logger.info(msg)
        return msg
    
    def log_config_change(self, config_type, setting_name, old_value="", new_value=""):
        """Registrar cambios de configuración"""
        msg = f"⚙️ CONFIGURACIÓN CAMBIADA | Servidor: {self.server_name} | Archivo: {config_type} | Setting: {setting_name}"
        if old_value and new_value:
            msg += f" | {old_value} → {new_value}"
        self.logger.info(msg)
        return msg
    
    def log_server_crash(self, error_details=""):
        """Registrar caída del servidor"""
        msg = f"💥 SERVIDOR CAÍDO | Servidor: {self.server_name}"
        if error_details:
            msg += f" | Error: {error_details}"
        self.logger.error(msg)
        return msg
    
    def log_custom_event(self, event_name, details="", level="info"):
        """Registrar evento personalizado"""
        msg = f"📋 {event_name.upper()} | Servidor: {self.server_name}"
        if details:
            msg += f" | {details}"
        
        if level.lower() == "error":
            self.logger.error(msg)
        elif level.lower() == "warning":
            self.logger.warning(msg)
        else:
            self.logger.info(msg)
        
        return msg
    
    def get_recent_events(self, hours=24):
        """Obtener eventos recientes del archivo de log"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = Path(f"logs/server_events/server_events_{today}.log")
            
            if not log_file.exists():
                return []
            
            events = []
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Tomar las últimas líneas (más recientes)
                for line in lines[-100:]:  # Últimas 100 líneas
                    if line.strip():
                        events.append(line.strip())
            
            return events
            
        except Exception as e:
            return [f"Error leyendo eventos: {e}"]
    
    def update_server_name(self, new_server_name):
        """Actualizar el nombre del servidor para futuros logs"""
        self.server_name = new_server_name
