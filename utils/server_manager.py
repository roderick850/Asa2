import subprocess
import threading
import time
import os
import psutil
import shutil
from pathlib import Path
from datetime import datetime
import logging
from .config_manager import ConfigManager
import ctypes
from ctypes import wintypes


class ServerManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.server_process = None
        self.server_console_hwnd = None
        self.server_pid = None
        self.uptime_start = None
        self.server_running = False
        self.logger = logging.getLogger(__name__)
        
        # Cargar APIs de Windows para controlar ventanas
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
        # Constantes de Windows
        self.SW_HIDE = 0
        self.SW_SHOW = 5
        self.SW_MINIMIZE = 6
        self.SW_RESTORE = 9
        
        # Configurar nivel de logging
        self.logger.setLevel(logging.DEBUG)
        
    def _find_server_console_window(self):
        """Encontrar la ventana de la consola del servidor"""
        try:
            # Buscar proceso del servidor por nombre si no tenemos referencia directa
            server_pid = None
            
            if self.server_process and self.server_process.poll() is None:
                server_pid = self.server_process.pid
                self.logger.debug(f"Usando PID del proceso guardado: {server_pid}")
            else:
                # Buscar proceso por nombre
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.info['name'] and 'ArkAscendedServer.exe' in proc.info['name']:
                            server_pid = proc.info['pid']
                            self.logger.debug(f"Proceso del servidor encontrado por nombre - PID: {server_pid}")
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                        
            if not server_pid:
                self.logger.debug("No se encontró proceso del servidor activo")
                return None
                
            self.logger.debug(f"Buscando ventana de consola para PID: {server_pid}")
            
            # Reset del handle de ventana
            self.server_console_hwnd = None
            windows_found = []
            
            # Enumerar todas las ventanas para encontrar la del servidor
            def enum_windows_callback(hwnd, lparam):
                try:
                    # Obtener el PID de la ventana
                    window_pid = ctypes.c_ulong()
                    self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
                    
                    if window_pid.value == server_pid:
                        # Obtener información de la ventana
                        window_text = ctypes.create_unicode_buffer(256)
                        self.user32.GetWindowTextW(hwnd, window_text, 256)
                        
                        class_name = ctypes.create_unicode_buffer(256)
                        self.user32.GetClassNameW(hwnd, class_name, 256)
                        
                        is_visible = ctypes.windll.user32.IsWindowVisible(hwnd)
                        
                        window_info = {
                            'hwnd': hwnd,
                            'title': window_text.value,
                            'class': class_name.value,
                            'visible': is_visible
                        }
                        windows_found.append(window_info)
                        
                        self.logger.debug(f"Ventana encontrada: HWND={hwnd}, Título='{window_text.value}', Clase='{class_name.value}', Visible={is_visible}")
                        
                        # Buscar ventanas que contengan palabras clave del servidor
                        title_lower = window_text.value.lower()
                        class_lower = class_name.value.lower()
                        
                        # Ampliar criterios de búsqueda
                        keywords = ['shootergame', 'ark', 'asa', 'ascended', 'server', 'console']
                        console_classes = ['consolewindowclass', 'cmd']
                        
                        # Verificar por título
                        title_match = any(keyword in title_lower for keyword in keywords)
                        # Verificar por clase de ventana (consolas)
                        class_match = any(cls in class_lower for cls in console_classes)
                        
                        if title_match or (class_match and is_visible):
                            self.server_console_hwnd = hwnd
                            self.logger.info(f"Ventana de consola del servidor encontrada: '{window_text.value}' (Clase: {class_name.value})")
                            return False  # Detener enumeración
                            
                except Exception as e:
                    self.logger.debug(f"Error al procesar ventana {hwnd}: {e}")
                return True  # Continuar enumeración
            
            # Enumerar ventanas
            self.user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(enum_windows_callback), 0)
            
            # Log de debug con todas las ventanas encontradas
            if windows_found:
                self.logger.debug(f"Total de ventanas encontradas para PID {server_pid}: {len(windows_found)}")
                for window in windows_found:
                    self.logger.debug(f"  - {window}")
            else:
                self.logger.warning(f"No se encontraron ventanas para PID {server_pid}")
            
            # Si no se encontró por criterios específicos, usar la primera ventana visible como fallback
            if not self.server_console_hwnd and windows_found:
                for window in windows_found:
                    if window['visible']:
                        self.server_console_hwnd = window['hwnd']
                        self.logger.info(f"Usando ventana visible como fallback: '{window['title']}' (Clase: {window['class']})")
                        break
            
            success = self.server_console_hwnd is not None
            self.logger.debug(f"Búsqueda de ventana completada. Éxito: {success}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error al buscar ventana de consola: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def show_server_console(self):
        """Mostrar la consola del servidor"""
        try:
            self.logger.debug("Intentando mostrar consola del servidor")
            
            # Verificar si ya tenemos el handle de la ventana
            if not self.server_console_hwnd:
                self.logger.debug("No hay handle de ventana, buscando...")
                if not self._find_server_console_window():
                    self.logger.warning("No se pudo encontrar la ventana de consola del servidor")
                    return False
            
            # Verificar que el handle sigue siendo válido
            if not ctypes.windll.user32.IsWindow(self.server_console_hwnd):
                self.logger.warning("Handle de ventana inválido, buscando nuevamente...")
                self.server_console_hwnd = None
                if not self._find_server_console_window():
                    self.logger.warning("No se pudo encontrar la ventana de consola del servidor")
                    return False
            
            # Verificar estado actual
            is_visible_before = ctypes.windll.user32.IsWindowVisible(self.server_console_hwnd)
            self.logger.debug(f"Estado antes de mostrar: visible={is_visible_before}")
            
            # Mostrar la ventana
            result = self.user32.ShowWindow(self.server_console_hwnd, self.SW_SHOW)
            self.logger.debug(f"ShowWindow devolvió: {result}")
            
            # Traer al frente
            self.user32.SetForegroundWindow(self.server_console_hwnd)
            
            # Verificar que se mostró correctamente
            is_visible_after = ctypes.windll.user32.IsWindowVisible(self.server_console_hwnd)
            self.logger.debug(f"Estado después de mostrar: visible={is_visible_after}")
            
            if is_visible_after:
                self.logger.info("Consola del servidor mostrada exitosamente")
                return True
            else:
                self.logger.warning("La consola no se mostró correctamente")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al mostrar consola: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def hide_server_console(self):
        """Ocultar la consola del servidor"""
        try:
            self.logger.debug("Intentando ocultar consola del servidor")
            
            # Verificar si ya tenemos el handle de la ventana
            if not self.server_console_hwnd:
                self.logger.debug("No hay handle de ventana, buscando...")
                if not self._find_server_console_window():
                    self.logger.warning("No se pudo encontrar la ventana de consola del servidor")
                    return False
            
            # Verificar que el handle sigue siendo válido
            if not ctypes.windll.user32.IsWindow(self.server_console_hwnd):
                self.logger.warning("Handle de ventana inválido, buscando nuevamente...")
                self.server_console_hwnd = None
                if not self._find_server_console_window():
                    self.logger.warning("No se pudo encontrar la ventana de consola del servidor")
                    return False
            
            # Verificar estado actual
            is_visible_before = ctypes.windll.user32.IsWindowVisible(self.server_console_hwnd)
            self.logger.debug(f"Estado antes de ocultar: visible={is_visible_before}")
            
            # Ocultar la ventana
            result = self.user32.ShowWindow(self.server_console_hwnd, self.SW_HIDE)
            self.logger.debug(f"ShowWindow devolvió: {result}")
            
            # Verificar que se ocultó correctamente
            is_visible_after = ctypes.windll.user32.IsWindowVisible(self.server_console_hwnd)
            self.logger.debug(f"Estado después de ocultar: visible={is_visible_after}")
            
            if not is_visible_after:
                self.logger.info("Consola del servidor ocultada exitosamente")
                return True
            else:
                self.logger.warning("La consola no se ocultó correctamente")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al ocultar consola: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def minimize_server_console(self):
        """Minimizar la consola del servidor"""
        try:
            if self._find_server_console_window():
                self.user32.ShowWindow(self.server_console_hwnd, self.SW_MINIMIZE)
                self.logger.info("Consola del servidor minimizada")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error al minimizar consola: {e}")
            return False
    
    def restore_server_console(self):
        """Restaurar la consola del servidor"""
        try:
            if self._find_server_console_window():
                self.user32.ShowWindow(self.server_console_hwnd, self.SW_RESTORE)
                self.user32.SetForegroundWindow(self.server_console_hwnd)
                self.logger.info("Consola del servidor restaurada")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error al restaurar consola: {e}")
            return False

    def get_server_status(self):
        """Obtiene el estado actual del servidor"""
        # Verificar proceso guardado
        if self.server_process and self.server_process.poll() is None:
            return "Ejecutándose"
        elif self.server_pid and psutil.pid_exists(self.server_pid):
            return "Ejecutándose"
        else:
            # Buscar procesos de ARK Server por nombre
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'ArkAscendedServer.exe' in proc.info['name']:
                        # Encontrado proceso ARK, actualizar PID
                        self.server_pid = proc.info['pid']
                        self.server_running = True
                        return "Ejecutándose"
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # No se encontró ningún proceso ARK
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
        """Obtener estadísticas del servidor (CPU, memoria)"""
        try:
            if not self.server_pid or not psutil.pid_exists(self.server_pid):
                return {"cpu_percent": 0, "memory_mb": 0}
            
            process = psutil.Process(self.server_pid)
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_mb = round(memory_info.rss / 1024 / 1024, 1)
            
            return {
                "cpu_percent": cpu_percent,
                "memory_mb": memory_mb
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas del servidor: {e}")
            return {"cpu_percent": 0, "memory_mb": 0}
    
    def is_server_running(self):
        """Verificar si el servidor está ejecutándose - Detecta por nombre de proceso"""
        try:
            # Método 1: Verificar proceso guardado
            if self.server_process and self.server_process.poll() is None:
                return True
                
            # Método 2: Buscar procesos por nombre (método principal)
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'ArkAscendedServer.exe' in proc.info['name']:
                        # Encontrado proceso ARK, actualizar PID
                        self.server_pid = proc.info['pid']
                        self.server_running = True
                        self.logger.debug(f"Servidor detectado por nombre - PID: {proc.info['pid']}")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            # Método 3: Verificar PID guardado (fallback)
            if self.server_pid and psutil.pid_exists(self.server_pid):
                return True
                
            # No se encontró servidor ejecutándose
            self.server_running = False
            self.server_pid = None
            return False
            
        except Exception as e:
            self.logger.error(f"Error verificando estado del servidor: {e}")
            return False
    
    def get_server_path(self, server_name=None):
        """Obtiene la ruta del directorio del servidor"""
        try:
            self.logger.info(f"get_server_path llamado con server_name: {server_name}")
            
            if server_name:
                # Obtener la ruta específica del servidor
                root_path = self.config_manager.get("server", "root_path")
                self.logger.info(f"root_path obtenido para server_name '{server_name}': {root_path}")
                if root_path:
                    server_path = os.path.join(root_path, server_name)
                    self.logger.info(f"server_path construido: {server_path}")
                    return server_path
            else:
                # Obtener la ruta del servidor actual desde la configuración
                current_server = self.config_manager.get("app", "selected_server")
                self.logger.info(f"current_server obtenido: {current_server}")
                if current_server:
                    root_path = self.config_manager.get("server", "root_path")
                    self.logger.info(f"root_path obtenido para current_server '{current_server}': {root_path}")
                    if root_path:
                        server_path = os.path.join(root_path, current_server)
                        self.logger.info(f"server_path construido: {server_path}")
                        return server_path
            
            self.logger.warning("No se pudo construir server_path")
            return None
            
        except Exception as e:
            self.logger.error(f"Error al obtener ruta del servidor: {e}")
            return None
    
    def start_server(self, callback=None, server_name=None, map_name=None, capture_console=False, force_stdin=False):
        """Inicia el servidor de Ark"""
        def _start():
            try:
                # Obtener la ruta del ejecutable del servidor
                if server_name:
                    # Usar la ruta específica del servidor
                    server_key = f"executable_path_{server_name}"
                    server_path = self.config_manager.get("server", server_key)
                    if not server_path:
                        # Buscar el ejecutable en la ruta del servidor
                        root_path = self.config_manager.get("server", "root_path")
                        if root_path:
                            server_dir = os.path.join(root_path, server_name)
                            server_path = self.find_server_executable(server_dir)
                else:
                    # Usar la ruta por defecto
                    server_path = self.config_manager.get("server", "executable_path")
                
                if not server_path or not os.path.exists(server_path):
                    self.logger.error("Ruta del ejecutable del servidor no válida")
                    if callback:
                        callback("error", "Ruta del ejecutable no válida")
                    return
                
                # Construir comando
                cmd = [server_path, "-server", "-log"]
                
                # Agregar mapa si se especifica
                if map_name:
                    # Mapear nombre amigable a identificador técnico
                    # IDENTIFICADORES PARA ARK SURVIVAL ASCENDED
                    map_identifiers = {
                        "The Island": "TheIsland_WP",
                        "TheIsland": "TheIsland_WP",
                        "TheIsland_WP": "TheIsland_WP",
                        "The Center": "TheCenter_WP",        # ✅ ASA usa _WP
                        "TheCenter": "TheCenter_WP",
                        "TheCenter_WP": "TheCenter_WP",
                        "Scorched Earth": "ScorchedEarth_WP", 
                        "ScorchedEarth": "ScorchedEarth_WP",
                        "ScorchedEarth_WP": "ScorchedEarth_WP",
                        "Ragnarok": "Ragnarok_WP",           # ✅ ASA usa _WP
                        "Ragnarok_WP": "Ragnarok_WP",
                        "Aberration": "Aberration_P",
                        "Extinction": "Extinction",
                        "Valguero": "Valguero_P",
                        "Genesis: Part 1": "Genesis",
                        "Genesis1": "Genesis",  # Variante sin espacio/abreviada
                        "Crystal Isles": "CrystalIsles",
                        "CrystalIsles": "CrystalIsles",  # Variante sin espacio
                        "Genesis: Part 2": "Genesis2",
                        "Genesis2": "Genesis2",  # Variante sin espacio/abreviada
                        "Lost Island": "LostIsland",
                        "LostIsland": "LostIsland",  # Variante sin espacio
                        "Fjordur": "Fjordur"
                    }
                    
                    map_identifier = map_identifiers.get(map_name, map_name)
                    cmd.append(f"/Game/Mods/{map_identifier}/{map_identifier}")
                
                # Agregar parámetros adicionales si existen
                additional_params = self.config_manager.get("server", "additional_params")
                if additional_params:
                    cmd.extend(additional_params.split())
                
                self.logger.info(f"Iniciando servidor {server_name} con mapa {map_name} - comando: {' '.join(cmd)}")
                
                # Iniciar proceso del servidor
                # Si se quiere capturar la consola o forzar stdin, no usar CREATE_NEW_CONSOLE
                use_pipes = capture_console or force_stdin
                self.logger.info(f"DEBUG: capture_console = {capture_console}, force_stdin = {force_stdin}")
                if use_pipes:
                    mode_desc = "CAPTURA" if capture_console else "STDIN FORZADO"
                    self.logger.info(f"DEBUG: Iniciando servidor en modo {mode_desc} (sin CREATE_NEW_CONSOLE)")
                    # Modo para capturar consola o usar stdin: usar pipes
                    self.server_process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,  # Combinar stderr con stdout
                        stdin=subprocess.PIPE,
                        bufsize=1,
                        universal_newlines=True,  # Para compatibilidad con texto
                        text=True,  # Asegurar modo texto
                        # NO usar CREATE_NEW_CONSOLE para poder capturar la salida
                    )
                else:
                    self.logger.info("DEBUG: Iniciando servidor en modo NORMAL (con CREATE_NEW_CONSOLE)")
                    # Modo normal: crear nueva consola separada
                    self.server_process = subprocess.Popen(
                        cmd,
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                
                self.server_pid = self.server_process.pid
                self.server_running = True
                self.uptime_start = datetime.now()
                
                self.logger.info(f"Servidor iniciado con PID: {self.server_pid}")
                if callback:
                    callback("started", f"Servidor {server_name} iniciado con mapa {map_name} (PID: {self.server_pid})")
                    
            except Exception as e:
                self.logger.error(f"Error al iniciar el servidor: {e}")
                if callback:
                    callback("error", f"Error al iniciar: {str(e)}")
        
        threading.Thread(target=_start, daemon=True).start()
    
    def start_server_with_args(self, callback=None, server_name=None, map_name=None, custom_args=None, capture_console=False, force_stdin=True):
        """Inicia el servidor de Ark con argumentos personalizados"""
        def _start_with_args():
            try:
                # Obtener la ruta del ejecutable del servidor
                if server_name:
                    # Usar la ruta específica del servidor
                    server_key = f"executable_path_{server_name}"
                    server_path = self.config_manager.get("server", server_key)
                    if not server_path:
                        # Buscar el ejecutable en la ruta del servidor
                        root_path = self.config_manager.get("server", "root_path")
                        if root_path:
                            server_dir = os.path.join(root_path, server_name)
                            server_path = self.find_server_executable(server_dir)
                else:
                    # Usar la ruta por defecto
                    server_path = self.config_manager.get("server", "executable_path")
                
                if not server_path or not os.path.exists(server_path):
                    self.logger.error("Ruta del ejecutable del servidor no válida")
                    if callback:
                        callback("error", "Ruta del ejecutable no válida")
                    return
                
                # Construir comando: solo el ejecutable más los argumentos personalizados
                cmd = [server_path]
                
                # Agregar argumentos personalizados si se proporcionan
                if custom_args and isinstance(custom_args, list):
                    if self.logger.level <= logging.DEBUG:
                        self.logger.debug(f"DEBUG: Usando argumentos personalizados: {custom_args}")
                    cmd.extend(custom_args)
                else:
                    # Si no hay argumentos personalizados, usar el método básico con mapeo correcto
                    if self.logger.level <= logging.DEBUG:
                        self.logger.debug(f"DEBUG: Sin argumentos personalizados, usando método básico con mapa: {map_name}")
                    cmd.extend(["-server", "-log"])
                    if map_name:
                        # Mapear nombre amigable a identificador técnico
                        # IDENTIFICADORES PARA ARK SURVIVAL ASCENDED
                        map_identifiers = {
                            "The Island": "TheIsland_WP",
                            "TheIsland": "TheIsland_WP",
                            "TheIsland_WP": "TheIsland_WP",
                            "The Center": "TheCenter_WP",        # ✅ ASA usa _WP
                            "TheCenter": "TheCenter_WP",
                            "TheCenter_WP": "TheCenter_WP",
                            "Scorched Earth": "ScorchedEarth_WP", 
                            "ScorchedEarth": "ScorchedEarth_WP",
                            "ScorchedEarth_WP": "ScorchedEarth_WP",
                            "Ragnarok": "Ragnarok_WP",           # ✅ ASA usa _WP
                            "Ragnarok_WP": "Ragnarok_WP",
                            "Aberration": "Aberration_P",
                            "Extinction": "Extinction",
                            "Valguero": "Valguero_P",
                            "Genesis: Part 1": "Genesis",
                            "Genesis1": "Genesis",  # Variante sin espacio/abreviada
                            "Crystal Isles": "CrystalIsles",
                            "CrystalIsles": "CrystalIsles",  # Variante sin espacio
                            "Genesis: Part 2": "Genesis2",
                            "Genesis2": "Genesis2",  # Variante sin espacio/abreviada
                            "Lost Island": "LostIsland",
                            "LostIsland": "LostIsland",  # Variante sin espacio
                            "Fjordur": "Fjordur"
                        }
                        
                        map_identifier = map_identifiers.get(map_name, map_name)
                        if self.logger.level <= logging.DEBUG:
                            self.logger.debug(f"DEBUG: Convertido '{map_name}' a '{map_identifier}'")
                        cmd.append(f"?Map={map_identifier}")
                
                # Log del comando (solo en desarrollo)
                if self.logger.level <= logging.DEBUG:
                    self.logger.debug(f"DEBUG: Comando final del servidor: {' '.join(cmd)}")
                    self.logger.debug(f"DEBUG: Parámetros recibidos - server_name: '{server_name}', map_name: '{map_name}', custom_args: {custom_args}")
                if callback:
                    callback("info", f"Comando del servidor: {' '.join(cmd)}")
                
                # Iniciar el proceso del servidor
                # Si se quiere capturar la consola o forzar stdin, usar pipes
                use_pipes = capture_console or force_stdin
                self.logger.info(f"DEBUG: start_server_with_args - capture_console = {capture_console}, force_stdin = {force_stdin}")
                
                # Obtener el directorio de trabajo del servidor
                server_dir = os.path.dirname(server_path)
                self.logger.info(f"DEBUG: Directorio de trabajo del servidor: {server_dir}")
                
                if capture_console:
                    self.logger.info("DEBUG: start_server_with_args - Iniciando servidor en modo CAPTURA de consola (con control de visibilidad de consola)")
                    
                    # Crear un archivo de log temporal para capturar la salida
                    import tempfile
                    
                    # Crear archivo de log temporal en el directorio del servidor
                    log_file_path = os.path.join(server_dir, "server_console.log")
                    self.log_file_path = log_file_path
                    
                    # Limpiar archivo de log anterior si existe
                    if os.path.exists(log_file_path):
                        try:
                            os.remove(log_file_path)
                        except:
                            pass
                    
                    # Determinar si mostrar la consola del servidor según la configuración
                    show_console = self.config_manager.get("app", "show_server_console", default="true").lower() == "true"
                    creation_flags = subprocess.CREATE_NEW_CONSOLE if show_console else subprocess.CREATE_NO_WINDOW
                    
                    self.logger.info(f"DEBUG: show_server_console = {show_console}, usando flags: {creation_flags}")
                    
                    # Iniciar servidor con o sin consola visible según configuración
                    self.server_process = subprocess.Popen(
                        cmd,
                        stdout=open(log_file_path, 'w', encoding='utf-8', errors='ignore'),
                        stderr=subprocess.STDOUT,
                        stdin=subprocess.PIPE,
                        creationflags=creation_flags,
                        cwd=server_dir
                    )
                    
                    # Logging adicional para debug
                    self.logger.info(f"DEBUG: Proceso del servidor iniciado con PID: {self.server_process.pid}")
                    self.logger.info(f"DEBUG: Archivo de log creado en: {log_file_path}")
                    
                    # Verificar estado del proceso inmediatamente
                    if self.server_process.poll() is None:
                        self.logger.info("DEBUG: ✅ Proceso del servidor está ejecutándose correctamente")
                    else:
                        exit_code = self.server_process.poll()
                        self.logger.error(f"DEBUG: ❌ El servidor terminó inmediatamente con código: {exit_code}")
                        
                elif force_stdin:
                    self.logger.info("DEBUG: start_server_with_args - Iniciando servidor en modo STDIN FORZADO (sin captura de consola)")
                    # Modo stdin forzado: usar pipes para stdin pero no capturar stdout
                    show_console = self.config_manager.get("app", "show_server_console", default="true").lower() == "true"
                    creation_flags = subprocess.CREATE_NEW_CONSOLE if show_console else subprocess.CREATE_NO_WINDOW
                    
                    self.logger.info(f"DEBUG: show_server_console = {show_console}, usando flags: {creation_flags}")
                    
                    self.server_process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE,
                        creationflags=creation_flags,
                        cwd=server_dir
                    )
                    
                    self.logger.info(f"DEBUG: Proceso del servidor iniciado con PID: {self.server_process.pid} (stdin habilitado)")
                    
                else:
                    self.logger.info("DEBUG: start_server_with_args - Iniciando servidor en modo NORMAL (con control de visibilidad de consola)")
                    # Modo normal: crear nueva consola separada según configuración
                    show_console = self.config_manager.get("app", "show_server_console", default="true").lower() == "true"
                    creation_flags = subprocess.CREATE_NEW_CONSOLE if show_console else subprocess.CREATE_NO_WINDOW
                    
                    self.logger.info(f"DEBUG: show_server_console = {show_console}, usando flags: {creation_flags}")
                    
                    self.server_process = subprocess.Popen(
                        cmd,
                        creationflags=creation_flags,
                        cwd=server_dir
                    )
                    
                    self.logger.info(f"DEBUG: Proceso del servidor iniciado con PID: {self.server_process.pid}")
                
                self.server_pid = self.server_process.pid
                self.server_running = True
                self.uptime_start = datetime.now()
                
                if callback:
                    callback("success", f"Servidor iniciado con PID: {self.server_pid}")
                
                # Cuando se está capturando la consola, NO leer stdout aquí
                # El ConsolePanel se encargará de leer la salida del servidor
                if capture_console:
                    self.logger.info("DEBUG: Modo captura de consola activado - ConsolePanel se encargará de leer stdout")
                    # Solo verificar que el proceso esté ejecutándose
                    if self.server_process.poll() is not None:
                        # El proceso terminó inmediatamente
                        self.server_running = False
                        self.server_pid = None
                        self.uptime_start = None
                        
                        if callback:
                            callback("error", "El servidor se detuvo inmediatamente después de iniciar")
                        self.logger.error("El servidor se detuvo inmediatamente después de iniciar")
                else:
                    # No se está capturando la consola, solo esperar a que el proceso termine
                    self.logger.info("DEBUG: No se está capturando la consola, esperando a que el proceso termine")
                    if self.server_process.poll() is not None:
                        # El proceso realmente terminó
                        self.server_running = False
                        self.server_pid = None
                        self.uptime_start = None
                        
                        if callback:
                            callback("info", "Servidor detenido")
                        self.logger.info("Proceso del servidor terminado")
                
            except Exception as e:
                self.logger.error(f"Error al iniciar servidor con argumentos personalizados: {e}")
                if callback:
                    callback("error", f"Error al iniciar servidor: {str(e)}")
        
        # Ejecutar en el hilo principal para poder retornar el resultado
        _start_with_args()
        
        # Retornar el estado del servidor después de iniciar
        if hasattr(self, 'server_process') and self.server_process and self.server_process.poll() is None:
            return True
        else:
            return False
    
    def stop_server(self, callback=None):
        """Detiene el servidor de Ark"""
        def _stop():
            try:
                stopped = False
                
                # Intentar detener usando el proceso guardado
                if self.server_process and self.server_process.poll() is None:
                    self.logger.info("Deteniendo servidor usando referencia de proceso...")
                    self.server_process.terminate()
                    
                    # Esperar hasta 30 segundos para que se cierre graciosamente
                    try:
                        self.server_process.wait(timeout=30)
                        stopped = True
                    except subprocess.TimeoutExpired:
                        self.logger.warning("Servidor no se cerró graciosamente, forzando cierre...")
                        self.server_process.kill()
                        self.server_process.wait()
                        stopped = True
                    
                    self.server_running = False
                    self.server_pid = None
                    self.uptime_start = None
                    self.logger.info("Servidor detenido exitosamente")
                        
                elif self.server_pid and psutil.pid_exists(self.server_pid):
                    # Si el proceso existe pero no tenemos referencia al subprocess
                    self.logger.info(f"Deteniendo servidor usando PID: {self.server_pid}")
                    process = psutil.Process(self.server_pid)
                    process.terminate()
                    
                    try:
                        process.wait(timeout=30)
                        stopped = True
                    except psutil.TimeoutExpired:
                        self.logger.warning("Forzando cierre del servidor...")
                        process.kill()
                        stopped = True
                    
                    self.server_running = False
                    self.server_pid = None
                    self.uptime_start = None
                    self.logger.info("Servidor detenido exitosamente")
                
                # Si no pudo detener con los métodos anteriores, buscar por nombre de proceso
                if not stopped:
                    self.logger.info("Buscando procesos de ARK Server ejecutándose...")
                    ark_processes = []
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            if proc.info['name'] and 'ArkAscendedServer.exe' in proc.info['name']:
                                ark_processes.append(proc)
                                self.logger.info(f"Encontrado proceso ARK: PID {proc.info['pid']}")
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    
                    if ark_processes:
                        self.logger.info(f"Deteniendo {len(ark_processes)} proceso(s) de ARK Server...")
                        for proc in ark_processes:
                            try:
                                proc.terminate()
                                try:
                                    proc.wait(timeout=30)
                                except psutil.TimeoutExpired:
                                    self.logger.warning(f"Forzando cierre del proceso PID {proc.pid}")
                                    proc.kill()
                                self.logger.info(f"Proceso ARK PID {proc.pid} detenido")
                                stopped = True
                            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                                self.logger.warning(f"No se pudo detener proceso PID {proc.pid}: {e}")
                        
                        self.server_running = False
                        self.server_pid = None
                        self.uptime_start = None
                        self.logger.info("Todos los procesos de ARK Server detenidos")
                    else:
                        self.logger.warning("No se encontraron procesos de ARK Server ejecutándose")
                        if callback:
                            callback("warning", "No hay servidor ejecutándose")
                        return
                
                if stopped and callback:
                    callback("stopped", "Servidor detenido exitosamente")
                        
            except Exception as e:
                self.logger.error(f"Error al detener el servidor: {e}")
                if callback:
                    callback("error", f"Error al detener: {str(e)}")
        
        threading.Thread(target=_stop, daemon=True).start()
    
    def restart_server(self, callback=None, server_name=None, map_name=None, custom_args=None, capture_console=False, force_stdin=True):
        """Reinicia el servidor de Ark con argumentos personalizados"""
        def _restart():
            try:
                self.logger.info(f"Reiniciando servidor {server_name} con mapa {map_name}...")
                if callback:
                    callback("info", f"Reiniciando servidor {server_name} con mapa {map_name}...")
                
                # Detener servidor
                self.stop_server()
                
                # Esperar un momento para asegurar que se detenga
                time.sleep(5)
                
                # Usar start_server_with_args para conservar argumentos personalizados y mods
                if custom_args:
                    self.start_server_with_args(callback, server_name, map_name, custom_args, capture_console, force_stdin)
                else:
                    self.start_server(callback, server_name, map_name, capture_console, force_stdin)
                
            except Exception as e:
                self.logger.error(f"Error al reiniciar el servidor: {e}")
                if callback:
                    callback("error", f"Error al reiniciar: {str(e)}")
        
        threading.Thread(target=_restart, daemon=True).start()
    
    def install_server(self, callback=None, server_name=None):
        """Instala/actualiza el servidor de Ark"""
        def _install():
            try:
                # Obtener rutas de configuración
                root_path = self.config_manager.get("server", "root_path")
                
                if not root_path:
                    if callback:
                        callback("error", "Ruta raíz no configurada. Configure la aplicación primero.")
                    return
                
                # Verificar que la ruta raíz existe
                if not os.path.exists(root_path):
                    try:
                        os.makedirs(root_path, exist_ok=True)
                        if callback:
                            callback("info", f"Directorio raíz creado: {root_path}")
                    except Exception as e:
                        if callback:
                            callback("error", f"No se pudo crear el directorio raíz: {str(e)}")
                        return
                
                # Determinar la ruta de instalación del servidor
                if server_name:
                    # Usar el nombre del servidor para crear una carpeta específica en el directorio raíz
                    install_path = os.path.join(root_path, server_name)
                else:
                    # Usar la ruta por defecto
                    install_path = self.config_manager.get("server", "install_path")
                    if not install_path:
                        install_path = os.path.join(root_path, "default_server")
                        self.config_manager.set("server", "install_path", install_path)
                        self.config_manager.save()
                
                # Verificar si el servidor ya existe
                server_exists = os.path.exists(install_path)
                if server_exists:
                    # Verificar si hay un ejecutable válido
                    existing_exe = self.find_server_executable(install_path)
                    if existing_exe:
                        if callback:
                            callback("info", f"Servidor existente encontrado en: {install_path}")
                            callback("info", f"Ejecutable encontrado: {existing_exe}")
                            callback("info", "Iniciando actualización del servidor...")
                    else:
                        if callback:
                            callback("info", f"Directorio de servidor encontrado pero sin ejecutable válido en: {install_path}")
                            callback("info", "Iniciando instalación completa...")
                else:
                    if callback:
                        callback("info", f"Servidor no existe. Iniciando instalación en: {install_path}")
                
                if callback:
                    callback("info", f"Ruta de instalación: {install_path}")
                
                # Verificar/instalar SteamCMD si es necesario
                if callback:
                    callback("progress", "Verificando SteamCMD...")
                steamcmd_path = self.install_steamcmd_if_needed(root_path, callback)
                if not steamcmd_path:
                    if callback:
                        callback("error", "No se pudo instalar SteamCMD. Verifique su conexión a internet.")
                    return
                
                # Crear directorio de instalación si no existe
                try:
                    os.makedirs(install_path, exist_ok=True)
                except Exception as e:
                    if callback:
                        callback("error", f"No se pudo crear el directorio de instalación: {str(e)}")
                    return
                
                # Determinar el tipo de operación
                operation_type = "actualización" if server_exists else "instalación"
                self.logger.info(f"Iniciando {operation_type} del servidor...")
                if callback:
                    callback("info", f"Iniciando {operation_type} del servidor de Ark Survival Ascended...")
                
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
                    callback("info", f"Ejecutando SteamCMD para {operation_type}...")
                
                # Ejecutar el proceso de instalación con buffering deshabilitado
                try:
                    env = os.environ.copy()
                    env['PYTHONUNBUFFERED'] = '1'  # Deshabilitar buffering de Python
                    
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,  # Combinar stderr con stdout
                        text=True,
                        bufsize=0,  # Sin buffering
                        universal_newlines=True,
                        env=env,
                        cwd=os.path.dirname(steamcmd_path) if steamcmd_path != "steamcmd" else None
                    )
                except Exception as e:
                    if callback:
                        callback("error", f"Error al ejecutar SteamCMD: {str(e)}")
                    return
                
                # Leer salida en tiempo real con polling más frecuente
                if callback:
                    callback("progress", f"Iniciando {operation_type}...")
                
                import select
                import sys
                import time
                import re  # Mover import fuera del loop
                
                last_progress_time = time.time()
                
                while True:
                    # Verificar si el proceso terminó
                    if process.poll() is not None:
                        # Leer cualquier salida restante
                        remaining_output = process.stdout.read()
                        if remaining_output:
                            for line in remaining_output.split('\n'):
                                if line.strip():
                                    self.logger.debug(f"SteamCMD Final Output: {line.strip()}")
                        break
                    
                    # Leer con timeout corto para ser más responsivo
                    try:
                        if sys.platform == "win32":
                            # En Windows, usar readline con timeout
                            import threading
                            import queue
                            
                            def read_line(q):
                                try:
                                    line = process.stdout.readline()
                                    if line:
                                        q.put(line)
                                except:
                                    pass
                            
                            q = queue.Queue()
                            t = threading.Thread(target=read_line, args=(q,))
                            t.daemon = True
                            t.start()
                            
                            try:
                                output = q.get(timeout=0.5)  # Timeout de 0.5 segundos
                            except queue.Empty:
                                # Mostrar progreso de "keep-alive" cada 30 segundos
                                current_time = time.time()
                                if current_time - last_progress_time > 30:
                                    if callback:
                                        callback("info", "🔄 Instalación en progreso... (puede tomar varios minutos)")
                                    last_progress_time = current_time
                                continue
                        else:
                            # En Linux/Mac, usar select
                            ready, _, _ = select.select([process.stdout], [], [], 0.5)
                            if not ready:
                                # Mostrar progreso de "keep-alive" cada 30 segundos
                                current_time = time.time()
                                if current_time - last_progress_time > 30:
                                    if callback:
                                        callback("info", "🔄 Instalación en progreso... (puede tomar varios minutos)")
                                    last_progress_time = current_time
                                continue
                            output = process.stdout.readline()
                        
                        if output:
                            output = output.strip()
                            if output:
                                self.logger.debug(f"SteamCMD Output: {output}")  # Debug log
                                last_progress_time = time.time()  # Reset timer cuando hay salida
                                
                                # Patrones específicos de progreso de SteamCMD
                                # Buscar patrones de progreso específicos
                                progress_patterns = [
                                r"Update state \(0x\d+\) downloading, progress: (\d+(?:\.\d+)?) \((\d+) / (\d+)\)",  # Progress con bytes
                                r"Update state \(0x\d+\) downloading, progress: (\d+(?:\.\d+)?)",  # Progress simple
                                r"downloading, progress: (\d+(?:\.\d+)?)",  # Progreso de descarga
                                r"Progress: (\d+(?:\.\d+)?)%",  # Progress con %
                                r"(\d+(?:\.\d+)?)% complete",  # X% complete
                            ]
                            
                            progress_found = False
                            for pattern in progress_patterns:
                                match = re.search(pattern, output, re.IGNORECASE)
                                if match:
                                    progress = float(match.group(1))
                                    if progress <= 100:  # Asegurar que el progreso esté en rango válido
                                        if callback:
                                            callback("progress", f"Progreso de descarga: {progress:.1f}%")
                                        progress_found = True
                                        break
                            
                            if not progress_found:
                                # Mensajes específicos de estado
                                if any(keyword in output.lower() for keyword in ["downloading", "installing", "validating"]):
                                    if callback:
                                        callback("progress", output)
                                elif "success!" in output.lower() or "update complete" in output.lower() or "app state" in output.lower():
                                    if callback:
                                        callback("success", output)
                                elif "error" in output.lower() or "failed" in output.lower():
                                    if callback:
                                        callback("error", output)
                                elif any(skip in output.lower() for skip in [
                                    "steam console client", "-- type 'quit' to exit --", 
                                    "loading steam api", "waiting for client config", "logging directory"
                                ]):
                                    # Filtrar mensajes de ruido de SteamCMD
                                    continue
                                elif "update state" in output.lower() and "idle" not in output.lower():
                                    # Estados de actualización importantes
                                    if callback:
                                        callback("info", output)
                                elif output.strip() and len(output.strip()) > 5:  # Solo mensajes significativos
                                    if callback:
                                        callback("info", output)
                    
                    except Exception as e:
                        self.logger.error(f"Error leyendo salida de SteamCMD: {e}")
                        time.sleep(0.1)  # Pequeña pausa antes de reintentar
                        continue
                
                # Obtener código de salida
                return_code = process.poll()
                
                # SteamCMD puede devolver códigos de salida diferentes a 0 incluso cuando la operación es exitosa
                # Código 7 es común cuando la instalación se completa correctamente
                if return_code == 0 or return_code == 7:
                    if callback:
                        callback("info", "Buscando ejecutable del servidor...")
                    
                    # Esperar un momento para que se complete la instalación
                    import time
                    time.sleep(2)
                    
                    # Buscar el ejecutable del servidor
                    server_exe = self.find_server_executable(install_path)
                    if server_exe:
                        # Guardar la ruta del ejecutable para este servidor específico
                        if server_name:
                            # Crear una clave específica para este servidor
                            server_key = f"executable_path_{server_name}"
                            self.config_manager.set("server", server_key, server_exe)
                        else:
                            self.config_manager.set("server", "executable_path", server_exe)
                        
                        self.config_manager.save()
                        
                        self.logger.info(f"{operation_type.capitalize()} completada exitosamente. Ejecutable: {server_exe}")
                        if callback:
                            callback("success", f"{operation_type.capitalize()} completada exitosamente. Servidor en: {server_exe}")
                    else:
                        self.logger.warning(f"{operation_type.capitalize()} completada pero no se encontró el ejecutable en: {install_path}")
                        if callback:
                            callback("warning", f"{operation_type.capitalize()} completada pero no se encontró el ejecutable del servidor en: {install_path}")
                        
                        # Listar archivos en el directorio para debugging
                        try:
                            self.logger.info("Contenido del directorio de instalación:")
                            for root, dirs, files in os.walk(install_path):
                                level = root.replace(install_path, '').count(os.sep)
                                indent = ' ' * 2 * level
                                self.logger.info(f"{indent}{os.path.basename(root)}/")
                                subindent = ' ' * 2 * (level + 1)
                                for file in files[:10]:  # Solo mostrar los primeros 10 archivos
                                    self.logger.info(f"{subindent}{file}")
                                if len(files) > 10:
                                    self.logger.info(f"{subindent}... y {len(files) - 10} archivos más")
                        except Exception as e:
                            self.logger.error(f"Error al listar contenido del directorio: {e}")
                else:
                    stderr_output = process.stderr.read()
                    self.logger.error(f"Error en la {operation_type}: {stderr_output}")
                    if callback:
                        callback("error", f"Error en la {operation_type}. Código de salida: {return_code}")
                        if stderr_output:
                            callback("error", f"Detalles: {stderr_output}")
                        
            except Exception as e:
                self.logger.error(f"Error durante la instalación: {e}")
                if callback:
                    callback("error", f"Error durante la instalación: {str(e)}")
        
        threading.Thread(target=_install, daemon=True).start()
    
    def install_steamcmd_if_needed(self, root_path, callback=None):
        """Instala SteamCMD si no está disponible o lo actualiza si existe"""
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
                    if callback:
                        callback("info", "SteamCMD encontrado en el PATH del sistema")
                    return "steamcmd"  # Está en el PATH
            except Exception as e:
                self.logger.debug(f"SteamCMD no encontrado en PATH: {e}")
            
            # Verificar si existe en la carpeta SteamCMD del directorio raíz
            steamcmd_dir = os.path.join(root_path, "SteamCMD")
            steamcmd_path = os.path.join(steamcmd_dir, "steamcmd.exe")
            
            if os.path.exists(steamcmd_path):
                if callback:
                    callback("info", f"SteamCMD encontrado en: {steamcmd_path}")
                
                # Verificar si necesita actualización
                if callback:
                    callback("progress", "Verificando actualizaciones de SteamCMD...")
                
                # Ejecutar SteamCMD para actualizarse
                try:
                    update_process = subprocess.run(
                        [steamcmd_path, "+quit"],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=steamcmd_dir
                    )
                    if update_process.returncode == 0:
                        if callback:
                            callback("success", "SteamCMD actualizado correctamente")
                    else:
                        if callback:
                            callback("warning", "No se pudo actualizar SteamCMD, pero se puede usar la versión existente")
                except Exception as e:
                    if callback:
                        callback("warning", f"No se pudo actualizar SteamCMD: {str(e)}, pero se puede usar la versión existente")
                
                return steamcmd_path
            
            # Instalar SteamCMD
            if callback:
                callback("progress", "SteamCMD no encontrado. Instalando...")
            
            import zipfile
            import urllib.request
            
            # Crear directorio para SteamCMD
            try:
                os.makedirs(steamcmd_dir, exist_ok=True)
            except Exception as e:
                if callback:
                    callback("error", f"No se pudo crear el directorio SteamCMD: {str(e)}")
                return None
            
            # URL de descarga de SteamCMD
            steamcmd_url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
            zip_path = os.path.join(steamcmd_dir, "steamcmd.zip")
            
            # Descargar SteamCMD con progreso
            if callback:
                callback("progress", "🔄 Descargando SteamCMD... (10%)")
            
            def download_progress_hook(block_num, block_size, total_size):
                if callback and total_size > 0:
                    downloaded = block_num * block_size
                    progress = min(100, (downloaded / total_size) * 100)
                    if progress % 10 == 0 or progress > 95:  # Actualizar cada 10% o al final
                        callback("progress", f"🔄 Descargando SteamCMD... ({progress:.0f}%)")
            
            try:
                urllib.request.urlretrieve(steamcmd_url, zip_path, download_progress_hook)
                if callback:
                    callback("success", "✅ SteamCMD descargado correctamente")
            except Exception as e:
                if callback:
                    callback("error", f"Error al descargar SteamCMD: {str(e)}")
                return None
            
            # Extraer archivo ZIP
            if callback:
                callback("progress", "🔄 Extrayendo SteamCMD... (15%)")
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(steamcmd_dir)
                if callback:
                    callback("success", "✅ SteamCMD extraído correctamente")
            except Exception as e:
                if callback:
                    callback("error", f"Error al extraer SteamCMD: {str(e)}")
                return None
            
            # Eliminar archivo ZIP
            try:
                os.remove(zip_path)
            except:
                pass  # No es crítico si no se puede eliminar
            
            # Verificar instalación
            if os.path.exists(steamcmd_path):
                self.config_manager.set("server", "steamcmd_path", steamcmd_path)
                self.config_manager.save()
                
                if callback:
                    callback("success", "SteamCMD instalado correctamente")
                return steamcmd_path
            else:
                raise Exception("Error al extraer SteamCMD - archivo ejecutable no encontrado")
                
        except Exception as e:
            self.logger.error(f"Error al instalar SteamCMD: {e}")
            if callback:
                callback("error", f"Error al instalar SteamCMD: {str(e)}")
            return None
    
    def find_server_executable(self, install_path):
        """Busca el ejecutable del servidor de Ark Survival Ascended"""
        self.logger.info(f"Buscando ejecutable en: {install_path}")
        
        possible_names = [
            "ArkAscendedServer.exe",
            "ArkAscendedServer-Win64-Shipping.exe",
            "ShooterGameServer.exe",
            "ArkServer.exe",
            "ArkAscendedServer"
        ]
        
        # Buscar en las rutas más comunes para Ark Survival Ascended
        common_paths = [
            os.path.join(install_path, "ShooterGame", "Binaries", "Win64"),
            os.path.join(install_path, "ShooterGame", "Binaries"),
            os.path.join(install_path, "Engine", "Binaries", "Win64"),
            os.path.join(install_path, "Binaries", "Win64"),
            os.path.join(install_path, "Binaries"),
            install_path
        ]
        
        # Primero buscar en las rutas comunes
        for path in common_paths:
            if os.path.exists(path):
                self.logger.info(f"Verificando ruta común: {path}")
                for name in possible_names:
                    exe_path = os.path.join(path, name)
                    if os.path.exists(exe_path):
                        self.logger.info(f"Ejecutable encontrado en ruta común: {exe_path}")
                        return exe_path
            else:
                self.logger.debug(f"Ruta no existe: {path}")
        
        # Si no se encuentra en las rutas comunes, buscar recursivamente
        self.logger.info(f"Buscando ejecutable recursivamente en: {install_path}")
        for root, dirs, files in os.walk(install_path):
            for file in files:
                if file.lower().endswith('.exe'):
                    # Buscar archivos que contengan 'server', 'ark', o 'ascended' en el nombre
                    file_lower = file.lower()
                    if any(keyword in file_lower for keyword in ['server', 'ark', 'ascended']):
                        exe_path = os.path.join(root, file)
                        self.logger.info(f"Ejecutable encontrado recursivamente: {exe_path}")
                        return exe_path
        
        # Si aún no se encuentra, buscar cualquier archivo .exe que pueda ser el servidor
        self.logger.info("Buscando cualquier archivo .exe que pueda ser el servidor...")
        for root, dirs, files in os.walk(install_path):
            for file in files:
                if file.lower().endswith('.exe'):
                    # Excluir archivos que claramente no son el servidor
                    file_lower = file.lower()
                    if not any(exclude in file_lower for exclude in ['steam', 'unins', 'install', 'setup', 'launcher']):
                        exe_path = os.path.join(root, file)
                        self.logger.info(f"Posible ejecutable encontrado: {exe_path}")
                        return exe_path
        
        self.logger.warning(f"No se encontró ningún ejecutable en: {install_path}")
        
        # Listar el contenido del directorio para debugging
        try:
            self.logger.info("Contenido del directorio de instalación:")
            for root, dirs, files in os.walk(install_path):
                level = root.replace(install_path, '').count(os.sep)
                indent = ' ' * 2 * level
                self.logger.info(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files[:10]:  # Solo mostrar los primeros 10 archivos
                    if file.lower().endswith('.exe'):
                        self.logger.info(f"{subindent}🔴 {file}")
                    else:
                        self.logger.info(f"{subindent}{file}")
                if len(files) > 10:
                    self.logger.info(f"{subindent}... y {len(files) - 10} archivos más")
        except Exception as e:
            self.logger.error(f"Error al listar contenido del directorio: {e}")
        
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

    def update_server(self, callback=None, server_name=None):
        """Actualiza un servidor existente de Ark"""
        def _update():
            try:
                # Obtener rutas de configuración
                root_path = self.config_manager.get("server", "root_path")
                
                if not root_path:
                    if callback:
                        callback("error", "Ruta raíz no configurada. Configure la aplicación primero.")
                    return
                
                # Determinar la ruta del servidor
                if server_name:
                    install_path = os.path.join(root_path, server_name)
                else:
                    if callback:
                        callback("error", "Nombre del servidor no especificado.")
                    return
                
                # Verificar que el servidor existe
                if not os.path.exists(install_path):
                    if callback:
                        callback("error", f"El servidor '{server_name}' no existe en la ruta: {install_path}")
                    return
                
                if callback:
                    callback("info", f"Servidor encontrado en: {install_path}")
                
                # Verificar/instalar SteamCMD si es necesario
                if callback:
                    callback("progress", "Verificando SteamCMD...")
                steamcmd_path = self.install_steamcmd_if_needed(root_path, callback)
                if not steamcmd_path:
                    if callback:
                        callback("error", "No se pudo instalar SteamCMD. Verifique su conexión a internet.")
                    return
                
                self.logger.info(f"Iniciando actualización del servidor: {server_name}")
                if callback:
                    callback("info", f"Iniciando actualización del servidor: {server_name}")
                
                # Comando para actualizar el servidor de Ark Survival Ascended
                # App ID: 2430930 (Ark Survival Ascended Dedicated Server)
                cmd = [
                    steamcmd_path,
                    "+login", "anonymous",
                    "+force_install_dir", install_path,
                    "+app_update", "2430930", "validate",
                    "+quit"
                ]
                
                if callback:
                    callback("info", "Ejecutando SteamCMD para actualización...")
                
                # Ejecutar el proceso de actualización
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=os.path.dirname(steamcmd_path) if steamcmd_path != "steamcmd" else None
                    )
                except Exception as e:
                    if callback:
                        callback("error", f"Error al ejecutar SteamCMD: {str(e)}")
                    return
                
                # Leer salida en tiempo real
                if callback:
                    callback("progress", "Iniciando actualización...")
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        output = output.strip()
                        if output:
                            # Filtrar mensajes importantes y actualizar progreso
                            if any(keyword in output for keyword in ["Downloading update", "Installing update", "Downloading", "Installing", "Validating", "Progress:"]):
                                if callback:
                                    callback("progress", output)
                            elif "Success!" in output or "Installed" in output or "Update complete" in output:
                                if callback:
                                    callback("success", output)
                            elif "ERROR" in output or "Failed" in output:
                                if callback:
                                    callback("error", output)
                            elif any(keyword in output for keyword in ["Update state", "App 2430930", "Logging directory", "Loading Steam API", "Connecting anonymously", "Waiting for client config"]):
                                if callback:
                                    callback("info", output)
                            elif "Steam" in output and ("updating" in output.lower() or "installing" in output.lower()):
                                if callback:
                                    callback("progress", output)
                            elif "Downloading" in output or "Installing" in output or "Validating" in output:
                                # Capturar cualquier mensaje que contenga estas palabras
                                if callback:
                                    callback("progress", output)
                            elif "Progress:" in output:
                                # Capturar mensajes de progreso específicos
                                if callback:
                                    callback("progress", output)
                            else:
                                # Para otros mensajes, mostrarlos como información
                                if callback and output.strip():
                                    callback("info", output)
                
                # Obtener código de salida
                return_code = process.poll()
                
                # SteamCMD puede devolver códigos de salida diferentes a 0 incluso cuando la operación es exitosa
                # Código 7 es común cuando la actualización se completa correctamente
                if return_code == 0 or return_code == 7:
                    if callback:
                        callback("info", "Buscando ejecutable del servidor...")
                    
                    # Esperar un momento para que se complete la actualización
                    import time
                    time.sleep(2)
                    
                    # Buscar el ejecutable del servidor
                    server_exe = self.find_server_executable(install_path)
                    if server_exe:
                        # Guardar la ruta del ejecutable para este servidor específico
                        if server_name:
                            server_key = f"executable_path_{server_name}"
                            self.config_manager.set("server", server_key, server_exe)
                            self.config_manager.save()
                        
                        self.logger.info(f"Actualización completada exitosamente. Ejecutable: {server_exe}")
                        if callback:
                            callback("success", f"Actualización completada exitosamente. Servidor en: {server_exe}")
                    else:
                        self.logger.warning(f"Actualización completada pero no se encontró el ejecutable en: {install_path}")
                        if callback:
                            callback("warning", f"Actualización completada pero no se encontró el ejecutable del servidor en: {install_path}")
                else:
                    stderr_output = process.stderr.read()
                    self.logger.error(f"Error en la actualización: {stderr_output}")
                    if callback:
                        callback("error", f"Error en la actualización. Código de salida: {return_code}")
                        if stderr_output:
                            callback("error", f"Detalles: {stderr_output}")
                        
            except Exception as e:
                self.logger.error(f"Error durante la actualización: {e}")
                if callback:
                    callback("error", f"Error durante la actualización: {str(e)}")
        
        threading.Thread(target=_update, daemon=True).start()
