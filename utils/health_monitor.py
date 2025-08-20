import threading
import time
import logging
from typing import Optional, Callable, Dict, Any

class HealthMonitor:
    """Monitor de salud automático para servidores ARK individuales y clusters"""
    
    def __init__(self, app_settings, server_manager, cluster_manager=None, main_window=None, logger=None):
        self.app_settings = app_settings
        self.server_manager = server_manager
        self.cluster_manager = cluster_manager
        self.main_window = main_window  # Agregar referencia al main_window
        self.logger = logger or logging.getLogger(__name__)
        
        # Estados de monitoreo
        self.server_monitoring_active = False
        self.cluster_monitoring_active = False
        
        # Hilos de monitoreo
        self.server_monitor_thread = None
        self.cluster_monitor_thread = None
        
        # Contadores de intentos de reinicio
        self.server_restart_attempts = 0
        self.cluster_restart_attempts = {}
        
        # Callbacks para notificaciones
        self.notification_callback = None
        self.status_callback = None
        
    def set_notification_callback(self, callback: Callable[[str, str], None]):
        """Establecer callback para notificaciones (título, mensaje)"""
        self.notification_callback = callback
        
    def set_status_callback(self, callback: Callable[[str], None]):
        """Establecer callback para actualizaciones de estado"""
        self.status_callback = callback
        
    def start_server_monitoring(self):
        """Iniciar monitoreo automático del servidor individual"""
        if not self.app_settings.get_setting('auto_check_server_health', False):
            self.logger.info("Monitoreo de servidor desactivado por configuración")
            return
            
        if self.server_monitoring_active:
            self.logger.warning("El monitoreo del servidor ya está activo")
            return
            
        self.server_monitoring_active = True
        self.server_restart_attempts = 0
        
        self.server_monitor_thread = threading.Thread(
            target=self._server_monitor_loop,
            daemon=True,
            name="ServerHealthMonitor"
        )
        self.server_monitor_thread.start()
        
        self.logger.info("🔍 Monitoreo automático del servidor iniciado")
        self._notify("ARK Server Monitor", "Monitoreo automático del servidor activado")
        
    def start_cluster_monitoring(self):
        """Iniciar monitoreo automático del cluster"""
        if not self.app_settings.get_setting('auto_check_cluster_health', False):
            self.logger.info("Monitoreo de cluster desactivado por configuración")
            return
            
        if not self.cluster_manager:
            self.logger.error("ClusterManager no disponible para monitoreo")
            return
            
        if self.cluster_monitoring_active:
            self.logger.warning("El monitoreo del cluster ya está activo")
            return
            
        self.cluster_monitoring_active = True
        self.cluster_restart_attempts = {}
        
        self.cluster_monitor_thread = threading.Thread(
            target=self._cluster_monitor_loop,
            daemon=True,
            name="ClusterHealthMonitor"
        )
        self.cluster_monitor_thread.start()
        
        self.logger.info("🌐 Monitoreo automático del cluster iniciado")
        self._notify("ARK Cluster Monitor", "Monitoreo automático del cluster activado")
        
    def stop_server_monitoring(self):
        """Detener monitoreo del servidor"""
        self.server_monitoring_active = False
        if self.server_monitor_thread and self.server_monitor_thread.is_alive():
            self.server_monitor_thread.join(timeout=5)
        self.logger.info("🔍 Monitoreo automático del servidor detenido")
        
    def stop_cluster_monitoring(self):
        """Detener monitoreo del cluster"""
        self.cluster_monitoring_active = False
        if self.cluster_monitor_thread and self.cluster_monitor_thread.is_alive():
            self.cluster_monitor_thread.join(timeout=5)
        self.logger.info("🌐 Monitoreo automático del cluster detenido")
        
    def stop_all_monitoring(self):
        """Detener todo el monitoreo"""
        self.stop_server_monitoring()
        self.stop_cluster_monitoring()
        
    def _server_monitor_loop(self):
        """Bucle principal de monitoreo del servidor"""
        interval = self.app_settings.get_setting('server_health_check_interval', 300)
        max_attempts = self.app_settings.get_setting('max_restart_attempts', 3)
        
        self.logger.info(f"Iniciando monitoreo del servidor (intervalo: {interval}s, max intentos: {max_attempts})")
        
        while self.server_monitoring_active:
            try:
                # Verificar si el monitoreo sigue habilitado
                if not self.app_settings.get_setting('auto_check_server_health', False):
                    self.logger.info("Monitoreo del servidor desactivado por configuración, deteniendo...")
                    break
                    
                # Verificar estado del servidor
                status = self.server_manager.get_server_status()
                self.logger.debug(f"Estado del servidor: {status}")
                
                if status == "Detenido":
                    self.logger.warning("⚠️ Servidor detectado como detenido")
                    
                    if self.server_restart_attempts < max_attempts:
                        self.server_restart_attempts += 1
                        self.logger.info(f"🔄 Intento de reinicio {self.server_restart_attempts}/{max_attempts}")
                        
                        self._notify(
                            "ARK Server Monitor", 
                            f"Servidor caído detectado. Intento de reinicio {self.server_restart_attempts}/{max_attempts}"
                        )
                        
                        # Intentar reiniciar el servidor
                        success = self._restart_server()
                        
                        if success:
                            self.logger.info("✅ Servidor reiniciado exitosamente")
                            self.server_restart_attempts = 0  # Resetear contador
                            self._notify("ARK Server Monitor", "Servidor reiniciado exitosamente")
                        else:
                            self.logger.error(f"❌ Fallo al reiniciar servidor (intento {self.server_restart_attempts})")
                            
                    else:
                        self.logger.error(f"❌ Máximo de intentos de reinicio alcanzado ({max_attempts}). Desactivando monitoreo.")
                        self._notify(
                            "ARK Server Monitor", 
                            f"Máximo de intentos de reinicio alcanzado. Monitoreo desactivado."
                        )
                        # Desactivar monitoreo automáticamente
                        self.app_settings.set_setting('auto_check_server_health', False)
                        break
                        
                elif status == "Ejecutándose":
                    # Servidor funcionando correctamente, resetear contador
                    if self.server_restart_attempts > 0:
                        self.logger.info("✅ Servidor funcionando correctamente, reseteando contador de intentos")
                        self.server_restart_attempts = 0
                        
                # Esperar antes de la siguiente verificación
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error en monitoreo del servidor: {e}")
                time.sleep(30)  # Esperar menos tiempo en caso de error
                
        self.server_monitoring_active = False
        self.logger.info("Bucle de monitoreo del servidor terminado")
        
    def _cluster_monitor_loop(self):
        """Bucle principal de monitoreo del cluster"""
        interval = self.app_settings.get_setting('cluster_health_check_interval', 600)
        max_attempts = self.app_settings.get_setting('max_restart_attempts', 3)
        
        self.logger.info(f"Iniciando monitoreo del cluster (intervalo: {interval}s, max intentos: {max_attempts})")
        
        while self.cluster_monitoring_active:
            try:
                # Verificar si el monitoreo sigue habilitado
                if not self.app_settings.get_setting('auto_check_cluster_health', False):
                    self.logger.info("Monitoreo del cluster desactivado por configuración, deteniendo...")
                    break
                    
                # Obtener estado de todos los servidores del cluster
                cluster_status = self.cluster_manager.get_cluster_status()
                
                if cluster_status:
                    failed_servers = []
                    
                    for server_name, server_info in cluster_status.items():
                        status = server_info.get('status', 'Desconocido')
                        
                        if status == "Detenido" or status == "Error":
                            failed_servers.append(server_name)
                            
                            # Verificar intentos de reinicio para este servidor
                            if server_name not in self.cluster_restart_attempts:
                                self.cluster_restart_attempts[server_name] = 0
                                
                            if self.cluster_restart_attempts[server_name] < max_attempts:
                                self.cluster_restart_attempts[server_name] += 1
                                
                                self.logger.warning(
                                    f"⚠️ Servidor del cluster '{server_name}' caído. "
                                    f"Intento {self.cluster_restart_attempts[server_name]}/{max_attempts}"
                                )
                                
                                self._notify(
                                    "ARK Cluster Monitor",
                                    f"Servidor '{server_name}' caído. Reiniciando..."
                                )
                                
                                # Intentar reiniciar el servidor específico
                                success = self._restart_cluster_server(server_name)
                                
                                if success:
                                    self.logger.info(f"✅ Servidor del cluster '{server_name}' reiniciado")
                                    self.cluster_restart_attempts[server_name] = 0
                                else:
                                    self.logger.error(f"❌ Fallo al reiniciar servidor '{server_name}'")
                                    
                            else:
                                self.logger.error(
                                    f"❌ Máximo de intentos alcanzado para servidor '{server_name}'. "
                                    "Omitiendo reinicio automático."
                                )
                                
                        elif status == "Ejecutándose":
                            # Servidor funcionando, resetear contador si había fallos
                            if server_name in self.cluster_restart_attempts and self.cluster_restart_attempts[server_name] > 0:
                                self.logger.info(f"✅ Servidor '{server_name}' funcionando correctamente")
                                self.cluster_restart_attempts[server_name] = 0
                                
                    # Notificar resumen si hay servidores caídos
                    if failed_servers:
                        self.logger.warning(f"Servidores del cluster con problemas: {', '.join(failed_servers)}")
                        
                # Esperar antes de la siguiente verificación
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error en monitoreo del cluster: {e}")
                time.sleep(60)  # Esperar más tiempo en caso de error
                
        self.cluster_monitoring_active = False
        self.logger.info("Bucle de monitoreo del cluster terminado")
        
    def _restart_server(self) -> bool:
        """Reiniciar el servidor individual"""
        try:
            self.logger.info("🔄 Iniciando reinicio automático del servidor...")
            
            # Obtener información del servidor actual desde main_window
            selected_server = None
            selected_map = None
            
            if self.main_window:
                if hasattr(self.main_window, 'selected_server'):
                    selected_server = self.main_window.selected_server
                if hasattr(self.main_window, 'selected_map'):
                    selected_map = self.main_window.selected_map
            
            # Verificar que tenemos la información necesaria
            if not selected_server:
                self.logger.error("No hay servidor seleccionado para reiniciar")
                return False
                
            if not selected_map:
                self.logger.error("No hay mapa seleccionado para reiniciar")
                return False
            
            self.logger.info(f"Reiniciando servidor: {selected_server} con mapa: {selected_map}")
            
            # ✅ CORRECCIÓN: Obtener argumentos personalizados del servidor
            server_args = []
            if (self.main_window and 
                hasattr(self.main_window, 'principal_panel') and 
                hasattr(self.main_window.principal_panel, 'build_server_arguments')):
                try:
                    server_args = self.main_window.principal_panel.build_server_arguments()
                    self.logger.info(f"Argumentos del servidor obtenidos: {len(server_args)} argumentos")
                except Exception as e:
                    self.logger.warning(f"Error al obtener argumentos del servidor: {e}")
                    server_args = []
            else:
                self.logger.warning("No se pudo acceder a principal_panel para obtener argumentos")
            
            # Callback para manejar el resultado del reinicio
            restart_success = {'value': False}
            restart_completed = threading.Event()
            
            def restart_callback(status, message):
                self.logger.info(f"Callback de reinicio: {status} - {message}")
                if status in ["started", "info"]:
                    restart_success['value'] = True
                elif status == "error":
                    restart_success['value'] = False
                restart_completed.set()
                
            # ✅ CORRECCIÓN: Usar el método de reinicio con argumentos personalizados
            self.server_manager.restart_server(
                callback=restart_callback,
                server_name=selected_server,
                map_name=selected_map,
                custom_args=server_args,  # ← ARGUMENTOS PERSONALIZADOS AGREGADOS
                capture_console=True,
                force_stdin=True
            )
            
            # Esperar hasta 60 segundos por el resultado
            if restart_completed.wait(timeout=60):
                return restart_success['value']
            else:
                self.logger.error("Timeout esperando resultado del reinicio")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al reiniciar servidor: {e}")
            return False
            
    def _restart_cluster_server(self, server_name: str) -> bool:
        """Reiniciar un servidor específico del cluster"""
        try:
            self.logger.info(f"🔄 Iniciando reinicio del servidor del cluster: {server_name}")
            
            if not self.cluster_manager:
                self.logger.error("ClusterManager no disponible")
                return False
                
            # Intentar reiniciar el servidor específico del cluster
            success = self.cluster_manager.restart_server(server_name)
            
            if success:
                self.logger.info(f"✅ Servidor del cluster '{server_name}' reiniciado exitosamente")
                return True
            else:
                self.logger.error(f"❌ Fallo al reiniciar servidor del cluster '{server_name}'")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al reiniciar servidor del cluster '{server_name}': {e}")
            return False
            
    def _notify(self, title: str, message: str):
        """Enviar notificación si hay callback disponible"""
        try:
            if self.notification_callback:
                self.notification_callback(title, message)
            if self.status_callback:
                self.status_callback(message)
        except Exception as e:
            self.logger.error(f"Error enviando notificación: {e}")
            
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Obtener estado actual del monitoreo"""
        return {
            'server_monitoring_active': self.server_monitoring_active,
            'cluster_monitoring_active': self.cluster_monitoring_active,
            'server_restart_attempts': self.server_restart_attempts,
            'cluster_restart_attempts': dict(self.cluster_restart_attempts),
            'server_health_check_enabled': self.app_settings.get_setting('auto_check_server_health', False),
            'cluster_health_check_enabled': self.app_settings.get_setting('auto_check_cluster_health', False),
            'server_check_interval': self.app_settings.get_setting('server_health_check_interval', 300),
            'cluster_check_interval': self.app_settings.get_setting('cluster_health_check_interval', 600),
            'max_restart_attempts': self.app_settings.get_setting('max_restart_attempts', 3)
        }