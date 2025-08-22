import customtkinter as ctk
import os
import shutil
import threading
import time
import json
import zipfile
import schedule
from datetime import datetime, timedelta
from tkinter import filedialog
# Importación de messagebox removida - usando solo CustomTkinter dialogs
from pathlib import Path

class AdvancedBackupPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger, main_window):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        
        # Variables de estado
        self.backup_running = False
        self.auto_backup_enabled = False
        self.backup_thread = None
        self.scheduler_thread = None
        self.current_server = None
        self.server_configs = {}  # Configuraciones por servidor
        
        # Configuración por defecto
        self.default_backup_config = {
            "backup_path": self.get_default_backup_path(),
            "auto_backup": False,
            "interval_type": "hours",  # minutes, hours, days
            "interval_value": 6,
            "compress": True,
            "max_backups": 10,
            "include_logs": True,
            "include_configs": True,
            "include_saves": True,
            "backup_name_format": "{server}_{date}_{time}",
            "saveworld_before_backup": True
        }
        
        # Lista de backups realizados
        self.backup_history = []
        
        # Para trackear cambios en la ruta de backup
        self._last_backup_path = ""
        
        self.create_widgets()
        self.pack(fill="both", expand=True)
        self.load_all_server_configs()
        self.load_backup_history()
        
        # Inicializar tracking de ruta después de crear widgets
        if hasattr(self, 'backup_path_entry'):
            self._last_backup_path = self.backup_path_entry.get().strip()
            
            # Escaneo inicial de la ruta actual para detectar backups existentes
            if self._last_backup_path:
                self.after(1000, lambda: self._on_backup_path_changed(self._last_backup_path))
        
        # Iniciar scheduler si está habilitado (con retraso para asegurar que la UI esté lista)
        self._safe_schedule_ui_update(lambda: self.after(3000, self.check_auto_backup))  # 3 segundos de retraso
    
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
    
    def get_default_backup_path(self):
        """Obtener ruta de backup por defecto"""
        try:
            # Opción 1: Usar ruta raíz del servidor + Backup
            root_path = self.config_manager.get("server", "root_path", "")
            if root_path and os.path.exists(root_path):
                # Normalizar la ruta para evitar mezcla de barras
                backup_path = os.path.normpath(os.path.join(root_path, "Backup"))
            else:
                # Opción 2: Usar directorio del proyecto + Backup
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                backup_path = os.path.normpath(os.path.join(project_root, "Backup"))
            
            # Crear el directorio si no existe
            os.makedirs(backup_path, exist_ok=True)
            self.logger.info(f"Ruta de backup configurada: {backup_path}")
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error al crear ruta de backup por defecto: {e}")
            # Fallback: usar directorio actual + Backup
            backup_path = os.path.normpath(os.path.join(os.getcwd(), "Backup"))
            try:
                os.makedirs(backup_path, exist_ok=True)
            except:
                pass
            return backup_path
    
    def show_ctk_info(self, title, message):
        """Mostrar diálogo de información con CustomTkinter"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrar ventana
        dialog.update_idletasks()
        x = self.winfo_rootx() + 50
        y = self.winfo_rooty() + 50
        dialog.geometry(f"+{x}+{y}")
        
        # Contenido
        label = ctk.CTkLabel(dialog, text=message, wraplength=350, justify="left")
        label.pack(pady=20, padx=20)
        
        button = ctk.CTkButton(dialog, text="OK", command=dialog.destroy, width=100)
        button.pack(pady=10)
        
        dialog.focus_set()
    
    def show_ctk_error(self, title, message):
        """Mostrar diálogo de error con CustomTkinter"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrar ventana
        dialog.update_idletasks()
        x = self.winfo_rootx() + 50
        y = self.winfo_rooty() + 50
        dialog.geometry(f"+{x}+{y}")
        
        # Contenido con color de error
        label = ctk.CTkLabel(dialog, text=f"❌ {message}", wraplength=350, justify="left", text_color="red")
        label.pack(pady=20, padx=20)
        
        button = ctk.CTkButton(dialog, text="OK", command=dialog.destroy, width=100)
        button.pack(pady=10)
        
        dialog.focus_set()
    
    def show_ctk_confirm(self, title, message, callback=None):
        """Mostrar diálogo de confirmación con CustomTkinter"""
        result = {"confirmed": False}
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("450x250")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrar ventana
        dialog.update_idletasks()
        x = self.winfo_rootx() + 50
        y = self.winfo_rooty() + 50
        dialog.geometry(f"+{x}+{y}")
        
        # Contenido
        label = ctk.CTkLabel(dialog, text=message, wraplength=350, justify="left")
        label.pack(pady=20, padx=20)
        
        # Botones
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=10)
        
        def on_yes():
            result["confirmed"] = True
            dialog.destroy()
            if callback:
                callback(True)
        
        def on_no():
            result["confirmed"] = False
            dialog.destroy()
            if callback:
                callback(False)
        
        yes_button = ctk.CTkButton(button_frame, text="Sí", command=on_yes, width=80)
        yes_button.pack(side="left", padx=5)
        
        no_button = ctk.CTkButton(button_frame, text="No", command=on_no, width=80)
        no_button.pack(side="left", padx=5)
        
        dialog.focus_set()
        return result
    
    def create_widgets(self):
        """Crear interfaz principal del panel de backup"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        
        # 1. Título y estado
        self.create_header()
        
        # 2. Configuración de backup
        self.create_backup_config_section()
        
        # 3. Controles de backup
        self.create_backup_controls()
        
        # 4. Historial de backups

    
    def create_header(self):
        """Crear sección de título y estado"""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Título
        title_label = ctk.CTkLabel(
            header_frame,
            text="🛡️ Sistema de Backup Avanzado",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=5)
        
        # Frame para estado y próximo backup en una línea
        status_container = ctk.CTkFrame(header_frame)
        status_container.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        
        # Estado del sistema con punto de color
        self.status_label = ctk.CTkLabel(
            status_container,
            text="🔴 ⏹️ Inactivo",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=(8, 15))
        
        # Próximo backup en la misma línea
        self.next_backup_info = ctk.CTkLabel(
            status_container,
            text="Próximo backup: Deshabilitado",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.next_backup_info.pack(side="left", padx=(0, 8))
    
    def create_backup_config_section(self):
        """Crear sección de configuración"""
        config_frame = ctk.CTkFrame(self)
        config_frame.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")
        config_frame.grid_columnconfigure(1, weight=1)
        
        # Título de configuración
        config_title = ctk.CTkLabel(
            config_frame,
            text="⚙️ Configuración de Backup",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        config_title.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Crear pestañas para organizar configuración
        self.config_tabview = ctk.CTkTabview(config_frame)
        self.config_tabview.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        # Pestaña General
        self.create_general_config_tab()
        
        # Pestaña Programación
        self.create_schedule_config_tab()
        
        # Pestaña Avanzado
        self.create_advanced_config_tab()
        
        # Pestaña Historial
        self.create_history_tab()
    
    def create_general_config_tab(self):
        """Crear pestaña de configuración general"""
        general_tab = self.config_tabview.add("General")
        general_tab.grid_columnconfigure(1, weight=1)
        
        # Ruta de backup
        path_label = ctk.CTkLabel(general_tab, text="📁 Ruta de Backup:")
        path_label.grid(row=0, column=0, padx=8, pady=3, sticky="w")
        
        self.backup_path_entry = ctk.CTkEntry(general_tab, placeholder_text="Por defecto: [Ruta Raíz]/Backup")
        self.backup_path_entry.grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        self.backup_path_entry.bind("<KeyRelease>", self.on_config_change)
        
        path_button = ctk.CTkButton(
            general_tab,
            text="🔍",
            command=self.select_backup_path,
            width=40
        )
        path_button.grid(row=0, column=2, padx=3, pady=3)
        
        default_path_button = ctk.CTkButton(
            general_tab,
            text="🏠",
            command=self.set_default_backup_path,
            width=40
        )
        default_path_button.grid(row=0, column=3, padx=3, pady=3)
        
        # Servidor objetivo
        server_label = ctk.CTkLabel(general_tab, text="🖥️ Servidor:")
        server_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.server_info_label = ctk.CTkLabel(
            general_tab,
            text="Selecciona un servidor en el panel principal",
            text_color="gray"
        )
        self.server_info_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Qué incluir en el backup
        include_label = ctk.CTkLabel(general_tab, text="📦 Incluir en Backup:")
        include_label.grid(row=2, column=0, padx=10, pady=(15, 5), sticky="nw")
        
        include_frame = ctk.CTkFrame(general_tab)
        include_frame.grid(row=2, column=1, columnspan=2, padx=5, pady=(15, 5), sticky="ew")
        
        self.include_saves_var = ctk.BooleanVar(value=True)
        self.include_saves_check = ctk.CTkCheckBox(
            include_frame,
            text="💾 Archivos de guardado (.ark)",
            variable=self.include_saves_var,
            command=self.on_config_change
        )
        self.include_saves_check.pack(anchor="w", padx=10, pady=2)
        
        self.include_configs_var = ctk.BooleanVar(value=True)
        self.include_configs_check = ctk.CTkCheckBox(
            include_frame,
            text="⚙️ Archivos de configuración (.ini)",
            variable=self.include_configs_var,
            command=self.on_config_change
        )
        self.include_configs_check.pack(anchor="w", padx=10, pady=2)
        
        self.include_logs_var = ctk.BooleanVar(value=False)
        self.include_logs_check = ctk.CTkCheckBox(
            include_frame,
            text="📄 Archivos de log",
            variable=self.include_logs_var,
            command=self.on_config_change
        )
        self.include_logs_check.pack(anchor="w", padx=10, pady=2)
        
        # Compresión
        self.compress_var = ctk.BooleanVar(value=True)
        self.compress_check = ctk.CTkCheckBox(
            general_tab,
            text="🗜️ Comprimir backup (ZIP)",
            variable=self.compress_var,
            command=self.on_config_change
        )
        self.compress_check.grid(row=3, column=1, padx=5, pady=10, sticky="w")
    
    def create_schedule_config_tab(self):
        """Crear pestaña de programación automática"""
        schedule_tab = self.config_tabview.add("Programación")
        schedule_tab.grid_columnconfigure(1, weight=1)
        
        # Auto backup habilitado
        self.auto_backup_var = ctk.BooleanVar()
        self.auto_backup_check = ctk.CTkCheckBox(
            schedule_tab,
            text="🔄 Habilitar backup automático",
            variable=self.auto_backup_var,
            command=self.toggle_auto_backup_and_save
        )
        self.auto_backup_check.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="w")
        
        # Frecuencia
        freq_label = ctk.CTkLabel(schedule_tab, text="⏰ Frecuencia:")
        freq_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        freq_frame = ctk.CTkFrame(schedule_tab)
        freq_frame.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        
        self.interval_value_entry = ctk.CTkEntry(freq_frame, width=80, placeholder_text="6")
        self.interval_value_entry.pack(side="left", padx=5, pady=5)
        self.interval_value_entry.bind("<KeyRelease>", self.on_interval_change)
        
        self.interval_type_combo = ctk.CTkComboBox(
            freq_frame,
            values=["minutos", "horas", "días"],
            width=100,
            command=self.on_interval_change
        )
        self.interval_type_combo.pack(side="left", padx=5, pady=5)
        self.interval_type_combo.set("horas")
        
        # Próximo backup programado
        self.next_backup_info = ctk.CTkLabel(
            schedule_tab,
            text="Próximo backup: No programado",
            font=ctk.CTkFont(size=11),
            text_color="orange"
        )
        self.next_backup_info.grid(row=2, column=1, padx=5, pady=10, sticky="w")
    
    def create_advanced_config_tab(self):
        """Crear pestaña de configuración avanzada"""
        advanced_tab = self.config_tabview.add("Avanzado")
        advanced_tab.grid_columnconfigure(1, weight=1)
        
        # Formato del nombre de archivo
        name_label = ctk.CTkLabel(advanced_tab, text="📝 Formato del nombre:")
        name_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.name_format_entry = ctk.CTkEntry(
            advanced_tab,
            placeholder_text="{server}_{date}_{time}"
        )
        self.name_format_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.name_format_entry.bind("<KeyRelease>", self.on_config_change)
        
        name_help = ctk.CTkLabel(
            advanced_tab,
            text="Variables: {server}, {date}, {time}, {map}",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        name_help.grid(row=1, column=1, padx=5, pady=(0, 10), sticky="w")
        
        # Máximo número de backups
        max_label = ctk.CTkLabel(advanced_tab, text="🗑️ Máx. backups a conservar:")
        max_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        max_frame = ctk.CTkFrame(advanced_tab)
        max_frame.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        self.max_backups_entry = ctk.CTkEntry(max_frame, width=80, placeholder_text="10")
        self.max_backups_entry.pack(side="left", padx=5, pady=5)
        self.max_backups_entry.bind("<KeyRelease>", self.on_config_change)
        
        max_help = ctk.CTkLabel(
            max_frame,
            text="(0 = sin límite)",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        max_help.pack(side="left", padx=5, pady=5)
        
        # Explicación de limpieza automática
        cleanup_info = ctk.CTkLabel(
            advanced_tab,
            text="💡 Los backups más antiguos se eliminan automáticamente después de cada backup",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        cleanup_info.grid(row=3, column=1, padx=5, pady=(0, 10), sticky="w")
        
        # Backup antes de iniciar servidor
        self.backup_before_start_var = ctk.BooleanVar()
        self.backup_before_start_check = ctk.CTkCheckBox(
            advanced_tab,
            text="🚀 Backup automático antes de iniciar servidor",
            variable=self.backup_before_start_var,
            command=self.on_config_change
        )
        self.backup_before_start_check.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        # Verificar integridad
        self.verify_backup_var = ctk.BooleanVar(value=True)
        self.verify_backup_check = ctk.CTkCheckBox(
            advanced_tab,
            text="✅ Verificar integridad del backup después de crearlo",
            variable=self.verify_backup_var,
            command=self.on_config_change
        )
        self.verify_backup_check.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        # Saveworld antes del backup
        self.saveworld_before_backup_var = ctk.BooleanVar(value=True)
        self.saveworld_before_backup_check = ctk.CTkCheckBox(
            advanced_tab,
            text="💾 Ejecutar saveworld 5 segundos antes del backup",
            variable=self.saveworld_before_backup_var,
            command=self.on_config_change
        )
        self.saveworld_before_backup_check.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="w")
    
    def create_backup_controls(self):
        """Crear controles de backup"""
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        # Botones principales
        self.backup_now_button = ctk.CTkButton(
            controls_frame,
            text="💾 Backup Ahora",
            command=self.start_manual_backup,
            width=150,
            height=40,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.backup_now_button.pack(side="left", padx=10, pady=10)
        
        self.stop_backup_button = ctk.CTkButton(
            controls_frame,
            text="⏹️ Detener",
            command=self.stop_backup,
            width=100,
            height=40,
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.stop_backup_button.pack(side="left", padx=5, pady=10)
        
        # Barra de progreso
        self.progress_frame = ctk.CTkFrame(controls_frame)
        self.progress_frame.pack(side="left", padx=10, pady=10, fill="x", expand=True)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Listo para backup",
            font=ctk.CTkFont(size=11)
        )
        self.progress_label.pack(pady=(5, 0))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 5))
        self.progress_bar.set(0)
        
        # Botones adicionales
        buttons_frame = ctk.CTkFrame(controls_frame)
        buttons_frame.pack(side="right", padx=10, pady=10)
        
        save_config_button = ctk.CTkButton(
            buttons_frame,
            text="💾 Guardar Config",
            command=self.save_backup_config,
            width=120
        )
        save_config_button.pack(side="left", padx=2)
        
        test_button = ctk.CTkButton(
            buttons_frame,
            text="🧪 Test",
            command=self.test_backup_config,
            width=80
        )
        test_button.pack(side="left", padx=2)
    
    def create_history_tab(self):
        """Crear pestaña de historial de backups"""
        history_tab = self.config_tabview.add("📂 Historial")
        history_tab.grid_columnconfigure(0, weight=1)
        history_tab.grid_rowconfigure(2, weight=1)
        
        # Título del historial con contador
        self.history_title = ctk.CTkLabel(
            history_tab,
            text="📋 Historial de Backups",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.history_title.grid(row=0, column=0, pady=(5, 5))
        
        # Contador de backups
        self.backup_counter_label = ctk.CTkLabel(
            history_tab,
            text="Backups: 0",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.backup_counter_label.grid(row=1, column=0, pady=(0, 10))
        
        # Lista de backups con scroll
        self.history_scroll = ctk.CTkScrollableFrame(history_tab)
        self.history_scroll.grid(row=2, column=0, padx=5, pady=(0, 5), sticky="nsew")
        self.history_scroll.grid_columnconfigure(0, weight=1)
        
        # Botones de gestión del historial
        history_buttons = ctk.CTkFrame(history_tab)
        history_buttons.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
        
        refresh_button = ctk.CTkButton(
            history_buttons,
            text="🔄 Actualizar",
            command=self.refresh_backup_history,
            width=100
        )
        refresh_button.pack(side="left", padx=5, pady=5)
        
        clean_button = ctk.CTkButton(
            history_buttons,
            text="🗑️ Limpiar Antiguos",
            command=self.clean_old_backups,
            width=140
        )
        clean_button.pack(side="left", padx=5, pady=5)
        
        open_folder_button = ctk.CTkButton(
            history_buttons,
            text="📁 Abrir Carpeta",
            command=self.open_backup_folder,
            width=120
        )
        open_folder_button.pack(side="right", padx=5, pady=5)
    
    def select_backup_path(self):
        """Seleccionar carpeta de backup"""
        folder = filedialog.askdirectory(title="Seleccionar carpeta para backups")
        if folder:
            old_path = self.backup_path_entry.get()
            self.backup_path_entry.delete(0, "end")
            self.backup_path_entry.insert(0, folder)
            
            # Si la ruta cambió, actualizar lista de backups
            if old_path != folder:
                self._on_backup_path_changed(folder)
    
    def set_default_backup_path(self):
        """Establecer la ruta de backup por defecto"""
        old_path = self.backup_path_entry.get()
        default_path = self.get_default_backup_path()
        self.backup_path_entry.delete(0, "end")
        self.backup_path_entry.insert(0, default_path)
        
        # Si la ruta cambió, actualizar lista de backups
        if old_path != default_path:
            self._on_backup_path_changed(default_path)
        
        # Mostrar confirmación
        self.show_ctk_info(
            "Ruta por defecto",
            f"Ruta de backup configurada a:\n{default_path}"
        )
    
    def toggle_auto_backup(self):
        """Habilitar/deshabilitar backup automático"""
        enabled = self.auto_backup_var.get()
        self.auto_backup_enabled = enabled
        
        if enabled:
            self._safe_update_status("🟢 🔄 Auto-backup activo")
            self.start_scheduler()
            # Asegurar que se calcule el próximo backup inmediatamente
            try:
                self.after(100, self._calculate_and_update_next_backup)
            except Exception as e:
                self.logger.error(f"Error al programar cálculo de próximo backup: {e}")
        else:
            self.stop_scheduler()
            self._safe_update_status("🔴 ⏹️ Inactivo")
            self._safe_update_next_backup("Próximo backup: Deshabilitado")
    
    def on_interval_change(self, event=None):
        """Llamado cuando cambia el intervalo de backup"""
        # Solo reiniciar scheduler si está habilitado
        if self.auto_backup_enabled and hasattr(self, 'auto_backup_var') and self.auto_backup_var.get():
            # Reiniciar scheduler con nueva configuración
            self.stop_scheduler()
            # Pequeño retraso para asegurar que se reinicie correctamente
            try:
                self.after(100, self.start_scheduler)
            except Exception:
                pass
            # Actualizar el próximo backup después de reiniciar
            try:
                self.after(600, self._calculate_and_update_next_backup)
            except Exception:
                pass
        elif hasattr(self, 'auto_backup_var') and self.auto_backup_var.get():
            # Si el scheduler no está corriendo pero debería estar, actualizar próximo backup
            try:
                self.after(100, self._calculate_and_update_next_backup)
            except Exception:
                pass
        else:
            # Si está deshabilitado, asegurar que muestre "Deshabilitado"
            self._safe_update_next_backup("Próximo backup: Deshabilitado")
        # Guardar configuración automáticamente
        self.on_config_change()
    
    def on_config_change(self, *args):
        """Callback cuando cambia cualquier configuración"""
        # Detectar si cambió la ruta de backup
        if hasattr(self, 'backup_path_entry') and hasattr(self, '_last_backup_path'):
            current_path = self.backup_path_entry.get().strip()
            if current_path != self._last_backup_path:
                self._last_backup_path = current_path
                if current_path:  # Solo si no está vacío
                    # Actualizar lista de backups después de un pequeño retraso
                    self.after(500, lambda: self._on_backup_path_changed(current_path))
        
        if hasattr(self, 'current_server') and self.current_server:
            # Guardar automáticamente la configuración del servidor actual
            self.save_server_config(self.current_server)
    
    def toggle_auto_backup_and_save(self):
        """Toggle auto backup y guardar configuración"""
        self.toggle_auto_backup()
        self.on_config_change()
    
    def _on_backup_path_changed(self, new_path):
        """Callback cuando cambia la ruta de backup"""
        try:
            self.logger.info(f"🔄 Ruta de backup cambiada a: {new_path}")
            
            # Escanear la nueva carpeta para encontrar backups existentes
            self._scan_backup_directory(new_path)
            
            # Actualizar la lista visual
            self.refresh_backup_history()
            
            self.logger.info(f"✅ Lista de backups actualizada para nueva ruta")
            
        except Exception as e:
            self.logger.error(f"Error al actualizar backups para nueva ruta: {e}")
    
    def _scan_backup_directory(self, backup_path):
        """Escanear directorio de backup para encontrar backups existentes"""
        try:
            if not backup_path or not os.path.exists(backup_path):
                self.logger.warning(f"Ruta de backup no existe: {backup_path}")
                self.backup_history = []
                return
            
            self.logger.info(f"🔍 Escaneando directorio de backup: {backup_path}")
            
            # Lista para almacenar los backups encontrados
            found_backups = []
            
            # Buscar archivos y carpetas que parezcan backups
            for item in os.listdir(backup_path):
                item_path = os.path.join(backup_path, item)
                
                # Buscar archivos .zip o carpetas que parezcan backups
                if self._is_backup_file(item_path):
                    backup_info = self._extract_backup_info(item_path)
                    if backup_info:
                        found_backups.append(backup_info)
            
            # Actualizar la lista de backups
            self.backup_history = found_backups
            
            # Guardar el historial actualizado
            self.save_backup_history()
            
            self.logger.info(f"📦 Encontrados {len(found_backups)} backups en la nueva ruta")
            
        except Exception as e:
            self.logger.error(f"Error escaneando directorio de backup: {e}")
            self.backup_history = []
    
    def _is_backup_file(self, file_path):
        """Determinar si un archivo o carpeta es un backup"""
        if not os.path.exists(file_path):
            return False
        
        name = os.path.basename(file_path)
        
        # Buscar patrones típicos de backup
        backup_patterns = [
            # Archivos ZIP
            lambda n: n.endswith('.zip'),
            # Carpetas que contengan nombre de servidor y fecha
            lambda n: any(server in n.lower() for server in ['ark', 'server', 'backup']),
            # Patrones con fechas
            lambda n: any(char.isdigit() for char in n) and ('_' in n or '-' in n)
        ]
        
        return any(pattern(name) for pattern in backup_patterns)
    
    def _extract_backup_info(self, backup_path):
        """Extraer información de un backup encontrado"""
        try:
            name = os.path.basename(backup_path)
            
            # Obtener información del archivo/carpeta
            stat = os.stat(backup_path)
            size = stat.st_size if os.path.isfile(backup_path) else self._get_directory_size(backup_path)
            date = datetime.fromtimestamp(stat.st_mtime)
            
            # Tratar de extraer el nombre del servidor del nombre del backup
            server_name = self._extract_server_name(name)
            
            backup_info = {
                "name": name,
                "server": server_name,
                "path": backup_path,
                "date": date.isoformat(),
                "size": size,
                "compressed": name.endswith('.zip'),
                "type": "existente"  # Marcar como backup existente encontrado
            }
            
            return backup_info
            
        except Exception as e:
            self.logger.error(f"Error extrayendo información de backup {backup_path}: {e}")
            return None
    
    def _extract_server_name(self, backup_name):
        """Extraer nombre del servidor del nombre del backup"""
        try:
            # Remover extensión
            name = backup_name.replace('.zip', '')
            
            # Buscar patrones comunes: servidor_fecha_hora
            parts = name.split('_')
            if len(parts) >= 2:
                # El primer parte suele ser el nombre del servidor
                return parts[0]
            
            # Si no hay guiones bajos, buscar otros separadores
            parts = name.split('-')
            if len(parts) >= 2:
                return parts[0]
            
            # Si no se puede determinar, usar "Unknown"
            return "Unknown"
            
        except Exception:
            return "Unknown"
    
    def _get_directory_size(self, directory):
        """Calcular tamaño total de un directorio"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            return total_size
        except Exception:
            return 0
    
    def _safe_open_folder(self, folder_path):
        """Abrir carpeta de forma segura en Windows"""
        try:
            # Normalizar el path para Windows
            normalized_path = os.path.normpath(folder_path)
            
            # Verificar que la carpeta existe
            if not os.path.exists(normalized_path):
                raise FileNotFoundError(f"La carpeta no existe: {normalized_path}")
            
            # Método 1: Usar startfile (más confiable en Windows)
            try:
                os.startfile(normalized_path)
                self.logger.info(f"📁 Carpeta abierta exitosamente: {normalized_path}")
                return  # IMPORTANTE: Salir aquí si fue exitoso
            except Exception as startfile_error:
                self.logger.warning(f"startfile falló: {startfile_error}")
            
            # Método 2: Solo si el primero falló - Usar subprocess con explorer
            try:
                import subprocess
                # Usar comillas para manejar espacios en la ruta
                cmd = f'explorer "{normalized_path}"'
                subprocess.run(cmd, shell=True, check=True)
                self.logger.info(f"📁 Carpeta abierta con explorer: {normalized_path}")
                return  # IMPORTANTE: Salir aquí si fue exitoso
            except Exception as explorer_error:
                self.logger.warning(f"explorer falló: {explorer_error}")
            
            # Método 3: Solo como último recurso
            try:
                import subprocess
                subprocess.Popen(['explorer', normalized_path])
                self.logger.info(f"📁 Carpeta abierta con Popen: {normalized_path}")
                return  # IMPORTANTE: Salir aquí si fue exitoso
            except Exception as popen_error:
                self.logger.error(f"Popen falló: {popen_error}")
            
            # Si todos los métodos fallan
            raise Exception("Todos los métodos de apertura fallaron")
            
        except Exception as e:
            error_msg = f"No se pudo abrir la carpeta: {e}"
            self.logger.error(error_msg)
            self.show_ctk_error("Error al abrir carpeta", error_msg)
    
    def _safe_open_file_location(self, file_path):
        """Abrir ubicación de archivo de forma segura en Windows"""
        try:
            # Normalizar el path para Windows
            normalized_path = os.path.normpath(file_path)
            
            # Usar subprocess con comando explorer /select
            import subprocess
            subprocess.run(['explorer', '/select,', normalized_path], shell=True, check=True)
            
            self.logger.info(f"📁 Ubicación abierta exitosamente: {normalized_path}")
            
        except Exception as e:
            # Fallback: abrir la carpeta padre
            try:
                parent_folder = os.path.dirname(file_path)
                if os.path.exists(parent_folder):
                    self._safe_open_folder(parent_folder)
                    self.logger.info(f"📁 Abrió carpeta padre como fallback: {parent_folder}")
                else:
                    raise Exception(f"La carpeta padre no existe: {parent_folder}")
                    
            except Exception as fallback_error:
                self.logger.error(f"Error en apertura de ubicación: explorer={e}, fallback={fallback_error}")
                raise Exception(f"No se pudo abrir la ubicación del archivo: {file_path}")
    
    def start_scheduler(self):
        """Iniciar programador de backups automáticos"""
        # Parar cualquier scheduler existente
        self.stop_scheduler()
        
        # Asegurar que el auto_backup esté habilitado
        self.auto_backup_enabled = True
        
        self.scheduler_thread = threading.Thread(target=self._scheduler_worker, daemon=True)
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        """Detener programador de backups"""
        self.auto_backup_enabled = False
        schedule.clear()
    
    def _scheduler_worker(self):
        """Worker del programador de backups"""
        try:
            # Esperar a que la UI esté completamente inicializada
            for i in range(10):  # Máximo 5 segundos de espera
                try:
                    if (hasattr(self, 'interval_value_entry') and 
                        hasattr(self, 'interval_type_combo') and 
                        hasattr(self, 'status_label') and 
                        hasattr(self, 'next_backup_info') and
                        self.interval_value_entry.winfo_exists() and
                        self.interval_type_combo.winfo_exists()):
                        break
                except:
                    pass
                time.sleep(0.5)
            else:
                self.logger.warning("Scheduler iniciado pero widgets de UI no están listos")
                return
            
            # Limpiar trabajos anteriores
            schedule.clear()
            
            # Obtener configuración de forma segura
            try:
                interval_value = int(self.interval_value_entry.get() or "6")
                interval_type = self.interval_type_combo.get()
            except Exception as e:
                self.logger.error(f"Error al obtener configuración del scheduler: {e}")
                # Usar valores por defecto
                interval_value = 6
                interval_type = "horas"
            
            # Programar según el tipo de intervalo
            if interval_type == "minutos":
                schedule.every(interval_value).minutes.do(self._scheduled_backup)
            elif interval_type == "horas":
                schedule.every(interval_value).hours.do(self._scheduled_backup)
            elif interval_type == "días":
                schedule.every(interval_value).days.do(self._scheduled_backup)
            
            self.logger.info(f"Backup automático programado cada {interval_value} {interval_type}")
            
            # Actualizar estado inicial de forma segura
            try:
                if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                    # Usar el hilo principal de Tkinter para actualizar la UI
                    self._safe_schedule_ui_update(lambda: self._safe_update_status("🟢 🔄 Auto-backup activo"))
                # Calcular y mostrar próximo backup inmediatamente
                # Usar el hilo principal de Tkinter para actualizar la UI
                self._safe_schedule_ui_update(self._calculate_and_update_next_backup)
            except:
                pass
            
            # Ejecutar scheduler
            while self.auto_backup_enabled:
                schedule.run_pending()
                
                # Actualizar próximo backup de forma segura
                try:
                    jobs = schedule.jobs
                    if jobs and hasattr(self, 'next_backup_info'):
                        # Obtener el próximo trabajo programado
                        next_job = jobs[0] if jobs else None
                        if next_job and hasattr(next_job, 'next_run'):
                            next_time = next_job.next_run.strftime('%d/%m/%Y %H:%M:%S')
                            # Usar el hilo principal de Tkinter para actualizar la UI
                            self._safe_schedule_ui_update(lambda t=next_time: self._safe_update_next_backup(f"Próximo backup: {t}"))
                        else:
                            # Calcular próximo backup basado en intervalo
                            self._calculate_and_update_next_backup()
                    else:
                        # Usar el hilo principal de Tkinter para actualizar la UI
                        self._safe_schedule_ui_update(lambda: self._safe_update_next_backup("Próximo backup: No programado"))
                except Exception as e:
                    self.logger.debug(f"Error al actualizar próximo backup: {e}")
                    # Fallback: calcular basado en configuración
                    self._calculate_and_update_next_backup()
                
                time.sleep(60)  # Verificar cada minuto
                
        except Exception as e:
            self.logger.error(f"Error en scheduler de backup: {e}")
            try:
                # Usar el hilo principal de Tkinter para actualizar la UI
                self._safe_schedule_ui_update(lambda: self._safe_update_status("❌ Error en programador"))
            except:
                pass
    
    def _safe_update_status(self, text):
        """Actualizar estado de forma segura"""
        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.configure(text=text)
        except Exception as e:
            self.logger.debug(f"Error al actualizar status label: {e}")
    
    def _safe_update_next_backup(self, text):
        """Actualizar próximo backup de forma segura"""
        try:
            if hasattr(self, 'next_backup_info') and self.next_backup_info.winfo_exists():
                self.next_backup_info.configure(text=text)
        except Exception as e:
            self.logger.debug(f"Error al actualizar next backup label: {e}")
    
    def _calculate_and_update_next_backup(self):
        """Calcular y actualizar próximo backup basado en configuración"""
        try:
            # Verificar que el auto-backup esté habilitado (usar solo la variable de UI como fuente de verdad)
            if not hasattr(self, 'auto_backup_var') or not self.auto_backup_var.get():
                self._safe_update_next_backup("Próximo backup: Deshabilitado")
                return
                
            if not hasattr(self, 'interval_value_entry') or not hasattr(self, 'interval_type_combo'):
                self._safe_update_next_backup("Próximo backup: Configuración no disponible")
                return
                
            interval_value = int(self.interval_value_entry.get() or "6")
            interval_type = self.interval_type_combo.get()
            
            from datetime import datetime, timedelta
            now = datetime.now()
            
            if interval_type == "minutos":
                next_backup = now + timedelta(minutes=interval_value)
            elif interval_type == "horas":
                next_backup = now + timedelta(hours=interval_value)
            elif interval_type == "días":
                next_backup = now + timedelta(days=interval_value)
            else:
                next_backup = now + timedelta(hours=6)  # fallback
                
            next_time = next_backup.strftime('%d/%m/%Y %H:%M:%S')
            # Usar el hilo principal de Tkinter para actualizar la UI
            self._safe_schedule_ui_update(lambda t=next_time: self._safe_update_next_backup(f"Próximo backup: {t}"))
            
        except Exception as e:
            self.logger.debug(f"Error al calcular próximo backup: {e}")
            # Usar el hilo principal de Tkinter para actualizar la UI
            self._safe_schedule_ui_update(lambda: self._safe_update_next_backup("Próximo backup: Error al calcular"))
    
    def _scheduled_backup(self):
        """Ejecutar backup programado"""
        if not self.backup_running:
            start_msg = "Ejecutando backup automático programado"
            self.logger.info(start_msg)
            self.show_message(f"🔄 {start_msg}")
            # Usar el hilo principal de Tkinter para actualizar la UI
            self._safe_schedule_ui_update(lambda: self.start_backup(is_manual=False))
    
    def start_manual_backup(self):
        """Iniciar backup manual"""
        self.start_backup(is_manual=True)
    
    def start_backup(self, is_manual=True):
        """Iniciar backup (manual o automático)"""
        if self.backup_running:
            if is_manual:
                self.show_ctk_error("Backup en progreso", "Ya hay un backup en ejecución")
            return
        
        # Validar configuración
        if not self.validate_backup_config():
            if is_manual:
                self.show_ctk_error("Configuración inválida", "Por favor revisa la configuración de backup")
            return
        
        # Log en área principal
        backup_type = "manual" if is_manual else "automático"
        if hasattr(self.main_window, 'add_log_message'):
            self.main_window.add_log_message(f"💾 Iniciando backup {backup_type}...")
        
        # Registrar inicio del backup
        if hasattr(self.main_window, 'log_server_event'):
            self.main_window.log_server_event("custom_event", 
                event_name=f"Backup {backup_type} iniciado", 
                details=f"Iniciando backup del servidor")
        
        # Verificar si debe hacer saveworld antes del backup
        if self.saveworld_before_backup_var.get():
            if hasattr(self.main_window, 'add_log_message'):
                self.main_window.add_log_message("⏳ Saveworld programado antes del backup...")
            # Ejecutar saveworld y luego backup
            self._execute_saveworld_then_backup(is_manual)
        else:
            # Iniciar backup directamente
            self._start_backup_worker(is_manual)
    
    def _execute_saveworld_then_backup(self, is_manual):
        """Ejecutar saveworld y luego iniciar backup después de 5 segundos"""
        try:
            # Ejecutar saveworld via RCON
            if hasattr(self.main_window, 'add_log_message'):
                        self._safe_schedule_ui_update(lambda: self.main_window.add_log_message("💾 Ejecutando saveworld antes del backup..."))
            
            saveworld_success = False
            if hasattr(self.main_window, 'rcon_panel'):
                result = self.main_window.rcon_panel.execute_rcon_command("saveworld")
                if result and not result.startswith("❌"):
                    saveworld_success = True
                    if hasattr(self.main_window, 'add_log_message'):
                        self._safe_schedule_ui_update(lambda: self.main_window.add_log_message("✅ Saveworld ejecutado correctamente"))
                else:
                    if hasattr(self.main_window, 'add_log_message'):
                        self._safe_schedule_ui_update(lambda: self.main_window.add_log_message("⚠️ Error en saveworld, continuando con backup..."))
            else:
                if hasattr(self.main_window, 'add_log_message'):
                    self._safe_schedule_ui_update(lambda: self.main_window.add_log_message("⚠️ RCON no disponible, continuando con backup..."))
            
            # Esperar 5 segundos antes del backup
            if hasattr(self.main_window, 'add_log_message'):
                self._safe_schedule_ui_update(lambda: self.main_window.add_log_message("⏳ Esperando 5 segundos antes del backup..."))
            
            # Programar el backup después de 5 segundos
            # Usar el hilo principal de Tkinter para programar el backup
            try:
                self.after(5000, lambda: self._start_backup_worker(is_manual))
            except Exception:
                pass
            
        except Exception as e:
            self.logger.error(f"Error en saveworld antes del backup: {e}")
            if hasattr(self.main_window, 'add_log_message'):
                self._safe_schedule_ui_update(lambda: self.main_window.add_log_message(f"❌ Error en saveworld: {e}, continuando con backup..."))
            # Continuar con backup aunque falle saveworld
            self._start_backup_worker(is_manual)
    
    def _start_backup_worker(self, is_manual):
        """Iniciar el worker del backup"""
        # Iniciar backup en hilo separado
        self.backup_thread = threading.Thread(target=lambda: self._backup_worker(is_manual), daemon=True)
        self.backup_thread.start()
    
    def _backup_worker(self, is_manual=True):
        """Worker del proceso de backup"""
        try:
            self.backup_running = True
            # Usar el hilo principal de Tkinter para actualizar la UI
            self._safe_schedule_ui_update(self._update_backup_ui_start)
            
            # Obtener información del servidor
            server_name = getattr(self.main_window, 'selected_server', 'Unknown')
            if server_name == 'Unknown' or not server_name:
                raise Exception("No hay servidor seleccionado")
            
            # Crear nombre del backup
            backup_name = self.generate_backup_name(server_name)
            backup_path = os.path.join(self.backup_path_entry.get(), backup_name)
            
            # Crear directorio temporal si es necesario
            if self.compress_var.get():
                temp_dir = backup_path + "_temp"
                os.makedirs(temp_dir, exist_ok=True)
                actual_backup_path = temp_dir
            else:
                os.makedirs(backup_path, exist_ok=True)
                actual_backup_path = backup_path
            
            # Obtener rutas del servidor
            server_root = os.path.join(
                self.config_manager.get("server", "root_path", ""),
                server_name
            )
            
            if not os.path.exists(server_root):
                raise Exception(f"No se encontró el directorio del servidor: {server_root}")
            
            # Realizar backup de diferentes componentes
            total_steps = 0
            if self.include_saves_var.get(): total_steps += 1
            if self.include_configs_var.get(): total_steps += 1
            if self.include_logs_var.get(): total_steps += 1
            
            current_step = 0
            
            # Log inicio del proceso de backup
            if hasattr(self.main_window, 'add_log_message'):
                self._safe_schedule_ui_update(lambda: self.main_window.add_log_message(f"📁 Iniciando backup de servidor: {server_name}"))
            
            # Backup de archivos de guardado
            if self.include_saves_var.get():
                if hasattr(self.main_window, 'add_log_message'):
                    self._safe_schedule_ui_update(lambda: self.main_window.add_log_message("💾 Copiando archivos de guardado..."))
                # Usar el hilo principal de Tkinter para actualizar la UI
                self._safe_schedule_ui_update(lambda: self.progress_label.configure(text="Copiando archivos de guardado..."))
                self._backup_saves(server_root, actual_backup_path)
                current_step += 1
                # Usar el hilo principal de Tkinter para actualizar la UI
                self._safe_schedule_ui_update(lambda: self.progress_bar.set(current_step / total_steps * 0.8))
                if hasattr(self.main_window, 'add_log_message'):
                    self._safe_schedule_ui_update(lambda: self.main_window.add_log_message("✅ Archivos de guardado copiados"))
            
            # Backup de configuraciones
            if self.include_configs_var.get():
                if hasattr(self.main_window, 'add_log_message'):
                    self._safe_schedule_ui_update(lambda: self.main_window.add_log_message("⚙️ Copiando configuraciones..."))
                # Usar el hilo principal de Tkinter para actualizar la UI
                self._safe_schedule_ui_update(lambda: self.progress_label.configure(text="Copiando configuraciones..."))
                self._backup_configs(server_root, actual_backup_path)
                current_step += 1
                # Usar el hilo principal de Tkinter para actualizar la UI
                self._safe_schedule_ui_update(lambda: self.progress_bar.set(current_step / total_steps * 0.8))
                if hasattr(self.main_window, 'add_log_message'):
                    self._safe_schedule_ui_update(lambda: self.main_window.add_log_message("✅ Configuraciones copiadas"))
            
            # Backup de logs
            if self.include_logs_var.get():
                if hasattr(self.main_window, 'add_log_message'):
                    self._safe_schedule_ui_update(lambda: self.main_window.add_log_message("📋 Copiando logs del servidor..."))
                # Usar el hilo principal de Tkinter para actualizar la UI
                self._safe_schedule_ui_update(lambda: self.progress_label.configure(text="Copiando logs..."))
                self._backup_logs(server_root, actual_backup_path)
                current_step += 1
                # Usar el hilo principal de Tkinter para actualizar la UI
                self._safe_schedule_ui_update(lambda: self.progress_bar.set(current_step / total_steps * 0.8))
                if hasattr(self.main_window, 'add_log_message'):
                    self._safe_schedule_ui_update(lambda: self.main_window.add_log_message("✅ Logs del servidor copiados"))
            
            # Comprimir si está habilitado
            if self.compress_var.get():
                if hasattr(self.main_window, 'add_log_message'):
                    self._safe_schedule_ui_update(lambda: self.main_window.add_log_message("🗜️ Comprimiendo backup..."))
                # Usar el hilo principal de Tkinter para actualizar la UI
                self._safe_schedule_ui_update(lambda: self.progress_label.configure(text="Comprimiendo backup..."))
                zip_path = backup_path + ".zip"
                self._compress_backup(actual_backup_path, zip_path)
                # Eliminar carpeta temporal con manejo robusto de errores
                self._safe_cleanup_temp_directory(actual_backup_path)
                final_path = zip_path
                if hasattr(self.main_window, 'add_log_message'):
                    self._safe_schedule_ui_update(lambda: self.main_window.add_log_message("✅ Backup comprimido correctamente"))
            else:
                final_path = backup_path
            
            # Verificar integridad si está habilitado
            if self.verify_backup_var.get():
                if hasattr(self.main_window, 'add_log_message'):
                    self._safe_schedule_ui_update(lambda: self.main_window.add_log_message("🔍 Verificando integridad del backup..."))
                # Usar el hilo principal de Tkinter para actualizar la UI
                self._safe_schedule_ui_update(lambda: self.progress_label.configure(text="Verificando integridad..."))
                self._verify_backup(final_path)
                if hasattr(self.main_window, 'add_log_message'):
                    self._safe_schedule_ui_update(lambda: self.main_window.add_log_message("✅ Integridad del backup verificada"))
            
            # Registrar backup exitoso
            backup_info = {
                "name": backup_name,
                "server": server_name,
                "path": final_path,
                "date": datetime.now().isoformat(),
                "size": self._get_backup_size(final_path),
                "compressed": self.compress_var.get(),
                "type": "manual" if is_manual else "automático"
            }
            
            # Calcular tamaño formateado
            size_mb = backup_info["size"] / (1024 * 1024)
            if hasattr(self.main_window, 'add_log_message'):
                self._safe_schedule_ui_update(lambda: self.main_window.add_log_message(f"✅ Backup completado exitosamente - Tamaño: {size_mb:.1f} MB"))
            
            self.backup_history.append(backup_info)
            self.save_backup_history()
            
            # Limpiar backups antiguos si es necesario
            self._cleanup_old_backups()
            
            # Usar el hilo principal de Tkinter para actualizar la UI
            self._safe_schedule_ui_update(lambda: self._update_backup_ui_success(backup_info, is_manual))
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error durante backup: {error_msg}")
            if hasattr(self.main_window, 'add_log_message') and hasattr(self.main_window, 'root'):
                self._safe_schedule_ui_update(lambda: self.main_window.add_log_message(f"❌ Error en backup: {error_msg}"))
            # Usar el hilo principal de Tkinter para actualizar la UI
            self._safe_schedule_ui_update(lambda: self._update_backup_ui_error(error_msg, is_manual))
        finally:
            self.backup_running = False
    
    def _backup_saves(self, server_root, backup_path):
        """Backup de archivos de guardado"""
        saves_src = os.path.join(server_root, "ShooterGame", "Saved", "SavedArks")
        saves_dst = os.path.join(backup_path, "SavedArks")
        
        if os.path.exists(saves_src):
            shutil.copytree(saves_src, saves_dst, dirs_exist_ok=True)
    
    def _backup_configs(self, server_root, backup_path):
        """Backup de archivos de configuración"""
        configs_src = os.path.join(server_root, "ShooterGame", "Saved", "Config")
        configs_dst = os.path.join(backup_path, "Config")
        
        if os.path.exists(configs_src):
            shutil.copytree(configs_src, configs_dst, dirs_exist_ok=True)
    
    def _backup_logs(self, server_root, backup_path):
        """Backup de archivos de log"""
        logs_src = os.path.join(server_root, "ShooterGame", "Saved", "Logs")
        logs_dst = os.path.join(backup_path, "Logs")
        
        if os.path.exists(logs_src):
            shutil.copytree(logs_src, logs_dst, dirs_exist_ok=True)
    
    def _compress_backup(self, source_dir, zip_path):
        """Comprimir backup a ZIP"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arc_name)
    
    def _safe_cleanup_temp_directory(self, temp_dir_path):
        """Limpiar directorio temporal de forma segura con reintentos"""
        if not temp_dir_path or not os.path.exists(temp_dir_path):
            return
            
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                shutil.rmtree(temp_dir_path)
                self.logger.info(f"🧹 Directorio temporal limpiado exitosamente: {temp_dir_path}")
                return
            except PermissionError as e:
                self.logger.warning(f"⚠️ Error de permisos limpiando directorio temporal (intento {attempt + 1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    # Esperar un poco y reintentar
                    import time
                    time.sleep(0.5)
                    continue
            except OSError as e:
                self.logger.warning(f"⚠️ Error del sistema limpiando directorio temporal (intento {attempt + 1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(0.5)
                    continue
            except Exception as e:
                self.logger.error(f"❌ Error inesperado limpiando directorio temporal (intento {attempt + 1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(0.5)
                    continue
        
        # Si llegamos aquí, todos los intentos fallaron
        try:
            # Último intento con ignore_errors=True
            shutil.rmtree(temp_dir_path, ignore_errors=True)
            if not os.path.exists(temp_dir_path):
                self.logger.info(f"🧹 Limpieza forzada exitosa: {temp_dir_path}")
            else:
                self.logger.error(f"❌ No se pudo limpiar directorio temporal después de {max_attempts} intentos: {temp_dir_path}")
                # Registrar contenido para debugging
                try:
                    files = os.listdir(temp_dir_path)
                    self.logger.error(f"📁 Contenido del directorio no eliminado: {files}")
                except:
                    pass
        except Exception as final_error:
            self.logger.error(f"❌ Error crítico en limpieza final: {final_error}")
    
    def _verify_backup(self, backup_path):
        """Verificar integridad del backup"""
        if backup_path.endswith('.zip'):
            # Verificar ZIP
            try:
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.testzip()
            except zipfile.BadZipFile:
                raise Exception("El archivo ZIP está corrupto")
        else:
            # Verificar directorio
            if not os.path.exists(backup_path):
                raise Exception("El directorio de backup no existe")
    
    def _get_backup_size(self, path):
        """Obtener tamaño del backup"""
        if os.path.isfile(path):
            return os.path.getsize(path)
        else:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
            return total_size
    
    def _cleanup_old_backups(self):
        """Limpiar backups antiguos según configuración"""
        try:
            max_backups = int(self.max_backups_entry.get() or "10")
            
            # Si max_backups es 0, no hay límite
            if max_backups <= 0:
                self.logger.info("Límite de backups deshabilitado (0 = sin límite)")
                return
            
            current_count = len(self.backup_history)
            if current_count > max_backups:
                # Ordenar por fecha (más antiguos primero)
                self.backup_history.sort(key=lambda x: x['date'])
                to_remove = self.backup_history[:-max_backups]
                removed_count = 0
                
                for backup in to_remove:
                    try:
                        if os.path.exists(backup['path']):
                            if os.path.isfile(backup['path']):
                                os.remove(backup['path'])
                            else:
                                shutil.rmtree(backup['path'])
                        self.backup_history.remove(backup)
                        removed_count += 1
                        self.logger.info(f"Backup antiguo eliminado: {backup['name']}")
                    except Exception as e:
                        self.logger.warning(f"No se pudo eliminar backup antiguo {backup['name']}: {e}")
                
                if removed_count > 0:
                    self.logger.info(f"Limpieza automática: {removed_count} backups antiguos eliminados (límite: {max_backups})")
                    self.save_backup_history()
            else:
                self.logger.debug(f"No es necesario limpiar backups ({current_count}/{max_backups})")
                
        except Exception as e:
            self.logger.error(f"Error al limpiar backups antiguos: {e}")
    
    def generate_backup_name(self, server_name):
        """Generar nombre del backup"""
        now = datetime.now()
        
        # Obtener formato o usar por defecto
        name_format = self.name_format_entry.get() or "{server}_{date}_{time}"
        
        # Obtener datos con valores por defecto seguros
        server_name = server_name or "Unknown"
        selected_map = getattr(self.main_window, 'selected_map', None) or "Unknown"
        
        # Reemplazar variables
        backup_name = name_format.replace("{server}", server_name)
        backup_name = backup_name.replace("{date}", now.strftime("%Y%m%d"))
        backup_name = backup_name.replace("{time}", now.strftime("%H%M%S"))
        backup_name = backup_name.replace("{map}", selected_map)
        
        return backup_name
    
    def validate_backup_config(self):
        """Validar configuración de backup"""
        if not self.backup_path_entry.get():
            self.show_ctk_error("Error", "Debe seleccionar una ruta de backup")
            return False
        
        if not os.path.exists(self.backup_path_entry.get()):
            try:
                os.makedirs(self.backup_path_entry.get(), exist_ok=True)
            except Exception as e:
                self.show_ctk_error("Error", f"No se puede crear la carpeta de backup: {e}")
                return False
        
        if not any([self.include_saves_var.get(), self.include_configs_var.get(), self.include_logs_var.get()]):
            self.show_ctk_error("Error", "Debe seleccionar al menos un tipo de contenido para el backup")
            return False
        
        return True
    
    def test_backup_config(self):
        """Probar configuración de backup"""
        if self.validate_backup_config():
            self.show_ctk_info("Test exitoso", "La configuración de backup es válida")
    
    def stop_backup(self):
        """Detener backup en progreso"""
        if self.backup_running:
            self.backup_running = False
            self.show_ctk_info("Backup detenido", "El backup ha sido cancelado")
    
    def _update_backup_ui_start(self):
        """Actualizar UI al iniciar backup"""
        self.backup_now_button.configure(state="disabled")
        self.stop_backup_button.configure(state="normal")
        self.status_label.configure(text="▶️ Backup en progreso")
        self.progress_bar.set(0.1)
        self.progress_label.configure(text="Iniciando backup...")
    
    def _update_backup_ui_success(self, backup_info, is_manual=True):
        """Actualizar UI al completar backup exitosamente"""
        self.backup_now_button.configure(state="normal")
        self.stop_backup_button.configure(state="disabled")
        self.status_label.configure(text="✅ Backup completado")
        self.progress_bar.set(1.0)
        self.progress_label.configure(text=f"Backup completado: {backup_info['name']}")
        
        # Refrescar historial
        self.refresh_backup_history()
        
        # Registrar finalización del backup
        if hasattr(self.main_window, 'log_server_event'):
            backup_type = "manual" if is_manual else "automático"
            self.main_window.log_server_event("backup_event", 
                success=True,
                details=f"Backup '{backup_info['name']}' creado exitosamente",
                event_type=backup_type)
        
        # Notificación solo para backups manuales
        if is_manual:
            self.show_ctk_info("Backup completado", f"Backup '{backup_info['name']}' creado exitosamente")
        else:
            # Para backups automáticos, log y mensaje en app
            success_msg = f"Backup automático completado exitosamente: {backup_info['name']}"
            self.logger.info(success_msg)
            self.show_message(f"✅ {success_msg}")
    
    def _update_backup_ui_error(self, error_msg, is_manual=True):
        """Actualizar UI en caso de error"""
        self.backup_now_button.configure(state="normal")
        self.stop_backup_button.configure(state="disabled")
        self.status_label.configure(text="❌ Error en backup")
        self.progress_bar.set(0)
        self.progress_label.configure(text=f"Error: {error_msg}")
        
        # Registrar error del backup
        if hasattr(self.main_window, 'log_server_event'):
            backup_type = "manual" if is_manual else "automático"
            self.main_window.log_server_event("backup_event", 
                event_type=backup_type,
                success=False,
                details=f"Error: {error_msg}")
        
        # Notificación de error solo para backups manuales
        if is_manual:
            self.show_ctk_error("Error de backup", f"Error durante el backup:\n{error_msg}")
        else:
            # Para backups automáticos, log y mensaje en app
            error_log_msg = f"Error en backup automático: {error_msg}"
            self.logger.error(error_log_msg)
            self.show_message(f"❌ {error_log_msg}")
    
    def update_backup_counter(self):
        """Actualizar contador de backups (por servidor)"""
        try:
            # Contar backups del servidor seleccionado
            if self.current_server:
                server_backups = [backup for backup in self.backup_history if backup.get('server') == self.current_server]
                current_count = len(server_backups)
                max_backups = int(self.max_backups_entry.get() or "10")
                
                if max_backups <= 0:
                    counter_text = f"Backups ({self.current_server}): {current_count} (sin límite)"
                else:
                    counter_text = f"Backups ({self.current_server}): {current_count}/{max_backups}"
                    if current_count >= max_backups:
                        counter_text += " (se eliminarán los más antiguos)"
            else:
                counter_text = "Seleccione un servidor"
            
            if hasattr(self, 'backup_counter_label'):
                self.backup_counter_label.configure(text=counter_text)
                
        except Exception as e:
            self.logger.error(f"Error al actualizar contador de backups: {e}")
    
    def refresh_backup_history(self):
        """Refrescar lista de historial de backups (filtrado por servidor)"""
        # Actualizar contador
        self.update_backup_counter()
        
        # Limpiar contenido actual
        for widget in self.history_scroll.winfo_children():
            widget.destroy()
        
        # Filtrar backups por servidor seleccionado
        if self.current_server:
            server_backups = [backup for backup in self.backup_history if backup.get('server') == self.current_server]
        else:
            server_backups = []
        
        if not server_backups:
            if self.current_server:
                no_backups_label = ctk.CTkLabel(
                    self.history_scroll,
                    text=f"📭 No hay backups para el servidor '{self.current_server}'",
                    text_color="gray"
                )
            else:
                no_backups_label = ctk.CTkLabel(
                    self.history_scroll,
                    text="📭 Seleccione un servidor para ver sus backups",
                    text_color="gray"
                )
            no_backups_label.pack(pady=20)
            return
        
        # Mostrar backups en orden inverso (más recientes primero)
        for i, backup in enumerate(reversed(server_backups)):
            self.create_backup_entry(backup, i)
    
    def create_backup_entry(self, backup, index):
        """Crear entrada de backup en el historial"""
        entry_frame = ctk.CTkFrame(self.history_scroll)
        entry_frame.pack(fill="x", padx=5, pady=2)
        entry_frame.grid_columnconfigure(1, weight=1)
        
        # Información del backup
        info_frame = ctk.CTkFrame(entry_frame)
        info_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
        info_frame.grid_columnconfigure(1, weight=1)
        
        # Nombre y fecha
        name_label = ctk.CTkLabel(
            info_frame,
            text=f"📦 {backup['name']}",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        name_label.grid(row=0, column=0, sticky="w", padx=5)
        
        date_obj = datetime.fromisoformat(backup['date'])
        date_label = ctk.CTkLabel(
            info_frame,
            text=date_obj.strftime("%Y-%m-%d %H:%M:%S"),
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        date_label.grid(row=0, column=1, sticky="e", padx=5)
        
        # Detalles
        size_mb = backup['size'] / (1024 * 1024)
        details_text = f"Servidor: {backup['server']} | Tamaño: {size_mb:.1f} MB"
        if backup['compressed']:
            details_text += " | Comprimido"
        
        details_label = ctk.CTkLabel(
            info_frame,
            text=details_text,
            font=ctk.CTkFont(size=9),
            text_color="gray"
        )
        details_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=5)
        
        # Botones de acción
        buttons_frame = ctk.CTkFrame(entry_frame)
        buttons_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 5))
        
        restore_button = ctk.CTkButton(
            buttons_frame,
            text="🔄 Restaurar",
            command=lambda b=backup: self.restore_backup(b),
            width=80,
            height=25
        )
        restore_button.pack(side="left", padx=2)
        
        verify_button = ctk.CTkButton(
            buttons_frame,
            text="✅ Verificar",
            command=lambda b=backup: self.verify_backup_integrity(b),
            width=80,
            height=25
        )
        verify_button.pack(side="left", padx=2)
        
        delete_button = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Eliminar",
            command=lambda b=backup: self.delete_backup(b),
            width=80,
            height=25,
            fg_color="red",
            hover_color="darkred"
        )
        delete_button.pack(side="right", padx=2)
        
        open_button = ctk.CTkButton(
            buttons_frame,
            text="📁 Abrir",
            command=lambda b=backup: self.open_backup_location(b),
            width=80,
            height=25
        )
        open_button.pack(side="right", padx=2)
    
    def restore_backup(self, backup):
        """Restaurar un backup"""
        def on_confirm():
            threading.Thread(target=self._restore_worker, args=(backup,), daemon=True).start()
        
        self.show_ctk_confirm(
            "Confirmar restauración",
            f"¿Está seguro de que desea restaurar el backup '{backup['name']}'?\n\n"
            "⚠️ ADVERTENCIA: Esto sobrescribirá los archivos actuales del servidor.",
            on_confirm
        )
    
    def _restore_worker(self, backup):
        """Worker para restaurar backup"""
        try:
            try:
                self.after(0, lambda: self.progress_label.configure(text="Restaurando backup..."))
            except Exception as e:
                self.logger.error(f"Error al actualizar etiqueta de progreso: {e}")
            
            server_name = backup['server']
            server_root = os.path.join(
                self.config_manager.get("server", "root_path", ""),
                server_name
            )
            
            # Implementar lógica de restauración específica aquí
            # Por ahora, solo un mensaje
            try:
                self.after(0, lambda: self.show_ctk_info(
                    "Restauración",
                    f"Funcionalidad de restauración para '{backup['name']}' en desarrollo"
                ))
            except Exception as e:
                self.logger.error(f"Error al mostrar mensaje de restauración: {e}")
            
        except Exception as e:
            self.logger.error(f"Error al restaurar backup: {e}")
            try:
                self.after(0, lambda: self.show_ctk_error("Error", f"Error al restaurar: {e}"))
            except Exception as e2:
                self.logger.error(f"Error al mostrar mensaje de error: {e2}")
    
    def verify_backup_integrity(self, backup):
        """Verificar integridad de un backup"""
        try:
            self._verify_backup(backup['path'])
            self.show_ctk_info("Verificación exitosa", f"El backup '{backup['name']}' está íntegro")
        except Exception as e:
            self.show_ctk_error("Error de integridad", f"El backup está corrupto: {e}")
    
    def delete_backup(self, backup):
        """Eliminar un backup"""
        def on_confirm():
            self._delete_backup_confirmed(backup)
        
        self.show_ctk_confirm(
            "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar el backup '{backup['name']}'?\n\n"
            "Esta acción no se puede deshacer.",
            on_confirm
        )
    
    def _delete_backup_confirmed(self, backup):
        """Ejecutar eliminación confirmada"""
        try:
            if os.path.exists(backup['path']):
                if os.path.isfile(backup['path']):
                    os.remove(backup['path'])
                else:
                    shutil.rmtree(backup['path'])
            
            self.backup_history.remove(backup)
            self.save_backup_history()
            self.refresh_backup_history()
            
            self.show_ctk_info("Eliminado", f"Backup '{backup['name']}' eliminado exitosamente")
            
        except Exception as e:
            self.show_ctk_error("Error", f"No se pudo eliminar el backup: {e}")
    
    def open_backup_location(self, backup):
        """Abrir ubicación del backup"""
        try:
            backup_path = backup['path']
            if os.path.exists(backup_path):
                self._safe_open_file_location(backup_path)
            else:
                self.logger.warning(f"Backup no existe: {backup_path}")
                self.show_ctk_error("Archivo no encontrado", "El backup no existe en la ubicación registrada")
        except Exception as e:
            self.logger.error(f"Error abriendo ubicación del backup: {e}")
            self.show_ctk_error("Error", f"No se pudo abrir la ubicación: {e}")
    
    def clean_old_backups(self):
        """Limpiar backups antiguos manualmente"""
        def on_confirm():
            self._cleanup_old_backups()
            self.refresh_backup_history()
            self.show_ctk_info("Limpieza completada", "Backups antiguos eliminados")
        
        self.show_ctk_confirm(
            "Limpiar backups antiguos",
            f"¿Eliminar todos los backups excepto los últimos {self.max_backups_entry.get() or '10'}?",
            on_confirm
        )
    
    def open_backup_folder(self):
        """Abrir carpeta de backups"""
        backup_path = self.backup_path_entry.get().strip()
        if backup_path and os.path.exists(backup_path):
            try:
                self._safe_open_folder(backup_path)
            except Exception as e:
                self.logger.error(f"Error abriendo carpeta de backup: {e}")
                self.show_ctk_error("Error", f"No se pudo abrir la carpeta: {e}")
        else:
            self.logger.warning(f"Carpeta de backup no existe: {backup_path}")
            self.show_ctk_error("Carpeta no encontrada", "La carpeta de backup no existe")
    
    def load_backup_config(self):
        """Cargar configuración de backup guardada"""
        try:
            config_file = "data/backup_config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                
                # Actualizar widgets con configuración guardada
                self.backup_path_entry.delete(0, "end")
                backup_path = saved_config.get("backup_path", self.get_default_backup_path())
                # Si la ruta guardada está vacía, usar la por defecto
                if not backup_path:
                    backup_path = self.get_default_backup_path()
                self.backup_path_entry.insert(0, backup_path)
                
                self.auto_backup_var.set(saved_config.get("auto_backup", False))
                self.interval_value_entry.delete(0, "end")
                self.interval_value_entry.insert(0, str(saved_config.get("interval_value", 6)))
                self.interval_type_combo.set(saved_config.get("interval_type", "horas"))
                
                self.compress_var.set(saved_config.get("compress", True))
                self.include_saves_var.set(saved_config.get("include_saves", True))
                self.include_configs_var.set(saved_config.get("include_configs", True))
                self.include_logs_var.set(saved_config.get("include_logs", False))
                
                self.name_format_entry.delete(0, "end")
                self.name_format_entry.insert(0, saved_config.get("backup_name_format", "{server}_{date}_{time}"))
                
                self.max_backups_entry.delete(0, "end")
                self.max_backups_entry.insert(0, str(saved_config.get("max_backups", 10)))
                
                self.backup_before_start_var.set(saved_config.get("backup_before_start", False))
                self.verify_backup_var.set(saved_config.get("verify_backup", True))
                self.saveworld_before_backup_var.set(saved_config.get("saveworld_before_backup", True))
                
            else:
                # Si no hay configuración guardada, usar valores por defecto
                self.backup_path_entry.delete(0, "end")
                self.backup_path_entry.insert(0, self.get_default_backup_path())
                self.logger.info(f"Configuración de backup por defecto cargada: {self.get_default_backup_path()}")
                
        except Exception as e:
            self.logger.error(f"Error al cargar configuración de backup: {e}")
            # En caso de error, usar configuración por defecto
            try:
                self.backup_path_entry.delete(0, "end")
                self.backup_path_entry.insert(0, self.get_default_backup_path())
            except:
                pass
    
    def save_backup_config(self):
        """Guardar configuración de backup (ahora por servidor)"""
        if self.current_server:
            self.save_server_config(self.current_server)
        else:
            self.show_ctk_error("Error", "Debe seleccionar un servidor antes de guardar la configuración")
    
    def load_backup_history(self):
        """Cargar historial de backups"""
        try:
            history_file = "data/backup_history.json"
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.backup_history = json.load(f)
                
                self.refresh_backup_history()
                
        except Exception as e:
            self.logger.error(f"Error al cargar historial de backup: {e}")
            self.backup_history = []
    
    def save_backup_history(self):
        """Guardar historial de backups"""
        try:
            # Usar método centralizado para obtener ruta de datos
            history_file = self.config_manager.get_data_file_path("backup_history.json")
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.backup_history, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error al guardar historial de backup: {e}")
    
    def check_auto_backup(self):
        """Verificar si debe habilitar auto backup al inicio"""
        try:
            # Verificar que los widgets estén listos
            if (hasattr(self, 'auto_backup_var') and 
                hasattr(self, 'interval_value_entry') and 
                hasattr(self, 'interval_type_combo') and 
                hasattr(self, 'status_label')):
                
                # Verificar que los widgets existan
                if (self.interval_value_entry.winfo_exists() and 
                    self.interval_type_combo.winfo_exists() and 
                    self.status_label.winfo_exists()):
                    
                    if self.auto_backup_var.get():
                        self.logger.info("Iniciando backup automático desde configuración guardada")
                        self.toggle_auto_backup()
                    else:
                        self._safe_update_status("🔴 ⏹️ Inactivo")
                else:
                    # Si los widgets no están listos, intentar más tarde
                    self.logger.debug("Widgets de backup no están listos, reintentando en 2 segundos")
                    try:
                        self.after(2000, self.check_auto_backup)
                    except Exception as e:
                        self.logger.error(f"Error al programar verificación de auto backup: {e}")
            else:
                # Si los atributos no existen, intentar más tarde
                self.logger.debug("Atributos de backup no están listos, reintentando en 2 segundos")
                try:
                    self.after(2000, self.check_auto_backup)
                except Exception as e:
                    self.logger.error(f"Error al programar verificación de auto backup: {e}")
                
        except Exception as e:
            self.logger.error(f"Error al verificar auto backup: {e}")
            self._safe_update_status("⚠️ Error al cargar")
    
    def update_server_selection(self, server_name):
        """Actualizar cuando se cambia el servidor seleccionado"""
        self.server_info_label.configure(text=f"Servidor actual: {server_name}")
        
        # Cargar configuración del servidor seleccionado
        if server_name:
            self.on_server_selected(server_name)
    
    def show_message(self, message, msg_type="info"):
        """Mostrar mensaje en el log principal"""
        if hasattr(self.main_window, 'add_log_message'):
            self.main_window.add_log_message(message)
        else:
            self.logger.info(message)
    
    def refresh_servers_list(self):
        """Método mantenido por compatibilidad - ya no es necesario"""
        pass
    
    def on_server_selected(self, server_name):
        """Manejar selección de servidor"""
        if server_name and server_name != "Seleccionar servidor...":
            self.current_server = server_name
            self.load_server_config(server_name)
            self.refresh_backup_history()
            self.logger.info(f"Servidor seleccionado para backup: {server_name}")
        else:
            self.current_server = None
    
    def get_server_config(self, server_name):
        """Obtener configuración específica del servidor"""
        if server_name not in self.server_configs:
            self.server_configs[server_name] = self.default_backup_config.copy()
        return self.server_configs[server_name]
    
    def load_server_config(self, server_name):
        """Cargar configuración específica del servidor"""
        try:
            config = self.get_server_config(server_name)
            
            # Actualizar widgets con configuración del servidor
            if hasattr(self, 'backup_path_entry'):
                old_path = self.backup_path_entry.get()
                self.backup_path_entry.delete(0, "end")
                backup_path = config.get("backup_path", self.get_default_backup_path())
                if not backup_path:
                    backup_path = self.get_default_backup_path()
                self.backup_path_entry.insert(0, backup_path)
                
                # Si la ruta cambió, escanear nueva carpeta
                if old_path != backup_path:
                    self._on_backup_path_changed(backup_path)
            
            if hasattr(self, 'auto_backup_var'):
                self.auto_backup_var.set(config.get("auto_backup", False))
            
            if hasattr(self, 'interval_value_entry'):
                self.interval_value_entry.delete(0, "end")
                self.interval_value_entry.insert(0, str(config.get("interval_value", 6)))
            
            if hasattr(self, 'interval_type_combo'):
                self.interval_type_combo.set(config.get("interval_type", "horas"))
            
            if hasattr(self, 'compress_var'):
                self.compress_var.set(config.get("compress", True))
            
            if hasattr(self, 'include_saves_var'):
                self.include_saves_var.set(config.get("include_saves", True))
            
            if hasattr(self, 'include_configs_var'):
                self.include_configs_var.set(config.get("include_configs", True))
            
            if hasattr(self, 'include_logs_var'):
                self.include_logs_var.set(config.get("include_logs", False))
            
            if hasattr(self, 'name_format_entry'):
                self.name_format_entry.delete(0, "end")
                self.name_format_entry.insert(0, config.get("backup_name_format", "{server}_{date}_{time}"))
            
            if hasattr(self, 'max_backups_entry'):
                self.max_backups_entry.delete(0, "end")
                self.max_backups_entry.insert(0, str(config.get("max_backups", 10)))
            
            if hasattr(self, 'backup_before_start_var'):
                self.backup_before_start_var.set(config.get("backup_before_start", False))
            
            if hasattr(self, 'verify_backup_var'):
                self.verify_backup_var.set(config.get("verify_backup", True))
            
            if hasattr(self, 'saveworld_before_backup_var'):
                self.saveworld_before_backup_var.set(config.get("saveworld_before_backup", True))
                
        except Exception as e:
            self.logger.error(f"Error al cargar configuración del servidor {server_name}: {e}")
    
    def save_server_config(self, server_name=None):
        """Guardar configuración específica del servidor"""
        if not server_name:
            server_name = self.current_server
        
        if not server_name:
            return
        
        try:
            config = {
                "backup_path": getattr(self, 'backup_path_entry', None) and self.backup_path_entry.get() or self.get_default_backup_path(),
                "auto_backup": getattr(self, 'auto_backup_var', None) and self.auto_backup_var.get() or False,
                "interval_type": getattr(self, 'interval_type_combo', None) and self.interval_type_combo.get() or "horas",
                "interval_value": int(getattr(self, 'interval_value_entry', None) and self.interval_value_entry.get() or "6"),
                "compress": getattr(self, 'compress_var', None) and self.compress_var.get() or True,
                "include_saves": getattr(self, 'include_saves_var', None) and self.include_saves_var.get() or True,
                "include_configs": getattr(self, 'include_configs_var', None) and self.include_configs_var.get() or True,
                "include_logs": getattr(self, 'include_logs_var', None) and self.include_logs_var.get() or False,
                "backup_name_format": getattr(self, 'name_format_entry', None) and self.name_format_entry.get() or "{server}_{date}_{time}",
                "max_backups": int(getattr(self, 'max_backups_entry', None) and self.max_backups_entry.get() or "10"),
                "backup_before_start": getattr(self, 'backup_before_start_var', None) and self.backup_before_start_var.get() or False,
                "verify_backup": getattr(self, 'verify_backup_var', None) and self.verify_backup_var.get() or True,
                "saveworld_before_backup": getattr(self, 'saveworld_before_backup_var', None) and self.saveworld_before_backup_var.get() or True
            }
            
            self.server_configs[server_name] = config
            self.save_all_server_configs()
            
        except Exception as e:
            self.logger.error(f"Error al guardar configuración del servidor {server_name}: {e}")
    
    def load_all_server_configs(self):
        """Cargar todas las configuraciones de servidores"""
        try:
            config_file = "data/backup_server_configs.json"
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
            # Usar método centralizado para obtener ruta de datos
            config_file = self.config_manager.get_data_file_path("backup_server_configs.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.server_configs, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error al guardar configuraciones de servidores: {e}")
