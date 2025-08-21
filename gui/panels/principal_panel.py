import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import os
import json
import time


class ToolTip:
    """Clase mejorada para crear tooltips que muestran descripciones al pasar el mouse"""
    def __init__(self, widget, text='tooltip info'):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.hide_id = None
        self.x = self.y = 0
        
        self.widget.bind('<Enter>', self.enter, add='+')
        self.widget.bind('<Leave>', self.leave, add='+')
        self.widget.bind('<Motion>', self.motion, add='+')
        self.widget.bind('<Button-1>', self.leave, add='+')  # Ocultar al hacer clic

    def enter(self, event=None):
        self.cancel_hide()
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.schedule_hide()

    def motion(self, event=None):
        if self.tipwindow:
            # Si ya está visible, mantenerlo
            self.cancel_hide()
        else:
            # Si no está visible, programar para mostrar
            self.unschedule()
            self.schedule()

    def schedule(self):
        self.unschedule()
        try:
            self.id = self.widget.after(800, self.showtip)  # Aumentar delay a 800ms
        except Exception:
            pass

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
        self.id = None

    def schedule_hide(self):
        self.cancel_hide()
        try:
            self.hide_id = self.widget.after(100, self.hidetip)  # Ocultar rápidamente
        except Exception:
            pass

    def cancel_hide(self):
        if self.hide_id:
            self.widget.after_cancel(self.hide_id)
        self.hide_id = None

    def showtip(self, event=None):
        if self.tipwindow:
            return  # Ya está visible
            
        try:
            x = self.widget.winfo_rootx() + 25
            y = self.widget.winfo_rooty() + 25
            
            # Crear ventana del tooltip
            self.tipwindow = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_attributes('-topmost', True)  # Mantener encima
            tw.wm_geometry(f"+{x}+{y}")
            
            # Estilo del tooltip mejorado
            label = tk.Label(tw, text=self.text, justify='left',
                            background='#ffffcc', relief='solid', borderwidth=1,
                            font=('Segoe UI', '9', 'normal'), wraplength=350,
                            padx=8, pady=6)
            label.pack()
            
            # Auto-ocultar después de un tiempo
            try:
                tw.after(5000, self.hidetip)  # Auto-ocultar después de 5 segundos
            except Exception:
                pass
            
        except tk.TclError:
            # El widget ya no existe
            self.hidetip()

    def hidetip(self):
        try:
            tw = self.tipwindow
            self.tipwindow = None
            if tw:
                tw.destroy()
        except (tk.TclError, AttributeError):
            # Ignorar errores si el widget ya no existe
            pass
        finally:
            self.cancel_hide()
            self.unschedule()
import json
import re
import logging
from utils.config_manager import ConfigManager
from utils.app_settings import AppSettings
import threading
import requests
import configparser
from datetime import datetime

class PrincipalPanel:
    def __init__(self, parent, config_manager, logger, main_window=None):
        self.parent = parent
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        
        # Sistema de configuración por servidor
        self.server_configs = {}
        self.current_server = None
        self.load_all_server_configs()
        self.server_manager = None
        
        # Inicializar server_manager si está disponible
        try:
            from utils.server_manager import ServerManager
            self.server_manager = ServerManager(config_manager)
        except ImportError:
            self.logger.warning("ServerManager no disponible")
        
        # Variables para el servidor seleccionado
        self.selected_server = None
        self.selected_map = None
        
        # Crear widgets
        self.create_widgets()
        
        # Cargar configuración guardada
        self.load_saved_config()
        
        # Cargar configuración del cluster
        self.load_cluster_configuration()
    
    def create_widgets(self):
        """Crear todos los widgets de la pestaña principal"""
        # Frame principal con scroll
        main_frame = ctk.CTkScrollableFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Título principal
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Configuración Principal del Servidor", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 5))
        
        # Frame para configuración de cluster
        cluster_frame = ctk.CTkFrame(main_frame)
        cluster_frame.pack(fill="x", padx=5, pady=5)
        
        # Título de configuración de cluster
        ctk.CTkLabel(
            cluster_frame, 
            text="🌐 Configuración de Cluster", 
            font=("Arial", 13, "bold")
        ).pack(pady=5)
        
        # Switch para habilitar cluster
        self.cluster_enabled_var = ctk.BooleanVar(value=False)
        cluster_switch_frame = ctk.CTkFrame(cluster_frame, fg_color="transparent")
        cluster_switch_frame.pack(fill="x", padx=10, pady=5)
        
        self.cluster_switch = ctk.CTkSwitch(
            cluster_switch_frame,
            text="🔗 Habilitar Modo Cluster (Múltiples Servidores)",
            variable=self.cluster_enabled_var,
            font=("Arial", 12, "bold"),
            command=self.on_cluster_toggle
        )
        self.cluster_switch.pack(anchor="w")
        
        # Frame para configuraciones de cluster (inicialmente oculto)
        self.cluster_config_frame = ctk.CTkFrame(cluster_frame)
        
        # Configuraciones de cluster en dos columnas
        cluster_columns_frame = ctk.CTkFrame(self.cluster_config_frame, fg_color="transparent")
        cluster_columns_frame.pack(fill="x", padx=10, pady=10)
        
        cluster_columns_frame.grid_columnconfigure(0, weight=1)
        cluster_columns_frame.grid_columnconfigure(1, weight=1)
        
        # Columna izquierda - Cluster ID y Carpeta de datos
        cluster_col1 = ctk.CTkFrame(cluster_columns_frame, fg_color="transparent")
        cluster_col1.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Cluster ID
        ctk.CTkLabel(cluster_col1, text="🆔 Cluster ID:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.cluster_id_entry = ctk.CTkEntry(cluster_col1, placeholder_text="MiClusterARK", width=200, height=28)
        self.cluster_id_entry.pack(fill="x", pady=(0, 6))
        
        # Carpeta de datos compartidos
        ctk.CTkLabel(cluster_col1, text="📁 Carpeta de Datos Compartidos:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        cluster_data_frame = ctk.CTkFrame(cluster_col1, fg_color="transparent")
        cluster_data_frame.pack(fill="x", pady=(0, 6))
        
        self.cluster_data_entry = ctk.CTkEntry(cluster_data_frame, placeholder_text="Cluster", height=28)
        self.cluster_data_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.cluster_data_button = ctk.CTkButton(
            cluster_data_frame,
            text="📂",
            command=self.browse_cluster_data_path,
            width=30,
            height=28
        )
        self.cluster_data_button.pack(side="right")
        
        # Columna derecha - Configuraciones adicionales
        cluster_col2 = ctk.CTkFrame(cluster_columns_frame, fg_color="transparent")
        cluster_col2.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Switches para transferencias de clúster
        self.allow_character_transfer_var = ctk.BooleanVar(value=True)
        self.character_transfer_switch = ctk.CTkSwitch(
            cluster_col2,
            text="👤 Permitir Transferencia de Personajes",
            variable=self.allow_character_transfer_var,
            font=("Arial", 9),
            command=self.save_cluster_configuration
        )
        self.character_transfer_switch.pack(anchor="w", pady=2)
        # Tooltip para transferencia de personajes
        try:
            ToolTip(self.character_transfer_switch, "NoTributeCharacterUploads / NoTributeCharacterDownloads")
        except: pass
        
        self.allow_item_transfer_var = ctk.BooleanVar(value=True)
        self.item_transfer_switch = ctk.CTkSwitch(
            cluster_col2,
            text="🎒 Permitir Transferencia de Items",
            variable=self.allow_item_transfer_var,
            font=("Arial", 9),
            command=self.save_cluster_configuration
        )
        self.item_transfer_switch.pack(anchor="w", pady=2)
        # Tooltip para transferencia de items
        try:
            ToolTip(self.item_transfer_switch, "NoTributeItemUploads / NoTributeItemDownloads")
        except: pass
        
        self.allow_dino_transfer_var = ctk.BooleanVar(value=True)
        self.dino_transfer_switch = ctk.CTkSwitch(
            cluster_col2,
            text="🦕 Permitir Transferencia de Dinos",
            variable=self.allow_dino_transfer_var,
            font=("Arial", 9),
            command=self.save_cluster_configuration
        )
        self.dino_transfer_switch.pack(anchor="w", pady=2)
        # Tooltip para transferencia de dinos
        try:
            ToolTip(self.dino_transfer_switch, "NoTributeDinoUploads / NoTributeDinoDownloads")
        except: pass
        
        # Separador para opciones de prevención
        separator_frame = ctk.CTkFrame(cluster_col2, height=2, fg_color="gray")
        separator_frame.pack(fill="x", pady=(10, 5))
        
        ctk.CTkLabel(
            cluster_col2,
            text="🚫 Opciones de Prevención (GameUserSettings.ini):",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(5, 2))
        
        # Switches para PreventDownload
        self.prevent_download_survivors_var = ctk.BooleanVar(value=False)
        self.prevent_download_survivors_switch = ctk.CTkSwitch(
            cluster_col2,
            text="🚫👤 Prevenir Descarga de Personajes",
            variable=self.prevent_download_survivors_var,
            font=("Arial", 9),
            command=self.save_cluster_configuration
        )
        self.prevent_download_survivors_switch.pack(anchor="w", pady=2)
        # Tooltip para prevenir descarga de personajes
        try:
            ToolTip(self.prevent_download_survivors_switch, "PreventDownloadSurvivors=True")
        except: pass
        
        self.prevent_download_items_var = ctk.BooleanVar(value=False)
        self.prevent_download_items_switch = ctk.CTkSwitch(
            cluster_col2,
            text="🚫🎒 Prevenir Descarga de Items",
            variable=self.prevent_download_items_var,
            font=("Arial", 9),
            command=self.save_cluster_configuration
        )
        self.prevent_download_items_switch.pack(anchor="w", pady=2)
        # Tooltip para prevenir descarga de items
        try:
            ToolTip(self.prevent_download_items_switch, "PreventDownloadItems=True")
        except: pass
        
        self.prevent_download_dinos_var = ctk.BooleanVar(value=False)
        self.prevent_download_dinos_switch = ctk.CTkSwitch(
            cluster_col2,
            text="🚫🦕 Prevenir Descarga de Dinos",
            variable=self.prevent_download_dinos_var,
            font=("Arial", 9),
            command=self.save_cluster_configuration
        )
        self.prevent_download_dinos_switch.pack(anchor="w", pady=2)
        # Tooltip para prevenir descarga de dinos
        try:
            ToolTip(self.prevent_download_dinos_switch, "PreventDownloadDinos=True")
        except: pass
        
        # Switches para PreventUpload
        self.prevent_upload_survivors_var = ctk.BooleanVar(value=False)
        self.prevent_upload_survivors_switch = ctk.CTkSwitch(
            cluster_col2,
            text="🚫👤 Prevenir Subida de Personajes",
            variable=self.prevent_upload_survivors_var,
            font=("Arial", 9),
            command=self.save_cluster_configuration
        )
        self.prevent_upload_survivors_switch.pack(anchor="w", pady=2)
        # Tooltip para prevenir subida de personajes
        try:
            ToolTip(self.prevent_upload_survivors_switch, "PreventUploadSurvivors=True")
        except: pass
        
        self.prevent_upload_items_var = ctk.BooleanVar(value=False)
        self.prevent_upload_items_switch = ctk.CTkSwitch(
            cluster_col2,
            text="🚫🎒 Prevenir Subida de Items",
            variable=self.prevent_upload_items_var,
            font=("Arial", 9),
            command=self.save_cluster_configuration
        )
        self.prevent_upload_items_switch.pack(anchor="w", pady=2)
        # Tooltip para prevenir subida de items
        try:
            ToolTip(self.prevent_upload_items_switch, "PreventUploadItems=True")
        except: pass
        
        self.prevent_upload_dinos_var = ctk.BooleanVar(value=False)
        self.prevent_upload_dinos_switch = ctk.CTkSwitch(
            cluster_col2,
            text="🚫🦕 Prevenir Subida de Dinos",
            variable=self.prevent_upload_dinos_var,
            font=("Arial", 9),
            command=self.save_cluster_configuration
        )
        self.prevent_upload_dinos_switch.pack(anchor="w", pady=2)
        # Tooltip para prevenir subida de dinos
        try:
            ToolTip(self.prevent_upload_dinos_switch, "PreventUploadDinos=True")
        except: pass
        
        # Frame para parámetros básicos
        basic_frame = ctk.CTkFrame(main_frame)
        basic_frame.pack(fill="x", padx=5, pady=5)
        
        # Título de parámetros básicos
        ctk.CTkLabel(
            basic_frame, 
            text="Parámetros Básicos", 
            font=("Arial", 13, "bold")
        ).pack(pady=5)
        
        # Crear layout en múltiples columnas
        columns_frame = ctk.CTkFrame(basic_frame, fg_color="transparent")
        columns_frame.pack(fill="x", padx=5, pady=5)
        
        # Configurar columnas (3 columnas)
        columns_frame.grid_columnconfigure(0, weight=1)
        columns_frame.grid_columnconfigure(1, weight=1)
        columns_frame.grid_columnconfigure(2, weight=1)
        
        # Primera columna
        col1_frame = ctk.CTkFrame(columns_frame, fg_color="transparent")
        col1_frame.grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        
        # SessionName
        ctk.CTkLabel(col1_frame, text="SessionName:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.session_name_entry = ctk.CTkEntry(col1_frame, placeholder_text="Nombre del servidor", width=200, height=28)
        self.session_name_entry.pack(fill="x", pady=(0, 6))
        
        # MaxPlayers
        ctk.CTkLabel(col1_frame, text="MaxPlayers:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.max_players_entry = ctk.CTkEntry(col1_frame, placeholder_text="70", width=200, height=28)
        self.max_players_entry.pack(fill="x", pady=(0, 3))
        
        # Switch para MaxPlayers como argumento
        self.maxplayers_as_arg_var = ctk.BooleanVar(value=False)
        maxplayers_switch_frame = ctk.CTkFrame(col1_frame, fg_color="transparent")
        maxplayers_switch_frame.pack(fill="x", pady=(0, 6))
        
        self.maxplayers_switch = ctk.CTkSwitch(
            maxplayers_switch_frame,
            text="Como argumento -WinLiveMaxPlayers",
            variable=self.maxplayers_as_arg_var,
            font=("Arial", 9),
            command=self.on_maxplayers_switch_change
        )
        self.maxplayers_switch.pack(anchor="w")
        
        # QueryPort
        ctk.CTkLabel(col1_frame, text="QueryPort:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.query_port_entry = ctk.CTkEntry(col1_frame, placeholder_text="27015", width=200, height=28)
        self.query_port_entry.pack(fill="x", pady=(0, 6))
        
        # Segunda columna
        col2_frame = ctk.CTkFrame(columns_frame, fg_color="transparent")
        col2_frame.grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        
        # ServerPassword
        ctk.CTkLabel(col2_frame, text="ServerPassword:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.server_password_entry = ctk.CTkEntry(col2_frame, placeholder_text="Contraseña del servidor", show="*", width=200, height=28)
        self.server_password_entry.pack(fill="x", pady=(0, 6))
        
        # Port
        ctk.CTkLabel(col2_frame, text="Port:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.port_entry = ctk.CTkEntry(col2_frame, placeholder_text="7777", width=200, height=28)
        self.port_entry.pack(fill="x", pady=(0, 6))
        
        # MultiHome
        multihome_label_frame = ctk.CTkFrame(col2_frame, fg_color="transparent")
        multihome_label_frame.pack(fill="x", pady=(0, 2))
        
        ctk.CTkLabel(multihome_label_frame, text="MultiHome:", font=("Arial", 11, "bold")).pack(side="left")
        
        self.ip_auto_button = ctk.CTkButton(
            multihome_label_frame,
            text="🌐 IP Pública",
            command=self.get_public_ip,
            width=80,
            height=20,
            font=("Arial", 9)
        )
        self.ip_auto_button.pack(side="right")
        
        self.multihome_entry = ctk.CTkEntry(col2_frame, placeholder_text="127.0.0.1", width=200, height=28)
        self.multihome_entry.pack(fill="x", pady=(0, 6))
        
        # Tercera columna
        col3_frame = ctk.CTkFrame(columns_frame, fg_color="transparent")
        col3_frame.grid(row=0, column=2, padx=3, pady=3, sticky="ew")
        
        # AdminPassword
        ctk.CTkLabel(col3_frame, text="AdminPassword:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.admin_password_entry = ctk.CTkEntry(col3_frame, placeholder_text="Contraseña de admin", show="*", width=200, height=28)
        self.admin_password_entry.pack(fill="x", pady=(0, 6))
        
        # Message (MessageOfTheDay)
        ctk.CTkLabel(col3_frame, text="Message:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.message_entry = ctk.CTkEntry(col3_frame, placeholder_text="Mensaje del día", width=200, height=28)
        self.message_entry.pack(fill="x", pady=(0, 6))
        
        # Duration (MessageOfTheDay)
        ctk.CTkLabel(col3_frame, text="Duration:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.duration_entry = ctk.CTkEntry(col3_frame, placeholder_text="60", width=200, height=28)
        self.duration_entry.pack(fill="x", pady=(0, 6))
        
        # Frame para argumentos opcionales
        optional_args_frame = ctk.CTkFrame(main_frame)
        optional_args_frame.pack(fill="x", padx=5, pady=5)
        
        # Título de argumentos opcionales
        ctk.CTkLabel(
            optional_args_frame, 
            text="⚙️ Argumentos de Inicio Opcionales", 
            font=("Arial", 13, "bold")
        ).pack(pady=5)
        
        # Descripción
        ctk.CTkLabel(
            optional_args_frame, 
            text="Seleccione los argumentos adicionales que desea incluir al iniciar el servidor:",
            font=("Arial", 10)
        ).pack(pady=(0, 5))
        
        # Frame para checkboxes en dos columnas
        checkboxes_frame = ctk.CTkFrame(optional_args_frame, fg_color="transparent")
        checkboxes_frame.pack(fill="x", padx=10, pady=5)
        
        # Configurar columnas
        checkboxes_frame.grid_columnconfigure(0, weight=1)
        checkboxes_frame.grid_columnconfigure(1, weight=1)
        
        # Columna izquierda
        left_col = ctk.CTkFrame(checkboxes_frame, fg_color="transparent")
        left_col.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Variables para los checkboxes
        self.server_arg_var = ctk.BooleanVar(value=True)  # Por defecto activado
        self.log_arg_var = ctk.BooleanVar(value=True)     # Por defecto activado
        self.nobattleye_var = ctk.BooleanVar(value=False)
        
        # Checkboxes columna izquierda
        self.server_checkbox = ctk.CTkCheckBox(
            left_col,
            text="🖥️ -server (Modo servidor dedicado)",
            variable=self.server_arg_var,
            font=("Arial", 11)
        )
        self.server_checkbox.pack(anchor="w", pady=3)
        
        self.log_checkbox = ctk.CTkCheckBox(
            left_col,
            text="📝 -log (Habilitar logging)",
            variable=self.log_arg_var,
            font=("Arial", 11)
        )
        self.log_checkbox.pack(anchor="w", pady=3)
        
        self.nobattleye_checkbox = ctk.CTkCheckBox(
            left_col,
            text="🛡️ -NoBattlEye (Deshabilitar BattlEye)",
            variable=self.nobattleye_var,
            font=("Arial", 11)
        )
        self.nobattleye_checkbox.pack(anchor="w", pady=3)
        
        # Columna derecha
        right_col = ctk.CTkFrame(checkboxes_frame, fg_color="transparent")
        right_col.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Variables para los checkboxes de la columna derecha
        self.servergamelog_var = ctk.BooleanVar(value=False)
        self.servergamelogincludetribelogs_var = ctk.BooleanVar(value=False)
        
        # Checkboxes columna derecha
        self.servergamelog_checkbox = ctk.CTkCheckBox(
            right_col,
            text="📊 -servergamelog (Log de eventos del juego)",
            variable=self.servergamelog_var,
            font=("Arial", 11)
        )
        self.servergamelog_checkbox.pack(anchor="w", pady=3)
        
        self.servergamelogincludetribelogs_checkbox = ctk.CTkCheckBox(
            right_col,
            text="🏛️ -servergamelogincludetribelogs (Incluir logs de tribus)",
            variable=self.servergamelogincludetribelogs_var,
            font=("Arial", 11)
        )
        self.servergamelogincludetribelogs_checkbox.pack(anchor="w", pady=3)
        
        # Frame para argumentos personalizados
        custom_frame = ctk.CTkFrame(main_frame)
        custom_frame.pack(fill="x", padx=5, pady=5)
        
        # Título de argumentos personalizados
        ctk.CTkLabel(
            custom_frame, 
            text="📝 Argumentos de Inicio Personalizados", 
            font=("Arial", 13, "bold")
        ).pack(pady=5)
        
        # Descripción
        ctk.CTkLabel(
            custom_frame, 
            text="Agregue argumentos adicionales para el servidor (uno por línea):",
            font=("Arial", 10)
        ).pack(pady=(0, 5))
        
        # Texto para argumentos personalizados
        self.custom_args_text = ctk.CTkTextbox(custom_frame, height=80)
        self.custom_args_text.pack(fill="x", padx=5, pady=5)
        
        # Frame para botones de acción
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", padx=5, pady=8)
        
        # Botones
        ctk.CTkButton(
            buttons_frame,
            text="Guardar Configuración",
            command=self.save_configuration,
            fg_color="green",
            hover_color="darkgreen",
            height=30
        ).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="Cargar Configuración",
            command=self.load_configuration,
            fg_color="blue",
            hover_color="darkblue",
            height=30
        ).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="Ver Argumentos",
            command=self.preview_arguments,
            fg_color="orange",
            hover_color="darkorange",
            height=30
        ).pack(side="left", padx=5, pady=5)
    
    def load_saved_config(self):
        """Cargar configuración guardada"""
        try:
            # Desactivar temporalmente los comandos de los switches para evitar que se ejecuten durante la carga
            switches_with_commands = []
            
            # Identificar switches con comandos y guardar sus comandos originales
            if hasattr(self, 'maxplayers_switch'):
                original_command = getattr(self.maxplayers_switch, '_command', None)
                if original_command:
                    switches_with_commands.append(('maxplayers_switch', original_command))
                    self.maxplayers_switch.configure(command=None)
            
            try:
                # Cargar valores guardados
                self.session_name_entry.insert(0, self.config_manager.get("server", "session_name", ""))
                self.server_password_entry.insert(0, self.config_manager.get("server", "server_password", ""))
                self.admin_password_entry.insert(0, self.config_manager.get("server", "admin_password", ""))
                self.max_players_entry.insert(0, self.config_manager.get("server", "max_players", "70"))
                self.query_port_entry.insert(0, self.config_manager.get("server", "query_port", "27015"))
                self.port_entry.insert(0, self.config_manager.get("server", "port", "7777"))
                self.multihome_entry.insert(0, self.config_manager.get("server", "multihome", "127.0.0.1"))
                self.message_entry.insert(0, self.config_manager.get("server", "message", ""))
                self.duration_entry.insert(0, self.config_manager.get("server", "duration", "60"))
                
                # Cargar argumentos personalizados
                custom_args = self.config_manager.get("server", "custom_args", "")
                if custom_args:
                    self.custom_args_text.insert("1.0", custom_args)
                
                # Cargar estado del switch de MaxPlayers como argumento
                if hasattr(self, 'maxplayers_as_arg_var'):
                    maxplayers_as_arg = self.config_manager.get("server", "maxplayers_as_arg", False)
                    if isinstance(maxplayers_as_arg, str):
                        maxplayers_as_arg = maxplayers_as_arg.lower() == 'true'
                    self.maxplayers_as_arg_var.set(maxplayers_as_arg)
                
                # Cargar estado de los checkboxes de argumentos opcionales
                if hasattr(self, 'server_arg_var'):
                    server_arg = self.config_manager.get("server", "server_arg", True)
                    if isinstance(server_arg, str):
                        server_arg = server_arg.lower() == 'true'
                    self.server_arg_var.set(server_arg)
                    
                if hasattr(self, 'log_arg_var'):
                    log_arg = self.config_manager.get("server", "log_arg", True)
                    if isinstance(log_arg, str):
                        log_arg = log_arg.lower() == 'true'
                    self.log_arg_var.set(log_arg)
                    
                if hasattr(self, 'nobattleye_var'):
                    nobattleye_arg = self.config_manager.get("server", "nobattleye_arg", False)
                    if isinstance(nobattleye_arg, str):
                        nobattleye_arg = nobattleye_arg.lower() == 'true'
                    self.nobattleye_var.set(nobattleye_arg)
                    
                if hasattr(self, 'servergamelog_var'):
                    servergamelog_arg = self.config_manager.get("server", "servergamelog_arg", False)
                    if isinstance(servergamelog_arg, str):
                        servergamelog_arg = servergamelog_arg.lower() == 'true'
                    self.servergamelog_var.set(servergamelog_arg)
                    
                if hasattr(self, 'servergamelogincludetribelogs_var'):
                    servergamelogincludetribelogs_arg = self.config_manager.get("server", "servergamelogincludetribelogs_arg", False)
                    if isinstance(servergamelogincludetribelogs_arg, str):
                        servergamelogincludetribelogs_arg = servergamelogincludetribelogs_arg.lower() == 'true'
                    self.servergamelogincludetribelogs_var.set(servergamelogincludetribelogs_arg)
                    
            finally:
                # Reactivar los comandos de los switches
                for switch_name, original_command in switches_with_commands:
                    try:
                        switch_obj = getattr(self, switch_name)
                        switch_obj.configure(command=original_command)
                        self.logger.info(f"Comando reactivado para {switch_name}")
                    except Exception as e:
                        self.logger.error(f"Error al reactivar comando de {switch_name}: {e}")
                
        except Exception as e:
            self.logger.error(f"Error al cargar configuración: {e}")
    
    def on_maxplayers_switch_change(self):
        """Callback cuando cambia el estado del switch de MaxPlayers"""
        try:
            # Guardar automáticamente el estado del switch
            maxplayers_as_arg = self.maxplayers_as_arg_var.get()
            self.config_manager.set("server", "maxplayers_as_arg", maxplayers_as_arg)
            self.config_manager.save()
            
            # Guardar automáticamente en configuración específica del servidor
            if self.current_server:
                self.save_server_config(self.current_server)
            
            if self.logger:
                self.logger.info(f"Estado del switch MaxPlayers guardado automáticamente: {maxplayers_as_arg}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al guardar estado del switch MaxPlayers: {e}")
    
    def save_configuration(self):
        """Guardar la configuración actual"""
        try:
            # Guardar parámetros básicos
            self.config_manager.set("server", "session_name", self.session_name_entry.get())
            self.config_manager.set("server", "server_password", self.server_password_entry.get())
            self.config_manager.set("server", "admin_password", self.admin_password_entry.get())
            self.config_manager.set("server", "max_players", self.max_players_entry.get())
            self.config_manager.set("server", "query_port", self.query_port_entry.get())
            self.config_manager.set("server", "port", self.port_entry.get())
            self.config_manager.set("server", "multihome", self.multihome_entry.get())
            self.config_manager.set("server", "message", self.message_entry.get())
            self.config_manager.set("server", "duration", self.duration_entry.get())
            
            # Guardar argumentos personalizados
            custom_args = self.custom_args_text.get("1.0", "end-1c")
            self.config_manager.set("server", "custom_args", custom_args)
            
            # Guardar estado del switch de MaxPlayers como argumento
            if hasattr(self, 'maxplayers_as_arg_var'):
                self.config_manager.set("server", "maxplayers_as_arg", self.maxplayers_as_arg_var.get())
            
            # Guardar estado de los checkboxes de argumentos opcionales
            if hasattr(self, 'server_arg_var'):
                self.config_manager.set("server", "server_arg", self.server_arg_var.get())
            if hasattr(self, 'log_arg_var'):
                self.config_manager.set("server", "log_arg", self.log_arg_var.get())
            if hasattr(self, 'nobattleye_var'):
                self.config_manager.set("server", "nobattleye_arg", self.nobattleye_var.get())
            if hasattr(self, 'servergamelog_var'):
                self.config_manager.set("server", "servergamelog_arg", self.servergamelog_var.get())
            if hasattr(self, 'servergamelogincludetribelogs_var'):
                self.config_manager.set("server", "servergamelogincludetribelogs_arg", self.servergamelogincludetribelogs_var.get())
            
            # Guardar en archivo
            self.config_manager.save()
            
            # Guardar en configuración específica del servidor
            if self.current_server:
                self.save_server_config(self.current_server)
            
            # Guardar en GameUserSettings.ini
            self.save_to_gameusersettings()
            
            # Notificar al panel RCON para actualizar password
            if (hasattr(self.main_window, 'rcon_panel') and 
                self.main_window.rcon_panel is not None and
                hasattr(self.main_window.rcon_panel, 'password_info')):
                self.main_window.rcon_panel.refresh_password_from_config()
            
            # Mostrar mensaje de éxito
            self.show_message("✅ Configuración guardada correctamente", "success")
            
        except Exception as e:
            self.logger.error(f"Error al guardar configuración: {e}")
            self.show_message(f"❌ Error al guardar: {str(e)}", "error")
    
    def save_to_gameusersettings(self):
        """Guardar ServerPassword, AdminPassword y SessionName en GameUserSettings.ini PRESERVANDO CONTENIDO EXISTENTE"""
        try:
            # Obtener servidor actual desde main_window si está disponible
            if not self.main_window or not hasattr(self.main_window, 'selected_server'):
                return
            
            selected_server = self.main_window.selected_server
            if not selected_server:
                return
            
            # Construir ruta al archivo GameUserSettings.ini
            server_path = self.config_manager.get("server", "root_path", "")
            if not server_path:
                return
            
            gameusersettings_path = os.path.join(
                server_path, 
                selected_server, 
                "ShooterGame", 
                "Saved", 
                "Config", 
                "WindowsServer", 
                "GameUserSettings.ini"
            )
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(gameusersettings_path), exist_ok=True)
            
            # Obtener valores a guardar
            server_password = self.server_password_entry.get()
            admin_password = self.admin_password_entry.get()
            session_name = self.session_name_entry.get()
            max_players = self.max_players_entry.get()
            message = self.message_entry.get()
            duration = self.duration_entry.get()
            
            # Verificar si MaxPlayers debe guardarse en INI o usarse como argumento
            save_maxplayers_to_ini = True
            if hasattr(self, 'maxplayers_as_arg_var') and self.maxplayers_as_arg_var.get():
                save_maxplayers_to_ini = False
                self.logger.info("MaxPlayers se usará como argumento -WinLiveMaxPlayers, no se guardará en GameUserSettings.ini")
            
            # Construir secciones a actualizar
            sections_to_update = {
                'ServerSettings': {
                    'ServerPassword': server_password if server_password else None,
                    'ServerAdminPassword': admin_password if admin_password else None
                },
                'SessionSettings': {
                    'SessionName': session_name if session_name else None
                },
                'MessageOfTheDay': {
                    'Message': message if message else None,
                    'Duration': duration if duration else None
                }
            }
            
            # Solo agregar MaxPlayers a la sección si NO se usa como argumento
            if save_maxplayers_to_ini:
                sections_to_update['/Script/Engine.GameSession'] = {
                    'MaxPlayers': max_players if max_players else None
                }
            
            # Agregar opciones de PreventDownload/Upload si el modo cluster está activo
            if self.is_cluster_mode():
                server_settings = sections_to_update.get('ServerSettings', {})
                
                # PreventDownload options
                if hasattr(self, 'prevent_download_survivors_var') and self.prevent_download_survivors_var.get():
                    server_settings['PreventDownloadSurvivors'] = 'true'
                
                if hasattr(self, 'prevent_download_items_var') and self.prevent_download_items_var.get():
                    server_settings['PreventDownloadItems'] = 'true'
                
                if hasattr(self, 'prevent_download_dinos_var') and self.prevent_download_dinos_var.get():
                    server_settings['PreventDownloadDinos'] = 'true'
                
                # PreventUpload options
                if hasattr(self, 'prevent_upload_survivors_var') and self.prevent_upload_survivors_var.get():
                    server_settings['PreventUploadSurvivors'] = 'true'
                
                if hasattr(self, 'prevent_upload_items_var') and self.prevent_upload_items_var.get():
                    server_settings['PreventUploadItems'] = 'true'
                
                if hasattr(self, 'prevent_upload_dinos_var') and self.prevent_upload_dinos_var.get():
                    server_settings['PreventUploadDinos'] = 'true'
                
                # Actualizar la sección ServerSettings
                sections_to_update['ServerSettings'] = server_settings
            
            # Usar método personalizado para preservar el archivo existente
            self._update_ini_file_preserving_content(
                gameusersettings_path,
                sections_to_update
            )
            
            if self.logger:
                self.logger.info(f"✅ Configuración guardada preservando contenido en GameUserSettings.ini: {gameusersettings_path}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al guardar en GameUserSettings.ini: {e}")
            print(f"Error al guardar en GameUserSettings.ini: {e}")
    
    def _update_ini_file_preserving_content(self, file_path, sections_to_update):
        """Actualizar archivo INI preservando capitalización original y contenido existente"""
        if not os.path.exists(file_path):
            # Si el archivo no existe, crearlo con la capitalización proporcionada
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    for section_name, section_data in sections_to_update.items():
                        f.write(f"[{section_name}]\n")
                        for key, value in section_data.items():
                            if value is not None:
                                f.write(f"{key}={value}\n")
                        f.write("\n")
                if self.logger and self.logger.should_log_debug():
                    self.logger.info(f"DEBUG: Nuevo archivo creado: {file_path}")
                return
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error creando archivo {file_path}: {e}")
                return
        
        try:
            # Leer archivo línea por línea preservando la estructura
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            updated_lines = []
            current_section = None
            processed_keys = {}  # Para evitar duplicados
            
            for line in lines:
                original_line = line.rstrip('\n\r')
                
                # Detectar secciones
                if original_line.strip().startswith('[') and original_line.strip().endswith(']'):
                    current_section = original_line.strip()[1:-1]
                    processed_keys[current_section] = set()
                    updated_lines.append(line)
                    continue
                
                # Si estamos en una sección que queremos actualizar
                if current_section and current_section in sections_to_update:
                    section_data = sections_to_update[current_section]
                    
                    # Buscar si esta línea contiene una clave que queremos actualizar
                    if '=' in original_line:
                        existing_key = original_line.split('=', 1)[0].strip()
                        existing_key_lower = existing_key.lower()
                        
                        # Buscar si tenemos una actualización para esta clave
                        update_key = None
                        for update_k, update_v in section_data.items():
                            if update_k.lower() == existing_key_lower:
                                update_key = update_k
                                break
                        
                        if update_key and existing_key_lower not in processed_keys[current_section]:
                            # Actualizar usando la capitalización ORIGINAL del archivo
                            new_value = section_data[update_key]
                            if new_value is not None:
                                updated_lines.append(f"{existing_key}={new_value}\n")
                                if self.logger and self.logger.should_log_debug():
                                    self.logger.info(f"DEBUG: Actualizado preservando capitalización: {existing_key} = {new_value}")
                            # Marcar como procesado
                            processed_keys[current_section].add(existing_key_lower)
                            continue
                        elif existing_key_lower in processed_keys[current_section]:
                            # Esta clave ya fue procesada, eliminar duplicado
                            if self.logger and self.logger.should_log_debug():
                                self.logger.info(f"DEBUG: Eliminando duplicado: {existing_key}")
                            continue
                
                # Línea normal, mantener tal como está
                updated_lines.append(line)
            
            # Agregar claves nuevas que no existían
            for section_name, section_data in sections_to_update.items():
                if section_name not in processed_keys:
                    # Sección nueva
                    updated_lines.append(f"\n[{section_name}]\n")
                    for key, value in section_data.items():
                        if value is not None:
                            updated_lines.append(f"{key}={value}\n")
                            if self.logger and self.logger.should_log_debug():
                                self.logger.info(f"DEBUG: Nueva sección creada: [{section_name}] {key} = {value}")
                else:
                    # Agregar claves que no se encontraron en sección existente
                    section_end = len(updated_lines)
                    section_start = -1
                    
                    # Encontrar dónde está la sección
                    for i, line in enumerate(updated_lines):
                        if line.strip() == f"[{section_name}]":
                            section_start = i
                            # Encontrar el final de esta sección
                            for j in range(i + 1, len(updated_lines)):
                                if updated_lines[j].strip().startswith('['):
                                    section_end = j
                                    break
                            break
                    
                    # Insertar claves nuevas
                    for key, value in section_data.items():
                        key_lower = key.lower()
                        if (key_lower not in processed_keys[section_name] and 
                            value is not None):
                            updated_lines.insert(section_end, f"{key}={value}\n")
                            if self.logger and self.logger.should_log_debug():
                                self.logger.info(f"DEBUG: Nueva clave agregada: {key} = {value}")
                            section_end += 1
            
            # Escribir archivo actualizado
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            
            if self.logger and self.logger.should_log_debug():
                self.logger.info(f"DEBUG: Archivo actualizado preservando capitalización: {file_path}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error actualizando {file_path}: {e}")
    
    def load_from_gameusersettings(self):
        """Cargar ServerPassword, AdminPassword y SessionName desde GameUserSettings.ini"""
        try:
            # Obtener servidor actual desde main_window si está disponible
            if not self.main_window or not hasattr(self.main_window, 'selected_server'):
                return
            
            selected_server = self.main_window.selected_server
            if not selected_server:
                return
            
            # Construir ruta al archivo GameUserSettings.ini
            server_path = self.config_manager.get("server", "root_path", "")
            if not server_path:
                return
            
            gameusersettings_path = os.path.join(
                server_path, 
                selected_server, 
                "ShooterGame", 
                "Saved", 
                "Config", 
                "WindowsServer", 
                "GameUserSettings.ini"
            )
            
            if not os.path.exists(gameusersettings_path):
                return
            
            # Leer archivo
            config = configparser.ConfigParser()
            config.optionxform = str  # Preservar mayúsculas/minúsculas
            try:
                config.read(gameusersettings_path, encoding='utf-8')
            except configparser.DuplicateOptionError as e:
                if self.logger:
                    self.logger.warning(f"Error leyendo GameUserSettings.ini: {e}")
                return
            
            # Cargar valores en los campos
            if config.has_section('ServerSettings'):
                # ServerPassword
                if config.has_option('ServerSettings', 'ServerPassword'):
                    self.server_password_entry.delete(0, "end")
                    self.server_password_entry.insert(0, config.get('ServerSettings', 'ServerPassword'))
                
                # ServerAdminPassword
                if config.has_option('ServerSettings', 'ServerAdminPassword'):
                    self.admin_password_entry.delete(0, "end")
                    self.admin_password_entry.insert(0, config.get('ServerSettings', 'ServerAdminPassword'))
            
            if config.has_section('SessionSettings'):
                # SessionName
                if config.has_option('SessionSettings', 'SessionName'):
                    self.session_name_entry.delete(0, "end")
                    self.session_name_entry.insert(0, config.get('SessionSettings', 'SessionName'))
            
            if config.has_section('/Script/Engine.GameSession'):
                # MaxPlayers
                if config.has_option('/Script/Engine.GameSession', 'MaxPlayers'):
                    self.max_players_entry.delete(0, "end")
                    self.max_players_entry.insert(0, config.get('/Script/Engine.GameSession', 'MaxPlayers'))
            
            if config.has_section('MessageOfTheDay'):
                # Message
                if config.has_option('MessageOfTheDay', 'Message'):
                    self.message_entry.delete(0, "end")
                    self.message_entry.insert(0, config.get('MessageOfTheDay', 'Message'))
                
                # Duration
                if config.has_option('MessageOfTheDay', 'Duration'):
                    self.duration_entry.delete(0, "end")
                    self.duration_entry.insert(0, config.get('MessageOfTheDay', 'Duration'))
            
            # Cargar el estado del switch de maxplayers desde la configuración guardada
            try:
                maxplayers_as_arg = self.config_manager.get("server", "maxplayers_as_arg", False)
                if isinstance(maxplayers_as_arg, str):
                    maxplayers_as_arg = maxplayers_as_arg.lower() == 'true'
                
                if maxplayers_as_arg:
                    self.maxplayers_switch.select()
                else:
                    self.maxplayers_switch.deselect()
                    
                if self.logger:
                    self.logger.info(f"Estado del switch MaxPlayers cargado: {maxplayers_as_arg}")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Error al cargar estado del switch MaxPlayers: {e}")
                self.maxplayers_switch.deselect()  # Valor por defecto
            
            if self.logger:
                self.logger.info(f"Configuración cargada desde GameUserSettings.ini: {gameusersettings_path}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al cargar desde GameUserSettings.ini: {e}")
    
    def load_configuration(self):
        """Cargar configuración desde archivo"""
        try:
            # Limpiar campos
            self.session_name_entry.delete(0, "end")
            self.server_password_entry.delete(0, "end")
            self.admin_password_entry.delete(0, "end")
            self.max_players_entry.delete(0, "end")
            self.query_port_entry.delete(0, "end")
            self.port_entry.delete(0, "end")
            self.multihome_entry.delete(0, "end")
            self.message_entry.delete(0, "end")
            self.duration_entry.delete(0, "end")
            self.custom_args_text.delete("1.0", "end")
            
            # Cargar valores
            self.load_saved_config()
            
            # Cargar también desde GameUserSettings.ini
            self.load_from_gameusersettings()
            
            self.show_message("✅ Configuración cargada correctamente", "success")
            
        except Exception as e:
            self.logger.error(f"Error al cargar configuración: {e}")
            self.show_message(f"❌ Error al cargar: {str(e)}", "error")
    
    def start_server_with_config(self, capture_console=False, server_name=None):
        """Iniciar servidor con la configuración actual"""
        # Si estamos en modo clúster y se especifica un servidor
        if self.is_cluster_mode() and server_name:
            return self.start_cluster_server(server_name, capture_console)
        
        # Obtener servidor y mapa desde main_window
        selected_server = server_name
        selected_map = None
        
        if self.main_window and hasattr(self.main_window, 'selected_server'):
            if not selected_server:
                selected_server = self.main_window.selected_server
            selected_map = self.main_window.selected_map
        
        # Fallback a las variables locales si no están disponibles en main_window
        if not selected_server:
            selected_server = self.selected_server
        if not selected_map:
            selected_map = self.selected_map
        
        # Verificar si hay un servidor seleccionado
        if not selected_server:
            self.show_message("❌ Debe seleccionar un servidor primero", "error")
            return
        
        # Verificar si hay un mapa seleccionado
        if not selected_map:
            self.show_message("❌ Debe seleccionar un mapa primero", "error")
            return
        
        # Guardar configuración antes de iniciar
        self.save_configuration()
        
        # Construir argumentos del servidor
        server_args = self.build_server_arguments(server_name)
        
        # Iniciar servidor con argumentos personalizados
        try:
            self.show_message(f"🚀 Iniciando servidor {selected_server} con mapa {selected_map}", "info")
            
            # Log de depuración
            self.logger.info(f"DEBUG: principal_panel.start_server_with_config - capture_console = {capture_console}")
            
            # Llamar al método de inicio del servidor con argumentos personalizados
            if self.server_manager:
                self.server_manager.start_server_with_args(
                    self.add_status_message, 
                    selected_server, 
                    selected_map, 
                    server_args,
                    capture_console,
                    force_stdin=True
                )
                
                # También notificar al main window si hay uno
                if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'server_panel'):
                    self.main_window.server_panel.update_server_status("Iniciando...", "orange")
            
        except Exception as e:
            self.logger.error(f"Error al iniciar servidor: {e}")
            self.show_message(f"❌ Error al iniciar servidor: {str(e)}", "error")
    
    def stop_server(self, server_name=None):
        """Detener servidor (modo normal o clúster)"""
        # Si estamos en modo clúster y se especifica un servidor
        if self.is_cluster_mode() and server_name:
            return self.stop_cluster_server(server_name)
        
        # Modo servidor único - delegar al server_manager
        try:
            if self.server_manager:
                self.show_message("⏹️ Deteniendo servidor...", "info")
                
                def stop_callback(status, message):
                    if status == "stopped":
                        self.add_status_message(f"✅ {message}", "success")
                        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'server_panel'):
                            self.main_window.server_panel.update_server_status("Detenido", "red")
                    else:
                        self.add_status_message(f"❌ Error: {message}", "error")
                
                self.server_manager.stop_server(stop_callback)
                return True
            else:
                self.show_message("❌ ServerManager no disponible", "error")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al detener servidor: {e}")
            self.show_message(f"❌ Error al detener servidor: {str(e)}", "error")
            return False
    
    def restart_server_with_config(self, capture_console=False, server_name=None):
        """Reiniciar servidor con la configuración actual"""
        # Si estamos en modo clúster y se especifica un servidor
        if self.is_cluster_mode() and server_name:
            return self.restart_cluster_server(server_name, capture_console)
        
        # Obtener servidor y mapa desde main_window
        selected_server = server_name
        selected_map = None
        
        if self.main_window and hasattr(self.main_window, 'selected_server'):
            if not selected_server:
                selected_server = self.main_window.selected_server
            selected_map = self.main_window.selected_map
        
        # Fallback a las variables locales si no están disponibles en main_window
        if not selected_server:
            selected_server = self.selected_server
        if not selected_map:
            selected_map = self.selected_map
        
        # Verificar si hay un servidor seleccionado
        if not selected_server:
            self.show_message("❌ Debe seleccionar un servidor primero", "error")
            return
        
        # Verificar si hay un mapa seleccionado
        if not selected_map:
            self.show_message("❌ Debe seleccionar un mapa primero", "error")
            return
        
        # Guardar configuración antes de reiniciar
        self.save_configuration()
        
        # Construir argumentos del servidor
        server_args = self.build_server_arguments()
        
        # Reiniciar servidor con argumentos personalizados
        try:
            self.show_message(f"🔄 Reiniciando servidor {selected_server} con mapa {selected_map}", "info")
            
            # Llamar al método de reinicio del servidor con argumentos personalizados
            if self.server_manager:
                self.server_manager.restart_server(
                    self.add_status_message, 
                    selected_server, 
                    selected_map, 
                    server_args,
                    capture_console,
                    force_stdin=True
                )
                
                # También notificar al main window si hay uno
                if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'server_panel'):
                    self.main_window.server_panel.update_server_status("Reiniciando...", "orange")
            
        except Exception as e:
            self.logger.error(f"Error al reiniciar servidor: {e}")
            self.show_message(f"❌ Error al reiniciar servidor: {str(e)}", "error")
    
    def build_server_arguments(self, server_name=None):
        """Construir argumentos del servidor basados en la configuración"""
        # 1. Obtener el mapa seleccionado
        selected_map = None
        
        # Si estamos en modo clúster y se especifica un servidor, obtener mapa desde configuración del clúster
        if self.is_cluster_mode() and server_name and server_name in self.server_configs:
            server_config = self.server_configs[server_name]
            selected_map = server_config.get("map")
            if self.logger.should_log_debug():
                self.logger.info(f"DEBUG: Modo clúster - Mapa obtenido desde configuración del servidor {server_name}: '{selected_map}'")
        
        # Fallback a la selección de la ventana principal
        if not selected_map:
            if hasattr(self.main_window, 'selected_map') and self.main_window.selected_map:
                selected_map = self.main_window.selected_map
            elif self.selected_map:
                selected_map = self.selected_map
        
        # Mapear nombres de mapas a sus identificadores técnicos
        # NOTA: Incluimos todas las variantes posibles para máxima compatibilidad
        map_identifiers = {
            # IDENTIFICADORES CORRECTOS PARA ARK SURVIVAL ASCENDED:
            "The Island": "TheIsland_WP",        # ✅ SÍ necesita _WP
            "TheIsland": "TheIsland_WP",
            "TheIsland_WP": "TheIsland_WP",
            "The Center": "TheCenter_WP",        # ✅ SÍ necesita _WP (ASA)
            "TheCenter": "TheCenter_WP",
            "TheCenter_WP": "TheCenter_WP",
            "Scorched Earth": "ScorchedEarth_WP", # ✅ SÍ necesita _WP
            "ScorchedEarth": "ScorchedEarth_WP",
            "ScorchedEarth_WP": "ScorchedEarth_WP",
            "Ragnarok": "Ragnarok_WP",           # ✅ SÍ necesita _WP (ASA)
            "Ragnarok_WP": "Ragnarok_WP",
            "Aberration": "Aberration_P",        # ✅ Usa _P
            "Aberration_P": "Aberration_P",
            "Extinction": "Extinction",          # ✅ NO necesita _WP
            "Valguero": "Valguero_P",           # ✅ Usa _P
            "Valguero_P": "Valguero_P",
            "Genesis: Part 1": "Genesis",        # ✅ NO necesita _WP
            "Genesis1": "Genesis",
            "Genesis": "Genesis",
            "Crystal Isles": "CrystalIsles",     # ✅ NO necesita _WP
            "CrystalIsles": "CrystalIsles",
            "Genesis: Part 2": "Gen2",          # ✅ Abreviado a Gen2
            "Genesis2": "Gen2",
            "Gen2": "Gen2",
            "Lost Island": "LostIsland",         # ✅ NO necesita _WP
            "LostIsland": "LostIsland",
            "Fjordur": "Fjordur",               # ✅ NO necesita _WP
            "Modded Map": "ModdedMap",
            "ModdedMap": "ModdedMap"
        }
        
        # Construir el argumento base del mapa siguiendo el formato correcto
        # Solo mostrar logs de debug en desarrollo
        if self.logger.should_log_debug():
            self.logger.info(f"DEBUG: Mapa seleccionado: '{selected_map}' (tipo: {type(selected_map)}, len: {len(selected_map) if selected_map else 'N/A'})")
            self.logger.info(f"DEBUG: Mapas disponibles: {list(map_identifiers.keys())}")
            self.logger.info(f"DEBUG: ¿Mapa es None?: {selected_map is None}")
            self.logger.info(f"DEBUG: ¿Mapa en diccionario?: {selected_map in map_identifiers if selected_map else 'N/A'}")
            
            # Debug más específico: comparar caractér por caractér
            if selected_map:
                for key in map_identifiers.keys():
                    if key == selected_map:
                        self.logger.info(f"DEBUG: ✅ Coincidencia exacta encontrada con '{key}'")
                    elif key.strip() == selected_map.strip():
                        self.logger.info(f"DEBUG: ⚠️ Coincidencia con espacios: '{key}' vs '{selected_map}'")
                
        if selected_map and selected_map in map_identifiers:
            map_identifier = map_identifiers[selected_map]
            if self.logger.should_log_debug():
                self.logger.info(f"DEBUG: ✅ Mapa encontrado. Usando identificador: {map_identifier}")
        else:
            # Mapa por defecto si no hay selección
            map_identifier = "TheIsland_WP"
            if self.logger.should_log_debug():
                self.logger.info(f"DEBUG: ❌ Mapa no encontrado o vacío. Razón: selected_map='{selected_map}', en diccionario={selected_map in map_identifiers if selected_map else False}. Usando por defecto: TheIsland_WP")
        
        # 2. Obtener mods configurados (buscar por servidor/mapa específico primero)
        # Obtener servidor seleccionado
        selected_server = None
        if hasattr(self.main_window, 'selected_server') and self.main_window.selected_server:
            selected_server = self.main_window.selected_server
        elif self.selected_server:
            selected_server = self.selected_server
            
        server_map_key = f"{selected_server}_{selected_map}" if selected_server and selected_map else "default"
        
        # Obtener mod_ids específicos del servidor/mapa actual
        # Solo usar la configuración específica, sin fallback a configuración general
        mod_ids = self.config_manager.get("server", f"mod_ids_{server_map_key}", "").strip()
        
        # Log para debugging
        if self.logger.should_log_debug():
            self.logger.info(f"DEBUG: Buscando mods para clave: mod_ids_{server_map_key}")
            self.logger.info(f"DEBUG: Mods encontrados: '{mod_ids}'")
        
        # 3. Construir la lista final con argumentos separados
        # El primer argumento debe ser el mapa con todos sus parámetros concatenados
        map_arg = map_identifier + "?listen"
        
        # Obtener configuración específica del servidor si estamos en modo cluster
        server_config = None
        if self.is_cluster_mode() and server_name and server_name in self.server_configs:
            server_config = self.server_configs[server_name]
        
        # Agregar los parámetros de configuración al argumento del mapa
        # Port
        if server_config:
            port = server_config.get("port", "7777")
        else:
            port = self.port_entry.get() or "7777"
        map_arg += f"?Port={port}"
        
        # QueryPort
        if server_config:
            query_port = server_config.get("query_port", "27015")
        else:
            query_port = self.query_port_entry.get() or "27015"
        map_arg += f"?QueryPort={query_port}"
        
        # MultiHome
        if server_config:
            multihome = server_config.get("multihome", "127.0.0.1")
        else:
            multihome = self.multihome_entry.get() or "127.0.0.1"
        map_arg += f"?MultiHome={multihome}"
        
        # Argumentos personalizados - separar los que empiezan con ? de los que empiezan con -
        custom_dash_args = []  # Para argumentos que empiezan con -
        if server_config:
            custom_args = server_config.get("custom_args", "").strip()
        else:
            custom_args = self.custom_args_text.get("1.0", "end-1c").strip()
        if custom_args:
            for line in custom_args.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):  # Ignorar líneas vacías y comentarios
                    # Si la línea comienza con -, la guardamos para agregar al final
                    if line.startswith('-'):
                        custom_dash_args.append(line)
                    # Si la línea ya comienza con ?, la agregamos tal como está al mapa
                    elif line.startswith('?'):
                        map_arg += line
                    else:
                        # Si no tiene prefijo, agregamos el ? al principio para el mapa
                        map_arg += f"?{line}"
        
        # RCON
        if (hasattr(self.main_window, 'rcon_panel') and 
            self.main_window.rcon_panel and 
            hasattr(self.main_window.rcon_panel, 'get_rcon_enabled') and 
            hasattr(self.main_window.rcon_panel, 'get_rcon_port') and 
            self.main_window.rcon_panel.get_rcon_enabled()):
            try:
                rcon_port = self.main_window.rcon_panel.get_rcon_port()
                map_arg += "?RCONEnabled=True"
                map_arg += f"?RCONPort={rcon_port}"
            except Exception as e:
                self.logger.error(f"Error al obtener configuración RCON: {e}")
                # Usar configuración por defecto si hay error
                map_arg += "?RCONEnabled=True"
                map_arg += "?RCONPort=32330"
        
        # Construir la lista final - PRIMERO argumentos con '?' (mapa y parámetros)
        args = [map_arg]
        
        # Preparar argumentos con '-' para agregar al final
        dash_args = []
        
        # Agregar argumentos opcionales basados en los checkboxes
        if server_config:
            # En modo cluster, usar configuración guardada
            if server_config.get("server_arg", True):
                dash_args.append("-server")
            if server_config.get("log_arg", True):
                dash_args.append("-log")
            if server_config.get("nobattleye_arg", False):
                dash_args.append("-NoBattlEye")
            if server_config.get("servergamelog_arg", False):
                dash_args.append("-servergamelog")
            if server_config.get("servergamelogincludetribelogs_arg", False):
                dash_args.append("-servergamelogincludetribelogs")
        else:
            # En modo normal, usar checkboxes de la interfaz
            if hasattr(self, 'server_arg_var') and self.server_arg_var.get():
                dash_args.append("-server")
            if hasattr(self, 'log_arg_var') and self.log_arg_var.get():
                dash_args.append("-log")
            if hasattr(self, 'nobattleye_var') and self.nobattleye_var.get():
                dash_args.append("-NoBattlEye")
            if hasattr(self, 'servergamelog_var') and self.servergamelog_var.get():
                dash_args.append("-servergamelog")
            if hasattr(self, 'servergamelogincludetribelogs_var') and self.servergamelogincludetribelogs_var.get():
                dash_args.append("-servergamelogincludetribelogs")
        
        # 4. Agregar mods si existen (van con '-')
        if mod_ids:
            dash_args.append(f"-mods={mod_ids}")
        
        # 5. Agregar MaxPlayers como argumento si el switch está activado (va con '-')
        maxplayers_as_arg = False
        max_players = "70"
        
        if server_config:
            maxplayers_as_arg = server_config.get("maxplayers_as_arg", False)
            max_players = server_config.get("max_players", "70")
        else:
            if hasattr(self, 'maxplayers_as_arg_var'):
                maxplayers_as_arg = self.maxplayers_as_arg_var.get()
            max_players = self.max_players_entry.get() or "70"
        
        if maxplayers_as_arg:
            dash_args.append(f"-WinLiveMaxPlayers={max_players}")
            if self.logger.should_log_debug():
                self.logger.info(f"DEBUG: MaxPlayers agregado como argumento: -WinLiveMaxPlayers={max_players}")
        
        # 6. Agregar argumentos de cluster si está activo (van con '-')
        if self.is_cluster_mode():
            cluster_config = self.get_cluster_config()
            if cluster_config:
                # Agregar cluster ID
                cluster_id = cluster_config.get("cluster_id", "")
                if cluster_id:
                    dash_args.append(f"-clusterid={cluster_id}")
                    if self.logger.should_log_debug():
                        self.logger.info(f"DEBUG: Cluster ID agregado: -clusterid={cluster_id}")
                
                # Agregar ClusterDirOverride
                cluster_data_path = cluster_config.get("cluster_data_path", "")
                if cluster_data_path:
                    dash_args.append(f"-ClusterDirOverride={cluster_data_path}")
                    if self.logger.should_log_debug():
                        self.logger.info(f"DEBUG: ClusterDirOverride agregado: -ClusterDirOverride={cluster_data_path}")
        
        # Agregar argumentos personalizados que empiezan con '-' al final
        dash_args.extend(custom_dash_args)
        
        # FINALMENTE: Agregar todos los argumentos con '-' al final
        args.extend(dash_args)
        
        if self.logger.should_log_debug():
            self.logger.info(f"DEBUG: Argumentos finales generados: {args}")
        
        return args
    
    def update_server_info(self, server_name, map_name):
        """Actualizar información del servidor seleccionado"""
        # Guardar configuración del servidor anterior si existe
        if self.current_server and self.current_server != server_name:
            self.save_server_config(self.current_server)
        
        # Actualizar servidor actual
        self.current_server = server_name
        self.selected_server = server_name
        self.selected_map = map_name
        
        # Cargar configuración específica del servidor
        if server_name:
            # Primero intentar cargar desde configuración guardada
            self.load_server_config(server_name)
            # Luego cargar desde GameUserSettings.ini (esto puede sobrescribir algunos valores)
            self.load_from_gameusersettings()
    
    def get_public_ip(self):
        """Obtener IP pública automáticamente"""
        def _get_ip():
            try:
                self.ip_auto_button.configure(text="🔄 Obteniendo...", state="disabled")
                
                # Intentar varios servicios para obtener la IP pública
                services = [
                    "https://api.ipify.org",
                    "https://ipecho.net/plain",
                    "https://icanhazip.com",
                    "https://ident.me"
                ]
                
                for service in services:
                    try:
                        response = requests.get(service, timeout=5)
                        if response.status_code == 200:
                            public_ip = response.text.strip()
                            # Validar que sea una IP válida
                            if self.is_valid_ip(public_ip):
                                # Actualizar campo en el hilo principal
                                self.parent.after(0, lambda: self.update_multihome_ip(public_ip))
                                return
                    except:
                        continue
                        
                # Si no se pudo obtener IP
                self.parent.after(0, lambda: self.show_ip_error())
                
            except Exception as e:
                self.logger.error(f"Error al obtener IP pública: {e}")
                self.parent.after(0, lambda: self.show_ip_error())
            finally:
                self.parent.after(0, lambda: self.ip_auto_button.configure(text="🌐 IP Pública", state="normal"))
        
        threading.Thread(target=_get_ip, daemon=True).start()
    
    def is_valid_ip(self, ip):
        """Validar si una cadena es una IP válida"""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False
    
    def update_multihome_ip(self, ip):
        """Actualizar campo MultiHome con la IP obtenida"""
        self.multihome_entry.delete(0, "end")
        self.multihome_entry.insert(0, ip)
        self.show_message(f"✅ IP pública obtenida: {ip}", "success")
    
    def show_ip_error(self):
        """Mostrar error al no poder obtener IP"""
        self.show_message("❌ No se pudo obtener la IP pública. Usando IP local.", "error")
    
    def refresh_rcon_args(self):
        """Refrescar vista previa cuando cambian configuraciones RCON"""
        # Este método puede ser llamado desde el panel RCON
        # Para futuras implementaciones de vista previa en tiempo real
        pass
    
    def preview_arguments(self):
        """Mostrar una vista previa de los argumentos que se generarán"""
        try:
            # Construir argumentos
            server_args = self.build_server_arguments()
            
            # Crear ventana de vista previa
            import customtkinter as ctk
            
            preview_window = ctk.CTkToplevel()
            preview_window.title("Vista Previa de Argumentos del Servidor")
            preview_window.geometry("800x400")
            preview_window.resizable(True, True)
            
            # Centrar la ventana
            preview_window.transient(self.parent)
            preview_window.grab_set()
            
            # Título
            ctk.CTkLabel(
                preview_window, 
                text="Argumentos que se pasarán al servidor:",
                font=("Arial", 14, "bold")
            ).pack(pady=10)
            
            # Área de texto para mostrar los argumentos
            args_text = ctk.CTkTextbox(preview_window, height=300)
            args_text.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Formatear argumentos para mejor visualización
            args_formatted = ""
            for i, arg in enumerate(server_args):
                args_formatted += f"Argumento {i+1}: {arg}\n"
            
            # Comando completo
            args_formatted += f"\n--- COMANDO COMPLETO ---\n"
            args_formatted += f"ArkAscendedServer.exe {' '.join(server_args)}\n"
            
            # Insertar texto
            args_text.insert("1.0", args_formatted)
            args_text.configure(state="disabled")
            
            # Botón cerrar
            ctk.CTkButton(
                preview_window,
                text="Cerrar",
                command=preview_window.destroy,
                height=30
            ).pack(pady=10)
            
        except Exception as e:
            self.logger.error(f"Error al generar vista previa: {e}")
            self.show_message(f"❌ Error al generar vista previa: {str(e)}", "error")
    
    def show_message(self, message, message_type="info"):
        """Mostrar mensaje en el log principal"""
        if self.main_window and hasattr(self.main_window, 'add_log_message'):
            self.main_window.add_log_message(message)
        else:
            # Fallback: mostrar en consola
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")
    
    def add_status_message(self, message, message_type="info"):
        """Agregar mensaje de estado"""
        self.show_message(message, message_type)
    
    # ===== SISTEMA DE CONFIGURACIÓN POR SERVIDOR =====
    
    def load_all_server_configs(self):
        """Cargar todas las configuraciones de servidores"""
        try:
            config_file = "data/principal_server_configs.json"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.server_configs = json.load(f)
            else:
                self.server_configs = {}
                
        except Exception as e:
            self.logger.error(f"Error al cargar configuraciones de servidores: {e}")
            self.server_configs = {}
    
    def save_all_server_configs(self):
        """Guardar todas las configuraciones de servidores"""
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/principal_server_configs.json", 'w', encoding='utf-8') as f:
                json.dump(self.server_configs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error al guardar configuraciones de servidores: {e}")
    
    def on_cluster_toggle(self):
        """Manejar el cambio del switch de cluster"""
        try:
            is_enabled = self.cluster_enabled_var.get()
            
            if is_enabled:
                # Mostrar configuraciones de cluster
                self.cluster_config_frame.pack(fill="x", padx=10, pady=(0, 10))
                self.logger.info("🔗 Modo cluster habilitado")
                
                # Cambiar título principal
                if hasattr(self, 'title_label'):
                    # Buscar y actualizar el título
                    for widget in self.parent.winfo_children():
                        if isinstance(widget, ctk.CTkScrollableFrame):
                            for child in widget.winfo_children():
                                if isinstance(child, ctk.CTkLabel) and "Configuración Principal" in child.cget("text"):
                                    child.configure(text="🌐 Configuración Principal del Cluster")
                                    break
                            break
                
                # Notificar al main_window sobre el cambio de modo
                if self.main_window and hasattr(self.main_window, 'on_cluster_mode_changed'):
                    self.main_window.on_cluster_mode_changed(True)
                    
            else:
                # Ocultar configuraciones de cluster
                self.cluster_config_frame.pack_forget()
                self.logger.info("📱 Modo servidor único habilitado")
                
                # Restaurar título original
                for widget in self.parent.winfo_children():
                    if isinstance(widget, ctk.CTkScrollableFrame):
                        for child in widget.winfo_children():
                            if isinstance(child, ctk.CTkLabel) and "Configuración Principal" in child.cget("text"):
                                child.configure(text="Configuración Principal del Servidor")
                                break
                        break
                
                # Notificar al main_window sobre el cambio de modo
                if self.main_window and hasattr(self.main_window, 'on_cluster_mode_changed'):
                    self.main_window.on_cluster_mode_changed(False)
            
            # Guardar configuración
            self.save_cluster_configuration()
            
        except Exception as e:
            self.logger.error(f"Error al cambiar modo cluster: {e}")
    
    def browse_cluster_data_path(self):
        """Seleccionar carpeta de datos compartidos del cluster"""
        try:
            from tkinter import filedialog
            
            # Obtener ruta actual si existe
            current_path = self.cluster_data_entry.get() or "C:\\"
            
            # Abrir diálogo de selección de carpeta
            selected_path = filedialog.askdirectory(
                title="Seleccionar Carpeta de Datos Compartidos del Cluster",
                initialdir=current_path
            )
            
            if selected_path:
                # Actualizar el campo de entrada
                self.cluster_data_entry.delete(0, "end")
                self.cluster_data_entry.insert(0, selected_path)
                
                # Crear la carpeta si no existe
                os.makedirs(selected_path, exist_ok=True)
                
                self.logger.info(f"📁 Carpeta de datos del cluster configurada: {selected_path}")
                
                # Guardar configuración
                self.save_cluster_configuration()
                
        except Exception as e:
            self.logger.error(f"Error al seleccionar carpeta de cluster: {e}")
            messagebox.showerror("Error", f"Error al seleccionar carpeta: {e}")
    
    def save_cluster_configuration(self):
        """Guardar configuración del cluster"""
        try:
            cluster_config = {
                "enabled": self.cluster_enabled_var.get(),
                "cluster_id": self.cluster_id_entry.get(),
                "cluster_data_path": self.cluster_data_entry.get(),
                "allow_character_transfer": self.allow_character_transfer_var.get(),
                "allow_item_transfer": self.allow_item_transfer_var.get(),
                "allow_dino_transfer": self.allow_dino_transfer_var.get(),
                "prevent_download_survivors": getattr(self, 'prevent_download_survivors_var', ctk.BooleanVar(value=False)).get(),
                "prevent_download_items": getattr(self, 'prevent_download_items_var', ctk.BooleanVar(value=False)).get(),
                "prevent_download_dinos": getattr(self, 'prevent_download_dinos_var', ctk.BooleanVar(value=False)).get(),
                "prevent_upload_survivors": getattr(self, 'prevent_upload_survivors_var', ctk.BooleanVar(value=False)).get(),
                "prevent_upload_items": getattr(self, 'prevent_upload_items_var', ctk.BooleanVar(value=False)).get(),
                "prevent_upload_dinos": getattr(self, 'prevent_upload_dinos_var', ctk.BooleanVar(value=False)).get()
            }
            
            # Guardar en config_manager
            self.config_manager.set("cluster", "enabled", cluster_config["enabled"])
            self.config_manager.set("cluster", "cluster_id", cluster_config["cluster_id"])
            self.config_manager.set("cluster", "cluster_data_path", cluster_config["cluster_data_path"])
            self.config_manager.set("cluster", "allow_character_transfer", cluster_config["allow_character_transfer"])
            self.config_manager.set("cluster", "allow_item_transfer", cluster_config["allow_item_transfer"])
            self.config_manager.set("cluster", "allow_dino_transfer", cluster_config["allow_dino_transfer"])
            
            # Guardar opciones de prevención
            self.config_manager.set("cluster", "prevent_download_survivors", cluster_config["prevent_download_survivors"])
            self.config_manager.set("cluster", "prevent_download_items", cluster_config["prevent_download_items"])
            self.config_manager.set("cluster", "prevent_download_dinos", cluster_config["prevent_download_dinos"])
            self.config_manager.set("cluster", "prevent_upload_survivors", cluster_config["prevent_upload_survivors"])
            self.config_manager.set("cluster", "prevent_upload_items", cluster_config["prevent_upload_items"])
            self.config_manager.set("cluster", "prevent_upload_dinos", cluster_config["prevent_upload_dinos"])
            
            # También guardar en archivo JSON separado
            os.makedirs("data", exist_ok=True)
            with open("data/cluster_config.json", 'w', encoding='utf-8') as f:
                json.dump(cluster_config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error al guardar configuración del cluster: {e}")
    
    def load_cluster_configuration(self):
        """Cargar configuración del cluster"""
        try:
            # Desactivar temporalmente los comandos de los switches para evitar guardado automático
            original_cluster_command = self.cluster_switch.cget("command")
            self.cluster_switch.configure(command=None)
            
            # Desactivar comandos de switches de transferencia
            original_char_command = self.character_transfer_switch.cget("command")
            original_item_command = self.item_transfer_switch.cget("command")
            original_dino_command = self.dino_transfer_switch.cget("command")
            
            self.character_transfer_switch.configure(command=None)
            self.item_transfer_switch.configure(command=None)
            self.dino_transfer_switch.configure(command=None)
            
            # Cargar desde cluster_config.json
            cluster_config_file = self.config_manager.get_data_file_path("cluster_config.json")
            cluster_config = {}
            
            if os.path.exists(cluster_config_file):
                try:
                    with open(cluster_config_file, 'r', encoding='utf-8') as f:
                        cluster_config = json.load(f)
                except Exception as e:
                    self.logger.error(f"Error leyendo cluster_config.json: {e}")
            
            # Obtener valores de configuración
            cluster_enabled = cluster_config.get("enabled", False)
            if isinstance(cluster_enabled, str):
                cluster_enabled = cluster_enabled.lower() == 'true'
            
            cluster_id = cluster_config.get("cluster_id", "MiClusterARK")
            # Establecer carpeta por defecto 'Cluster' en la raíz si no hay configuración previa
            default_cluster_path = os.path.join(os.getcwd(), "Cluster")
            cluster_data_path = cluster_config.get("cluster_data_path", default_cluster_path)
            allow_character_transfer = cluster_config.get("allow_character_transfer", True)
            allow_item_transfer = cluster_config.get("allow_item_transfer", True)
            allow_dino_transfer = cluster_config.get("allow_dino_transfer", True)
            
            # Cargar opciones de PreventDownload/Upload
            prevent_download_survivors = cluster_config.get("prevent_download_survivors", False)
            prevent_download_items = cluster_config.get("prevent_download_items", False)
            prevent_download_dinos = cluster_config.get("prevent_download_dinos", False)
            prevent_upload_survivors = cluster_config.get("prevent_upload_survivors", False)
            prevent_upload_items = cluster_config.get("prevent_upload_items", False)
            prevent_upload_dinos = cluster_config.get("prevent_upload_dinos", False)
            
            # Aplicar configuración a los widgets
            self.cluster_enabled_var.set(cluster_enabled)
            self.cluster_id_entry.delete(0, "end")
            self.cluster_id_entry.insert(0, cluster_id)
            self.cluster_data_entry.delete(0, "end")
            self.cluster_data_entry.insert(0, cluster_data_path)
            
            if isinstance(allow_character_transfer, str):
                allow_character_transfer = allow_character_transfer.lower() == 'true'
            if isinstance(allow_item_transfer, str):
                allow_item_transfer = allow_item_transfer.lower() == 'true'
            if isinstance(allow_dino_transfer, str):
                allow_dino_transfer = allow_dino_transfer.lower() == 'true'
                
            self.allow_character_transfer_var.set(allow_character_transfer)
            self.allow_item_transfer_var.set(allow_item_transfer)
            self.allow_dino_transfer_var.set(allow_dino_transfer)
            
            # Aplicar configuración de PreventDownload/Upload
            if isinstance(prevent_download_survivors, str):
                prevent_download_survivors = prevent_download_survivors.lower() == 'true'
            if isinstance(prevent_download_items, str):
                prevent_download_items = prevent_download_items.lower() == 'true'
            if isinstance(prevent_download_dinos, str):
                prevent_download_dinos = prevent_download_dinos.lower() == 'true'
            if isinstance(prevent_upload_survivors, str):
                prevent_upload_survivors = prevent_upload_survivors.lower() == 'true'
            if isinstance(prevent_upload_items, str):
                prevent_upload_items = prevent_upload_items.lower() == 'true'
            if isinstance(prevent_upload_dinos, str):
                prevent_upload_dinos = prevent_upload_dinos.lower() == 'true'
                
            if hasattr(self, 'prevent_download_survivors_var'):
                self.prevent_download_survivors_var.set(prevent_download_survivors)
            if hasattr(self, 'prevent_download_items_var'):
                self.prevent_download_items_var.set(prevent_download_items)
            if hasattr(self, 'prevent_download_dinos_var'):
                self.prevent_download_dinos_var.set(prevent_download_dinos)
            if hasattr(self, 'prevent_upload_survivors_var'):
                self.prevent_upload_survivors_var.set(prevent_upload_survivors)
            if hasattr(self, 'prevent_upload_items_var'):
                self.prevent_upload_items_var.set(prevent_upload_items)
            if hasattr(self, 'prevent_upload_dinos_var'):
                self.prevent_upload_dinos_var.set(prevent_upload_dinos)
            
            # Aplicar el estado del cluster
            if cluster_enabled:
                self.cluster_config_frame.pack(fill="x", padx=10, pady=(0, 10))
            else:
                self.cluster_config_frame.pack_forget()
            
            # Reactivar todos los comandos de los switches
            self.cluster_switch.configure(command=original_cluster_command)
            self.character_transfer_switch.configure(command=original_char_command)
            self.item_transfer_switch.configure(command=original_item_command)
            self.dino_transfer_switch.configure(command=original_dino_command)
            
            # Programar notificación al main_window sobre el estado inicial del cluster
            # Se hace con delay para asegurar que todos los paneles estén inicializados
            if self.main_window and hasattr(self.main_window, 'on_cluster_mode_changed'):
                self.main_window.root.after(500, lambda: self.main_window.on_cluster_mode_changed(cluster_enabled))
            
            self.logger.info(f"Configuración del cluster cargada: enabled={cluster_enabled}")
                
        except Exception as e:
            self.logger.error(f"Error al cargar configuración del cluster: {e}")
            # Reactivar los comandos de los switches en caso de error
            try:
                self.cluster_switch.configure(command=self.on_cluster_toggle)
                self.character_transfer_switch.configure(command=self.save_cluster_configuration)
                self.item_transfer_switch.configure(command=self.save_cluster_configuration)
                self.dino_transfer_switch.configure(command=self.save_cluster_configuration)
            except:
                pass
    
    def is_cluster_mode(self):
        """Verificar si está en modo cluster"""
        return self.cluster_enabled_var.get() if hasattr(self, 'cluster_enabled_var') else False
    
    def get_cluster_config(self):
        """Obtener configuración actual del cluster"""
        if not self.is_cluster_mode():
            return None
            
        return {
            "cluster_id": self.cluster_id_entry.get(),
            "cluster_data_path": self.cluster_data_entry.get(),
            "allow_character_transfer": self.allow_character_transfer_var.get(),
            "allow_item_transfer": self.allow_item_transfer_var.get(),
            "allow_dino_transfer": self.allow_dino_transfer_var.get(),
            "prevent_download_survivors": getattr(self, 'prevent_download_survivors_var', ctk.BooleanVar(value=False)).get(),
            "prevent_download_items": getattr(self, 'prevent_download_items_var', ctk.BooleanVar(value=False)).get(),
            "prevent_download_dinos": getattr(self, 'prevent_download_dinos_var', ctk.BooleanVar(value=False)).get(),
            "prevent_upload_survivors": getattr(self, 'prevent_upload_survivors_var', ctk.BooleanVar(value=False)).get(),
            "prevent_upload_items": getattr(self, 'prevent_upload_items_var', ctk.BooleanVar(value=False)).get(),
            "prevent_upload_dinos": getattr(self, 'prevent_upload_dinos_var', ctk.BooleanVar(value=False)).get()
        }
    
    def save_server_config(self, server_name=None):
        """Guardar configuración específica del servidor"""
        if not server_name:
            server_name = self.current_server
        
        if not server_name:
            return
        
        try:
            config = {
                "session_name": getattr(self, 'session_name_entry', None) and self.session_name_entry.get() or "",
                "server_password": getattr(self, 'server_password_entry', None) and self.server_password_entry.get() or "",
                "admin_password": getattr(self, 'admin_password_entry', None) and self.admin_password_entry.get() or "",
                "max_players": getattr(self, 'max_players_entry', None) and self.max_players_entry.get() or "70",
                "query_port": getattr(self, 'query_port_entry', None) and self.query_port_entry.get() or "27015",
                "port": getattr(self, 'port_entry', None) and self.port_entry.get() or "7777",
                "multihome": getattr(self, 'multihome_entry', None) and self.multihome_entry.get() or "",
                "message": getattr(self, 'message_entry', None) and self.message_entry.get() or "",
                "duration": getattr(self, 'duration_entry', None) and self.duration_entry.get() or "1440",
                "custom_args": getattr(self, 'custom_args_text', None) and self.custom_args_text.get("1.0", "end-1c") or "",
                "maxplayers_as_arg": getattr(self, 'maxplayers_as_arg_var', None) and self.maxplayers_as_arg_var.get() or False,
                "server_arg": getattr(self, 'server_arg_var', None) and self.server_arg_var.get() or True,
                "log_arg": getattr(self, 'log_arg_var', None) and self.log_arg_var.get() or True,
                "nobattleye_arg": getattr(self, 'nobattleye_var', None) and self.nobattleye_var.get() or False,
                "servergamelog_arg": getattr(self, 'servergamelog_var', None) and self.servergamelog_var.get() or False,
                "servergamelogincludetribelogs_arg": getattr(self, 'servergamelogincludetribelogs_var', None) and self.servergamelogincludetribelogs_var.get() or False
            }
            
            self.server_configs[server_name] = config
            self.save_all_server_configs()
            
            self.logger.info(f"Configuración guardada para servidor: {server_name}")
            
        except Exception as e:
            self.logger.error(f"Error al guardar configuración del servidor {server_name}: {e}")
    
    def load_server_config(self, server_name):
        """Cargar configuración específica del servidor"""
        if not server_name or server_name not in self.server_configs:
            return
        
        try:
            config = self.server_configs[server_name]
            
            # Cargar valores en los campos
            if hasattr(self, 'session_name_entry'):
                self.session_name_entry.delete(0, 'end')
                self.session_name_entry.insert(0, config.get("session_name", ""))
            
            if hasattr(self, 'server_password_entry'):
                self.server_password_entry.delete(0, 'end')
                self.server_password_entry.insert(0, config.get("server_password", ""))
            
            if hasattr(self, 'admin_password_entry'):
                self.admin_password_entry.delete(0, 'end')
                self.admin_password_entry.insert(0, config.get("admin_password", ""))
            
            if hasattr(self, 'max_players_entry'):
                self.max_players_entry.delete(0, 'end')
                self.max_players_entry.insert(0, config.get("max_players", "70"))
            
            if hasattr(self, 'query_port_entry'):
                self.query_port_entry.delete(0, 'end')
                self.query_port_entry.insert(0, config.get("query_port", "27015"))
            
            if hasattr(self, 'port_entry'):
                self.port_entry.delete(0, 'end')
                self.port_entry.insert(0, config.get("port", "7777"))
            
            if hasattr(self, 'multihome_entry'):
                self.multihome_entry.delete(0, 'end')
                self.multihome_entry.insert(0, config.get("multihome", ""))
            
            if hasattr(self, 'message_entry'):
                self.message_entry.delete(0, 'end')
                self.message_entry.insert(0, config.get("message", ""))
            
            if hasattr(self, 'duration_entry'):
                self.duration_entry.delete(0, 'end')
                self.duration_entry.insert(0, config.get("duration", "1440"))
            
            if hasattr(self, 'custom_args_text'):
                self.custom_args_text.delete("1.0", 'end')
                self.custom_args_text.insert("1.0", config.get("custom_args", ""))
            
            # Cargar estado del switch MaxPlayers
            if hasattr(self, 'maxplayers_as_arg_var'):
                maxplayers_value = config.get("maxplayers_as_arg", False)
                if isinstance(maxplayers_value, str):
                    maxplayers_value = maxplayers_value.lower() == 'true'
                self.maxplayers_as_arg_var.set(maxplayers_value)
            
            # Cargar estado de los checkboxes de argumentos opcionales
            if hasattr(self, 'server_arg_var'):
                server_arg_value = config.get("server_arg", True)
                if isinstance(server_arg_value, str):
                    server_arg_value = server_arg_value.lower() == 'true'
                self.server_arg_var.set(server_arg_value)
                
            if hasattr(self, 'log_arg_var'):
                log_arg_value = config.get("log_arg", True)
                if isinstance(log_arg_value, str):
                    log_arg_value = log_arg_value.lower() == 'true'
                self.log_arg_var.set(log_arg_value)
                
            if hasattr(self, 'nobattleye_var'):
                nobattleye_value = config.get("nobattleye_arg", False)
                if isinstance(nobattleye_value, str):
                    nobattleye_value = nobattleye_value.lower() == 'true'
                self.nobattleye_var.set(nobattleye_value)
                
            if hasattr(self, 'servergamelog_var'):
                servergamelog_value = config.get("servergamelog_arg", False)
                if isinstance(servergamelog_value, str):
                    servergamelog_value = servergamelog_value.lower() == 'true'
                self.servergamelog_var.set(servergamelog_value)
                
            if hasattr(self, 'servergamelogincludetribelogs_var'):
                servergamelogincludetribelogs_value = config.get("servergamelogincludetribelogs_arg", False)
                if isinstance(servergamelogincludetribelogs_value, str):
                    servergamelogincludetribelogs_value = servergamelogincludetribelogs_value.lower() == 'true'
                self.servergamelogincludetribelogs_var.set(servergamelogincludetribelogs_value)
            
            self.logger.info(f"Configuración cargada para servidor: {server_name}")
            
        except Exception as e:
            self.logger.error(f"Error al cargar configuración del servidor {server_name}: {e}")
    
    def start_cluster_server(self, server_name, capture_console=False):
        """Iniciar un servidor específico del clúster"""
        try:
            if not hasattr(self, 'cluster_manager'):
                self._initialize_cluster_manager()
            
            if not self.cluster_manager:
                self.show_message("❌ ClusterManager no disponible", "error")
                return False
            
            server_instance = self.cluster_manager.get_server(server_name)
            if not server_instance:
                self.show_message(f"❌ Servidor {server_name} no encontrado en el clúster", "error")
                return False
            
            self.show_message(f"🚀 Iniciando servidor del clúster: {server_name}", "info")
            
            # Construir argumentos del servidor
            server_args = self.build_server_arguments(server_name)
            
            # Obtener configuración del servidor
            server_config = self.server_configs.get(server_name, {})
            selected_map = server_config.get("map", "TheIsland_WP")
            
            def callback(level, message):
                self.add_status_message(message, level)
            
            # Usar el ServerManager del servidor para iniciar con argumentos específicos
            if server_instance.server_manager:
                success = server_instance.server_manager.start_server_with_args(
                    callback, server_name, selected_map, server_args, capture_console
                )
                if success:
                    server_instance.status = "running"
                    from datetime import datetime
                    server_instance.uptime_start = datetime.now()
                    server_instance.start_monitoring()
                    
                    # Forzar actualización del estado después de un breve delay
                    def force_status_update():
                        try:
                            time.sleep(3)  # Esperar 3 segundos para que el proceso se estabilice
                            server_instance.update_status()
                            self.logger.info(f"Estado forzado actualizado para {server_name}: {server_instance.status}")
                        except Exception as e:
                            self.logger.error(f"Error en actualización forzada de estado: {e}")
                    
                    import threading
                    threading.Thread(target=force_status_update, daemon=True).start()
            else:
                success = server_instance.start(callback)
            if success:
                self.show_message(f"✅ Servidor {server_name} iniciado correctamente", "success")
            else:
                self.show_message(f"❌ Error al iniciar servidor {server_name}", "error")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error al iniciar servidor del clúster {server_name}: {e}")
            self.show_message(f"❌ Error al iniciar servidor {server_name}: {str(e)}", "error")
            return False
    
    def stop_cluster_server(self, server_name):
        """Detener un servidor específico del clúster"""
        try:
            if not hasattr(self, 'cluster_manager') or not self.cluster_manager:
                self.show_message("❌ ClusterManager no disponible", "error")
                return False
            
            server_instance = self.cluster_manager.get_server(server_name)
            if not server_instance:
                self.show_message(f"❌ Servidor {server_name} no encontrado en el clúster", "error")
                return False
            
            self.show_message(f"⏹️ Deteniendo servidor del clúster: {server_name}", "info")
            
            def callback(level, message):
                self.add_status_message(message, level)
            
            success = server_instance.stop(callback)
            if success:
                self.show_message(f"✅ Servidor {server_name} detenido correctamente", "success")
            else:
                self.show_message(f"❌ Error al detener servidor {server_name}", "error")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error al detener servidor del clúster {server_name}: {e}")
            self.show_message(f"❌ Error al detener servidor {server_name}: {str(e)}", "error")
            return False
    
    def restart_cluster_server(self, server_name, capture_console=False):
        """Reiniciar un servidor específico del clúster"""
        try:
            if not hasattr(self, 'cluster_manager') or not self.cluster_manager:
                self.show_message("❌ ClusterManager no disponible", "error")
                return False
            
            server_instance = self.cluster_manager.get_server(server_name)
            if not server_instance:
                self.show_message(f"❌ Servidor {server_name} no encontrado en el clúster", "error")
                return False
            
            self.show_message(f"🔄 Reiniciando servidor del clúster: {server_name}", "info")
            
            def callback(level, message):
                self.add_status_message(message, level)
            
            success = server_instance.restart(callback)
            if success:
                self.show_message(f"✅ Servidor {server_name} reiniciado correctamente", "success")
            else:
                self.show_message(f"❌ Error al reiniciar servidor {server_name}", "error")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error al reiniciar servidor del clúster {server_name}: {e}")
            self.show_message(f"❌ Error al reiniciar servidor {server_name}: {str(e)}", "error")
            return False
    
    def _initialize_cluster_manager(self):
        """Inicializar ClusterManager si no existe"""
        try:
            if not hasattr(self, 'cluster_manager'):
                from utils.cluster_manager import ClusterManager
                self.cluster_manager = ClusterManager(self.config_manager, self.logger)
                self.logger.info("ClusterManager inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando ClusterManager: {e}")
            self.cluster_manager = None
    
    def get_cluster_manager(self):
         """Obtener instancia del ClusterManager"""
         if not hasattr(self, 'cluster_manager'):
             self._initialize_cluster_manager()
         return getattr(self, 'cluster_manager', None)
