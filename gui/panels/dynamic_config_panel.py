import customtkinter as ctk
import configparser
import os
import shutil
from tkinter import filedialog, messagebox
from pathlib import Path
import re

class DynamicConfigPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        
        # Diccionarios para almacenar widgets dinámicos
        self.config_widgets = {}  # {section: {key: widget}}
        self.config_data = {}     # {file_path: configparser_object}
        self.config_files = []    # Lista de archivos de configuración encontrados
        
        # Mapeo de tipos de datos comunes en ARK
        self.type_hints = {
            # Booleanos
            'true': bool, 'false': bool, 'enable': bool, 'disable': bool,
            'allow': bool, 'prevent': bool, 'show': bool, 'hide': bool,
            # Números
            'multiplier': float, 'rate': float, 'factor': float, 'scale': float,
            'amount': float, 'damage': float, 'health': float, 'stamina': float,
            'max': int, 'min': int, 'limit': int, 'count': int, 'level': int,
            'port': int, 'timeout': int, 'interval': int, 'duration': int,
            # Texto
            'name': str, 'password': str, 'message': str, 'motd': str,
            'admin': str, 'server': str, 'map': str, 'mod': str
        }
        
        self.create_widgets()
        self.pack(fill="both", expand=True)
        
        # Agregar contenido de prueba para asegurar que se ve
        self.show_test_content()
        
        # Usar after para ejecutar scan después de que la UI esté lista
        self.after(100, self.scan_for_config_files)
        
    def create_widgets(self):
        """Crear la estructura básica del panel"""
        # Configurar grid principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Título
        title_label = ctk.CTkLabel(
            self, 
            text="🎮 Configuración Dinámica de ARK", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(10, 5), sticky="ew")
        
        # Frame de control superior
        control_frame = ctk.CTkFrame(self)
        control_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        control_frame.grid_columnconfigure(1, weight=1)
        
        # Botón para buscar archivos de configuración
        scan_button = ctk.CTkButton(
            control_frame,
            text="🔍 Buscar Configs",
            command=self.scan_for_config_files,
            width=120
        )
        scan_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Label de estado
        self.status_label = ctk.CTkLabel(
            control_frame,
            text="Buscando archivos de configuración...",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Botones de acción
        action_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        action_frame.grid(row=0, column=2, padx=5, pady=5)
        
        save_button = ctk.CTkButton(
            action_frame,
            text="💾 Guardar Todo",
            command=self.save_all_configs,
            fg_color="green",
            hover_color="darkgreen",
            width=100
        )
        save_button.pack(side="left", padx=2)
        
        reload_button = ctk.CTkButton(
            action_frame,
            text="🔄 Recargar",
            command=self.reload_all_configs,
            width=100
        )
        reload_button.pack(side="left", padx=2)
        
        # Frame principal con scroll para las configuraciones
        self.main_scroll = ctk.CTkScrollableFrame(self)
        self.main_scroll.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.main_scroll.grid_columnconfigure(0, weight=1)
    
    def show_test_content(self):
        """Mostrar contenido de prueba para verificar que el panel funciona"""
        test_frame = ctk.CTkFrame(self.main_scroll)
        test_frame.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
        test_frame.grid_columnconfigure(0, weight=1)
        
        test_label = ctk.CTkLabel(
            test_frame,
            text="🎮 Panel de Configuración Dinámica\n\nBuscando archivos de configuración...",
            font=ctk.CTkFont(size=14)
        )
        test_label.grid(row=0, column=0, pady=20)
        
    def scan_for_config_files(self):
        """Buscar archivos de configuración de ARK en las rutas del servidor"""
        try:
            # Limpiar contenido de prueba
            for widget in self.main_scroll.winfo_children():
                widget.destroy()
                
            self.status_label.configure(text="🔍 Buscando archivos de configuración...")
            self.config_files = []
            
            # Obtener ruta raíz del servidor
            root_path = self.config_manager.get("server", "root_path", "")
            if not root_path:
                self.status_label.configure(text="⚠️ Ruta raíz no configurada")
                self.show_manual_selection_option()
                return
                
            if not os.path.exists(root_path):
                self.status_label.configure(text=f"❌ Ruta no existe: {root_path}")
                self.show_manual_selection_option()
                return
            
            self.logger.info(f"Buscando configs en: {root_path}")
            
            # Buscar archivos de configuración comunes de ARK
            config_patterns = [
                "**/GameUserSettings.ini",
                "**/Game.ini", 
                "**/Engine.ini",
                "**/ServerSettings.ini"
            ]
            
            found_files = []
            root_pathlib = Path(root_path)
            
            for pattern in config_patterns:
                try:
                    for file_path in root_pathlib.glob(pattern):
                        if file_path.is_file():
                            found_files.append(str(file_path))
                            self.logger.info(f"Encontrado archivo config: {file_path}")
                except Exception as e:
                    self.logger.warning(f"Error al buscar patrón {pattern}: {e}")
            
            self.config_files = found_files
            
            if self.config_files:
                self.status_label.configure(
                    text=f"✅ Encontrados {len(self.config_files)} archivos de configuración"
                )
                self.load_all_configs()
            else:
                self.status_label.configure(text="⚠️ No se encontraron archivos de configuración")
                self.show_manual_selection_option()
                
        except Exception as e:
            self.logger.error(f"Error al buscar archivos de configuración: {e}")
            self.status_label.configure(text=f"❌ Error al buscar configs: {str(e)}")
            self.show_manual_selection_option()
    
    def show_manual_selection_option(self):
        """Mostrar opción para seleccionar archivos manualmente"""
        manual_frame = ctk.CTkFrame(self.main_scroll)
        manual_frame.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
        manual_frame.grid_columnconfigure(0, weight=1)
        
        info_label = ctk.CTkLabel(
            manual_frame,
            text="No se encontraron archivos de configuración automáticamente.\n"
                 "Puedes seleccionarlos manualmente:",
            font=ctk.CTkFont(size=12)
        )
        info_label.grid(row=0, column=0, pady=10)
        
        select_button = ctk.CTkButton(
            manual_frame,
            text="📂 Seleccionar Archivos de Configuración",
            command=self.select_config_files_manually,
            width=250
        )
        select_button.grid(row=1, column=0, pady=5)
    
    def select_config_files_manually(self):
        """Permitir al usuario seleccionar archivos de configuración manualmente"""
        file_paths = filedialog.askopenfilenames(
            title="Seleccionar archivos de configuración de ARK",
            filetypes=[
                ("Archivos INI", "*.ini"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if file_paths:
            self.config_files = list(file_paths)
            self.status_label.configure(
                text=f"✅ Seleccionados {len(self.config_files)} archivos manualmente"
            )
            self.load_all_configs()
    
    def load_all_configs(self):
        """Cargar todos los archivos de configuración encontrados"""
        try:
            # Limpiar contenido anterior
            for widget in self.main_scroll.winfo_children():
                widget.destroy()
            
            self.config_data = {}
            self.config_widgets = {}
            
            row_index = 0
            
            for config_file in self.config_files:
                if not os.path.exists(config_file):
                    continue
                    
                # Crear frame para este archivo
                file_frame = self.create_file_frame(config_file, row_index)
                row_index += 1
                
                # Cargar y parsear el archivo
                self.load_single_config(config_file, file_frame)
                
        except Exception as e:
            self.logger.error(f"Error al cargar configuraciones: {e}")
            self.status_label.configure(text=f"❌ Error al cargar configs: {str(e)}")
    
    def create_file_frame(self, config_file, row_index):
        """Crear frame para un archivo de configuración específico"""
        file_name = os.path.basename(config_file)
        
        # Frame principal del archivo
        file_frame = ctk.CTkFrame(self.main_scroll)
        file_frame.grid(row=row_index, column=0, padx=5, pady=5, sticky="ew")
        file_frame.grid_columnconfigure(0, weight=1)
        
        # Header del archivo
        header_frame = ctk.CTkFrame(file_frame, fg_color=("gray80", "gray30"))
        header_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Icono y nombre del archivo
        icon_label = ctk.CTkLabel(header_frame, text="📄", font=ctk.CTkFont(size=16))
        icon_label.grid(row=0, column=0, padx=5, pady=5)
        
        name_label = ctk.CTkLabel(
            header_frame, 
            text=file_name,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        name_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Ruta del archivo (más pequeña)
        path_label = ctk.CTkLabel(
            header_frame,
            text=config_file,
            font=ctk.CTkFont(size=9),
            text_color="gray"
        )
        path_label.grid(row=1, column=1, padx=5, pady=(0, 5), sticky="w")
        
        # Botón para abrir archivo externamente
        open_button = ctk.CTkButton(
            header_frame,
            text="📂",
            command=lambda: self.open_file_externally(config_file),
            width=30,
            height=25
        )
        open_button.grid(row=0, column=2, padx=5, pady=5)
        
        return file_frame
    
    def load_single_config(self, config_file, parent_frame):
        """Cargar un archivo de configuración específico"""
        try:
            # Configurar parser para ser más permisivo
            config = configparser.ConfigParser(
                allow_no_value=True,
                strict=False,
                interpolation=None
            )
            config.read(config_file, encoding='utf-8')
            
            self.config_data[config_file] = config
            self.config_widgets[config_file] = {}
            
            row_index = 1
            
            # Crear secciones y campos dinámicamente
            for section_name in config.sections():
                section_frame = self.create_section_frame(
                    parent_frame, section_name, row_index
                )
                row_index += 1
                
                self.config_widgets[config_file][section_name] = {}
                
                # Crear campos para cada opción en la sección
                field_row = 0
                for key, value in config[section_name].items():
                    widget = self.create_dynamic_field(
                        section_frame, key, value, field_row
                    )
                    self.config_widgets[config_file][section_name][key] = widget
                    field_row += 1
                    
        except configparser.DuplicateOptionError as e:
            self.logger.warning(f"Archivo con claves duplicadas {config_file}: {e}")
            # Usar método alternativo para archivos con duplicados
            self.load_config_with_duplicates(config_file, parent_frame)
        except Exception as e:
            self.logger.error(f"Error al cargar {config_file}: {e}")
            error_label = ctk.CTkLabel(
                parent_frame,
                text=f"❌ Error al cargar archivo: {str(e)}",
                text_color="red"
            )
            error_label.grid(row=1, column=0, padx=10, pady=5)
    
    def load_config_with_duplicates(self, config_file, parent_frame):
        """Cargar archivo de configuración con claves duplicadas usando lectura manual"""
        try:
            self.config_widgets[config_file] = {}
            current_section = None
            row_index = 1
            
            with open(config_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Parsear manualmente el archivo
            config_data = {}
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith(';'):
                    continue
                
                # Detectar sección
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    config_data[current_section] = {}
                    continue
                
                # Detectar clave=valor
                if '=' in line and current_section:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Si la clave ya existe, agregar un sufijo
                    original_key = key
                    counter = 1
                    while key in config_data[current_section]:
                        key = f"{original_key}_{counter}"
                        counter += 1
                    
                    config_data[current_section][key] = value
            
            # Crear UI para los datos parseados
            for section_name, section_data in config_data.items():
                if not section_data:  # Saltar secciones vacías
                    continue
                    
                section_frame = self.create_section_frame(
                    parent_frame, section_name, row_index
                )
                row_index += 1
                
                self.config_widgets[config_file][section_name] = {}
                
                field_row = 0
                for key, value in section_data.items():
                    widget = self.create_dynamic_field(
                        section_frame, key, value, field_row
                    )
                    self.config_widgets[config_file][section_name][key] = widget
                    field_row += 1
            
            # Crear un objeto configparser simulado para compatibilidad
            config = configparser.ConfigParser(allow_no_value=True)
            for section_name, section_data in config_data.items():
                if section_name and section_data:
                    config.add_section(section_name)
                    for key, value in section_data.items():
                        config.set(section_name, key, value)
            
            self.config_data[config_file] = config
            
        except Exception as e:
            self.logger.error(f"Error al cargar archivo con duplicados {config_file}: {e}")
            error_label = ctk.CTkLabel(
                parent_frame,
                text=f"❌ Error al cargar archivo con duplicados: {str(e)}",
                text_color="red"
            )
            error_label.grid(row=1, column=0, padx=10, pady=5)
    
    def create_section_frame(self, parent, section_name, row_index):
        """Crear frame para una sección de configuración"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.grid(row=row_index, column=0, padx=10, pady=5, sticky="ew")
        section_frame.grid_columnconfigure(1, weight=1)
        
        # Header de la sección
        section_label = ctk.CTkLabel(
            section_frame,
            text=f"[{section_name}]",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("blue", "lightblue")
        )
        section_label.grid(row=0, column=0, columnspan=2, padx=5, pady=(5, 10), sticky="w")
        
        return section_frame
    
    def create_dynamic_field(self, parent, key, value, row_index):
        """Crear campo dinámico basado en el tipo de valor"""
        # Label para la clave
        key_label = ctk.CTkLabel(
            parent,
            text=f"{key}:",
            font=ctk.CTkFont(size=11)
        )
        key_label.grid(row=row_index + 1, column=0, padx=5, pady=2, sticky="w")
        
        # Determinar tipo de widget basado en el valor
        widget_type = self.detect_value_type(key, value)
        
        if widget_type == bool:
            # Switch para valores booleanos
            widget = ctk.CTkSwitch(parent, text="")
            if value.lower() in ['true', '1', 'yes', 'on', 'enabled']:
                widget.select()
            else:
                widget.deselect()
                
        elif widget_type == int:
            # Entry numérico para enteros
            widget = ctk.CTkEntry(parent, placeholder_text="Número entero")
            widget.insert(0, str(value))
            
        elif widget_type == float:
            # Entry numérico para decimales
            widget = ctk.CTkEntry(parent, placeholder_text="Número decimal")
            widget.insert(0, str(value))
            
        else:
            # Entry de texto por defecto
            if len(value) > 50:
                # Textbox para valores largos
                widget = ctk.CTkTextbox(parent, height=60)
                widget.insert("1.0", value)
            else:
                # Entry normal para valores cortos
                widget = ctk.CTkEntry(parent)
                widget.insert(0, value)
        
        widget.grid(row=row_index + 1, column=1, padx=5, pady=2, sticky="ew")
        
        # Tooltip con información adicional
        self.create_tooltip(widget, key, value, widget_type)
        
        return widget
    
    def detect_value_type(self, key, value):
        """Detectar el tipo de dato basado en la clave y valor"""
        key_lower = key.lower()
        value_lower = value.lower()
        
        # Verificar si es booleano
        if value_lower in ['true', 'false', '1', '0', 'yes', 'no', 'on', 'off', 'enabled', 'disabled']:
            return bool
        
        # Verificar patrones en la clave
        for pattern, data_type in self.type_hints.items():
            if pattern in key_lower:
                return data_type
        
        # Verificar si el valor es numérico
        try:
            if '.' in value:
                float(value)
                return float
            else:
                int(value)
                return int
        except ValueError:
            pass
        
        # Por defecto, tratar como string
        return str
    
    def create_tooltip(self, widget, key, value, widget_type):
        """Crear tooltip informativo para el widget"""
        tooltip_text = f"Clave: {key}\nValor original: {value}\nTipo: {widget_type.__name__}"
        
        # Agregar información adicional basada en patrones conocidos
        key_lower = key.lower()
        if 'multiplier' in key_lower or 'rate' in key_lower:
            tooltip_text += "\n💡 Multiplicador (1.0 = normal)"
        elif 'max' in key_lower or 'limit' in key_lower:
            tooltip_text += "\n💡 Valor máximo permitido"
        elif 'port' in key_lower:
            tooltip_text += "\n💡 Puerto de red (1024-65535)"
        elif 'password' in key_lower:
            tooltip_text += "\n🔒 Campo de contraseña"
        
        # Nota: En una implementación completa, aquí se podría agregar
        # un sistema de tooltips más sofisticado
    
    def save_all_configs(self):
        """Guardar todos los archivos de configuración modificados"""
        try:
            saved_files = 0
            
            for config_file, config_obj in self.config_data.items():
                if self.save_single_config(config_file, config_obj):
                    saved_files += 1
            
            if saved_files > 0:
                self.status_label.configure(
                    text=f"✅ Guardados {saved_files} archivos de configuración"
                )
                messagebox.showinfo(
                    "Configuración Guardada", 
                    f"Se guardaron exitosamente {saved_files} archivos de configuración."
                )
            else:
                self.status_label.configure(text="⚠️ No se guardó ningún archivo")
                
        except Exception as e:
            self.logger.error(f"Error al guardar configuraciones: {e}")
            self.status_label.configure(text=f"❌ Error al guardar: {str(e)}")
            messagebox.showerror("Error", f"Error al guardar configuraciones:\n{str(e)}")
    
    def save_single_config(self, config_file, config_obj):
        """Guardar un archivo de configuración específico"""
        try:
            if config_file not in self.config_widgets:
                return False
            
            # Actualizar el objeto de configuración con los valores de los widgets
            for section_name, section_widgets in self.config_widgets[config_file].items():
                if not config_obj.has_section(section_name):
                    config_obj.add_section(section_name)
                
                for key, widget in section_widgets.items():
                    try:
                        # Obtener valor del widget según su tipo
                        if isinstance(widget, ctk.CTkSwitch):
                            value = "True" if widget.get() else "False"
                        elif isinstance(widget, ctk.CTkTextbox):
                            value = widget.get("1.0", "end-1c")
                        else:  # CTkEntry
                            value = widget.get()
                        
                        config_obj.set(section_name, key, str(value))
                        
                    except Exception as e:
                        self.logger.warning(f"Error al obtener valor de {key}: {e}")
                        continue
            
            # Crear backup del archivo original
            backup_path = f"{config_file}.backup"
            if os.path.exists(config_file):
                shutil.copy2(config_file, backup_path)
            
            # Guardar el archivo actualizado
            with open(config_file, 'w', encoding='utf-8') as f:
                config_obj.write(f)
            
            self.logger.info(f"Configuración guardada: {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al guardar {config_file}: {e}")
            return False
    
    def reload_all_configs(self):
        """Recargar todos los archivos de configuración"""
        self.scan_for_config_files()
    
    def open_file_externally(self, file_path):
        """Abrir archivo de configuración en editor externo"""
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', file_path])
                
        except Exception as e:
            self.logger.error(f"Error al abrir archivo externamente: {e}")
            messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{str(e)}")
