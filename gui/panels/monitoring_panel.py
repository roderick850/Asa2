import customtkinter as ctk
import psutil
import threading
import time
from datetime import datetime

class MonitoringPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.monitoring_active = False
        
        self.create_widgets()
        
        # Iniciar monitoreo con retraso para asegurar que la UI esté lista
        self.after(2000, self.start_monitoring)  # 2 segundos de retraso
        
    def create_widgets(self):
        """Crear todos los widgets del panel"""
        # Título
        title_label = ctk.CTkLabel(
            self, 
            text="Monitoreo del Sistema", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(20, 30))
        
        # Frame de estadísticas del sistema
        system_stats_frame = ctk.CTkFrame(self)
        system_stats_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        system_stats_label = ctk.CTkLabel(
            system_stats_frame, 
            text="Estadísticas del Sistema", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        system_stats_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # CPU
        self.cpu_label = ctk.CTkLabel(system_stats_frame, text="CPU: --")
        self.cpu_label.grid(row=1, column=0, padx=20, pady=5, sticky="w")
        
        self.cpu_progress = ctk.CTkProgressBar(system_stats_frame)
        self.cpu_progress.grid(row=1, column=1, padx=20, pady=5, sticky="ew")
        self.cpu_progress.set(0)
        
        # Memoria RAM
        self.memory_label = ctk.CTkLabel(system_stats_frame, text="Memoria RAM: --")
        self.memory_label.grid(row=2, column=0, padx=20, pady=5, sticky="w")
        
        self.memory_progress = ctk.CTkProgressBar(system_stats_frame)
        self.memory_progress.grid(row=2, column=1, padx=20, pady=5, sticky="ew")
        self.memory_progress.set(0)
        
        # Disco
        self.disk_label = ctk.CTkLabel(system_stats_frame, text="Disco: --")
        self.disk_label.grid(row=3, column=0, padx=20, pady=5, sticky="w")
        
        self.disk_progress = ctk.CTkProgressBar(system_stats_frame)
        self.disk_progress.grid(row=3, column=1, padx=20, pady=5, sticky="ew")
        self.disk_progress.set(0)
        
        # Red
        self.network_label = ctk.CTkLabel(system_stats_frame, text="Red: --")
        self.network_label.grid(row=4, column=0, padx=20, pady=5, sticky="w")
        
        # Frame de estadísticas del servidor
        server_stats_frame = ctk.CTkFrame(self)
        server_stats_frame.grid(row=1, column=1, padx=20, pady=10, sticky="nsew")
        
        server_stats_label = ctk.CTkLabel(
            server_stats_frame, 
            text="Estadísticas del Servidor", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        server_stats_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Estado del servidor
        self.server_status_label = ctk.CTkLabel(server_stats_frame, text="Estado: Desconocido")
        self.server_status_label.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="w")
        
        # Jugadores conectados
        self.players_connected_label = ctk.CTkLabel(server_stats_frame, text="Jugadores: --")
        self.players_connected_label.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="w")
        
        # Tiempo activo
        self.uptime_label = ctk.CTkLabel(server_stats_frame, text="Tiempo activo: --")
        self.uptime_label.grid(row=3, column=0, columnspan=2, padx=20, pady=5, sticky="w")
        
        # Uso de CPU del servidor
        self.server_cpu_label = ctk.CTkLabel(server_stats_frame, text="CPU del servidor: --")
        self.server_cpu_label.grid(row=4, column=0, columnspan=2, padx=20, pady=5, sticky="w")
        
        # Uso de memoria del servidor
        self.server_memory_label = ctk.CTkLabel(server_stats_frame, text="Memoria del servidor: --")
        self.server_memory_label.grid(row=5, column=0, columnspan=2, padx=20, pady=5, sticky="w")
        
        # Frame de gráficos
        charts_frame = ctk.CTkFrame(self)
        charts_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        charts_label = ctk.CTkLabel(
            charts_frame, 
            text="Gráficos de Rendimiento", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        charts_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Área para gráficos (placeholder)
        self.charts_area = ctk.CTkTextbox(charts_frame, height=200)
        self.charts_area.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        self.charts_area.insert("1.0", "Gráficos de rendimiento en tiempo real\n\n")
        self.charts_area.insert("end", "• CPU del sistema\n")
        self.charts_area.insert("end", "• Uso de memoria\n")
        self.charts_area.insert("end", "• Actividad de red\n")
        self.charts_area.insert("end", "• Jugadores conectados\n")
        
        # Frame de controles
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        # Botones de control
        self.start_monitoring_button = ctk.CTkButton(
            controls_frame,
            text="Iniciar Monitoreo",
            command=self.start_monitoring,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.start_monitoring_button.grid(row=0, column=0, padx=10, pady=10)
        
        self.stop_monitoring_button = ctk.CTkButton(
            controls_frame,
            text="Detener Monitoreo",
            command=self.stop_monitoring,
            fg_color="red",
            hover_color="darkred"
        )
        self.stop_monitoring_button.grid(row=0, column=1, padx=10, pady=10)
        
        self.refresh_button = ctk.CTkButton(
            controls_frame,
            text="Actualizar",
            command=self.refresh_stats
        )
        self.refresh_button.grid(row=0, column=2, padx=10, pady=10)
        
        # Configurar grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        system_stats_frame.grid_columnconfigure(1, weight=1)
        server_stats_frame.grid_columnconfigure(0, weight=1)
        charts_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(1, weight=1)
        controls_frame.grid_columnconfigure(2, weight=1)
        
    def start_monitoring(self):
        """Iniciar monitoreo en tiempo real"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.start_monitoring_button.configure(state="disabled")
            self.stop_monitoring_button.configure(state="normal")
            
            # Iniciar hilo de monitoreo
            threading.Thread(target=self.monitoring_loop, daemon=True).start()
            self.logger.info("Monitoreo iniciado")
    
    def stop_monitoring(self):
        """Detener monitoreo"""
        self.monitoring_active = False
        self.start_monitoring_button.configure(state="normal")
        self.stop_monitoring_button.configure(state="disabled")
        self.logger.info("Monitoreo detenido")
    
    def monitoring_loop(self):
        """Bucle principal de monitoreo"""
        while self.monitoring_active:
            try:
                self.update_system_stats()
                self.update_server_stats()
                time.sleep(2)  # Actualizar cada 2 segundos
            except Exception as e:
                self.logger.error(f"Error en monitoreo: {e}")
                break
    
    def update_system_stats(self):
        """Actualizar estadísticas del sistema"""
        try:
            # Obtener datos del sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            network = psutil.net_io_counters()
            network_mb = network.bytes_sent / (1024**2)
            network_recv_mb = network.bytes_recv / (1024**2)
            
            # Programar actualización de UI en el hilo principal
            def update_ui():
                try:
                    if hasattr(self, 'cpu_label') and self.cpu_label.winfo_exists():
                        self.cpu_label.configure(text=f"CPU: {cpu_percent:.1f}%")
                        self.cpu_progress.set(cpu_percent / 100)
                    
                    if hasattr(self, 'memory_label') and self.memory_label.winfo_exists():
                        self.memory_label.configure(
                            text=f"Memoria RAM: {memory_percent:.1f}% ({memory_gb:.1f}GB / {memory_total_gb:.1f}GB)"
                        )
                        self.memory_progress.set(memory_percent / 100)
                    
                    if hasattr(self, 'disk_label') and self.disk_label.winfo_exists():
                        self.disk_label.configure(
                            text=f"Disco: {disk_percent:.1f}% ({disk_gb:.1f}GB / {disk_total_gb:.1f}GB)"
                        )
                        self.disk_progress.set(disk_percent / 100)
                    
                    if hasattr(self, 'network_label') and self.network_label.winfo_exists():
                        self.network_label.configure(
                            text=f"Red: ↑{network_mb:.1f}MB ↓{network_recv_mb:.1f}MB"
                        )
                except Exception:
                    # Silenciar errores de UI
                    pass
            
            # Programar la actualización en el hilo principal
            try:
                if hasattr(self, 'winfo_exists') and self.winfo_exists():
                    self.after(0, update_ui)
            except Exception:
                # Widget ya no existe
                pass
            
        except Exception as e:
            self.logger.error(f"Error al actualizar estadísticas del sistema: {e}")
    
    def update_server_stats(self):
        """Actualizar estadísticas del servidor"""
        try:
            # Buscar proceso del servidor Ark
            ark_process = None
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'ark' in proc.info['name'].lower() or any('ark' in str(arg).lower() for arg in proc.info['cmdline'] or []):
                        ark_process = proc
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Obtener datos del servidor
            if ark_process:
                server_cpu = ark_process.cpu_percent()
                server_memory = ark_process.memory_info()
                server_memory_mb = server_memory.rss / (1024**2)
                create_time = ark_process.create_time()
                uptime_seconds = time.time() - create_time
                uptime_hours = uptime_seconds / 3600
                
                status_text = "Estado: Ejecutándose"
                status_color = "green"
                cpu_text = f"CPU del servidor: {server_cpu:.1f}%"
                memory_text = f"Memoria del servidor: {server_memory_mb:.1f}MB"
                uptime_text = f"Tiempo activo: {uptime_hours:.1f} horas"
            else:
                status_text = "Estado: No ejecutándose"
                status_color = "red"
                cpu_text = "CPU del servidor: --"
                memory_text = "Memoria del servidor: --"
                uptime_text = "Tiempo activo: --"
            
            # Programar actualización de UI en el hilo principal
            def update_ui():
                try:
                    if hasattr(self, 'server_status_label') and self.server_status_label.winfo_exists():
                        self.server_status_label.configure(text=status_text, text_color=status_color)
                    
                    if hasattr(self, 'server_cpu_label') and self.server_cpu_label.winfo_exists():
                        self.server_cpu_label.configure(text=cpu_text)
                    
                    if hasattr(self, 'server_memory_label') and self.server_memory_label.winfo_exists():
                        self.server_memory_label.configure(text=memory_text)
                    
                    if hasattr(self, 'uptime_label') and self.uptime_label.winfo_exists():
                        self.uptime_label.configure(text=uptime_text)
                    
                    if hasattr(self, 'players_connected_label') and self.players_connected_label.winfo_exists():
                        self.players_connected_label.configure(text="Jugadores: 0 (placeholder)")
                except Exception:
                    # Silenciar errores de UI
                    pass
            
            # Programar la actualización en el hilo principal
            try:
                if hasattr(self, 'winfo_exists') and self.winfo_exists():
                    self.after(0, update_ui)
            except Exception:
                # Widget ya no existe
                pass
            
        except Exception as e:
            self.logger.error(f"Error al actualizar estadísticas del servidor: {e}")
    
    def refresh_stats(self):
        """Actualizar estadísticas manualmente"""
        self.update_system_stats()
        self.update_server_stats()
        self.logger.info("Estadísticas actualizadas manualmente")
