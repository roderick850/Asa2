import customtkinter as ctk
import threading
import time
import os
import psutil
import queue
from datetime import datetime


class ConsolePanel:
    def __init__(self, parent, config_manager, logger, main_window=None):
        self.parent = parent
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        
        # Variables de control
        self.console_active = False
        self.console_thread = None
        self.console_running = False
        self.max_lines = 1000  # Máximo número de líneas en la consola
        self._last_file_position = None  # Posición del archivo de log para seguimiento
        self._current_log_file = None  # Archivo de log actual para detectar cambios
        self._content_loaded = False  # Indica si ya se cargó el contenido existente
        
        # Variables para modo cluster
        self.is_cluster_mode = False
        self.cluster_servers = {}  # Diccionario de servidores del cluster
        self.current_server_id = None  # Servidor actualmente seleccionado
        self.server_consoles = {}  # Diccionario de widgets de consola por servidor
        self.server_threads = {}  # Diccionario de threads de monitoreo por servidor
        
        # Cola thread-safe para comunicación entre hilos
        self.message_queue = queue.Queue()
        self.queue_processor_running = False
        
        # Referencia al server_manager para acceder a la consola
        if main_window and hasattr(main_window, 'server_panel'):
            self.server_manager = main_window.server_panel.server_manager
        else:
            from utils.server_manager import ServerManager
            self.server_manager = ServerManager(config_manager)
        
        self.create_widgets()
        
    def create_widgets(self):
        """Crear los widgets del panel de consola"""
        if self.parent is None:
            return
            
        # Frame principal con padding mínimo
        self.main_frame = ctk.CTkFrame(self.parent)
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Frame de título y pestañas combinado - ultra compacto
        title_frame = ctk.CTkFrame(self.main_frame, fg_color=("gray90", "gray20"), height=35)
        title_frame.pack(fill="x", pady=(2, 2))
        title_frame.pack_propagate(False)  # Mantener altura fija
        
        # Título más compacto
        self.title_label = ctk.CTkLabel(
            title_frame, 
            text="🖥️ Consola del Servidor", 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.title_label.pack(side="left", padx=(6, 10), pady=4)
        
        # Frame para pestañas de servidores (en la misma línea que el título)
        self.server_tabs_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        self.server_tabs_frame.pack(side="left", padx=(10, 0), pady=2)
        
        # Diccionario para almacenar pestañas de servidores
        self.server_tabs = {}
        self.server_tab_buttons = {}
        self.active_server_tab = None
        
        # Eliminado: Frame de selección de servidor ya no es necesario con las pestañas
        
        # Frame de controles ultra-compacto - todo en una línea
        controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=30)
        controls_frame.pack(fill="x", padx=3, pady=(0, 2))
        controls_frame.pack_propagate(False)  # Mantener altura fija
        
        # Switch para mostrar/ocultar consola del servidor (modo único) - lado izquierdo
        self.console_visibility_var = ctk.BooleanVar(value=self.config_manager.get("app", "show_server_console", default="true").lower() == "true")
        self.show_console_switch = ctk.CTkSwitch(
            controls_frame,
            text="Consola",
            command=self.toggle_server_console_visibility,
            variable=self.console_visibility_var,
            width=70
        )
        self.show_console_switch.pack(side="left", padx=(3, 10))
        
        # Frame para switches individuales de visibilidad (modo cluster) - oculto inicialmente
        self.cluster_console_visibility_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        
        # Diccionario para almacenar switches individuales de cada servidor
        self.server_console_switches = {}
        self.server_console_vars = {}
        
        # Botones de control - lado derecho, más pequeños
        self.clear_button = ctk.CTkButton(
            controls_frame,
            text="🧹",
            command=self.clear_console,
            width=30,
            height=22
        )
        self.clear_button.pack(side="right", padx=1)
        
        self.save_button = ctk.CTkButton(
            controls_frame,
            text="💾",
            command=self.save_console,
            width=30,
            height=22
        )
        self.save_button.pack(side="right", padx=1)
        
        self.reload_content_button = ctk.CTkButton(
            controls_frame,
            text="📄",
            command=self.force_reload_content,
            width=30,
            height=22
        )
        self.reload_content_button.pack(side="right", padx=1)
        
        self.start_monitoring_button = ctk.CTkButton(
            controls_frame,
            text="🔄",
            command=self.start_console,
            width=30,
            height=22
        )
        self.start_monitoring_button.pack(side="right", padx=1)
        
        # Frame para comandos - ultra compacto
        command_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=28)
        command_frame.pack(fill="x", padx=3, pady=(0, 2))
        command_frame.pack_propagate(False)  # Mantener altura fija
        
        # Label y entrada de comando en la misma línea
        command_label = ctk.CTkLabel(
            command_frame,
            text="Comando:",
            font=ctk.CTkFont(size=10),
            width=55
        )
        command_label.pack(side="left", padx=(3, 3))
        
        # Entrada de comando
        self.command_entry = ctk.CTkEntry(
            command_frame,
            placeholder_text="Escribe un comando del servidor...",
            height=24
        )
        self.command_entry.pack(side="left", padx=3, fill="x", expand=True)
        
        # Enlazar la tecla Enter para enviar comandos
        self.command_entry.bind("<Return>", lambda event: self.send_command())
        
        # Botón para enviar comando
        self.send_button = ctk.CTkButton(
            command_frame,
            text="📤 Enviar",
            command=self.send_command,
            width=70,
            height=24
        )
        self.send_button.pack(side="right", padx=3)
        
        # Frame de consola (para modo servidor único) - padding mínimo
        self.console_frame = ctk.CTkFrame(self.main_frame)
        self.console_frame.pack(fill="both", expand=True, padx=2, pady=(0, 2))
        
        # Título de la consola - más compacto
        console_title = ctk.CTkLabel(
            self.console_frame, 
            text="Salida del Servidor:", 
            font=ctk.CTkFont(size=10, weight="bold")
        )
        console_title.pack(pady=(2, 1))
        
        # Área de texto para la consola (con scrollbar) - padding mínimo
        self.console_text = ctk.CTkTextbox(
            self.console_frame, 
            state="disabled",
            font=ctk.CTkFont(family="Consolas", size=9),
            height=250  # Altura mínima reducida
        )
        self.console_text.pack(fill="both", expand=True, padx=2, pady=(1, 2))
        
        # Frame de estado - ultra compacto
        status_frame = ctk.CTkFrame(self.main_frame, height=25)
        status_frame.pack(fill="x", padx=2, pady=(0, 2))
        status_frame.pack_propagate(False)  # Mantener altura fija
        
        # Estado de la consola - texto más pequeño
        self.status_label = ctk.CTkLabel(
            status_frame, 
            text="Estado: Iniciando automáticamente...", 
            text_color="blue",
            font=ctk.CTkFont(size=9)
        )
        self.status_label.pack(side="left", padx=4, pady=2)
        
        # Contador de líneas - texto más pequeño
        self.lines_label = ctk.CTkLabel(
            status_frame, 
            text="Líneas: 0",
            font=ctk.CTkFont(size=9)
        )
        self.lines_label.pack(side="right", padx=4, pady=2)
        
        # Mensaje inicial
        self.add_console_message("Consola del servidor inicializada. Iniciando monitoreo automático...")
        
        # Iniciar monitoreo automáticamente con retraso para asegurar que la app esté lista
        try:
            self.parent.after(3000, self.auto_start_monitoring)
        except Exception:
            pass
        

    
    def auto_start_monitoring(self):
        """Iniciar monitoreo automáticamente cuando la app se inicia"""
        self.add_console_message("🚀 Iniciando monitoreo automático del servidor...")
        
        # Notificar a MainWindow que ConsolePanel está manejando el inicio
        if hasattr(self.main_window, 'console_panel_managing_startup'):
            self.main_window.console_panel_managing_startup = True
        
        # Marcar estado inicial como inactivo
        if hasattr(self.main_window, 'update_server_status'):
            self.main_window.update_server_status("Inactivo")
        
        # Iniciar el monitoreo de consola
        self.start_console()
        
        # Auto-iniciar el servidor después de un pequeño retraso
        # SOLO si está configurado para auto-inicio Y no hay un servidor ejecutándose ya
        should_auto_start = False
        
        # Verificar configuración de auto-inicio
        if hasattr(self.main_window, 'app_settings'):
            # Verificar si se inició con Windows o manualmente
            if hasattr(self.main_window, 'started_with_windows') and self.main_window.started_with_windows:
                # Se inició con Windows - usar configuración específica
                should_auto_start = self.main_window.app_settings.get_setting("auto_start_server_with_windows")
            else:
                # Se inició manualmente - usar configuración normal
                should_auto_start = self.main_window.app_settings.get_setting("auto_start_server")
        
        if should_auto_start and not self.server_manager.is_server_running():
            try:
                self.parent.after(2000, self.auto_start_server)
            except Exception:
                pass
            self.add_console_message("🚀 Auto-inicio del servidor configurado, iniciando en 2 segundos...")
        else:
            if should_auto_start:
                self.add_console_message("✅ Servidor ya está ejecutándose, monitoreando...")
            else:
                self.add_console_message("⏸️ Auto-inicio del servidor desactivado por configuración")
            # Verificar si ya está activo
            if hasattr(self.main_window, 'update_server_status'):
                self.main_window.update_server_status("Verificando...")
    
    def auto_start_server(self):
        """Iniciar el servidor automáticamente"""
        self.add_console_message("🔄 Iniciando servidor automáticamente...")
        
        # Log adicional para diagnóstico
        if hasattr(self.main_window, 'logger'):
            self.main_window.logger.info("🚀 ConsolePanel: Auto-inicio del servidor iniciado")
        
        # Notificar al MainWindow que el servidor está iniciando
        if hasattr(self.main_window, 'update_server_status'):
            self.main_window.update_server_status("Iniciando")
        
        try:
            # Obtener argumentos del servidor desde el panel principal
            if hasattr(self.main_window, 'principal_panel'):
                server_args = self.main_window.principal_panel.build_server_arguments()
                
                self.server_manager.start_server_with_args(
                    callback=self.on_server_status_change,
                    server_name=self.main_window.selected_server,
                    map_name=self.main_window.selected_map,
                    custom_args=server_args
                )
            else:
                # Fallback si no hay panel principal
                self.server_manager.start_server_with_args(
                    callback=self.on_server_status_change,
                    server_name="Prueba",
                    map_name="The Center"
                )
            
            self.add_console_message("✅ Servidor iniciado automáticamente en modo de captura de consola")
            
        except Exception as e:
            self.add_console_message(f"❌ Error iniciando servidor automáticamente: {e}")
            self.logger.error(f"Error iniciando servidor automáticamente: {e}")
            
            # Notificar error al MainWindow
            if hasattr(self.main_window, 'update_server_status'):
                self.main_window.update_server_status("Error")

    def start_console(self):
        """Iniciar la captura de la consola del servidor"""
        if self.console_running:
            self.add_console_message("ℹ️ La consola ya está ejecutándose")
            return
            
        self.console_active = True
        self.console_running = True
        self.status_label.configure(text="Estado: Activada", text_color="green")
        
        # Verificar si el servidor está ejecutándose (usando detección mejorada)
        server_running = self._is_server_running_comprehensive()
        if server_running:
            
            # El servidor ya está ejecutándose, verificar si está en modo de captura
            self.add_console_message("✅ Servidor ya ejecutándose, verificando modo de captura...")
            
            # Solo reiniciar si no está en modo de captura Y si el auto-inicio está habilitado
            if not self._is_server_in_capture_mode():
                # VERIFICAR CONFIGURACIÓN DE AUTO-INICIO ANTES DE REINICIAR
                should_auto_start = False
                if hasattr(self.main_window, 'app_settings'):
                    if hasattr(self.main_window, 'started_with_windows') and self.main_window.started_with_windows:
                        should_auto_start = self.main_window.app_settings.get_setting("auto_start_server_with_windows")
                    else:
                        should_auto_start = self.main_window.app_settings.get_setting("auto_start_server")
                
                # En lugar de reiniciar, intentar reconectar al proceso existente
                self.add_console_message("🔄 Servidor detectado pero no en modo de captura, intentando reconectar...")
                try:
                    # Intentar reconectar al proceso existente sin reiniciarlo
                    if self._try_reconnect_to_existing_server():
                        self.add_console_message("✅ Reconectado al servidor existente para monitoreo")
                    else:
                        # Solo si falla la reconexión Y auto-inicio está habilitado, reiniciar
                        if should_auto_start:
                            self.add_console_message("⚠️ No se pudo reconectar, reiniciando servidor...")
                            # Detener el servidor actual
                            self.server_manager.stop_server()
                            time.sleep(2)
                            
                            # Reiniciar en modo de captura
                            self._start_server_in_capture_mode()
                            self.add_console_message("✅ Servidor reiniciado en modo de captura de consola")
                        else:
                            self.add_console_message("⏸️ No se pudo reconectar y auto-inicio desactivado - monitoreo limitado")
                except Exception as e:
                    self.add_console_message(f"❌ Error en reconexión: {e}")
            else:
                self.add_console_message("✅ Servidor ya está en modo de captura de consola")
        else:
            # El servidor no está ejecutándose - verificar si debe iniciarse
            should_auto_start = False
            if hasattr(self.main_window, 'app_settings'):
                if hasattr(self.main_window, 'started_with_windows') and self.main_window.started_with_windows:
                    should_auto_start = self.main_window.app_settings.get_setting("auto_start_server_with_windows")
                else:
                    should_auto_start = self.main_window.app_settings.get_setting("auto_start_server")
            
            if should_auto_start:
                self.add_console_message("🚀 No hay servidor ejecutándose, iniciando servidor en modo de captura...")
                try:
                    self._start_server_in_capture_mode()
                    self.add_console_message("🚀 Servidor iniciado en modo de captura de consola")
                except Exception as e:
                    self.add_console_message(f"❌ Error iniciando servidor: {e}")
                    self.logger.error(f"Error iniciando servidor: {e}")
            else:
                self.add_console_message("⏸️ No hay servidor ejecutándose y auto-inicio desactivado - monitoreo en espera")
        
        # Iniciar el thread de monitoreo
        self.console_thread = threading.Thread(target=self.console_monitor, daemon=True)
        self.console_thread.start()
        
        # Actualizar el switch de visibilidad de consola
        if self.main_window and hasattr(self.main_window, 'root'):
            try:
                self.main_window.root.after(1000, self.refresh_console_visibility_switch)
            except Exception:
                pass
    
    def _start_server_in_capture_mode(self):
        """Método auxiliar para iniciar el servidor en modo de captura"""
        # Notificar al MainWindow que el servidor está iniciando
        if hasattr(self.main_window, 'update_server_status'):
            self.main_window.update_server_status("Iniciando")
        
        # Obtener argumentos del servidor desde el panel principal
        if hasattr(self.main_window, 'principal_panel'):
            server_args = self.main_window.principal_panel.build_server_arguments()
            
            result = self.server_manager.start_server_with_args(
                callback=self.on_server_status_change,
                server_name=self.main_window.selected_server,
                map_name=self.main_window.selected_map,
                custom_args=server_args
            )
        else:
            # Fallback si no hay panel principal
            result = self.server_manager.start_server_with_args(
                callback=self.on_server_status_change,
                server_name="Prueba",
                map_name="The Center",
                custom_args=[]
            )
        
        self.add_console_message("🟢 Consola activada - Capturando salida del servidor...")
    
    def stop_console(self):
        """Detener la captura de la consola del servidor"""
        self.console_active = False
        self.console_running = False
        self.status_label.configure(text="Estado: Desactivada", text_color="red")
        
        # Notificar al MainWindow que el servidor está inactivo
        if hasattr(self.main_window, 'update_server_status'):
            self.main_window.update_server_status("Inactivo")
        
        self.logger.info("Consola del servidor desactivada")
        self.add_console_message("🔴 Consola desactivada")
    
    def console_monitor(self):
        """Monitorear la salida de la consola del servidor"""
        consecutive_empty_reads = 0
        max_empty_reads = 10  # Máximo de lecturas vacías consecutivas antes de pausar
        
        while self.console_active and self.console_running:
            try:
                # Verificar si el servidor está ejecutándose usando detección mejorada
                if self.server_manager.is_server_running():
                    # Intentar leer la salida del proceso desde el archivo de log del juego
                    game_log_path = self._get_latest_game_log()
                    if game_log_path and os.path.exists(game_log_path):
                        try:
                            # Leer el archivo de log del juego en tiempo real
                            with open(game_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                                # Si es la primera vez que leemos este archivo o si cambió el archivo, leer todo el contenido existente
                                # También forzar la lectura si no hemos cargado contenido aún
                                if (not hasattr(self, '_last_file_position') or 
                                    self._last_file_position is None or
                                    not hasattr(self, '_current_log_file') or
                                    self._current_log_file != game_log_path or
                                    not hasattr(self, '_content_loaded') or
                                    not self._content_loaded):
                                    
                                    # Leer todo el contenido existente primero
                                    f.seek(0, 0)  # Ir al inicio del archivo
                                    existing_content = f.read()
                                    if existing_content:
                                        # Dividir en líneas y agregar cada una
                                        lines = existing_content.split('\n')
                                        lines_added = 0
                                        for line in lines:
                                            line = line.strip()
                                            if line:
                                                timestamp = datetime.now().strftime("%H:%M:%S")
                                                formatted_line = f"[{timestamp}] {line}"
                                                self.add_console_message(formatted_line)
                                                lines_added += 1
                                    
                                    # Ahora posicionarse al final para futuras lecturas
                                    f.seek(0, 2)
                                    self._last_file_position = f.tell()
                                    self._current_log_file = game_log_path
                                    self._content_loaded = True
                                else:
                                    # Ir a la posición donde nos quedamos
                                    f.seek(self._last_file_position)
                                    
                                    # Leer nuevas líneas
                                    lines_read = 0
                                    while True:
                                        line = f.readline()
                                        if line:
                                            consecutive_empty_reads = 0  # Resetear contador
                                            lines_read += 1
                                            
                                            line = line.strip()
                                            if line:
                                                # Agregar timestamp
                                                timestamp = datetime.now().strftime("%H:%M:%S")
                                                formatted_line = f"[{timestamp}] {line}"
                                                self.add_console_message(formatted_line)
                                                
                                                # Detectar cuando el servidor ha completado el inicio
                                                if "Server has completed startup and is now advertising for join" in line:
                                                    self._notify_server_active()
                                        
                                        # Actualizar la posición del archivo
                                        current_position = f.tell()
                                        if current_position > self._last_file_position:
                                            self._last_file_position = current_position
                                        
                                        # Solo leer hasta 10 líneas por iteración para no bloquear
                                        if lines_read >= 10 or not line:
                                            break
                                    
                                    if lines_read == 0:
                                        consecutive_empty_reads += 1
                                        
                                        # Si no hay nuevas líneas y es la primera vez, forzar la lectura del contenido existente
                                        if consecutive_empty_reads == 1 and not hasattr(self, '_content_loaded'):
                                            self._content_loaded = False  # Forzar recarga
                                        
                                        if consecutive_empty_reads >= max_empty_reads:
                                            # Pausar un poco más si no hay datos
                                            time.sleep(0.5)
                                            consecutive_empty_reads = 0
                                    else:
                                        consecutive_empty_reads = 0
                                        
                        except Exception as e:
                            self.logger.error(f"Error leyendo archivo de log del juego: {e}")
                            time.sleep(0.5)
                        else:
                            time.sleep(1.0)
                    else:
                        # El proceso terminó
                        exit_code = self.server_manager.server_process.poll()
                        self.add_console_message(f"🔴 Proceso del servidor terminado (código: {exit_code})")
                        break
                elif hasattr(self.server_manager, 'server_pid') and self.server_manager.server_pid:
                    # Servidor reconectado - verificar si sigue ejecutándose por PID
                    if psutil.pid_exists(self.server_manager.server_pid):
                        # Intentar leer desde archivo de log (mismo código que arriba)
                        game_log_path = self._get_latest_game_log()
                        if game_log_path and os.path.exists(game_log_path):
                            try:
                                # Leer el archivo de log del juego en tiempo real
                                with open(game_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    # Usar la misma lógica de lectura que el servidor directo
                                    if (not hasattr(self, '_last_file_position') or 
                                        self._last_file_position is None or
                                        not hasattr(self, '_current_log_file') or
                                        self._current_log_file != game_log_path or
                                        not hasattr(self, '_content_loaded') or
                                        not self._content_loaded):
                                        
                                        # Leer todo el contenido existente primero (solo las últimas 50 líneas)
                                        f.seek(0, 0)
                                        all_lines = f.readlines()
                                        if len(all_lines) > 50:
                                            lines_to_show = all_lines[-50:]
                                        else:
                                            lines_to_show = all_lines
                                        
                                        for line in lines_to_show:
                                            line = line.strip()
                                            if line:
                                                timestamp = datetime.now().strftime("%H:%M:%S")
                                                formatted_line = f"[{timestamp}] {line}"
                                                self.add_console_message(formatted_line)
                                        
                                        # Ahora posicionarse al final para futuras lecturas
                                        f.seek(0, 2)
                                        self._last_file_position = f.tell()
                                        self._current_log_file = game_log_path
                                        self._content_loaded = True
                                    else:
                                        # Ir a la posición donde nos quedamos
                                        f.seek(self._last_file_position)
                                    
                                    # Leer nuevas líneas
                                    lines_read = 0
                                    while True:
                                        line = f.readline()
                                        if line:
                                            consecutive_empty_reads = 0
                                            lines_read += 1
                                            
                                            line = line.strip()
                                            if line:
                                                timestamp = datetime.now().strftime("%H:%M:%S")
                                                formatted_line = f"[{timestamp}] {line}"
                                                self.add_console_message(formatted_line)
                                                
                                                if "Server has completed startup and is now advertising for join" in line:
                                                    self._notify_server_active()
                                        
                                        current_position = f.tell()
                                        if current_position > self._last_file_position:
                                            self._last_file_position = current_position
                                        
                                        if lines_read >= 10 or not line:
                                            break
                                    
                                    consecutive_empty_reads = 0
                            except Exception as e:
                                self.logger.error(f"Error leyendo archivo de log (servidor reconectado): {e}")
                                time.sleep(0.5)
                        else:
                            time.sleep(1.0)
                    else:
                        # El proceso reconectado terminó
                        self.add_console_message(f"🔴 Proceso del servidor reconectado terminado (PID: {self.server_manager.server_pid})")
                        self.server_manager.server_pid = None
                        self.server_manager.server_running = False
                        break
                else:
                    # No hay proceso del servidor
                    if self.console_active:
                        time.sleep(1.0)  # Esperar más tiempo si no hay servidor
                        continue
                
                # Pausa adaptativa basada en si hay datos o no
                if consecutive_empty_reads > 0:
                    time.sleep(0.2)  # Pausa más larga si no hay datos
                else:
                    time.sleep(0.05)  # Pausa corta si hay datos
                
            except Exception as e:
                self.logger.error(f"Error en el monitor de consola: {e}")
                time.sleep(1.0)
        
        self.console_running = False
    
    def add_console_message(self, message):
        """Agregar mensaje a la consola"""
        if not self.parent:
            return
        
        try:
            # Si estamos en modo cluster con pestañas, agregar a la pestaña activa
            if self.is_cluster_mode and self.active_server_tab and self.active_server_tab in self.server_tabs:
                self.add_console_message_to_tab(self.active_server_tab, message)
                return
            
            # Modo servidor único o fallback
            # Habilitar el texto para edición
            self.console_text.configure(state="normal")
            
            # Agregar el mensaje con timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            full_message = f"[{timestamp}] {message}\n"
            
            # Insertar al final
            self.console_text.insert("end", full_message)
            
            # Limitar el número de líneas
            lines = self.console_text.get("1.0", "end").split('\n')
            if len(lines) > self.max_lines:
                # Eliminar líneas antiguas
                excess_lines = len(lines) - self.max_lines
                self.console_text.delete("1.0", f"{excess_lines + 1}.0")
            
            # Desplazar al final
            self.console_text.see("end")
            
            # Deshabilitar el texto
            self.console_text.configure(state="disabled")
            
            # Actualizar contador de líneas
            current_lines = len(self.console_text.get("1.0", "end").split('\n')) - 1
            self.lines_label.configure(text=f"Líneas: {current_lines}")
            
        except Exception as e:
            self.logger.error(f"Error agregando mensaje a la consola: {e}")
    
    def clear_console(self):
        """Limpiar la consola"""
        try:
            self.console_text.configure(state="normal")
            self.console_text.delete("1.0", "end")
            self.console_text.configure(state="disabled")
            
            self.lines_label.configure(text="Líneas: 0")
            self.add_console_message("🧹 Consola limpiada")
            
        except Exception as e:
            self.logger.error(f"Error limpiando consola: {e}")
    
    def save_console(self):
        """Guardar la consola en un archivo"""
        try:
            from tkinter import filedialog
            import os
            
            # Obtener contenido de la consola
            console_content = self.console_text.get("1.0", "end")
            
            if not console_content.strip():
                self.add_console_message("⚠️ No hay contenido para guardar")
                return
            
            # Solicitar ubicación del archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"consola_servidor_{timestamp}.txt"
            
            file_path = filedialog.asksaveasfilename(
                title="Guardar Consola del Servidor",
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
                initialname=default_filename
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(console_content)
                
                self.add_console_message(f"💾 Consola guardada en: {os.path.basename(file_path)}")
                self.logger.info(f"Consola del servidor guardada en: {file_path}")
                
        except Exception as e:
            self.logger.error(f"Error guardando consola: {e}")
            self.add_console_message(f"❌ Error guardando consola: {e}")
    
    def send_command(self):
        """Enviar comando al servidor"""
        command = self.command_entry.get().strip()
        if not command:
            return
            
        try:
            # Verificar si el servidor está ejecutándose usando detección mejorada
            if (self.server_manager.is_server_running() and 
                hasattr(self.server_manager, 'server_process') and 
                self.server_manager.server_process):
                
                # Enviar comando al servidor
                if self.server_manager.server_process.stdin:
                    # Agregar el comando a la consola
                    self.add_console_message(f"📤 Comando enviado: {command}")
                    
                    # Enviar al servidor
                    try:
                        self.server_manager.server_process.stdin.write(command + '\n')
                        self.server_manager.server_process.stdin.flush()
                    except Exception as e:
                        self.add_console_message(f"❌ Error enviando comando: {e}")
                        self.logger.error(f"Error enviando comando al servidor: {e}")
                else:
                    self.add_console_message("❌ No se puede enviar comando: stdin no disponible")
            else:
                self.add_console_message("❌ No se puede enviar comando: servidor no está ejecutándose")
                
        except Exception as e:
            self.add_console_message(f"❌ Error enviando comando: {e}")
            self.logger.error(f"Error enviando comando: {e}")
        finally:
            # Limpiar el campo de entrada
            self.command_entry.delete(0, "end")
    
    def update_server_status(self, status):
        """Actualizar estado del servidor en la consola"""
        if status == "Ejecutándose":
            self.add_console_message("🟢 Servidor iniciado")
        elif status == "Detenido":
            self.add_console_message("🔴 Servidor detenido")
    
    def _notify_server_active(self):
        """Notificar que el servidor está activo"""
        try:
            # Marcar el servidor como completamente iniciado en ServerManager
            if hasattr(self.server_manager, 'server_fully_started'):
                self.server_manager.server_fully_started = True
                self.logger.info("Servidor marcado como completamente iniciado")
            
            # Notificar al MainWindow que el servidor está ejecutándose
            if hasattr(self.main_window, 'update_server_status'):
                self.main_window.update_server_status("Ejecutándose")
            
            # Actualizar el estado local
            self.add_console_message("🟢 Servidor ejecutándose y listo para conexiones")
            
        except Exception as e:
            self.logger.error(f"Error notificando estado activo del servidor: {e}")
    
    def force_reload_content(self):
        """Forzar la recarga del contenido del archivo de log"""
        try:
            # Resetear las variables para forzar la lectura del contenido existente
            self._content_loaded = False
            self._last_file_position = None
            self._current_log_file = None
            
            self.add_console_message("🔄 Recargando contenido del archivo de log...")
            
        except Exception as e:
            self.logger.error(f"Error forzando recarga del contenido: {e}")
            self.add_console_message(f"❌ Error forzando recarga: {e}")
    
    def cleanup(self):
        """Limpiar recursos del panel"""
        self.stop_console()
        if self.console_thread and self.console_thread.is_alive():
            self.console_thread.join(timeout=1.0)
        
        # Detener todos los hilos de monitoreo de servidores
        for server_name in list(self.server_tabs.keys()):
            if server_name in self.server_tabs:
                self.server_tabs[server_name]['monitoring'] = False
        
        # Esperar a que terminen los hilos de monitoreo
        for server_name, thread in list(self.server_threads.items()):
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        self.server_threads.clear()
        
        # Detener el procesador de cola
        self.queue_processor_running = False

    def _get_latest_game_log(self, server_name=None):
        """Obtener la ruta del archivo de log del juego más reciente para un servidor específico"""
        try:
            # Usar servidor específico o el seleccionado globalmente
            target_server = server_name or (self.main_window.selected_server if hasattr(self.main_window, 'selected_server') else None)
            
            if target_server:
                # Construir la ruta al directorio de logs del juego
                root_path = self.config_manager.get("server", "root_path")
                if root_path:
                    logs_dir = os.path.join(root_path, target_server, "ShooterGame", "Saved", "Logs")
                    if os.path.exists(logs_dir):
                        # Buscar archivos ShooterGame*.log
                        log_files = []
                        for file in os.listdir(logs_dir):
                            if file.startswith("ShooterGame") and file.endswith(".log") and not file.endswith("backup"):
                                file_path = os.path.join(logs_dir, file)
                                log_files.append((file_path, os.path.getmtime(file_path)))
                        
                        if log_files:
                            # Ordenar por fecha de modificación (más reciente primero)
                            log_files.sort(key=lambda x: x[1], reverse=True)
                            latest_log = log_files[0][0]
                            
                            # Si el archivo de log cambió, resetear la posición para este servidor
                            server_key = f"_current_log_file_{target_server}"
                            if not hasattr(self, server_key) or getattr(self, server_key) != latest_log:
                                setattr(self, server_key, latest_log)
                                setattr(self, f"_last_file_position_{target_server}", None)
                            
                            return latest_log
        except Exception as e:
            self.logger.error(f"Error obteniendo archivo de log del juego para {target_server}: {e}")
        
        return None

    def on_server_status_change(self, status, message):
        """Callback para cambios de estado del servidor"""
        if status == "started":
            self.add_console_message("🟢 Servidor iniciado correctamente")
            # El estado "Activo" se marcará cuando se detecte el mensaje de inicio completo
        elif status == "success":
            self.add_console_message("🟢 Servidor iniciado exitosamente")
            # Actualizar estado a "Iniciando" hasta que se complete totalmente
            if hasattr(self.main_window, 'update_server_status'):
                self.main_window.update_server_status("Iniciando")
        elif status == "stopped":
            self.add_console_message("🔴 Servidor detenido")
            # Notificar al MainWindow que el servidor está inactivo
            if hasattr(self.main_window, 'update_server_status'):
                self.main_window.update_server_status("Inactivo")
        elif status == "error":
            self.add_console_message(f"❌ Error del servidor: {message}")
            # Notificar al MainWindow que hay un error
            if hasattr(self.main_window, 'update_server_status'):
                self.main_window.update_server_status("Error")
        elif status == "active":
            self._notify_server_active()
    
    def toggle_server_console_visibility(self):
        """Cambiar la visibilidad de la consola del servidor en tiempo real"""
        try:
            # Obtener el estado actual del switch
            show_console = self.show_console_switch.get()
            action = "mostrar" if show_console else "ocultar"
            
            self.logger.info(f"Usuario solicitó {action} la consola del servidor")
            
            # Guardar la configuración
            self.config_manager.set("app", "show_server_console", str(show_console).lower())
            self.config_manager.save()
            self.logger.debug(f"Configuración guardada: show_server_console = {show_console}")
            
            # Verificar si hay servidor ejecutándose usando detección mejorada
            if not self.server_manager:
                if self.main_window:
                    self.main_window.add_log_message("⚠️ ServerManager no disponible")
                self.logger.warning("ServerManager no disponible")
                return
            
            # Usar el método mejorado de detección de servidor
            server_running = self.server_manager.is_server_running()
            if not server_running:
                if self.main_window:
                    self.main_window.add_log_message("ℹ️ No hay servidor ejecutándose. El cambio se aplicará al iniciar el servidor")
                self.logger.info("No hay servidor ejecutándose (detección mejorada)")
                return
            
            # El servidor está ejecutándose, aplicar el cambio
            self.logger.info(f"Aplicando cambio de visibilidad: {action} consola")
            
            if show_console:
                # Mostrar consola
                if self.main_window:
                    self.main_window.add_log_message("🔄 Mostrando consola del servidor...")
                
                success = self.server_manager.show_server_console()
                
                if success:
                    if self.main_window:
                        self.main_window.add_log_message("✅ Consola del servidor: VISIBLE")
                    self.add_console_message("👁️ Consola del servidor mostrada")
                else:
                    if self.main_window:
                        self.main_window.add_log_message("⚠️ No se pudo mostrar la consola del servidor")
                    self.add_console_message("❌ Error al mostrar la consola del servidor")
                    # Revertir el switch si falló
                    self.console_visibility_var.set(False)
            else:
                # Ocultar consola
                if self.main_window:
                    self.main_window.add_log_message("🔄 Ocultando consola del servidor...")
                
                success = self.server_manager.hide_server_console()
                
                if success:
                    if self.main_window:
                        self.main_window.add_log_message("✅ Consola del servidor: OCULTA")
                    self.add_console_message("🙈 Consola del servidor ocultada")
                else:
                    if self.main_window:
                        self.main_window.add_log_message("⚠️ No se pudo ocultar la consola del servidor")
                    self.add_console_message("❌ Error al ocultar la consola del servidor")
                    # Revertir el switch si falló
                    self.console_visibility_var.set(True)
            
            self.logger.info(f"Configuración de consola del servidor cambiada a: {'visible' if show_console else 'oculta'}")
            
        except Exception as e:
            self.logger.error(f"Error al cambiar configuración de consola del servidor: {e}")
            import traceback
            self.logger.error(f"Traceback completo: {traceback.format_exc()}")
            
            if self.main_window:
                self.main_window.add_log_message(f"❌ Error al cambiar configuración: {str(e)}")
            self.add_console_message(f"❌ Error en switch de consola: {str(e)}")
            
            # Revertir el switch en caso de error
            try:
                current_config = self.config_manager.get("app", "show_server_console", default="true").lower() == "true"
                self.console_visibility_var.set(current_config)
            except:
                pass
    
    def refresh_console_visibility_switch(self):
        """Actualizar el estado del switch de visibilidad de consola"""
        try:
            if not self.server_manager:
                return
                
            # Verificación thread-safe del estado del servidor
            server_running = False
            try:
                server_running = self.server_manager.is_server_running()
            except Exception as server_check_error:
                self.logger.debug(f"Error verificando estado del servidor: {server_check_error}")
                # Fallback: verificar usando el proceso guardado
                if hasattr(self.server_manager, 'server_process') and self.server_manager.server_process:
                    try:
                        server_running = self.server_manager.server_process.poll() is None
                    except:
                        server_running = False
            
            if server_running:
                # Verificar si la consola está visible
                if self.server_manager.server_console_hwnd:
                    # La consola existe, verificar si está visible
                    import ctypes
                    try:
                        is_visible = ctypes.windll.user32.IsWindowVisible(self.server_manager.server_console_hwnd)
                        self.console_visibility_var.set(is_visible)
                    except Exception as visibility_error:
                        self.logger.debug(f"Error verificando visibilidad de consola: {visibility_error}")
                else:
                    # Buscar la ventana de consola
                    try:
                        self.server_manager._find_server_console_window()
                        if self.server_manager.server_console_hwnd:
                            import ctypes
                            is_visible = ctypes.windll.user32.IsWindowVisible(self.server_manager.server_console_hwnd)
                            self.console_visibility_var.set(is_visible)
                    except Exception as find_error:
                        self.logger.debug(f"Error buscando ventana de consola: {find_error}")
        except Exception as e:
            self.logger.debug(f"Error al actualizar switch de visibilidad: {e}")
    
    def _is_server_running_comprehensive(self):
        """Verificación comprehensiva si el servidor está ejecutándose"""
        try:
            # Usar el método mejorado de detección de servidor
            server_running = self.server_manager.is_server_running()
            if server_running:
                self.add_console_message("🔍 Servidor detectado usando detección mejorada")
                return True
            else:
                 self.add_console_message("❌ No se detectó servidor ejecutándose")
                 return False
                
            # Método 3: Buscar procesos por nombre (como hace server_manager.get_server_status)
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'ArkAscendedServer.exe' in proc.info['name']:
                        # Encontrado proceso ARK, actualizar PID en server_manager
                        self.server_manager.server_pid = proc.info['pid']
                        self.server_manager.server_running = True
                        self.add_console_message(f"🔍 Servidor detectado por búsqueda de nombre - PID: {proc.info['pid']}")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            # No se encontró servidor ejecutándose
            return False
            
        except Exception as e:
            self.logger.error(f"Error en detección comprehensiva del servidor: {e}")
            return False
    
    def _is_server_in_capture_mode(self):
        """Verificar si el servidor está en modo de captura de consola"""
        try:
            if (self.server_manager.is_server_running() and 
                hasattr(self.server_manager, 'server_process') and 
                self.server_manager.server_process):
                # Verificar si tiene stdout disponible
                if hasattr(self.server_manager.server_process, 'stdout') and self.server_manager.server_process.stdout:
                    self.add_console_message("🔍 Servidor detectado en modo de captura")
                    return True
                else:
                    self.add_console_message("🔍 Servidor detectado pero NO en modo de captura")
                    return False
            else:
                # Si no hay referencia de proceso, asumir que NO está en modo de captura
                self.add_console_message("🔍 No hay referencia de proceso - servidor NO en modo de captura")
                return False
        except Exception as e:
            self.logger.error(f"Error verificando modo de captura: {e}")
            return False
    
    def _try_reconnect_to_existing_server(self):
        """Intentar reconectar al servidor existente sin reiniciarlo"""
        try:
            # Buscar proceso del servidor por nombre
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'ArkAscendedServer.exe' in proc.info['name']:
                        # Encontrado proceso del servidor
                        self.add_console_message(f"🔍 Encontrado proceso del servidor - PID: {proc.info['pid']}")
                        
                        # Actualizar referencia en server_manager
                        self.server_manager.server_pid = proc.info['pid']
                        self.server_manager.server_running = True
                        
                        # Intentar obtener el objeto proceso
                        try:
                            server_process = psutil.Process(proc.info['pid'])
                            
                            # NO podemos conectarnos directamente al stdout de un proceso existente
                            # Pero podemos monitorearlo de otras formas
                            self.add_console_message("📡 Configurando monitoreo del servidor existente...")
                            
                            # Limpiar referencias previas para permitir monitoreo basado en archivos
                            self.server_manager.server_process = None  # No tenemos acceso directo al proceso
                            
                            return True
                        except psutil.NoSuchProcess:
                            self.add_console_message("⚠️ El proceso del servidor ya no existe")
                            continue
                        except Exception as e:
                            self.add_console_message(f"❌ Error al acceder al proceso: {e}")
                            continue
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            return False
        except Exception as e:
            self.add_console_message(f"❌ Error al buscar servidor existente: {e}")
            return False
    
    def on_cluster_mode_changed(self, is_cluster_mode):
        """Manejar el cambio de modo cluster"""
        try:
            self.logger.info(f"🔄 Console panel: on_cluster_mode_changed llamado con is_cluster_mode={is_cluster_mode}")
            self.is_cluster_mode = is_cluster_mode
            
            if is_cluster_mode:
                # Crear pestañas dinámicas para servidores
                self.create_server_tabs()
                self.title_label.configure(text="🌐 Consola del Cluster")
                
                # Ocultar switch único y mostrar switches individuales
                self.show_console_switch.pack_forget()
                self.cluster_console_visibility_frame.pack(fill="x", padx=5, pady=2)
                
                # Eliminado: update_server_list ya no es necesario sin el desplegable
                
                # Crear switches individuales para cada servidor
                self.create_individual_console_switches()
                
                self.logger.info("🌐 Console panel cambiado a modo cluster con pestañas dinámicas")
                
            else:
                # Limpiar pestañas de servidor y mostrar consola única
                self.clear_server_tabs()
                self.title_label.configure(text="🖥️ Consola del Servidor")
                
                # Mostrar consola única
                if hasattr(self, 'console_frame'):
                    self.console_frame.pack(fill="both", expand=True, padx=5, pady=5)
                
                # Mostrar switch único y ocultar switches individuales
                self.cluster_console_visibility_frame.pack_forget()
                self.show_console_switch.pack(side="left", padx=(5, 15))
                
                # Limpiar datos del cluster
                self.cluster_servers.clear()
                self.current_server_id = None
                self.clear_individual_console_switches()
                
                self.logger.info("📱 Console panel cambiado a modo servidor único")
                
        except Exception as e:
            self.logger.error(f"Error al cambiar modo cluster en console panel: {e}")
    
    # Eliminado: update_server_list ya no es necesario sin el desplegable
    
    # Eliminado: on_server_selected ya no es necesario sin el desplegable
    
    def get_current_server_log_path(self):
        """Obtener la ruta del log del servidor actual"""
        try:
            if self.is_cluster_mode and self.current_server_id:
                # En modo cluster, cada servidor tiene su propio directorio de logs
                if self.main_window and hasattr(self.main_window, 'cluster_panel'):
                    cluster_panel = self.main_window.cluster_panel
                    if hasattr(cluster_panel, 'servers') and self.current_server_id in cluster_panel.servers:
                        server_info = cluster_panel.servers[self.current_server_id]
                        # Construir ruta del log específica del servidor
                        server_dir = f"server_{self.current_server_id}"
                        log_path = os.path.join("logs", server_dir, "server.log")
                        return log_path
            
            # Modo servidor único o fallback
            return self.server_manager.get_log_file_path()
            
        except Exception as e:
            self.logger.error(f"Error al obtener ruta del log: {e}")
            return self.server_manager.get_log_file_path()
    
    def add_cluster_server(self, server_id, server_info):
        """Agregar un servidor al cluster"""
        try:
            self.cluster_servers[server_id] = server_info
            # Eliminado: update_server_list ya no es necesario sin el desplegable
            self.logger.info(f"Servidor agregado al cluster: {server_id}")
            
        except Exception as e:
            self.logger.error(f"Error al agregar servidor al cluster: {e}")
    
    def remove_cluster_server(self, server_id):
        """Remover un servidor del cluster"""
        try:
            if server_id in self.cluster_servers:
                del self.cluster_servers[server_id]
                
                # Si era el servidor actual, cambiar a ninguno
                if self.current_server_id == server_id:
                    self.current_server_id = None
                self.logger.info(f"Servidor removido del cluster: {server_id}")
                
        except Exception as e:
            self.logger.error(f"Error al remover servidor del cluster: {e}")
    
    def create_individual_console_switches(self):
        """Crear switches individuales para cada servidor del cluster"""
        try:
            # Limpiar switches existentes
            self.clear_individual_console_switches()
            
            if not self.main_window or not hasattr(self.main_window, 'cluster_panel'):
                return
            
            cluster_panel = self.main_window.cluster_panel
            if not hasattr(cluster_panel, 'servers') or not cluster_panel.servers:
                return
            
            # Crear título para la sección
            title_label = ctk.CTkLabel(
                self.cluster_console_visibility_frame,
                text="Visibilidad de Consola por Servidor:",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            title_label.pack(anchor="w", padx=(0, 10), pady=(0, 5))
            
            # Frame contenedor para los switches
            switches_container = ctk.CTkFrame(self.cluster_console_visibility_frame, fg_color="transparent")
            switches_container.pack(fill="x", padx=10)
            
            # Crear un switch para cada servidor
            for server_id, server_info in cluster_panel.servers.items():
                server_name = server_info.get('name', server_id)
                server_map = server_info.get('map', 'Unknown')
                
                # Frame para cada switch individual
                switch_frame = ctk.CTkFrame(switches_container, fg_color="transparent")
                switch_frame.pack(fill="x", pady=2)
                
                # Variable para el switch
                var_key = f"show_console_{server_id}"
                default_value = self.config_manager.get("cluster_console", var_key, default="true").lower() == "true"
                console_var = ctk.BooleanVar(value=default_value)
                self.server_console_vars[server_id] = console_var
                
                # Switch individual
                switch = ctk.CTkSwitch(
                    switch_frame,
                    text=f"{server_name} ({server_map})",
                    variable=console_var,
                    command=lambda sid=server_id: self.toggle_individual_server_console(sid)
                )
                switch.pack(side="left", padx=(0, 20))
                
                self.server_console_switches[server_id] = switch
            
            # Etiqueta explicativa
            ctk.CTkLabel(
                self.cluster_console_visibility_frame,
                text="Controla la visibilidad de la consola para cada servidor del cluster individualmente",
                font=("Arial", 10),
                text_color=("gray50", "gray70")
            ).pack(anchor="w", padx=(0, 10), pady=(5, 0))
            
            self.logger.info(f"Creados {len(self.server_console_switches)} switches individuales de consola")
            
        except Exception as e:
            self.logger.error(f"Error al crear switches individuales de consola: {e}")
    
    def clear_individual_console_switches(self):
        """Limpiar todos los switches individuales"""
        try:
            # Limpiar widgets del frame
            for widget in self.cluster_console_visibility_frame.winfo_children():
                widget.destroy()
            
            # Limpiar diccionarios
            self.server_console_switches.clear()
            self.server_console_vars.clear()
            
        except Exception as e:
            self.logger.error(f"Error al limpiar switches individuales: {e}")
    
    def toggle_individual_server_console(self, server_id):
        """Alternar la visibilidad de consola para un servidor específico"""
        try:
            if server_id not in self.server_console_vars:
                return
            
            is_visible = self.server_console_vars[server_id].get()
            
            # Guardar configuración
            var_key = f"show_console_{server_id}"
            self.config_manager.set("cluster_console", var_key, str(is_visible).lower())
            
            # Aplicar cambio si es el servidor actualmente seleccionado
            if self.current_server_id == server_id:
                if hasattr(self, 'server_manager') and self.server_manager:
                    if is_visible:
                        self.server_manager.show_console_window()
                        self.add_console_message(f"✅ Consola de {server_id} ahora visible")
                    else:
                        self.server_manager.hide_console_window()
                        self.add_console_message(f"🔇 Consola de {server_id} ahora oculta")
            
            server_name = server_id
            if self.main_window and hasattr(self.main_window, 'cluster_panel'):
                cluster_panel = self.main_window.cluster_panel
                if hasattr(cluster_panel, 'servers') and server_id in cluster_panel.servers:
                    server_name = cluster_panel.servers[server_id].get('name', server_id)
            
            status = "visible" if is_visible else "oculta"
            self.logger.info(f"Consola de servidor {server_name} configurada como {status}")
            
        except Exception as e:
            self.logger.error(f"Error al alternar consola individual del servidor {server_id}: {e}")
            self.add_console_message("❌ No se encontró proceso del servidor para reconectar")
            return False
    
    def create_server_tabs(self):
        """Crear pestañas dinámicas para cada servidor del cluster"""
        try:
            self.logger.info("🔄 Iniciando creación de pestañas de servidores...")
            # Limpiar pestañas existentes
            self.clear_server_tabs()
            
            if not self.main_window or not hasattr(self.main_window, 'cluster_panel'):
                self.logger.warning("❌ No se encontró main_window o cluster_panel")
                return
            
            cluster_panel = self.main_window.cluster_panel
            if not hasattr(cluster_panel, 'cluster_manager') or not cluster_panel.cluster_manager:
                self.logger.warning("❌ No se encontró cluster_manager")
                return
            
            if not hasattr(cluster_panel.cluster_manager, 'servers') or not cluster_panel.cluster_manager.servers:
                self.logger.warning("❌ No se encontraron servidores en cluster_manager")
                return
            
            self.logger.info(f"✅ Encontrados {len(cluster_panel.cluster_manager.servers)} servidores para crear pestañas")
            
            # Ocultar consola única
            if hasattr(self, 'console_frame'):
                self.console_frame.pack_forget()
            
            # Mostrar el frame de pestañas en la línea del título
            self.server_tabs_frame.pack(side="left", padx=(20, 0))
            
            # Crear una pestaña para cada servidor
            for i, (server_name, server_instance) in enumerate(cluster_panel.cluster_manager.servers.items()):
                server_map = server_instance.config.get('map', 'Unknown')
                
                # Crear botón de pestaña con closure correcto
                def create_tab_command(sname):
                    return lambda: self.switch_server_tab(sname)
                
                tab_button = ctk.CTkButton(
                    self.server_tabs_frame,
                    text=f"{server_name}\n({server_map})",
                    command=create_tab_command(server_name),
                    width=120,
                    height=50,
                    font=ctk.CTkFont(size=10),
                    fg_color=("blue", "darkblue") if i == 0 else ("gray", "darkgray")
                )
                tab_button.pack(side="left", padx=2, pady=2)
                
                self.server_tab_buttons[server_name] = tab_button
                
                # Crear área de consola para este servidor
                console_area = ctk.CTkTextbox(
                    self.main_frame,
                    state="disabled",
                    font=ctk.CTkFont(family="Consolas", size=10),
                    height=300  # Altura mínima para evitar que aparezca muy pequeña
                )
                
                self.server_tabs[server_name] = {
                    'console': console_area,
                    'lines': 0,
                    'monitoring': False
                }
                
                # Iniciar monitoreo de logs para este servidor (solo si no existe ya)
                if server_name not in self.server_threads or not self.server_threads[server_name].is_alive():
                    self.start_server_log_monitoring(server_name)
                else:
                    # Reactivar monitoreo existente
                    if server_name in self.server_tabs:
                        self.server_tabs[server_name]['monitoring'] = True
                    self.logger.info(f"🔄 Reutilizando hilo de monitoreo existente para servidor: {server_name}")
                
                # Ocultar inicialmente (excepto el primero)
                if i == 0:
                    self.active_server_tab = server_name
                    console_area.pack(fill="both", expand=True, padx=5, pady=5)
                
            # Eliminado: server_selection_frame ya no existe
            
            self.logger.info(f"Creadas {len(self.server_tab_buttons)} pestañas de servidor")
            
        except Exception as e:
            self.logger.error(f"Error al crear pestañas de servidor: {e}")
    
    def switch_server_tab(self, server_name):
        """Cambiar a una pestaña de servidor específica"""
        try:
            if server_name not in self.server_tabs:
                return
            
            # Ocultar la consola activa actual
            if self.active_server_tab and self.active_server_tab in self.server_tabs:
                self.server_tabs[self.active_server_tab]['console'].pack_forget()
                
                # Actualizar color del botón anterior
                if self.active_server_tab in self.server_tab_buttons:
                    self.server_tab_buttons[self.active_server_tab].configure(
                        fg_color=("gray", "darkgray")
                    )
            
            # Mostrar la nueva consola
            self.server_tabs[server_name]['console'].pack(fill="both", expand=True, padx=5, pady=5)
            self.active_server_tab = server_name
            
            # Actualizar color del botón activo
            if server_name in self.server_tab_buttons:
                self.server_tab_buttons[server_name].configure(
                    fg_color=("blue", "darkblue")
                )
            
            # Actualizar el servidor actual para el monitoreo
            self.current_server_id = server_name
            
            # Obtener información del servidor
            display_name = server_name
            if self.main_window and hasattr(self.main_window, 'cluster_panel'):
                cluster_panel = self.main_window.cluster_panel
                if (hasattr(cluster_panel, 'cluster_manager') and 
                    cluster_panel.cluster_manager and 
                    hasattr(cluster_panel.cluster_manager, 'servers') and 
                    server_name in cluster_panel.cluster_manager.servers):
                    server_instance = cluster_panel.cluster_manager.servers[server_name]
                    server_map = server_instance.config.get('map', 'Unknown')
                    display_name = f"{server_name} ({server_map})"
            
            # Actualizar título
            self.title_label.configure(text=f"🌐 Consola: {display_name}")
            
            # Agregar mensaje a la consola activa
            self.add_console_message_to_tab(server_name, f"🔄 Cambiado a servidor: {display_name}")
            
            self.logger.info(f"Cambiado a pestaña de servidor: {display_name}")
            
        except Exception as e:
            self.logger.error(f"Error al cambiar pestaña de servidor: {e}")
    
    def clear_server_tabs(self):
        """Limpiar todas las pestañas de servidor"""
        try:
            # NO detener monitoreo de logs - mantener hilos activos para cuando se vuelva al modo cluster
            # Solo marcar como no monitoreando en la UI
            for server_name in list(self.server_tabs.keys()):
                if server_name in self.server_tabs:
                    self.server_tabs[server_name]['monitoring'] = False
            
            # NO detener ni limpiar hilos - mantenerlos para reutilizar
            # Los hilos seguirán funcionando en segundo plano
            
            # Ocultar frame de pestañas
            self.server_tabs_frame.pack_forget()
            
            # Destruir botones de pestañas
            for button in self.server_tab_buttons.values():
                button.destroy()
            self.server_tab_buttons.clear()
            
            # Ocultar y limpiar áreas de consola
            for server_data in self.server_tabs.values():
                console = server_data['console']
                console.pack_forget()
                console.destroy()
            
            self.server_tabs.clear()
            self.active_server_tab = None
            
            # Eliminado: server_selection_frame ya no existe
            
            # Mostrar consola única
            if hasattr(self, 'console_frame'):
                self.console_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Restaurar título original
            self.title_label.configure(text="🖥️ Consola del Servidor")
            
        except Exception as e:
            self.logger.error(f"Error al limpiar pestañas de servidor: {e}")
    
    def add_console_message_to_tab(self, server_id, message):
        """Agregar mensaje a una pestaña específica de servidor usando cola thread-safe"""
        try:
            if server_id not in self.server_tabs:
                return
            
            # Enviar línea al PlayerMonitor para detectar eventos de jugadores
            if hasattr(self.main_window, 'player_monitor'):
                self.main_window.player_monitor.process_log_line(server_id, message)
            
            # Agregar mensaje a la cola thread-safe
            self.message_queue.put((server_id, message))
            
            # Iniciar procesador de cola si no está corriendo
            if not self.queue_processor_running:
                self.start_queue_processor()
                
        except Exception as e:
            self.logger.error(f"Error al agregar mensaje a cola para {server_id}: {e}")
    
    def _update_console_tab_safe(self, server_id, message):
        """Actualizar consola de forma segura en el hilo principal"""
        def do_update():
            try:
                if server_id not in self.server_tabs:
                    return
                
                console = self.server_tabs[server_id]['console']
                
                # Habilitar edición temporalmente
                console.configure(state="normal")
                
                # Agregar mensaje con timestamp
                timestamp = datetime.now().strftime("%H:%M:%S")
                formatted_message = f"[{timestamp}] {message}\n"
                console.insert("end", formatted_message)
                
                # Mantener límite de líneas
                lines = int(console.index("end-1c").split(".")[0])
                if lines > self.max_lines:
                    console.delete("1.0", f"{lines - self.max_lines}.0")
                
                # Scroll automático al final
                console.see("end")
                
                # Deshabilitar edición
                console.configure(state="disabled")
                
                # Actualizar contador de líneas
                self.server_tabs[server_id]['lines'] = lines
                
            except Exception as e:
                self.logger.error(f"Error en actualización de consola {server_id}: {e}")
        
        # Verificar si estamos en el hilo principal y si la ventana existe
        try:
            import threading
            current_thread = threading.current_thread()
            is_main_thread = isinstance(current_thread, threading._MainThread)
            
            if (is_main_thread and 
                hasattr(self, 'main_window') and self.main_window and 
                hasattr(self.main_window, 'root')):
                try:
                    # Verificar si la ventana aún existe
                    if self.main_window.root.winfo_exists():
                        do_update()
                    else:
                        # La ventana ya no existe, no hacer nada
                        return
                except Exception:
                    # Si hay error verificando la ventana, no hacer nada
                    return
            else:
                # No estamos en el hilo principal o no hay ventana válida
                # Simplemente no actualizar para evitar el error
                return
                
        except Exception as e:
            # Si hay cualquier error en la verificación, simplemente no actualizar
            # para evitar spam de errores en los logs
            pass
    
    def start_queue_processor(self):
        """Iniciar el procesador de cola de mensajes en el hilo principal"""
        try:
            # Verificar que estamos en el hilo principal
            import threading
            current_thread = threading.current_thread()
            is_main_thread = isinstance(current_thread, threading._MainThread)
            
            if not is_main_thread:
                # Si no estamos en el hilo principal, programar el inicio para el hilo principal
                if (hasattr(self, 'main_window') and self.main_window and 
                    hasattr(self.main_window, 'root')):
                    try:
                        if self.main_window.root.winfo_exists():
                            self.main_window.root.after_idle(self.start_queue_processor)
                    except Exception:
                        pass
                return
            
            if not self.queue_processor_running:
                self.queue_processor_running = True
                self.process_message_queue()
                
        except Exception as e:
            self.logger.error(f"Error iniciando procesador de cola: {e}")
    
    def process_message_queue(self):
        """Procesar mensajes de la cola en el hilo principal"""
        try:
            # Verificar que estamos en el hilo principal
            import threading
            current_thread = threading.current_thread()
            is_main_thread = isinstance(current_thread, threading._MainThread)
            
            if not is_main_thread:
                # Si no estamos en el hilo principal, detener el procesador
                self.queue_processor_running = False
                return
            
            # Procesar todos los mensajes disponibles en la cola
            while not self.message_queue.empty():
                try:
                    server_id, message = self.message_queue.get_nowait()
                    self._update_console_tab_safe(server_id, message)
                except queue.Empty:
                    break
                except Exception as e:
                    self.logger.error(f"Error procesando mensaje de cola: {e}")
            
            # Programar la próxima verificación de la cola solo si estamos en el hilo principal
            if (self.queue_processor_running and 
                hasattr(self, 'main_window') and self.main_window and 
                hasattr(self.main_window, 'root')):
                try:
                    # Verificar que la ventana aún existe
                    if self.main_window.root.winfo_exists():
                        self.main_window.root.after(100, self.process_message_queue)
                    else:
                        self.queue_processor_running = False
                except Exception:
                    self.queue_processor_running = False
            
        except Exception as e:
            self.logger.error(f"Error en procesador de cola: {e}")
            self.queue_processor_running = False
    
    def start_server_log_monitoring(self, server_name):
        """Iniciar monitoreo de logs para un servidor específico"""
        try:
            self.logger.info(f"🔍 DEBUG: Intentando iniciar monitoreo para {server_name}")
            
            if server_name in self.server_threads:
                # Ya hay un hilo monitoreando este servidor
                self.logger.info(f"🔍 DEBUG: Ya existe hilo para {server_name}, saltando")
                return
            
            # Crear y iniciar hilo de monitoreo para este servidor
            monitor_thread = threading.Thread(
                target=self._monitor_server_log,
                args=(server_name,),
                daemon=True,
                name=f"LogMonitor-{server_name}"
            )
            monitor_thread.start()
            self.server_threads[server_name] = monitor_thread
            
            # Marcar como monitoreando
            if server_name in self.server_tabs:
                self.server_tabs[server_name]['monitoring'] = True
                self.logger.info(f"🔍 DEBUG: Marcado {server_name} como monitoring=True")
            
            self.logger.info(f"🔍 Iniciado monitoreo de logs para servidor: {server_name} (Hilo: {monitor_thread.name})")
            
        except Exception as e:
            self.logger.error(f"Error iniciando monitoreo de logs para {server_name}: {e}")
    
    def _monitor_server_log(self, server_name):
        """Monitorear el archivo de log de un servidor específico"""
        consecutive_empty_reads = 0
        max_empty_reads = 10
        
        # Variables específicas para este servidor
        server_position_key = f"_last_file_position_{server_name}"
        server_file_key = f"_current_log_file_{server_name}"
        server_loaded_key = f"_content_loaded_{server_name}"
        
        self.logger.info(f"🔍 DEBUG: Iniciando bucle de monitoreo para {server_name}")
        
        while (server_name in self.server_tabs and 
               self.server_tabs[server_name].get('monitoring', False)):
            try:
                # Obtener archivo de log para este servidor específico
                game_log_path = self._get_latest_game_log(server_name)
                self.logger.debug(f"🔍 DEBUG: {server_name} - Ruta de log: {game_log_path}")
                
                if game_log_path and os.path.exists(game_log_path):
                    try:
                        with open(game_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                            # Si es la primera vez que leemos este archivo
                            if (not hasattr(self, server_position_key) or 
                                getattr(self, server_position_key) is None or
                                not hasattr(self, server_file_key) or
                                getattr(self, server_file_key) != game_log_path or
                                not hasattr(self, server_loaded_key) or
                                not getattr(self, server_loaded_key)):
                                
                                # Leer contenido existente (últimas 50 líneas)
                                f.seek(0, 0)
                                all_lines = f.readlines()
                                if len(all_lines) > 50:
                                    lines_to_show = all_lines[-50:]
                                else:
                                    lines_to_show = all_lines
                                
                                for line in lines_to_show:
                                    line = line.strip()
                                    if line:
                                        self.add_console_message_to_tab(server_name, line)
                                
                                # Posicionarse al final para futuras lecturas
                                f.seek(0, 2)
                                setattr(self, server_position_key, f.tell())
                                setattr(self, server_file_key, game_log_path)
                                setattr(self, server_loaded_key, True)
                            else:
                                # Ir a la posición donde nos quedamos
                                f.seek(getattr(self, server_position_key))
                            
                            # Leer nuevas líneas
                            new_lines_count = 0
                            while True:
                                line = f.readline()
                                if line:
                                    consecutive_empty_reads = 0
                                    line = line.strip()
                                    if line:
                                        new_lines_count += 1
                                        self.add_console_message_to_tab(server_name, line)
                                    
                                    # Actualizar posición
                                    setattr(self, server_position_key, f.tell())
                                else:
                                    break
                            
                            if new_lines_count > 0:
                                self.logger.debug(f"🔍 DEBUG: {server_name} - Leídas {new_lines_count} nuevas líneas")
                            
                    except Exception as e:
                        self.logger.error(f"Error leyendo archivo de log para {server_name}: {e}")
                        time.sleep(0.5)
                else:
                    consecutive_empty_reads += 1
                    if consecutive_empty_reads >= max_empty_reads:
                        time.sleep(2.0)
                    else:
                        time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error en monitoreo de logs para {server_name}: {e}")
                time.sleep(1.0)
            
            time.sleep(0.1)  # Pequeña pausa entre lecturas
        
        # Limpiar al terminar
        if server_name in self.server_threads:
            del self.server_threads[server_name]
        
        self.logger.info(f"🔍 Monitoreo de logs terminado para servidor: {server_name}")
