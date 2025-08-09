"""
Diálogo de configuraciones avanzadas de la aplicación
"""

import customtkinter as ctk
import tkinter.filedialog as fd
from tkinter import ttk
from pathlib import Path
from .custom_dialogs import show_info, show_warning, show_error, ask_yes_no


class AdvancedSettingsDialog:
    """Diálogo para configuraciones avanzadas de la aplicación"""
    
    def __init__(self, parent, app_settings, logger):
        self.parent = parent
        self.app_settings = app_settings
        self.logger = logger
        self.dialog = None
        self.changes_made = False
        self._theme_change_in_progress = False
        
    def show(self):
        """Mostrar el diálogo de configuraciones"""
        if self.dialog is not None:
            self.dialog.lift()
            return
            
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("⚙️ Configuraciones Avanzadas - Ark Server Manager")
        self.dialog.geometry("800x600")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Configurar icono
        try:
            icon_path = Path(__file__).parent.parent.parent / "ico" / "ArkManager.ico"
            if icon_path.exists():
                self.dialog.wm_iconbitmap(str(icon_path))
        except Exception:
            pass  # Ignorar errores de icono en diálogos
        
        # Centrar en pantalla
        self.dialog.geometry("+300+150")
        
        # Configurar el grid
        self.dialog.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(0, weight=1)
        
        # Crear notebook para categorías
        self.notebook = ctk.CTkTabview(self.dialog)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Crear pestañas
        self.create_startup_tab()
        self.create_behavior_tab()
        self.create_interface_tab()
        self.create_advanced_tab()
        
        # Frame de botones
        buttons_frame = ctk.CTkFrame(self.dialog)
        buttons_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        # Botones
        ctk.CTkButton(
            buttons_frame,
            text="💾 Guardar",
            command=self.save_settings,
            width=120
        ).grid(row=0, column=0, padx=(10, 5), pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text="🔄 Restablecer",
            command=self.reset_settings,
            width=120
        ).grid(row=0, column=2, padx=5, pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text="📤 Exportar",
            command=self.export_settings,
            width=120
        ).grid(row=0, column=3, padx=5, pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text="📥 Importar",
            command=self.import_settings,
            width=120
        ).grid(row=0, column=4, padx=5, pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text="❌ Cancelar",
            command=self.close_dialog,
            width=120
        ).grid(row=0, column=5, padx=(5, 10), pady=10)
        
        # Manejar cierre de ventana
        self.dialog.protocol("WM_DELETE_WINDOW", self.close_dialog)
        
    def create_startup_tab(self):
        """Crear pestaña de configuraciones de inicio"""
        tab = self.notebook.add("🚀 Inicio")
        
        # Frame principal con scroll
        main_frame = ctk.CTkScrollableFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        ctk.CTkLabel(
            main_frame,
            text="Configuraciones de Inicio del Sistema",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 20))
        
        # Inicio con Windows
        startup_frame = ctk.CTkFrame(main_frame)
        startup_frame.pack(fill="x", pady=5)
        
        self.startup_var = ctk.BooleanVar(value=self.app_settings.get_setting("startup_with_windows"))
        startup_switch = ctk.CTkSwitch(
            startup_frame,
            text="🖥️ Iniciar con Windows",
            variable=self.startup_var,
            command=self.on_startup_toggle
        )
        startup_switch.pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            startup_frame,
            text="Inicia la aplicación automáticamente cuando Windows se inicie",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
        # Auto-start servidor
        autostart_frame = ctk.CTkFrame(main_frame)
        autostart_frame.pack(fill="x", pady=5)
        
        self.autostart_var = ctk.BooleanVar(value=self.app_settings.get_setting("auto_start_server"))
        ctk.CTkSwitch(
            autostart_frame,
            text="🎮 Auto-iniciar servidor",
            variable=self.autostart_var
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            autostart_frame,
            text="Inicia automáticamente el último servidor usado al abrir la app",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
        # Minimizar al iniciar
        minimize_frame = ctk.CTkFrame(main_frame)
        minimize_frame.pack(fill="x", pady=5)
        
        self.start_minimized_var = ctk.BooleanVar(value=self.app_settings.get_setting("start_minimized"))
        ctk.CTkSwitch(
            minimize_frame,
            text="📦 Iniciar minimizado",
            variable=self.start_minimized_var
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            minimize_frame,
            text="Inicia la aplicación minimizada en la bandeja del sistema",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
        # Auto backup al iniciar
        backup_frame = ctk.CTkFrame(main_frame)
        backup_frame.pack(fill="x", pady=5)
        
        self.auto_backup_var = ctk.BooleanVar(value=self.app_settings.get_setting("auto_backup_on_start"))
        ctk.CTkSwitch(
            backup_frame,
            text="💾 Auto-backup al iniciar",
            variable=self.auto_backup_var
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            backup_frame,
            text="Realiza un backup automático al iniciar la aplicación",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
    def create_behavior_tab(self):
        """Crear pestaña de comportamiento"""
        tab = self.notebook.add("🎯 Comportamiento")
        
        main_frame = ctk.CTkScrollableFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        ctk.CTkLabel(
            main_frame,
            text="Comportamiento de la Aplicación",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 20))
        
        # Minimizar a bandeja
        tray_frame = ctk.CTkFrame(main_frame)
        tray_frame.pack(fill="x", pady=5)
        
        self.minimize_tray_var = ctk.BooleanVar(value=self.app_settings.get_setting("minimize_to_tray"))
        ctk.CTkSwitch(
            tray_frame,
            text="📮 Minimizar a bandeja",
            variable=self.minimize_tray_var
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            tray_frame,
            text="Minimiza a la bandeja del sistema en lugar de la barra de tareas",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
        # Cerrar a bandeja
        close_tray_frame = ctk.CTkFrame(main_frame)
        close_tray_frame.pack(fill="x", pady=5)
        
        self.close_tray_var = ctk.BooleanVar(value=self.app_settings.get_setting("close_to_tray"))
        ctk.CTkSwitch(
            close_tray_frame,
            text="🔒 Cerrar a bandeja",
            variable=self.close_tray_var
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            close_tray_frame,
            text="Al cerrar la ventana, mantiene la app ejecutándose en la bandeja",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
        # Confirmar salida
        confirm_frame = ctk.CTkFrame(main_frame)
        confirm_frame.pack(fill="x", pady=5)
        
        self.confirm_exit_var = ctk.BooleanVar(value=self.app_settings.get_setting("confirm_exit"))
        ctk.CTkSwitch(
            confirm_frame,
            text="⚠️ Confirmar salida",
            variable=self.confirm_exit_var
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            confirm_frame,
            text="Pide confirmación antes de cerrar la aplicación",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
        # Auto-check updates
        updates_frame = ctk.CTkFrame(main_frame)
        updates_frame.pack(fill="x", pady=5)
        
        self.auto_updates_var = ctk.BooleanVar(value=self.app_settings.get_setting("auto_check_updates"))
        ctk.CTkSwitch(
            updates_frame,
            text="🔄 Verificar actualizaciones",
            variable=self.auto_updates_var
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            updates_frame,
            text="Verifica automáticamente si hay actualizaciones disponibles",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
        # Auto-save config
        autosave_frame = ctk.CTkFrame(main_frame)
        autosave_frame.pack(fill="x", pady=5)
        
        self.auto_save_var = ctk.BooleanVar(value=self.app_settings.get_setting("auto_save_config"))
        ctk.CTkSwitch(
            autosave_frame,
            text="💾 Auto-guardar configuración",
            variable=self.auto_save_var
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            autosave_frame,
            text="Guarda automáticamente los cambios de configuración",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
    def create_interface_tab(self):
        """Crear pestaña de interfaz"""
        tab = self.notebook.add("🎨 Interfaz")
        
        main_frame = ctk.CTkScrollableFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        ctk.CTkLabel(
            main_frame,
            text="Configuraciones de Interfaz",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 20))
        
        # Siempre visible
        ontop_frame = ctk.CTkFrame(main_frame)
        ontop_frame.pack(fill="x", pady=5)
        
        self.always_ontop_var = ctk.BooleanVar(value=self.app_settings.get_setting("always_on_top"))
        ctk.CTkSwitch(
            ontop_frame,
            text="📌 Siempre visible",
            variable=self.always_ontop_var,
            command=self.on_always_on_top_toggle
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            ontop_frame,
            text="Mantiene la ventana siempre por encima de otras aplicaciones",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
        # Recordar posición
        position_frame = ctk.CTkFrame(main_frame)
        position_frame.pack(fill="x", pady=5)
        
        self.remember_position_var = ctk.BooleanVar(value=self.app_settings.get_setting("remember_window_position"))
        ctk.CTkSwitch(
            position_frame,
            text="📍 Recordar posición",
            variable=self.remember_position_var
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            position_frame,
            text="Recuerda la posición y tamaño de la ventana",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
        # Tema
        theme_frame = ctk.CTkFrame(main_frame)
        theme_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(theme_frame, text="🎨 Tema de la aplicación:").pack(side="left", padx=10, pady=10)
        
        self.theme_var = ctk.StringVar(value=self.app_settings.get_setting("theme_mode"))
        self.theme_combo = ctk.CTkComboBox(
            theme_frame,
            values=["light", "dark", "system"],
            variable=self.theme_var,
            command=self.on_theme_change
        )
        self.theme_combo.pack(side="left", padx=10, pady=10)
        
        # Label de estado del tema
        self.theme_status_label = ctk.CTkLabel(
            theme_frame,
            text="",
            text_color="gray"
        )
        self.theme_status_label.pack(side="left", padx=(10, 0), pady=10)
        
        # Sonidos de notificación
        sound_frame = ctk.CTkFrame(main_frame)
        sound_frame.pack(fill="x", pady=5)
        
        self.notification_sound_var = ctk.BooleanVar(value=self.app_settings.get_setting("notification_sound"))
        ctk.CTkSwitch(
            sound_frame,
            text="🔊 Sonidos de notificación",
            variable=self.notification_sound_var
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            sound_frame,
            text="Reproduce sonidos para notificaciones importantes",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
    def create_advanced_tab(self):
        """Crear pestaña de configuraciones avanzadas"""
        tab = self.notebook.add("🔧 Avanzado")
        
        main_frame = ctk.CTkScrollableFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        ctk.CTkLabel(
            main_frame,
            text="Configuraciones Avanzadas",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 20))
        
        # Ocultar consola
        console_frame = ctk.CTkFrame(main_frame)
        console_frame.pack(fill="x", pady=5)
        
        self.hide_console_var = ctk.BooleanVar(value=self.app_settings.get_setting("hide_console"))
        ctk.CTkSwitch(
            console_frame,
            text="🖥️ Ocultar consola",
            variable=self.hide_console_var
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            console_frame,
            text="Oculta la ventana de consola en modo debug",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
        # Información del sistema
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text="📊 Información del Sistema",
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        # Mostrar info
        import platform
        import psutil
        
        info_text = f"""
🖥️ Sistema: {platform.system()} {platform.release()}
🏗️ Arquitectura: {platform.architecture()[0]}
💾 RAM Total: {round(psutil.virtual_memory().total / (1024**3), 1)} GB
💽 Espacio libre: {round(psutil.disk_usage('.').free / (1024**3), 1)} GB
🐍 Python: {platform.python_version()}
        """.strip()
        
        ctk.CTkTextbox(
            info_frame,
            height=150,
            width=400
        ).pack(pady=10, padx=10, fill="x")
        
        # Insertar texto de información
        info_textbox = ctk.CTkTextbox(info_frame, height=150)
        info_textbox.pack(pady=10, padx=10, fill="x")
        info_textbox.insert("1.0", info_text)
        info_textbox.configure(state="disabled")
        
    def on_startup_toggle(self):
        """Manejar toggle de inicio con Windows"""
        enabled = self.startup_var.get()
        success = self.app_settings.set_startup_with_windows(enabled)
        if not success:
            # Revertir el switch si falló
            self.startup_var.set(not enabled)
            show_error(
                self.dialog,
                "Error de Permisos",
                "No se pudo configurar el inicio automático con Windows.\n\n"
                "Posibles soluciones:\n"
                "1. Ejecuta la aplicación como administrador\n"
                "2. Verifica que no hay software de seguridad bloqueando\n"
                "3. El sistema intentó usar un método alternativo (carpeta de inicio)\n\n"
                "Si el problema persiste, configura manualmente el inicio automático."
            )
    
    def on_always_on_top_toggle(self):
        """Manejar toggle de siempre visible"""
        if hasattr(self.parent, 'attributes'):
            self.parent.attributes('-topmost', self.always_ontop_var.get())
    
    def on_theme_change(self, value):
        """Manejar cambio de tema"""
        try:
            # Evitar cambios múltiples simultáneos
            if self._theme_change_in_progress:
                self.logger.warning("Cambio de tema ya en progreso, ignorando...")
                self.theme_status_label.configure(text="⚠️ Cambio en progreso...")
                return
            
            # Mostrar mensaje de confirmación
            self.logger.info(f"Cambiando tema a: {value}")
            
            # Actualizar estado visual
            self.theme_status_label.configure(text="🔄 Cambiando tema...")
            self.theme_combo.configure(state="disabled")
            
            # Marcar cambio en progreso
            self._theme_change_in_progress = True
            
            # Cambiar tema de forma asíncrona para evitar bloqueos
            self.dialog.after(100, lambda: self._apply_theme_change(value))
            self.changes_made = True
            
        except Exception as e:
            self.logger.error(f"Error al preparar cambio de tema: {e}")
            self.theme_status_label.configure(text="❌ Error en cambio")
            self._theme_change_in_progress = False
    
    def _apply_theme_change(self, theme_value):
        """Aplicar cambio de tema de forma segura"""
        try:
            # Deshabilitar temporalmente la interfaz
            self.dialog.configure(cursor="wait")
            
            # Aplicar el tema con manejo de errores específicos
            self.logger.info(f"Aplicando tema: {theme_value}")
            
            # Intentar cambio de tema con múltiples intentos para compatibilidad
            success = False
            for attempt in range(3):
                try:
                    ctk.set_appearance_mode(theme_value)
                    success = True
                    break
                except Exception as e:
                    self.logger.warning(f"Intento {attempt + 1} de cambio de tema falló: {e}")
                    if attempt < 2:  # No es el último intento
                        # Esperar un poco más antes del siguiente intento
                        import time
                        time.sleep(0.2)
                    continue
            
            if not success:
                raise Exception("No se pudo cambiar el tema después de 3 intentos")
            
            # Forzar actualización de la interfaz
            try:
                self.dialog.update_idletasks()
                if hasattr(self.parent, 'update_idletasks'):
                    self.parent.update_idletasks()
            except Exception as e:
                self.logger.warning(f"Error al actualizar interfaz: {e}")
            
            # Restaurar cursor normal y habilitar cambios futuros
            self.dialog.after(800, lambda: self._finish_theme_change())
            
            self.logger.info(f"Tema cambiado exitosamente a: {theme_value}")
            
        except Exception as e:
            self.logger.error(f"Error crítico al cambiar tema: {e}")
            self.theme_status_label.configure(text=f"❌ Error: {str(e)[:30]}...")
            # Restaurar estado en caso de error
            self._finish_theme_change()
    
    def _finish_theme_change(self):
        """Finalizar el proceso de cambio de tema"""
        try:
            self.dialog.configure(cursor="")
            self.theme_combo.configure(state="normal")
            self.theme_status_label.configure(text="✅ Tema aplicado")
            self._theme_change_in_progress = False
            
            # Limpiar mensaje después de unos segundos
            self.dialog.after(3000, lambda: self.theme_status_label.configure(text=""))
            
        except Exception as e:
            self.logger.error(f"Error al finalizar cambio de tema: {e}")
            self.theme_status_label.configure(text="❌ Error en cambio")
            self.theme_combo.configure(state="normal")
            self._theme_change_in_progress = False
    
    def save_settings(self):
        """Guardar todas las configuraciones"""
        try:
            # Recopilar todos los valores
            settings_to_save = {
                "startup_with_windows": self.startup_var.get(),
                "auto_start_server": self.autostart_var.get(),
                "start_minimized": self.start_minimized_var.get(),
                "auto_backup_on_start": self.auto_backup_var.get(),
                "minimize_to_tray": self.minimize_tray_var.get(),
                "close_to_tray": self.close_tray_var.get(),
                "confirm_exit": self.confirm_exit_var.get(),
                "auto_check_updates": self.auto_updates_var.get(),
                "auto_save_config": self.auto_save_var.get(),
                "always_on_top": self.always_ontop_var.get(),
                "remember_window_position": self.remember_position_var.get(),
                "theme_mode": self.theme_var.get(),
                "notification_sound": self.notification_sound_var.get(),
                "hide_console": self.hide_console_var.get()
            }
            
            # Aplicar configuraciones
            for key, value in settings_to_save.items():
                self.app_settings.set_setting(key, value)
            
            # Guardar al archivo
            self.app_settings.save_settings()
            
            show_info(self.dialog, "Éxito", "Configuraciones guardadas correctamente")
            self.changes_made = False
            self.close_dialog()
            
        except Exception as e:
            self.logger.error(f"Error al guardar configuraciones: {e}")
            show_error(self.dialog, "Error", f"Error al guardar configuraciones: {e}")
    
    def reset_settings(self):
        """Restablecer configuraciones por defecto"""
        if ask_yes_no(
            self.dialog,
            "Confirmar",
            "¿Estás seguro de que quieres restablecer todas las configuraciones a sus valores por defecto?"
        ):
            self.app_settings.reset_to_defaults()
            show_info(self.dialog, "Éxito", "Configuraciones restablecidas. Reinicia la aplicación para aplicar todos los cambios.")
            self.close_dialog()
    
    def export_settings(self):
        """Exportar configuraciones"""
        file_path = fd.asksaveasfilename(
            title="Exportar configuraciones",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            if self.app_settings.export_settings(file_path):
                show_info(self.dialog, "Éxito", "Configuraciones exportadas correctamente")
            else:
                show_error(self.dialog, "Error", "Error al exportar configuraciones")
    
    def import_settings(self):
        """Importar configuraciones"""
        file_path = fd.askopenfilename(
            title="Importar configuraciones",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            if self.app_settings.import_settings(file_path):
                show_info(self.dialog, "Éxito", "Configuraciones importadas correctamente. Reinicia la aplicación para aplicar todos los cambios.")
                self.close_dialog()
            else:
                show_error(self.dialog, "Error", "Error al importar configuraciones")
    
    def close_dialog(self):
        """Cerrar el diálogo"""
        if self.changes_made:
            if ask_yes_no(self.dialog, "Cambios sin guardar", "Hay cambios sin guardar. ¿Quieres cerrar sin guardar?"):
                self.dialog.destroy()
                self.dialog = None
        else:
            self.dialog.destroy()
            self.dialog = None
