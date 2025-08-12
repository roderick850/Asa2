"""
Diálogo de configuraciones avanzadas de la aplicación
"""

import customtkinter as ctk
import tkinter as tk
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
            text="🔍 Verificar",
            command=self.verify_settings_integrity,
            width=120
        ).grid(row=0, column=1, padx=5, pady=10)
        
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
        
        # NO cargar configuraciones automáticamente al abrir
        # self.load_current_settings()
        
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
        
        # Botón de carga manual
        load_button_frame = ctk.CTkFrame(main_frame)
        load_button_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(
            load_button_frame,
            text="📥 Cargar Configuraciones",
            command=self.load_current_settings,
            width=200
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            load_button_frame,
            text="Carga manualmente las configuraciones actuales desde el archivo",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
        # Botón de recarga del archivo config.ini
        reload_config_button_frame = ctk.CTkFrame(main_frame)
        reload_config_button_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(
            reload_config_button_frame,
            text="🔄 Recargar config.ini",
            command=self.reload_config_file,
            width=200
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            reload_config_button_frame,
            text="Recarga el archivo config.ini preservando el formato original",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
        # Inicio con Windows
        startup_frame = ctk.CTkFrame(main_frame)
        startup_frame.pack(fill="x", pady=5)
        
        self.startup_var = ctk.BooleanVar(value=False)  # Valor por defecto, no cargar automáticamente
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
        
        self.autostart_var = ctk.BooleanVar(value=False)  # Valor por defecto, no cargar automáticamente
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
        
        self.autostart_windows_var = ctk.BooleanVar(value=False)  # Valor por defecto, no cargar automáticamente
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
        
        self.start_minimized_var = ctk.BooleanVar(value=False)  # Valor por defecto, no cargar automáticamente
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
        
        self.auto_backup_var = ctk.BooleanVar(value=False)  # Valor por defecto, no cargar automáticamente
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
        
        self.minimize_tray_var = ctk.BooleanVar(value=False)  # Valor por defecto, no cargar automáticamente
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
        
        self.close_tray_var = ctk.BooleanVar(value=False)  # Valor por defecto, no cargar automáticamente
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
        
        self.auto_updates_var = ctk.BooleanVar(value=False)  # Valor por defecto, no cargar automáticamente
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
        
        self.auto_save_var = ctk.BooleanVar(value=False)  # Valor por defecto, no cargar automáticamente
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
        
        self.always_ontop_var = ctk.BooleanVar(value=False)  # Valor por defecto, no cargar automáticamente
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
        
        self.remember_position_var = ctk.BooleanVar(value=False)  # Valor por defecto, no cargar automáticamente
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
        
        self.theme_var = ctk.StringVar(value="dark")  # Valor por defecto, no cargar automáticamente
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
        
        self.notification_sound_var = ctk.BooleanVar(value=False)  # Valor por defecto, no cargar automáticamente
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
        
        # Descripción
        ctk.CTkLabel(
            main_frame,
            text="Esta pestaña permite configurar parámetros avanzados del servidor y la aplicación.",
            text_color="gray",
            wraplength=400
        ).pack(pady=(0, 30))
        
        # Botón para cargar formulario dinámico
        load_form_button_frame = ctk.CTkFrame(main_frame)
        load_form_button_frame.pack(fill="x", pady=(0, 20))
        
        self.load_advanced_form_button = ctk.CTkButton(
            load_form_button_frame,
            text="📥 Cargar Formulario Avanzado",
            command=self.load_advanced_form,
            width=250,
            height=40
        )
        self.load_advanced_form_button.pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            load_form_button_frame,
            text="Carga dinámicamente todas las configuraciones INI disponibles",
            text_color="gray"
        ).pack(side="left", padx=(10, 0), pady=10)
        
        # Frame para el formulario dinámico (inicialmente vacío)
        self.advanced_form_frame = ctk.CTkFrame(main_frame)
        # NO se hace pack aquí - solo se muestra cuando se carga el formulario
        
        # Variable para controlar si el formulario está cargado
        self.advanced_form_loaded = False
        
        # Botón para recargar (inicialmente oculto)
        self.reload_advanced_button = ctk.CTkButton(
            main_frame,
            text="🔄 Recargar Formulario",
            command=self.reload_advanced_form,
            width=200,
            height=35
        )
        # NO se hace pack aquí - solo se muestra cuando se carga el formulario
    
    def load_advanced_form(self):
        """Cargar el formulario avanzado dinámicamente"""
        try:
            if self.advanced_form_loaded:
                return  # Ya está cargado
            
            self.logger.info("🔄 Cargando formulario avanzado...")
            
            # Limpiar el frame del formulario
            for widget in self.advanced_form_frame.winfo_children():
                widget.destroy()
            
            # Crear título del formulario
            ctk.CTkLabel(
                self.advanced_form_frame,
                text="📋 Configuraciones INI del Servidor",
            font=("Arial", 14, "bold")
            ).pack(pady=(20, 10))
            
            # Crear formulario dinámico basado en config.ini
            self.create_dynamic_ini_form()
            
            # Mostrar el frame del formulario
            self.advanced_form_frame.pack(fill="both", expand=True, pady=10)
            
            # Ocultar el botón de carga
            self.load_advanced_form_button.pack_forget()
            
            # Mostrar botón de recarga
            self.reload_advanced_button.pack(pady=10)
            
            # Marcar como cargado
            self.advanced_form_loaded = True
            
            self.logger.info("✅ Formulario avanzado cargado exitosamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error cargando formulario avanzado: {e}")
            show_error(self.dialog, "Error", f"Error al cargar el formulario avanzado:\n{e}")
    
    def reload_advanced_form(self):
        """Recargar el formulario avanzado"""
        try:
            self.logger.info("🔄 Recargando formulario avanzado...")
            
            # Ocultar el formulario actual
            self.advanced_form_frame.pack_forget()
            self.reload_advanced_button.pack_forget()
            
            # Resetear estado
            self.advanced_form_loaded = False
            
            # Mostrar botón de carga nuevamente
            self.load_advanced_form_button.pack(side="left", padx=10, pady=10)
            
            self.logger.info("✅ Formulario avanzado recargado")
            
        except Exception as e:
            self.logger.error(f"❌ Error recargando formulario avanzado: {e}")
            show_error(self.dialog, "Error", f"Error al recargar el formulario avanzado:\n{e}")
    
    def create_dynamic_ini_form(self):
        """Crear formulario dinámico basado en config.ini preservando formato original"""
        try:
            # Inicializar diccionario para almacenar las variables de los campos
            self.advanced_form_vars = {}
            
            # Obtener la ruta del archivo config.ini
            config_file = self.app_settings.config_manager.config_file
            
            self.logger.info(f"🔄 Creando formulario dinámico desde: {config_file}")
            
            # Leer el archivo original línea por línea para preservar formato
            with open(config_file, 'r', encoding='utf-8') as f:
                original_lines = f.readlines()
            
            # Parsear manualmente para preservar claves originales
            sections_data = {}
            current_section = None
            
            for line in original_lines:
                stripped_line = line.strip()
                
                # Líneas de sección
                if stripped_line.startswith('[') and stripped_line.endswith(']'):
                    current_section = stripped_line[1:-1]
                    if current_section not in sections_data:
                        sections_data[current_section] = {}
                    continue
                
                # Líneas vacías o comentarios
                if not stripped_line or stripped_line.startswith(';') or stripped_line.startswith('#'):
                    continue
                
                # Líneas con parámetros key=value
                if '=' in stripped_line and current_section:
                    key_part, value_part = stripped_line.split('=', 1)
                    original_key = key_part.strip()
                    original_value = value_part.strip()
                    
                    # Preservar la clave exactamente como está en el archivo
                    sections_data[current_section][original_key] = original_value
            
            self.logger.info(f"✅ Archivo parseado manualmente. Secciones encontradas: {list(sections_data.keys())}")
            
            # Crear pestañas para cada sección
            notebook = ctk.CTkTabview(self.advanced_form_frame)
            notebook.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Crear pestaña para cada sección
            for section, section_data in sections_data.items():
                if not section_data:  # Saltar secciones vacías
                    continue
                    
                tab = notebook.add(section.title())
                
                # Frame con scroll para la pestaña
                tab_frame = ctk.CTkScrollableFrame(tab)
                tab_frame.pack(fill="both", expand=True, padx=10, pady=10)
                
                # Título de la sección
                ctk.CTkLabel(
                    tab_frame,
                    text=f"Configuración de {section.title()}",
                    font=("Arial", 12, "bold")
                ).pack(pady=(0, 20))
                
                # Crear campos para cada opción preservando claves originales
                for key, value in section_data.items():
                    self.create_form_field(tab_frame, section, key, value)
            
            # Botón para guardar cambios
            save_frame = ctk.CTkFrame(self.advanced_form_frame)
            save_frame.pack(fill="x", pady=20)
            
            ctk.CTkButton(
                save_frame,
                text="💾 Guardar Cambios",
                command=self.save_advanced_form,
                width=200,
                height=35
            ).pack(side="left", padx=10, pady=10)
            
            ctk.CTkLabel(
                save_frame,
                text="Guarda todos los cambios realizados en el formulario",
                text_color="gray"
            ).pack(side="left", padx=(10, 0), pady=10)
            
        except Exception as e:
            self.logger.error(f"❌ Error creando formulario dinámico: {e}")
            show_error(self.dialog, "Error", f"Error al crear el formulario dinámico:\n{e}")
    
    def create_form_field(self, parent, section, key, value):
        """Crear un campo de formulario individual"""
        try:
            # Frame para el campo
            field_frame = ctk.CTkFrame(parent)
            field_frame.pack(fill="x", pady=5)
            
            # Label del campo
            ctk.CTkLabel(
                field_frame,
                text=f"{key}:",
                font=("Arial", 10, "bold")
            ).pack(side="left", padx=10, pady=10)
            
            # Determinar el tipo de campo basado en el valor
            field_type = self.determine_field_type(value)
            
            # Crear el widget apropiado
            if field_type == "boolean":
                var = ctk.BooleanVar(value=self.parse_boolean(value))
                widget = ctk.CTkSwitch(
                    field_frame,
                    text="",
                    variable=var
                )
            elif field_type == "number":
                var = ctk.StringVar(value=str(value))
                widget = ctk.CTkEntry(
                    field_frame,
                    textvariable=var,
                    width=200
                )
            else:
                var = ctk.StringVar(value=str(value))
                widget = ctk.CTkEntry(
                    field_frame,
                    textvariable=var,
                    width=300
                )
            
            widget.pack(side="left", padx=10, pady=10)
            
            # Almacenar la variable para acceso posterior
            field_id = f"{section}.{key}"
            self.advanced_form_vars[field_id] = {
                'var': var,
                'type': field_type,
                'section': section,
                'key': key,
                'original_value': value
            }
            
            # Tooltip con información del campo
            tooltip_text = f"Sección: {section}\nClave: {key}\nValor actual: {value}"
            self.create_tooltip(widget, tooltip_text)
            
        except Exception as e:
            self.logger.error(f"❌ Error creando campo {key}: {e}")
    
    def determine_field_type(self, value):
        """Determinar el tipo de campo basado en el valor"""
        try:
            # Intentar convertir a boolean
            if str(value).lower() in ['true', 'false', '1', '0', 'yes', 'no']:
                return "boolean"
            
            # Intentar convertir a número
            float(value)
            return "number"
            
        except (ValueError, TypeError):
            pass
        
        return "text"
    
    def parse_boolean(self, value):
        """Parsear valor booleano"""
        if str(value).lower() in ['true', '1', 'yes']:
            return True
        return False
    
    def create_tooltip(self, widget, text):
        """Crear tooltip para un widget"""
        try:
            # Implementación simple de tooltip
            def show_tooltip(event):
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                
                label = tk.Label(tooltip, text=text, justify='left',
                               background='#ffffcc', relief='solid', borderwidth=1,
                               font=('Segoe UI', '9', 'normal'), wraplength=200)
                label.pack(padx=5, pady=5)
                
                def hide_tooltip():
                    tooltip.destroy()
                
                widget.tooltip = tooltip
                widget.bind('<Leave>', lambda e: hide_tooltip())
                tooltip.bind('<Leave>', lambda e: hide_tooltip())
            
            widget.bind('<Enter>', show_tooltip)
            
        except Exception as e:
            self.logger.debug(f"No se pudo crear tooltip: {e}")
    
    def save_advanced_form(self):
        """Guardar los cambios del formulario avanzado preservando formato original"""
        try:
            self.logger.info("💾 Guardando formulario avanzado preservando formato...")
            
            changes_made = False
            changes_to_apply = {}
            
            # Recorrer todas las variables del formulario
            for field_id, field_info in self.advanced_form_vars.items():
                var = field_info['var']
                section = field_info['section']
                key = field_info['key']
                field_type = field_info['type']
                original_value = field_info['original_value']
                
                # Obtener el valor actual
                if field_type == "boolean":
                    current_value = var.get()
                    # Convertir a string para comparar
                    current_value_str = str(current_value)
                else:
                    current_value_str = var.get()
                
                # Verificar si el valor cambió
                if str(original_value) != current_value_str:
                    self.logger.info(f"🔄 Cambiando {section}.{key}: {original_value} → {current_value_str}")
                    
                    # Guardar cambio para aplicar después
                    if section not in changes_to_apply:
                        changes_to_apply[section] = {}
                    changes_to_apply[section][key] = current_value_str
                    changes_made = True
            
            if changes_made:
                # Aplicar cambios preservando formato original
                self.logger.info("💾 Aplicando cambios preservando formato...")
                success = self._save_advanced_form_preserving_format(changes_to_apply)
                
                if success:
                    self.logger.info("✅ Cambios guardados preservando formato")
                    show_info(self.dialog, "Éxito", "Los cambios han sido guardados exitosamente.")
                    
                    # Recargar el formulario para mostrar valores actualizados
                    self._reload_advanced_form()
                else:
                    self.logger.error("❌ Error al guardar preservando formato")
                    show_error(self.dialog, "Error", "Error al guardar los cambios preservando formato.")
            else:
                self.logger.info("ℹ️ No hay cambios para guardar")
                show_info(self.dialog, "Información", "No hay cambios para guardar.")
                
        except Exception as e:
            self.logger.error(f"❌ Error guardando formulario avanzado: {e}")
            show_error(self.dialog, "Error", f"Error al guardar los cambios:\n{e}")
    
    def _save_advanced_form_preserving_format(self, changes_to_apply):
        """Guardar cambios preservando formato original del archivo"""
        try:
            config_file = self.app_settings.config_manager.config_file
            
            # Leer el archivo original línea por línea
            with open(config_file, 'r', encoding='utf-8') as f:
                original_lines = f.readlines()
            
            modified_lines = []
            current_section = None
            
            for line in original_lines:
                original_line = line
                stripped_line = line.strip()
                
                # Líneas de sección
                if stripped_line.startswith('[') and stripped_line.endswith(']'):
                    current_section = stripped_line[1:-1]
                    modified_lines.append(original_line)
                    continue
                
                # Líneas vacías o comentarios
                if not stripped_line or stripped_line.startswith(';') or stripped_line.startswith('#'):
                    modified_lines.append(original_line)
                    continue
                
                # Líneas con parámetros key=value
                if '=' in stripped_line and current_section:
                    key_part, value_part = stripped_line.split('=', 1)
                    original_key = key_part.strip()
                    
                    # Verificar si este campo tiene un valor modificado
                    if (current_section in changes_to_apply and 
                        original_key in changes_to_apply[current_section]):
                        
                        new_value = changes_to_apply[current_section][original_key]
                        
                        # Preservar el formato original (espacios, etc.) solo cambiar el valor
                        prefix = line[:line.find('=') + 1]
                        suffix = '\n' if line.endswith('\n') else ''
                        modified_line = f"{prefix}{new_value}{suffix}"
                        modified_lines.append(modified_line)
                        
                        self.logger.debug(f"Modificado: {original_key} = {new_value}")
                        
                        # Remover este cambio de la lista para no procesarlo de nuevo
                        del changes_to_apply[current_section][original_key]
                    else:
                        # Mantener línea original
                        modified_lines.append(original_line)
                else:
                    # Mantener línea original
                    modified_lines.append(original_line)
            
            # Escribir archivo modificado
            with open(config_file, 'w', encoding='utf-8') as f:
                f.writelines(modified_lines)
                
            self.logger.info(f"✅ Archivo {config_file} guardado preservando formato original")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error preservando formato de {config_file}: {e}")
            return False
    
    def _reload_advanced_form(self):
        """Recargar el formulario avanzado con valores actualizados"""
        try:
            self.logger.info("🔄 Recargando formulario avanzado...")
            
            # Limpiar formulario actual
            for widget in self.advanced_form_frame.winfo_children():
                widget.destroy()
            
            # Limpiar variables
            self.advanced_form_vars.clear()
            
            # Ocultar botón de recarga
            if hasattr(self, 'reload_advanced_button'):
                self.reload_advanced_button.pack_forget()
            
            # Mostrar botón de carga
            if hasattr(self, 'load_advanced_form_button'):
                self.load_advanced_form_button.pack(pady=10)
            
            # Marcar como no cargado
            self.advanced_form_loaded = False
            
            self.logger.info("✅ Formulario avanzado recargado")
            
        except Exception as e:
            self.logger.error(f"❌ Error recargando formulario avanzado: {e}")
        
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
        """Guardar todas las configuraciones con verificación robusta"""
        try:
            self.logger.info("🔄 Iniciando proceso de guardado desde diálogo...")
            
            # Forzar recarga antes de guardar para sincronizar
            self.app_settings.load_settings()
            self.logger.info("✅ Configuraciones recargadas antes de guardar")
            
            # Recopilar todos los valores con verificación
            settings_to_save = {
                "startup_with_windows": self.startup_var.get(),
                "auto_start_server": self.autostart_var.get(),
                "auto_start_server_with_windows": self.autostart_windows_var.get(),
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
            
            self.logger.info(f"📝 Configuraciones recopiladas: {len(settings_to_save)} items")
            
            # Log de configuraciones críticas ANTES de aplicar
            critical_settings = ["auto_start_server", "startup_with_windows", "auto_start_server_with_windows"]
            for key in critical_settings:
                if key in settings_to_save:
                    self.logger.info(f"🔍 ANTES - {key}: {settings_to_save[key]}")
            
            # Aplicar configuraciones una por una con verificación
            successful_sets = 0
            failed_sets = 0
            
            for key, value in settings_to_save.items():
                try:
                    # Verificar valor anterior
                    old_value = self.app_settings.get_setting(key)
                    
                    # Aplicar nuevo valor
                    self.app_settings.set_setting(key, value)
                    
                    # Verificar que se aplicó
                    new_value = self.app_settings.get_setting(key)
                    
                    if new_value == value:
                        successful_sets += 1
                        if key in critical_settings:
                            self.logger.info(f"✅ {key}: {old_value} → {new_value}")
                    else:
                        failed_sets += 1
                        self.logger.error(f"❌ {key}: no se aplicó correctamente (esperado: {value}, actual: {new_value})")
                        
                except Exception as e:
                    failed_sets += 1
                    self.logger.error(f"❌ Error al aplicar {key}: {e}")
            
            self.logger.info(f"📊 Aplicación: {successful_sets} exitosas, {failed_sets} fallidas")
            
            if failed_sets > 0:
                self.logger.warning(f"⚠️ Algunas configuraciones no se aplicaron correctamente")
            
            # Guardar al archivo con verificación
            self.logger.info("💾 Guardando al archivo...")
            self.app_settings.save_settings()
            self.logger.info("✅ save_settings() completado")
            
            # Verificación post-guardado: recargar y verificar
            self.logger.info("🔍 Verificando persistencia...")
            self.app_settings.load_settings()
            
            verification_passed = True
            for key in critical_settings:
                if key in settings_to_save:
                    expected_value = settings_to_save[key]
                    actual_value = self.app_settings.get_setting(key)
                    if expected_value == actual_value:
                        self.logger.info(f"✅ VERIFICADO - {key}: {actual_value}")
                    else:
                        self.logger.error(f"❌ FALLÓ VERIFICACIÓN - {key}: esperado {expected_value}, actual {actual_value}")
                        verification_passed = False
            
            if verification_passed:
                self.logger.info("🎉 TODAS LAS CONFIGURACIONES VERIFICADAS EXITOSAMENTE")
                show_info(self.dialog, "Éxito", "✅ Configuraciones guardadas y verificadas correctamente")
            else:
                self.logger.error("❌ FALLÓ LA VERIFICACIÓN DE ALGUNAS CONFIGURACIONES")
                show_warning(self.dialog, "Advertencia", "⚠️ Configuraciones guardadas, pero algunas pueden no haberse aplicado correctamente. Revisa los logs.")
            
            self.changes_made = False
            
            # NO cerrar automáticamente para que el usuario pueda verificar
            # self.close_dialog()
            
        except Exception as e:
            self.logger.error(f"❌ Error crítico al guardar configuraciones: {e}")
            show_error(self.dialog, "Error", f"❌ Error crítico al guardar configuraciones:\n{e}")
    
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
    
    def reload_config_file(self):
        """Recargar el archivo config.ini desde el disco"""
        try:
            self.logger.info("🔄 Iniciando recarga de config.ini...")
            if hasattr(self.app_settings, 'load_settings'):
                self.app_settings.load_settings()
                self.logger.info("✅ Config.ini recargado con éxito.")
                show_info(self.dialog, "Recarga exitosa", "Archivo config.ini recargado con éxito.")
            else:
                self.logger.warning("⚠️ AppSettings no tiene método load_settings, no se puede recargar el archivo.")
                show_warning(self.dialog, "Advertencia", "No se pudo recargar el archivo config.ini. La aplicación no tiene un método para cargar configuraciones.")
        except Exception as e:
            self.logger.error(f"❌ Error al recargar config.ini: {e}")
            show_error(self.dialog, "Error", f"❌ Error al recargar config.ini:\n{e}")
    
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
                'start_minimized_var': 'start_minimized',
                'minimize_tray_var': 'minimize_to_tray',
                'close_tray_var': 'close_to_tray',
                'always_ontop_var': 'always_on_top',
                'remember_position_var': 'remember_window_position',
                'auto_backup_var': 'auto_backup_on_start',
                'confirm_exit_var': 'confirm_exit',
                'auto_save_var': 'auto_save_config',
                'auto_updates_var': 'auto_check_updates',
                'notification_sound_var': 'notification_sound',
                'theme_var': 'theme_mode'
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

    def verify_settings_integrity(self):
        """Verificar la integridad de las configuraciones"""
        try:
            self.logger.info("🔍 Iniciando verificación de integridad...")
            
            # Recargar configuraciones desde archivo
            self.app_settings.load_settings()
            
            # Verificar que las variables de UI coincidan con app_settings
            critical_mappings = {
                'startup_var': 'startup_with_windows',
                'autostart_var': 'auto_start_server',
                'autostart_windows_var': 'auto_start_server_with_windows'
            }
            
            integrity_ok = True
            
            for var_name, setting_key in critical_mappings.items():
                if hasattr(self, var_name):
                    var_obj = getattr(self, var_name)
                    ui_value = var_obj.get()
                    settings_value = self.app_settings.get_setting(setting_key)
                    
                    if ui_value == settings_value:
                        self.logger.info(f"✅ {setting_key}: UI={ui_value}, Settings={settings_value}")
                    else:
                        self.logger.warning(f"⚠️ {setting_key}: DESINCRONIZADO - UI={ui_value}, Settings={settings_value}")
                        integrity_ok = False
                        
                        # Sincronizar UI con settings
                        var_obj.set(settings_value)
                        self.logger.info(f"🔄 Sincronizado {setting_key} UI con Settings: {settings_value}")
            
            if integrity_ok:
                self.logger.info("🎉 INTEGRIDAD VERIFICADA: UI y Settings sincronizados")
            else:
                self.logger.warning("⚠️ INTEGRIDAD RESTAURADA: Se aplicaron correcciones")
            
            return integrity_ok
            
        except Exception as e:
            self.logger.error(f"❌ Error en verificación de integridad: {e}")
            return False

    def close_dialog(self):
        """Cerrar el diálogo"""
        if self.changes_made:
            if ask_yes_no(self.dialog, "Cambios sin guardar", "Hay cambios sin guardar. ¿Quieres cerrar sin guardar?"):
                self.dialog.destroy()
                self.dialog = None
        else:
            self.dialog.destroy()
            self.dialog = None
