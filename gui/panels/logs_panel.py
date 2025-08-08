import customtkinter as ctk
import os
import threading
import time
from datetime import datetime
from tkinter import filedialog

class LogsPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.log_files = []
        self.current_log_file = None
        self.monitoring_active = False
        
        self.create_widgets()
        self.load_log_files()
        
    def create_widgets(self):
        """Crear todos los widgets del panel"""
        # Configurar el grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        
        # Título
        title_label = ctk.CTkLabel(
            self, 
            text="Gestión de Logs", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 15))
        
        # Frame para acceso rápido a logs del servidor
        server_logs_frame = ctk.CTkFrame(self)
        server_logs_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        server_logs_label = ctk.CTkLabel(
            server_logs_frame, 
            text="Logs del Servidor ARK", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        server_logs_label.pack(pady=5)
        
        # Frame para botones de logs rápidos
        quick_logs_frame = ctk.CTkFrame(server_logs_frame, fg_color="transparent")
        quick_logs_frame.pack(fill="x", padx=10, pady=5)
        
        # Botones para logs comunes
        ctk.CTkButton(
            quick_logs_frame,
            text="Log de Chat",
            command=self.view_chat_log,
            width=120,
            height=30
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            quick_logs_frame,
            text="Log de Errores",
            command=self.view_error_log,
            width=120,
            height=30
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            quick_logs_frame,
            text="Log del Servidor",
            command=self.view_server_log,
            width=120,
            height=30
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            quick_logs_frame,
            text="Actualizar",
            command=self.refresh_server_logs,
            width=100,
            height=30,
            fg_color="orange",
            hover_color="darkorange"
        ).pack(side="left", padx=5)
        
        # Frame de configuración de logs
        config_frame = ctk.CTkFrame(self)
        config_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        config_label = ctk.CTkLabel(
            config_frame, 
            text="Configuración de Logs", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        config_label.grid(row=0, column=0, columnspan=3, pady=5)
        
        # Ruta de logs
        logs_path_label = ctk.CTkLabel(config_frame, text="Ruta de logs:")
        logs_path_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.logs_path_entry = ctk.CTkEntry(config_frame, width=400)
        self.logs_path_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        logs_browse_button = ctk.CTkButton(
            config_frame,
            text="Buscar",
            command=self.browse_logs_path,
            width=80
        )
        logs_browse_button.grid(row=1, column=2, padx=5, pady=5)
        
        # Filtro de logs
        filter_label = ctk.CTkLabel(config_frame, text="Filtro:")
        filter_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.filter_entry = ctk.CTkEntry(config_frame, placeholder_text="Filtrar logs...")
        self.filter_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        apply_filter_button = ctk.CTkButton(
            config_frame,
            text="Aplicar",
            command=self.apply_filter,
            width=80
        )
        apply_filter_button.grid(row=2, column=2, padx=5, pady=5)
        
        # Frame de archivos de log
        files_frame = ctk.CTkFrame(self)
        files_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        files_label = ctk.CTkLabel(
            files_frame, 
            text="Archivos de Log", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        files_label.grid(row=0, column=0, pady=10)
        
        # Lista de archivos de log
        self.log_files_listbox = ctk.CTkTextbox(files_frame, height=300)
        self.log_files_listbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Botones para archivos
        refresh_files_button = ctk.CTkButton(
            files_frame,
            text="Actualizar Lista",
            command=self.load_log_files
        )
        refresh_files_button.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        delete_log_button = ctk.CTkButton(
            files_frame,
            text="Eliminar Log",
            command=self.delete_log_file,
            fg_color="red",
            hover_color="darkred"
        )
        delete_log_button.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        # Frame de visualización de logs
        viewer_frame = ctk.CTkFrame(self)
        viewer_frame.grid(row=2, column=1, padx=20, pady=10, sticky="nsew")
        
        viewer_label = ctk.CTkLabel(
            viewer_frame, 
            text="Visor de Logs", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        viewer_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Área de visualización de logs
        self.log_viewer = ctk.CTkTextbox(viewer_frame, height=300)
        self.log_viewer.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        # Controles del visor
        self.start_monitoring_button = ctk.CTkButton(
            viewer_frame,
            text="Iniciar Monitoreo",
            command=self.start_monitoring,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.start_monitoring_button.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        
        self.stop_monitoring_button = ctk.CTkButton(
            viewer_frame,
            text="Detener Monitoreo",
            command=self.stop_monitoring,
            fg_color="red",
            hover_color="darkred"
        )
        self.stop_monitoring_button.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        # Frame de estadísticas
        stats_frame = ctk.CTkFrame(self)
        stats_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        stats_label = ctk.CTkLabel(
            stats_frame, 
            text="Estadísticas de Logs", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        stats_label.grid(row=0, column=0, columnspan=4, pady=10)
        
        # Estadísticas
        self.total_logs_label = ctk.CTkLabel(stats_frame, text="Total de archivos: 0")
        self.total_logs_label.grid(row=1, column=0, padx=20, pady=5)
        
        self.total_size_label = ctk.CTkLabel(stats_frame, text="Tamaño total: 0 MB")
        self.total_size_label.grid(row=1, column=1, padx=20, pady=5)
        
        self.last_modified_label = ctk.CTkLabel(stats_frame, text="Última modificación: --")
        self.last_modified_label.grid(row=1, column=2, padx=20, pady=5)
        
        self.monitoring_status_label = ctk.CTkLabel(stats_frame, text="Monitoreo: Detenido")
        self.monitoring_status_label.grid(row=1, column=3, padx=20, pady=5)
        
        # Configurar grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        config_frame.grid_columnconfigure(1, weight=1)
        files_frame.grid_columnconfigure(0, weight=1)
        files_frame.grid_rowconfigure(1, weight=1)
        viewer_frame.grid_columnconfigure(0, weight=1)
        viewer_frame.grid_columnconfigure(1, weight=1)
        viewer_frame.grid_rowconfigure(1, weight=1)
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        stats_frame.grid_columnconfigure(2, weight=1)
        stats_frame.grid_columnconfigure(3, weight=1)
        
    def browse_logs_path(self):
        """Buscar directorio de logs"""
        directory = filedialog.askdirectory(title="Seleccionar directorio de logs")
        if directory:
            self.logs_path_entry.delete(0, "end")
            self.logs_path_entry.insert(0, directory)
            self.load_log_files()
    
    def load_log_files(self):
        """Cargar lista de archivos de log"""
        try:
            logs_path = self.logs_path_entry.get()
            if not logs_path or not os.path.exists(logs_path):
                self.log_files_listbox.delete("1.0", "end")
                self.log_files_listbox.insert("1.0", "No hay archivos de log disponibles")
                return
            
            # Buscar archivos de log
            self.log_files = []
            total_size = 0
            last_modified = None
            
            for file in os.listdir(logs_path):
                if file.endswith(('.log', '.txt')) or 'log' in file.lower():
                    file_path = os.path.join(logs_path, file)
                    try:
                        stat = os.stat(file_path)
                        size_mb = stat.st_size / (1024 * 1024)
                        total_size += size_mb
                        
                        file_info = {
                            "name": file,
                            "path": file_path,
                            "size": size_mb,
                            "modified": datetime.fromtimestamp(stat.st_mtime)
                        }
                        
                        if last_modified is None or file_info["modified"] > last_modified:
                            last_modified = file_info["modified"]
                        
                        self.log_files.append(file_info)
                        
                    except Exception as e:
                        self.logger.error(f"Error al obtener información del archivo {file}: {e}")
            
            # Ordenar por fecha de modificación (más reciente primero)
            self.log_files.sort(key=lambda x: x["modified"], reverse=True)
            
            # Actualizar lista
            self.log_files_listbox.delete("1.0", "end")
            if self.log_files:
                for log_file in self.log_files:
                    date_str = log_file["modified"].strftime("%Y-%m-%d %H:%M")
                    self.log_files_listbox.insert("end", 
                        f"{log_file['name']:<30} {date_str:<20} {log_file['size']:.1f}MB\n")
            else:
                self.log_files_listbox.insert("1.0", "No hay archivos de log disponibles")
            
            # Actualizar estadísticas
            self.total_logs_label.configure(text=f"Total de archivos: {len(self.log_files)}")
            self.total_size_label.configure(text=f"Tamaño total: {total_size:.1f}MB")
            
            if last_modified:
                last_modified_str = last_modified.strftime("%Y-%m-%d %H:%M")
                self.last_modified_label.configure(text=f"Última modificación: {last_modified_str}")
            else:
                self.last_modified_label.configure(text="Última modificación: --")
                
        except Exception as e:
            self.logger.error(f"Error al cargar archivos de log: {e}")
    
    def apply_filter(self):
        """Aplicar filtro a los logs"""
        try:
            filter_text = self.filter_entry.get().lower()
            if not filter_text:
                self.load_log_files()
                return
            
            # Filtrar archivos que contengan el texto
            filtered_files = [f for f in self.log_files if filter_text in f["name"].lower()]
            
            # Actualizar lista filtrada
            self.log_files_listbox.delete("1.0", "end")
            if filtered_files:
                for log_file in filtered_files:
                    date_str = log_file["modified"].strftime("%Y-%m-%d %H:%M")
                    self.log_files_listbox.insert("end", 
                        f"{log_file['name']:<30} {date_str:<20} {log_file['size']:.1f}MB\n")
            else:
                self.log_files_listbox.insert("1.0", "No se encontraron archivos que coincidan con el filtro")
                
        except Exception as e:
            self.logger.error(f"Error al aplicar filtro: {e}")
    
    def start_monitoring(self):
        """Iniciar monitoreo de logs"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.start_monitoring_button.configure(state="disabled")
            self.stop_monitoring_button.configure(state="normal")
            self.monitoring_status_label.configure(text="Monitoreo: Activo", text_color="green")
            
            # Iniciar hilo de monitoreo
            threading.Thread(target=self.monitoring_loop, daemon=True).start()
            self.logger.info("Monitoreo de logs iniciado")
    
    def stop_monitoring(self):
        """Detener monitoreo de logs"""
        self.monitoring_active = False
        self.start_monitoring_button.configure(state="normal")
        self.stop_monitoring_button.configure(state="disabled")
        self.monitoring_status_label.configure(text="Monitoreo: Detenido", text_color="red")
        self.logger.info("Monitoreo de logs detenido")
    
    def monitoring_loop(self):
        """Bucle principal de monitoreo de logs"""
        while self.monitoring_active:
            try:
                # Buscar el archivo de log más reciente
                if self.log_files:
                    latest_log = self.log_files[0]["path"]
                    self.load_log_content(latest_log)
                
                time.sleep(2)  # Actualizar cada 2 segundos
            except Exception as e:
                self.logger.error(f"Error en monitoreo de logs: {e}")
                break
    
    def load_log_content(self, log_file_path):
        """Cargar contenido del archivo de log"""
        try:
            if not os.path.exists(log_file_path):
                return
            
            # Leer las últimas líneas del archivo
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            # Mostrar las últimas 100 líneas
            recent_lines = lines[-100:] if len(lines) > 100 else lines
            
            # Actualizar visor
            self.log_viewer.delete("1.0", "end")
            for line in recent_lines:
                self.log_viewer.insert("end", line)
            
            # Scroll al final
            self.log_viewer.see("end")
            
        except Exception as e:
            self.logger.error(f"Error al cargar contenido del log: {e}")
    
    def delete_log_file(self):
        """Eliminar archivo de log seleccionado"""
        try:
            # Obtener archivo seleccionado (implementación simplificada)
            if not self.log_files:
                self.logger.warning("No hay archivos de log disponibles para eliminar")
                return
            
            # Aquí se implementaría la lógica para eliminar el archivo seleccionado
            self.logger.info("Función de eliminación de archivo de log (a implementar)")
            
        except Exception as e:
            self.logger.error(f"Error al eliminar archivo de log: {e}")
    
    def view_chat_log(self):
        """Ver logs de chat del servidor"""
        try:
            server_path = self.get_current_server_path()
            if not server_path:
                self.add_log_message("❌ No hay servidor seleccionado o ruta no configurada")
                self.show_demo_chat_log()
                return
            
            self.add_log_message(f"🔍 Buscando logs de chat en: {server_path}")
            
            # Rutas comunes para logs de chat en ARK
            possible_chat_logs = [
                os.path.join(server_path, "ShooterGame", "Saved", "Logs", "chat.log"),
                os.path.join(server_path, "ShooterGame", "Logs", "chat.log"),
                os.path.join(server_path, "Logs", "chat.log")
            ]
            
            chat_log_found = None
            for log_path in possible_chat_logs:
                self.add_log_message(f"🔍 Verificando: {log_path}")
                if os.path.exists(log_path):
                    chat_log_found = log_path
                    break
            
            if chat_log_found:
                self.load_log_content(chat_log_found)
                self.add_log_message(f"✅ Cargado log de chat: {chat_log_found}")
            else:
                self.add_log_message("⚠️ No se encontró archivo de log de chat")
                self.show_demo_chat_log()
                
        except Exception as e:
            self.logger.error(f"Error al cargar log de chat: {e}")
            self.add_log_message(f"❌ Error al cargar log de chat: {str(e)}")
            self.show_demo_chat_log()
    
    def view_error_log(self):
        """Ver logs de errores del servidor"""
        try:
            server_path = self.get_current_server_path()
            if not server_path:
                self.add_log_message("❌ No hay servidor seleccionado o ruta no configurada")
                self.show_demo_error_log()
                return
            
            self.add_log_message(f"🔍 Buscando logs de errores en: {server_path}")
            
            # Rutas comunes para logs de errores en ARK
            possible_error_logs = [
                os.path.join(server_path, "ShooterGame", "Saved", "Logs", "ShooterGame.log"),
                os.path.join(server_path, "ShooterGame", "Logs", "error.log"),
                os.path.join(server_path, "Logs", "error.log")
            ]
            
            error_log_found = None
            for log_path in possible_error_logs:
                self.add_log_message(f"🔍 Verificando: {log_path}")
                if os.path.exists(log_path):
                    error_log_found = log_path
                    break
            
            if error_log_found:
                self.load_log_content(error_log_found)
                self.add_log_message(f"✅ Cargado log de errores: {error_log_found}")
            else:
                self.add_log_message("⚠️ No se encontró archivo de log de errores")
                self.show_demo_error_log()
                
        except Exception as e:
            self.logger.error(f"Error al cargar log de errores: {e}")
            self.add_log_message(f"❌ Error al cargar log de errores: {str(e)}")
            self.show_demo_error_log()
    
    def view_server_log(self):
        """Ver logs principales del servidor"""
        try:
            server_path = self.get_current_server_path()
            if not server_path:
                self.add_log_message("❌ No hay servidor seleccionado o ruta no configurada")
                self.show_demo_server_log()
                return
            
            self.add_log_message(f"🔍 Buscando logs del servidor en: {server_path}")
            
            # Rutas comunes para logs principales en ARK
            possible_server_logs = [
                os.path.join(server_path, "ShooterGame", "Saved", "Logs", "ShooterGame.log"),
                os.path.join(server_path, "Logs", "server.log"),
                os.path.join(server_path, "ShooterGame", "Logs", "ShooterGame.log")
            ]
            
            server_log_found = None
            for log_path in possible_server_logs:
                self.add_log_message(f"🔍 Verificando: {log_path}")
                if os.path.exists(log_path):
                    server_log_found = log_path
                    break
            
            if server_log_found:
                self.load_log_content(server_log_found)
                self.add_log_message(f"✅ Cargado log del servidor: {server_log_found}")
            else:
                self.add_log_message("⚠️ No se encontró archivo de log del servidor")
                self.show_demo_server_log()
                
        except Exception as e:
            self.logger.error(f"Error al cargar log del servidor: {e}")
            self.add_log_message(f"❌ Error al cargar log del servidor: {str(e)}")
            self.show_demo_server_log()
    
    def refresh_server_logs(self):
        """Actualizar la lista de logs del servidor"""
        try:
            server_path = self.get_current_server_path()
            if not server_path:
                self.add_log_message("❌ No hay servidor seleccionado o ruta no configurada")
                return
            
            # Buscar todos los archivos de log disponibles
            log_dirs = [
                os.path.join(server_path, "ShooterGame", "Saved", "Logs"),
                os.path.join(server_path, "ShooterGame", "Logs"),
                os.path.join(server_path, "Logs")
            ]
            
            found_logs = []
            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    for file in os.listdir(log_dir):
                        if file.endswith('.log'):
                            found_logs.append(os.path.join(log_dir, file))
            
            if found_logs:
                log_list = "\n".join([f"📄 {os.path.basename(log)}" for log in found_logs[:10]])  # Mostrar solo los primeros 10
                self.add_log_message(f"✅ Logs encontrados ({len(found_logs)} total):\n{log_list}")
            else:
                self.add_log_message("⚠️ No se encontraron archivos de log")
                
        except Exception as e:
            self.logger.error(f"Error al buscar logs: {e}")
            self.add_log_message(f"❌ Error al buscar logs: {str(e)}")
    
    def get_current_server_path(self):
        """Obtener la ruta del servidor actualmente seleccionado"""
        try:
            root_path = self.config_manager.get("server", "root_path", "").strip()
            if not root_path:
                return None
            
            # Buscar el primer servidor válido disponible
            for item in os.listdir(root_path):
                item_path = os.path.join(root_path, item)
                if os.path.isdir(item_path) and item != "SteamCMD":
                    # Verificar si es un directorio de servidor válido
                    if any(os.path.exists(os.path.join(item_path, subdir)) 
                           for subdir in ["ShooterGame", "Logs"]):
                        return item_path
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error al obtener ruta del servidor: {e}")
            return None
    
    def add_log_message(self, message):
        """Agregar mensaje al área de logs"""
        try:
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            full_message = f"{timestamp} {message}\n"
            
            if hasattr(self, 'log_viewer'):
                self.log_viewer.configure(state="normal")
                self.log_viewer.insert("end", full_message)
                self.log_viewer.see("end")
                self.log_viewer.configure(state="disabled")
                
        except Exception as e:
            self.logger.error(f"Error al agregar mensaje de log: {e}")
    
    def show_demo_chat_log(self):
        """Mostrar contenido demo de log de chat"""
        try:
            demo_content = """=== LOG DE CHAT DEL SERVIDOR ARK ===
[2025-01-08 19:05:12] [CHAT] Jugador1: Hola a todos!
[2025-01-08 19:05:45] [CHAT] Jugador2: ¿Alguien quiere hacer una tribu?
[2025-01-08 19:06:20] [CONNECT] Jugador3 se ha conectado al servidor
[2025-01-08 19:06:55] [CHAT] Jugador3: ¡Hola! Soy nuevo
[2025-01-08 19:07:30] [ADMIN] Administrador: Bienvenido al servidor!
[2025-01-08 19:08:15] [CHAT] Jugador1: Te ayudo a empezar
[2025-01-08 19:09:00] [DISCONNECT] Jugador2 se ha desconectado
[2025-01-08 19:09:30] [CHAT] Jugador3: Gracias por la ayuda!

=== ESTE ES CONTENIDO DE DEMOSTRACIÓN ===
Para ver logs reales, asegúrate de:
1. Tener un servidor instalado
2. Que el servidor haya sido ejecutado al menos una vez
3. Que los jugadores hayan enviado mensajes de chat
"""
            
            if hasattr(self, 'log_viewer'):
                self.log_viewer.configure(state="normal")
                self.log_viewer.delete("1.0", "end")
                self.log_viewer.insert("1.0", demo_content)
                self.log_viewer.configure(state="disabled")
                
        except Exception as e:
            self.logger.error(f"Error al mostrar demo de chat: {e}")
    
    def show_demo_error_log(self):
        """Mostrar contenido demo de log de errores"""
        try:
            demo_content = """=== LOG DE ERRORES DEL SERVIDOR ARK ===
[2025-01-08 19:00:12] [ERROR] Failed to load mod: ModID 123456789
[2025-01-08 19:00:45] [WARNING] High memory usage detected: 85%
[2025-01-08 19:01:20] [ERROR] Connection timeout for player: SteamID64_12345
[2025-01-08 19:01:55] [WARNING] Server performance degraded
[2025-01-08 19:02:30] [ERROR] Database query failed: timeout
[2025-01-08 19:03:15] [INFO] Automatic restart scheduled in 30 minutes
[2025-01-08 19:04:00] [ERROR] Asset loading failed: map_texture_001
[2025-01-08 19:04:30] [WARNING] Disk space low: 15% remaining

=== ESTE ES CONTENIDO DE DEMOSTRACIÓN ===
Para ver logs reales de errores:
1. Ejecuta el servidor con configuración de logs habilitada
2. Los errores aparecerán automáticamente aquí
3. Revisa regularmente para mantener el servidor estable
"""
            
            if hasattr(self, 'log_viewer'):
                self.log_viewer.configure(state="normal")
                self.log_viewer.delete("1.0", "end")
                self.log_viewer.insert("1.0", demo_content)
                self.log_viewer.configure(state="disabled")
                
        except Exception as e:
            self.logger.error(f"Error al mostrar demo de errores: {e}")
    
    def show_demo_server_log(self):
        """Mostrar contenido demo de log del servidor"""
        try:
            demo_content = """=== LOG PRINCIPAL DEL SERVIDOR ARK ===
[2025-01-08 19:00:00] [INFO] Server starting up...
[2025-01-08 19:00:15] [INFO] Loading map: TheIsland_WP
[2025-01-08 19:00:30] [INFO] Loading game mode: Survival
[2025-01-08 19:00:45] [INFO] Loading mods: 3 mods found
[2025-01-08 19:01:00] [INFO] Mod loaded: S+ (731604991)
[2025-01-08 19:01:15] [INFO] Mod loaded: Awesome Spyglass (793605978)
[2025-01-08 19:01:30] [INFO] Server ready for connections
[2025-01-08 19:01:45] [INFO] Listening on port: 7777
[2025-01-08 19:02:00] [INFO] Query port: 27015
[2025-01-08 19:02:15] [INFO] Max players: 20
[2025-01-08 19:02:30] [INFO] PvE mode enabled
[2025-01-08 19:03:00] [INFO] Auto-save interval: 15 minutes

=== ESTE ES CONTENIDO DE DEMOSTRACIÓN ===
Este log contiene información general del servidor:
- Inicialización y configuración
- Estados de conexión
- Información de mods
- Eventos del sistema
"""
            
            if hasattr(self, 'log_viewer'):
                self.log_viewer.configure(state="normal")
                self.log_viewer.delete("1.0", "end")
                self.log_viewer.insert("1.0", demo_content)
                self.log_viewer.configure(state="disabled")
                
        except Exception as e:
            self.logger.error(f"Error al mostrar demo del servidor: {e}")
