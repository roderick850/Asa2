import customtkinter as ctk
import threading
import time
import os
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
            self.server_manager = ServerManager(config_manager, logger)
        
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
        
        # Label informativo
        info_label = ctk.CTkLabel(
            controls_frame,
            text="La consola del servidor se muestra automáticamente",
            font=ctk.CTkFont(size=12),
            text_color="green"
        )
        info_label.pack(side="left", padx=10, pady=5)
        
        # Botón para limpiar consola
        self.clear_button = ctk.CTkButton(
            controls_frame,
            text="🧹 Limpiar Consola",
            command=self.clear_console,
            width=120,
            height=30
        )
        self.clear_button.pack(side="right", padx=10, pady=5)
        
        # Botón para guardar consola
        self.save_button = ctk.CTkButton(
            controls_frame,
            text="💾 Guardar Consola",
            command=self.save_console,
            width=120,
            height=30
        )
        self.save_button.pack(side="right", padx=5, pady=5)
        
        # Botón para forzar recarga del contenido del archivo de log
        self.reload_content_button = ctk.CTkButton(
            controls_frame,
            text="📄 Recargar Contenido",
            command=self.force_reload_content,
            width=140,
            height=30
        )
        self.reload_content_button.pack(side="right", padx=5, pady=5)
        
        # Botón para iniciar monitoreo de consola (se eliminará - siempre monitorear)
        self.start_monitoring_button = ctk.CTkButton(
            controls_frame,
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
        # Solo si no hay un servidor ejecutándose ya
        if not (hasattr(self.server_manager, 'server_process') and 
                self.server_manager.server_process and 
                self.server_manager.server_process.poll() is None):
            self.parent.after(2000, self.auto_start_server)
        else:
            self.add_console_message("✅ Servidor ya está ejecutándose, monitoreando...")
            # Verificar si ya está activo
            if hasattr(self.main_window, 'update_server_status'):
                self.main_window.update_server_status("Verificando...")
    
    def auto_start_server(self):
        """Iniciar el servidor automáticamente"""
        self.add_console_message("🔄 Iniciando servidor automáticamente...")
        
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
                    custom_args=server_args,
                    capture_console=True
                )
            else:
                # Fallback si no hay panel principal
                self.server_manager.start_server_with_args(
                    callback=self.on_server_status_change,
                    server_name="Prueba",
                    map_name="The Center",
                    capture_console=True
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
        
        # Verificar si el servidor está ejecutándose
        if (hasattr(self.server_manager, 'server_process') and 
            self.server_manager.server_process and 
            self.server_manager.server_process.poll() is None):
            
            # El servidor ya está ejecutándose, verificar si está en modo de captura
            self.add_console_message("✅ Servidor ya ejecutándose, verificando modo de captura...")
            
            # Solo reiniciar si no está en modo de captura
            if not hasattr(self.server_manager.server_process, 'stdout') or not self.server_manager.server_process.stdout:
                self.add_console_message("🔄 Servidor no está en modo de captura, reiniciando...")
                try:
                    # Detener el servidor actual
                    self.server_manager.stop_server()
                    time.sleep(2)
                    
                    # Reiniciar en modo de captura
                    self._start_server_in_capture_mode()
                    self.add_console_message("✅ Servidor reiniciado en modo de captura de consola")
                except Exception as e:
                    self.add_console_message(f"❌ Error reiniciando servidor: {e}")
                    self.logger.error(f"Error reiniciando servidor para captura: {e}")
            else:
                self.add_console_message("✅ Servidor ya está en modo de captura de consola")
        else:
            # El servidor no está ejecutándose, iniciarlo en modo de captura
            try:
                self._start_server_in_capture_mode()
                self.add_console_message("🚀 Servidor iniciado en modo de captura de consola")
            except Exception as e:
                self.add_console_message(f"❌ Error iniciando servidor: {e}")
                self.logger.error(f"Error iniciando servidor: {e}")
        
        # Iniciar el thread de monitoreo
        self.console_thread = threading.Thread(target=self.console_monitor, daemon=True)
        self.console_thread.start()
    
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
                custom_args=server_args,
                capture_console=True
            )
        else:
            # Fallback si no hay panel principal
            result = self.server_manager.start_server_with_args(
                callback=self.on_server_status_change,
                server_name="Prueba",
                map_name="The Center",
                custom_args=[],
                capture_console=True
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
                # Verificar si el servidor está ejecutándose
                if hasattr(self.server_manager, 'server_process') and self.server_manager.server_process:
                    # Verificar si el proceso sigue vivo
                    if self.server_manager.server_process.poll() is None:
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
            # Verificar si el servidor está ejecutándose
            if (hasattr(self.server_manager, 'server_process') and 
                self.server_manager.server_process and 
                self.server_manager.server_process.poll() is None):
                
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
