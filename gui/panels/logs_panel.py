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
        # Título
        title_label = ctk.CTkLabel(
            self, 
            text="Gestión de Logs", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(20, 30))
        
        # Frame de configuración de logs
        config_frame = ctk.CTkFrame(self)
        config_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        config_label = ctk.CTkLabel(
            config_frame, 
            text="Configuración de Logs", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        config_label.grid(row=0, column=0, columnspan=3, pady=10)
        
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
