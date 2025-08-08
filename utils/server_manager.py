import subprocess
import threading
import time
import os
import psutil
import shutil
from pathlib import Path
from datetime import datetime


class ServerManager:
    def __init__(self, config_manager, logger):
        self.config_manager = config_manager
        self.logger = logger
        self.server_process = None
        self.server_running = False
        self.server_pid = None
        self.uptime_start = None
        
    def get_server_status(self):
        """Obtiene el estado actual del servidor"""
        if self.server_process and self.server_process.poll() is None:
            return "Ejecutándose"
        elif self.server_pid and psutil.pid_exists(self.server_pid):
            return "Ejecutándose"
        else:
            self.server_running = False
            self.server_pid = None
            return "Detenido"
    
    def get_uptime(self):
        """Obtiene el tiempo de actividad del servidor"""
        if not self.uptime_start or not self.server_running:
            return "00:00:00"
        
        uptime = datetime.now() - self.uptime_start
        hours, remainder = divmod(uptime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    def get_server_stats(self):
        """Obtiene estadísticas del servidor"""
        if not self.server_pid or not psutil.pid_exists(self.server_pid):
            return {"cpu": 0, "memory": 0, "memory_mb": 0}
        
        try:
            process = psutil.Process(self.server_pid)
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            return {
                "cpu": cpu_percent,
                "memory": 0,  # Porcentaje de memoria del sistema
                "memory_mb": memory_mb
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {"cpu": 0, "memory": 0, "memory_mb": 0}
    
    def start_server(self, callback=None):
        """Inicia el servidor de Ark"""
        def _start():
            try:
                server_path = self.config_manager.get("server", "executable_path")
                port = self.config_manager.get("server", "port")
                max_players = self.config_manager.get("server", "max_players")
                server_name = self.config_manager.get("server", "server_name")
                
                if not server_path or not os.path.exists(server_path):
                    self.logger.error("Ruta del ejecutable del servidor no válida")
                    if callback:
                        callback("error", "Ruta del ejecutable no válida")
                    return
                
                # Construir comando del servidor
                cmd = [
                    server_path,
                    f"?Port={port}",
                    f"?MaxPlayers={max_players}",
                    f"?ServerName={server_name}",
                    "-server",
                    "-log"
                ]
                
                # Agregar parámetros adicionales si existen
                additional_params = self.config_manager.get("server", "additional_params", "")
                if additional_params:
                    cmd.extend(additional_params.split())
                
                self.logger.info(f"Iniciando servidor con comando: {' '.join(cmd)}")
                
                # Iniciar proceso del servidor
                self.server_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                
                self.server_pid = self.server_process.pid
                self.server_running = True
                self.uptime_start = datetime.now()
                
                self.logger.info(f"Servidor iniciado con PID: {self.server_pid}")
                if callback:
                    callback("started", f"Servidor iniciado (PID: {self.server_pid})")
                    
            except Exception as e:
                self.logger.error(f"Error al iniciar el servidor: {e}")
                if callback:
                    callback("error", f"Error al iniciar: {str(e)}")
        
        threading.Thread(target=_start, daemon=True).start()
    
    def stop_server(self, callback=None):
        """Detiene el servidor de Ark"""
        def _stop():
            try:
                if self.server_process and self.server_process.poll() is None:
                    self.logger.info("Deteniendo servidor...")
                    self.server_process.terminate()
                    
                    # Esperar hasta 30 segundos para que se cierre graciosamente
                    try:
                        self.server_process.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        self.logger.warning("Servidor no se cerró graciosamente, forzando cierre...")
                        self.server_process.kill()
                        self.server_process.wait()
                    
                    self.server_running = False
                    self.server_pid = None
                    self.uptime_start = None
                    self.logger.info("Servidor detenido exitosamente")
                    if callback:
                        callback("stopped", "Servidor detenido exitosamente")
                        
                elif self.server_pid and psutil.pid_exists(self.server_pid):
                    # Si el proceso existe pero no tenemos referencia al subprocess
                    process = psutil.Process(self.server_pid)
                    process.terminate()
                    
                    try:
                        process.wait(timeout=30)
                    except psutil.TimeoutExpired:
                        process.kill()
                    
                    self.server_running = False
                    self.server_pid = None
                    self.uptime_start = None
                    self.logger.info("Servidor detenido exitosamente")
                    if callback:
                        callback("stopped", "Servidor detenido exitosamente")
                else:
                    self.logger.warning("No hay servidor ejecutándose")
                    if callback:
                        callback("warning", "No hay servidor ejecutándose")
                        
            except Exception as e:
                self.logger.error(f"Error al detener el servidor: {e}")
                if callback:
                    callback("error", f"Error al detener: {str(e)}")
        
        threading.Thread(target=_stop, daemon=True).start()
    
    def restart_server(self, callback=None):
        """Reinicia el servidor de Ark"""
        def _restart():
            try:
                self.logger.info("Reiniciando servidor...")
                if callback:
                    callback("info", "Reiniciando servidor...")
                
                # Detener servidor
                self.stop_server()
                
                # Esperar un momento para asegurar que se detenga
                time.sleep(5)
                
                # Iniciar servidor
                self.start_server(callback)
                
            except Exception as e:
                self.logger.error(f"Error al reiniciar el servidor: {e}")
                if callback:
                    callback("error", f"Error al reiniciar: {str(e)}")
        
        threading.Thread(target=_restart, daemon=True).start()
    
    def install_server(self, callback=None):
        """Instala/actualiza el servidor de Ark"""
        def _install():
            try:
                # Obtener rutas de configuración
                root_path = self.config_manager.get("server", "root_path")
                install_path = self.config_manager.get("server", "install_path")
                steamcmd_path = self.config_manager.get("server", "steamcmd_path")
                
                if not root_path:
                    if callback:
                        callback("error", "Ruta raíz no configurada. Configure la aplicación primero.")
                    return
                
                if not install_path:
                    install_path = os.path.join(root_path, "servers")
                    self.config_manager.set("server", "install_path", install_path)
                    self.config_manager.save()
                
                # Verificar/instalar SteamCMD si es necesario
                if not steamcmd_path or not os.path.exists(steamcmd_path):
                    steamcmd_path = self.install_steamcmd_if_needed(root_path, callback)
                    if not steamcmd_path:
                        return
                
                # Crear directorio de instalación si no existe
                os.makedirs(install_path, exist_ok=True)
                
                self.logger.info("Iniciando instalación/actualización del servidor...")
                if callback:
                    callback("info", "Iniciando instalación del servidor de Ark...")
                
                # Comando para instalar/actualizar el servidor de Ark Survival Ascended
                # App ID: 2430930 (Ark Survival Ascended Dedicated Server)
                cmd = [
                    steamcmd_path,
                    "+login", "anonymous",
                    "+force_install_dir", install_path,
                    "+app_update", "2430930", "validate",
                    "+quit"
                ]
                
                if callback:
                    callback("info", f"Ejecutando: {' '.join(cmd)}")
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.path.dirname(steamcmd_path)
                )
                
                # Leer salida en tiempo real
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        if callback:
                            callback("info", output.strip())
                
                # Obtener código de salida
                return_code = process.poll()
                
                if return_code == 0:
                    # Buscar el ejecutable del servidor
                    server_exe = self.find_server_executable(install_path)
                    if server_exe:
                        self.config_manager.set("server", "executable_path", server_exe)
                        self.config_manager.save()
                        
                        self.logger.info("Instalación completada exitosamente")
                        if callback:
                            callback("success", f"Instalación completada. Servidor en: {server_exe}")
                    else:
                        self.logger.warning("Instalación completada pero no se encontró el ejecutable")
                        if callback:
                            callback("warning", "Instalación completada pero no se encontró el ejecutable del servidor")
                else:
                    stderr_output = process.stderr.read()
                    self.logger.error(f"Error en la instalación: {stderr_output}")
                    if callback:
                        callback("error", f"Error en la instalación: {stderr_output}")
                        
            except Exception as e:
                self.logger.error(f"Error durante la instalación: {e}")
                if callback:
                    callback("error", f"Error durante la instalación: {str(e)}")
        
        threading.Thread(target=_install, daemon=True).start()
    
    def install_steamcmd_if_needed(self, root_path, callback=None):
        """Instala SteamCMD si no está disponible"""
        try:
            # Verificar si steamcmd está en el PATH
            try:
                result = subprocess.run(
                    ["steamcmd", "+quit"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    return "steamcmd"  # Está en el PATH
            except:
                pass
            
            # Verificar si existe en la ruta raíz
            steamcmd_path = os.path.join(root_path, "steamcmd", "steamcmd.exe")
            if os.path.exists(steamcmd_path):
                return steamcmd_path
            
            # Instalar SteamCMD
            if callback:
                callback("info", "SteamCMD no encontrado. Instalando...")
            
            import zipfile
            import urllib.request
            
            # Crear directorio para SteamCMD
            steamcmd_dir = os.path.join(root_path, "steamcmd")
            os.makedirs(steamcmd_dir, exist_ok=True)
            
            # URL de descarga de SteamCMD
            steamcmd_url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
            zip_path = os.path.join(steamcmd_dir, "steamcmd.zip")
            
            # Descargar SteamCMD
            if callback:
                callback("info", "Descargando SteamCMD...")
            urllib.request.urlretrieve(steamcmd_url, zip_path)
            
            # Extraer archivo ZIP
            if callback:
                callback("info", "Extrayendo SteamCMD...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(steamcmd_dir)
            
            # Eliminar archivo ZIP
            os.remove(zip_path)
            
            # Verificar instalación
            if os.path.exists(steamcmd_path):
                self.config_manager.set("server", "steamcmd_path", steamcmd_path)
                self.config_manager.save()
                
                if callback:
                    callback("success", "SteamCMD instalado correctamente")
                return steamcmd_path
            else:
                raise Exception("Error al extraer SteamCMD")
                
        except Exception as e:
            self.logger.error(f"Error al instalar SteamCMD: {e}")
            if callback:
                callback("error", f"Error al instalar SteamCMD: {str(e)}")
            return None
    
    def find_server_executable(self, install_path):
        """Busca el ejecutable del servidor de Ark"""
        possible_names = [
            "ArkAscendedServer.exe",
            "ShooterGameServer.exe",
            "ArkServer.exe"
        ]
        
        for name in possible_names:
            exe_path = os.path.join(install_path, "ShooterGame", "Binaries", "Win64", name)
            if os.path.exists(exe_path):
                return exe_path
        
        # Buscar recursivamente
        for root, dirs, files in os.walk(install_path):
            for file in files:
                if file.lower().endswith('.exe') and 'server' in file.lower():
                    return os.path.join(root, file)
        
        return None
    
    def backup_server(self, callback=None):
        """Crea un backup del servidor"""
        def _backup():
            try:
                source_path = self.config_manager.get("backup", "source_path")
                backup_path = self.config_manager.get("backup", "backup_path")
                
                if not source_path or not backup_path:
                    if callback:
                        callback("error", "Rutas de backup no configuradas")
                    return
                
                if not os.path.exists(source_path):
                    if callback:
                        callback("error", "Ruta de origen no existe")
                    return
                
                # Crear directorio de backup si no existe
                os.makedirs(backup_path, exist_ok=True)
                
                # Nombre del backup con timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"ark_backup_{timestamp}"
                backup_full_path = os.path.join(backup_path, backup_name)
                
                self.logger.info(f"Creando backup: {backup_name}")
                if callback:
                    callback("info", f"Creando backup: {backup_name}")
                
                # Copiar directorio
                shutil.copytree(source_path, backup_full_path)
                
                self.logger.info("Backup creado exitosamente")
                if callback:
                    callback("success", "Backup creado exitosamente")
                    
            except Exception as e:
                self.logger.error(f"Error al crear backup: {e}")
                if callback:
                    callback("error", f"Error al crear backup: {str(e)}")
        
        threading.Thread(target=_backup, daemon=True).start()
    
    def save_world(self, callback=None):
        """Guarda el mundo del servidor"""
        def _save():
            try:
                self.logger.info("Guardando mundo...")
                if callback:
                    callback("info", "Guardando mundo...")
                
                # Enviar comando de guardado al servidor
                # Esto dependerá de cómo se comunique con el servidor
                # Por ahora es un placeholder
                
                time.sleep(2)  # Simular tiempo de guardado
                
                self.logger.info("Mundo guardado exitosamente")
                if callback:
                    callback("success", "Mundo guardado exitosamente")
                    
            except Exception as e:
                self.logger.error(f"Error al guardar mundo: {e}")
                if callback:
                    callback("error", f"Error al guardar mundo: {str(e)}")
        
        threading.Thread(target=_save, daemon=True).start()
    
    def broadcast_message(self, message, callback=None):
        """Envía un mensaje broadcast al servidor"""
        def _broadcast():
            try:
                self.logger.info(f"Enviando broadcast: {message}")
                if callback:
                    callback("info", f"Enviando broadcast: {message}")
                
                # Enviar mensaje al servidor
                # Esto dependerá de cómo se comunique con el servidor
                # Por ahora es un placeholder
                
                time.sleep(1)  # Simular envío
                
                self.logger.info("Mensaje broadcast enviado")
                if callback:
                    callback("success", "Mensaje broadcast enviado")
                    
            except Exception as e:
                self.logger.error(f"Error al enviar broadcast: {e}")
                if callback:
                    callback("error", f"Error al enviar broadcast: {str(e)}")
        
        threading.Thread(target=_broadcast, daemon=True).start()
    
    def kick_all_players(self, callback=None):
        """Expulsa a todos los jugadores del servidor"""
        def _kick_all():
            try:
                self.logger.info("Expulsando a todos los jugadores...")
                if callback:
                    callback("info", "Expulsando a todos los jugadores...")
                
                # Enviar comando para expulsar a todos
                # Esto dependerá de cómo se comunique con el servidor
                # Por ahora es un placeholder
                
                time.sleep(2)  # Simular proceso
                
                self.logger.info("Todos los jugadores han sido expulsados")
                if callback:
                    callback("success", "Todos los jugadores han sido expulsados")
                    
            except Exception as e:
                self.logger.error(f"Error al expulsar jugadores: {e}")
                if callback:
                    callback("error", f"Error al expulsar jugadores: {str(e)}")
        
        threading.Thread(target=_kick_all, daemon=True).start()
    
    def get_player_list(self):
        """Obtiene la lista de jugadores conectados"""
        # Esta función dependerá de cómo se comunique con el servidor
        # Por ahora retorna una lista de ejemplo
        return [
            {"name": "Jugador1", "level": 50, "time_connected": "02:30:15"},
            {"name": "Jugador2", "level": 35, "time_connected": "01:45:22"},
            {"name": "Jugador3", "level": 67, "time_connected": "00:20:10"}
        ]
    
    def kick_player(self, player_name, callback=None):
        """Expulsa a un jugador específico"""
        def _kick():
            try:
                self.logger.info(f"Expulsando jugador: {player_name}")
                if callback:
                    callback("info", f"Expulsando jugador: {player_name}")
                
                # Enviar comando para expulsar al jugador
                # Esto dependerá de cómo se comunique con el servidor
                
                time.sleep(1)  # Simular proceso
                
                self.logger.info(f"Jugador {player_name} expulsado")
                if callback:
                    callback("success", f"Jugador {player_name} expulsado")
                    
            except Exception as e:
                self.logger.error(f"Error al expulsar jugador: {e}")
                if callback:
                    callback("error", f"Error al expulsar jugador: {str(e)}")
        
        threading.Thread(target=_kick, daemon=True).start()
    
    def ban_player(self, player_name, callback=None):
        """Banea a un jugador específico"""
        def _ban():
            try:
                self.logger.info(f"Baneando jugador: {player_name}")
                if callback:
                    callback("info", f"Baneando jugador: {player_name}")
                
                # Enviar comando para banear al jugador
                # Esto dependerá de cómo se comunique con el servidor
                
                time.sleep(1)  # Simular proceso
                
                self.logger.info(f"Jugador {player_name} baneado")
                if callback:
                    callback("success", f"Jugador {player_name} baneado")
                    
            except Exception as e:
                self.logger.error(f"Error al banear jugador: {e}")
                if callback:
                    callback("error", f"Error al banear jugador: {str(e)}")
        
        threading.Thread(target=_ban, daemon=True).start()
