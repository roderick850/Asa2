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
        
        # Cargar configuraciones actuales para asegurar sincronización
        self.load_current_settings()
        
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
        
        # Auto-start servidor (manual)
        autostart_frame = ctk.CTkFrame(main_frame)
        autostart_frame.pack(fill="x", pady=5)
        
        self.autostart_var = ctk.BooleanVar(value=self.app_settings.get_setting("auto_start_server"))
        ctk.CTkSwitch(
            autostart_frame,
            text="🎮 Auto-iniciar servidor (Manual)",
            variable=self.autostart_var
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            autostart_frame,
            text="Inicia automáticamente el servidor al abrir la aplicación manualmente",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
        # Auto-start servidor (con Windows)
        autostart_windows_frame = ctk.CTkFrame(main_frame)
        autostart_windows_frame.pack(fill="x", pady=5)
        
        self.autostart_windows_var = ctk.BooleanVar(value=self.app_settings.get_setting("auto_start_server_with_windows"))
        ctk.CTkSwitch(
            autostart_windows_frame,
            text="🖥️ Auto-iniciar servidor (Con Windows)",
            variable=self.autostart_windows_var
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            autostart_windows_frame,
            text="Inicia automáticamente el servidor cuando la aplicación arranca con Windows",
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
            
            # Intentar cambio de tema con threading para evitar congelamiento
            success = False
            
            # Usar threading para prevenir congelamiento en equipos problemáticos
            import threading
            import time
            
            def change_theme_thread():
                nonlocal success
                try:
                    ctk.set_appearance_mode(theme_value)
                    success = True
                except Exception as e:
                    self.logger.warning(f"Error en hilo de cambio de tema: {e}")
                    success = False
            
            # Ejecutar cambio en hilo separado con timeout
            theme_thread = threading.Thread(target=change_theme_thread, daemon=True)
            theme_thread.start()
            theme_thread.join(timeout=3.0)  # Timeout de 3 segundos
            
            # Si el hilo aún está vivo, significa que se colgó
            if theme_thread.is_alive():
                self.logger.warning("Cambio de tema se colgó, intentando método alternativo...")
                success = False
                
                # Intentar método directo como fallback
                try:
                    ctk.set_appearance_mode(theme_value)
                    success = True
                    self.logger.info("Método alternativo exitoso")
                except Exception as e:
                    self.logger.error(f"Método alternativo también falló: {e}")
            
            if not success:
                raise Exception("No se pudo cambiar el tema - posible incompatibilidad de sistema")
            
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
            # Restaurar cursor de forma defensiva
            try:
                self.dialog.configure(cursor="")
            except:
                pass
            
            # Habilitar combo de forma defensiva
            try:
                self.theme_combo.configure(state="normal")
            except:
                pass
            
            # Actualizar label de forma defensiva
            try:
                self.theme_status_label.configure(text="✅ Tema aplicado")
            except:
                pass
            
            # Siempre resetear el flag de progreso
            self._theme_change_in_progress = False
            
            # Limpiar mensaje después de unos segundos
            try:
                self.dialog.after(3000, lambda: self._clear_theme_status())
            except:
                pass
            
        except Exception as e:
            self.logger.error(f"Error al finalizar cambio de tema: {e}")
            # Asegurar que siempre se resetee el estado
            self._theme_change_in_progress = False
            try:
                self.theme_status_label.configure(text="❌ Error en cambio")
                self.theme_combo.configure(state="normal")
            except:
                pass
    
    def _clear_theme_status(self):
        """Limpiar el estado del tema de forma segura"""
        try:
            if hasattr(self, 'theme_status_label'):
                self.theme_status_label.configure(text="")
        except:
            pass
    
    def save_settings(self):
        """Guardar todas las configuraciones"""
        try:
            # Recopilar todos los valores
            settings_to_save = {
                "startup_with_windows": self.startup_var.get(),
                "auto_start_server": self.autostart_var.get(),
                "auto_start_server_with_windows": self.autostart_windows_var.get(),  # ✅ AGREGADO
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
                # Log específico para configuraciones críticas
                if key in ['auto_start_server', 'auto_start_server_with_windows']:
                    self.logger.info(f"💾 Guardando {key}: {value}")
            
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
    
    def save_settings(self):
        """Guardar todas las configuraciones"""
        try:
            # Configuraciones de inicio
            if hasattr(self, 'startup_var'):
                self.app_settings.set_setting("startup_with_windows", self.startup_var.get())
            
            if hasattr(self, 'autostart_var'):
                self.app_settings.set_setting("auto_start_server", self.autostart_var.get())
                
            if hasattr(self, 'autostart_windows_var'):
                self.app_settings.set_setting("auto_start_server_with_windows", self.autostart_windows_var.get())
                
            if hasattr(self, 'minimize_start_var'):
                self.app_settings.set_setting("start_minimized", self.minimize_start_var.get())
                
            if hasattr(self, 'minimize_tray_var'):
                self.app_settings.set_setting("minimize_to_tray", self.minimize_tray_var.get())
                
            if hasattr(self, 'close_tray_var'):
                self.app_settings.set_setting("close_to_tray", self.close_tray_var.get())
            
            # Configuraciones de ventana
            if hasattr(self, 'always_top_var'):
                self.app_settings.set_setting("always_on_top", self.always_top_var.get())
                
            if hasattr(self, 'remember_position_var'):
                self.app_settings.set_setting("remember_window_position", self.remember_position_var.get())
            
            # Otras configuraciones
            if hasattr(self, 'auto_backup_var'):
                self.app_settings.set_setting("auto_backup_on_start", self.auto_backup_var.get())
                
            if hasattr(self, 'confirm_exit_var'):
                self.app_settings.set_setting("confirm_exit", self.confirm_exit_var.get())
                
            if hasattr(self, 'hide_console_var'):
                self.app_settings.set_setting("hide_console", self.hide_console_var.get())
                
            if hasattr(self, 'auto_save_var'):
                self.app_settings.set_setting("auto_save_config", self.auto_save_var.get())
                
            if hasattr(self, 'notification_sound_var'):
                self.app_settings.set_setting("notification_sound", self.notification_sound_var.get())
            
            # Guardar configuraciones
            self.app_settings.save_settings()
            self.changes_made = False
            
            show_info(self.dialog, "Configuraciones guardadas", "Todas las configuraciones han sido guardadas correctamente.")
            self.logger.info("Configuraciones avanzadas guardadas")
            
            # Cerrar diálogo
            self.close_dialog()
            
        except Exception as e:
            self.logger.error(f"Error al guardar configuraciones: {e}")
            show_error(self.dialog, "Error", f"Error al guardar configuraciones:\n{e}")
    
    def reset_settings(self):
        """Restablecer configuraciones a valores por defecto"""
        try:
            if ask_yes_no(self.dialog, "Restablecer configuraciones", "¿Estás seguro de que quieres restablecer todas las configuraciones a sus valores por defecto?"):
                # Restablecer a valores por defecto
                self.app_settings.reset_to_defaults()
                
                # Actualizar interfaz
                self.load_current_settings()
                
                show_info(self.dialog, "Configuraciones restablecidas", "Todas las configuraciones han sido restablecidas a sus valores por defecto.")
                self.logger.info("Configuraciones restablecidas a valores por defecto")
                
        except Exception as e:
            self.logger.error(f"Error al restablecer configuraciones: {e}")
            show_error(self.dialog, "Error", f"Error al restablecer configuraciones:\n{e}")
    
    def export_settings(self):
        """Exportar configuraciones a archivo"""
        try:
            from tkinter import filedialog
            import json
            
            file_path = filedialog.asksaveasfilename(
                parent=self.dialog,
                title="Exportar configuraciones",
                defaultextension=".json",
                filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
            )
            
            if file_path:
                settings_data = self.app_settings.get_all_settings()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(settings_data, f, indent=2, ensure_ascii=False)
                
                show_info(self.dialog, "Exportación completada", f"Configuraciones exportadas a:\n{file_path}")
                self.logger.info(f"Configuraciones exportadas a: {file_path}")
                
        except Exception as e:
            self.logger.error(f"Error al exportar configuraciones: {e}")
            show_error(self.dialog, "Error", f"Error al exportar configuraciones:\n{e}")
    
    def import_settings(self):
        """Importar configuraciones desde archivo"""
        try:
            from tkinter import filedialog
            import json
            
            file_path = filedialog.askopenfilename(
                parent=self.dialog,
                title="Importar configuraciones",
                filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                
                # Aplicar configuraciones importadas
                for key, value in settings_data.items():
                    self.app_settings.set_setting(key, value)
                
                # Guardar y actualizar interfaz
                self.app_settings.save_settings()
                self.load_current_settings()
                
                show_info(self.dialog, "Importación completada", f"Configuraciones importadas desde:\n{file_path}")
                self.logger.info(f"Configuraciones importadas desde: {file_path}")
                
        except Exception as e:
            self.logger.error(f"Error al importar configuraciones: {e}")
            show_error(self.dialog, "Error", f"Error al importar configuraciones:\n{e}")
    
    def load_current_settings(self):
        """Cargar configuraciones actuales en la interfaz"""
        try:
            self.logger.info("🔄 Iniciando sincronización de configuraciones...")
            
            # Forzar recarga de configuraciones desde archivo
            if hasattr(self.app_settings, 'load_settings'):
                self.app_settings.load_settings()
                self.logger.info("✅ Configuraciones recargadas desde archivo")
            else:
                self.logger.warning("⚠️ AppSettings no tiene método load_settings")
            
            # Actualizar variables de interfaz con valores actuales
            settings_map = {
                'startup_var': 'startup_with_windows',
                'autostart_var': 'auto_start_server',
                'autostart_windows_var': 'auto_start_server_with_windows',
                'minimize_start_var': 'start_minimized',
                'minimize_tray_var': 'minimize_to_tray',
                'close_tray_var': 'close_to_tray',
                'always_top_var': 'always_on_top',
                'remember_position_var': 'remember_window_position',
                'auto_backup_var': 'auto_backup_on_start',
                'confirm_exit_var': 'confirm_exit',
                'hide_console_var': 'hide_console',
                'auto_save_var': 'auto_save_config',
                'notification_sound_var': 'notification_sound'
            }
            
            successful_updates = 0
            failed_updates = 0
            
            for var_name, setting_key in settings_map.items():
                if hasattr(self, var_name):
                    try:
                        current_value = self.app_settings.get_setting(setting_key)
                        var_obj = getattr(self, var_name)
                        
                        # Verificar que la variable existe y tiene método set
                        if hasattr(var_obj, 'set'):
                            old_value = var_obj.get() if hasattr(var_obj, 'get') else "UNKNOWN"
                            var_obj.set(current_value)
                            successful_updates += 1
                            
                            # Log detallado para configuraciones críticas
                            if setting_key in ['auto_start_server', 'auto_start_server_with_windows', 'startup_with_windows']:
                                self.logger.info(f"🔄 {setting_key}: {old_value} → {current_value}")
                        else:
                            self.logger.error(f"❌ Variable {var_name} no tiene método set()")
                            failed_updates += 1
                            
                    except Exception as e:
                        self.logger.error(f"❌ Error al actualizar {var_name} ({setting_key}): {e}")
                        failed_updates += 1
                else:
                    self.logger.warning(f"⚠️ Variable {var_name} no existe en el diálogo")
                    failed_updates += 1
            
            self.logger.info(f"✅ Sincronización completada: {successful_updates} exitosas, {failed_updates} fallidas")
                
        except Exception as e:
            self.logger.error(f"❌ Error crítico al cargar configuraciones actuales: {e}")
            # Intentar recarga básica como fallback
            try:
                self.logger.info("🔄 Intentando recarga básica...")
                if hasattr(self, 'autostart_windows_var') and hasattr(self.app_settings, 'get_setting'):
                    value = self.app_settings.get_setting('auto_start_server_with_windows')
                    self.autostart_windows_var.set(value)
                    self.logger.info(f"🔄 Recarga básica: auto_start_server_with_windows = {value}")
            except Exception as fallback_error:
                self.logger.error(f"❌ Recarga básica falló: {fallback_error}")

    def close_dialog(self):
        """Cerrar el diálogo"""
        if self.changes_made:
            if ask_yes_no(self.dialog, "Cambios sin guardar", "Hay cambios sin guardar. ¿Quieres cerrar sin guardar?"):
                self.dialog.destroy()
                self.dialog = None
        else:
            self.dialog.destroy()
            self.dialog = None
