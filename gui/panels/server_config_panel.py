import customtkinter as ctk
import configparser
import os
from pathlib import Path
from tkinter import messagebox
import re

class ServerConfigPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger, main_window):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        
        # Variables para el servidor actual
        self.current_server = None
        self.current_server_path = None
        
        # Diccionarios para almacenar datos
        self.config_data = {}  # {file_type: configparser_object}
        self.config_widgets = {}  # {file_type: {section: {key: widget}}}
        self.filtered_widgets = {}  # Para el filtro de búsqueda
        
        # Filtro de búsqueda
        self.search_filter = ""
        self.current_tab_type = None  # Para rastrear la pestaña actual
        
        # Tipos de archivos INI de ARK
        self.ini_types = {
            "GameUserSettings": "GameUserSettings.ini",
            "Game": "Game.ini",
            "Engine": "Engine.ini"
        }
        
        # Patrones para detectar tipos de datos
        self.type_patterns = {
            # Booleanos
            'enable': bool, 'disable': bool, 'use': bool, 'allow': bool,
            'show': bool, 'hide': bool, 'auto': bool, 'force': bool,
            'pve': bool, 'pvp': bool, 'public': bool, 'private': bool,
            # Números flotantes
            'multiplier': float, 'rate': float, 'speed': float, 'scale': float,
            'offset': float, 'factor': float, 'percent': float, 'ratio': float,
            'damage': float, 'health': float, 'stamina': float, 'weight': float,
            # Números enteros
            'max': int, 'min': int, 'limit': int, 'count': int,
            'time': int, 'duration': int, 'interval': int, 'period': int,
            'port': int, 'players': int, 'level': int, 'size': int,
            # Texto
            'name': str, 'password': str, 'message': str, 'motd': str,
            'admin': str, 'server': str, 'map': str, 'mod': str, 'path': str
        }
        
        self.create_widgets()
        self.pack(fill="both", expand=True)
        
        # Cargar configuración inicial después de un breve delay
        self.after(100, self.load_current_server_configs)
    
    def create_widgets(self):
        """Crear la estructura básica del panel"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        
        # 1. Título y servidor actual
        title_frame = ctk.CTkFrame(self)
        title_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        title_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="🎮 Configuración del Servidor",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.server_info_label = ctk.CTkLabel(
            title_frame,
            text="Servidor: No seleccionado",
            font=ctk.CTkFont(size=12)
        )
        self.server_info_label.grid(row=0, column=1, padx=10, pady=10, sticky="e")
        
        # 2. Barra de búsqueda
        search_frame = ctk.CTkFrame(self)
        search_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        search_frame.grid_columnconfigure(1, weight=1)
        
        search_label = ctk.CTkLabel(search_frame, text="🔍 Buscar:")
        search_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Buscar: max, multiplier, enable, port, server...",
            width=350
        )
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        
        clear_button = ctk.CTkButton(
            search_frame,
            text="🗑️",
            command=self.clear_search,
            width=30
        )
        clear_button.grid(row=0, column=2, padx=5, pady=5)
        
        # 3. Botones de acción
        buttons_frame = ctk.CTkFrame(self)
        buttons_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        refresh_button = ctk.CTkButton(
            buttons_frame,
            text="🔄 Recargar",
            command=self.load_current_server_configs,
            width=100
        )
        refresh_button.pack(side="left", padx=5, pady=5)
        
        save_button = ctk.CTkButton(
            buttons_frame,
            text="💾 Guardar Todo",
            command=self.save_all_configs,
            width=120
        )
        save_button.pack(side="left", padx=5, pady=5)
        
        self.status_label = ctk.CTkLabel(
            buttons_frame,
            text="⏳ Cargando...",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(side="right", padx=10, pady=5)
        
        # 4. Pestañas para diferentes tipos de INI
        self.ini_tabview = ctk.CTkTabview(self, command=self.on_tab_change)
        self.ini_tabview.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
        
        # Crear pestañas para cada tipo de INI
        self.tabs = {}
        self.tab_contents = {}
        
        for ini_type in self.ini_types.keys():
            tab = self.ini_tabview.add(ini_type)
            self.tabs[ini_type] = tab
            
            # Crear contenido scrolleable para cada pestaña
            scroll_frame = ctk.CTkScrollableFrame(tab)
            scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
            scroll_frame.grid_columnconfigure(0, weight=1)
            
            self.tab_contents[ini_type] = scroll_frame
        
        # Establecer pestaña inicial
        if self.ini_types:
            self.current_tab_type = list(self.ini_types.keys())[0]
    
    def on_tab_change(self):
        """Manejar cambio de pestaña"""
        try:
            current_tab = self.ini_tabview.get()
            self.current_tab_type = current_tab
            
            # Si hay un filtro activo, reaplicarlo a la nueva pestaña
            if self.search_filter:
                self.apply_search_filter(self.search_filter)
        except Exception as e:
            self.logger.error(f"Error al cambiar pestaña: {e}")
    
    def load_current_server_configs(self):
        """Cargar configuraciones del servidor actualmente seleccionado"""
        try:
            # Obtener servidor seleccionado del MainWindow
            if hasattr(self.main_window, 'selected_server') and self.main_window.selected_server:
                server_name = self.main_window.selected_server
            else:
                self.status_label.configure(text="⚠️ No hay servidor seleccionado")
                self.server_info_label.configure(text="Servidor: No seleccionado")
                return
            
            # Construir ruta del servidor
            root_path = self.config_manager.get("server", "root_path", "")
            if not root_path:
                self.status_label.configure(text="❌ Ruta raíz no configurada")
                return
            
            server_path = os.path.join(root_path, server_name)
            if not os.path.exists(server_path):
                self.status_label.configure(text=f"❌ Servidor no encontrado: {server_name}")
                return
            
            self.current_server = server_name
            self.current_server_path = server_path
            self.server_info_label.configure(text=f"Servidor: {server_name}")
            self.status_label.configure(text="🔍 Buscando archivos INI...")
            
            # Buscar archivos INI específicos del servidor
            config_path = os.path.join(server_path, "ShooterGame", "Saved", "Config", "WindowsServer")
            
            self.logger.info(f"Buscando configuraciones en: {config_path}")
            
            if not os.path.exists(config_path):
                self.status_label.configure(text="⚠️ Directorio de configuración no encontrado")
                self.show_config_help(config_path)
                return
            
            # Cargar cada tipo de INI
            loaded_files = 0
            for ini_type, filename in self.ini_types.items():
                file_path = os.path.join(config_path, filename)
                if os.path.exists(file_path):
                    self.load_ini_file(ini_type, file_path)
                    loaded_files += 1
                    self.logger.info(f"Cargado {filename} para {server_name}")
                else:
                    self.show_missing_ini_help(ini_type, file_path)
            
            if loaded_files > 0:
                self.status_label.configure(text=f"✅ {loaded_files} archivos INI cargados")
            else:
                self.status_label.configure(text="⚠️ No se encontraron archivos INI")
                
        except Exception as e:
            self.logger.error(f"Error al cargar configuraciones del servidor: {e}")
            self.status_label.configure(text=f"❌ Error: {str(e)}")
    
    def load_ini_file(self, ini_type, file_path):
        """Cargar un archivo INI específico"""
        try:
            # Limpiar contenido anterior de esta pestaña
            for widget in self.tab_contents[ini_type].winfo_children():
                widget.destroy()
            
            # Intentar cargar con configparser estándar
            try:
                config = configparser.ConfigParser(
                    allow_no_value=True,
                    strict=False,
                    interpolation=None
                )
                config.read(file_path, encoding='utf-8')
                self.config_data[ini_type] = config
                
            except configparser.DuplicateOptionError:
                # Si hay claves duplicadas, usar método manual
                self.logger.warning(f"Archivo {file_path} tiene claves duplicadas, usando parser manual")
                config = self.parse_ini_manually(file_path)
                self.config_data[ini_type] = config
            
            # Crear widgets para las secciones y opciones
            self.create_ini_widgets(ini_type, config)
            
        except Exception as e:
            self.logger.error(f"Error al cargar {file_path}: {e}")
            error_label = ctk.CTkLabel(
                self.tab_contents[ini_type],
                text=f"❌ Error al cargar archivo:\n{str(e)}",
                text_color="red"
            )
            error_label.pack(pady=20)
    
    def parse_ini_manually(self, file_path):
        """Parser manual para archivos INI con claves duplicadas"""
        config = configparser.ConfigParser(allow_no_value=True, strict=False)
        current_section = None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Saltar líneas vacías y comentarios
                if not line or line.startswith('#') or line.startswith(';'):
                    continue
                
                # Detectar sección
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    if not config.has_section(current_section):
                        config.add_section(current_section)
                    continue
                
                # Detectar clave=valor
                if '=' in line and current_section:
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Si la clave ya existe, agregar sufijo numérico
                        original_key = key
                        counter = 1
                        while config.has_option(current_section, key):
                            key = f"{original_key}_{counter}"
                            counter += 1
                        
                        config.set(current_section, key, value)
                        
                    except Exception as e:
                        self.logger.warning(f"Error en línea {line_num} de {file_path}: {e}")
        
        return config
    
    def create_ini_widgets(self, ini_type, config):
        """Crear widgets para un archivo INI"""
        self.config_widgets[ini_type] = {}
        
        row = 0
        for section_name in config.sections():
            # Crear frame para la sección
            section_frame = ctk.CTkFrame(self.tab_contents[ini_type])
            section_frame.pack(fill="x", padx=5, pady=5)
            section_frame.grid_columnconfigure(1, weight=1)
            
            # Título de la sección
            section_label = ctk.CTkLabel(
                section_frame,
                text=f"📁 [{section_name}]",
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w"
            )
            section_label.pack(fill="x", padx=10, pady=(10, 5))
            
            # Contenedor para las opciones
            options_frame = ctk.CTkFrame(section_frame)
            options_frame.pack(fill="x", padx=10, pady=(0, 10))
            options_frame.grid_columnconfigure(1, weight=1)
            
            self.config_widgets[ini_type][section_name] = {}
            
            # Crear widgets para cada opción
            option_row = 0
            for key, value in config[section_name].items():
                widget = self.create_parameter_widget(
                    options_frame, key, value, option_row
                )
                self.config_widgets[ini_type][section_name][key] = widget
                option_row += 1
    
    def create_parameter_widget(self, parent, key, value, row):
        """Crear widget apropiado para un parámetro"""
        # Detectar tipo de dato
        data_type = self.detect_data_type(key, value)
        
        # Frame para el parámetro
        param_frame = ctk.CTkFrame(parent)
        param_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        param_frame.grid_columnconfigure(1, weight=1)
        
        # Label del parámetro
        label = ctk.CTkLabel(
            param_frame,
            text=f"{key}:",
            font=ctk.CTkFont(size=11),
            anchor="w",
            width=200
        )
        label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Widget apropiado según el tipo
        if data_type == bool:
            widget = ctk.CTkSwitch(
                param_frame,
                text="",
                width=50
            )
            # Establecer valor inicial
            if value.lower() in ['true', '1', 'yes', 'on']:
                widget.select()
        
        elif data_type in [int, float]:
            widget = ctk.CTkEntry(
                param_frame,
                placeholder_text=f"Valor {data_type.__name__}",
                width=150
            )
            widget.insert(0, str(value))
        
        else:  # string
            # Si el valor es muy largo, usar textbox
            if len(str(value)) > 50:
                widget = ctk.CTkTextbox(
                    param_frame,
                    height=60,
                    width=300
                )
                widget.insert("1.0", str(value))
            else:
                widget = ctk.CTkEntry(
                    param_frame,
                    placeholder_text="Valor de texto",
                    width=300
                )
                widget.insert(0, str(value))
        
        widget.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        return widget
    
    def detect_data_type(self, key, value):
        """Detectar tipo de dato basado en clave y valor"""
        key_lower = key.lower()
        value_str = str(value).lower().strip()
        
        # Verificar booleanos
        if (any(pattern in key_lower for pattern in ['enable', 'allow', 'show', 'use', 'auto', 'force', 'pve', 'pvp']) or
            value_str in ['true', 'false', '1', '0', 'yes', 'no', 'on', 'off']):
            return bool
        
        # Verificar números flotantes
        try:
            if '.' in value_str and float(value_str):
                return float
        except:
            pass
        
        # Verificar enteros
        try:
            if value_str.isdigit() or (value_str.startswith('-') and value_str[1:].isdigit()):
                return int
        except:
            pass
        
        # Por defecto, string
        return str
    
    def on_search_change(self, event=None):
        """Manejar cambios en el filtro de búsqueda"""
        search_text = self.search_entry.get().lower().strip()
        self.search_filter = search_text
        
        # Si no hay filtro, restaurar orden original
        if not search_text:
            self.restore_original_order()
            return
        
        # Aplicar filtro y reordenar
        self.apply_search_filter(search_text)
    
    def apply_search_filter(self, search_text):
        """Aplicar filtro de búsqueda y reordenar resultados"""
        # Solo filtrar la pestaña actualmente visible
        if self.current_tab_type and self.current_tab_type in self.config_data:
            self.filter_and_reorder_tab(self.current_tab_type, search_text)
    
    def filter_and_reorder_tab(self, ini_type, search_text):
        """Filtrar y reordenar contenido de una pestaña"""
        tab_content = self.tab_contents[ini_type]
        
        # Limpiar contenido actual
        for widget in tab_content.winfo_children():
            widget.destroy()
        
        # Obtener datos de configuración para esta pestaña
        if ini_type not in self.config_data:
            return
        
        config = self.config_data[ini_type]
        
        # Recopilar todos los parámetros con información de coincidencia
        all_params = []
        
        for section_name in config.sections():
            for key, value in config[section_name].items():
                param_info = {
                    'section': section_name,
                    'key': key,
                    'value': value,
                    'match_type': self.get_param_match_type(key, value, search_text),
                    'match_score': self.get_match_score(key, value, search_text)
                }
                all_params.append(param_info)
        
        # Filtrar solo parámetros con coincidencias
        matching_params = [p for p in all_params if p['match_type'] != 'none']
        
        # Ordenar por relevancia: exactos primero, luego por puntuación
        matching_params.sort(key=lambda x: (
            0 if x['match_type'] == 'exact' else 1,  # Exactos primero
            -x['match_score']  # Mayor puntuación primero
        ))
        
        # Crear widgets para los parámetros encontrados
        if matching_params:
            # Crear un frame de resultados
            results_frame = ctk.CTkFrame(tab_content)
            results_frame.pack(fill="x", padx=5, pady=5)
            
            results_label = ctk.CTkLabel(
                results_frame,
                text=f"🔍 {len(matching_params)} coincidencias para '{search_text}'",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#4CAF50"
            )
            results_label.pack(pady=10)
            
            # Crear widgets para cada parámetro encontrado
            for i, param in enumerate(matching_params):
                self.create_search_result_widget(tab_content, param, search_text, i)
        else:
            # Sin resultados
            no_results_frame = ctk.CTkFrame(tab_content)
            no_results_frame.pack(fill="x", padx=5, pady=20)
            
            no_results_label = ctk.CTkLabel(
                no_results_frame,
                text=f"❌ No se encontraron coincidencias para '{search_text}'",
                font=ctk.CTkFont(size=12),
                text_color="#FF6B6B"
            )
            no_results_label.pack(pady=20)
    
    def get_param_match_type(self, key, value, search_text):
        """Determinar tipo de coincidencia para un parámetro específico"""
        key_lower = key.lower()
        value_lower = str(value).lower()
        
        # Coincidencia exacta en nombre del parámetro
        if search_text == key_lower:
            return 'exact'
        
        # Coincidencia parcial en nombre del parámetro (prioritaria)
        if search_text in key_lower:
            return 'partial_key'
        
        # Coincidencia en valor
        if search_text in value_lower:
            return 'partial_value'
        
        return 'none'
    
    def get_match_score(self, key, value, search_text):
        """Calcular puntuación de coincidencia (mayor = más relevante)"""
        score = 0
        key_lower = key.lower()
        value_lower = str(value).lower()
        
        # Puntuación por posición en el nombre del parámetro
        if search_text in key_lower:
            pos = key_lower.find(search_text)
            # Coincidencia al inicio vale más
            score += 100 - pos
            
            # Coincidencia exacta vale mucho más
            if search_text == key_lower:
                score += 1000
        
        # Puntuación por coincidencia en valor (menor peso)
        if search_text in value_lower:
            score += 10
        
        # Penalizar parámetros muy largos
        score -= len(key) * 0.1
        
        return score
    
    def create_search_result_widget(self, parent, param_info, search_text, index):
        """Crear widget para un resultado de búsqueda"""
        # Frame principal del resultado
        result_frame = ctk.CTkFrame(parent)
        result_frame.pack(fill="x", padx=5, pady=3)
        result_frame.grid_columnconfigure(1, weight=1)
        
        # Indicador de relevancia
        relevance_color = "#FFD700" if param_info['match_type'] == 'exact' else "#87CEEB"
        relevance_label = ctk.CTkLabel(
            result_frame,
            text=f"#{index + 1}",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=relevance_color,
            width=30
        )
        relevance_label.grid(row=0, column=0, padx=5, pady=5)
        
        # Frame de información del parámetro
        param_frame = ctk.CTkFrame(result_frame)
        param_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        param_frame.grid_columnconfigure(1, weight=1)
        
        # Sección y parámetro con resaltado
        section_text = f"[{param_info['section']}]"
        param_text = self.highlight_text(param_info['key'], search_text)
        
        info_label = ctk.CTkLabel(
            param_frame,
            text=f"{section_text} → {param_text}",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        info_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        
        # Widget de edición
        widget = self.create_parameter_widget_simple(param_frame, param_info)
        
        # Almacenar referencia del widget para guardado
        if param_info['section'] not in self.config_widgets.setdefault(self.current_tab_type, {}):
            self.config_widgets[self.current_tab_type][param_info['section']] = {}
        
        self.config_widgets[self.current_tab_type][param_info['section']][param_info['key']] = widget
    
    def highlight_text(self, text, search_text):
        """Resaltar texto de búsqueda (para mostrar en labels)"""
        text_lower = text.lower()
        search_lower = search_text.lower()
        
        if search_lower in text_lower:
            # Encontrar la posición exacta respetando mayúsculas
            start_pos = text_lower.find(search_lower)
            if start_pos != -1:
                end_pos = start_pos + len(search_text)
                original_match = text[start_pos:end_pos]
                
                # Reemplazar con asteriscos para resaltar
                highlighted = text[:start_pos] + f"*{original_match}*" + text[end_pos:]
                return highlighted
        
        return text
    
    def create_parameter_widget_simple(self, parent, param_info):
        """Crear widget simplificado para resultado de búsqueda"""
        key = param_info['key']
        value = param_info['value']
        
        # Detectar tipo de dato
        data_type = self.detect_data_type(key, value)
        
        # Label del parámetro
        label = ctk.CTkLabel(
            parent,
            text=f"{key}:",
            font=ctk.CTkFont(size=10),
            anchor="w",
            width=150
        )
        label.grid(row=1, column=0, padx=10, pady=2, sticky="w")
        
        # Widget apropiado según el tipo
        if data_type == bool:
            widget = ctk.CTkSwitch(parent, text="", width=50)
            if str(value).lower() in ['true', '1', 'yes', 'on']:
                widget.select()
        elif data_type in [int, float]:
            widget = ctk.CTkEntry(parent, width=120)
            widget.insert(0, str(value))
        else:
            widget = ctk.CTkEntry(parent, width=200)
            widget.insert(0, str(value))
        
        widget.grid(row=1, column=1, padx=10, pady=2, sticky="w")
        
        return widget
    
    def get_frame_match_type(self, frame, search_text):
        """Determinar el tipo de coincidencia de un frame"""
        frame_text = self.get_frame_text(frame).lower()
        
        if not frame_text:
            return "none"
        
        # Buscar coincidencias exactas en nombres de parámetros
        for line in frame_text.split('\n'):
            if ':' in line:
                param_name = line.split(':')[0].strip()
                if search_text == param_name.lower():
                    return "exact"
        
        # Buscar coincidencias parciales
        if search_text in frame_text:
            return "partial"
        
        return "none"
    
    def get_frame_text(self, frame):
        """Obtener todo el texto de un frame recursivamente"""
        text_parts = []
        
        def extract_text(widget):
            if isinstance(widget, ctk.CTkLabel):
                text_parts.append(widget.cget("text"))
            elif isinstance(widget, ctk.CTkEntry):
                try:
                    text_parts.append(widget.get())
                except:
                    pass
            elif isinstance(widget, ctk.CTkTextbox):
                try:
                    text_parts.append(widget.get("1.0", "end-1c"))
                except:
                    pass
            
            # Recursivamente obtener texto de widgets hijos
            try:
                for child in widget.winfo_children():
                    extract_text(child)
            except:
                pass
        
        extract_text(frame)
        return ' '.join(text_parts)
    
    def highlight_matches_in_frame(self, frame, search_text):
        """Resaltar coincidencias dentro de un frame"""
        def highlight_widget(widget):
            try:
                if isinstance(widget, ctk.CTkLabel):
                    text = widget.cget("text").lower()
                    if search_text in text:
                        # Cambiar color del label para resaltar
                        widget.configure(text_color="#FFD700")  # Dorado
                    else:
                        widget.configure(text_color=None)  # Color por defecto
                
                # Recursivamente aplicar a widgets hijos
                for child in widget.winfo_children():
                    highlight_widget(child)
            except:
                pass
        
        highlight_widget(frame)
    
    def restore_original_order(self):
        """Restaurar el orden original y quitar resaltado"""
        for ini_type in self.config_data.keys():
            if ini_type in self.tab_contents:
                tab_content = self.tab_contents[ini_type]
                
                # Obtener todos los frames
                frames = []
                for widget in tab_content.winfo_children():
                    if isinstance(widget, ctk.CTkFrame):
                        frames.append(widget)
                
                # Ocultar todos
                for frame in frames:
                    frame.pack_forget()
                
                # Volver a mostrar en orden original
                for frame in frames:
                    frame.pack(fill="x", padx=5, pady=5)
                    # Quitar resaltado
                    self.remove_highlight_from_frame(frame)
    
    def remove_highlight_from_frame(self, frame):
        """Quitar resaltado de un frame"""
        def remove_highlight(widget):
            try:
                if isinstance(widget, ctk.CTkLabel):
                    widget.configure(text_color=None)  # Color por defecto
                
                # Recursivamente aplicar a widgets hijos
                for child in widget.winfo_children():
                    remove_highlight(child)
            except:
                pass
        
        remove_highlight(frame)
    
    def show_all_widgets(self):
        """Mostrar todos los widgets (método legacy)"""
        self.restore_original_order()
    
    def clear_search(self):
        """Limpiar filtro de búsqueda"""
        self.search_entry.delete(0, "end")
        self.show_all_widgets()
    
    def show_config_help(self, config_path):
        """Mostrar ayuda cuando no se encuentra el directorio de configuración"""
        help_frame = ctk.CTkFrame(self.tab_contents["GameUserSettings"])
        help_frame.pack(fill="x", padx=10, pady=10)
        
        help_label = ctk.CTkLabel(
            help_frame,
            text=f"📁 Directorio de configuración no encontrado:\n{config_path}\n\n"
                 "💡 Para generar los archivos de configuración:\n"
                 "1. Inicia el servidor al menos una vez\n"
                 "2. Los archivos se crearán automáticamente\n"
                 "3. Recarga esta pestaña",
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        help_label.pack(padx=20, pady=20)
    
    def show_missing_ini_help(self, ini_type, file_path):
        """Mostrar mensaje cuando falta un archivo INI específico"""
        if ini_type in self.tab_contents:
            help_label = ctk.CTkLabel(
                self.tab_contents[ini_type],
                text=f"📄 Archivo {self.ini_types[ini_type]} no encontrado\n\n"
                     f"Ruta esperada: {file_path}\n\n"
                     "💡 Este archivo se creará automáticamente al iniciar el servidor",
                font=ctk.CTkFont(size=11),
                text_color="orange"
            )
            help_label.pack(pady=20)
    
    def save_all_configs(self):
        """Guardar todas las configuraciones modificadas"""
        try:
            if not self.current_server:
                messagebox.showwarning("Advertencia", "No hay servidor seleccionado")
                return
            
            saved_files = 0
            config_path = os.path.join(
                self.current_server_path, 
                "ShooterGame", "Saved", "Config", "WindowsServer"
            )
            
            for ini_type in self.config_data.keys():
                if self.save_ini_file(ini_type, config_path):
                    saved_files += 1
            
            if saved_files > 0:
                self.status_label.configure(text=f"✅ {saved_files} archivos guardados")
                messagebox.showinfo("Éxito", f"Se guardaron {saved_files} archivos de configuración")
            else:
                self.status_label.configure(text="⚠️ No hay cambios para guardar")
                
        except Exception as e:
            self.logger.error(f"Error al guardar configuraciones: {e}")
            self.status_label.configure(text=f"❌ Error al guardar: {str(e)}")
            messagebox.showerror("Error", f"Error al guardar configuraciones:\n{str(e)}")
    
    def save_ini_file(self, ini_type, config_path):
        """Guardar un archivo INI específico"""
        try:
            if ini_type not in self.config_data or ini_type not in self.config_widgets:
                return False
            
            config = self.config_data[ini_type]
            file_path = os.path.join(config_path, self.ini_types[ini_type])
            
            # Crear backup
            if os.path.exists(file_path):
                backup_path = f"{file_path}.backup"
                import shutil
                shutil.copy2(file_path, backup_path)
                self.logger.info(f"Backup creado: {backup_path}")
            
            # Actualizar valores del config con los widgets
            for section_name, section_widgets in self.config_widgets[ini_type].items():
                for key, widget in section_widgets.items():
                    try:
                        if isinstance(widget, ctk.CTkSwitch):
                            value = "True" if widget.get() else "False"
                        elif isinstance(widget, ctk.CTkTextbox):
                            value = widget.get("1.0", "end-1c")
                        else:  # CTkEntry
                            value = widget.get()
                        
                        config.set(section_name, key, str(value))
                        
                    except Exception as e:
                        self.logger.warning(f"Error al obtener valor de {key}: {e}")
            
            # Escribir archivo
            with open(file_path, 'w', encoding='utf-8') as f:
                config.write(f)
            
            self.logger.info(f"Guardado {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al guardar {ini_type}: {e}")
            return False
    
    def update_server_selection(self, server_name):
        """Actualizar cuando se cambia el servidor seleccionado"""
        if server_name != self.current_server:
            self.load_current_server_configs()
    
    def show_message(self, message, msg_type="info"):
        """Mostrar mensaje en el log principal"""
        if hasattr(self.main_window, 'add_log_message'):
            self.main_window.add_log_message(message)
        else:
            self.logger.info(message)
