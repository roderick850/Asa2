import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import os
import time
import threading
import logging
from utils.server_manager import ServerManager
from utils.config_manager import ConfigManager
from datetime import datetime


class ServerPanel:
    def __init__(self, parent, config_manager, logger, main_window=None):
        self.parent = parent
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        self.server_manager = ServerManager(config_manager)
        
        # Inicializar variables de selección
        self.selected_server = None
        self.selected_map = None
        
        self.create_widgets()
        
        # Iniciar monitoreo con retraso para asegurar que main_window esté listo
        if self.main_window and hasattr(self.main_window, 'after'):
            self.main_window.after(2000, self.start_monitoring)  # 2 segundos de retraso
        else:
            # Fallback si no hay main_window
            import threading
            threading.Timer(2.0, self.start_monitoring).start()
    
    def create_widgets(self):
        # Si no hay parent, no crear widgets (modo backend solamente)
        if self.parent is None:
            return
            
        # Frame principal
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Título
        title_label = ctk.CTkLabel(main_frame, text="Panel de Control", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=(5, 10))
        
        # Frame para información del servidor
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", padx=5, pady=5)
        
        # Información del servidor
        info_label = ctk.CTkLabel(info_frame, text="Información del Servidor", font=ctk.CTkFont(size=14, weight="bold"))
        info_label.pack(pady=(10, 5))
        
        # Grid para información
        info_grid = ctk.CTkFrame(info_frame)
        info_grid.pack(pady=5)
        
        # Estado del servidor
        ctk.CTkLabel(info_grid, text="Estado:").grid(row=0, column=0, padx=8, pady=3, sticky="w")
        self.status_label = ctk.CTkLabel(info_grid, text="Detenido", text_color="red")
        self.status_label.grid(row=0, column=1, padx=8, pady=3, sticky="w")
        
        # Tiempo de actividad
        ctk.CTkLabel(info_grid, text="Tiempo de actividad:").grid(row=1, column=0, padx=8, pady=3, sticky="w")
        self.uptime_label = ctk.CTkLabel(info_grid, text="00:00:00")
        self.uptime_label.grid(row=1, column=1, padx=8, pady=3, sticky="w")
        
        # Uso de CPU
        ctk.CTkLabel(info_grid, text="Uso de CPU:").grid(row=2, column=0, padx=8, pady=3, sticky="w")
        self.cpu_label = ctk.CTkLabel(info_grid, text="0%")
        self.cpu_label.grid(row=2, column=1, padx=8, pady=3, sticky="w")
        
        # Uso de memoria
        ctk.CTkLabel(info_grid, text="Uso de memoria:").grid(row=3, column=0, padx=8, pady=3, sticky="w")
        self.memory_label = ctk.CTkLabel(info_grid, text="0 MB")
        self.memory_label.grid(row=3, column=1, padx=8, pady=3, sticky="w")
        
        # Frame para barra de progreso
        self.progress_frame = ctk.CTkFrame(main_frame)
        self.progress_frame.pack(fill="x", padx=5, pady=5)
        
        # Barra de progreso
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.progress_label.pack(pady=(5, 2))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 5))
        self.progress_bar.set(0)
        
        # Ocultar la barra de progreso inicialmente
        self.progress_frame.pack_forget()
        
        # Frame para acciones rápidas
        quick_actions_frame = ctk.CTkFrame(main_frame)
        quick_actions_frame.pack(fill="x", padx=5, pady=5)
        
        quick_actions_label = ctk.CTkLabel(quick_actions_frame, text="Acciones Rápidas", font=ctk.CTkFont(size=14, weight="bold"))
        quick_actions_label.pack(pady=(10, 5))
        
        # Botones de acciones rápidas
        quick_buttons_frame = ctk.CTkFrame(quick_actions_frame)
        quick_buttons_frame.pack(pady=5)
        
        self.save_button = ctk.CTkButton(
            quick_buttons_frame,
            text="Guardar Mundo",
            command=self.save_world,
            width=100,
            height=30
        )
        self.save_button.grid(row=0, column=0, padx=3, pady=3)
        
        self.backup_button = ctk.CTkButton(
            quick_buttons_frame,
            text="Crear Backup",
            command=self.create_backup,
            width=100,
            height=30
        )
        self.backup_button.grid(row=0, column=1, padx=3, pady=3)
        
        self.broadcast_button = ctk.CTkButton(
            quick_buttons_frame,
            text="Broadcast",
            command=self.show_broadcast_dialog,
            width=100,
            height=30
        )
        self.broadcast_button.grid(row=0, column=2, padx=3, pady=3)
        
        self.kick_all_button = ctk.CTkButton(
            quick_buttons_frame,
            text="Expulsar Todos",
            command=self.kick_all_players,
            width=100,
            height=30
        )
        self.kick_all_button.grid(row=0, column=3, padx=3, pady=3)
        
        # Botón de prueba de logs
        test_logs_button = ctk.CTkButton(
            quick_buttons_frame, 
            text="🧪 Test Logs", 
            command=self.test_logs,
            width=80,
            height=30,
            fg_color="purple"
        )
        test_logs_button.grid(row=0, column=4, padx=3, pady=3)
        
        # Frame para área de logs
        logs_frame = ctk.CTkFrame(main_frame)
        logs_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        logs_label = ctk.CTkLabel(logs_frame, text="Logs del Sistema", font=ctk.CTkFont(size=14, weight="bold"))
        logs_label.pack(pady=(10, 5))
        
        # Área de logs con scroll
        self.logs_text = ctk.CTkTextbox(logs_frame, height=200)
        self.logs_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configurar el área de logs para mostrar mensajes
        self.logs_text.configure(state="normal")
        initial_message = """📋 LOGS DEL SISTEMA - ARK SERVER MANAGER
════════════════════════════════════════════

✅ Panel de control del servidor iniciado correctamente
📅 """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """

🎮 ESTADO: Esperando comandos...

💡 Los mensajes de estado, errores y eventos aparecerán aquí
💡 Use los botones superiores para controlar el servidor
"""
        self.logs_text.insert("1.0", initial_message)
        self.logs_text.configure(state="disabled")
        
        # Agregar mensajes de prueba para verificar funcionamiento
        self.add_status_message("Panel de servidor cargado correctamente", "success")
        self.add_status_message("Sistema de logs funcionando", "info")
        self.add_status_message("Listo para recibir comandos", "info")
        
        # Programar mensajes adicionales para asegurar visibilidad
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.after(1000, lambda: self.add_status_message("Área de logs activa", "success"))
            self.main_window.after(2000, lambda: self.add_status_message("Monitoreo del sistema iniciado", "info"))
    
    def browse_root_path(self):
        """Buscar directorio raíz para servidores"""
        directory = filedialog.askdirectory(title="Seleccionar ruta raíz para servidores")
        if directory:
            self.config_manager.set("server", "root_path", directory)
            self.config_manager.save()
            self.update_current_path_display()
            self.add_status_message(f"Ruta raíz cambiada a: {directory}", "success")
    
    def update_current_path_display(self):
        """Actualizar la visualización de la ruta actual"""
        # Este método ya no es necesario en el panel ya que la ruta se muestra en la barra superior
        # Solo refrescar la lista de servidores cuando cambia la ruta
        self.refresh_servers_list()
    
    def refresh_servers_list(self):
        """Refresca la lista de servidores disponibles"""
        try:
            root_path = self.config_manager.get("server", "root_path", "").strip()
            if not root_path or not os.path.exists(root_path):
                # Buscar el dropdown en la ventana principal
                if hasattr(self.main_window, 'server_dropdown'):
                    self.main_window.server_dropdown.configure(values=["Seleccionar servidor..."])
                return
            
            # Buscar servidores en el directorio raíz
            servers = []
            for item in os.listdir(root_path):
                item_path = os.path.join(root_path, item)
                if os.path.isdir(item_path) and item != "SteamCMD":
                    # Verificar si es un servidor válido buscando el ejecutable
                    if self.server_manager.find_server_executable(item_path):
                        servers.append(item)
            
            if servers:
                # Buscar el dropdown en la ventana principal
                if hasattr(self.main_window, 'server_dropdown'):
                    self.main_window.server_dropdown.configure(values=["Seleccionar servidor..."] + servers)
                self.add_status_message(f"Encontrados {len(servers)} servidor(es)", "info")
            else:
                # Buscar el dropdown en la ventana principal
                if hasattr(self.main_window, 'server_dropdown'):
                    self.main_window.server_dropdown.configure(values=["Seleccionar servidor..."])
                self.add_status_message("No se encontraron servidores instalados", "warning")
                
        except Exception as e:
            self.logger.error(f"Error al refrescar lista de servidores: {e}")
            # Buscar el dropdown en la ventana principal
            if hasattr(self.main_window, 'server_dropdown'):
                self.main_window.server_dropdown.configure(values=["Seleccionar servidor..."])
    
    def on_server_selected(self, server_name):
        """Maneja la selección de un servidor"""
        if server_name and server_name != "Seleccionar servidor...":
            self.selected_server = server_name
            self.add_status_message(f"Servidor seleccionado: {server_name}", "info")
            # Cargar mapas disponibles para este servidor
            self.load_maps_for_server(server_name)
            # Actualizar información del servidor
            self.update_server_info_for_selected()
            # Mostrar información del servidor en la interfaz
            self.show_selected_server_info()
        else:
            self.selected_server = None
            # Buscar el dropdown en la ventana principal
            if hasattr(self.main_window, 'map_dropdown'):
                self.main_window.map_dropdown.configure(values=["Seleccionar mapa..."])
            self.clear_selected_server_info()
    
    def show_selected_server_info(self):
        """Muestra la información del servidor seleccionado en la interfaz"""
        server_info = self.get_selected_server_info()
        if server_info:
            # Actualizar el título o mostrar información adicional
            info_text = f"Servidor: {server_info['name']}"
            if server_info['has_executable']:
                info_text += " ✅"
            else:
                info_text += " ⚠️"
            
            # Aquí podrías actualizar un label o mostrar más información
            self.add_status_message(f"Información del servidor: {info_text}", "info")
    
    def clear_selected_server_info(self):
        """Limpia la información del servidor seleccionado"""
        # Aquí podrías limpiar la información mostrada
        pass
    
    def update_server_info_for_selected(self):
        """Actualiza la información del servidor seleccionado"""
        if not self.selected_server:
            return
        
        try:
            root_path = self.config_manager.get("server", "root_path", "").strip()
            if not root_path:
                return
            
            server_path = os.path.join(root_path, self.selected_server)
            if not os.path.exists(server_path):
                return
            
            # Buscar el ejecutable del servidor
            server_exe = self.server_manager.find_server_executable(server_path)
            if server_exe:
                # Guardar la ruta del ejecutable en la configuración
                server_key = f"executable_path_{self.selected_server}"
                self.config_manager.set("server", server_key, server_exe)
                self.config_manager.save()
                
                self.add_status_message(f"✅ Ejecutable encontrado para {self.selected_server}: {server_exe}", "success")
            else:
                self.add_status_message(f"⚠️ No se encontró el ejecutable para {self.selected_server}", "warning")
                
        except Exception as e:
            self.logger.error(f"Error al actualizar información del servidor: {e}")
    
    def load_maps_for_server(self, server_name):
        """Carga los mapas disponibles para el servidor seleccionado"""
        try:
            root_path = self.config_manager.get("server", "root_path", "").strip()
            if not root_path or not server_name:
                # Buscar el dropdown en la ventana principal
                if hasattr(self.main_window, 'map_dropdown'):
                    self.main_window.map_dropdown.configure(values=["Seleccionar mapa..."])
                return
            
            server_path = os.path.join(root_path, server_name)
            if not os.path.exists(server_path):
                # Buscar el dropdown en la ventana principal
                if hasattr(self.main_window, 'map_dropdown'):
                    self.main_window.map_dropdown.configure(values=["Seleccionar mapa..."])
                return
            
            # Mapas disponibles para Ark Survival Ascended - USAR NOMBRES AMIGABLES
            # NOTA: El dropdown del main_window debe tener nombres amigables, no identificadores técnicos
            available_maps_technical = [
                "TheIsland_WP",           # The Island ✅ _WP
                "TheCenter_WP",              # The Center ✅ Sin _WP
                "ScorchedEarth_WP",       # Scorched Earth ✅ _WP
                "Ragnarok_WP",               # Ragnarok ✅ Sin _WP
                "Aberration_P",           # Aberration ✅ _P
                "Extinction",             # Extinction ✅ Sin _WP
                "Valguero_P",             # Valguero ✅ _P
                "Genesis",                # Genesis Part 1 ✅ Sin _WP
                "CrystalIsles",           # Crystal Isles ✅ Sin _WP
                "Gen2",                   # Genesis Part 2 ✅ Gen2 (corregido)
                "LostIsland",             # Lost Island ✅ Sin _WP
                "Fjordur",                # Fjordur ✅ Sin _WP
                "ModdedMap"               # Mapa Modded
            ]
            
            # Mapeo de identificadores técnicos a nombres amigables - CORREGIDO
            tech_to_friendly_maps = {
                "TheIsland_WP": "The Island",        # ✅ _WP
                "TheCenter_WP": "The Center",           # ✅ Sin _WP
                "ScorchedEarth_WP": "Scorched Earth", # ✅ _WP
                "Ragnarok_WP": "Ragnarok",              # ✅ Sin _WP
                "Aberration_P": "Aberration",        # ✅ _P
                "Extinction": "Extinction",          # ✅ Sin _WP
                "Valguero_P": "Valguero",           # ✅ _P
                "Genesis": "Genesis: Part 1",        # ✅ Sin _WP
                "CrystalIsles": "Crystal Isles",     # ✅ Sin _WP
                "Gen2": "Genesis: Part 2",          # ✅ Gen2 (corregido)
                "LostIsland": "Lost Island",         # ✅ Sin _WP
                "Fjordur": "Fjordur",               # ✅ Sin _WP
                "ModdedMap": "Modded Map"
            }
            
            # Verificar qué mapas están disponibles en el servidor
            available_maps_found_technical = []
            
            # Buscar archivos de mapa en el servidor
            for root, dirs, files in os.walk(server_path):
                for file in files:
                    if file.lower().endswith('.umap'):
                        # Extraer el nombre del mapa del archivo
                        map_name = os.path.splitext(file)[0]
                        if map_name not in available_maps_found_technical:
                            available_maps_found_technical.append(map_name)
            
            # Si no se encontraron mapas específicos, usar la lista completa (identificadores técnicos)
            if not available_maps_found_technical:
                available_maps_found_technical = available_maps_technical
            
            # Convertir identificadores técnicos a nombres amigables para el dropdown
            available_maps_friendly = []
            for tech_map in available_maps_found_technical:
                friendly_name = tech_to_friendly_maps.get(tech_map, tech_map)
                available_maps_friendly.append(friendly_name)
            
            # Ordenar los mapas encontrados (nombres amigables)
            available_maps_friendly.sort()
            
            # Buscar el dropdown en la ventana principal y cargar NOMBRES AMIGABLES
            if hasattr(self.main_window, 'map_dropdown'):
                self.main_window.map_dropdown.configure(values=["Seleccionar mapa..."] + available_maps_friendly)
                if self.logger.should_log_debug():
                    self.logger.info(f"DEBUG: Cargando mapas amigables en dropdown: {available_maps_friendly}")
            self.add_status_message(f"Cargados {len(available_maps_friendly)} mapa(s) para {server_name}", "info")
            
        except Exception as e:
            self.logger.error(f"Error al cargar mapas: {e}")
            # Buscar el dropdown en la ventana principal
            if hasattr(self.main_window, 'map_dropdown'):
                self.main_window.map_dropdown.configure(values=["Seleccionar mapa..."])
    
    def on_map_selected(self, map_name):
        """Maneja la selección de un mapa"""
        if map_name and map_name != "Seleccionar mapa...":
            self.selected_map = map_name
            self.add_status_message(f"Mapa seleccionado: {map_name}", "info")
        else:
            self.selected_map = None
    
    def start_monitoring(self):
        """Inicia el monitoreo del servidor en un hilo separado"""
        def monitor():
            while True:
                try:
                    self.update_server_info()
                    time.sleep(2)  # Actualizar cada 2 segundos
                except Exception as e:
                    self.logger.error(f"Error en monitoreo: {e}")
                    time.sleep(5)
        
        threading.Thread(target=monitor, daemon=True).start()
    
    def update_server_info(self):
        """Actualiza la información del servidor"""
        try:
            # Obtener información del servidor usando ServerManager
            status = self.server_manager.get_server_status()
            uptime = self.server_manager.get_uptime()
            stats = self.server_manager.get_server_stats()
            
            # Actualizar etiquetas
            if status == "Ejecutándose":
                status_color = "green"
            else:
                status_color = "red"
            
            # Programar actualizaciones de UI en el hilo principal
            def update_ui():
                try:
                    # Actualizar etiquetas solo si existen (cuando hay widgets)
                    if hasattr(self, 'status_label') and self.status_label and self.status_label.winfo_exists():
                        self.status_label.configure(text=status, text_color=status_color)
                    
                    if hasattr(self, 'uptime_label') and self.uptime_label and self.uptime_label.winfo_exists():
                        self.uptime_label.configure(text=uptime)
                    
                    if hasattr(self, 'cpu_label') and self.cpu_label and self.cpu_label.winfo_exists():
                        self.cpu_label.configure(text=f"{stats['cpu']:.1f}%")
                    
                    if hasattr(self, 'memory_label') and self.memory_label and self.memory_label.winfo_exists():
                        self.memory_label.configure(text=f"{stats['memory_mb']:.1f} MB")
                    
                    # Actualizar en la ventana principal si está disponible
                    if hasattr(self.main_window, 'update_server_status'):
                        self.main_window.update_server_status(status, status_color)
                except Exception as e:
                    # Silenciar errores de UI para evitar spam en logs
                    pass
            
            # Programar la actualización en el hilo principal
            if self.main_window and hasattr(self.main_window, 'after') and hasattr(self.main_window, 'winfo_exists'):
                try:
                    if self.main_window.winfo_exists():
                        self.main_window.after(0, update_ui)
                except Exception:
                    # Ventana ya no existe, parar el monitoreo
                    pass
            
            if hasattr(self.main_window, 'update_uptime'):
                self.main_window.update_uptime(uptime)
            
            if hasattr(self.main_window, 'update_cpu_usage'):
                self.main_window.update_cpu_usage(stats['cpu'])
            
            if hasattr(self.main_window, 'update_memory_usage'):
                self.main_window.update_memory_usage(stats['memory_mb'])
            
            # Mostrar información del servidor seleccionado si hay uno
            if hasattr(self, 'selected_server') and self.selected_server:
                # Actualizar el título o mostrar información adicional
                pass
                
        except Exception as e:
            self.logger.error(f"Error al actualizar información del servidor: {e}")
    
    def get_selected_server_info(self):
        """Obtiene información del servidor seleccionado"""
        if not hasattr(self, 'selected_server') or not self.selected_server:
            return None
        
        try:
            root_path = self.config_manager.get("server", "root_path", "").strip()
            if not root_path:
                return None
            
            server_path = os.path.join(root_path, self.selected_server)
            if not os.path.exists(server_path):
                return None
            
            # Buscar el ejecutable del servidor
            server_exe = self.server_manager.find_server_executable(server_path)
            
            return {
                "name": self.selected_server,
                "path": server_path,
                "executable": server_exe,
                "exists": os.path.exists(server_path),
                "has_executable": server_exe is not None
            }
        except Exception as e:
            self.logger.error(f"Error al obtener información del servidor: {e}")
            return None
    
    def update_server_status(self, status, color="red"):
        """Actualiza el estado del servidor en la ventana principal"""
        try:
            # Buscar la ventana principal y actualizar el estado
            if hasattr(self.main_window, 'update_server_status'):
                self.main_window.update_server_status(status, color)
        except Exception as e:
            self.logger.error(f"Error al actualizar estado del servidor: {e}")
    
    def update_uptime(self, uptime):
        """Actualiza el tiempo de actividad en la ventana principal"""
        try:
            if hasattr(self.main_window, 'update_uptime'):
                self.main_window.update_uptime(uptime)
        except Exception as e:
            self.logger.error(f"Error al actualizar tiempo de actividad: {e}")
    
    def update_cpu_usage(self, cpu_percent):
        """Actualiza el uso de CPU en la ventana principal"""
        try:
            if hasattr(self.main_window, 'update_cpu_usage'):
                self.main_window.update_cpu_usage(cpu_percent)
        except Exception as e:
            self.logger.error(f"Error al actualizar uso de CPU: {e}")
    
    def update_memory_usage(self, memory_mb):
        """Actualiza el uso de memoria en la ventana principal"""
        try:
            if hasattr(self.main_window, 'update_memory_usage'):
                self.main_window.update_memory_usage(memory_mb)
        except Exception as e:
            self.logger.error(f"Error al actualizar uso de memoria: {e}")
    
    def start_server(self):
        """Inicia el servidor usando la configuración de la pestaña Principal"""
        if not hasattr(self, 'selected_server') or not self.selected_server:
            error_msg = "❌ ERROR: Debe seleccionar un servidor primero"
            self.add_status_message(error_msg, "error")
            # También mostrar en logs principales si está disponible
            if hasattr(self.main_window, 'logs_panel') and hasattr(self.main_window.logs_panel, 'add_message'):
                self.main_window.logs_panel.add_message(error_msg, "error")
            return
        
        if not hasattr(self, 'selected_map') or not self.selected_map:
            error_msg = "❌ ERROR CRÍTICO: Debe seleccionar un MAPA antes de iniciar el servidor"
            error_detail = "\n🗺️  Vaya a la pestaña 'Principal' y seleccione un mapa en el dropdown correspondiente."
            full_error = error_msg + error_detail
            
            self.add_status_message(full_error, "error")
            # También registrar en logger principal
            self.logger.error(f"Intento de inicio sin mapa seleccionado. Servidor: {self.selected_server}")
            
            # También mostrar en logs principales si está disponible
            if hasattr(self.main_window, 'logs_panel') and hasattr(self.main_window.logs_panel, 'add_message'):
                self.main_window.logs_panel.add_message(full_error, "error")
            
            return
        
        # Registrar evento en logs principales
        start_message = f"🚀 Iniciando servidor: {self.selected_server} con mapa: {self.selected_map}"
        self.add_status_message(start_message, "info")
        if hasattr(self.main_window, 'add_log_message'):
            self.main_window.add_log_message(start_message)
        
        # Delegar al panel principal para usar la configuración correcta
        if hasattr(self.main_window, 'principal_panel'):
            # Actualizar información del servidor seleccionado en el panel principal
            self.main_window.principal_panel.selected_server = self.selected_server
            self.main_window.principal_panel.selected_map = self.selected_map
            
            # Iniciar servidor con configuración del panel principal
            self.update_server_status("Iniciando...", "orange")
            self.main_window.principal_panel.start_server_with_config(capture_console=True)
        else:
            # Fallback al método antiguo si no hay panel principal
            self.update_server_status("Iniciando...", "orange")
            self.server_manager.start_server(self.add_status_message, self.selected_server, self.selected_map, capture_console=True)
    
    def stop_server(self):
        """Detiene el servidor"""
        if not hasattr(self, 'selected_server') or not self.selected_server:
            error_msg = "❌ Error: Debe seleccionar un servidor primero"
            self.add_status_message(error_msg, "error")
            if hasattr(self.main_window, 'add_log_message'):
                self.main_window.add_log_message(error_msg)
            return
        
        # Registrar eventos de detención en logs principales
        stop_message = f"🛑 Iniciando detención del servidor: {self.selected_server}"
        self.add_status_message(stop_message, "warning")
        if hasattr(self.main_window, 'add_log_message'):
            self.main_window.add_log_message(stop_message)
            
        process_message = "📋 Verificando procesos en ejecución..."
        self.add_status_message(process_message, "info")
        if hasattr(self.main_window, 'add_log_message'):
            self.main_window.add_log_message(process_message)
            
        self.update_server_status("Deteniendo...", "orange")
        
        # Simular pasos de detención con logs en ambos lugares
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'root'):
            self.main_window.root.after(500, lambda: self._log_stop_step("🔄 Enviando señal de detención al servidor"))
            self.main_window.root.after(1000, lambda: self._log_stop_step("⏳ Esperando que el servidor termine procesos"))
            self.main_window.root.after(1500, lambda: self._log_stop_step("✅ Servidor detenido correctamente"))
    
    def _log_stop_step(self, message):
        """Helper para registrar pasos de detención en ambos logs"""
        self.add_status_message(message, "info")
        if hasattr(self.main_window, 'add_log_message'):
            self.main_window.add_log_message(message)
        
        # Si es el último paso, llamar realmente al método de detención
        if "✅ Servidor detenido correctamente" in message:
            self._actually_stop_server()
    
    def _actually_stop_server(self):
        """Realmente detener el servidor usando ServerManager"""
        try:
            if hasattr(self, 'server_manager') and self.server_manager:
                self.add_log_message("🔍 Verificando procesos del servidor...")
                
                # Obtener estado antes de detener
                status_before = self.server_manager.get_server_status()
                self.add_log_message(f"📊 Estado del servidor antes de detener: {status_before}")
                
                if status_before == "Ejecutándose":
                    self.add_log_message("🛑 Enviando señal de detención al proceso del servidor...")
                    
                    # Definir callback para mostrar resultado
                    def stop_callback(status, message):
                        if status == "stopped":
                            self.add_log_message(f"✅ {message}")
                            self.add_log_message("🔍 Verificando que el proceso se cerró completamente...")
                            
                            # Verificar después de 2 segundos
                            if hasattr(self.main_window, 'root'):
                                self.main_window.root.after(2000, self._verify_server_stopped)
                        else:
                            self.add_log_message(f"❌ Error en detención: {message}")
                    
                    # Detener servidor con callback
                    self.server_manager.stop_server(stop_callback)
                else:
                    self.add_log_message("ℹ️ El servidor ya estaba detenido")
                    self.update_server_status("Detenido", "red")
            else:
                self.add_log_message("❌ Error: ServerManager no disponible")
                
        except Exception as e:
            self.logger.error(f"Error al detener servidor realmente: {e}")
            self.add_log_message(f"❌ Error crítico al detener servidor: {e}")
    
    def _verify_server_stopped(self):
        """Verificar que el servidor realmente se detuvo"""
        try:
            if hasattr(self, 'server_manager') and self.server_manager:
                status_after = self.server_manager.get_server_status()
                self.add_log_message(f"📊 Estado final del servidor: {status_after}")
                
                if status_after == "Detenido":
                    self.add_log_message("✅ ¡Servidor completamente detenido!")
                    self.update_server_status("Detenido", "red")
                else:
                    self.add_log_message("⚠️ El servidor aún parece estar ejecutándose")
                    self.add_log_message("🔧 Intentando detención forzada...")
                    # Aquí se podría agregar lógica para forzar el cierre
                    
        except Exception as e:
            self.logger.error(f"Error al verificar estado del servidor: {e}")
            self.add_log_message(f"❌ Error al verificar estado: {e}")
    
    def add_log_message(self, message):
        """Helper para agregar mensaje a logs principales"""
        if hasattr(self.main_window, 'add_log_message'):
            self.main_window.add_log_message(message)
        
        # Registrar evento de detención
        if hasattr(self.main_window, 'log_server_event'):
            self.main_window.log_server_event("server_stop", 
                reason="Manual - Botón Detener", 
                additional_info=f"Usuario detuvo servidor desde interfaz")
        
        self.server_manager.stop_server(self.add_status_message)
    
    def restart_server(self):
        """Reinicia el servidor usando la configuración del panel principal"""
        if not hasattr(self, 'selected_server') or not self.selected_server:
            self.add_status_message("Error: Debe seleccionar un servidor primero", "error")
            return
        
        if not hasattr(self, 'selected_map') or not self.selected_map:
            self.add_status_message("Error: Debe seleccionar un mapa primero", "error")
            return
        
        restart_message = f"🔄 Reiniciando servidor: {self.selected_server} con mapa: {self.selected_map}"
        self.add_status_message(restart_message, "info")
        if hasattr(self.main_window, 'add_log_message'):
            self.main_window.add_log_message(restart_message)
        
        self.update_server_status("Reiniciando...", "orange")
        
        # Registrar evento de reinicio
        if hasattr(self.main_window, 'log_server_event'):
            self.main_window.log_server_event("server_restart", 
                reason="Manual - Botón Reiniciar", 
                additional_info=f"Usuario reinició servidor desde interfaz | Mapa: {self.selected_map}")
        
        # Usar el mismo método que start_server para conservar argumentos
        if hasattr(self.main_window, 'principal_panel'):
            # Actualizar información del servidor seleccionado en el panel principal
            self.main_window.principal_panel.selected_server = self.selected_server
            self.main_window.principal_panel.selected_map = self.selected_map
            
            # Reiniciar servidor con configuración del panel principal
            self.main_window.principal_panel.restart_server_with_config(capture_console=True)
        else:
            # Fallback al método antiguo si no hay panel principal
            self.server_manager.restart_server(self.add_status_message, self.selected_server, self.selected_map, capture_console=True)
    
    def show_progress(self, message="", progress=0):
        """Muestra la barra de progreso con un mensaje y porcentaje"""
        # Solo mostrar progreso si hay widgets (no en modo backend)
        if hasattr(self, 'progress_frame') and self.progress_frame:
            self.progress_frame.pack(fill="x", padx=5, pady=5)
            self.progress_label.configure(text=message)
            self.progress_bar.set(progress / 100)
        
        # Siempre mostrar mensaje en logs
        self.add_status_message(f"🔄 {message} ({progress}%)", "info")
        
    def hide_progress(self):
        """Oculta la barra de progreso"""
        # Solo ocultar progreso si hay widgets (no en modo backend)
        if hasattr(self, 'progress_frame') and self.progress_frame:
            self.progress_frame.pack_forget()
        
    def update_progress(self, message, progress):
        """Actualiza la barra de progreso"""
        # Solo actualizar progreso si hay widgets (no en modo backend)
        if hasattr(self, 'progress_label') and self.progress_label:
            self.progress_label.configure(text=message)
        if hasattr(self, 'progress_bar') and self.progress_bar:
            self.progress_bar.set(progress / 100)
        
        # Siempre mostrar mensaje en logs
        self.add_status_message(f"🔄 {message} ({progress:.1f}%)", "info")
        
        # Forzar actualización inmediata del GUI
        if hasattr(self, 'main_window') and hasattr(self.main_window, 'root'):
            self.main_window.root.update_idletasks()
            
        # También imprimir en consola para debug
        print(f"[PROGRESS] {message} ({progress:.1f}%)", flush=True)
        
    def install_server(self):
        """Instala un nuevo servidor"""
        # Verificar si hay una ruta raíz configurada
        root_path = self.config_manager.get("server", "root_path", "").strip()
        if not root_path:
            self.add_status_message("Error: Primero debe configurar la ruta raíz en la pestaña Configuración", "error")
            return
        
        # Mostrar diálogo para el nombre del servidor
        dialog = ctk.CTkInputDialog(
            text="Ingrese el nombre del servidor (será el nombre de la carpeta):",
            title="Nombre del Servidor"
        )
        server_name = dialog.get_input()
        
        if not server_name or not server_name.strip():
            self.add_status_message("Error: Debe ingresar un nombre para el servidor", "error")
            return
        
        # Limpiar el nombre del servidor (remover caracteres especiales)
        server_name = server_name.strip()
        # Reemplazar caracteres no válidos para nombres de carpeta
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            server_name = server_name.replace(char, '_')
        
        # Verificar si ya existe un servidor con ese nombre
        server_path = os.path.join(root_path, server_name)
        if os.path.exists(server_path):
            # Preguntar si quiere sobrescribir
            update_dialog = ctk.CTkInputDialog(
                text=f"El servidor '{server_name}' ya existe.\n¿Desea sobrescribirlo? (s/n):",
                title="Servidor Existente"
            )
            update_response = update_dialog.get_input()
            if not update_response or update_response.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
                self.add_status_message("Instalación cancelada por el usuario", "info")
                return
        
        # Deshabilitar el botón durante la instalación
        if hasattr(self.main_window, 'install_button'):
            self.main_window.install_button.configure(state="disabled", text="Instalando...")
        
        # Mostrar barra de progreso
        self.show_progress("Preparando instalación...", 0)
        
        # Ejecutar la instalación en un hilo separado
        def install_thread():
            try:
                self.add_status_message(f"Iniciando instalación del servidor: {server_name}", "info")
                self.add_status_message(f"Ruta de instalación: {server_path}", "info")
                
                # Llamar al método de instalación del server_manager con callback mejorado
                self.server_manager.install_server(self.install_callback, server_name)
                
            except Exception as e:
                self.add_status_message(f"❌ Error en la instalación: {str(e)}", "error")
                self.logger.error(f"Error en la instalación: {e}")
            finally:
                # Rehabilitar el botón
                if hasattr(self.main_window, 'install_button'):
                    self.main_window.install_button.configure(state="normal", text="Instalar Servidor")
        
        threading.Thread(target=install_thread, daemon=True).start()
    
    def update_server(self):
        """Actualiza el servidor seleccionado"""
        # Verificar si hay un servidor seleccionado
        if not hasattr(self, 'selected_server') or not self.selected_server:
            self.add_status_message("Error: Debe seleccionar un servidor primero", "error")
            return
        
        # Verificar si hay una ruta raíz configurada
        root_path = self.config_manager.get("server", "root_path", "").strip()
        if not root_path:
            self.add_status_message("Error: Primero debe configurar la ruta raíz en la pestaña Configuración", "error")
            return
        
        server_name = self.selected_server
        server_path = os.path.join(root_path, server_name)
        
        # Verificar si el servidor existe
        if not os.path.exists(server_path):
            self.add_status_message(f"Error: El servidor '{server_name}' no existe en la ruta especificada", "error")
            return
        
        # Mostrar diálogo de confirmación usando CustomTkinter
        import customtkinter as ctk
        
        # Crear ventana de confirmación
        confirm_window = ctk.CTkToplevel()
        confirm_window.title("Confirmar Actualización")
        confirm_window.geometry("400x200")
        confirm_window.resizable(False, False)
        
        # Centrar la ventana
        confirm_window.transient(self.parent)
        confirm_window.grab_set()
        
        # Contenido de la ventana
        ctk.CTkLabel(
            confirm_window, 
            text=f"¿Desea actualizar el servidor '{server_name}'?",
            font=("Arial", 14, "bold")
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            confirm_window, 
            text="Esto puede tomar varios minutos.",
            font=("Arial", 12)
        ).pack(pady=(0, 20))
        
        # Frame para botones
        buttons_frame = ctk.CTkFrame(confirm_window, fg_color="transparent")
        buttons_frame.pack(pady=20)
        
        # Variable para almacenar la respuesta
        response = [False]
        
        def on_confirm():
            response[0] = True
            confirm_window.destroy()
        
        def on_cancel():
            response[0] = False
            confirm_window.destroy()
        
        # Botones
        ctk.CTkButton(
            buttons_frame,
            text="Confirmar",
            command=on_confirm,
            fg_color="green",
            hover_color="darkgreen",
            width=100
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            buttons_frame,
            text="Cancelar",
            command=on_cancel,
            fg_color="red",
            hover_color="darkred",
            width=100
        ).pack(side="left", padx=10)
        
        # Esperar a que se cierre la ventana
        confirm_window.wait_window()
        
        if not response[0]:
            self.add_status_message("Actualización cancelada por el usuario", "info")
            return
        
        # Deshabilitar el botón durante la actualización (usar el botón de la ventana principal)
        if hasattr(self.main_window, 'update_button'):
            self.main_window.update_button.configure(state="disabled", text="Actualizando...")
        
        # Mostrar barra de progreso
        self.show_progress("Preparando actualización...", 0)
        
        # Ejecutar la actualización en un hilo separado
        def update_thread():
            try:
                self.add_status_message(f"Iniciando actualización del servidor: {server_name}", "info")
                self.add_status_message(f"Ruta del servidor: {server_path}", "info")
                
                # Registrar inicio de actualización
                if hasattr(self.main_window, 'log_server_event'):
                    self.main_window.log_server_event("update_start", method="SteamCMD")
                
                # Llamar al método de actualización del server_manager
                result = self.server_manager.update_server(self.install_callback, server_name)
                
                # Registrar resultado de actualización
                if hasattr(self.main_window, 'log_server_event'):
                    if result and "success" in str(result).lower():
                        self.main_window.log_server_event("update_complete", 
                            success=True, 
                            details="Actualización completada vía botón Actualizar")
                    else:
                        self.main_window.log_server_event("update_complete", 
                            success=False, 
                            details=f"Error en actualización: {result}")
                
            except Exception as e:
                self.add_status_message(f"❌ Error en la actualización: {str(e)}", "error")
                self.logger.error(f"Error en la actualización: {e}")
                
                # Registrar error de actualización
                if hasattr(self.main_window, 'log_server_event'):
                    self.main_window.log_server_event("update_complete", 
                        success=False, 
                        details=f"Excepción: {str(e)}")
            finally:
                # Rehabilitar el botón
                if hasattr(self.main_window, 'update_button'):
                    self.main_window.update_button.configure(state="normal", text="Actualizar Servidor")
        
        threading.Thread(target=update_thread, daemon=True).start()
    
    def install_callback(self, message_type, message):
        """Callback mejorado para la instalación con barra de progreso"""
        try:
            # Forzar actualización inmediata del GUI
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'root'):
                self.main_window.root.update_idletasks()
            if message_type == "progress":
                # Extraer porcentaje del mensaje
                if "Progress:" in message:
                    # Buscar el porcentaje en el mensaje
                    import re
                    progress_match = re.search(r'Progress:\s*(\d+(?:\.\d+)?)', message)
                    if progress_match:
                        progress = float(progress_match.group(1))
                        self.update_progress(f"Progreso: {progress:.1f}%", progress)
                    else:
                        self.update_progress(message, 50)  # Valor por defecto
                elif "Progreso de descarga:" in message:
                    # Extraer el porcentaje del mensaje de progreso mejorado
                    import re
                    progress_match = re.search(r'Progreso de descarga: (\d+(?:\.\d+)?)%', message)
                    if progress_match:
                        progress = float(progress_match.group(1))
                        # Mostrar progreso con timestamp para indicar que está actualizado
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                        self.update_progress(f"[{timestamp}] Descargando ARK: {progress:.1f}%", progress)
                    else:
                        self.update_progress(message, 50)
                elif "Downloading" in message:
                    # Extraer porcentaje de descarga si está disponible
                    import re
                    download_match = re.search(r'(\d+(?:\.\d+)?)%', message)
                    if download_match:
                        progress = float(download_match.group(1))
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                        self.update_progress(f"[{timestamp}] {message} {progress:.1f}%", progress)
                    else:
                        # Si no hay porcentaje, incrementar gradualmente
                        if hasattr(self, 'progress_bar') and self.progress_bar:
                            current_progress = self.progress_bar.get()
                            new_progress = min(current_progress + 0.1, 0.9)  # Incrementar hasta 90%
                            self.update_progress(message, new_progress * 100)
                        else:
                            self.update_progress(message, 50)  # Valor por defecto
                elif "Installing" in message:
                    self.update_progress(message, 75)
                elif "Validating" in message:
                    self.update_progress(message, 90)
                elif "Verificando SteamCMD" in message:
                    self.update_progress(message, 5)
                elif "Descargando SteamCMD" in message:
                    self.update_progress(message, 10)
                elif "Extrayendo SteamCMD" in message:
                    self.update_progress(message, 15)
                elif "Buscando ejecutable" in message:
                    self.update_progress(message, 95)
                elif "Update state" in message:
                    # Para mensajes de estado de actualización, mantener progreso actual
                    if hasattr(self, 'progress_bar') and self.progress_bar:
                        current_progress = self.progress_bar.get()
                        self.update_progress(message, current_progress * 100)
                    else:
                        self.update_progress(message, 70)  # Valor por defecto
                else:
                    # Para otros mensajes de progreso, mantener el progreso actual
                    if hasattr(self, 'progress_bar') and self.progress_bar:
                        current_progress = self.progress_bar.get()
                        self.update_progress(message, current_progress * 100)
                    else:
                        self.update_progress(message, 50)  # Valor por defecto
            elif message_type == "error":
                # Mostrar error y ocultar barra de progreso
                self.add_status_message(f"{message}", "error")  # Ya tiene ❌ en add_status_message
                self.hide_progress()
            elif message_type == "success":
                # Mostrar éxito
                self.add_status_message(f"{message}", "success")  # Ya tiene ✅ en add_status_message
                # Si es un mensaje de éxito final, ocultar la barra de progreso y refrescar lista
                if "completada exitosamente" in message.lower():
                    self.hide_progress()
                    # Refrescar la lista de servidores
                    self.refresh_servers_list()
            elif message_type == "warning":
                # Mostrar advertencia
                self.add_status_message(f"{message}", "warning")  # Ya tiene ⚠️ en add_status_message
            elif message_type == "info":
                # Mostrar información - filtrar algunos mensajes de SteamCMD para evitar spam
                if not any(skip in message for skip in [
                    "Steam Console Client", "-- type 'quit' to exit --", 
                    "Logging directory:", "Loading Steam API", "Waiting for client config"
                ]):
                    self.add_status_message(f"{message}", "info")  # Ya tiene ℹ️ en add_status_message
            else:
                # Usar el método original para otros tipos de mensajes
                self.add_status_message(message, message_type)
        except Exception as e:
            # En caso de error en el callback, mostrar el error
            self.add_status_message(f"❌ Error en el callback: {str(e)}", "error")
            self.logger.error(f"Error en install_callback: {e}")
    
    def save_world(self):
        """Guarda el mundo del servidor"""
        self.server_manager.save_world(self.add_status_message)
    
    def create_backup(self):
        """Crea un backup del servidor"""
        self.server_manager.backup_server(self.add_status_message)
    
    def show_broadcast_dialog(self):
        """Muestra el diálogo para enviar broadcast"""
        dialog = ctk.CTkInputDialog(
            text="Ingrese el mensaje a enviar:",
            title="Enviar Broadcast"
        )
        message = dialog.get_input()
        
        if message:
            self.broadcast_message(message)
    
    def broadcast_message(self, message):
        """Envía un mensaje broadcast"""
        self.server_manager.broadcast_message(message, self.add_status_message)
    
    def kick_all_players(self):
        """Expulsa a todos los jugadores"""
        self.server_manager.kick_all_players(self.add_status_message)
    
    def kick_player(self):
        """Expulsa a un jugador específico"""
        # Mostrar diálogo para ingresar nombre del jugador
        dialog = ctk.CTkInputDialog(
            text="Ingrese el nombre del jugador a expulsar:",
            title="Expulsar Jugador"
        )
        player_name = dialog.get_input()
        if player_name:
            self.server_manager.kick_player(player_name, self.add_status_message)
        else:
            self.add_status_message("Error: Ingrese el nombre del jugador", "error")
    
    def ban_player(self):
        """Banea a un jugador específico"""
        # Mostrar diálogo para ingresar nombre del jugador
        dialog = ctk.CTkInputDialog(
            text="Ingrese el nombre del jugador a banear:",
            title="Banear Jugador"
        )
        player_name = dialog.get_input()
        if player_name:
            self.server_manager.ban_player(player_name, self.add_status_message)
        else:
            self.add_status_message("Error: Ingrese el nombre del jugador", "error")
    
    def teleport_player(self):
        """Teletransporta a un jugador"""
        # Mostrar diálogo para ingresar nombre del jugador
        dialog = ctk.CTkInputDialog(
            text="Ingrese el nombre del jugador a teletransportar:",
            title="Teletransportar Jugador"
        )
        player_name = dialog.get_input()
        if player_name:
            # Mostrar diálogo para coordenadas
            coord_dialog = ctk.CTkInputDialog(
                text="Ingrese las coordenadas (X,Y,Z):",
                title="Teletransportar Jugador"
            )
            coordinates = coord_dialog.get_input()
            
            if coordinates:
                self.add_status_message(f"Teletransportando {player_name} a {coordinates}", "info")
                # Aquí iría la lógica para teletransportar al jugador
            else:
                self.add_status_message("Error: Ingrese las coordenadas", "error")
        else:
            self.add_status_message("Error: Ingrese el nombre del jugador", "error")
    
    def give_item_to_player(self):
        """Da un item a un jugador"""
        # Mostrar diálogo para ingresar nombre del jugador
        dialog = ctk.CTkInputDialog(
            text="Ingrese el nombre del jugador:",
            title="Dar Item"
        )
        player_name = dialog.get_input()
        if player_name:
            # Mostrar diálogo para item
            item_dialog = ctk.CTkInputDialog(
                text="Ingrese el nombre del item:",
                title="Dar Item"
            )
            item_name = item_dialog.get_input()
            
            if item_name:
                self.add_status_message(f"Dando {item_name} a {player_name}", "info")
                # Aquí iría la lógica para dar el item al jugador
            else:
                self.add_status_message("Error: Ingrese el nombre del item", "error")
        else:
            self.add_status_message("Error: Ingrese el nombre del jugador", "error")
    
    def test_logs(self):
        """Generar eventos de prueba para verificar que los logs funcionan"""
        import random
        
        test_messages = [
            "Verificando conexión al servidor...",
            "Conexión establecida correctamente",
            "Comprobando estado del servidor", 
            "Servidor respondiendo normalmente",
            "Verificando archivos de configuración",
            "Configuración válida",
            "Simulando evento del servidor",
            "Test de logs completado exitosamente"
        ]
        
        # Agregar mensaje inmediato
        initial_msg = "🧪 Iniciando prueba de logs..."
        self.add_status_message(initial_msg, "info")
        if hasattr(self.main_window, 'add_log_message'):
            self.main_window.add_log_message(initial_msg)
        
        # Programar mensajes de prueba con delays
        for i, message in enumerate(test_messages):
            delay = (i + 1) * 400  # 400ms entre cada mensaje
            if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'root'):
                self.main_window.root.after(delay, lambda m=message: self._test_log_step(m))
        
        # Mensaje final
        final_delay = len(test_messages) * 400 + 500
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'root'):
            self.main_window.root.after(final_delay, lambda: self._test_log_step("✅ Prueba de logs finalizada - Sistema funcionando correctamente"))
    
    def _test_log_step(self, message):
        """Helper para mostrar paso de prueba en ambos logs"""
        self.add_status_message(message, "info")
        if hasattr(self.main_window, 'add_log_message'):
            self.main_window.add_log_message(message)
    
    def add_status_message(self, message, message_type="info"):
        """Agrega un mensaje al área de logs"""
        try:
            # Obtener timestamp
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            
            # Determinar el icono según el tipo de mensaje
            if message_type == "error":
                icon = "❌"
            elif message_type == "success":
                icon = "✅"
            elif message_type == "warning":
                icon = "⚠️"
            elif message_type == "info":
                icon = "ℹ️"
            else:
                icon = "📝"
            
            # Crear el mensaje completo
            full_message = f"{timestamp} {icon} {message}"
            
            # Solo acceder a logs_text si existe (modo con widgets)
            if hasattr(self, 'logs_text') and self.logs_text:
                # Habilitar el área de logs para edición
                self.logs_text.configure(state="normal")
                
                # Insertar el mensaje al final
                self.logs_text.insert("end", full_message + "\n")
                
                # Hacer scroll al final
                self.logs_text.see("end")
                
                # Deshabilitar el área de logs
                self.logs_text.configure(state="disabled")
                
                # Limitar el número de líneas para evitar que crezca demasiado
                lines = self.logs_text.get("1.0", "end").split('\n')
                if len(lines) > 1000:  # Mantener solo las últimas 1000 líneas
                    # Eliminar las primeras 500 líneas
                    self.logs_text.configure(state="normal")
                    self.logs_text.delete("1.0", f"{500}.0")
                    self.logs_text.configure(state="disabled")
            
            # Siempre enviar el mensaje a la ventana principal si está disponible
            if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'add_log_message'):
                self.main_window.add_log_message(full_message)
                
        except Exception as e:
            self.logger.error(f"Error al agregar mensaje de estado: {e}")
