import customtkinter as ctk
import os
import shutil
import threading
import time
from datetime import datetime
from tkinter import filedialog

class BackupPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.backups = []
        self.backup_running = False
        
        self.create_widgets()
        self.load_backups()
        
    def create_widgets(self):
        """Crear todos los widgets del panel"""
        # Título
        title_label = ctk.CTkLabel(
            self, 
            text="Gestión de Backups", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(20, 30))
        
        # Frame de configuración de backups
        config_frame = ctk.CTkFrame(self)
        config_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        config_label = ctk.CTkLabel(
            config_frame, 
            text="Configuración de Backups", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        config_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Ruta de origen
        source_label = ctk.CTkLabel(config_frame, text="Ruta de origen:")
        source_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.source_entry = ctk.CTkEntry(config_frame, width=300)
        self.source_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        source_browse_button = ctk.CTkButton(
            config_frame,
            text="Buscar",
            command=self.browse_source_path,
            width=80
        )
        source_browse_button.grid(row=1, column=2, padx=5, pady=5)
        
        # Ruta de destino
        destination_label = ctk.CTkLabel(config_frame, text="Ruta de destino:")
        destination_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.destination_entry = ctk.CTkEntry(config_frame, width=300)
        self.destination_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        dest_browse_button = ctk.CTkButton(
            config_frame,
            text="Buscar",
            command=self.browse_destination_path,
            width=80
        )
        dest_browse_button.grid(row=2, column=2, padx=5, pady=5)
        
        # Frecuencia de backup
        frequency_label = ctk.CTkLabel(config_frame, text="Frecuencia (horas):")
        frequency_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        
        self.frequency_entry = ctk.CTkEntry(config_frame, placeholder_text="24")
        self.frequency_entry.grid(row=3, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        self.frequency_entry.insert(0, "24")
        
        # Retener backups
        retain_label = ctk.CTkLabel(config_frame, text="Retener backups:")
        retain_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        
        self.retain_entry = ctk.CTkEntry(config_frame, placeholder_text="7")
        self.retain_entry.grid(row=4, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        self.retain_entry.insert(0, "7")
        
        # Frame de controles de backup
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=1, column=1, padx=20, pady=10, sticky="nsew")
        
        controls_label = ctk.CTkLabel(
            controls_frame, 
            text="Controles de Backup", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        controls_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Botones de control
        self.create_backup_button = ctk.CTkButton(
            controls_frame,
            text="Crear Backup Manual",
            command=self.create_manual_backup,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.create_backup_button.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        self.start_auto_backup_button = ctk.CTkButton(
            controls_frame,
            text="Iniciar Backup Automático",
            command=self.start_auto_backup,
            fg_color="blue",
            hover_color="darkblue"
        )
        self.start_auto_backup_button.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        self.stop_auto_backup_button = ctk.CTkButton(
            controls_frame,
            text="Detener Backup Automático",
            command=self.stop_auto_backup,
            fg_color="red",
            hover_color="darkred"
        )
        self.stop_auto_backup_button.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        # Estado del backup automático
        self.auto_backup_status_label = ctk.CTkLabel(controls_frame, text="Estado: Detenido", text_color="red")
        self.auto_backup_status_label.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
        
        # Próximo backup
        self.next_backup_label = ctk.CTkLabel(controls_frame, text="Próximo backup: --")
        self.next_backup_label.grid(row=5, column=0, columnspan=2, padx=10, pady=5)
        
        # Frame de lista de backups
        backups_frame = ctk.CTkFrame(self)
        backups_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        backups_label = ctk.CTkLabel(
            backups_frame, 
            text="Backups Disponibles", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        backups_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Lista de backups
        self.backups_listbox = ctk.CTkTextbox(backups_frame, height=200)
        self.backups_listbox.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        # Botones de acción para backups
        restore_button = ctk.CTkButton(
            backups_frame,
            text="Restaurar Backup",
            command=self.restore_backup
        )
        restore_button.grid(row=2, column=0, padx=10, pady=10)
        
        delete_button = ctk.CTkButton(
            backups_frame,
            text="Eliminar Backup",
            command=self.delete_backup,
            fg_color="red",
            hover_color="darkred"
        )
        delete_button.grid(row=2, column=1, padx=10, pady=10)
        
        refresh_button = ctk.CTkButton(
            backups_frame,
            text="Actualizar Lista",
            command=self.load_backups
        )
        refresh_button.grid(row=2, column=2, padx=10, pady=10)
        
        # Frame de estadísticas
        stats_frame = ctk.CTkFrame(self)
        stats_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        stats_label = ctk.CTkLabel(
            stats_frame, 
            text="Estadísticas de Backups", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        stats_label.grid(row=0, column=0, columnspan=4, pady=10)
        
        # Estadísticas
        self.total_backups_label = ctk.CTkLabel(stats_frame, text="Total de backups: 0")
        self.total_backups_label.grid(row=1, column=0, padx=20, pady=5)
        
        self.total_size_label = ctk.CTkLabel(stats_frame, text="Tamaño total: 0 MB")
        self.total_size_label.grid(row=1, column=1, padx=20, pady=5)
        
        self.last_backup_label = ctk.CTkLabel(stats_frame, text="Último backup: --")
        self.last_backup_label.grid(row=1, column=2, padx=20, pady=5)
        
        self.backup_status_label = ctk.CTkLabel(stats_frame, text="Estado: --")
        self.backup_status_label.grid(row=1, column=3, padx=20, pady=5)
        
        # Configurar grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        config_frame.grid_columnconfigure(1, weight=1)
        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(1, weight=1)
        backups_frame.grid_columnconfigure(0, weight=1)
        backups_frame.grid_columnconfigure(1, weight=1)
        backups_frame.grid_columnconfigure(2, weight=1)
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        stats_frame.grid_columnconfigure(2, weight=1)
        stats_frame.grid_columnconfigure(3, weight=1)
        
    def browse_source_path(self):
        """Buscar directorio de origen"""
        directory = filedialog.askdirectory(title="Seleccionar directorio de origen")
        if directory:
            self.source_entry.delete(0, "end")
            self.source_entry.insert(0, directory)
    
    def browse_destination_path(self):
        """Buscar directorio de destino"""
        directory = filedialog.askdirectory(title="Seleccionar directorio de destino")
        if directory:
            self.destination_entry.delete(0, "end")
            self.destination_entry.insert(0, directory)
    
    def create_manual_backup(self):
        """Crear backup manual"""
        try:
            source = self.source_entry.get()
            destination = self.destination_entry.get()
            
            if not source or not destination:
                self.logger.warning("Debe especificar rutas de origen y destino")
                return
            
            if not os.path.exists(source):
                self.logger.error("La ruta de origen no existe")
                return
            
            # Crear nombre del backup con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"ark_backup_{timestamp}"
            backup_path = os.path.join(destination, backup_name)
            
            # Crear backup en hilo separado
            threading.Thread(target=self._create_backup, args=(source, backup_path), daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Error al crear backup manual: {e}")
    
    def _create_backup(self, source, destination):
        """Crear backup (ejecutado en hilo separado)"""
        try:
            self.backup_running = True
            self.backup_status_label.configure(text="Estado: Creando backup...", text_color="orange")
            
            # Crear directorio de destino si no existe
            os.makedirs(destination, exist_ok=True)
            
            # Copiar archivos
            shutil.copytree(source, destination, dirs_exist_ok=True)
            
            self.backup_running = False
            self.backup_status_label.configure(text="Estado: Backup completado", text_color="green")
            self.logger.info(f"Backup creado exitosamente: {destination}")
            
            # Actualizar lista de backups
            self.load_backups()
            
        except Exception as e:
            self.backup_running = False
            self.backup_status_label.configure(text="Estado: Error en backup", text_color="red")
            self.logger.error(f"Error al crear backup: {e}")
    
    def start_auto_backup(self):
        """Iniciar backup automático"""
        try:
            frequency = int(self.frequency_entry.get())
            if frequency <= 0:
                self.logger.warning("La frecuencia debe ser mayor a 0")
                return
            
            self.auto_backup_status_label.configure(text="Estado: Activo", text_color="green")
            self.start_auto_backup_button.configure(state="disabled")
            self.stop_auto_backup_button.configure(state="normal")
            
            # Iniciar hilo de backup automático
            threading.Thread(target=self._auto_backup_loop, daemon=True).start()
            
            self.logger.info("Backup automático iniciado")
            
        except Exception as e:
            self.logger.error(f"Error al iniciar backup automático: {e}")
    
    def stop_auto_backup(self):
        """Detener backup automático"""
        self.auto_backup_status_label.configure(text="Estado: Detenido", text_color="red")
        self.start_auto_backup_button.configure(state="normal")
        self.stop_auto_backup_button.configure(state="disabled")
        self.logger.info("Backup automático detenido")
    
    def _auto_backup_loop(self):
        """Bucle de backup automático"""
        while self.auto_backup_status_label.cget("text") == "Estado: Activo":
            try:
                # Crear backup
                self.create_manual_backup()
                
                # Esperar hasta el próximo backup
                frequency = int(self.frequency_entry.get())
                time.sleep(frequency * 3600)  # Convertir horas a segundos
                
            except Exception as e:
                self.logger.error(f"Error en backup automático: {e}")
                break
    
    def load_backups(self):
        """Cargar lista de backups"""
        try:
            destination = self.destination_entry.get()
            if not destination or not os.path.exists(destination):
                self.backups_listbox.delete("1.0", "end")
                self.backups_listbox.insert("1.0", "No hay backups disponibles")
                return
            
            # Buscar directorios de backup
            self.backups = []
            total_size = 0
            
            for item in os.listdir(destination):
                item_path = os.path.join(destination, item)
                if os.path.isdir(item_path) and item.startswith("ark_backup_"):
                    try:
                        # Obtener información del backup
                        stat = os.stat(item_path)
                        size_mb = stat.st_size / (1024 * 1024)
                        total_size += size_mb
                        
                        self.backups.append({
                            "name": item,
                            "path": item_path,
                            "size": size_mb,
                            "date": datetime.fromtimestamp(stat.st_mtime)
                        })
                    except Exception as e:
                        self.logger.error(f"Error al obtener información del backup {item}: {e}")
            
            # Ordenar por fecha (más reciente primero)
            self.backups.sort(key=lambda x: x["date"], reverse=True)
            
            # Actualizar lista
            self.backups_listbox.delete("1.0", "end")
            if self.backups:
                for backup in self.backups:
                    date_str = backup["date"].strftime("%Y-%m-%d %H:%M")
                    self.backups_listbox.insert("end", 
                        f"{backup['name']:<25} {date_str:<20} {backup['size']:.1f}MB\n")
            else:
                self.backups_listbox.insert("1.0", "No hay backups disponibles")
            
            # Actualizar estadísticas
            self.total_backups_label.configure(text=f"Total de backups: {len(self.backups)}")
            self.total_size_label.configure(text=f"Tamaño total: {total_size:.1f}MB")
            
            if self.backups:
                last_backup = self.backups[0]["date"].strftime("%Y-%m-%d %H:%M")
                self.last_backup_label.configure(text=f"Último backup: {last_backup}")
            else:
                self.last_backup_label.configure(text="Último backup: --")
                
        except Exception as e:
            self.logger.error(f"Error al cargar backups: {e}")
    
    def restore_backup(self):
        """Restaurar backup seleccionado"""
        try:
            # Obtener backup seleccionado (implementación simplificada)
            if not self.backups:
                self.logger.warning("No hay backups disponibles para restaurar")
                return
            
            # Aquí se implementaría la lógica para restaurar el backup
            self.logger.info("Función de restauración de backup (a implementar)")
            
        except Exception as e:
            self.logger.error(f"Error al restaurar backup: {e}")
    
    def delete_backup(self):
        """Eliminar backup seleccionado"""
        try:
            # Obtener backup seleccionado (implementación simplificada)
            if not self.backups:
                self.logger.warning("No hay backups disponibles para eliminar")
                return
            
            # Aquí se implementaría la lógica para eliminar el backup
            self.logger.info("Función de eliminación de backup (a implementar)")
            
        except Exception as e:
            self.logger.error(f"Error al eliminar backup: {e}")
