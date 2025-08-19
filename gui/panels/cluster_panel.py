#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClusterPanel - Panel de gestión de cluster de servidores ARK

Este panel proporciona una interfaz unificada para:
- Gestionar múltiples servidores ARK como cluster
- Monitorear estado de todos los servidores
- Operaciones coordinadas (inicio, parada, reinicio)
- Configuración del cluster
- Vista consolidada de estadísticas
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import customtkinter as ctk
import threading
import time
import os
from datetime import datetime
from typing import Optional, Dict, Any

from utils.cluster_manager import ClusterManager, ServerInstance
from utils.logger import Logger

class ServerStatusFrame(ctk.CTkFrame):
    """Frame para mostrar el estado de un servidor individual"""
    
    def __init__(self, parent, server_name: str, server_instance: ServerInstance, cluster_panel):
        super().__init__(parent, fg_color=("gray90", "gray20"))
        self.server_name = server_name
        self.server_instance = server_instance
        self.cluster_panel = cluster_panel
        
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """Configurar interfaz del frame del servidor"""
        # Título del servidor
        title_label = ctk.CTkLabel(self, text=f"🖥️ {self.server_name}", 
                                  font=("Arial", 14, "bold"))
        title_label.pack(pady=(10, 5))
        
        # Frame de información compacta
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=5)
        
        # Primera fila: Estado y Mapa
        row1_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        row1_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(row1_frame, text="Estado:", width=60).pack(side="left")
        self.status_label = ctk.CTkLabel(row1_frame, text="⭕ Detenido", 
                                        text_color="red", width=80)
        self.status_label.pack(side="left", padx=(5, 20))
        
        ctk.CTkLabel(row1_frame, text="Mapa:", width=50).pack(side="left")
        map_name = self.server_instance.config.get("map", "N/A")
        ctk.CTkLabel(row1_frame, text=map_name, width=100).pack(side="left", padx=5)
        
        # Segunda fila: Puerto y Jugadores
        row2_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        row2_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(row2_frame, text="Puerto:", width=60).pack(side="left")
        port = self.server_instance.config.get("port", "N/A")
        ctk.CTkLabel(row2_frame, text=str(port), width=80).pack(side="left", padx=(5, 20))
        
        ctk.CTkLabel(row2_frame, text="Jugadores:", width=70).pack(side="left")
        self.players_label = ctk.CTkLabel(row2_frame, text="👥 0", width=80)
        self.players_label.pack(side="left", padx=5)
        
        # Tercera fila: Estadísticas
        row3_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        row3_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(row3_frame, text="Uptime:", width=60).pack(side="left")
        self.uptime_label = ctk.CTkLabel(row3_frame, text="⏱️ 0s", width=80)
        self.uptime_label.pack(side="left", padx=(5, 10))
        
        ctk.CTkLabel(row3_frame, text="CPU:", width=40).pack(side="left")
        self.cpu_label = ctk.CTkLabel(row3_frame, text="💻 0%", width=60)
        self.cpu_label.pack(side="left", padx=(5, 10))
        
        ctk.CTkLabel(row3_frame, text="RAM:", width=40).pack(side="left")
        self.memory_label = ctk.CTkLabel(row3_frame, text="🧠 0 MB", width=80)
        self.memory_label.pack(side="left", padx=5)
        
        # Botones de control compactos
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        self.start_btn = ctk.CTkButton(buttons_frame, text="▶️ Iniciar", 
                                      command=self.start_server, width=80, height=28,
                                      fg_color="green", hover_color="darkgreen")
        self.start_btn.pack(side="left", padx=(0, 5))
        
        self.stop_btn = ctk.CTkButton(buttons_frame, text="⏹️ Detener", 
                                     command=self.stop_server, width=80, height=28,
                                     fg_color="red", hover_color="darkred")
        self.stop_btn.pack(side="left", padx=(0, 5))
        
        self.restart_btn = ctk.CTkButton(buttons_frame, text="🔄 Reiniciar", 
                                        command=self.restart_server, width=90, height=28,
                                        fg_color="orange", hover_color="darkorange")
        self.restart_btn.pack(side="left", padx=(0, 5))
        
        # Botón de eliminar servidor
        self.remove_btn = ctk.CTkButton(buttons_frame, text="🗑️ Eliminar", 
                                       command=self.remove_server, width=90, height=28,
                                       fg_color="#8B0000", hover_color="#A52A2A")
        self.remove_btn.pack(side="left", padx=(0, 5))
        
        # Botón de configuración
        self.config_btn = ctk.CTkButton(buttons_frame, text="⚙️ Config", 
                                       command=self.open_config, width=80, height=28)
        self.config_btn.pack(side="right")
    
    def update_display(self):
        """Actualizar la visualización del estado del servidor"""
        try:
            # Estado
            status = self.server_instance.status
            if status == "running":
                self.status_label.configure(text="✅ Ejecutándose", text_color="green")
                self.start_btn.configure(state="disabled")
                self.stop_btn.configure(state="normal")
                self.restart_btn.configure(state="normal")
            elif status == "stopped":
                self.status_label.configure(text="⭕ Detenido", text_color="red")
                self.start_btn.configure(state="normal")
                self.stop_btn.configure(state="disabled")
                self.restart_btn.configure(state="disabled")
            else:
                self.status_label.configure(text=f"⚠️ {status.title()}", text_color="orange")
                self.start_btn.configure(state="normal")
                self.stop_btn.configure(state="normal")
                self.restart_btn.configure(state="normal")
            
            # Jugadores
            self.players_label.configure(text=f"👥 {self.server_instance.players_online}")
            
            # Uptime
            uptime_seconds = self.server_instance.get_uptime()
            if uptime_seconds > 0:
                hours = uptime_seconds // 3600
                minutes = (uptime_seconds % 3600) // 60
                seconds = uptime_seconds % 60
                uptime_text = f"⏱️ {hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                uptime_text = "⏱️ 00:00:00"
            self.uptime_label.configure(text=uptime_text)
            
            # CPU y Memoria
            self.cpu_label.configure(text=f"💻 {self.server_instance.cpu_usage:.1f}%")
            memory_mb = self.server_instance.memory_usage // (1024 * 1024) if self.server_instance.memory_usage > 0 else 0
            self.memory_label.configure(text=f"🧠 {memory_mb} MB")
            
        except Exception as e:
            self.cluster_panel.logger.error(f"Error actualizando display de {self.server_name}: {e}")
    
    def start_server(self):
        """Iniciar servidor"""
        def start_thread():
            def callback(level, message):
                self.cluster_panel.log_callback(level.upper(), message)
            
            success = self.server_instance.start(callback)
            self.cluster_panel._safe_schedule_ui_update(self.cluster_panel.update_cluster_stats)
            
            if success:
                self.cluster_panel.log_callback("INFO", f"✅ Servidor '{self.server_name}' iniciado correctamente")
            else:
                self.cluster_panel.log_callback("ERROR", f"❌ Error al iniciar servidor '{self.server_name}'")
        
        threading.Thread(target=start_thread, daemon=True).start()
    
    def stop_server(self):
        """Detener servidor"""
        def stop_thread():
            def callback(level, message):
                self.cluster_panel.log_callback(level.upper(), message)
            
            success = self.server_instance.stop(callback)
            self.cluster_panel._safe_schedule_ui_update(self.cluster_panel.update_cluster_stats)
            
            if success:
                self.cluster_panel.log_callback("INFO", f"✅ Servidor '{self.server_name}' detenido correctamente")
            else:
                self.cluster_panel.log_callback("ERROR", f"❌ Error al detener servidor '{self.server_name}'")
        
        threading.Thread(target=stop_thread, daemon=True).start()
    
    def restart_server(self):
        """Reiniciar servidor"""
        def restart_thread():
            def callback(level, message):
                self.cluster_panel.log_callback(level.upper(), message)
            
            success = self.server_instance.restart(callback)
            self.cluster_panel._safe_schedule_ui_update(self.cluster_panel.update_cluster_stats)
            
            if success:
                self.cluster_panel.log_callback("INFO", f"✅ Servidor '{self.server_name}' reiniciado correctamente")
            else:
                self.cluster_panel.log_callback("ERROR", f"❌ Error al reiniciar servidor '{self.server_name}'")
        
        threading.Thread(target=restart_thread, daemon=True).start()
    
    def open_config(self):
        """Abrir configuración del servidor"""
        try:
            # Obtener la ruta del servidor desde la configuración
            server_config = self.server_instance.config
            server_path = server_config.get('path', '')
            
            if not server_path:
                messagebox.showerror(
                    "Error", 
                    f"No se pudo determinar la ruta del servidor '{self.server_name}'.\n"
                    "Verifica que el servidor esté correctamente configurado."
                )
                return
            
            # Construir la ruta de la carpeta de configuración
            config_folder = os.path.join(server_path, "ShooterGame", "Saved", "Config", "WindowsServer")
            
            # Verificar que la carpeta existe
            if not os.path.exists(config_folder):
                # Intentar crear la carpeta si no existe
                try:
                    os.makedirs(config_folder, exist_ok=True)
                    self.cluster_panel.log_callback("INFO", f"📁 Carpeta de configuración creada: {config_folder}")
                    messagebox.showinfo(
                        "Carpeta creada",
                        f"La carpeta de configuración no existía y ha sido creada:\n{config_folder}\n\n"
                        "💡 Para generar los archivos de configuración:\n"
                        "1. Inicia el servidor al menos una vez\n"
                        "2. Los archivos se crearán automáticamente"
                    )
                except Exception as e:
                    self.cluster_panel.log_callback("ERROR", f"❌ Error al crear carpeta de configuración: {e}")
                    messagebox.showerror(
                        "Error al crear carpeta",
                        f"No se pudo crear la carpeta de configuración:\n{config_folder}\n\nError: {e}"
                    )
                    return
            
            # Abrir la carpeta en el explorador de archivos
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                subprocess.run(["explorer", config_folder], check=False)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", config_folder], check=False)
            else:  # Linux
                subprocess.run(["xdg-open", config_folder], check=False)
            
            self.cluster_panel.log_callback("INFO", f"📁 Abriendo carpeta de configuración: {config_folder}")
            
        except Exception as e:
            self.cluster_panel.log_callback("ERROR", f"❌ Error al abrir configuración: {e}")
            messagebox.showerror(
                "Error",
                f"Error al abrir la configuración del servidor:\n{str(e)}"
            )
    
    def remove_server(self):
        """Eliminar servidor del cluster"""
        # Confirmar eliminación
        result = messagebox.askyesno(
            "Confirmar Eliminación", 
            f"¿Estás seguro de que deseas eliminar el servidor '{self.server_name}' del cluster?\n\n"
            f"Esta acción no se puede deshacer.",
            icon="warning"
        )
        
        if result:
            try:
                # Detener el servidor si está corriendo
                if self.server_instance.status == "running":
                    self.server_instance.stop()
                
                # Eliminar del cluster manager
                self.cluster_panel.cluster_manager.remove_server(self.server_name)
                
                # Actualizar la interfaz
                self.cluster_panel.refresh_server_frames()
                self.cluster_panel.update_cluster_stats()
                
                # Log de la acción
                self.cluster_panel.log_callback("INFO", f"🗑️ Servidor '{self.server_name}' eliminado del cluster")
                
                messagebox.showinfo("Éxito", f"Servidor '{self.server_name}' eliminado correctamente del cluster.")
                
            except Exception as e:
                error_msg = f"Error al eliminar servidor '{self.server_name}': {e}"
                self.cluster_panel.log_callback("ERROR", error_msg)
                messagebox.showerror("Error", error_msg)

class ClusterPanel(ctk.CTkFrame):
    """Panel principal de gestión del cluster"""
    
    def __init__(self, parent, config_manager, logger: Optional[Logger] = None, main_window=None):
        super().__init__(parent, fg_color="transparent")
        self.config_manager = config_manager
        self.logger = logger or Logger()
        self.main_window = main_window
        
        # Cluster Manager
        self.cluster_manager = ClusterManager(config_manager, logger)
        
        # Variables de UI
        self.server_frames: Dict[str, ServerStatusFrame] = {}
        self.update_thread = None
        self.update_active = False
        
        self.setup_ui()
        self.start_auto_update()
        
        # Verificar estado inicial del cluster
        self.check_initial_cluster_state()
        
        # Empaquetar el panel en su contenedor padre
        self.pack(fill="both", expand=True)
        
        self.logger.info("ClusterPanel inicializado")
    
    def _safe_schedule_ui_update(self, callback):
        """Programar actualización de UI de forma segura"""
        try:
            # Verificar si la ventana principal aún existe
            if (self.main_window and hasattr(self.main_window, 'root') and 
                hasattr(self.main_window.root, 'winfo_exists')):
                try:
                    if self.main_window.root.winfo_exists():
                        self.main_window.root.after(0, callback)
                        return
                except Exception:
                    pass
            
            # Verificar si este widget aún existe
            try:
                if hasattr(self, 'winfo_exists') and self.winfo_exists():
                    self.after(0, callback)
            except Exception:
                pass
        except Exception:
            pass
    
    def check_initial_cluster_state(self):
        """Verificar estado inicial del cluster y deshabilitar si es necesario"""
        try:
            # Verificar si el main_window tiene principal_panel
            if (self.main_window and hasattr(self.main_window, 'principal_panel') and 
                hasattr(self.main_window.principal_panel, 'is_cluster_mode')):
                
                is_cluster_enabled = self.main_window.principal_panel.is_cluster_mode()
                
                if not is_cluster_enabled:
                    # Si el cluster no está habilitado, deshabilitar todos los elementos
                    self.disable_all_elements()
                    self.logger.info("📱 Cluster panel inicializado en estado deshabilitado")
                else:
                    self.logger.info("🌐 Cluster panel inicializado en estado habilitado")
            else:
                # Si no se puede determinar el estado, deshabilitar por seguridad
                self.disable_all_elements()
                self.logger.warning("⚠️ No se pudo determinar estado del cluster, deshabilitando panel")
                
        except Exception as e:
            self.logger.error(f"Error verificando estado inicial del cluster: {e}")
            # En caso de error, deshabilitar por seguridad
            self.disable_all_elements()
    
    def setup_ui(self):
        """Configurar interfaz del panel"""
        # Frame principal
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header con información del cluster
        header_frame = ctk.CTkFrame(main_frame, fg_color=("gray85", "gray25"))
        header_frame.pack(fill="x", pady=(0, 10))
        
        # Título del header
        title_label = ctk.CTkLabel(header_frame, text="🏢 Información del Cluster", 
                                  font=("Arial", 16, "bold"))
        title_label.pack(pady=(10, 5))
        
        # Información del cluster compacta
        cluster_info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        cluster_info_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Primera fila: Nombre y ID
        info_row1 = ctk.CTkFrame(cluster_info_frame, fg_color="transparent")
        info_row1.pack(fill="x", pady=2)
        
        ctk.CTkLabel(info_row1, text="📋 Nombre:", width=80).pack(side="left")
        self.cluster_name_label = ctk.CTkLabel(info_row1, text=self.cluster_manager.cluster_name, 
                                              font=("Arial", 12, "bold"), width=150)
        self.cluster_name_label.pack(side="left", padx=(5, 20))
        
        ctk.CTkLabel(info_row1, text="🆔 ID:", width=60).pack(side="left")
        ctk.CTkLabel(info_row1, text=self.cluster_manager.cluster_id, width=200).pack(side="left", padx=5)
        
        # Segunda fila: Estadísticas del cluster
        info_row2 = ctk.CTkFrame(cluster_info_frame, fg_color="transparent")
        info_row2.pack(fill="x", pady=2)
        
        ctk.CTkLabel(info_row2, text="🖥️ Servidores:", width=80).pack(side="left")
        self.active_servers_label = ctk.CTkLabel(info_row2, text="0/0", text_color="blue", width=60)
        self.active_servers_label.pack(side="left", padx=(5, 20))
        
        ctk.CTkLabel(info_row2, text="👥 Jugadores:", width=80).pack(side="left")
        self.total_players_label = ctk.CTkLabel(info_row2, text="0", width=60)
        self.total_players_label.pack(side="left", padx=(5, 20))
        
        ctk.CTkLabel(info_row2, text="💻 CPU Prom:", width=80).pack(side="left")
        self.avg_cpu_label = ctk.CTkLabel(info_row2, text="0%", width=60)
        self.avg_cpu_label.pack(side="left", padx=5)
        
        # Botones de control del cluster
        cluster_buttons_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        cluster_buttons_frame.pack(fill="x", padx=10, pady=(10, 10))
        
        # Primera fila de botones: Control del cluster
        control_row = ctk.CTkFrame(cluster_buttons_frame, fg_color="transparent")
        control_row.pack(fill="x", pady=(0, 5))
        
        self.start_cluster_btn = ctk.CTkButton(control_row, text="▶️ Iniciar Cluster", 
                                              command=self.start_cluster, width=120, height=32,
                                              fg_color="green", hover_color="darkgreen")
        self.start_cluster_btn.pack(side="left", padx=(0, 5))
        
        self.stop_cluster_btn = ctk.CTkButton(control_row, text="⏹️ Detener Cluster", 
                                             command=self.stop_cluster, width=120, height=32,
                                             fg_color="red", hover_color="darkred")
        self.stop_cluster_btn.pack(side="left", padx=(0, 5))
        
        self.restart_cluster_btn = ctk.CTkButton(control_row, text="🔄 Reiniciar Cluster", 
                                                command=self.restart_cluster, width=130, height=32,
                                                fg_color="orange", hover_color="darkorange")
        self.restart_cluster_btn.pack(side="left", padx=(0, 5))
        
        # Segunda fila de botones: Gestión
        manage_row = ctk.CTkFrame(cluster_buttons_frame, fg_color="transparent")
        manage_row.pack(fill="x")
        
        self.add_server_btn = ctk.CTkButton(manage_row, text="➕ Agregar Servidor", 
                                           command=self.add_server, width=140, height=32)
        self.add_server_btn.pack(side="left", padx=(0, 5))
        
        self.cluster_config_btn = ctk.CTkButton(manage_row, text="⚙️ Configurar Cluster", 
                                               command=self.configure_cluster, width=140, height=32)
        self.cluster_config_btn.pack(side="right")
        
        # Frame para servidores con scroll
        servers_container = ctk.CTkFrame(main_frame, fg_color=("gray85", "gray25"))
        servers_container.pack(fill="both", expand=True)
        
        # Título de la sección de servidores
        servers_title = ctk.CTkLabel(servers_container, text="🖥️ Servidores del Cluster", 
                                    font=("Arial", 16, "bold"))
        servers_title.pack(pady=(10, 5))
        
        # Frame scrollable para servidores
        self.servers_scrollable = ctk.CTkScrollableFrame(servers_container, 
                                                        fg_color="transparent",
                                                        height=300)
        self.servers_scrollable.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Referencia al frame interno para compatibilidad
        self.servers_frame = self.servers_scrollable
        
        # Crear frames para servidores existentes
        self.refresh_server_frames()
        
        # Frame de logs expandido
        logs_frame = ctk.CTkFrame(main_frame, fg_color=("gray85", "gray25"))
        logs_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Título de logs
        logs_title = ctk.CTkLabel(logs_frame, text="📋 Logs del Cluster", 
                                 font=("Arial", 14, "bold"))
        logs_title.pack(pady=(10, 5))
        
        # Text widget para logs con altura expandida
        logs_container = ctk.CTkFrame(logs_frame, fg_color="transparent")
        logs_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.logs_text = ctk.CTkTextbox(logs_container, height=200, wrap="word")
        self.logs_text.pack(fill="both", expand=True, pady=(0, 10))
        
        # Botones de logs compactos
        logs_buttons_frame = ctk.CTkFrame(logs_container, fg_color="transparent")
        logs_buttons_frame.pack(fill="x")
        
        ctk.CTkButton(logs_buttons_frame, text="🗑️ Limpiar", 
                     command=self.clear_logs, width=100, height=28).pack(side="left")
        
        ctk.CTkButton(logs_buttons_frame, text="💾 Exportar", 
                     command=self.export_logs, width=100, height=28).pack(side="left", padx=(10, 0))
    
    def refresh_server_frames(self):
        """Actualizar frames de servidores"""
        # Limpiar frames existentes
        for frame in self.server_frames.values():
            frame.destroy()
        self.server_frames.clear()
        
        # Recargar configuración del cluster para asegurar sincronización
        try:
            self.cluster_manager.load_cluster_config()
            self.logger.info(f"Configuración del cluster recargada - {len(self.cluster_manager.servers)} servidores")
        except Exception as e:
            self.logger.error(f"Error recargando configuración del cluster: {e}")
        
        # Verificar si hay servidores
        if not self.cluster_manager.servers:
            # Mostrar mensaje si no hay servidores
            no_servers_label = ctk.CTkLabel(
                self.servers_frame, 
                text="❌ No hay servidores configurados en el cluster.\n\n➕ Usa 'Agregar Servidor' para añadir servidores.",
                justify="center",
                font=("Arial", 12),
                text_color="gray"
            )
            no_servers_label.pack(expand=True, pady=40)
            self.logger.warning("No hay servidores configurados en el cluster")
            return
        
        # Crear frames para servidores actuales
        for server_name, server_instance in self.cluster_manager.servers.items():
            try:
                frame = ServerStatusFrame(self.servers_frame, server_name, server_instance, self)
                frame.pack(fill="x", pady=2)
                self.server_frames[server_name] = frame
                self.logger.info(f"✓ Frame creado para servidor: {server_name} - Puerto: {server_instance.config.get('port', 'N/A')}")
            except Exception as e:
                self.logger.error(f"Error creando frame para servidor {server_name}: {e}")
        
        # Log para debug
        self.logger.info(f"Servidores cargados en cluster: {list(self.cluster_manager.servers.keys())}")
        self.logger.info(f"Frames de servidores creados: {len(self.server_frames)}")
        
        # Actualizar estadísticas del cluster
        self.update_cluster_stats()
    
    def start_auto_update(self):
        """Iniciar actualización automática de la UI"""
        if not self.update_active:
            self.update_active = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
    
    def stop_auto_update(self):
        """Detener actualización automática"""
        self.update_active = False
    
    def _update_loop(self):
        """Loop de actualización de la UI"""
        while self.update_active:
            try:
                # Verificar si la ventana principal aún existe
                if (self.main_window and hasattr(self.main_window, 'root') and 
                    hasattr(self.main_window.root, 'winfo_exists')):
                    try:
                        if not self.main_window.root.winfo_exists():
                            self.update_active = False
                            break
                    except Exception:
                        self.update_active = False
                        break
                
                # Verificar si este widget aún existe
                try:
                    if hasattr(self, 'winfo_exists') and not self.winfo_exists():
                        self.update_active = False
                        break
                except Exception:
                    self.update_active = False
                    break
                
                try:
                    self.after(0, self.update_ui)
                except Exception:
                    pass
                time.sleep(2)  # Actualizar cada 2 segundos
            except Exception as e:
                self.logger.error(f"Error en loop de actualización: {e}")
                self.update_active = False
                time.sleep(5)
    
    def update_ui(self):
        """Actualizar interfaz de usuario"""
        try:
            # Actualizar frames de servidores
            for frame in self.server_frames.values():
                frame.update_display()
            
            # Actualizar estadísticas del cluster
            self.update_cluster_stats()
            
        except Exception as e:
            self.logger.error(f"Error actualizando UI: {e}")
    
    def update_cluster_stats(self):
        """Actualizar estadísticas del cluster en la UI"""
        try:
            # Contar servidores activos
            active_count = len([s for s in self.cluster_manager.servers.values() if s.status == "running"])
            total_count = len(self.cluster_manager.servers)
            self.active_servers_label.configure(text=f"{active_count}/{total_count}")
            
            # Jugadores totales
            total_players = sum(s.players_online for s in self.cluster_manager.servers.values())
            self.total_players_label.configure(text=str(total_players))
            
            # CPU promedio
            cpu_values = [s.cpu_usage for s in self.cluster_manager.servers.values() if s.cpu_usage > 0]
            avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
            self.avg_cpu_label.configure(text=f"{avg_cpu:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Error actualizando estadísticas del cluster: {e}")
    
    def log_callback(self, level: str, message: str):
        """Callback para mostrar logs en la UI"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {level.upper()}: {message}\n"
            
            # Agregar al widget de texto
            current_text = self.logs_text.get("0.0", "end")
            self.logs_text.delete("0.0", "end")
            self.logs_text.insert("0.0", current_text + log_entry)
            
            # Limitar número de líneas (aproximado)
            lines = current_text.count('\n')
            if lines > 500:
                lines_to_keep = current_text.split('\n')[-400:]
                self.logs_text.delete("0.0", "end")
                self.logs_text.insert("0.0", '\n'.join(lines_to_keep) + log_entry)
            
        except Exception as e:
            self.logger.error(f"Error en log_callback: {e}")
    
    def start_cluster(self):
        """Iniciar todo el cluster con delays entre servidores"""
        def start_thread():
            try:
                servers = list(self.cluster_manager.servers.keys())
                if not servers:
                    self.log_callback("ERROR", "❌ No hay servidores en el cluster para iniciar")
                    return
                
                self.log_callback("INFO", f"🚀 Iniciando cluster con {len(servers)} servidor(es)...")
                
                for i, server_name in enumerate(servers):
                    try:
                        self.log_callback("INFO", f"▶️ Iniciando servidor {i+1}/{len(servers)}: {server_name}")
                        
                        # Usar el principal_panel para iniciar el servidor si está disponible
                        if self.main_window and hasattr(self.main_window, 'principal_panel'):
                            self.main_window.principal_panel.start_server_with_config(capture_console=True, server_name=server_name)
                        else:
                            # Fallback al método del cluster_manager
                            server_instance = self.cluster_manager.servers[server_name]
                            server_instance.start()
                        
                        # Delay entre servidores (excepto el último)
                        if i < len(servers) - 1:
                            delay_seconds = 5  # 5 segundos de delay
                            self.log_callback("INFO", f"⏳ Esperando {delay_seconds} segundos antes del siguiente servidor...")
                            time.sleep(delay_seconds)
                            
                    except Exception as e:
                        self.log_callback("ERROR", f"❌ Error iniciando servidor {server_name}: {e}")
                
                self.log_callback("INFO", "✅ Proceso de inicio del cluster completado")
                try:
                    self.after(0, self.update_cluster_stats)
                except Exception:
                    pass
                
            except Exception as e:
                self.log_callback("ERROR", f"❌ Error en inicio del cluster: {e}")
        
        threading.Thread(target=start_thread, daemon=True).start()
    
    def stop_cluster(self):
        """Detener todo el cluster con delays entre servidores"""
        def stop_thread():
            try:
                servers = list(self.cluster_manager.servers.keys())
                if not servers:
                    self.log_callback("ERROR", "❌ No hay servidores en el cluster para detener")
                    return
                
                self.log_callback("INFO", f"🛑 Deteniendo cluster con {len(servers)} servidor(es)...")
                
                for i, server_name in enumerate(servers):
                    try:
                        self.log_callback("INFO", f"⏹️ Deteniendo servidor {i+1}/{len(servers)}: {server_name}")
                        
                        # Usar el principal_panel para detener el servidor si está disponible
                        if self.main_window and hasattr(self.main_window, 'principal_panel'):
                            self.main_window.principal_panel.stop_server_with_config(server_name=server_name)
                        else:
                            # Fallback al método del cluster_manager
                            server_instance = self.cluster_manager.servers[server_name]
                            server_instance.stop()
                        
                        # Delay entre servidores (excepto el último)
                        if i < len(servers) - 1:
                            delay_seconds = 3  # 3 segundos de delay
                            self.log_callback("INFO", f"⏳ Esperando {delay_seconds} segundos antes del siguiente servidor...")
                            time.sleep(delay_seconds)
                            
                    except Exception as e:
                        self.log_callback("ERROR", f"❌ Error deteniendo servidor {server_name}: {e}")
                
                self.log_callback("INFO", "✅ Proceso de detención del cluster completado")
                # Verificar si la ventana aún existe antes de programar actualización
                self._safe_schedule_ui_update(self.update_cluster_stats)
                
            except Exception as e:
                self.log_callback("ERROR", f"❌ Error en detención del cluster: {e}")
        
        threading.Thread(target=stop_thread, daemon=True).start()
    
    def restart_cluster(self):
        """Reiniciar todo el cluster con delays entre servidores"""
        def restart_thread():
            try:
                servers = list(self.cluster_manager.servers.keys())
                if not servers:
                    self.log_callback("ERROR", "❌ No hay servidores en el cluster para reiniciar")
                    return
                
                self.log_callback("INFO", f"🔄 Reiniciando cluster con {len(servers)} servidor(es)...")
                
                for i, server_name in enumerate(servers):
                    try:
                        self.log_callback("INFO", f"🔄 Reiniciando servidor {i+1}/{len(servers)}: {server_name}")
                        
                        # Usar el principal_panel para reiniciar el servidor si está disponible
                        if self.main_window and hasattr(self.main_window, 'principal_panel'):
                            self.main_window.principal_panel.restart_server_with_config(capture_console=True, server_name=server_name)
                        else:
                            # Fallback al método del cluster_manager
                            server_instance = self.cluster_manager.servers[server_name]
                            server_instance.restart()
                        
                        # Delay entre servidores (excepto el último)
                        if i < len(servers) - 1:
                            delay_seconds = 8  # 8 segundos de delay para reinicio
                            self.log_callback("INFO", f"⏳ Esperando {delay_seconds} segundos antes del siguiente servidor...")
                            time.sleep(delay_seconds)
                            
                    except Exception as e:
                        self.log_callback("ERROR", f"❌ Error reiniciando servidor {server_name}: {e}")
                
                self.log_callback("INFO", "✅ Proceso de reinicio del cluster completado")
                # Verificar si la ventana aún existe antes de programar actualización
                self._safe_schedule_ui_update(self.update_cluster_stats)
                
            except Exception as e:
                self.log_callback("ERROR", f"❌ Error en reinicio del cluster: {e}")
        
        threading.Thread(target=restart_thread, daemon=True).start()
    
    def add_server(self):
        """Agregar un servidor configurado al cluster"""
        dialog = AddServerDialog(self, self.cluster_manager, self.main_window)
        if dialog.result:
            self.refresh_server_frames()
            self.update_cluster_stats()
    
    def configure_cluster(self):
        """Configurar cluster"""
        messagebox.showinfo("Configuración", "Panel de configuración del cluster\n\nEsta funcionalidad se implementará próximamente.")
    
    def clear_logs(self):
        """Limpiar logs"""
        self.logs_text.delete("0.0", "end")
    
    def export_logs(self):
        """Exportar logs"""
        messagebox.showinfo("Exportar", "Funcionalidad de exportación de logs\n\nEsta funcionalidad se implementará próximamente.")
    
    def on_cluster_mode_changed(self, is_cluster_mode):
        """Manejar el cambio de modo cluster"""
        try:
            if is_cluster_mode:
                # Habilitar todos los elementos del cluster panel
                self.enable_all_elements()
                self.logger.info("🌐 Cluster panel habilitado")
            else:
                # Deshabilitar todos los elementos del cluster panel
                self.disable_all_elements()
                self.logger.info("📱 Cluster panel deshabilitado")
        except Exception as e:
            self.logger.error(f"Error al cambiar modo cluster en cluster panel: {e}")
    
    def disable_all_elements(self):
        """Deshabilitar todos los elementos del cluster panel"""
        try:
            # Deshabilitar botones principales del cluster
            if hasattr(self, 'start_cluster_btn'):
                self.start_cluster_btn.configure(state="disabled")
            if hasattr(self, 'stop_cluster_btn'):
                self.stop_cluster_btn.configure(state="disabled")
            if hasattr(self, 'restart_cluster_btn'):
                self.restart_cluster_btn.configure(state="disabled")
            if hasattr(self, 'add_server_btn'):
                self.add_server_btn.configure(state="disabled")
            if hasattr(self, 'cluster_config_btn'):
                self.cluster_config_btn.configure(state="disabled")
            
            # Deshabilitar botones de logs
            for widget in self.winfo_children():
                self._disable_widget_recursive(widget)
            
            # Deshabilitar todos los frames de servidores
            for frame in self.server_frames.values():
                self._disable_server_frame(frame)
                
        except Exception as e:
            self.logger.error(f"Error deshabilitando elementos del cluster panel: {e}")
    
    def enable_all_elements(self):
        """Habilitar todos los elementos del cluster panel"""
        try:
            # Habilitar botones principales del cluster
            if hasattr(self, 'start_cluster_btn'):
                self.start_cluster_btn.configure(state="normal")
            if hasattr(self, 'stop_cluster_btn'):
                self.stop_cluster_btn.configure(state="normal")
            if hasattr(self, 'restart_cluster_btn'):
                self.restart_cluster_btn.configure(state="normal")
            if hasattr(self, 'add_server_btn'):
                self.add_server_btn.configure(state="normal")
            if hasattr(self, 'cluster_config_btn'):
                self.cluster_config_btn.configure(state="normal")
            
            # Habilitar botones de logs
            for widget in self.winfo_children():
                self._enable_widget_recursive(widget)
            
            # Habilitar todos los frames de servidores
            for frame in self.server_frames.values():
                self._enable_server_frame(frame)
                
        except Exception as e:
            self.logger.error(f"Error habilitando elementos del cluster panel: {e}")
    
    def _disable_widget_recursive(self, widget):
        """Deshabilitar widget y sus hijos recursivamente"""
        try:
            # Deshabilitar el widget actual si es un botón
            if isinstance(widget, ctk.CTkButton):
                widget.configure(state="disabled")
            elif isinstance(widget, ctk.CTkTextbox):
                widget.configure(state="disabled")
            
            # Recursivamente deshabilitar widgets hijos
            for child in widget.winfo_children():
                self._disable_widget_recursive(child)
        except Exception:
            pass
    
    def _enable_widget_recursive(self, widget):
        """Habilitar widget y sus hijos recursivamente"""
        try:
            # Habilitar el widget actual si es un botón
            if isinstance(widget, ctk.CTkButton):
                widget.configure(state="normal")
            elif isinstance(widget, ctk.CTkTextbox):
                widget.configure(state="normal")
            
            # Recursivamente habilitar widgets hijos
            for child in widget.winfo_children():
                self._enable_widget_recursive(child)
        except Exception:
            pass
    
    def _disable_server_frame(self, server_frame):
        """Deshabilitar todos los elementos de un frame de servidor"""
        try:
            if hasattr(server_frame, 'start_btn'):
                server_frame.start_btn.configure(state="disabled")
            if hasattr(server_frame, 'stop_btn'):
                server_frame.stop_btn.configure(state="disabled")
            if hasattr(server_frame, 'restart_btn'):
                server_frame.restart_btn.configure(state="disabled")
            if hasattr(server_frame, 'remove_btn'):
                server_frame.remove_btn.configure(state="disabled")
            if hasattr(server_frame, 'config_btn'):
                server_frame.config_btn.configure(state="disabled")
        except Exception:
            pass
    
    def _enable_server_frame(self, server_frame):
        """Habilitar todos los elementos de un frame de servidor"""
        try:
            if hasattr(server_frame, 'start_btn'):
                server_frame.start_btn.configure(state="normal")
            if hasattr(server_frame, 'stop_btn'):
                server_frame.stop_btn.configure(state="normal")
            if hasattr(server_frame, 'restart_btn'):
                server_frame.restart_btn.configure(state="normal")
            if hasattr(server_frame, 'remove_btn'):
                server_frame.remove_btn.configure(state="normal")
            if hasattr(server_frame, 'config_btn'):
                server_frame.config_btn.configure(state="normal")
        except Exception:
            pass

    def on_closing(self):
        """Manejar cierre del panel"""
        self.stop_auto_update()
        self.cluster_manager.stop_cluster_monitoring()

class AddServerDialog:
    """Diálogo para agregar servidor configurado al cluster"""
    
    def __init__(self, parent, cluster_manager: ClusterManager, main_window=None):
        self.parent = parent
        self.cluster_manager = cluster_manager
        self.main_window = main_window
        self.result = None
        self.available_servers = []
        
        self.get_available_servers()
        self.create_dialog()
    
    def get_available_servers(self):
        """Obtener lista de servidores configurados disponibles"""
        try:
            import os
            self.available_servers = []
            
            if not self.main_window:
                return
            
            # Obtener servidores del sistema de archivos
            if hasattr(self.main_window, 'server_panel'):
                config_manager = self.main_window.config_manager
                root_path = config_manager.get("server", "root_path", "").strip()
                
                if root_path and os.path.exists(root_path):
                    for item in os.listdir(root_path):
                        item_path = os.path.join(root_path, item)
                        if os.path.isdir(item_path) and item != "SteamCMD":
                            # Verificar que sea una carpeta de servidor válida
                            if self._is_valid_server_directory(item_path):
                                # Verificar que no esté ya en el cluster
                                if item not in self.cluster_manager.servers:
                                    self.available_servers.append(item)
            
        except Exception as e:
            if hasattr(self.main_window, 'logger'):
                self.main_window.logger.error(f"Error obteniendo servidores disponibles: {e}")
    
    def _is_valid_server_directory(self, server_path):
        """Verificar si un directorio contiene datos válidos de servidor ARK"""
        try:
            import os
            
            # Rutas típicas de archivos de configuración de ARK
            config_paths = [
                os.path.join(server_path, "ShooterGame", "Saved", "Config", "WindowsServer", "GameUserSettings.ini"),
                os.path.join(server_path, "ShooterGame", "Saved", "Config", "WindowsServer", "Game.ini"),
                os.path.join(server_path, "ShooterGame", "Binaries", "Win64", "ArkAscendedServer.exe"),
                os.path.join(server_path, "ShooterGame", "Content"),
                os.path.join(server_path, "ShooterGame", "Saved")
            ]
            
            # Verificar si existe al menos uno de los archivos/carpetas críticos
            critical_found = False
            for path in config_paths[:3]:  # Archivos críticos
                if os.path.exists(path):
                    critical_found = True
                    break
            
            # Verificar carpetas importantes
            folders_found = 0
            for path in config_paths[3:]:  # Carpetas importantes
                if os.path.exists(path):
                    folders_found += 1
            
            # Es válido si tiene al menos un archivo crítico O ambas carpetas importantes
            return critical_found or folders_found >= 2
            
        except Exception as e:
            if hasattr(self.main_window, 'logger'):
                self.main_window.logger.error(f"Error validando directorio de servidor {server_path}: {e}")
            return False
    
    def create_dialog(self):
        """Crear diálogo"""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Agregar Servidor al Cluster")
        self.dialog.geometry("500x350")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Centrar diálogo
        self.dialog.geometry("+%d+%d" % (self.parent.winfo_rootx() + 50, self.parent.winfo_rooty() + 50))
        
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Verificar si hay servidores disponibles
        if not self.available_servers:
            ctk.CTkLabel(main_frame, text="No hay servidores configurados disponibles para agregar al cluster.", 
                        wraplength=400, font=("Arial", 12)).pack(pady=20)
            ctk.CTkLabel(main_frame, text="Todos los servidores ya están en el cluster o no hay servidores configurados.", 
                        wraplength=400, font=("Arial", 11), text_color="gray").pack(pady=10)
            
            ctk.CTkButton(main_frame, text="Cerrar", command=self.cancel).pack(pady=20)
            return
        
        # Título
        ctk.CTkLabel(main_frame, text="Seleccionar servidor configurado para agregar al cluster:", 
                    font=("Arial", 14, "bold")).pack(pady=(20, 30))
        
        # Dropdown de servidores
        ctk.CTkLabel(main_frame, text="Servidor:", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
        self.server_var = tk.StringVar()
        server_combo = ctk.CTkComboBox(main_frame, variable=self.server_var, values=self.available_servers, 
                                      state="readonly", width=400)
        server_combo.pack(fill="x", pady=(0, 20))
        
        # Información adicional
        info_text = "El servidor seleccionado será agregado al cluster con su configuración actual."
        ctk.CTkLabel(main_frame, text=info_text, wraplength=400, text_color="gray", 
                    font=("Arial", 11)).pack(pady=(0, 20))
        
        # Botones
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(pady=30)
        
        ctk.CTkButton(buttons_frame, text="Agregar al Cluster", command=self.add_server, 
                     width=150, height=35).pack(side="left", padx=(0, 15))
        ctk.CTkButton(buttons_frame, text="Cancelar", command=self.cancel, 
                     width=100, height=35, fg_color="gray", hover_color="darkgray").pack(side="left")
        
        # Focus inicial
        if self.available_servers:
            server_combo.set(self.available_servers[0])
        self.dialog.focus_set()
    
    def add_server(self):
        """Agregar servidor configurado al cluster"""
        try:
            # Validar selección
            server_name = self.server_var.get().strip()
            if not server_name:
                messagebox.showerror("Error", "Debe seleccionar un servidor")
                return
            
            if server_name in self.cluster_manager.servers:
                messagebox.showerror("Error", f"El servidor '{server_name}' ya está en el cluster")
                return
            
            # Obtener configuración del servidor desde principal_panel si está disponible
            server_config = {
                "name": server_name,
                "map": "TheIsland_WP",  # Valor por defecto
                "port": 7777,
                "query_port": 27015,
                "rcon_port": 32330,
                "priority": len(self.cluster_manager.servers) + 1,
                "auto_start": True,
                "transfer_allowed": True
            }
            
            # Intentar obtener configuración guardada del servidor
            if self.main_window and hasattr(self.main_window, 'principal_panel'):
                principal_panel = self.main_window.principal_panel
                if hasattr(principal_panel, 'server_configs') and server_name in principal_panel.server_configs:
                    saved_config = principal_panel.server_configs[server_name]
                    server_config.update({
                        "port": int(saved_config.get("port", 7777)),
                        "query_port": int(saved_config.get("query_port", 27015)),
                        "rcon_port": int(saved_config.get("rcon_port", 32330))
                    })
                
                # Obtener el mapa seleccionado del servidor
                # Primero intentar desde main_window si el servidor está seleccionado
                selected_map = None
                if (hasattr(self.main_window, 'selected_server') and 
                    self.main_window.selected_server == server_name and 
                    hasattr(self.main_window, 'selected_map') and 
                    self.main_window.selected_map):
                    selected_map = self.main_window.selected_map
                
                # Si tenemos un mapa seleccionado, convertirlo al identificador técnico
                if selected_map:
                    # Mapear nombres amigables a identificadores técnicos
                    map_identifiers = {
                        "The Island": "TheIsland_WP",
                        "TheIsland": "TheIsland_WP",
                        "TheIsland_WP": "TheIsland_WP",
                        "The Center": "TheCenter_WP",
                        "TheCenter": "TheCenter_WP",
                        "TheCenter_WP": "TheCenter_WP",
                        "Scorched Earth": "ScorchedEarth_WP",
                        "ScorchedEarth": "ScorchedEarth_WP",
                        "ScorchedEarth_WP": "ScorchedEarth_WP",
                        "Ragnarok": "Ragnarok_WP",
                        "Ragnarok_WP": "Ragnarok_WP",
                        "Aberration": "Aberration_P",
                        "Aberration_P": "Aberration_P",
                        "Extinction": "Extinction_WP",
                        "Extinction_WP": "Extinction_WP",
                        "Genesis": "Genesis_WP",
                        "Genesis_WP": "Genesis_WP",
                        "Genesis2": "Gen2_WP",
                        "Gen2_WP": "Gen2_WP",
                        "Crystal Isles": "CrystalIsles_WP",
                        "CrystalIsles": "CrystalIsles_WP",
                        "CrystalIsles_WP": "CrystalIsles_WP",
                        "Lost Island": "LostIsland_WP",
                        "LostIsland": "LostIsland_WP",
                        "LostIsland_WP": "LostIsland_WP",
                        "Fjordur": "Fjordur_WP",
                        "Fjordur_WP": "Fjordur_WP"
                    }
                    
                    if selected_map in map_identifiers:
                        server_config["map"] = map_identifiers[selected_map]
                        print(f"DEBUG: Mapa configurado para {server_name}: {selected_map} -> {map_identifiers[selected_map]}")
                    else:
                        print(f"DEBUG: Mapa no reconocido '{selected_map}', usando TheIsland_WP por defecto")
            
            # Agregar servidor al cluster
            if self.cluster_manager.add_server(server_name, server_config):
                self.result = True
                messagebox.showinfo("Éxito", f"Servidor '{server_name}' agregado al cluster correctamente")
                self.dialog.destroy()
                # Notificar al panel padre para que actualice la UI
                if hasattr(self.parent, 'refresh_server_frames'):
                    self.parent.refresh_server_frames()
                    self.parent.update_cluster_stats()
            else:
                messagebox.showerror("Error", "No se pudo agregar el servidor al cluster")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error agregando servidor al cluster: {e}")
    
    def cancel(self):
        """Cancelar diálogo"""
        self.result = False
        self.dialog.destroy()

# Agregar método al ClusterPanel para actualizar conteos de jugadores
def update_player_counts(self):
    """Actualizar conteos de jugadores usando el PlayerMonitor"""
    try:
        if not hasattr(self.main_window, 'player_monitor'):
            return
            
        player_monitor = self.main_window.player_monitor
        
        # Actualizar conteo individual de cada servidor
        for server_name, server_frame in self.server_frames.items():
            if hasattr(server_frame, 'players_label'):
                count = player_monitor.get_player_count(server_name)
                server_frame.players_label.configure(text=f"👥 {count}")
        
        # Actualizar conteo total del cluster
        total_players = 0
        all_servers = player_monitor.get_all_servers()
        for server in all_servers:
            total_players += player_monitor.get_player_count(server)
        
        if hasattr(self, 'total_players_label'):
            self.total_players_label.configure(text=str(total_players))
            
    except Exception as e:
        if hasattr(self, 'logger'):
            self.logger.error(f"Error actualizando conteos de jugadores en cluster: {e}")

# Agregar el método a la clase ClusterPanel
ClusterPanel.update_player_counts = update_player_counts