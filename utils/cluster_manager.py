#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClusterManager - Gestión de clusters de servidores ARK

Este módulo proporciona funcionalidades para manejar múltiples servidores ARK
como un cluster coordinado, incluyendo:
- Gestión de múltiples instancias de servidor
- Monitoreo consolidado
- Operaciones coordinadas (inicio, parada, reinicio)
- Backup del cluster
- Transferencias entre servidores
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from pathlib import Path

from .server_manager import ServerManager
from .logger import Logger

class ServerInstance:
    """Representa una instancia individual de servidor en el cluster"""
    
    def __init__(self, name: str, config: dict, cluster_manager):
        self.name = name
        self.config = config
        self.cluster_manager = cluster_manager
        self.logger = cluster_manager.logger
        
        # Estado del servidor
        self.status = "stopped"
        self.pid = None
        self.uptime_start = None
        self.last_update = datetime.now()
        
        # Estadísticas
        self.players_online = 0
        self.memory_usage = 0
        self.cpu_usage = 0.0
        self.last_backup = None
        
        # ServerManager individual para este servidor
        self.server_manager = None
        self._initialize_server_manager()
        
        # Thread para monitoreo
        self.monitoring_thread = None
        self.monitoring_active = False
    
    def _initialize_server_manager(self):
        """Inicializar ServerManager para esta instancia"""
        try:
            # Usar el config_manager existente directamente
            # El ServerManager manejará la configuración específica del servidor
            from .config_manager import ConfigManager
            server_config = ConfigManager()
            
            # Actualizar configuración con datos específicos del servidor
            server_config.set("server", "port", str(self.config.get("port", 7777)))
            server_config.set("server", "query_port", str(self.config.get("query_port", 27015)))
            server_config.set("server", "rcon_port", str(self.config.get("rcon_port", 32330)))
            server_config.set("server", "server_name", self.config.get("name", self.name))
            
            # Configurar ruta específica del servidor
            root_path = server_config.get("server", "root_path", "")
            if root_path:
                server_path = os.path.join(root_path, self.name)
                server_config.set("server", "server_path", server_path)
            
            self.server_manager = ServerManager(server_config)
            self.logger.info(f"ServerManager inicializado para {self.name}")
            
        except Exception as e:
            self.logger.error(f"Error inicializando ServerManager para {self.name}: {e}")
    
    def start(self, callback: Optional[Callable] = None) -> bool:
        """Iniciar el servidor"""
        try:
            if self.status == "running":
                if callback:
                    callback("warning", f"Servidor {self.name} ya está ejecutándose")
                return True
            
            if callback:
                callback("info", f"Iniciando servidor {self.name}...")
            
            # Usar ServerManager para iniciar
            if self.server_manager:
                success = self.server_manager.start_server(callback)
                if success:
                    self.status = "running"
                    self.uptime_start = datetime.now()
                    self.start_monitoring()
                    if callback:
                        callback("success", f"Servidor {self.name} iniciado correctamente")
                    return True
                else:
                    if callback:
                        callback("error", f"Error iniciando servidor {self.name}")
                    return False
            else:
                if callback:
                    callback("error", f"ServerManager no disponible para {self.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error iniciando servidor {self.name}: {e}")
            if callback:
                callback("error", f"Error iniciando servidor {self.name}: {e}")
            return False
    
    def stop(self, callback: Optional[Callable] = None) -> bool:
        """Detener el servidor"""
        try:
            if self.status == "stopped":
                if callback:
                    callback("warning", f"Servidor {self.name} ya está detenido")
                return True
            
            if callback:
                callback("info", f"Deteniendo servidor {self.name}...")
            
            # Detener monitoreo
            self.stop_monitoring()
            
            # Usar ServerManager para detener
            if self.server_manager:
                # Crear un callback wrapper para manejar la respuesta asíncrona
                def stop_callback_wrapper(status, message):
                    if status in ["stopped", "warning"]:
                        self.status = "stopped"
                        self.pid = None
                        self.uptime_start = None
                        if callback:
                            callback("success", f"Servidor {self.name} detenido correctamente")
                    else:
                        if callback:
                            callback("error", f"Error deteniendo servidor {self.name}: {message}")
                
                # Llamar al método asíncrono sin esperar retorno
                self.server_manager.stop_server(stop_callback_wrapper)
                return True  # Retornar True inmediatamente ya que es asíncrono
            else:
                if callback:
                    callback("error", f"ServerManager no disponible para {self.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deteniendo servidor {self.name}: {e}")
            if callback:
                callback("error", f"Error deteniendo servidor {self.name}: {e}")
            return False
    
    def restart(self, callback: Optional[Callable] = None) -> bool:
        """Reiniciar el servidor"""
        try:
            if callback:
                callback("info", f"Reiniciando servidor {self.name}...")
            
            # Detener primero
            if not self.stop(callback):
                return False
            
            # Esperar un momento
            time.sleep(5)
            
            # Iniciar de nuevo
            return self.start(callback)
            
        except Exception as e:
            self.logger.error(f"Error reiniciando servidor {self.name}: {e}")
            if callback:
                callback("error", f"Error reiniciando servidor {self.name}: {e}")
            return False
    
    def update_status(self):
        """Actualizar estado del servidor"""
        try:
            if self.server_manager:
                # Verificar si está ejecutándose
                is_running = self.server_manager.is_server_running()
                
                # Log de depuración para entender el estado
                self.logger.debug(f"Actualizando estado de {self.name}: is_running={is_running}, status_actual={self.status}")
                
                if is_running and self.status != "running":
                    self.status = "running"
                    if not self.uptime_start:
                        self.uptime_start = datetime.now()
                    self.logger.info(f"Servidor {self.name} cambiado a estado 'running'")
                elif not is_running and self.status == "running":
                    self.status = "stopped"
                    self.uptime_start = None
                    self.pid = None
                    self.logger.info(f"Servidor {self.name} cambiado a estado 'stopped'")
                
                # Actualizar PID si está ejecutándose
                if is_running:
                    old_pid = self.pid
                    self.pid = getattr(self.server_manager, 'server_pid', None)
                    if old_pid != self.pid:
                        self.logger.info(f"PID actualizado para {self.name}: {old_pid} -> {self.pid}")
                
                # Actualizar estadísticas (implementar según necesidades)
                self._update_stats()
                
                self.last_update = datetime.now()
                
        except Exception as e:
            self.logger.error(f"Error actualizando estado de {self.name}: {e}")
    
    def _update_stats(self):
        """Actualizar estadísticas del servidor"""
        try:
            # Aquí se pueden implementar métricas más avanzadas
            # Por ahora, valores básicos
            if self.status == "running":
                # Simular estadísticas (implementar con psutil o similar)
                self.players_online = 0  # Implementar con RCON
                self.memory_usage = 0    # Implementar con psutil
                self.cpu_usage = 0.0     # Implementar con psutil
            else:
                self.players_online = 0
                self.memory_usage = 0
                self.cpu_usage = 0.0
                
        except Exception as e:
            self.logger.error(f"Error actualizando estadísticas de {self.name}: {e}")
    
    def start_monitoring(self):
        """Iniciar monitoreo del servidor"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                name=f"Monitor-{self.name}",
                daemon=True
            )
            self.monitoring_thread.start()
            self.logger.info(f"Monitoreo iniciado para {self.name}")
    
    def stop_monitoring(self):
        """Detener monitoreo del servidor"""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        self.logger.info(f"Monitoreo detenido para {self.name}")
    
    def _monitoring_loop(self):
        """Loop de monitoreo del servidor"""
        while self.monitoring_active:
            try:
                self.update_status()
                time.sleep(30)  # Actualizar cada 30 segundos
            except Exception as e:
                self.logger.error(f"Error en monitoreo de {self.name}: {e}")
                time.sleep(60)  # Esperar más tiempo si hay error
    
    def get_uptime(self) -> int:
        """Obtener tiempo de actividad en segundos"""
        if self.uptime_start and self.status == "running":
            return int((datetime.now() - self.uptime_start).total_seconds())
        return 0
    
    def to_dict(self) -> dict:
        """Convertir instancia a diccionario para serialización"""
        return {
            "name": self.name,
            "status": self.status,
            "pid": self.pid,
            "uptime": self.get_uptime(),
            "players_online": self.players_online,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "last_backup": self.last_backup.isoformat() if self.last_backup else None,
            "last_update": self.last_update.isoformat(),
            "config": self.config
        }

class ClusterManager:
    """Gestor principal del cluster de servidores ARK"""
    
    def __init__(self, config_manager, logger: Optional[Logger] = None):
        self.config_manager = config_manager
        self.logger = logger or Logger()
        
        # Configuración del cluster
        self.cluster_config = {}
        self.cluster_id = ""
        self.cluster_name = ""
        
        # Instancias de servidores
        self.servers: Dict[str, ServerInstance] = {}
        self.active_servers = set()
        
        # Estado del cluster
        self.cluster_status = {
            "last_update": datetime.now(),
            "total_players": 0,
            "total_memory": 0,
            "average_cpu": 0.0,
            "active_servers": 0
        }
        
        # Archivos de configuración
        self.cluster_config_file = self.config_manager.get_data_file_path("cluster_config.json")
        self.cluster_status_file = self.config_manager.get_data_file_path("cluster_status.json")
        
        # Thread para monitoreo del cluster
        self.cluster_monitoring_thread = None
        self.cluster_monitoring_active = False
        
        # Cargar configuración existente
        self.load_cluster_config()
        
        self.logger.info("ClusterManager inicializado")
    
    def load_cluster_config(self):
        """Cargar configuración del cluster"""
        try:
            if os.path.exists(self.cluster_config_file):
                with open(self.cluster_config_file, 'r', encoding='utf-8') as f:
                    self.cluster_config = json.load(f)
                
                self.cluster_id = self.cluster_config.get("cluster_id", "default_cluster")
                self.cluster_name = self.cluster_config.get("cluster_name", "Mi Cluster ARK")
                
                # Crear instancias de servidores
                servers_config = self.cluster_config.get("servers", {})
                for server_name, server_config in servers_config.items():
                    self.servers[server_name] = ServerInstance(server_name, server_config, self)
                
                self.logger.info(f"Configuración del cluster cargada: {self.cluster_name} ({len(self.servers)} servidores)")
            else:
                self.logger.info("No se encontró configuración de cluster, creando configuración por defecto")
                self.create_default_cluster_config()
                
        except Exception as e:
            self.logger.error(f"Error cargando configuración del cluster: {e}")
            self.create_default_cluster_config()
    
    def create_default_cluster_config(self):
        """Crear configuración por defecto del cluster"""
        self.cluster_config = {
            "cluster_id": "my_ark_cluster",
            "cluster_name": "Mi Cluster ARK",
            "servers": {
                "island": {
                    "name": "The Island",
                    "map": "TheIsland_WP",
                    "port": 7777,
                    "query_port": 27015,
                    "rcon_port": 32330,
                    "priority": 1,
                    "auto_start": True,
                    "transfer_allowed": True
                }
            },
            "shared_settings": {
                "cluster_directory_override": "MyClusterSaves",
                "prevent_download_survivors": False,
                "prevent_download_items": False,
                "prevent_download_dinos": False,
                "prevent_upload_survivors": False,
                "prevent_upload_items": False,
                "prevent_upload_dinos": False,
                "max_tribute_characters": 5,
                "max_tribute_dinos": 10,
                "max_tribute_items": 50
            },
            "backup_settings": {
                "coordinated_backup": True,
                "backup_schedule": "0 2 * * *",
                "retention_days": 7,
                "compress_backups": True
            },
            "monitoring": {
                "check_interval": 30,
                "restart_on_crash": True,
                "max_restart_attempts": 3,
                "notification_webhook": ""
            }
        }
        
        self.cluster_id = self.cluster_config["cluster_id"]
        self.cluster_name = self.cluster_config["cluster_name"]
        
        # Crear instancia por defecto
        self.servers["island"] = ServerInstance("island", self.cluster_config["servers"]["island"], self)
        
        self.save_cluster_config()
        self.logger.info("Configuración por defecto del cluster creada")
    
    def save_cluster_config(self):
        """Guardar configuración del cluster"""
        try:
            with open(self.cluster_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.cluster_config, f, indent=2, ensure_ascii=False)
            self.logger.info("Configuración del cluster guardada")
        except Exception as e:
            self.logger.error(f"Error guardando configuración del cluster: {e}")
    
    def add_server(self, server_name: str, server_config: dict) -> bool:
        """Agregar un nuevo servidor al cluster"""
        try:
            if server_name in self.servers:
                self.logger.warning(f"Servidor {server_name} ya existe en el cluster")
                return False
            
            # Validar configuración
            required_fields = ["name", "map", "port"]
            for field in required_fields:
                if field not in server_config:
                    self.logger.error(f"Campo requerido '{field}' faltante en configuración del servidor")
                    return False
            
            # Verificar que el puerto no esté en uso
            port = server_config["port"]
            for existing_server in self.servers.values():
                if existing_server.config.get("port") == port:
                    self.logger.error(f"Puerto {port} ya está en uso por servidor {existing_server.name}")
                    return False
            
            # Crear instancia del servidor
            self.servers[server_name] = ServerInstance(server_name, server_config, self)
            
            # Actualizar configuración del cluster
            if "servers" not in self.cluster_config:
                self.cluster_config["servers"] = {}
            self.cluster_config["servers"][server_name] = server_config
            self.save_cluster_config()
            
            self.logger.info(f"Servidor {server_name} agregado al cluster")
            return True
            
        except Exception as e:
            self.logger.error(f"Error agregando servidor {server_name}: {e}")
            return False
    
    def remove_server(self, server_name: str) -> bool:
        """Remover un servidor del cluster"""
        try:
            if server_name not in self.servers:
                self.logger.warning(f"Servidor {server_name} no existe en el cluster")
                return False
            
            # Detener servidor si está ejecutándose
            server = self.servers[server_name]
            if server.status == "running":
                server.stop()
            
            # Detener monitoreo
            server.stop_monitoring()
            
            # Remover de estructuras de datos
            del self.servers[server_name]
            self.active_servers.discard(server_name)
            
            # Actualizar configuración
            if "servers" in self.cluster_config and server_name in self.cluster_config["servers"]:
                del self.cluster_config["servers"][server_name]
                self.save_cluster_config()
            
            self.logger.info(f"Servidor {server_name} removido del cluster")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removiendo servidor {server_name}: {e}")
            return False
    
    def start_cluster(self, callback: Optional[Callable] = None) -> bool:
        """Iniciar todo el cluster"""
        try:
            if callback:
                callback("info", f"Iniciando cluster {self.cluster_name}...")
            
            # Obtener servidores ordenados por prioridad
            servers_by_priority = sorted(
                self.servers.items(),
                key=lambda x: x[1].config.get("priority", 999)
            )
            
            success_count = 0
            total_servers = len([s for s in servers_by_priority if s[1].config.get("auto_start", True)])
            
            for server_name, server in servers_by_priority:
                if server.config.get("auto_start", True):
                    if callback:
                        callback("info", f"Iniciando servidor {server_name} ({success_count + 1}/{total_servers})...")
                    
                    if server.start(callback):
                        success_count += 1
                        self.active_servers.add(server_name)
                        # Esperar un poco entre inicios para evitar sobrecarga
                        time.sleep(10)
                    else:
                        if callback:
                            callback("error", f"Error iniciando servidor {server_name}")
            
            # Iniciar monitoreo del cluster
            self.start_cluster_monitoring()
            
            if callback:
                callback("success", f"Cluster iniciado: {success_count}/{total_servers} servidores activos")
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Error iniciando cluster: {e}")
            if callback:
                callback("error", f"Error iniciando cluster: {e}")
            return False
    
    def stop_cluster(self, callback: Optional[Callable] = None) -> bool:
        """Detener todo el cluster"""
        try:
            if callback:
                callback("info", f"Deteniendo cluster {self.cluster_name}...")
            
            # Detener monitoreo del cluster
            self.stop_cluster_monitoring()
            
            success_count = 0
            active_servers = [name for name in self.active_servers if name in self.servers]
            total_servers = len(active_servers)
            
            for server_name in active_servers:
                server = self.servers[server_name]
                if callback:
                    callback("info", f"Deteniendo servidor {server_name} ({success_count + 1}/{total_servers})...")
                
                if server.stop(callback):
                    success_count += 1
                    self.active_servers.discard(server_name)
                else:
                    if callback:
                        callback("error", f"Error deteniendo servidor {server_name}")
            
            if callback:
                callback("success", f"Cluster detenido: {success_count}/{total_servers} servidores detenidos")
            
            return success_count == total_servers
            
        except Exception as e:
            self.logger.error(f"Error deteniendo cluster: {e}")
            if callback:
                callback("error", f"Error deteniendo cluster: {e}")
            return False
    
    def restart_cluster(self, callback: Optional[Callable] = None) -> bool:
        """Reiniciar todo el cluster"""
        try:
            if callback:
                callback("info", f"Reiniciando cluster {self.cluster_name}...")
            
            # Detener cluster
            if not self.stop_cluster(callback):
                if callback:
                    callback("error", "Error deteniendo cluster para reinicio")
                return False
            
            # Esperar un momento
            time.sleep(10)
            
            # Iniciar cluster
            return self.start_cluster(callback)
            
        except Exception as e:
            self.logger.error(f"Error reiniciando cluster: {e}")
            if callback:
                callback("error", f"Error reiniciando cluster: {e}")
            return False
    
    def start_cluster_monitoring(self):
        """Iniciar monitoreo del cluster"""
        if not self.cluster_monitoring_active:
            self.cluster_monitoring_active = True
            self.cluster_monitoring_thread = threading.Thread(
                target=self._cluster_monitoring_loop,
                name="ClusterMonitor",
                daemon=True
            )
            self.cluster_monitoring_thread.start()
            self.logger.info("Monitoreo del cluster iniciado")
    
    def stop_cluster_monitoring(self):
        """Detener monitoreo del cluster"""
        self.cluster_monitoring_active = False
        if self.cluster_monitoring_thread and self.cluster_monitoring_thread.is_alive():
            self.cluster_monitoring_thread.join(timeout=5)
        self.logger.info("Monitoreo del cluster detenido")
    
    def _cluster_monitoring_loop(self):
        """Loop de monitoreo del cluster"""
        while self.cluster_monitoring_active:
            try:
                self.update_cluster_status()
                self.save_cluster_status()
                
                # Verificar si hay servidores que necesitan reinicio
                self._check_server_health()
                
                # Esperar intervalo configurado
                interval = self.cluster_config.get("monitoring", {}).get("check_interval", 30)
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error en monitoreo del cluster: {e}")
                time.sleep(60)
    
    def update_cluster_status(self):
        """Actualizar estado consolidado del cluster"""
        try:
            total_players = 0
            total_memory = 0
            cpu_values = []
            active_count = 0
            
            for server in self.servers.values():
                if server.status == "running":
                    active_count += 1
                    total_players += server.players_online
                    total_memory += server.memory_usage
                    if server.cpu_usage > 0:
                        cpu_values.append(server.cpu_usage)
            
            self.cluster_status = {
                "last_update": datetime.now(),
                "total_players": total_players,
                "total_memory": total_memory,
                "average_cpu": sum(cpu_values) / len(cpu_values) if cpu_values else 0.0,
                "active_servers": active_count
            }
            
        except Exception as e:
            self.logger.error(f"Error actualizando estado del cluster: {e}")
    
    def save_cluster_status(self):
        """Guardar estado del cluster"""
        try:
            status_data = {
                "cluster_id": self.cluster_id,
                "last_update": self.cluster_status["last_update"].isoformat(),
                "servers": {name: server.to_dict() for name, server in self.servers.items()},
                "cluster_stats": {
                    "total_players": self.cluster_status["total_players"],
                    "total_memory": self.cluster_status["total_memory"],
                    "average_cpu": self.cluster_status["average_cpu"],
                    "active_servers": self.cluster_status["active_servers"]
                }
            }
            
            with open(self.cluster_status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error guardando estado del cluster: {e}")
    
    def _check_server_health(self):
        """Verificar salud de los servidores y reiniciar si es necesario"""
        try:
            restart_on_crash = self.cluster_config.get("monitoring", {}).get("restart_on_crash", True)
            if not restart_on_crash:
                return
            
            for server_name, server in self.servers.items():
                if server_name in self.active_servers and server.status != "running":
                    self.logger.warning(f"Servidor {server_name} debería estar ejecutándose pero está {server.status}")
                    
                    # Intentar reiniciar
                    max_attempts = self.cluster_config.get("monitoring", {}).get("max_restart_attempts", 3)
                    restart_count = getattr(server, '_restart_count', 0)
                    
                    if restart_count < max_attempts:
                        self.logger.info(f"Intentando reiniciar servidor {server_name} (intento {restart_count + 1}/{max_attempts})")
                        if server.start():
                            server._restart_count = 0
                        else:
                            server._restart_count = restart_count + 1
                    else:
                        self.logger.error(f"Servidor {server_name} falló {max_attempts} veces, removiendo de servidores activos")
                        self.active_servers.discard(server_name)
                        server._restart_count = 0
                        
        except Exception as e:
            self.logger.error(f"Error verificando salud de servidores: {e}")
    
    def get_cluster_info(self) -> dict:
        """Obtener información completa del cluster"""
        return {
            "cluster_id": self.cluster_id,
            "cluster_name": self.cluster_name,
            "servers": {name: server.to_dict() for name, server in self.servers.items()},
            "cluster_stats": self.cluster_status,
            "config": self.cluster_config
        }
    
    def get_server(self, server_name: str) -> Optional[ServerInstance]:
        """Obtener instancia de servidor específico"""
        return self.servers.get(server_name)
    
    def get_active_servers(self) -> List[str]:
        """Obtener lista de servidores activos"""
        return list(self.active_servers)
    
    def get_server_count(self) -> dict:
        """Obtener conteo de servidores por estado"""
        counts = {"running": 0, "stopped": 0, "starting": 0, "error": 0}
        for server in self.servers.values():
            status = server.status if server.status in counts else "stopped"
            counts[status] += 1
        
        counts["total"] = len(self.servers)
        return counts