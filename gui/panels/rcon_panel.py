import customtkinter as ctk
import subprocess
import threading
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import schedule
import time


class RconPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger, main_window=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        
        # Variables de configuración RCON
        self.rcon_ip = "127.0.0.1"
        self.rcon_port = "27020"
        self.rcon_password = ""
        
        # Variables del estado
        self.is_connected = False
        self.command_history = []
        
        # Variables para programación de tareas
        self.scheduled_tasks = []
        self.scheduler_running = False
        self.scheduler_thread = None
        
        # Variables para tareas rápidas personalizables
        self.quick_tasks = []
        self.quick_tasks_file = "config/quick_rcon_tasks.json"
        
        # Cargar tareas programadas y rápidas
        self.load_scheduled_tasks()
        self.load_quick_tasks_config()
        
        # Empaquetar el frame principal
        self.pack(fill="both", expand=True)
        
        self.create_widgets()
        
        # Cargar configuración después de un pequeño retraso para asegurar que los widgets estén listos
        self.after(100, self.load_rcon_config)
        
    def create_widgets(self):
        """Crear todos los widgets del panel RCON"""
        # Crear un frame scrollable principal
        self.main_scrollable_frame = ctk.CTkScrollableFrame(self)
        self.main_scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configurar el grid del frame scrollable
        self.main_scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # === CONFIGURACIÓN RCON ===
        config_frame = ctk.CTkFrame(self.main_scrollable_frame)
        config_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        config_frame.grid_columnconfigure((1, 3, 5), weight=1)
        
        # Título de configuración
        config_title = ctk.CTkLabel(config_frame, text="🔧 Configuración RCON", 
                                   font=ctk.CTkFont(size=14, weight="bold"))
        config_title.grid(row=0, column=0, columnspan=6, pady=(10, 5))
        
        # IP
        ctk.CTkLabel(config_frame, text="IP:").grid(row=1, column=0, padx=(10, 5), pady=5, sticky="w")
        self.ip_entry = ctk.CTkEntry(config_frame, width=120)
        self.ip_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Puerto
        ctk.CTkLabel(config_frame, text="Puerto:").grid(row=1, column=2, padx=(10, 5), pady=5, sticky="w")
        self.port_entry = ctk.CTkEntry(config_frame, width=80)
        self.port_entry.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        
        # Información del password (automático)
        ctk.CTkLabel(config_frame, text="Password:").grid(row=1, column=4, padx=(10, 5), pady=5, sticky="w")
        self.password_info = ctk.CTkLabel(config_frame, text="🔗 Automático (AdminPassword)", 
                                         font=ctk.CTkFont(size=10),
                                         fg_color=("lightblue", "darkblue"),
                                         corner_radius=3, padx=6, pady=2)
        self.password_info.grid(row=1, column=5, padx=(5, 10), pady=5, sticky="ew")
        
        # Switch para RCON Enable
        rcon_enable_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        rcon_enable_frame.grid(row=2, column=0, columnspan=6, pady=5, sticky="ew")
        
        ctk.CTkLabel(rcon_enable_frame, text="🔧 RCON en Argumentos de Inicio:", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(10, 10))
        
        self.rcon_enable_switch = ctk.CTkSwitch(
            rcon_enable_frame,
            text=f"Agregar ?RCONEnabled=True?RCONPort={self.rcon_port}",
            command=self.on_rcon_switch_change
        )
        self.rcon_enable_switch.pack(side="left", padx=10)
        
        # Opción para elegir tipo de mensaje
        message_type_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        message_type_frame.grid(row=3, column=0, columnspan=6, pady=5, sticky="ew")
        
        ctk.CTkLabel(message_type_frame, text="📢 Tipo de Mensaje:", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(10, 10))
        
        self.message_type_var = ctk.StringVar(value="serverchat")
        self.message_type_menu = ctk.CTkOptionMenu(
            message_type_frame,
            values=["serverchat", "broadcast"],
            variable=self.message_type_var,
            command=self.on_message_type_change
        )
        self.message_type_menu.pack(side="left", padx=10)
        
        # Información sobre el tipo de mensaje seleccionado
        self.message_type_info = ctk.CTkLabel(
            message_type_frame, 
            text="✅ Recomendado para ASA (funciona correctamente)", 
            font=ctk.CTkFont(size=10),
            fg_color=("lightgreen", "darkgreen"),
            corner_radius=3, padx=6, pady=2
        )
        self.message_type_info.pack(side="left", padx=(10, 5))
        
        # Botones de configuración
        config_buttons_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        config_buttons_frame.grid(row=4, column=0, columnspan=6, pady=5)
        
        self.test_button = ctk.CTkButton(config_buttons_frame, text="🔍 Probar Conexión", 
                                        command=self.test_connection, width=120)
        self.test_button.pack(side="left", padx=5)
        
        self.save_config_button = ctk.CTkButton(config_buttons_frame, text="💾 Guardar Config", 
                                               command=self.save_rcon_config, width=120)
        self.save_config_button.pack(side="left", padx=5)
        
        # Indicador de estado
        self.status_label = ctk.CTkLabel(config_buttons_frame, text="❌ Desconectado", 
                                        fg_color=("lightcoral", "darkred"), corner_radius=5, 
                                        padx=10, pady=3)
        self.status_label.pack(side="left", padx=(20, 5))
        
        # === COMANDOS RÁPIDOS ===
        commands_frame = ctk.CTkFrame(self.main_scrollable_frame)
        commands_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        commands_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Título de comandos
        commands_title = ctk.CTkLabel(commands_frame, text="⚡ Comandos Rápidos", 
                                     font=ctk.CTkFont(size=14, weight="bold"))
        commands_title.grid(row=0, column=0, columnspan=4, pady=(10, 5))
        
        # Fila 1 de comandos
        self.list_players_btn = ctk.CTkButton(commands_frame, text="👥 Lista Jugadores", 
                                             command=lambda: self.execute_command("listPlayers"), 
                                             height=35)
        self.list_players_btn.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.save_world_btn = ctk.CTkButton(commands_frame, text="💾 Guardar Mundo", 
                                           command=lambda: self.execute_command("saveworld"), 
                                           height=35)
        self.save_world_btn.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.server_info_btn = ctk.CTkButton(commands_frame, text="ℹ️ Info Servidor", 
                                            command=lambda: self.execute_command("GetServerInfo"), 
                                            height=35)
        self.server_info_btn.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        
        self.broadcast_btn = ctk.CTkButton(commands_frame, text="📢 Anuncio", 
                                          command=self.show_broadcast_dialog, 
                                          height=35)
        self.broadcast_btn.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        
        # Fila 2 de comandos
        self.kick_player_btn = ctk.CTkButton(commands_frame, text="🚪 Kickear Jugador", 
                                            command=self.show_kick_dialog, 
                                            height=35)
        self.kick_player_btn.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        
        self.ban_player_btn = ctk.CTkButton(commands_frame, text="🔨 Banear Jugador", 
                                           command=self.show_ban_dialog, 
                                           height=35)
        self.ban_player_btn.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        self.shutdown_btn = ctk.CTkButton(commands_frame, text="🛑 Apagar Servidor", 
                                         command=self.show_shutdown_dialog, 
                                         height=35, 
                                         fg_color=("red", "darkred"))
        self.shutdown_btn.grid(row=2, column=2, padx=5, pady=5, sticky="ew")
        
        self.restart_btn = ctk.CTkButton(commands_frame, text="🔄 Reiniciar", 
                                        command=self.show_restart_dialog, 
                                        height=35,
                                        fg_color=("orange", "darkorange"))
        self.restart_btn.grid(row=2, column=3, padx=5, pady=(5, 10), sticky="ew")
        
        # === COMANDO PERSONALIZADO ===
        custom_frame = ctk.CTkFrame(self.main_scrollable_frame)
        custom_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        custom_frame.grid_columnconfigure(1, weight=1)
        
        # Título comando personalizado
        custom_title = ctk.CTkLabel(custom_frame, text="⌨️ Comando Personalizado", 
                                   font=ctk.CTkFont(size=14, weight="bold"))
        custom_title.grid(row=0, column=0, columnspan=3, pady=(10, 5))
        
        # Campo de comando
        ctk.CTkLabel(custom_frame, text="Comando:").grid(row=1, column=0, padx=(10, 5), pady=5, sticky="w")
        self.custom_command_entry = ctk.CTkEntry(custom_frame, placeholder_text="Ej: GetGameLog")
        self.custom_command_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.custom_command_entry.bind("<Return>", lambda e: self.execute_custom_command())
        
        self.execute_custom_btn = ctk.CTkButton(custom_frame, text="▶️ Ejecutar", 
                                               command=self.execute_custom_command, 
                                               width=80)
        self.execute_custom_btn.grid(row=1, column=2, padx=(5, 10), pady=5)
        
        # === ÁREA DE RESULTADOS ===
        results_frame = ctk.CTkFrame(self.main_scrollable_frame)
        results_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)
        
        # Título de resultados
        results_title = ctk.CTkLabel(results_frame, text="📋 Resultados de Comandos", 
                                    font=ctk.CTkFont(size=14, weight="bold"))
        results_title.grid(row=0, column=0, pady=(10, 5))
        
        # Área de texto para resultados
        self.results_text = ctk.CTkTextbox(results_frame, state="disabled", wrap="word")
        self.results_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        # Frame de botones de resultados
        results_buttons_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        results_buttons_frame.grid(row=2, column=0, pady=(0, 10))
        
        self.clear_results_btn = ctk.CTkButton(results_buttons_frame, text="🧹 Limpiar", 
                                              command=self.clear_results, width=80)
        self.clear_results_btn.pack(side="left", padx=5)
        
        self.export_results_btn = ctk.CTkButton(results_buttons_frame, text="💾 Exportar", 
                                               command=self.export_results, width=80)
        self.export_results_btn.pack(side="left", padx=5)
        
        # === PROGRAMACIÓN DE TAREAS ===
        self.create_scheduler_section()
        
        # === COMANDOS AVANZADOS ===
        self.create_advanced_commands_section()
        
        # === MONITOREO DEL SERVIDOR ===
        self.create_monitoring_section()
    
    def load_rcon_config(self):
        """Cargar configuración RCON guardada"""
        try:
            self.rcon_ip = self.config_manager.get("rcon", "ip", "127.0.0.1")
            self.rcon_port = self.config_manager.get("rcon", "port", "27020")
            
            self.logger.info(f"Cargando configuración RCON - IP: {self.rcon_ip}, Puerto: {self.rcon_port}")
            
            # Actualizar campos de entrada
            self.ip_entry.delete(0, "end")
            self.ip_entry.insert(0, self.rcon_ip)
            
            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, self.rcon_port)
            
            # Actualizar información del password
            self.update_password_info()
            
            # Cargar estado del switch RCON
            rcon_enabled_str = self.config_manager.get("rcon", "enable_startup_args", "False")
            rcon_enabled = rcon_enabled_str in ["True", "1", "true"]
            
            self.logger.info(f"Cargando estado RCON switch - Valor en config: '{rcon_enabled_str}', Habilitado: {rcon_enabled}")
            
            if rcon_enabled:
                self.rcon_enable_switch.select()
                self.add_result("🔄 RCON habilitado desde configuración guardada")
            else:
                self.rcon_enable_switch.deselect()
                self.add_result("🔄 RCON deshabilitado desde configuración guardada")
            
            # Cargar tipo de mensaje si existe el widget
            if hasattr(self, 'message_type_option'):
                message_type = self.config_manager.get("rcon", "message_type", "serverchat")
                self.message_type_option.set(message_type)
                # Actualizar la información visual
                self.on_message_type_change(message_type)
            
        except Exception as e:
            self.logger.error(f"Error al cargar configuración RCON: {e}")
    
    def update_password_info(self):
        """Actualizar información del password desde AdminPassword"""
        try:
            admin_password = self.config_manager.get("server", "admin_password", "")
            if admin_password:
                self.password_info.configure(text=f"🔗 Configurado ({len(admin_password)} caracteres)")
                self.rcon_password = admin_password
            else:
                self.password_info.configure(text="⚠️ AdminPassword no configurado")
                self.rcon_password = ""
        except Exception as e:
            self.logger.error(f"Error al actualizar información del password: {e}")
            self.password_info.configure(text="❌ Error al obtener password")
    
    def refresh_password_from_config(self):
        """Método público para refrescar el password desde configuración (llamado desde main_window)"""
        self.update_password_info()
    
    def on_rcon_switch_change(self):
        """Callback cuando cambia el switch de RCON Enable"""
        try:
            rcon_enabled = self.rcon_enable_switch.get()
            
            self.logger.info(f"Cambiando estado RCON switch a: {rcon_enabled}")
            
            # Guardar estado del switch (normalizar a "True"/"False")
            rcon_value = "True" if rcon_enabled else "False"
            self.config_manager.set("rcon", "enable_startup_args", rcon_value)
            self.config_manager.save()
            
            self.logger.info(f"Estado RCON guardado en configuración: '{rcon_value}'")
            
            if rcon_enabled:
                self.add_result("✅ RCON habilitado - se agregará a argumentos de inicio")
                # Notificar al panel principal para refrescar argumentos
                if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'principal_panel'):
                    self.main_window.principal_panel.refresh_rcon_args()
            else:
                self.add_result("❌ RCON deshabilitado - se removerá de argumentos de inicio")
                
        except Exception as e:
            self.logger.error(f"Error al cambiar estado RCON: {e}")
    
    def on_message_type_change(self, value):
        """Manejar cambio en el tipo de mensaje"""
        try:
            if value == "serverchat":
                self.message_type_info.configure(
                    text="✅ Recomendado para ASA (funciona correctamente)",
                    fg_color=("lightgreen", "darkgreen")
                )
            else:  # broadcast
                self.message_type_info.configure(
                    text="⚠️ Puede tener problemas en ASA (usar solo si funciona)",
                    fg_color=("orange", "darkorange")
                )
            
            # Guardar configuración automáticamente
            self.save_rcon_config()
            
            self.logger.info(f"Tipo de mensaje RCON cambiado a: {value}")
            
        except Exception as e:
            self.logger.error(f"Error al cambiar tipo de mensaje: {e}")
    
    def get_message_type(self):
        """Obtener el tipo de mensaje configurado"""
        try:
            if hasattr(self, 'message_type_option'):
                return self.message_type_option.get()
            else:
                return self.config_manager.get("rcon", "message_type", "serverchat")
        except:
            return "serverchat"  # Default seguro
    
    def get_rcon_enabled(self):
        """Obtener si RCON está habilitado para argumentos de inicio"""
        try:
            value = self.config_manager.get("rcon", "enable_startup_args", "False")
            return value in ["True", "1", "true"]
        except:
            return False
    
    def get_rcon_port(self):
        """Obtener puerto RCON configurado"""
        # Obtener el valor actual del campo, o usar el valor guardado como fallback
        try:
            if hasattr(self, 'port_entry') and self.port_entry.winfo_exists():
                current_port = self.port_entry.get()
                return current_port if current_port else self.rcon_port
            else:
                return self.rcon_port
        except:
            return self.rcon_port
    
    def get_rcon_status(self):
        """Obtener estado de RCON (si está habilitado)"""
        return self.get_rcon_enabled()
    
    def save_rcon_config(self):
        """Guardar configuración RCON (sin password, se toma automáticamente)"""
        try:
            self.rcon_ip = self.ip_entry.get()
            self.rcon_port = self.port_entry.get()
            
            self.logger.info(f"Guardando configuración RCON - IP: {self.rcon_ip}, Puerto: {self.rcon_port}")
            
            self.config_manager.set("rcon", "ip", self.rcon_ip)
            self.config_manager.set("rcon", "port", self.rcon_port)
            
            # Guardar tipo de mensaje si existe el widget
            if hasattr(self, 'message_type_option'):
                message_type = self.message_type_option.get()
                self.config_manager.set("rcon", "message_type", message_type)
            
            self.config_manager.save()
            
            # Actualizar password desde AdminPassword
            self.update_password_info()
            
            self.add_result("✅ Configuración RCON guardada correctamente")
            self.add_result("💡 Password tomado automáticamente de AdminPassword")
            
        except Exception as e:
            self.logger.error(f"Error al guardar configuración RCON: {e}")
            self.add_result(f"❌ Error al guardar configuración: {e}")
    
    def test_connection(self):
        """Probar conexión RCON"""
        def _test():
            try:
                self.update_status("🔄 Probando conexión...", "orange")
                
                # Actualizar configuración actual
                self.rcon_ip = self.ip_entry.get()
                self.rcon_port = self.port_entry.get()
                
                # Obtener password desde AdminPassword
                self.update_password_info()
                
                # Intentar ejecutar un comando simple
                result = self.execute_rcon_command("GetServerInfo")
                
                if result and "error" not in result.lower():
                    self.is_connected = True
                    self.update_status("✅ Conectado", "green")
                    self.add_result("✅ Conexión RCON exitosa")
                else:
                    self.is_connected = False
                    self.update_status("❌ Error de conexión", "red")
                    self.add_result(f"❌ Error de conexión RCON: {result}")
                    
            except Exception as e:
                self.is_connected = False
                self.update_status("❌ Error de conexión", "red")
                self.add_result(f"❌ Error al probar conexión: {e}")
                self.logger.error(f"Error al probar conexión RCON: {e}")
        
        threading.Thread(target=_test, daemon=True).start()
    
    def execute_rcon_command(self, command):
        """Ejecutar comando RCON usando el ejecutable en la carpeta rcon"""
        # Log del intento de ejecución
        if hasattr(self, 'main_window') and hasattr(self.main_window, 'add_log_message') and hasattr(self.main_window, 'root'):
            self.main_window.root.after(0, lambda: self.main_window.add_log_message(f"🎮 RCON: Ejecutando '{command}'..."))
        
        try:
            # Buscar el ejecutable RCON en múltiples ubicaciones
            rcon_exe = None
            search_paths = [
                Path("rcon"),  # Carpeta rcon relativa
                Path(__file__).parent.parent.parent / "rcon",  # Carpeta rcon desde el script
                Path.cwd() / "rcon",  # Carpeta rcon desde directorio de trabajo
                Path(__file__).parent.parent.parent,  # Directorio raíz del proyecto
                Path.cwd(),  # Directorio actual
            ]
            
            for search_path in search_paths:
                if search_path.exists():
                    # Buscar archivos .exe en la carpeta
                    for file in search_path.glob("*.exe"):
                        if "rcon" in file.name.lower():
                            rcon_exe = file
                            break
                    if rcon_exe:
                        break
            
            if not rcon_exe:
                error_msg = "❌ No se encontró ejecutable RCON"
                search_info = "Buscado en: " + ", ".join([str(p) for p in search_paths])
                self.logger.error(f"RCON executable not found. {search_info}")
                if hasattr(self, 'main_window') and hasattr(self.main_window, 'add_log_message') and hasattr(self.main_window, 'root'):
                    self.main_window.root.after(0, lambda: self.main_window.add_log_message(f"🔌 RCON Error: No se encontró ejecutable RCON"))
                return error_msg
            
            # Construir comando
            cmd = [
                str(rcon_exe),
                "-a", f"{self.rcon_ip}:{self.rcon_port}",
                "-p", self.rcon_password,
                command
            ]
            
            self.logger.info(f"Ejecutando comando RCON: {' '.join(cmd[:-1])} [comando oculto]")
            
            # Ejecutar comando sin mostrar ventana de consola
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(rcon_exe.parent),  # Usar el directorio del ejecutable encontrado
                creationflags=subprocess.CREATE_NO_WINDOW  # Ocultar ventana DOS
            )
            
            if result.returncode == 0:
                # Registrar comando RCON exitoso
                success_msg = f"✅ RCON: '{command}' ejecutado correctamente"
                response = result.stdout.strip()
                if response:
                    success_msg += f" - Respuesta: {response[:50]}{'...' if len(response) > 50 else ''}"
                
                # Log en área principal
                if hasattr(self, 'main_window') and hasattr(self.main_window, 'add_log_message') and hasattr(self.main_window, 'root'):
                    self.main_window.root.after(0, lambda: self.main_window.add_log_message(success_msg))
                
                # Log en archivo
                if hasattr(self, 'main_window') and hasattr(self.main_window, 'log_server_event'):
                    self.main_window.log_server_event("rcon_command", 
                        command=command,
                        success=True,
                        result=result.stdout.strip()[:100])  # Limitar resultado a 100 chars
                
                return result.stdout.strip()
            else:
                error_msg = result.stderr.strip() if result.stderr else f"Código de salida: {result.returncode}"
                
                # Registrar comando RCON fallido
                fail_msg = f"❌ RCON: '{command}' falló - {error_msg}"
                
                # Log en área principal
                if hasattr(self, 'main_window') and hasattr(self.main_window, 'add_log_message') and hasattr(self.main_window, 'root'):
                    self.main_window.root.after(0, lambda: self.main_window.add_log_message(fail_msg))
                
                # Log en archivo
                if hasattr(self, 'main_window') and hasattr(self.main_window, 'log_server_event'):
                    self.main_window.log_server_event("rcon_command", 
                        command=command,
                        success=False,
                        result=error_msg)
                
                return f"❌ Error: {error_msg}"
                
        except subprocess.TimeoutExpired:
            timeout_msg = f"⏱️ RCON Timeout: '{command}' tardó demasiado en ejecutarse"
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'add_log_message') and hasattr(self.main_window, 'root'):
                self.main_window.root.after(0, lambda: self.main_window.add_log_message(timeout_msg))
            return "❌ Timeout: El comando tardó demasiado en ejecutarse"
        except Exception as e:
            self.logger.error(f"Error al ejecutar comando RCON: {e}")
            error_msg = f"🔌 RCON Error: '{command}' - Error de conexión: {str(e)}"
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'add_log_message') and hasattr(self.main_window, 'root'):
                self.main_window.root.after(0, lambda: self.main_window.add_log_message(error_msg))
            return f"❌ Error al ejecutar comando: {e}"
    
    def execute_command(self, command):
        """Ejecutar comando RCON específico"""
        def _execute():
            try:
                # Actualizar password antes de ejecutar comando
                self.update_password_info()
                
                self.add_result(f"▶️ Ejecutando: {command}")
                result = self.execute_rcon_command(command)
                
                if result:
                    self.add_result(f"📋 Resultado:\n{result}")
                    # Agregar a historial
                    self.command_history.append({"command": command, "result": result})
                else:
                    self.add_result("❌ No se recibió respuesta")
                    
            except Exception as e:
                self.add_result(f"❌ Error al ejecutar comando: {e}")
                self.logger.error(f"Error al ejecutar comando {command}: {e}")
        
        threading.Thread(target=_execute, daemon=True).start()
    
    def execute_custom_command(self):
        """Ejecutar comando personalizado"""
        command = self.custom_command_entry.get().strip()
        if command:
            self.execute_command(command)
            self.custom_command_entry.delete(0, "end")
    
    def show_broadcast_dialog(self):
        """Mostrar diálogo para enviar anuncio"""
        dialog = ctk.CTkInputDialog(text="Mensaje para anunciar:", title="Anuncio al Servidor")
        message = dialog.get_input()
        
        if message:
            message_type = self.get_message_type()
            self.execute_command(f'{message_type} "{message}"')
            self.add_result(f"📢 Mensaje enviado usando: {message_type}")
    
    def show_kick_dialog(self):
        """Mostrar diálogo para kickear jugador"""
        dialog = ctk.CTkInputDialog(text="ID o nombre del jugador:", title="Kickear Jugador")
        player = dialog.get_input()
        
        if player:
            self.execute_command(f'KickPlayer "{player}"')
    
    def show_ban_dialog(self):
        """Mostrar diálogo para banear jugador"""
        dialog = ctk.CTkInputDialog(text="ID o nombre del jugador:", title="Banear Jugador")
        player = dialog.get_input()
        
        if player:
            self.execute_command(f'BanPlayer "{player}"')
    
    def show_shutdown_dialog(self):
        """Mostrar diálogo para apagar servidor"""
        # Crear ventana de confirmación personalizada
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirmar Apagado")
        dialog.geometry("400x280")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrar ventana
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (280 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Contenido
        ctk.CTkLabel(dialog, text="⚠️ ¿Estás seguro de que quieres apagar el servidor?", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=20)
        
        ctk.CTkLabel(dialog, text="Tiempo de espera (segundos):").pack(pady=5)
        time_entry = ctk.CTkEntry(dialog, width=100)
        time_entry.insert(0, "30")
        time_entry.pack(pady=5)
        
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(pady=20)
        
        def confirm_shutdown():
            time_seconds = time_entry.get()
            dialog.destroy()
            self.execute_command(f"DoExit {time_seconds}")
        
        ctk.CTkButton(buttons_frame, text="✅ Confirmar", command=confirm_shutdown, 
                     fg_color="red").pack(side="left", padx=10)
        ctk.CTkButton(buttons_frame, text="❌ Cancelar", command=dialog.destroy).pack(side="left", padx=10)
    
    def show_restart_dialog(self):
        """Mostrar diálogo para reiniciar servidor"""
        # Crear ventana de confirmación personalizada
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirmar Reinicio")
        dialog.geometry("350x240")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrar ventana
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (dialog.winfo_screenheight() // 2) - (200 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Contenido
        ctk.CTkLabel(dialog, text="🔄 ¿Estás seguro de que quieres reiniciar el servidor?", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=20)
        
        ctk.CTkLabel(dialog, text="Tiempo de espera (segundos):").pack(pady=5)
        time_entry = ctk.CTkEntry(dialog, width=100)
        time_entry.insert(0, "30")
        time_entry.pack(pady=5)
        
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(pady=20)
        
        def confirm_restart():
            time_seconds = time_entry.get()
            dialog.destroy()
            # Primero guardar mundo, luego reiniciar
            self.execute_command("saveworld")
            self.execute_command(f"DoExit {time_seconds}")
        
        ctk.CTkButton(buttons_frame, text="✅ Confirmar", command=confirm_restart, 
                     fg_color="orange").pack(side="left", padx=10)
        ctk.CTkButton(buttons_frame, text="❌ Cancelar", command=dialog.destroy).pack(side="left", padx=10)
    
    def add_result(self, text):
        """Agregar resultado al área de texto"""
        try:
            self.results_text.configure(state="normal")
            
            # Agregar timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            self.results_text.insert("end", f"[{timestamp}] {text}\n")
            self.results_text.see("end")
            self.results_text.configure(state="disabled")
            
        except Exception as e:
            self.logger.error(f"Error al agregar resultado: {e}")
    
    def update_status(self, text, color):
        """Actualizar el estado de conexión"""
        try:
            color_map = {
                "green": ("lightgreen", "darkgreen"),
                "red": ("lightcoral", "darkred"),
                "orange": ("orange", "darkorange")
            }
            
            self.status_label.configure(text=text, fg_color=color_map.get(color, ("gray", "darkgray")))
            
        except Exception as e:
            self.logger.error(f"Error al actualizar estado: {e}")
    
    def clear_results(self):
        """Limpiar área de resultados"""
        try:
            self.results_text.configure(state="normal")
            self.results_text.delete("1.0", "end")
            self.results_text.configure(state="disabled")
            
        except Exception as e:
            self.logger.error(f"Error al limpiar resultados: {e}")
    
    def export_results(self):
        """Exportar resultados a archivo"""
        try:
            content = self.results_text.get("1.0", "end")
            if not content.strip():
                self.add_result("❌ No hay resultados para exportar")
                return
            
            # Crear carpeta de exportación
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)
            
            # Generar nombre de archivo
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = export_dir / f"rcon_results_{timestamp}.txt"
            
            # Guardar archivo
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.add_result(f"✅ Resultados exportados a: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error al exportar resultados: {e}")
            self.add_result(f"❌ Error al exportar: {e}")
    
    def create_scheduler_section(self):
        """Crear sección de programación de tareas"""
        scheduler_frame = ctk.CTkFrame(self.main_scrollable_frame)
        scheduler_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
        scheduler_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Título
        scheduler_title = ctk.CTkLabel(scheduler_frame, text="⏰ Programación de Tareas RCON", 
                                      font=ctk.CTkFont(size=14, weight="bold"))
        scheduler_title.grid(row=0, column=0, columnspan=4, pady=(10, 5))
        
        # Estado del programador
        status_frame = ctk.CTkFrame(scheduler_frame, fg_color="transparent")
        status_frame.grid(row=1, column=0, columnspan=4, pady=5, sticky="ew")
        
        self.scheduler_status_label = ctk.CTkLabel(status_frame, text="⏸️ Programador: Detenido", 
                                                  fg_color=("lightcoral", "darkred"), 
                                                  corner_radius=5, padx=10, pady=3)
        self.scheduler_status_label.pack(side="left", padx=10)
        
        self.start_scheduler_btn = ctk.CTkButton(status_frame, text="▶️ Iniciar", 
                                                command=self.start_scheduler, width=80)
        self.start_scheduler_btn.pack(side="left", padx=5)
        
        self.stop_scheduler_btn = ctk.CTkButton(status_frame, text="⏹️ Detener", 
                                               command=self.stop_scheduler, width=80)
        self.stop_scheduler_btn.pack(side="left", padx=5)
        
        # Formulario para nueva tarea
        form_frame = ctk.CTkFrame(scheduler_frame)
        form_frame.grid(row=2, column=0, columnspan=4, pady=5, padx=10, sticky="ew")
        form_frame.grid_columnconfigure((1, 3), weight=1)
        
        ctk.CTkLabel(form_frame, text="Nueva Tarea Programada:", 
                    font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, columnspan=4, pady=5)
        
        # Comando
        ctk.CTkLabel(form_frame, text="Comando:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.task_command_entry = ctk.CTkEntry(form_frame, placeholder_text="Ej: saveworld")
        self.task_command_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Tipo de programación
        ctk.CTkLabel(form_frame, text="Tipo:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.task_type_var = ctk.StringVar(value="Cada 5 minutos")
        self.task_type_combo = ctk.CTkComboBox(form_frame, 
                                              values=["Cada 5 minutos", "Cada 15 minutos", "Cada 30 minutos", "Cada hora", "Cada 6 horas", "Diario"],
                                              variable=self.task_type_var,
                                              width=120)
        self.task_type_combo.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        self.task_type_combo.bind("<<ComboboxSelected>>", self.on_task_type_change)
        
        # Configuración de tiempo
        self.time_config_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.time_config_frame.grid(row=2, column=0, columnspan=4, pady=5, sticky="ew")
        
        # Descripción
        ctk.CTkLabel(form_frame, text="Descripción:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.task_description_entry = ctk.CTkEntry(form_frame, placeholder_text="Descripción opcional")
        self.task_description_entry.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Botón agregar
        self.add_task_btn = ctk.CTkButton(form_frame, text="➕ Agregar Tarea", 
                                         command=self.add_scheduled_task, width=120)
        self.add_task_btn.grid(row=3, column=3, padx=5, pady=5)
        
        # Separador
        separator = ctk.CTkFrame(scheduler_frame, height=2)
        separator.grid(row=3, column=0, columnspan=4, pady=20, padx=10, sticky="ew")
        
        # Sistema unificado de tareas RCON
        unified_tasks_frame = ctk.CTkFrame(scheduler_frame)
        unified_tasks_frame.grid(row=4, column=0, columnspan=4, pady=10, padx=10, sticky="ew")
        unified_tasks_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(unified_tasks_frame, text="⚡ Gestión de Tareas RCON", 
                    font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=10)
        
        # Frame para botones de tareas rápidas existentes
        self.quick_tasks_frame = ctk.CTkFrame(unified_tasks_frame)
        self.quick_tasks_frame.grid(row=1, column=0, pady=10, padx=10, sticky="ew")
        
        # Formulario unificado de tareas
        task_form_frame = ctk.CTkFrame(unified_tasks_frame)
        task_form_frame.grid(row=2, column=0, pady=10, padx=10, sticky="ew")
        task_form_frame.grid_columnconfigure(1, weight=1)
        
        # Tipo de tarea
        ctk.CTkLabel(task_form_frame, text="Tipo de Tarea:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.task_type = ctk.CTkOptionMenu(task_form_frame, values=["Ejecutar Ahora", "Programar", "Tarea Rápida"])
        self.task_type.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.task_type.set("Ejecutar Ahora")
        self.task_type.configure(command=lambda value: self.on_task_type_change(value))
        
        # Tipo de comando
        ctk.CTkLabel(task_form_frame, text="Comando:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.unified_command_type = ctk.CTkOptionMenu(task_form_frame, values=[
            "broadcast", "serverchat", "saveworld", "listplayers", "kick", "ban", 
            "unban", "admincheat", "destroywilddinos", "time", "weather", "custom"
        ])
        self.unified_command_type.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.unified_command_type.set("broadcast")
        
        # Parámetros del comando
        ctk.CTkLabel(task_form_frame, text="Parámetros:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.unified_command_params = ctk.CTkEntry(task_form_frame, placeholder_text="Parámetros del comando")
        self.unified_command_params.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        # Frame para opciones específicas (se muestra según el tipo)
        self.options_frame = ctk.CTkFrame(task_form_frame)
        self.options_frame.grid(row=3, column=0, columnspan=2, pady=10, padx=5, sticky="ew")
        self.options_frame.grid_columnconfigure(1, weight=1)
        self.options_frame.grid_columnconfigure(3, weight=1)
        
        # Opciones para tareas programadas (inicialmente ocultas)
        self.schedule_widgets = []
        
        # Fecha y hora
        date_label = ctk.CTkLabel(self.options_frame, text="Fecha:")
        self.schedule_widgets.append(date_label)
        self.scheduled_date_entry = ctk.CTkEntry(self.options_frame, width=120, placeholder_text="YYYY-MM-DD")
        self.schedule_widgets.append(self.scheduled_date_entry)
        
        time_label = ctk.CTkLabel(self.options_frame, text="Hora:")
        self.schedule_widgets.append(time_label)
        self.scheduled_time_entry = ctk.CTkEntry(self.options_frame, width=100, placeholder_text="HH:MM:SS")
        self.schedule_widgets.append(self.scheduled_time_entry)
        
        # Botones de tiempo rápido
        quick_time_frame = ctk.CTkFrame(self.options_frame)
        self.schedule_widgets.append(quick_time_frame)
        
        ctk.CTkLabel(quick_time_frame, text="⚡ Tiempo rápido:").pack(side="left", padx=5)
        ctk.CTkButton(quick_time_frame, text="+1 min", width=60,
                     command=lambda: self.set_scheduled_quick_time(1)).pack(side="left", padx=2)
        ctk.CTkButton(quick_time_frame, text="+5 min", width=60,
                     command=lambda: self.set_scheduled_quick_time(5)).pack(side="left", padx=2)
        ctk.CTkButton(quick_time_frame, text="+15 min", width=60,
                     command=lambda: self.set_scheduled_quick_time(15)).pack(side="left", padx=2)
        ctk.CTkButton(quick_time_frame, text="+1 hora", width=60,
                     command=lambda: self.set_scheduled_quick_time(60)).pack(side="left", padx=2)
        
        # Opciones para tareas rápidas (inicialmente ocultas)
        self.quick_task_widgets = []
        
        name_label = ctk.CTkLabel(self.options_frame, text="Nombre:")
        self.quick_task_widgets.append(name_label)
        self.quick_task_name = ctk.CTkEntry(self.options_frame, placeholder_text="Nombre de la tarea rápida")
        self.quick_task_widgets.append(self.quick_task_name)
        
        color_label = ctk.CTkLabel(self.options_frame, text="Color:")
        self.quick_task_widgets.append(color_label)
        self.quick_task_color = ctk.CTkOptionMenu(self.options_frame, values=["blue", "green", "red", "orange", "purple"])
        self.quick_task_widgets.append(self.quick_task_color)
        self.quick_task_color.set("blue")
        
        # Descripción (común para programadas y rápidas)
        self.description_label = ctk.CTkLabel(self.options_frame, text="Descripción:")
        self.unified_description_entry = ctk.CTkEntry(self.options_frame, placeholder_text="Descripción opcional")
        
        # Botón de acción (cambia según el tipo)
        self.action_button = ctk.CTkButton(task_form_frame, text="▶️ Ejecutar Ahora", 
                                         command=self.execute_unified_task, fg_color="green")
        self.action_button.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Botones de gestión
        management_frame = ctk.CTkFrame(unified_tasks_frame)
        management_frame.grid(row=3, column=0, pady=10, padx=10, sticky="ew")
        
        ctk.CTkButton(management_frame, text="📋 Ver Tareas Programadas", width=150, 
                     command=self.show_scheduled_tasks_list).pack(side="left", padx=5)
        ctk.CTkButton(management_frame, text="✏️ Editar Tareas Rápidas", width=150,
                     command=self.edit_quick_tasks).pack(side="left", padx=5)
        ctk.CTkButton(management_frame, text="🗑️ Limpiar Completadas", width=150,
                     command=self.clear_completed_tasks).pack(side="left", padx=5)
        
        # Frame scrollable para mostrar tareas activas
        self.tasks_scrollable = ctk.CTkScrollableFrame(unified_tasks_frame, height=150)
        self.tasks_scrollable.grid(row=4, column=0, sticky="ew", padx=10, pady=(5, 10))
        self.tasks_scrollable.grid_columnconfigure(0, weight=1)
        
        # Inicializar vista
        self.on_task_type_change("Ejecutar Ahora")
        
        # Actualizar configuración de tiempo inicial
        self.update_time_config()
        
        # Inicializar fechas por defecto para tareas programadas
        self.set_default_datetime()
        
        # Cargar y actualizar listas
        self.load_scheduled_tasks()
        self.load_scheduled_tasks_display()
        self.update_tasks_list()
        self.load_quick_tasks()
        self.load_scheduled_tasks_display()
    
    def create_advanced_commands_section(self):
        """Crear sección de comandos avanzados"""
        advanced_frame = ctk.CTkFrame(self.main_scrollable_frame)
        advanced_frame.grid(row=5, column=0, sticky="ew", padx=5, pady=5)
        advanced_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Título
        advanced_title = ctk.CTkLabel(advanced_frame, text="🔧 Comandos Avanzados", 
                                     font=ctk.CTkFont(size=14, weight="bold"))
        advanced_title.grid(row=0, column=0, columnspan=4, pady=(10, 5))
        
        # Fila 1 - Gestión de jugadores
        self.whitelist_btn = ctk.CTkButton(advanced_frame, text="📋 Lista Blanca", 
                                          command=lambda: self.execute_command("ShowWhitelist"), 
                                          height=35)
        self.whitelist_btn.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.banlist_btn = ctk.CTkButton(advanced_frame, text="🚫 Lista Baneados", 
                                        command=lambda: self.execute_command("ShowBanList"), 
                                        height=35)
        self.banlist_btn.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.adminlist_btn = ctk.CTkButton(advanced_frame, text="👑 Lista Admins", 
                                          command=lambda: self.execute_command("ShowAdminList"), 
                                          height=35)
        self.adminlist_btn.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        
        self.player_stats_btn = ctk.CTkButton(advanced_frame, text="📊 Stats Jugadores", 
                                             command=self.show_player_stats_dialog, 
                                             height=35)
        self.player_stats_btn.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        
        # Fila 2 - Gestión del mundo
        self.world_info_btn = ctk.CTkButton(advanced_frame, text="🌍 Info Mundo", 
                                           command=lambda: self.execute_command("ShowWorldInfo"), 
                                           height=35)
        self.world_info_btn.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        
        self.dino_count_btn = ctk.CTkButton(advanced_frame, text="🦕 Contar Dinos", 
                                           command=lambda: self.execute_command("GetDinoCount"), 
                                           height=35)
        self.dino_count_btn.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        self.destroy_wild_btn = ctk.CTkButton(advanced_frame, text="💥 Destruir Salvajes", 
                                             command=self.show_destroy_wild_dialog, 
                                             height=35,
                                             fg_color=("orange", "darkorange"))
        self.destroy_wild_btn.grid(row=2, column=2, padx=5, pady=5, sticky="ew")
        
        self.chat_log_btn = ctk.CTkButton(advanced_frame, text="💬 Log Chat", 
                                         command=lambda: self.execute_command("GetChatLog"), 
                                         height=35)
        self.chat_log_btn.grid(row=2, column=3, padx=5, pady=(5, 10), sticky="ew")
    
    def create_monitoring_section(self):
        """Crear sección de monitoreo del servidor"""
        monitoring_frame = ctk.CTkFrame(self.main_scrollable_frame)
        monitoring_frame.grid(row=6, column=0, sticky="ew", padx=5, pady=5)
        monitoring_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Título
        monitoring_title = ctk.CTkLabel(monitoring_frame, text="📊 Monitoreo del Servidor", 
                                       font=ctk.CTkFont(size=14, weight="bold"))
        monitoring_title.grid(row=0, column=0, columnspan=2, pady=(10, 5))
        
        # Frame izquierdo - Información en tiempo real
        info_frame = ctk.CTkFrame(monitoring_frame)
        info_frame.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="nsew")
        info_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(info_frame, text="📈 Información en Tiempo Real", 
                    font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, pady=5)
        
        self.server_info_text = ctk.CTkTextbox(info_frame, height=120, state="disabled")
        self.server_info_text.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Botones de actualización
        info_buttons_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        info_buttons_frame.grid(row=2, column=0, pady=5)
        
        self.refresh_info_btn = ctk.CTkButton(info_buttons_frame, text="🔄 Actualizar", 
                                             command=self.refresh_server_info, width=100)
        self.refresh_info_btn.pack(side="left", padx=5)
        
        self.auto_refresh_switch = ctk.CTkSwitch(info_buttons_frame, text="Auto (30s)", 
                                                command=self.toggle_auto_refresh)
        self.auto_refresh_switch.pack(side="left", padx=10)
        
        # Frame derecho - Alertas y notificaciones
        alerts_frame = ctk.CTkFrame(monitoring_frame)
        alerts_frame.grid(row=1, column=1, padx=(5, 10), pady=5, sticky="nsew")
        alerts_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(alerts_frame, text="🚨 Alertas y Notificaciones", 
                    font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, pady=5)
        
        self.alerts_text = ctk.CTkTextbox(alerts_frame, height=120, state="disabled")
        self.alerts_text.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Configuración de alertas
        alerts_config_frame = ctk.CTkFrame(alerts_frame, fg_color="transparent")
        alerts_config_frame.grid(row=2, column=0, pady=5)
        
        self.player_alert_switch = ctk.CTkSwitch(alerts_config_frame, text="Alertas Jugadores")
        self.player_alert_switch.pack(pady=2)
        
        self.performance_alert_switch = ctk.CTkSwitch(alerts_config_frame, text="Alertas Rendimiento")
        self.performance_alert_switch.pack(pady=2)
        
        # Variables para monitoreo automático
        self.auto_refresh_active = False
        self.monitoring_thread = None
        
        # Configurar grid weights para que se expandan
        monitoring_frame.grid_rowconfigure(1, weight=1)
    
    # Métodos para programación de tareas
    def start_scheduler(self):
        """Iniciar el programador de tareas"""
        if not self.scheduler_running:
            self.scheduler_running = True
            self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self.scheduler_thread.start()
            self.scheduler_status_label.configure(text="Estado: ✅ Activo", text_color="green")
            self.start_scheduler_btn.configure(state="disabled")
            self.stop_scheduler_btn.configure(state="normal")
            self.add_result("Programador de tareas iniciado")
    
    def stop_scheduler(self):
        """Detener el programador de tareas"""
        if self.scheduler_running:
            self.scheduler_running = False
            schedule.clear()
            self.scheduler_status_label.configure(text="Estado: ❌ Inactivo", text_color="red")
            self.start_scheduler_btn.configure(state="normal")
            self.stop_scheduler_btn.configure(state="disabled")
            self.add_result("Programador de tareas detenido")
    
    def run_scheduler(self):
        """Ejecutar el bucle del programador"""
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(1)
    
    def add_scheduled_task(self):
        """Agregar nueva tarea programada"""
        command = self.task_command_entry.get().strip()
        task_type = self.task_type_var.get()
        description = self.task_description_entry.get().strip()
        
        if not command:
            self.add_result("Error: El comando no puede estar vacío")
            return
        
        if not description:
            description = f"Tarea {task_type}: {command}"
        
        # Crear la tarea según el tipo
        task_id = f"task_{len(self.scheduled_tasks) + 1}"
        
        try:
            if task_type == "Cada 5 minutos":
                schedule.every(5).minutes.do(self.execute_scheduled_command, command, task_id)
            elif task_type == "Cada 15 minutos":
                schedule.every(15).minutes.do(self.execute_scheduled_command, command, task_id)
            elif task_type == "Cada 30 minutos":
                schedule.every(30).minutes.do(self.execute_scheduled_command, command, task_id)
            elif task_type == "Cada hora":
                schedule.every().hour.do(self.execute_scheduled_command, command, task_id)
            elif task_type == "Cada 6 horas":
                schedule.every(6).hours.do(self.execute_scheduled_command, command, task_id)
            elif task_type == "Diario":
                schedule.every().day.at("12:00").do(self.execute_scheduled_command, command, task_id)
            
            # Guardar la tarea
            task = {
                'id': task_id,
                'command': command,
                'type': task_type,
                'description': description,
                'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.scheduled_tasks.append(task)
            self.save_scheduled_tasks()
            self.update_tasks_list()
            
            # Limpiar campos
            self.task_command_entry.delete(0, 'end')
            self.task_description_entry.delete(0, 'end')
            
            self.add_result(f"Tarea programada agregada: {description}")
            
        except Exception as e:
            self.add_result(f"Error al agregar tarea: {str(e)}")
    
    def execute_scheduled_command(self, command, task_id):
        """Ejecutar comando programado"""
        try:
            self.add_result(f"[PROGRAMADO] Ejecutando: {command}")
            self.execute_command(command)
        except Exception as e:
            self.add_result(f"Error en tarea programada {task_id}: {str(e)}")
    
    def remove_selected_task(self):
        """Eliminar tarea seleccionada (método legacy)"""
        self.add_result("Usa el botón 🗑️ junto a cada tarea para eliminarla")
    
    def remove_task_by_index(self, index):
        """Eliminar tarea por índice"""
        if 0 <= index < len(self.scheduled_tasks):
            task = self.scheduled_tasks[index]
            
            # Eliminar del programador
            schedule.clear(task['id'])
            
            # Eliminar de la lista
            self.scheduled_tasks.pop(index)
            self.save_scheduled_tasks()
            self.update_tasks_list()
            
            self.add_result(f"Tarea eliminada: {task['description']}")
        else:
            self.add_result("Error: Índice de tarea inválido")
    
    def update_tasks_list(self):
        """Actualizar lista de tareas programadas"""
        # Limpiar widgets existentes en el scrollable frame
        for widget in self.tasks_scrollable.winfo_children():
            widget.destroy()
        
        # Crear widgets para cada tarea
        for i, task in enumerate(self.scheduled_tasks):
            task_frame = ctk.CTkFrame(self.tasks_scrollable)
            task_frame.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
            task_frame.grid_columnconfigure(0, weight=1)
            
            # Información de la tarea
            display_text = f"[{task['type']}] {task['description']} - {task['created']}"
            task_label = ctk.CTkLabel(task_frame, text=display_text, anchor="w")
            task_label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
            
            # Botón eliminar
            delete_btn = ctk.CTkButton(task_frame, text="🗑️", width=30, height=25,
                                     command=lambda idx=i: self.remove_task_by_index(idx))
            delete_btn.grid(row=0, column=1, padx=5, pady=5)
    
    def save_scheduled_tasks(self):
        """Guardar tareas programadas en archivo"""
        try:
            tasks_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'scheduled_rcon_tasks.json')
            os.makedirs(os.path.dirname(tasks_file), exist_ok=True)
            
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.scheduled_tasks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.add_result(f"Error al guardar tareas: {str(e)}")
    
    def load_scheduled_tasks(self):
        """Cargar tareas programadas desde archivo"""
        try:
            tasks_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'scheduled_rcon_tasks.json')
            if os.path.exists(tasks_file):
                with open(tasks_file, 'r', encoding='utf-8') as f:
                    self.scheduled_tasks = json.load(f)
                    
                # Recargar tareas en el programador
                for task in self.scheduled_tasks:
                    task_type = task['type']
                    command = task['command']
                    task_id = task['id']
                    
                    if task_type == "Cada 5 minutos":
                        schedule.every(5).minutes.do(self.execute_scheduled_command, command, task_id)
                    elif task_type == "Cada 15 minutos":
                        schedule.every(15).minutes.do(self.execute_scheduled_command, command, task_id)
                    elif task_type == "Cada 30 minutos":
                        schedule.every(30).minutes.do(self.execute_scheduled_command, command, task_id)
                    elif task_type == "Cada hora":
                        schedule.every().hour.do(self.execute_scheduled_command, command, task_id)
                    elif task_type == "Cada 6 horas":
                        schedule.every(6).hours.do(self.execute_scheduled_command, command, task_id)
                    elif task_type == "Diario":
                        schedule.every().day.at("12:00").do(self.execute_scheduled_command, command, task_id)
        except Exception as e:
             self.add_result(f"Error al cargar tareas: {str(e)}")
             self.scheduled_tasks = []
    
    # Métodos para comandos avanzados
    def show_player_stats_dialog(self):
        """Mostrar diálogo para estadísticas de jugador"""
        dialog = ctk.CTkInputDialog(text="Ingresa el nombre del jugador:", title="Estadísticas de Jugador")
        player_name = dialog.get_input()
        
        if player_name:
            self.execute_command(f"GetPlayerStats {player_name}")
    
    def show_destroy_wild_dialog(self):
        """Mostrar diálogo de confirmación para destruir dinosaurios salvajes"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirmar Acción")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrar el diálogo
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (200 // 2)
        dialog.geometry(f"400x200+{x}+{y}")
        
        # Contenido del diálogo
        warning_label = ctk.CTkLabel(dialog, text="⚠️ ADVERTENCIA", 
                                    font=ctk.CTkFont(size=16, weight="bold"),
                                    text_color="orange")
        warning_label.pack(pady=10)
        
        message_label = ctk.CTkLabel(dialog, 
                                    text="Esta acción eliminará TODOS los dinosaurios salvajes\ndel servidor. Esta acción NO se puede deshacer.",
                                    font=ctk.CTkFont(size=12))
        message_label.pack(pady=10)
        
        question_label = ctk.CTkLabel(dialog, text="¿Estás seguro de continuar?", 
                                     font=ctk.CTkFont(size=12, weight="bold"))
        question_label.pack(pady=10)
        
        # Botones
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(pady=20)
        
        def confirm_destroy():
            self.execute_command("DestroyWildDinos")
            dialog.destroy()
        
        def cancel_destroy():
            dialog.destroy()
        
        cancel_btn = ctk.CTkButton(buttons_frame, text="❌ Cancelar", 
                                  command=cancel_destroy, width=100)
        cancel_btn.pack(side="left", padx=10)
        
        confirm_btn = ctk.CTkButton(buttons_frame, text="✅ Confirmar", 
                                   command=confirm_destroy, width=100,
                                   fg_color=("red", "darkred"))
        confirm_btn.pack(side="right", padx=10)
    
    # Métodos para monitoreo del servidor
    def refresh_server_info(self):
        """Actualizar información del servidor"""
        try:
            # Obtener información básica del servidor
            commands_info = [
                ("ListPlayers", "👥 Jugadores Conectados:"),
                ("GetGameTime", "⏰ Tiempo del Juego:"),
                ("ShowWorldInfo", "🌍 Información del Mundo:"),
                ("GetDinoCount", "🦕 Conteo de Dinosaurios:")
            ]
            
            info_text = f"📊 Actualizado: {datetime.now().strftime('%H:%M:%S')}\n\n"
            
            for command, label in commands_info:
                try:
                    # Ejecutar comando y capturar resultado
                    result = self.execute_rcon_command_sync(command)
                    if result:
                        info_text += f"{label}\n{result}\n\n"
                    else:
                        info_text += f"{label}\nNo disponible\n\n"
                except Exception as e:
                    info_text += f"{label}\nError: {str(e)}\n\n"
            
            # Actualizar el textbox
            self.server_info_text.configure(state="normal")
            self.server_info_text.delete("1.0", "end")
            self.server_info_text.insert("1.0", info_text)
            self.server_info_text.configure(state="disabled")
            
        except Exception as e:
            self.add_result(f"Error al actualizar información del servidor: {str(e)}")
    
    def execute_rcon_command_sync(self, command):
        """Ejecutar comando RCON de forma síncrona y retornar resultado"""
        try:
            if not self.get_rcon_status():
                return "RCON no está habilitado"
            
            rcon_executable = self.find_rcon_executable()
            if not rcon_executable:
                return "Ejecutable RCON no encontrado"
            
            rcon_command = [
                rcon_executable,
                "-H", self.rcon_ip,
                "-P", str(self.rcon_port),
                "-p", self.rcon_password,
                command
            ]
            
            result = subprocess.run(
                rcon_command,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=os.path.dirname(rcon_executable)
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            return "Timeout: El comando tardó demasiado"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def toggle_auto_refresh(self):
        """Activar/desactivar actualización automática"""
        if self.auto_refresh_switch.get():
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()
    
    def start_auto_refresh(self):
        """Iniciar actualización automática"""
        if not self.auto_refresh_active:
            self.auto_refresh_active = True
            self.monitoring_thread = threading.Thread(target=self.auto_refresh_loop, daemon=True)
            self.monitoring_thread.start()
            self.add_alert("🔄 Monitoreo automático iniciado")
    
    def stop_auto_refresh(self):
        """Detener actualización automática"""
        self.auto_refresh_active = False
        self.add_alert("⏹️ Monitoreo automático detenido")
    
    def auto_refresh_loop(self):
        """Bucle de actualización automática"""
        while self.auto_refresh_active:
            try:
                self.refresh_server_info()
                self.check_server_alerts()
                time.sleep(30)  # Actualizar cada 30 segundos
            except Exception as e:
                self.add_alert(f"Error en monitoreo automático: {str(e)}")
                time.sleep(30)
    
    def check_server_alerts(self):
        """Verificar alertas del servidor"""
        try:
            current_time = datetime.now()
            
            # Verificar alertas de jugadores si está habilitado
            if self.player_alert_switch.get():
                players_result = self.execute_rcon_command_sync("ListPlayers")
                if players_result and "No players" not in players_result:
                    player_count = len([line for line in players_result.split('\n') if line.strip()])
                    if player_count > 10:  # Alerta si hay más de 10 jugadores
                        self.add_alert(f"⚠️ Alto número de jugadores: {player_count}")
            
            # Verificar alertas de rendimiento si está habilitado
            if self.performance_alert_switch.get():
                dino_result = self.execute_rcon_command_sync("GetDinoCount")
                if dino_result and dino_result.isdigit():
                    dino_count = int(dino_result)
                    if dino_count > 50000:  # Alerta si hay más de 50k dinosaurios
                        self.add_alert(f"⚠️ Alto número de dinosaurios: {dino_count}")
                        
        except Exception as e:
            self.add_alert(f"Error verificando alertas: {str(e)}")
    
    def add_alert(self, message):
        """Agregar alerta al panel de alertas"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            alert_message = f"[{timestamp}] {message}\n"
            
            self.alerts_text.configure(state="normal")
            self.alerts_text.insert("end", alert_message)
            
            # Mantener solo las últimas 50 líneas
            lines = self.alerts_text.get("1.0", "end").split('\n')
            if len(lines) > 50:
                self.alerts_text.delete("1.0", f"{len(lines) - 50}.0")
            
            self.alerts_text.configure(state="disabled")
            self.alerts_text.see("end")
            
        except Exception as e:
             print(f"Error agregando alerta: {str(e)}")
    
    def on_task_type_change_old(self, event=None):
        """Método obsoleto - reemplazado por el nuevo sistema unificado"""
        pass
    
    def update_time_config(self):
        """Actualizar configuración de tiempo según el tipo de tarea"""
        # Este método se puede usar para mostrar/ocultar opciones de tiempo específicas
        pass
    
    # Métodos para tareas rápidas personalizables
    def load_quick_tasks_config(self):
        """Cargar configuración de tareas rápidas desde archivo"""
        try:
            # Asegurar que el directorio config existe
            os.makedirs("config", exist_ok=True)
            
            if os.path.exists(self.quick_tasks_file):
                with open(self.quick_tasks_file, 'r', encoding='utf-8') as f:
                    self.quick_tasks = json.load(f)
            else:
                # Crear tareas por defecto
                self.quick_tasks = [
                    {"name": "📢 Broadcast", "command": "broadcast Mensaje del administrador", "color": "blue"},
                    {"name": "💾 Guardar Mundo", "command": "saveworld", "color": "green"},
                    {"name": "📋 Lista Jugadores", "command": "listplayers", "color": "orange"},
                    {"name": "⏰ Tiempo", "command": "time", "color": "purple"}
                ]
                self.save_quick_tasks_config()
        except Exception as e:
            self.logger.error(f"Error al cargar tareas rápidas: {e}")
            self.quick_tasks = []
    
    def save_quick_tasks_config(self):
        """Guardar configuración de tareas rápidas"""
        try:
            os.makedirs("config", exist_ok=True)
            with open(self.quick_tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.quick_tasks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error al guardar tareas rápidas: {e}")
    
    def load_quick_tasks(self):
        """Cargar y mostrar botones de tareas rápidas"""
        # Limpiar botones existentes
        for widget in self.quick_tasks_frame.winfo_children():
            widget.destroy()
        
        # Crear filas de botones
        current_row = 0
        current_col = 0
        max_cols = 4
        
        for task in self.quick_tasks:
            if current_col == 0:
                row_frame = ctk.CTkFrame(self.quick_tasks_frame)
                row_frame.pack(fill="x", pady=5)
            
            color = task.get("color", "blue")
            btn = ctk.CTkButton(row_frame, text=task["name"], 
                               command=lambda cmd=task["command"]: self.execute_quick_task(cmd),
                               fg_color=color, width=120, height=35)
            btn.pack(side="left", padx=5)
            
            current_col += 1
            if current_col >= max_cols:
                current_col = 0
                current_row += 1
    
    def execute_quick_task(self, command):
        """Ejecutar una tarea rápida"""
        try:
            # Verificar si es un comando broadcast y reemplazarlo con el tipo configurado
            if command.startswith('broadcast '):
                message_type = self.get_message_type()
                # Extraer el mensaje del comando broadcast
                message_part = command[10:]  # Remover 'broadcast '
                command = f'{message_type} {message_part}'
                self.add_result(f"🚀 Tarea Rápida", f"Ejecutando: {command} (usando {message_type})")
            else:
                self.add_result(f"🚀 Tarea Rápida", f"Ejecutando: {command}")
            
            result = self.execute_rcon_command(command)
            if result:
                self.add_result(f"✅ Completado", result)
            else:
                self.add_result(f"⚠️ Sin respuesta", "Comando enviado pero sin respuesta del servidor")
        except Exception as e:
            self.add_result(f"❌ Error", f"Error al ejecutar tarea rápida: {str(e)}")
    
    def add_quick_task(self):
        """Agregar nueva tarea rápida"""
        dialog = QuickTaskDialog(self, "Agregar Nueva Tarea Rápida")
        if dialog.result:
            task_data = dialog.result
            self.quick_tasks.append(task_data)
            self.save_quick_tasks_config()
            self.load_quick_tasks()
            self.add_result("✅ Tarea Agregada", f"Nueva tarea rápida: {task_data['name']}")
    
    def edit_quick_tasks(self):
        """Editar tareas rápidas existentes"""
        if not self.quick_tasks:
            self.add_result("⚠️ Sin Tareas", "No hay tareas rápidas para editar")
            return
        
        dialog = EditTasksDialog(self, self.quick_tasks)
        if dialog.result:
            self.quick_tasks = dialog.result
            self.save_quick_tasks_config()
            self.load_quick_tasks()
            self.add_result("✅ Tareas Actualizadas", "Tareas rápidas actualizadas correctamente")
    
    def delete_quick_task(self):
        """Eliminar tarea rápida"""
        if not self.quick_tasks:
            self.add_result("⚠️ Sin Tareas", "No hay tareas rápidas para eliminar")
            return
        
        dialog = DeleteTaskDialog(self, self.quick_tasks)
        if dialog.result is not None:
            task_name = self.quick_tasks[dialog.result]["name"]
            del self.quick_tasks[dialog.result]
            self.save_quick_tasks_config()
            self.load_quick_tasks()
            self.add_result("🗑️ Tarea Eliminada", f"Tarea eliminada: {task_name}")
    
    # Métodos para tareas programadas estilo comandos directos
    def set_default_datetime(self):
        """Establecer fecha y hora por defecto"""
        from datetime import datetime, timedelta
        
        # Fecha actual
        today = datetime.now().strftime("%Y-%m-%d")
        self.scheduled_date_entry.insert(0, today)
        
        # Hora actual + 1 minuto
        future_time = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M:%S")
        self.scheduled_time_entry.insert(0, future_time)
    
    def set_scheduled_quick_time(self, minutes):
        """Establecer tiempo rápido para tareas programadas"""
        from datetime import datetime, timedelta
        
        future_time = datetime.now() + timedelta(minutes=minutes)
        
        # Limpiar y establecer nueva fecha
        self.scheduled_date_entry.delete(0, "end")
        self.scheduled_date_entry.insert(0, future_time.strftime("%Y-%m-%d"))
        
        # Limpiar y establecer nueva hora
        self.scheduled_time_entry.delete(0, "end")
        self.scheduled_time_entry.insert(0, future_time.strftime("%H:%M:%S"))
    
    def create_scheduled_task(self):
        """Crear nueva tarea programada"""
        try:
            from datetime import datetime
            
            # Obtener datos del formulario
            command_type = self.scheduled_command_type.get()
            params = self.scheduled_command_params.get().strip()
            date_str = self.scheduled_date_entry.get().strip()
            time_str = self.scheduled_time_entry.get().strip()
            description = self.scheduled_description_entry.get().strip()
            
            # Validar datos
            if not params:
                self.add_result("❌ Error", "Los parámetros del comando son obligatorios")
                return
            
            if not date_str or not time_str:
                self.add_result("❌ Error", "La fecha y hora son obligatorias")
                return
            
            # Construir comando completo
            if command_type == "custom":
                full_command = params
            else:
                full_command = f"{command_type} {params}"
            
            # Parsear fecha y hora
            try:
                datetime_str = f"{date_str} {time_str}"
                execution_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                self.add_result("❌ Error", "Formato de fecha/hora inválido. Use YYYY-MM-DD HH:MM:SS")
                return
            
            # Verificar que la fecha sea futura
            if execution_time <= datetime.now():
                self.add_result("❌ Error", "La fecha y hora deben ser futuras")
                return
            
            # Crear tarea programada
            task_data = {
                "id": f"task_{int(datetime.now().timestamp())}",
                "command": full_command,
                "execution_time": execution_time.isoformat(),
                "description": description or f"Comando {command_type}",
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
            
            # Agregar a la lista de tareas programadas
            if not hasattr(self, 'scheduled_tasks_list'):
                self.scheduled_tasks_list = []
            
            self.scheduled_tasks_list.append(task_data)
            
            # Guardar en archivo
            self.save_scheduled_tasks()
            
            # Actualizar display
            self.load_scheduled_tasks_display()
            
            # Limpiar formulario
            self.scheduled_command_params.delete(0, "end")
            self.scheduled_description_entry.delete(0, "end")
            self.set_default_datetime()
            
            self.add_result("✅ Tarea Creada", 
                          f"Tarea programada creada exitosamente\n\n"
                          f"Comando: {full_command}\n"
                          f"Ejecución: {execution_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            self.add_result("❌ Error", f"Error al crear tarea programada: {str(e)}")
    
    def save_scheduled_tasks(self):
        """Guardar tareas programadas en archivo"""
        try:
            import json
            os.makedirs("config", exist_ok=True)
            
            if not hasattr(self, 'scheduled_tasks_list'):
                self.scheduled_tasks_list = []
            
            with open("config/scheduled_rcon_tasks.json", 'w', encoding='utf-8') as f:
                json.dump(self.scheduled_tasks_list, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error al guardar tareas programadas: {e}")
    
    def load_scheduled_tasks(self):
        """Cargar tareas programadas desde archivo"""
        try:
            import json
            
            if os.path.exists("config/scheduled_rcon_tasks.json"):
                with open("config/scheduled_rcon_tasks.json", 'r', encoding='utf-8') as f:
                    self.scheduled_tasks_list = json.load(f)
            else:
                self.scheduled_tasks_list = []
                
        except Exception as e:
            self.logger.error(f"Error al cargar tareas programadas: {e}")
            self.scheduled_tasks_list = []
    
    def load_scheduled_tasks_display(self):
        """Cargar y mostrar tareas programadas en el display"""
        # Limpiar display actual
        for widget in self.tasks_scrollable.winfo_children():
            widget.destroy()
        
        if not hasattr(self, 'scheduled_tasks_list'):
            self.load_scheduled_tasks()
        
        if not self.scheduled_tasks_list:
            no_tasks_label = ctk.CTkLabel(self.tasks_scrollable, text="📭 No hay tareas programadas")
            no_tasks_label.pack(pady=20)
            return
        
        from datetime import datetime
        
        for i, task in enumerate(self.scheduled_tasks_list):
            if task.get('status') == 'completed':
                continue
                
            task_frame = ctk.CTkFrame(self.tasks_scrollable)
            task_frame.pack(fill="x", padx=5, pady=5)
            task_frame.grid_columnconfigure(1, weight=1)
            
            # Información de la tarea
            try:
                execution_time = datetime.fromisoformat(task['execution_time'])
                time_left = execution_time - datetime.now()
                
                if time_left.total_seconds() > 0:
                    hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    time_left_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    status_icon = "⏳"
                    status_color = "blue"
                else:
                    time_left_str = "¡Atrasada!"
                    status_icon = "⚠️"
                    status_color = "red"
                
                # Título y estado
                title_text = f"{status_icon} {task.get('description', 'Tarea sin descripción')}"
                title_label = ctk.CTkLabel(task_frame, text=title_text, font=ctk.CTkFont(weight="bold"))
                title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=2)
                
                # Comando
                command_label = ctk.CTkLabel(task_frame, text=f"Comando: {task['command']}")
                command_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=1)
                
                # Tiempo
                time_text = f"Ejecución: {execution_time.strftime('%Y-%m-%d %H:%M:%S')} (Restante: {time_left_str})"
                time_label = ctk.CTkLabel(task_frame, text=time_text)
                time_label.grid(row=2, column=0, sticky="w", padx=5, pady=1)
                
                # Botón eliminar
                delete_btn = ctk.CTkButton(task_frame, text="🗑️", width=30, height=25,
                                         command=lambda idx=i: self.delete_scheduled_task(idx),
                                         fg_color="red")
                delete_btn.grid(row=2, column=1, sticky="e", padx=5, pady=1)
                
            except Exception as e:
                error_label = ctk.CTkLabel(task_frame, text=f"Error en tarea: {str(e)}")
                error_label.pack(padx=5, pady=5)
    
    def delete_scheduled_task(self, index):
        """Eliminar tarea programada"""
        try:
            if 0 <= index < len(self.scheduled_tasks_list):
                task_name = self.scheduled_tasks_list[index].get('description', 'Tarea sin nombre')
                del self.scheduled_tasks_list[index]
                self.save_scheduled_tasks()
                self.load_scheduled_tasks_display()
                self.add_result("🗑️ Tarea Eliminada", f"Tarea eliminada: {task_name}")
        except Exception as e:
            self.add_result("❌ Error", f"Error al eliminar tarea: {str(e)}")
    
    def show_scheduled_tasks_list(self):
        """Mostrar lista detallada de tareas programadas"""
        dialog = ScheduledTasksListDialog(self, self.scheduled_tasks_list if hasattr(self, 'scheduled_tasks_list') else [])
        dialog.grab_set()
    
    def show_scheduled_history(self):
        """Mostrar historial de tareas ejecutadas"""
        self.add_result("ℹ️ Historial", "Funcionalidad de historial en desarrollo")
    
    def clear_completed_tasks(self):
        """Limpiar tareas completadas"""
        if not hasattr(self, 'scheduled_tasks_list'):
            self.scheduled_tasks_list = []
        
        original_count = len(self.scheduled_tasks_list)
        self.scheduled_tasks_list = [task for task in self.scheduled_tasks_list if task.get('status') != 'completed']
        cleared_count = original_count - len(self.scheduled_tasks_list)
        
        if cleared_count > 0:
            self.save_scheduled_tasks()
            self.load_scheduled_tasks_display()
            self.add_result("🗑️ Limpieza", f"Se eliminaron {cleared_count} tareas completadas")
        else:
            self.add_result("ℹ️ Limpieza", "No hay tareas completadas para eliminar")
    
    # Métodos para el sistema unificado de tareas
    def on_task_type_change(self, task_type):
        """Manejar cambio de tipo de tarea"""
        # Ocultar todos los widgets específicos
        for widget in self.schedule_widgets:
            widget.grid_remove()
        
        for widget in self.quick_task_widgets:
            widget.grid_remove()
        
        self.description_label.grid_remove()
        self.unified_description_entry.grid_remove()
        
        if task_type == "Ejecutar Ahora":
            self.action_button.configure(text="▶️ Ejecutar Ahora", fg_color="green")
            
        elif task_type == "Programar":
            # Mostrar widgets de programación
            self.schedule_widgets[0].grid(row=0, column=0, padx=5, pady=5, sticky="w")  # date_label
            self.schedule_widgets[1].grid(row=0, column=1, padx=5, pady=5, sticky="w")  # date_entry
            self.schedule_widgets[2].grid(row=0, column=2, padx=5, pady=5, sticky="w")  # time_label
            self.schedule_widgets[3].grid(row=0, column=3, padx=5, pady=5, sticky="w")  # time_entry
            self.schedule_widgets[4].grid(row=1, column=0, columnspan=4, pady=5, sticky="ew")  # quick_time_frame
            
            self.description_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
            self.unified_description_entry.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
            
            self.action_button.configure(text="⏰ Programar Tarea", fg_color="blue")
            self.set_default_datetime()
            
        elif task_type == "Tarea Rápida":
            # Mostrar widgets de tarea rápida
            self.quick_task_widgets[0].grid(row=0, column=0, padx=5, pady=5, sticky="w")  # name_label
            self.quick_task_widgets[1].grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="ew")  # name_entry
            self.quick_task_widgets[2].grid(row=1, column=0, padx=5, pady=5, sticky="w")  # color_label
            self.quick_task_widgets[3].grid(row=1, column=1, padx=5, pady=5, sticky="w")  # color_option
            
            self.description_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
            self.unified_description_entry.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
            
            self.action_button.configure(text="💾 Guardar Tarea Rápida", fg_color="purple")
    
    def execute_unified_task(self):
        """Ejecutar tarea según el tipo seleccionado"""
        task_type = self.task_type.get()
        command_type = self.unified_command_type.get()
        params = self.unified_command_params.get().strip()
        
        if not params:
            self.add_result("❌ Error", "Los parámetros del comando son obligatorios")
            return
        
        # Construir comando completo
        if command_type == "custom":
            full_command = params
        else:
            full_command = f"{command_type} {params}"
        
        # Si es un comando broadcast o serverchat, usar el tipo de mensaje configurado
        if command_type == "broadcast":
            message_type = self.get_message_type()
            full_command = f"{message_type} {params}"
        elif command_type == "serverchat":
            # serverchat siempre usa serverchat, no necesita configuración
            full_command = f"serverchat {params}"
        
        if task_type == "Ejecutar Ahora":
            # Ejecutar inmediatamente
            self.execute_command(full_command)
            
        elif task_type == "Programar":
            # Crear tarea programada
            self.create_scheduled_task_unified(full_command)
            
        elif task_type == "Tarea Rápida":
            # Crear tarea rápida
            self.create_quick_task_unified(full_command)
    
    def create_scheduled_task_unified(self, full_command):
        """Crear tarea programada desde el sistema unificado"""
        try:
            from datetime import datetime
            
            date_str = self.scheduled_date_entry.get().strip()
            time_str = self.scheduled_time_entry.get().strip()
            description = self.unified_description_entry.get().strip()
            
            if not date_str or not time_str:
                self.add_result("❌ Error", "La fecha y hora son obligatorias")
                return
            
            # Parsear fecha y hora
            try:
                datetime_str = f"{date_str} {time_str}"
                execution_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                self.add_result("❌ Error", "Formato de fecha/hora inválido. Use YYYY-MM-DD HH:MM:SS")
                return
            
            # Verificar que la fecha sea futura
            if execution_time <= datetime.now():
                self.add_result("❌ Error", "La fecha y hora deben ser futuras")
                return
            
            # Crear tarea programada
            task_data = {
                "id": f"task_{int(datetime.now().timestamp())}",
                "command": full_command,
                "execution_time": execution_time.isoformat(),
                "description": description or f"Tarea programada",
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
            
            # Agregar a la lista de tareas programadas
            if not hasattr(self, 'scheduled_tasks_list'):
                self.scheduled_tasks_list = []
            
            self.scheduled_tasks_list.append(task_data)
            
            # Guardar en archivo
            self.save_scheduled_tasks()
            
            # Actualizar display
            self.load_scheduled_tasks_display()
            
            # Limpiar formulario
            self.unified_command_params.delete(0, "end")
            self.unified_description_entry.delete(0, "end")
            self.set_default_datetime()
            
            self.add_result("✅ Tarea Programada", 
                          f"Tarea creada exitosamente\n\n"
                          f"Comando: {full_command}\n"
                          f"Ejecución: {execution_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            self.add_result("❌ Error", f"Error al crear tarea programada: {str(e)}")
    
    def create_quick_task_unified(self, full_command):
        """Crear tarea rápida desde el sistema unificado"""
        try:
            name = self.quick_task_name.get().strip()
            color = self.quick_task_color.get()
            description = self.unified_description_entry.get().strip()
            
            if not name:
                self.add_result("❌ Error", "El nombre de la tarea rápida es obligatorio")
                return
            
            # Verificar que no exista una tarea con el mismo nombre
            for task in self.quick_tasks:
                if task["name"] == name:
                    self.add_result("❌ Error", f"Ya existe una tarea rápida con el nombre '{name}'")
                    return
            
            # Crear tarea rápida
            task_data = {
                "name": name,
                "command": full_command,
                "color": color,
                "description": description or name
            }
            
            self.quick_tasks.append(task_data)
            self.save_quick_tasks_config()
            self.load_quick_tasks()
            
            # Limpiar formulario
            self.unified_command_params.delete(0, "end")
            self.quick_task_name.delete(0, "end")
            self.unified_description_entry.delete(0, "end")
            
            self.add_result("✅ Tarea Rápida Creada", 
                          f"Tarea rápida '{name}' creada exitosamente\n\n"
                          f"Comando: {full_command}")
            
        except Exception as e:
            self.add_result("❌ Error", f"Error al crear tarea rápida: {str(e)}")


# Diálogos para gestión de tareas rápidas
class QuickTaskDialog(ctk.CTkToplevel):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.parent = parent
        self.result = None
        
        self.title(title)
        self.geometry("400x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Centrar ventana
        self.center_window()
        
        self.create_widgets()
    
    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (300 // 2)
        self.geometry(f"400x300+{x}+{y}")
    
    def create_widgets(self):
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(main_frame, text="Nueva Tarea Rápida", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Nombre
        ctk.CTkLabel(main_frame, text="Nombre de la tarea:").pack(anchor="w", padx=10)
        self.name_entry = ctk.CTkEntry(main_frame, placeholder_text="📢 Mi Tarea")
        self.name_entry.pack(fill="x", padx=10, pady=5)
        
        # Comando
        ctk.CTkLabel(main_frame, text="Comando RCON:").pack(anchor="w", padx=10, pady=(10,0))
        self.command_entry = ctk.CTkEntry(main_frame, placeholder_text="broadcast Hola mundo")
        self.command_entry.pack(fill="x", padx=10, pady=5)
        
        # Color
        ctk.CTkLabel(main_frame, text="Color del botón:").pack(anchor="w", padx=10, pady=(10,0))
        self.color_var = ctk.StringVar(value="blue")
        color_frame = ctk.CTkFrame(main_frame)
        color_frame.pack(fill="x", padx=10, pady=5)
        
        colors = [("Azul", "blue"), ("Verde", "green"), ("Naranja", "orange"), 
                 ("Rojo", "red"), ("Púrpura", "purple"), ("Gris", "gray")]
        
        for i, (name, value) in enumerate(colors):
            ctk.CTkRadioButton(color_frame, text=name, variable=self.color_var, 
                              value=value).grid(row=i//3, column=i%3, padx=5, pady=2, sticky="w")
        
        # Botones
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=20)
        
        ctk.CTkButton(button_frame, text="✅ Agregar", 
                     command=self.accept, fg_color="green").pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="❌ Cancelar", 
                     command=self.cancel, fg_color="red").pack(side="right", padx=5)
    
    def accept(self):
        name = self.name_entry.get().strip()
        command = self.command_entry.get().strip()
        color = self.color_var.get()
        
        if not name or not command:
            return
        
        self.result = {
            "name": name,
            "command": command,
            "color": color
        }
        self.destroy()
    
    def cancel(self):
        self.destroy()

class ScheduledTasksListDialog(ctk.CTkToplevel):
    def __init__(self, parent, tasks):
        super().__init__(parent)
        self.tasks = tasks
        
        self.title("Lista de Tareas Programadas")
        self.geometry("600x400")
        self.transient(parent)
        
        # Centrar ventana
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (400 // 2)
        self.geometry(f"600x400+{x}+{y}")
        
        self.create_widgets()
    
    def create_widgets(self):
        # Título
        title_label = ctk.CTkLabel(self, text="📋 Tareas Programadas", 
                                  font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=20)
        
        # Lista de tareas
        self.tasks_frame = ctk.CTkScrollableFrame(self, height=250)
        self.tasks_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        if not self.tasks:
            no_tasks_label = ctk.CTkLabel(self.tasks_frame, text="📭 No hay tareas programadas")
            no_tasks_label.pack(pady=50)
        else:
            from datetime import datetime
            
            for i, task in enumerate(self.tasks):
                if task.get('status') == 'completed':
                    continue
                    
                task_frame = ctk.CTkFrame(self.tasks_frame)
                task_frame.pack(fill="x", padx=5, pady=5)
                
                try:
                    execution_time = datetime.fromisoformat(task['execution_time'])
                    time_left = execution_time - datetime.now()
                    
                    if time_left.total_seconds() > 0:
                        hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        time_left_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        status_icon = "⏳"
                    else:
                        time_left_str = "¡Atrasada!"
                        status_icon = "⚠️"
                    
                    # Información de la tarea
                    info_text = f"{status_icon} {task.get('description', 'Sin descripción')}\n"
                    info_text += f"Comando: {task['command']}\n"
                    info_text += f"Ejecución: {execution_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    info_text += f"Tiempo restante: {time_left_str}"
                    
                    task_label = ctk.CTkLabel(task_frame, text=info_text, justify="left")
                    task_label.pack(padx=10, pady=10)
                    
                except Exception as e:
                    error_label = ctk.CTkLabel(task_frame, text=f"Error en tarea: {str(e)}")
                    error_label.pack(padx=10, pady=10)
        
        # Botón cerrar
        close_btn = ctk.CTkButton(self, text="Cerrar", command=self.destroy)
        close_btn.pack(pady=20)


class EditTasksDialog(ctk.CTkToplevel):
    def __init__(self, parent, tasks):
        super().__init__(parent)
        self.parent = parent
        self.tasks = tasks.copy()
        self.result = None
        
        self.title("Editar Tareas Rápidas")
        self.geometry("600x400")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        self.center_window()
        self.create_widgets()
    
    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (400 // 2)
        self.geometry(f"600x400+{x}+{y}")
    
    def create_widgets(self):
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(main_frame, text="Editar Tareas Rápidas", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Lista scrollable
        self.scrollable_frame = ctk.CTkScrollableFrame(main_frame)
        self.scrollable_frame.pack(fill="both", expand=True, pady=10)
        
        self.load_tasks()
        
        # Botones
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(button_frame, text="✅ Guardar Cambios", 
                     command=self.save_changes, fg_color="green").pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="❌ Cancelar", 
                     command=self.cancel, fg_color="red").pack(side="right", padx=5)
    
    def load_tasks(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.task_entries = []
        
        for i, task in enumerate(self.tasks):
            task_frame = ctk.CTkFrame(self.scrollable_frame)
            task_frame.pack(fill="x", padx=5, pady=5)
            
            # Nombre
            ctk.CTkLabel(task_frame, text=f"Tarea {i+1}:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
            name_entry = ctk.CTkEntry(task_frame, width=150)
            name_entry.insert(0, task["name"])
            name_entry.grid(row=0, column=1, padx=5, pady=2)
            
            # Comando
            ctk.CTkLabel(task_frame, text="Comando:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
            command_entry = ctk.CTkEntry(task_frame, width=200)
            command_entry.insert(0, task["command"])
            command_entry.grid(row=0, column=3, padx=5, pady=2)
            
            # Color
            color_var = ctk.StringVar(value=task.get("color", "blue"))
            color_menu = ctk.CTkOptionMenu(task_frame, values=["blue", "green", "orange", "red", "purple", "gray"],
                                          variable=color_var, width=80)
            color_menu.grid(row=0, column=4, padx=5, pady=2)
            
            self.task_entries.append((name_entry, command_entry, color_var))
    
    def save_changes(self):
        updated_tasks = []
        for name_entry, command_entry, color_var in self.task_entries:
            name = name_entry.get().strip()
            command = command_entry.get().strip()
            color = color_var.get()
            
            if name and command:
                updated_tasks.append({
                    "name": name,
                    "command": command,
                    "color": color
                })
        
        self.result = updated_tasks
        self.destroy()
    
    def cancel(self):
        self.destroy()


class DeleteTaskDialog(ctk.CTkToplevel):
    def __init__(self, parent, tasks):
        super().__init__(parent)
        self.parent = parent
        self.tasks = tasks
        self.result = None
        
        self.title("Eliminar Tarea Rápida")
        self.geometry("400x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.center_window()
        self.create_widgets()
    
    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (300 // 2)
        self.geometry(f"400x300+{x}+{y}")
    
    def create_widgets(self):
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(main_frame, text="Seleccionar Tarea a Eliminar", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Lista de tareas
        self.task_var = ctk.StringVar()
        
        for i, task in enumerate(self.tasks):
            ctk.CTkRadioButton(main_frame, text=f"{task['name']} - {task['command']}", 
                              variable=self.task_var, value=str(i)).pack(anchor="w", padx=10, pady=2)
        
        # Botones
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=20)
        
        ctk.CTkButton(button_frame, text="🗑️ Eliminar", 
                     command=self.delete_task, fg_color="red").pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="❌ Cancelar", 
                     command=self.cancel, fg_color="gray").pack(side="right", padx=5)
    
    def delete_task(self):
        selected = self.task_var.get()
        if selected:
            self.result = int(selected)
            self.destroy()
    
    def cancel(self):
        self.destroy()
