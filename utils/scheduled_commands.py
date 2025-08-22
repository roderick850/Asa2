import json
import threading
import time
from datetime import datetime, timedelta
import os
import logging
from typing import List, Dict, Optional, Callable

class ScheduledCommand:
    """Representa un comando programado"""
    def __init__(self, command_type: str, execution_time: datetime, 
                 parameters: str = "", command_id: str = None):
        self.command_id = command_id or str(int(time.time() * 1000))  # timestamp como ID
        self.command_type = command_type
        self.execution_time = execution_time
        self.parameters = parameters
        self.created_at = datetime.now()
        self.executed = False
        self.execution_result = None
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario para serialización"""
        return {
            'command_id': self.command_id,
            'command_type': self.command_type,
            'execution_time': self.execution_time.isoformat(),
            'parameters': self.parameters,
            'created_at': self.created_at.isoformat(),
            'executed': self.executed,
            'execution_result': self.execution_result
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ScheduledCommand':
        """Crear desde diccionario"""
        cmd = cls(
            command_type=data['command_type'],
            execution_time=datetime.fromisoformat(data['execution_time']),
            parameters=data.get('parameters', ''),
            command_id=data['command_id']
        )
        cmd.created_at = datetime.fromisoformat(data['created_at'])
        cmd.executed = data.get('executed', False)
        cmd.execution_result = data.get('execution_result')
        return cmd
    
    def get_command_string(self) -> str:
        """Obtener el comando completo como string"""
        if self.command_type == 'broadcast':
            return f"broadcast {self.parameters}"
        elif self.command_type == 'saveworld':
            return "saveworld"
        elif self.command_type == 'listplayers':
            return "listplayers"
        elif self.command_type == 'kick':
            return f"kick {self.parameters}"
        elif self.command_type == 'ban':
            return f"ban {self.parameters}"
        elif self.command_type == 'time':
            return "time"
        elif self.command_type == 'weather':
            return "weather"
        elif self.command_type == 'custom':
            return self.parameters
        else:
            return self.parameters

class ScheduledCommandsManager:
    """Gestor de comandos programados"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.tasks_file = os.path.join(data_dir, "scheduled_tasks.json")
        self.history_file = os.path.join(data_dir, "command_history.json")
        
        # Asegurar que el directorio existe
        try:
            os.makedirs(data_dir, exist_ok=True)
        except (OSError, PermissionError):
            # Si falla, usar directorio temporal
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix="ArkSM_scheduled_")
            self.tasks_file = os.path.join(temp_dir, "scheduled_tasks.json")
            self.history_file = os.path.join(temp_dir, "command_history.json")
            print(f"⚠️ ScheduledCommands: Usando directorio temporal: {temp_dir}")
        
        self.scheduled_commands: List[ScheduledCommand] = []
        self.command_history: List[Dict] = []
        self.server_process = None
        self.is_running = False
        self.scheduler_thread = None
        self.logger = logging.getLogger(__name__)
        
        # Callbacks
        self.on_command_executed: Optional[Callable] = None
        self.on_command_failed: Optional[Callable] = None
        
        # Cargar datos existentes
        self.load_tasks()
        self.load_history()
    
    def set_server_process(self, server_process):
        """Establecer el proceso del servidor para enviar comandos"""
        self.server_process = server_process
        
        if server_process is not None:
            # Verificar que stdin esté disponible
            if hasattr(server_process, 'stdin') and server_process.stdin is not None:
                self.logger.info("Proceso del servidor establecido con stdin habilitado")
                # Probar la conexión stdin
                if self.test_stdin_connection():
                    self.logger.info("Conexión stdin verificada exitosamente")
                else:
                    self.logger.warning("Advertencia: No se pudo verificar la conexión stdin")
            else:
                self.logger.error("Proceso del servidor establecido pero stdin no está disponible")
        else:
            self.logger.info("Proceso del servidor establecido como None")
    
    def test_stdin_connection(self) -> bool:
        """Probar la conexión stdin enviando un comando de prueba"""
        if not self.server_process or not hasattr(self.server_process, 'stdin') or self.server_process.stdin is None:
            return False
        
        try:
            # Enviar comando de prueba silencioso
            self.server_process.stdin.write("time\n")
            self.server_process.stdin.flush()
            return True
        except Exception as e:
            self.logger.error(f"Error al probar conexión stdin: {e}")
            return False
    
    def add_scheduled_command(self, command_type: str, execution_time: datetime, 
                            parameters: str = "") -> str:
        """Agregar un nuevo comando programado"""
        command = ScheduledCommand(command_type, execution_time, parameters)
        self.scheduled_commands.append(command)
        self.save_tasks()
        
        self.logger.info(f"Comando programado agregado: {command.get_command_string()} para {execution_time}")
        return command.command_id
    
    def remove_scheduled_command(self, command_id: str) -> bool:
        """Eliminar un comando programado"""
        for i, cmd in enumerate(self.scheduled_commands):
            if cmd.command_id == command_id:
                removed_cmd = self.scheduled_commands.pop(i)
                self.save_tasks()
                self.logger.info(f"Comando programado eliminado: {removed_cmd.get_command_string()}")
                return True
        return False
    
    def get_scheduled_commands(self) -> List[ScheduledCommand]:
        """Obtener lista de comandos programados"""
        # Filtrar comandos no ejecutados y futuros
        now = datetime.now()
        return [cmd for cmd in self.scheduled_commands if not cmd.executed or cmd.execution_time > now]
    
    def get_pending_commands(self) -> List[ScheduledCommand]:
        """Obtener comandos pendientes de ejecución"""
        now = datetime.now()
        return [cmd for cmd in self.scheduled_commands 
                if not cmd.executed and cmd.execution_time <= now]
    
    def execute_manual_command(self, command: str) -> bool:
        """Ejecutar un comando manual inmediatamente"""
        if not self.server_process:
            self.logger.error("No hay proceso del servidor disponible")
            return False
        
        try:
            # Enviar comando al servidor
            self.server_process.stdin.write(f"{command}\n")
            self.server_process.stdin.flush()
            
            # Registrar en historial
            self._add_to_history(command, "manual", True, "Ejecutado manualmente")
            
            self.logger.info(f"Comando manual ejecutado: {command}")
            
            if self.on_command_executed:
                self.on_command_executed(command, "manual")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error ejecutando comando manual '{command}': {e}")
            self._add_to_history(command, "manual", False, str(e))
            
            if self.on_command_failed:
                self.on_command_failed(command, str(e))
            
            return False
    
    def start_scheduler(self):
        """Iniciar el programador de comandos"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        self.logger.info("Programador de comandos iniciado")
    
    def stop_scheduler(self):
        """Detener el programador de comandos"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        self.logger.info("Programador de comandos detenido")
    
    def _scheduler_loop(self):
        """Bucle principal del programador"""
        while self.is_running:
            try:
                # Verificar comandos pendientes cada 5 segundos
                pending_commands = self.get_pending_commands()
                
                for command in pending_commands:
                    if not self.is_running:
                        break
                    
                    self._execute_scheduled_command(command)
                
                time.sleep(5)  # Verificar cada 5 segundos
                
            except Exception as e:
                self.logger.error(f"Error en bucle del programador: {e}")
                time.sleep(10)  # Esperar más tiempo si hay error
    
    def _execute_scheduled_command(self, command: ScheduledCommand):
        """Ejecutar un comando programado"""
        if not self.server_process:
            self.logger.error(f"No hay proceso del servidor para ejecutar: {command.get_command_string()}")
            command.executed = True
            command.execution_result = "Error: No hay proceso del servidor"
            self.save_tasks()
            return
        
        try:
            command_string = command.get_command_string()
            
            # Enviar comando al servidor
            self.server_process.stdin.write(f"{command_string}\n")
            self.server_process.stdin.flush()
            
            # Marcar como ejecutado
            command.executed = True
            command.execution_result = "Ejecutado exitosamente"
            
            # Registrar en historial
            self._add_to_history(command_string, "scheduled", True, "Ejecutado automáticamente")
            
            self.logger.info(f"Comando programado ejecutado: {command_string}")
            
            if self.on_command_executed:
                self.on_command_executed(command_string, "scheduled")
            
        except Exception as e:
            command.executed = True
            command.execution_result = f"Error: {str(e)}"
            
            self.logger.error(f"Error ejecutando comando programado '{command.get_command_string()}': {e}")
            self._add_to_history(command.get_command_string(), "scheduled", False, str(e))
            
            if self.on_command_failed:
                self.on_command_failed(command.get_command_string(), str(e))
        
        finally:
            self.save_tasks()
    
    def _add_to_history(self, command: str, execution_type: str, success: bool, result: str):
        """Agregar comando al historial"""
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'type': execution_type,  # 'manual' o 'scheduled'
            'success': success,
            'result': result
        }
        
        self.command_history.append(history_entry)
        
        # Mantener solo los últimos 1000 registros
        if len(self.command_history) > 1000:
            self.command_history = self.command_history[-1000:]
        
        self.save_history()
    
    def get_command_history(self, limit: int = 100) -> List[Dict]:
        """Obtener historial de comandos"""
        return self.command_history[-limit:] if limit else self.command_history
    
    def save_tasks(self):
        """Guardar tareas programadas en archivo"""
        try:
            data = {
                'tasks': [cmd.to_dict() for cmd in self.scheduled_commands],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error guardando tareas: {e}")
    
    def load_tasks(self):
        """Cargar tareas programadas desde archivo"""
        try:
            if os.path.exists(self.tasks_file):
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.scheduled_commands = [
                    ScheduledCommand.from_dict(task_data) 
                    for task_data in data.get('tasks', [])
                ]
                
                self.logger.info(f"Cargadas {len(self.scheduled_commands)} tareas programadas")
            
        except Exception as e:
            self.logger.error(f"Error cargando tareas: {e}")
            self.scheduled_commands = []
    
    def save_history(self):
        """Guardar historial de comandos en archivo"""
        try:
            data = {
                'history': self.command_history,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error guardando historial: {e}")
    
    def load_history(self):
        """Cargar historial de comandos desde archivo"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.command_history = data.get('history', [])
                
                self.logger.info(f"Cargado historial con {len(self.command_history)} entradas")
            
        except Exception as e:
            self.logger.error(f"Error cargando historial: {e}")
            self.command_history = []
    
    def cleanup_old_tasks(self, days_old: int = 7):
        """Limpiar tareas antiguas ejecutadas"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        original_count = len(self.scheduled_commands)
        self.scheduled_commands = [
            cmd for cmd in self.scheduled_commands 
            if not cmd.executed or cmd.execution_time > cutoff_date
        ]
        
        removed_count = original_count - len(self.scheduled_commands)
        if removed_count > 0:
            self.save_tasks()
            self.logger.info(f"Limpiadas {removed_count} tareas antiguas")
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas del sistema"""
        now = datetime.now()
        pending = len([cmd for cmd in self.scheduled_commands if not cmd.executed and cmd.execution_time > now])
        overdue = len([cmd for cmd in self.scheduled_commands if not cmd.executed and cmd.execution_time <= now])
        executed = len([cmd for cmd in self.scheduled_commands if cmd.executed])
        
        return {
            'total_tasks': len(self.scheduled_commands),
            'pending_tasks': pending,
            'overdue_tasks': overdue,
            'executed_tasks': executed,
            'history_entries': len(self.command_history),
            'scheduler_running': self.is_running,
            'server_connected': self.server_process is not None
        }