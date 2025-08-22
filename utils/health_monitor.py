import threading
import time
import logging
import os
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
        
        # Esperar el intervalo completo antes de la primera verificación
        self.logger.info(f"⏰ Esperando {interval} segundos antes de la primera verificación...")
        
        # Dormir por chunks para permitir detener el monitoreo si es necesario
        sleep_time = 0
        while sleep_time < interval and self.server_monitoring_active:
            time.sleep(min(30, interval - sleep_time))  # Dormir máximo 30s a la vez
            sleep_time += 30
        
        # Si se detuvo el monitoreo durante la espera, salir
        if not self.server_monitoring_active:
            self.logger.info("Monitoreo detenido durante espera inicial")
            return
        
        self.logger.info("✅ Tiempo de espera inicial completado, iniciando verificaciones periódicas")
        
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
                        self.logger.info(f"🔍 Monitor: Servidor caído detectado. Intento de reinicio {self.server_restart_attempts}/{max_attempts}")
                        success = self._restart_server()
                        
                        if success:
                            self.logger.info("🔍 Monitor: Servidor reiniciado y confirmado como estable")
                            self.server_restart_attempts = 0  # Resetear contador
                            self._notify("ARK Server Monitor", "Servidor reiniciado y confirmado funcionando correctamente")
                        else:
                            self.logger.error(f"🔍 Monitor: Fallo al reiniciar o servidor inestable (intento {self.server_restart_attempts}/{max_attempts})")
                            self._notify("ARK Server Monitor", f"Fallo al reiniciar servidor (intento {self.server_restart_attempts}/{max_attempts})")
                            
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
        
        # Esperar el intervalo completo antes de la primera verificación
        self.logger.info(f"⏰ Esperando {interval} segundos antes de la primera verificación del cluster...")
        
        # Dormir por chunks para permitir detener el monitoreo si es necesario
        sleep_time = 0
        while sleep_time < interval and self.cluster_monitoring_active:
            time.sleep(min(60, interval - sleep_time))  # Dormir máximo 60s a la vez para cluster
            sleep_time += 60
        
        # Si se detuvo el monitoreo durante la espera, salir
        if not self.cluster_monitoring_active:
            self.logger.info("Monitoreo del cluster detenido durante espera inicial")
            return
        
        self.logger.info("✅ Tiempo de espera inicial del cluster completado, iniciando verificaciones periódicas")
        
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
            
            # Obtener información del servidor actual desde main_window y server_panel
            selected_server = None
            selected_map = None
            
            if self.main_window:
                # Intentar obtener desde main_window primero
                if hasattr(self.main_window, 'selected_server') and self.main_window.selected_server:
                    selected_server = self.main_window.selected_server
                if hasattr(self.main_window, 'selected_map') and self.main_window.selected_map:
                    selected_map = self.main_window.selected_map
                
                # Si no hay servidor seleccionado en main_window, intentar desde server_panel
                if not selected_server and hasattr(self.main_window, 'server_panel'):
                    server_panel = self.main_window.server_panel
                    if hasattr(server_panel, 'selected_server') and server_panel.selected_server:
                        selected_server = server_panel.selected_server
                        
                # Si no hay información, intentar cargar la última configuración
                if not selected_server:
                    last_server = self.server_manager.config_manager.get("app", "last_server", "")
                    if last_server:
                        selected_server = last_server
                        self.logger.info(f"🔄 Usando último servidor guardado: {last_server}")
                        
                if not selected_map:
                    last_map = self.server_manager.config_manager.get("app", "last_map", "")
                    if last_map:
                        selected_map = last_map
                        self.logger.info(f"🔄 Usando último mapa guardado: {last_map}")
            
            # Verificar que tenemos la información necesaria
            if not selected_server:
                self.logger.error("❌ No hay servidor seleccionado ni guardado para reiniciar")
                return False
                
            if not selected_map:
                # Si no hay mapa, usar uno por defecto común
                selected_map = "The Island"
                self.logger.warning(f"⚠️ No hay mapa seleccionado, usando por defecto: {selected_map}")
            
            self.logger.info(f"Reiniciando servidor: {selected_server} con mapa: {selected_map}")
            
            # Callback para manejar el resultado del reinicio
            restart_success = {'value': False}
            restart_error = {'value': None}
            restart_completed = threading.Event()
            
            def restart_callback(status, message):
                self.logger.info(f"Callback de reinicio: {status} - {message}")
                if status == "started":
                    # Servidor proceso iniciado, pero necesita verificación adicional
                    self.logger.info("🔄 Proceso iniciado, verificando estabilidad del servidor...")
                    
                    # Resetear posición del console panel para detectar nuevas líneas
                    self._reset_console_log_position()
                    
                    # Programar verificación con reintentos para esperar startup completo
                    def verify_server_stability():
                        max_wait_time = 120  # Máximo 2 minutos para startup completo
                        check_interval = 15  # Verificar cada 15 segundos
                        elapsed_time = 0
                        
                        self.logger.info(f"🔄 Esperando hasta {max_wait_time}s para startup completo del servidor...")
                        
                        while elapsed_time < max_wait_time:
                            time.sleep(check_interval)
                            elapsed_time += check_interval
                            
                            # Verificar estado actual
                            current_status = self.server_manager.get_server_status()
                            self.logger.info(f"⏱️ Verificación {elapsed_time}s: Estado del servidor = {current_status}")
                            
                            if current_status == "Ejecutándose":
                                self.logger.info("✅ Servidor completamente iniciado y funcionando correctamente")
                                restart_success['value'] = True
                                restart_completed.set()
                                return
                            elif current_status == "Detenido":
                                self.logger.error(f"❌ Servidor se detuvo durante el inicio (después de {elapsed_time}s)")
                                restart_success['value'] = False
                                restart_error['value'] = f"Servidor se detuvo durante el inicio"
                                restart_completed.set()
                                return
                            elif current_status == "Iniciando":
                                # Servidor aún iniciando, continuar esperando
                                self.logger.info(f"⏳ Servidor aún iniciando... ({elapsed_time}s/{max_wait_time}s)")
                                continue
                        
                        # Si llegamos aquí, se agotó el tiempo
                        final_status = self.server_manager.get_server_status()
                        self.logger.warning(f"⚠️ Timeout esperando startup completo. Estado final: {final_status}")
                        restart_success['value'] = False
                        restart_error['value'] = f"Timeout esperando startup completo (estado final: {final_status})"
                        restart_completed.set()
                    
                    # Ejecutar verificación en hilo separado
                    threading.Thread(target=verify_server_stability, daemon=True).start()
                    
                elif status == "error":
                    # Error en el reinicio
                    restart_success['value'] = False
                    restart_error['value'] = message
                    restart_completed.set()
                elif status == "info":
                    # Información del proceso, continuar esperando
                    pass
                elif status in ["stopped", "warning"]:
                    # Estados intermedios, continuar esperando
                    pass
                
            # Antes de reiniciar, verificar que existe el ejecutable del servidor
            root_path = self.server_manager.config_manager.get("server", "root_path", "")
            if root_path:
                server_dir = os.path.join(root_path, selected_server)
                executable_path = self.server_manager.find_server_executable(server_dir)
                if not executable_path or not os.path.exists(executable_path):
                    self.logger.error(f"❌ No se encontró ejecutable para servidor '{selected_server}' en '{server_dir}'")
                    return False
                else:
                    self.logger.info(f"✅ Ejecutable encontrado: {executable_path}")
                
            # Obtener argumentos completos usando la misma lógica que el inicio manual
            custom_args = None
            
            # Intentar usar PrincipalPanel para generar argumentos exactos
            if self.main_window and hasattr(self.main_window, 'principal_panel'):
                try:
                    principal_panel = self.main_window.principal_panel
                    if hasattr(principal_panel, 'build_server_arguments'):
                        custom_args = principal_panel.build_server_arguments(selected_server)
                        self.logger.info(f"✅ Argumentos obtenidos del PrincipalPanel: {custom_args}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Error obteniendo argumentos del PrincipalPanel: {e}")
            
            # Si no se pudieron obtener argumentos, usar reinicio básico
            if custom_args:
                # Usar start_server_with_args para reinicio con argumentos completos
                self.logger.info("🔄 Reiniciando con argumentos completos (como inicio manual)")
                
                # Primero detener el servidor
                def stop_and_start():
                    try:
                        # Detener servidor si está corriendo
                        if self.server_manager.is_server_running():
                            self.logger.info("🛑 Deteniendo servidor antes de reiniciar...")
                            
                            stop_success = threading.Event()
                            
                            def stop_callback(status, message):
                                if status in ["stopped", "warning"]:
                                    stop_success.set()
                            
                            self.server_manager.stop_server(stop_callback)
                            
                            # Esperar hasta 30 segundos a que se detenga
                            if stop_success.wait(timeout=30):
                                self.logger.info("✅ Servidor detenido, iniciando con argumentos completos...")
                                time.sleep(3)  # Esperar un poco más
                        
                        # Iniciar con argumentos completos
                        self.server_manager.start_server_with_args(
                            callback=restart_callback,
                            server_name=selected_server,
                            map_name=selected_map,
                            custom_args=custom_args,
                            capture_console=True,
                            force_stdin=True
                        )
                    except Exception as e:
                        self.logger.error(f"Error en detener y reiniciar: {e}")
                        restart_callback("error", f"Error en reinicio: {str(e)}")
                
                # Ejecutar en hilo separado
                threading.Thread(target=stop_and_start, daemon=True).start()
            else:
                # Fallback: usar método básico de reinicio
                self.logger.warning("⚠️ Usando reinicio básico sin argumentos completos")
                self.server_manager.restart_server(
                    callback=restart_callback,
                    server_name=selected_server,
                    map_name=selected_map,
                    capture_console=True,
                    force_stdin=True
                )
            
            # Esperar hasta 180 segundos por el resultado (incluyendo verificación de estabilidad extendida)
            if restart_completed.wait(timeout=180):
                if restart_success['value']:
                    self.logger.info(f"✅ Servidor '{selected_server}' reiniciado exitosamente")
                    return True
                else:
                    error_msg = restart_error['value'] or "Error desconocido"
                    self.logger.error(f"❌ Fallo al reiniciar servidor '{selected_server}': {error_msg}")
                    return False
            else:
                self.logger.error("❌ Timeout esperando resultado del reinicio")
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
            
    def _reset_console_log_position(self):
        """Resetear posición del console panel para detectar nuevas líneas de log"""
        try:
            if self.main_window and hasattr(self.main_window, 'console_panel'):
                console_panel = self.main_window.console_panel
                if console_panel and hasattr(console_panel, 'reset_log_position'):
                    console_panel.reset_log_position()
                    self.logger.info("✅ Posición de console panel reseteada para nuevo startup")
                else:
                    self.logger.warning("⚠️ Console panel no tiene método reset_log_position")
            else:
                self.logger.warning("⚠️ Console panel no disponible para resetear posición")
        except Exception as e:
            self.logger.error(f"Error reseteando posición del console panel: {e}")
    
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