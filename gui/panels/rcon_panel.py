import customtkinter as ctk
import subprocess
import threading
import os
import json
from pathlib import Path


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
        
        # Empaquetar el frame principal
        self.pack(fill="both", expand=True)
        
        self.create_widgets()
        
        # Cargar configuración después de un pequeño retraso para asegurar que los widgets estén listos
        self.after(100, self.load_rcon_config)
        
    def create_widgets(self):
        """Crear todos los widgets del panel RCON"""
        # Configurar el grid principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # El área de resultados se expande
        
        # === CONFIGURACIÓN RCON ===
        config_frame = ctk.CTkFrame(self)
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
            text="Agregar ?RCONEnable=True?RCONPort=27020",
            command=self.on_rcon_switch_change
        )
        self.rcon_enable_switch.pack(side="left", padx=10)
        
        # Botones de configuración
        config_buttons_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        config_buttons_frame.grid(row=3, column=0, columnspan=6, pady=5)
        
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
        commands_frame = ctk.CTkFrame(self)
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
        custom_frame = ctk.CTkFrame(self)
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
        results_frame = ctk.CTkFrame(self)
        results_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
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
    
    def save_rcon_config(self):
        """Guardar configuración RCON (sin password, se toma automáticamente)"""
        try:
            self.rcon_ip = self.ip_entry.get()
            self.rcon_port = self.port_entry.get()
            
            self.logger.info(f"Guardando configuración RCON - IP: {self.rcon_ip}, Puerto: {self.rcon_port}")
            
            self.config_manager.set("rcon", "ip", self.rcon_ip)
            self.config_manager.set("rcon", "port", self.rcon_port)
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
        if hasattr(self, 'main_window') and hasattr(self.main_window, 'add_log_message'):
            self.main_window.add_log_message(f"🎮 RCON: Ejecutando '{command}'...")
        
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
                if hasattr(self, 'main_window') and hasattr(self.main_window, 'add_log_message'):
                    self.main_window.add_log_message(f"🔌 RCON Error: No se encontró ejecutable RCON")
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
                if hasattr(self, 'main_window') and hasattr(self.main_window, 'add_log_message'):
                    self.main_window.add_log_message(success_msg)
                
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
                if hasattr(self, 'main_window') and hasattr(self.main_window, 'add_log_message'):
                    self.main_window.add_log_message(fail_msg)
                
                # Log en archivo
                if hasattr(self, 'main_window') and hasattr(self.main_window, 'log_server_event'):
                    self.main_window.log_server_event("rcon_command", 
                        command=command,
                        success=False,
                        result=error_msg)
                
                return f"❌ Error: {error_msg}"
                
        except subprocess.TimeoutExpired:
            timeout_msg = f"⏱️ RCON Timeout: '{command}' tardó demasiado en ejecutarse"
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'add_log_message'):
                self.main_window.add_log_message(timeout_msg)
            return "❌ Timeout: El comando tardó demasiado en ejecutarse"
        except Exception as e:
            self.logger.error(f"Error al ejecutar comando RCON: {e}")
            error_msg = f"🔌 RCON Error: '{command}' - Error de conexión: {str(e)}"
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'add_log_message'):
                self.main_window.add_log_message(error_msg)
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
            self.execute_command(f'broadcast "{message}"')
    
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
        dialog.geometry("350x200")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrar ventana
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (dialog.winfo_screenheight() // 2) - (200 // 2)
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
        dialog.geometry("350x200")
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
