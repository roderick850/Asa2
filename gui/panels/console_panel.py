import customtkinter as ctk
import threading
import time
import os
import psutil
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
            
        # Frame principal
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame, 
            text="🖥️ Consola del Servidor", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(5, 10))
        
        # Frame de controles
        controls_frame = ctk.CTkFrame(main_frame)
        controls_frame.pack(fill="x", padx=5, pady=5)
        
        # Frame para el switch de visibilidad de consola
        console_visibility_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        console_visibility_frame.pack(fill="x", padx=10, pady=5)
        
        # Switch para mostrar/ocultar consola del servidor
        self.console_visibility_var = ctk.BooleanVar(value=self.config_manager.get("app", "show_server_console", default="true").lower() == "true")
        self.show_console_switch = ctk.CTkSwitch(
            console_visibility_frame,
            text="Mostrar Consola del Servidor",
            command=self.toggle_server_console_visibility,
            variable=self.console_visibility_var
        )
        self.show_console_switch.pack(side="left", padx=(0, 20))
        
        # Etiqueta explicativa
        ctk.CTkLabel(
            console_visibility_frame, 
            text="Controla si la ventana de consola del servidor es visible o se ejecuta en segundo plano",
            font=("Arial", 10),
            text_color=("gray50", "gray70")
        ).pack(side="left", padx=(0, 20))
        
        # Frame para botones de control
        buttons_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=10, pady=5)
        
        # Label informativo
        info_label = ctk.CTkLabel(
            buttons_frame,
            text="La consola del servidor se muestra automáticamente",
            font=ctk.CTkFont(size=12),
            text_color="green"
        )
        info_label.pack(side="left", padx=10, pady=5)
        
        # Botón para limpiar consola
        self.clear_button = ctk.CTkButton(
            buttons_frame,
            text="🧹 Limpiar Consola",
            command=self.clear_console,
            width=120,
            height=30
        )
        self.clear_button.pack(side="right", padx=10, pady=5)
        
        # Botón para guardar consola
        self.save_button = ctk.CTkButton(
            buttons_frame,
            text="💾 Guardar Consola",
            command=self.save_console,
            width=120,
            height=30
        )
        self.save_button.pack(side="right", padx=5, pady=5)
        
        # Botón para forzar recarga del contenido del archivo de log
        self.reload_content_button = ctk.CTkButton(
            buttons_frame,
            text="📄 Recargar Contenido",
            command=self.force_reload_content,
            width=140,
            height=30
        )
        self.reload_content_button.pack(side="right", padx=5, pady=5)
        
        # Botón para iniciar monitoreo de consola (se eliminará - siempre monitorear)
        self.start_monitoring_button = ctk.CTkButton(
            buttons_frame,
            text="🔄 Reiniciar Monitoreo",
            command=self.start_console,
            width=140,
            height=30
        )
        self.start_monitoring_button.pack(side="right", padx=5, pady=5)
        
        # Frame para comandos
        command_frame = ctk.CTkFrame(main_frame)
        command_frame.pack(fill="x", padx=5, pady=5)
        
        # Label para comandos
        command_label = ctk.CTkLabel(
            command_frame,
            text="Comando:",
            font=ctk.CTkFont(size=12)
        )
        command_label.pack(side="left", padx=(10, 5), pady=5)
        
        # Entrada de comando
        self.command_entry = ctk.CTkEntry(
            command_frame,
            placeholder_text="Escribe un comando del servidor...",
            width=300
        )
        self.command_entry.pack(side="left", padx=5, pady=5)
        
        # Enlazar la tecla Enter para enviar comandos
        self.command_entry.bind("<Return>", lambda event: self.send_command())
        
        # Botón para enviar comando
        self.send_button = ctk.CTkButton(
            command_frame,
            text="📤 Enviar",
            command=self.send_command,
            width=80,
            height=30
        )
        self.send_button.pack(side="left", padx=5, pady=5)
        
        # Frame para la consola
        console_frame = ctk.CTkFrame(main_frame)
        console_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Título de la consola
        console_title = ctk.CTkLabel(
            console_frame, 
            text="Salida del Servidor:", 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        console_title.pack(pady=(5, 2))
        
        # Área de texto para la consola (con scrollbar)
        self.console_text = ctk.CTkTextbox(
            console_frame, 
            state="disabled",
            font=ctk.CTkFont(family="Consolas", size=10)
        )
        self.console_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Frame de estado
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.pack(fill="x", padx=5, pady=5)
        
        # Estado de la consola
        self.status_label = ctk.CTkLabel(
            status_frame, 
            text="Estado: Iniciando automáticamente...", 
            text_color="blue"
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Contador de líneas
        self.lines_label = ctk.CTkLabel(
            status_frame, 
            text="Líneas: 0"
        )
        self.lines_label.pack(side="right", padx=10, pady=5)
        
        # Mensaje inicial
        self.add_console_message("Consola del servidor inicializada. Iniciando monitoreo automático...")
        
        # Iniciar monitoreo automáticamente con retraso para asegurar que la app esté lista
        self.parent.after(3000, self.auto_start_monitoring)
        

    
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
            self.parent.after(2000, self.auto_start_server)
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
            self.main_window.root.after(1000, self.refresh_console_visibility_switch)
    
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
            # Notificar al MainWindow que el servidor está activo
            if hasattr(self.main_window, 'update_server_status'):
                self.main_window.update_server_status("Activo")
            
            # Actualizar el estado local
            self.add_console_message("🟢 Servidor activo y listo para conexiones")
            
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

    def _get_latest_game_log(self):
        """Obtener la ruta del archivo de log del juego más reciente"""
        try:
            if hasattr(self.main_window, 'selected_server') and self.main_window.selected_server:
                server_name = self.main_window.selected_server
                # Construir la ruta al directorio de logs del juego
                root_path = self.config_manager.get("server", "root_path")
                if root_path:
                    logs_dir = os.path.join(root_path, server_name, "ShooterGame", "Saved", "Logs")
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
                            
                            # Si el archivo de log cambió, resetear la posición
                            if not hasattr(self, '_current_log_file') or self._current_log_file != latest_log:
                                self._current_log_file = latest_log
                                self._last_file_position = None
                            
                            return latest_log
        except Exception as e:
            self.logger.error(f"Error obteniendo archivo de log del juego: {e}")
        
        return None

    def on_server_status_change(self, status, message):
        """Callback para cambios de estado del servidor"""
        if status == "started":
            self.add_console_message("🟢 Servidor iniciado correctamente")
            # El estado "Activo" se marcará cuando se detecte el mensaje de inicio completo
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
            if self.server_manager and self.server_manager.is_server_running():
                    # Verificar si la consola está visible
                    if self.server_manager.server_console_hwnd:
                        # La consola existe, verificar si está visible
                        import ctypes
                        is_visible = ctypes.windll.user32.IsWindowVisible(self.server_manager.server_console_hwnd)
                        self.console_visibility_var.set(is_visible)
                    else:
                        # Buscar la ventana de consola
                        self.server_manager._find_server_console_window()
                        if self.server_manager.server_console_hwnd:
                            import ctypes
                            is_visible = ctypes.windll.user32.IsWindowVisible(self.server_manager.server_console_hwnd)
                            self.console_visibility_var.set(is_visible)
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
                            
                            # Limpiar estado de archivos para forzar nueva lectura
                            if hasattr(self, '_last_file_position'):
                                self._last_file_position = None
                            if hasattr(self, '_current_log_file'):
                                self._current_log_file = None
                            if hasattr(self, '_content_loaded'):
                                self._content_loaded = False
                            
                            # Actualizar estado en MainWindow
                            if hasattr(self.main_window, 'update_server_status'):
                                self.main_window.update_server_status("Activo (Monitoreando)")
                            
                            self.add_console_message("📋 Monitoreo configurado para leer logs del servidor existente")
                            return True
                            
                        except psutil.NoSuchProcess:
                            self.add_console_message("⚠️ El proceso desapareció durante la reconexión")
                            continue
                        except psutil.AccessDenied:
                            self.add_console_message("⚠️ Sin permisos para acceder al proceso")
                            continue
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            # No se encontró servidor
            self.add_console_message("❌ No se encontró proceso del servidor para reconectar")
            return False
            
        except Exception as e:
            self.logger.error(f"Error en reconexión al servidor: {e}")
            self.add_console_message(f"❌ Error en reconexión: {e}")
            return False
