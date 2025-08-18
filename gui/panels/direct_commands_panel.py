import customtkinter as ctk
import subprocess
import threading
import time
import os
from datetime import datetime, timedelta
from tkinter import messagebox
from utils.scheduled_commands import ScheduledCommandsManager, ScheduledCommand
from utils.dialogs import AddTaskDialog, TasksListDialog, CommandHistoryDialog

class DirectCommandsPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger, main_window):
        super().__init__(parent)
        self.parent = parent
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        
        # Variables de estado
        self.server_process = None
        self.is_connected = False
        self.command_history = []
        self.monitoring_thread = None
        self.stop_monitoring = False
        self.auto_connect_enabled = True
        
        # Sistema de comandos programados
        self.scheduled_manager = ScheduledCommandsManager()
        self.scheduled_manager.on_command_executed = self._on_command_executed
        self.scheduled_manager.on_command_failed = self._on_command_failed
        
        # Variables para monitoreo del archivo de log
        self.log_monitoring_thread = None
        self.stop_log_monitoring_flag = False
        self.last_log_position = 0
        self.current_log_file = None
        
        # Variables para monitoreo directo del stdout
        self.stdout_monitoring_thread = None
        self.stop_stdout_monitoring_flag = False
        
        # Variable para modo debug
        self.debug_mode = False
        
        # Empaquetar el frame principal
        self.pack(fill="both", expand=True)
        
        # Crear widgets
        self.create_widgets()
        
        # Cargar configuración
        self.load_config()
        
        # Iniciar monitoreo automático para conectar cuando el servidor esté disponible
        self.start_auto_connect_monitoring()
    
    def _safe_schedule_ui_update(self, callback, delay=0):
        """Programar actualización de UI de forma segura"""
        try:
            # Verificar si la ventana principal aún existe
            if (self.main_window and hasattr(self.main_window, 'root') and 
                hasattr(self.main_window.root, 'winfo_exists')):
                try:
                    if self.main_window.root.winfo_exists():
                        self.main_window.root.after(delay, callback)
                        return
                except Exception:
                    pass
            
            # Verificar si el parent aún existe
            try:
                if hasattr(self.parent, 'winfo_exists') and self.parent.winfo_exists():
                    self.parent.after(delay, callback)
            except Exception:
                pass
        except Exception:
            pass
        
    def create_widgets(self):
        """Crear todos los widgets del panel"""
        # Frame principal con scroll
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título principal
        title_label = ctk.CTkLabel(main_frame, text="⌨️ Comandos Directos del Servidor", 
                                 font=("Arial", 20, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Frame de estado de conexión
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.pack(fill="x", padx=10, pady=10)
        
        status_title = ctk.CTkLabel(status_frame, text="🔌 Estado de Conexión", 
                                  font=("Arial", 16, "bold"))
        status_title.pack(pady=10)
        
        # Indicador de estado
        self.status_label = ctk.CTkLabel(status_frame, text="❌ Desconectado", 
                                       fg_color="red", corner_radius=5, padx=10, pady=5)
        self.status_label.pack(pady=5)
        
        # Botones de conexión
        connection_buttons_frame = ctk.CTkFrame(status_frame)
        connection_buttons_frame.pack(fill="x", padx=10, pady=10)
        
        self.connect_button = ctk.CTkButton(connection_buttons_frame, text="🔌 Conectar al Servidor", 
                                          command=self.connect_to_server, fg_color="green")
        self.connect_button.pack(side="left", padx=5)
        
        self.disconnect_button = ctk.CTkButton(connection_buttons_frame, text="🔌 Desconectar", 
                                             command=self.disconnect_from_server, fg_color="red", state="disabled")
        self.disconnect_button.pack(side="left", padx=5)
        
        # Separador
        separator1 = ctk.CTkFrame(main_frame, height=2)
        separator1.pack(fill="x", padx=10, pady=20)
        
        # Frame de comandos rápidos
        quick_commands_frame = ctk.CTkFrame(main_frame)
        quick_commands_frame.pack(fill="x", padx=10, pady=10)
        
        quick_title = ctk.CTkLabel(quick_commands_frame, text="⚡ Comandos Rápidos", 
                                 font=("Arial", 16, "bold"))
        quick_title.pack(pady=10)
        
        # Botones de comandos rápidos
        quick_buttons_frame = ctk.CTkFrame(quick_commands_frame)
        quick_buttons_frame.pack(fill="x", padx=10, pady=10)
        
        # Primera fila
        row1_frame = ctk.CTkFrame(quick_buttons_frame)
        row1_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(row1_frame, text="📢 Broadcast", 
                     command=lambda: self.quick_command("broadcast Hola desde el administrador!"),
                     width=120).pack(side="left", padx=5)
        
        ctk.CTkButton(row1_frame, text="⏰ Tiempo", 
                     command=lambda: self.quick_command("time"),
                     width=120).pack(side="left", padx=5)
        
        ctk.CTkButton(row1_frame, text="🌤️ Clima", 
                     command=lambda: self.quick_command("weather"),
                     width=120).pack(side="left", padx=5)
        
        ctk.CTkButton(row1_frame, text="📋 Lista Jugadores", 
                     command=lambda: self.quick_command("listplayers"),
                     width=120).pack(side="left", padx=5)
        
        # Segunda fila
        row2_frame = ctk.CTkFrame(quick_buttons_frame)
        row2_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(row2_frame, text="💾 Guardar Mundo", 
                     command=lambda: self.quick_command("saveworld"),
                     width=120).pack(side="left", padx=5)
        
        ctk.CTkButton(row2_frame, text="🔄 Reiniciar", 
                     command=lambda: self.quick_command("doexit"),
                     width=120).pack(side="left", padx=5)
        
        ctk.CTkButton(row2_frame, text="📊 Estadísticas", 
                     command=lambda: self.quick_command("showmyadminmanager"),
                     width=120).pack(side="left", padx=5)
        
        ctk.CTkButton(row2_frame, text="🌍 Información Mapa", 
                     command=lambda: self.quick_command("showworldinfo"),
                     width=120).pack(side="left", padx=5)
        
        # Separador
        separator2 = ctk.CTkFrame(main_frame, height=2)
        separator2.pack(fill="x", padx=10, pady=20)
        
        # Frame de comando personalizado
        custom_command_frame = ctk.CTkFrame(main_frame)
        custom_command_frame.pack(fill="x", padx=10, pady=10)
        
        custom_title = ctk.CTkLabel(custom_command_frame, text="⌨️ Comando Personalizado", 
                                   font=("Arial", 16, "bold"))
        custom_title.pack(pady=10)
        
        # Entrada de comando
        command_input_frame = ctk.CTkFrame(custom_command_frame)
        command_input_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(command_input_frame, text="Comando:").pack(side="left", padx=5)
        self.command_entry = ctk.CTkEntry(command_input_frame, placeholder_text="broadcast Hola Mundo")
        self.command_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkButton(command_input_frame, text="📤 Ejecutar", 
                     command=self.execute_custom_command).pack(side="right", padx=5)
        
        # Separador
        separator3 = ctk.CTkFrame(main_frame, height=2)
        separator3.pack(fill="x", padx=10, pady=20)
        
        # Frame de comandos programados
        scheduled_frame = ctk.CTkFrame(main_frame)
        scheduled_frame.pack(fill="x", padx=10, pady=10)
        
        scheduled_title = ctk.CTkLabel(scheduled_frame, text="⏰ Comandos Programados", 
                                     font=("Arial", 16, "bold"))
        scheduled_title.pack(pady=10)
        
        # Botones de gestión de tareas
        scheduled_buttons_frame = ctk.CTkFrame(scheduled_frame)
        scheduled_buttons_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(scheduled_buttons_frame, text="➕ Nueva Tarea", 
                     command=self.show_add_task_dialog, fg_color="green").pack(side="left", padx=5)
        
        ctk.CTkButton(scheduled_buttons_frame, text="📋 Ver Tareas", 
                     command=self.show_tasks_list, fg_color="blue").pack(side="left", padx=5)
        
        ctk.CTkButton(scheduled_buttons_frame, text="📊 Historial", 
                     command=self.show_command_history, fg_color="orange").pack(side="left", padx=5)
        
        # Estado del programador
        self.scheduler_status_label = ctk.CTkLabel(scheduled_frame, text="⏸️ Programador: Detenido", 
                                                 fg_color="red", corner_radius=5, padx=10, pady=5)
        self.scheduler_status_label.pack(pady=5)
        
        # Separador
        separator5 = ctk.CTkFrame(main_frame, height=2)
        separator5.pack(fill="x", padx=10, pady=20)
        
        # Frame de monitoreo en tiempo real
        monitoring_frame = ctk.CTkFrame(main_frame)
        monitoring_frame.pack(fill="x", padx=10, pady=10)
        
        monitoring_title = ctk.CTkLabel(monitoring_frame, text="📡 Monitoreo en Tiempo Real", 
                                      font=("Arial", 16, "bold"))
        monitoring_title.pack(pady=10)
        
        # Botones de monitoreo
        monitoring_buttons_frame = ctk.CTkFrame(monitoring_frame)
        monitoring_buttons_frame.pack(fill="x", padx=10, pady=10)
        
        self.monitor_button = ctk.CTkButton(monitoring_buttons_frame, text="📡 Iniciar Monitoreo", 
                                          command=self.toggle_monitoring, fg_color="green")
        self.monitor_button.pack(side="left", padx=5)
        
        ctk.CTkButton(monitoring_buttons_frame, text="🔄 Actualizar Ahora", 
                     command=self.refresh_server_info).pack(side="left", padx=5)
        
        # Botón para recargar contenido
        self.reload_log_button = ctk.CTkButton(monitoring_buttons_frame, text="🔄 Solicitar Info", 
                                             command=self.reload_log_content, fg_color="blue")
        self.reload_log_button.pack(side="left", padx=5)
        
        # Botón para modo debug
        self.debug_button = ctk.CTkButton(monitoring_buttons_frame, text="🐛 Modo Debug", 
                                        command=self.toggle_debug_mode, fg_color="orange")
        self.debug_button.pack(side="left", padx=5)
        
        # Separador
        separator4 = ctk.CTkFrame(main_frame, height=2)
        separator4.pack(fill="x", padx=10, pady=20)
        
        # Frame de resultados
        results_frame = ctk.CTkFrame(main_frame)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        results_title = ctk.CTkLabel(results_frame, text="📋 Respuestas del Servidor", 
                                   font=("Arial", 16, "bold"))
        results_title.pack(pady=10)
        
        # Área de resultados
        self.results_text = ctk.CTkTextbox(results_frame, height=200)
        self.results_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Botones de resultados
        results_buttons_frame = ctk.CTkFrame(results_frame)
        results_buttons_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(results_buttons_frame, text="🗑️ Limpiar", 
                     command=self.clear_results).pack(side="left", padx=5)
        
        ctk.CTkButton(results_buttons_frame, text="💾 Guardar", 
                     command=self.save_results).pack(side="left", padx=5)
        
        ctk.CTkButton(results_buttons_frame, text="📋 Copiar", 
                     command=self.copy_results).pack(side="left", padx=5)
        
    def load_config(self):
        """Cargar configuración"""
        try:
            # Aquí podrías cargar configuraciones específicas si las necesitas
            pass
        except Exception as e:
            self.logger.error(f"Error al cargar configuración: {e}")
    
    def connect_to_server(self):
        """Conectar al servidor de Ark"""
        try:
            if self.is_connected:
                self.show_message("Ya estás conectado al servidor", "info")
                return
            
            # Obtener información del servidor actual
            server_name = self.main_window.selected_server
            if not server_name:
                self.show_error("Debes seleccionar un servidor primero")
                return
            
            # Verificar que el server_manager esté disponible
            if not hasattr(self.main_window, 'server_manager') or not self.main_window.server_manager:
                self.show_error("El administrador del servidor no está disponible")
                return
            
            # Buscar el proceso del servidor
            server_process = self.main_window.server_manager.server_process
            if not server_process or server_process.poll() is not None:
                self.show_error("El servidor no está ejecutándose. Inicia el servidor primero desde la pestaña Consola.")
                self.add_result("ℹ️ Información", "El servidor se iniciará automáticamente desde la pestaña Consola. La conexión se establecerá automáticamente cuando esté disponible.")
                self.add_result("⚠️ Importante", "Para usar comandos programados, el servidor debe iniciarse con captura de consola habilitada.")
                return
            
            # Verificar que el servidor tenga stdin disponible
            if not hasattr(server_process, 'stdin') or server_process.stdin is None:
                self.show_error("El servidor no fue iniciado con captura de stdin.")
                self.add_result("⚠️ Advertencia", "Para comandos programados, el servidor necesita stdin habilitado.")
                self.add_result("💡 Solución", "El servidor se reiniciará automáticamente con stdin habilitado.")
                
                # Reiniciar automáticamente el servidor con stdin habilitado
                self.restart_server_with_stdin()
                return
            
            # Intentar conectar enviando un comando de prueba
            try:
                # Enviar comando de prueba (sin encode porque el proceso usa text=True)
                server_process.stdin.write("time\n")
                server_process.stdin.flush()
                
                # Marcar como conectado
                self.is_connected = True
                self.server_process = server_process
                
                # Conectar el programador de comandos
                self.scheduled_manager.set_server_process(server_process)
                self.scheduled_manager.start_scheduler()
                
                # Actualizar interfaz
                self.status_label.configure(text="✅ Conectado", fg_color="green")
                self.scheduler_status_label.configure(text="▶️ Programador: Activo", fg_color="green")
                self.connect_button.configure(state="disabled")
                self.disconnect_button.configure(state="normal")
                
                self.show_success("✅ Conectado exitosamente al servidor")
                self.add_result("🔌 Conexión", "Conectado al servidor de Ark")
                self.add_result("⏰ Programador", "Sistema de comandos programados iniciado")
                
                # Iniciar monitoreo automáticamente
                self.start_monitoring()
                
            except Exception as e:
                self.show_error(f"Error al conectar: {e}")
                
        except Exception as e:
            self.show_error(f"Error al conectar al servidor: {e}")
    
    def disconnect_from_server(self):
        """Desconectar del servidor"""
        try:
            if not self.is_connected:
                return
            
            # Detener monitoreo
            self.stop_monitoring_thread()
            
            # Detener programador de comandos
            self.scheduled_manager.stop_scheduler()
            
            # Limpiar estado
            self.is_connected = False
            self.server_process = None
            
            # Actualizar interfaz
            self.status_label.configure(text="❌ Desconectado", fg_color="red")
            self.scheduler_status_label.configure(text="⏸️ Programador: Detenido", fg_color="red")
            self.connect_button.configure(state="normal")
            self.disconnect_button.configure(state="disabled")
            
            self.show_success("✅ Desconectado del servidor")
            self.add_result("🔌 Conexión", "Desconectado del servidor")
            self.add_result("⏰ Programador", "Sistema de comandos programados detenido")
            
        except Exception as e:
            self.show_error(f"Error al desconectar: {e}")
    
    def quick_command(self, command):
        """Ejecutar comando rápido"""
        self.command_entry.delete(0, "end")
        self.command_entry.insert(0, command)
        self.execute_custom_command()
    
    def execute_custom_command(self):
        """Ejecutar comando personalizado"""
        if not self.is_connected:
            self.show_error("Debes conectarte al servidor primero")
            return
        
        command = self.command_entry.get().strip()
        if not command:
            self.show_error("Ingresa un comando para ejecutar")
            return
        
        try:
            # Enviar comando al servidor
            self.server_process.stdin.write(f"{command}\n")
            self.server_process.stdin.flush()
            
            # Agregar a historial
            self.command_history.append(command)
            
            # Mostrar en resultados
            self.add_result("📤 Comando Enviado", f"Comando: {command}")
            
            # Limpiar entrada
            self.command_entry.delete(0, "end")
            
        except Exception as e:
            self.show_error(f"Error al ejecutar comando: {e}")
    
    def toggle_monitoring(self):
        """Alternar monitoreo en tiempo real"""
        if not self.is_connected:
            self.show_error("Debes conectarte al servidor primero")
            return
            
        if not self.monitoring_thread or not self.monitoring_thread.is_alive():
            self.start_monitoring()
        else:
            self.stop_monitoring_thread()
    
    def start_monitoring(self):
        """Iniciar monitoreo en tiempo real"""
        if not self.is_connected:
            return
            
        self.stop_monitoring = False
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Iniciar monitoreo directo del stdout del servidor
        self.start_stdout_monitoring()
        
        self.monitor_button.configure(text="⏹️ Detener Monitoreo", fg_color="red")
        self.add_result("📡 Monitoreo", "Monitoreo en tiempo real iniciado")
    
    def stop_monitoring_thread(self):
        """Detener monitoreo en tiempo real"""
        self.stop_monitoring = True
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
        
        # Detener también el monitoreo del stdout
        self.stop_stdout_monitoring()
        
        self.monitor_button.configure(text="📡 Iniciar Monitoreo", fg_color="green")
        self.add_result("📡 Monitoreo", "Monitoreo en tiempo real detenido")
    
    def _monitoring_loop(self):
        """Bucle de monitoreo en tiempo real"""
        while not self.stop_monitoring and self.is_connected:
            try:
                # Enviar comando de estado cada 30 segundos
                if self.server_process and self.server_process.poll() is None:
                    self.server_process.stdin.write("time\n")
                    self.server_process.stdin.flush()
                
                time.sleep(30)  # Actualizar cada 30 segundos
                
            except Exception as e:
                self.logger.error(f"Error en monitoreo: {e}")
                break
    
    def refresh_server_info(self):
        """Actualizar información del servidor"""
        if not self.is_connected:
            self.show_error("Debes conectarte al servidor primero")
            return
        
        try:
            # Enviar comando para obtener información
            self.server_process.stdin.write("showworldinfo\n")
            self.server_process.stdin.flush()
            
            self.add_result("🔄 Actualización", "Solicitando información del servidor...")
            
        except Exception as e:
            self.show_error(f"Error al actualizar información: {e}")
    
    def add_result(self, title, content):
        """Agregar resultado al área de texto"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        result_text = f"[{timestamp}] {title}\n{content}\n{'='*50}\n\n"
        
        self.results_text.configure(state="normal")
        self.results_text.insert("end", result_text)
        self.results_text.configure(state="disabled")
        self.results_text.see("end")
    
    def clear_results(self):
        """Limpiar área de resultados"""
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.configure(state="disabled")
    
    def save_results(self):
        """Guardar resultados en archivo"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.results_text.get("1.0", "end"))
                self.show_success(f"✅ Resultados guardados en: {filename}")
                
        except Exception as e:
            self.show_error(f"Error al guardar: {e}")
    
    def copy_results(self):
        """Copiar resultados al portapapeles"""
        try:
            self.results_text.configure(state="normal")
            self.results_text.tag_add("sel", "1.0", "end")
            self.results_text.configure(state="disabled")
            
            self.clipboard_clear()
            self.clipboard_append(self.results_text.get("1.0", "end"))
            self.show_success("✅ Resultados copiados al portapapeles")
            
        except Exception as e:
            self.show_error(f"Error al copiar: {e}")
    
    def show_success(self, message):
        """Mostrar mensaje de éxito"""
        self.add_result("✅ Éxito", message)
    
    def show_error(self, message):
        """Mostrar mensaje de error"""
        self.add_result("❌ Error", message)
    
    def show_message(self, message, message_type="info"):
        """Mostrar mensaje general"""
        if message_type == "info":
            self.add_result("ℹ️ Información", message)
        elif message_type == "warning":
            self.add_result("⚠️ Advertencia", message)
        else:
            self.add_result("ℹ️ Mensaje", message)
    
    def start_auto_connect_monitoring(self):
        """Iniciar monitoreo automático para conectar cuando el servidor esté disponible"""
        def auto_connect_loop():
            self.logger.info("Iniciando monitoreo automático de conexión...")
            while self.auto_connect_enabled and not self.is_connected:
                try:
                    # Verificar si el servidor está disponible
                    if (hasattr(self.main_window, 'server_manager') and 
                        self.main_window.server_manager and 
                        hasattr(self.main_window.server_manager, 'server_process') and
                        self.main_window.server_manager.server_process and 
                        self.main_window.server_manager.server_process.poll() is None):
                        
                        # Servidor disponible, conectar automáticamente
                        self.logger.info("Servidor detectado, conectando automáticamente...")
                        self.auto_connect_to_server()
                        break
                    else:
                        self.logger.debug("Servidor no disponible aún, verificando en 5 segundos...")
                    
                    time.sleep(5)  # Verificar cada 5 segundos
                    
                except Exception as e:
                    self.logger.error(f"Error en monitoreo automático: {e}")
                    time.sleep(10)  # Esperar más tiempo si hay error
            
            self.logger.info("Monitoreo automático de conexión finalizado")
        
        # Iniciar en un hilo separado
        auto_connect_thread = threading.Thread(target=auto_connect_loop, daemon=True)
        auto_connect_thread.start()
        self.logger.info("Hilo de monitoreo automático iniciado")
    
    def auto_connect_to_server(self):
        """Conectar automáticamente al servidor cuando esté disponible"""
        try:
            if self.is_connected:
                self.logger.info("Ya conectado, saltando conexión automática")
                return
            
            # Obtener el proceso del servidor
            server_process = self.main_window.server_manager.server_process
            if not server_process:
                self.logger.warning("server_process es None en auto_connect_to_server")
                return
                
            if server_process.poll() is not None:
                self.logger.warning(f"Proceso del servidor terminado con código: {server_process.poll()}")
                return
            
            self.logger.info("Proceso del servidor encontrado, intentando conexión...")
            
            # Intentar conectar enviando un comando de prueba
            try:
                # Verificar que stdin esté disponible
                if not hasattr(server_process, 'stdin') or server_process.stdin is None:
                    self.logger.error("stdin no disponible en el proceso del servidor")
                    self.logger.info("Intentando reiniciar servidor con stdin habilitado...")
                    self.parent.after(0, self.restart_server_with_stdin)
                    return
                
                # Enviar comando de prueba
                self.logger.info("Enviando comando de prueba 'time'...")
                server_process.stdin.write("time\n")
                server_process.stdin.flush()
                
                # Marcar como conectado
                self.is_connected = True
                self.server_process = server_process
                
                self.logger.info("Conexión automática exitosa, estableciendo proceso en ScheduledCommandsManager...")
                
                # Conectar el programador de comandos
                self.scheduled_manager.set_server_process(server_process)
                self.scheduled_manager.start_scheduler()
                
                self.logger.info("Actualizando UI...")
                
                # Actualizar interfaz en el hilo principal
                self._safe_schedule_ui_update(self._update_ui_after_auto_connect)
                
                # Iniciar monitoreo automáticamente en el hilo principal
                self._safe_schedule_ui_update(self.start_monitoring)
                
            except Exception as e:
                self.logger.error(f"Error al enviar comando de prueba: {e}")
                self.logger.info("Reintentando conexión en 10 segundos...")
                # Reintentar después de un delay
                self._safe_schedule_ui_update(self.auto_connect_to_server, 10000)
                
        except Exception as e:
            self.logger.error(f"Error general en conexión automática: {e}")
    
    def _update_ui_after_auto_connect(self):
        """Actualizar la interfaz después de la conexión automática (llamado en hilo principal)"""
        try:
            # Conectar el programador de comandos
            self.scheduled_manager.set_server_process(self.server_process)
            self.scheduled_manager.start_scheduler()
            
            # Actualizar interfaz
            self.status_label.configure(text="✅ Conectado", fg_color="green")
            self.scheduler_status_label.configure(text="▶️ Programador: Activo", fg_color="green")
            self.connect_button.configure(state="disabled")
            self.disconnect_button.configure(state="normal")
            
            self.add_result("🔌 Conexión Automática", "Conectado automáticamente al servidor")
            self.add_result("⏰ Programador", "Sistema de comandos programados iniciado")
            
        except Exception as e:
            self.logger.error(f"Error al actualizar UI después de conexión automática: {e}")
    
    def start_stdout_monitoring(self):
        """Iniciar monitoreo directo del stdout del servidor"""
        if self.stdout_monitoring_thread and self.stdout_monitoring_thread.is_alive():
            return
            
        self.stop_stdout_monitoring_flag = False
        self.stdout_monitoring_thread = threading.Thread(target=self._stdout_monitoring_loop, daemon=True)
        self.stdout_monitoring_thread.start()
        self.logger.info("Monitoreo directo del stdout del servidor iniciado")
    
    def stop_stdout_monitoring(self):
        """Detener monitoreo directo del stdout del servidor"""
        self.stop_stdout_monitoring_flag = True
        if self.stdout_monitoring_thread:
            self.stdout_monitoring_thread.join(timeout=1)
        self.logger.info("Monitoreo directo del stdout del servidor detenido")
    
    def _stdout_monitoring_loop(self):
        """Bucle de monitoreo directo del stdout del servidor"""
        self.logger.info("Bucle de monitoreo del stdout iniciado")
        while not self.stop_stdout_monitoring_flag and self.is_connected:
            try:
                if self.server_process and self.server_process.poll() is None:
                    # Leer del stdout del servidor
                    self._read_server_stdout()
                else:
                    self.logger.warning("Proceso del servidor no disponible")
                    break
                
                time.sleep(0.1)  # Verificar cada 100ms para respuestas rápidas
                
            except Exception as e:
                self.logger.error(f"Error en monitoreo del stdout: {e}")
                time.sleep(1)  # Esperar más tiempo si hay error
        
        self.logger.info("Bucle de monitoreo del stdout finalizado")
    
    def _read_server_stdout(self):
        """Leer respuesta del stdout del servidor"""
        try:
            if not hasattr(self.server_process, 'stdout') or self.server_process.stdout is None:
                return
            
            # Intentar leer del stdout
            import select
            if hasattr(select, 'select'):
                # En Windows, usar select si está disponible
                ready, _, _ = select.select([self.server_process.stdout], [], [], 0.1)
                if ready:
                    line = self.server_process.stdout.readline()
                    if line:
                        line = line.decode('utf-8', errors='ignore').strip()
                        if line and self._is_command_response(line):
                            self.parent.after(0, lambda l=line: self._add_server_response(l))
                            self.logger.info(f"Respuesta del servidor capturada: {line}")
            
        except Exception as e:
            # Si select falla, intentar lectura directa
            try:
                if self.server_process.stdout.readable():
                    line = self.server_process.stdout.readline()
                    if line:
                        line = line.decode('utf-8', errors='ignore').strip()
                        if line and self._is_command_response(line):
                            self.parent.after(0, lambda l=line: self._add_server_response(l))
                            self.logger.info(f"Respuesta del servidor capturada: {line}")
            except Exception as e2:
                self.logger.debug(f"No se pudo leer stdout: {e2}")
                
        except Exception as e:
            self.logger.debug(f"Error en lectura de stdout: {e}")
    
    def _get_server_log_file(self):
        """Obtener la ruta del archivo de log del servidor"""
        try:
            if not self.main_window.server_manager:
                self.logger.info("server_manager no disponible")
                return None
            
            # Obtener el servidor seleccionado del MainWindow
            selected_server = getattr(self.main_window, 'selected_server', None)
            if not selected_server:
                self.logger.info("No hay servidor seleccionado en MainWindow")
                return None
            
            self.logger.info(f"Servidor seleccionado: {selected_server}")
            
            # Obtener la ruta del servidor desde el server_manager
            server_path = self.main_window.server_manager.get_server_path(selected_server)
            if not server_path:
                self.logger.info("No se pudo obtener server_path")
                return None
            
            self.logger.info(f"Server path obtenido: {server_path}")
            
            # Construir la ruta del archivo de log
            log_dir = os.path.join(server_path, "ShooterGame", "Saved", "Logs")
            if not os.path.exists(log_dir):
                self.logger.info(f"Directorio de logs no existe: {log_dir}")
                return None
            
            self.logger.info(f"Directorio de logs encontrado: {log_dir}")
            
            # Buscar el archivo de log más reciente
            log_files = [f for f in os.listdir(log_dir) if f.startswith("ShooterGame") and f.endswith(".log")]
            if not log_files:
                self.logger.info("No se encontraron archivos de log ShooterGame")
                return None
            
            self.logger.info(f"Archivos de log encontrados: {log_files}")
            
            # Obtener el archivo más reciente
            latest_log = max(log_files, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
            log_file_path = os.path.join(log_dir, latest_log)
            self.logger.info(f"Archivo de log más reciente: {log_file_path}")
            
            return log_file_path
            
        except Exception as e:
            self.logger.error(f"Error al obtener archivo de log: {e}")
            return None
    
    def _read_new_log_content(self, log_file):
        """Leer nuevo contenido del archivo de log"""
        try:
            # Si es un archivo nuevo, resetear la posición
            if log_file != self.current_log_file:
                self.current_log_file = log_file
                self.last_log_position = 0
                self.logger.info(f"Nuevo archivo de log detectado: {log_file}")
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                # Ir al final del archivo
                f.seek(0, 2)
                current_size = f.tell()
                
                # Si el archivo se ha truncado o es nuevo, resetear posición
                if current_size < self.last_log_position:
                    self.last_log_position = 0
                    self.logger.info("Archivo de log truncado, reseteando posición")
                
                # Leer solo el contenido nuevo
                if current_size > self.last_log_position:
                    f.seek(self.last_log_position, 0)
                    new_content = f.read()
                    
                    if new_content.strip():
                        self.logger.info(f"Leyendo {len(new_content)} bytes de contenido nuevo")
                        
                        # Filtrar solo líneas que parezcan respuestas a comandos
                        lines = new_content.split('\n')
                        filtered_lines = 0
                        for line in lines:
                            line = line.strip()
                            if line:
                                if self.debug_mode or self._is_command_response(line):
                                    # En modo debug, mostrar todas las líneas
                                    if self.debug_mode:
                                        self.parent.after(0, lambda l=line: self._add_server_response(f"[DEBUG] {l}"))
                                    else:
                                        # Mostrar en la interfaz en el hilo principal
                                        self.parent.after(0, lambda l=line: self._add_server_response(l))
                                    filtered_lines += 1
                                else:
                                    # Log de líneas filtradas para depuración
                                    self.logger.debug(f"Línea filtrada: {line[:100]}...")
                        
                        self.logger.info(f"Procesadas {len(lines)} líneas, {filtered_lines} mostradas")
                    else:
                        self.logger.debug("No hay contenido nuevo para procesar")
                    
                    self.last_log_position = current_size
                else:
                    self.logger.debug("No hay contenido nuevo en el archivo de log")
                    
        except Exception as e:
            self.logger.error(f"Error al leer archivo de log: {e}")
    
    def _is_command_response(self, line):
        """Verificar si una línea es una respuesta a un comando"""
        # Filtrar líneas que parezcan respuestas del servidor
        # Excluir líneas de debug, warnings, etc.
        if not line or len(line) < 3:
            return False
            
        # Excluir líneas que sean claramente de debug o warnings
        debug_patterns = [
            'log:', 'warning:', 'error:', 'debug:', 'trace:', 'verbose:',
            'shootergame', 'ue4', 'unreal', 'engine', 'garbage collection',
            'memory', 'performance', 'fps', 'tick', 'garbage', 'gc'
        ]
        
        line_lower = line.lower()
        if any(pattern in line_lower for pattern in debug_patterns):
            return False
            
        # Incluir líneas que parezcan respuestas a comandos
        command_responses = [
            'players online:', 'online players:', 'player list:', 'time:', 'weather:',
            'world saved', 'server restarting', 'broadcast:', 'admin command:',
            'player', 'players', 'online', 'time', 'weather', 'world', 'server',
            'broadcast', 'admin', 'command', 'list', 'info', 'status', 'saved',
            'restarting', 'restart', 'shutdown', 'exit', 'stopping', 'stopped'
        ]
        
        # Permitir líneas con timestamps (formato [HH:MM:SS])
        if line.startswith('[') and ']' in line:
            # Verificar si es un timestamp válido
            timestamp_part = line[1:line.find(']')]
            if ':' in timestamp_part and len(timestamp_part.split(':')) == 3:
                # Es un timestamp, verificar si el resto de la línea contiene información útil
                content_after_timestamp = line[line.find(']')+1:].strip()
                if content_after_timestamp and len(content_after_timestamp) > 3:
                    # Excluir solo líneas muy específicas de debug
                    if not any(pattern in content_after_timestamp.lower() for pattern in debug_patterns):
                        return True
        
        # Verificar si contiene respuestas de comandos
        if any(response in line_lower for response in command_responses):
            return True
            
        # Incluir líneas que parezcan respuestas de comandos específicos
        if any(keyword in line_lower for keyword in ['list', 'players', 'time', 'weather', 'broadcast', 'save']):
            return True
            
        return False
    
    def _add_server_response(self, response):
        """Agregar respuesta del servidor al área de resultados"""
        try:
            self.add_result("📥 Respuesta del Servidor", response)
        except Exception as e:
            self.logger.error(f"Error al agregar respuesta del servidor: {e}")
    
    def reload_log_content(self):
        """Recargar contenido del servidor (ahora lee del stdout)"""
        try:
            if not self.is_connected:
                self.show_error("Debes conectarte al servidor primero")
                return
            
            self.add_result("🔄 Recarga", "Solicitando información del servidor...")
            
            # Enviar comandos de prueba para obtener respuestas
            test_commands = ["time", "listplayers", "showworldinfo"]
            
            for cmd in test_commands:
                try:
                    self.server_process.stdin.write(f"{cmd}\n")
                    self.server_process.stdin.flush()
                    self.logger.info(f"Comando de prueba enviado: {cmd}")
                    time.sleep(0.5)  # Pequeña pausa entre comandos
                except Exception as e:
                    self.logger.error(f"Error al enviar comando {cmd}: {e}")
            
            self.add_result("📊 Recarga Completada", f"Enviados {len(test_commands)} comandos de prueba. Las respuestas aparecerán automáticamente si están disponibles.")
                
        except Exception as e:
            self.logger.error(f"Error al recargar contenido: {e}")
            self.show_error(f"Error al recargar: {e}")
    
    def toggle_debug_mode(self):
        """Alternar modo debug para ver todas las líneas del log"""
        self.debug_mode = not self.debug_mode
        
        if self.debug_mode:
            self.debug_button.configure(text="🐛 Debug ON", fg_color="red")
            self.add_result("🐛 Debug", "Modo debug activado - Mostrando todas las líneas del log")
        else:
            self.debug_button.configure(text="🐛 Modo Debug", fg_color="orange")
            self.add_result("🐛 Debug", "Modo debug desactivado - Solo mostrando respuestas relevantes")
    
    # Métodos para comandos programados
    def show_add_task_dialog(self):
        """Mostrar diálogo para agregar nueva tarea programada"""
        dialog = AddTaskDialog(self, self.scheduled_manager)
        dialog.grab_set()
        
    def show_tasks_list(self):
        """Mostrar lista de tareas programadas"""
        dialog = TasksListDialog(self, self.scheduled_manager)
        dialog.grab_set()
        
    def show_command_history(self):
        """Mostrar historial de comandos ejecutados"""
        dialog = CommandHistoryDialog(self, self.scheduled_manager)
        dialog.grab_set()
    
    def _on_command_executed(self, command, success, result):
        """Callback cuando se ejecuta un comando programado"""
        status = "✅" if success else "❌"
        self.add_result(f"{status} Comando Programado", f"{command}: {result}")
        
    def _on_command_failed(self, command, error):
        """Callback cuando falla un comando programado"""
        self.add_result("❌ Error Programado", f"{command}: {error}")
        self.show_error(f"Error en comando programado: {error}")
    
    def restart_server_with_stdin(self):
        """Reiniciar el servidor con stdin habilitado para comandos programados"""
        try:
            self.add_result("🔄 Reinicio", "Reiniciando servidor con soporte para comandos programados...")
            
            # Desconectar primero si está conectado
            if self.is_connected:
                self.disconnect_from_server()
            
            # Detener el servidor actual
            if (hasattr(self.main_window, 'server_manager') and 
                self.main_window.server_manager and 
                self.main_window.server_manager.server_process):
                
                self.main_window.server_manager.stop_server()
                self.add_result("⏹️ Deteniendo", "Servidor detenido")
                
                # Esperar un momento para que el servidor se detenga completamente
                time.sleep(3)
            
            # Obtener configuración actual
            server_name = getattr(self.main_window, 'selected_server', None)
            map_name = getattr(self.main_window, 'selected_map', None)
            
            # Reiniciar el servidor con force_stdin=True
            def restart_callback(status, message):
                if status == "started":
                    self.add_result("✅ Iniciado", "Servidor reiniciado con soporte para comandos programados")
                    # Intentar conectar automáticamente después de un momento
                    self._safe_schedule_ui_update(self.connect_to_server, 5000)
                elif status == "error":
                    self.add_result("❌ Error", f"Error al reiniciar servidor: {message}")
                    self.show_error(f"Error al reiniciar servidor: {message}")
            
            # Usar el método start_server con force_stdin=True
            self.main_window.server_manager.start_server(
                callback=restart_callback,
                server_name=server_name,
                map_name=map_name,
                capture_console=False,
                force_stdin=True
            )
            
            self.add_result("🚀 Iniciando", "Servidor iniciándose con soporte para comandos programados...")
            
        except Exception as e:
            self.logger.error(f"Error al reiniciar servidor con stdin: {e}")
            self.show_error(f"Error al reiniciar servidor: {e}")
            self.add_result("❌ Error", f"Error al reiniciar servidor: {e}")
