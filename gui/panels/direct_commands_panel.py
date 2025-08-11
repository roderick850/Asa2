import customtkinter as ctk
import subprocess
import threading
import time
import os
from datetime import datetime

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
        
        # Empaquetar el frame principal
        self.pack(fill="both", expand=True)
        
        # Crear widgets
        self.create_widgets()
        
        # Cargar configuración
        self.load_config()
        
        # Iniciar monitoreo automático para conectar cuando el servidor esté disponible
        self.start_auto_connect_monitoring()
        
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
                return
            
            # Intentar conectar enviando un comando de prueba
            try:
                # Enviar comando de prueba
                server_process.stdin.write("time\n".encode())
                server_process.stdin.flush()
                
                # Marcar como conectado
                self.is_connected = True
                self.server_process = server_process
                
                # Actualizar interfaz
                self.status_label.configure(text="✅ Conectado", fg_color="green")
                self.connect_button.configure(state="disabled")
                self.disconnect_button.configure(state="normal")
                
                self.show_success("✅ Conectado exitosamente al servidor")
                self.add_result("🔌 Conexión", "Conectado al servidor de Ark")
                
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
            
            # Limpiar estado
            self.is_connected = False
            self.server_process = None
            
            # Actualizar interfaz
            self.status_label.configure(text="❌ Desconectado", fg_color="red")
            self.connect_button.configure(state="normal")
            self.disconnect_button.configure(state="disabled")
            
            self.show_success("✅ Desconectado del servidor")
            self.add_result("🔌 Conexión", "Desconectado del servidor")
            
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
            self.server_process.stdin.write(f"{command}\n".encode())
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
        
        self.monitor_button.configure(text="⏹️ Detener Monitoreo", fg_color="red")
        self.add_result("📡 Monitoreo", "Monitoreo en tiempo real iniciado")
    
    def stop_monitoring_thread(self):
        """Detener monitoreo en tiempo real"""
        self.stop_monitoring = True
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
        
        self.monitor_button.configure(text="📡 Iniciar Monitoreo", fg_color="green")
        self.add_result("📡 Monitoreo", "Monitoreo en tiempo real detenido")
    
    def _monitoring_loop(self):
        """Bucle de monitoreo en tiempo real"""
        while not self.stop_monitoring and self.is_connected:
            try:
                # Enviar comando de estado cada 30 segundos
                if self.server_process and self.server_process.poll() is None:
                    self.server_process.stdin.write("time\n".encode())
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
            self.server_process.stdin.write("showworldinfo\n".encode())
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
                    
                    time.sleep(5)  # Verificar cada 5 segundos
                    
                except Exception as e:
                    self.logger.error(f"Error en monitoreo automático: {e}")
                    time.sleep(10)  # Esperar más tiempo si hay error
        
        # Iniciar en un hilo separado
        auto_connect_thread = threading.Thread(target=auto_connect_loop, daemon=True)
        auto_connect_thread.start()
    
    def auto_connect_to_server(self):
        """Conectar automáticamente al servidor cuando esté disponible"""
        try:
            if self.is_connected:
                return
            
            # Obtener el proceso del servidor
            server_process = self.main_window.server_manager.server_process
            if not server_process or server_process.poll() is not None:
                return
            
            # Intentar conectar enviando un comando de prueba
            try:
                # Enviar comando de prueba
                server_process.stdin.write("time\n".encode())
                server_process.stdin.flush()
                
                # Marcar como conectado
                self.is_connected = True
                self.server_process = server_process
                
                # Actualizar interfaz
                self.status_label.configure(text="✅ Conectado", fg_color="green")
                self.connect_button.configure(state="disabled")
                self.disconnect_button.configure(state="normal")
                
                self.add_result("🔌 Conexión Automática", "Conectado automáticamente al servidor")
                
                # Iniciar monitoreo automáticamente
                self.start_monitoring()
                
            except Exception as e:
                self.logger.error(f"Error en conexión automática: {e}")
                
        except Exception as e:
            self.logger.error(f"Error en conexión automática: {e}")
