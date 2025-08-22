import customtkinter as ctk
import requests
import json
import threading
import os
import sys
from datetime import datetime
from tkinter import messagebox
import webbrowser
from PIL import Image, ImageTk
import io

class ModsPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger, main_window=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        
        # API Key de CurseForge
        self.api_key = "$2a$10$QpJTDU3rwgYCGDk/QUeUyO./vQpjf4A1uanFh0b/nxnaZTIErME7y"
        self.base_url = "https://api.curseforge.com/v1"
        self.game_id = 83374  # ARK: Survival Ascended
        
        # Variables del estado
        self.current_mods = []
        self.installed_mods = []
        self.favorite_mods = []
        self.search_results = []
        
        # Estado actual del servidor/mapa
        self.current_server = None
        self.current_map = None
        
        # Variables para filtros y vista
        self.current_view = "grid"  # "grid" o "list"
        self.current_filter = "all"  # "all", "favorites", "installed", "search"
        self.search_filter = ""
        
        # Variable para controlar mensajes de inicio
        self.show_startup_messages = True
        self.load_startup_messages_setting()
        
        # Empaquetar el frame principal
        self.pack(fill="both", expand=True)
        
        self.create_widgets()
        self.load_favorite_mods()
        self.load_current_server_map()
        self.load_installed_mods()
        
        # Actualizar UI inicial después de cargar datos
        self._safe_schedule_ui_update(lambda: self.after(100, self.refresh_initial_tabs))
    
    def _safe_schedule_ui_update(self, callback):
        """Programar actualización de UI de forma segura verificando que la ventana principal y el widget existan"""
        try:
            # Verificar si la ventana principal existe y no está destruida
            if (hasattr(self, 'main_window') and self.main_window and 
                hasattr(self.main_window, 'root') and self.main_window.root and 
                self.main_window.root.winfo_exists()):
                # Verificar si este widget aún existe
                if self.winfo_exists():
                    self.main_window.root.after(0, callback)
                else:
                    return
            elif self.winfo_exists():
                # Fallback: usar el método after del widget actual si existe
                self.after(0, callback)
        except Exception as e:
            # Si hay cualquier error, simplemente ignorar la actualización
            if hasattr(self, 'logger') and self.logger:
                self.logger.debug(f"Error programando actualización UI: {e}")
    
    def get_data_directory(self):
        """Obtener directorio de datos correcto para ejecutable y desarrollo"""
        try:
            if hasattr(sys, '_MEIPASS'):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            data_dir = os.path.join(base_dir, "data")
            try:
                os.makedirs(data_dir, exist_ok=True)
                return data_dir
            except (OSError, PermissionError):
                # Si falla, usar directorio temporal
                import tempfile
                temp_dir = tempfile.mkdtemp(prefix="ArkSM_mods_data_")
                if self.logger:
                    self.logger.warning(f"ModsPanel: Usando directorio temporal para datos: {temp_dir}")
                else:
                    print(f"⚠️ ModsPanel: Usando directorio temporal para datos: {temp_dir}")
                return temp_dir
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al obtener directorio de datos: {e}")
            fallback_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
            try:
                os.makedirs(fallback_dir, exist_ok=True)
                return fallback_dir
            except (OSError, PermissionError):
                # Como último recurso, usar directorio temporal
                import tempfile
                emergency_dir = tempfile.mkdtemp(prefix="ArkSM_mods_emergency_")
                if self.logger:
                    self.logger.error(f"ModsPanel: Usando directorio de emergencia: {emergency_dir}")
                else:
                    print(f"🆘 ModsPanel: Usando directorio de emergencia: {emergency_dir}")
                return emergency_dir
    
    def refresh_initial_tabs(self):
        """Refrescar pestañas con contenido inicial"""
        try:
            self.refresh_mods_display()
            self.update_mods_ids_entry()
            
            # Solo mostrar mensajes si está habilitado en configuración
            if self.show_startup_messages:
                if self.favorite_mods or self.installed_mods:
                    status_msg = "✅ Mods cargados: "
                    if self.favorite_mods:
                        status_msg += f"{len(self.favorite_mods)} favoritos "
                    if self.installed_mods:
                        status_msg += f"{len(self.installed_mods)} instalados"
                    self.show_message(status_msg, "success")
                else:
                    self.show_message("💡 Busca mods usando la barra de búsqueda o haz clic en 'Populares'", "info")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al refrescar pestañas iniciales: {e}")
    
    def create_widgets(self):
        """Crear todos los widgets del panel"""
        # Frame principal con scroll
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Título principal
        title_label = ctk.CTkLabel(
            main_frame, 
            text="🎮 Gestor de Mods - ARK Survival Ascended", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Frame de configuración de mensajes de inicio
        self.create_startup_messages_frame(main_frame)
        
        # Frame de búsqueda mejorado
        self.create_search_frame(main_frame)
        
        # Frame de filtros y vista
        self.create_filters_frame(main_frame)
        
        # Frame de estadísticas rápidas
        self.create_stats_frame(main_frame)
        
        # Frame de mods con vista mejorada
        self.create_mods_display_frame(main_frame)
        
        # Frame de información de mods instalados
        self.create_installed_info_frame(main_frame)
    
    def create_startup_messages_frame(self, parent):
        """Crear frame para configuración de mensajes de inicio"""
        startup_frame = ctk.CTkFrame(parent, corner_radius=8)
        startup_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        # Frame interno para organizar elementos
        inner_frame = ctk.CTkFrame(startup_frame, fg_color="transparent")
        inner_frame.pack(fill="x", padx=10, pady=8)
        
        # Etiqueta descriptiva
        startup_label = ctk.CTkLabel(
            inner_frame,
            text="⚙️ Configuración de Mensajes",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        startup_label.pack(side="left")
        
        # Switch para controlar mensajes de inicio
        self.startup_messages_switch = ctk.CTkSwitch(
            inner_frame,
            text="Mostrar mensajes de inicio de la aplicación",
            command=self.toggle_startup_messages,
            font=ctk.CTkFont(size=11)
        )
        self.startup_messages_switch.pack(side="right", padx=(10, 0))
        
        # Establecer estado inicial del switch
        if self.show_startup_messages:
            self.startup_messages_switch.select()
        else:
            self.startup_messages_switch.deselect()
    
    def create_search_frame(self, parent):
        """Crear frame de búsqueda mejorado"""
        search_frame = ctk.CTkFrame(parent, corner_radius=8)
        search_frame.pack(fill="x", padx=5, pady=5)
        
        # Título de búsqueda
        search_title = ctk.CTkLabel(
            search_frame,
            text="🔍 Buscar Mods",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        search_title.pack(pady=5)
        
        # Frame de entrada y botones
        input_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=8, pady=5)
        
        # Entrada de búsqueda
        self.search_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Buscar mods por nombre, descripción...",
            height=32,
            font=ctk.CTkFont(size=12)
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Botón de búsqueda
        search_button = ctk.CTkButton(
            input_frame,
            text="🔍 Buscar",
            command=self.search_mods,
            height=32,
            width=100,
            font=ctk.CTkFont(size=11),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        search_button.pack(side="left", padx=(0, 5))
        
        # Botón de mods populares
        popular_button = ctk.CTkButton(
            input_frame,
            text="🔥 Populares",
            command=self.load_popular_mods,
            height=32,
            width=100,
            font=ctk.CTkFont(size=11),
            fg_color="#FF9800",
            hover_color="#F57C00"
        )
        popular_button.pack(side="left")
        
        # Status de búsqueda
        self.search_status_label = ctk.CTkLabel(
            search_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=("gray", "lightgray")
        )
        self.search_status_label.pack(pady=3)
    
    def create_filters_frame(self, parent):
        """Crear frame de filtros y vista"""
        filters_frame = ctk.CTkFrame(parent, corner_radius=8)
        filters_frame.pack(fill="x", padx=5, pady=5)
        
        # Título de filtros
        filters_title = ctk.CTkLabel(
            filters_frame,
            text="🎯 Filtros y Vista",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        filters_title.pack(pady=5)
        
        # Frame de botones de filtro
        filter_buttons_frame = ctk.CTkFrame(filters_frame, fg_color="transparent")
        filter_buttons_frame.pack(fill="x", padx=8, pady=5)
        
        # Botones de filtro
        self.all_filter_btn = ctk.CTkButton(
            filter_buttons_frame,
            text="📋 Todos",
            command=lambda: self.set_filter("all"),
            height=28,
            width=80,
            font=ctk.CTkFont(size=10),
            fg_color="#4CAF50",
            hover_color="#388E3C"
        )
        self.all_filter_btn.pack(side="left", padx=3)
        
        self.favorites_filter_btn = ctk.CTkButton(
            filter_buttons_frame,
            text="⭐ Favoritos",
            command=lambda: self.set_filter("favorites"),
            height=28,
            width=80,
            font=ctk.CTkFont(size=10),
            fg_color="#FF9800",
            hover_color="#F57C00"
        )
        self.favorites_filter_btn.pack(side="left", padx=3)
        
        self.installed_filter_btn = ctk.CTkButton(
            filter_buttons_frame,
            text="📦 Instalados",
            command=lambda: self.set_filter("installed"),
            height=28,
            width=80,
            font=ctk.CTkFont(size=10),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        self.installed_filter_btn.pack(side="left", padx=3)
        
        # Frame de vista y búsqueda local
        view_frame = ctk.CTkFrame(filters_frame, fg_color="transparent")
        view_frame.pack(fill="x", padx=8, pady=5)
        
        # Botones de vista
        self.grid_view_btn = ctk.CTkButton(
            view_frame,
            text="🔲 Vista Cuadrícula",
            command=lambda: self.set_view("grid"),
            height=28,
            width=100,
            font=ctk.CTkFont(size=10),
            fg_color="#9C27B0",
            hover_color="#7B1FA2"
        )
        self.grid_view_btn.pack(side="left", padx=3)
        
        self.list_view_btn = ctk.CTkButton(
            view_frame,
            text="📝 Vista Lista",
            command=lambda: self.set_view("list"),
            height=28,
            width=100,
            font=ctk.CTkFont(size=10),
            fg_color="#607D8B",
            hover_color="#455A64"
        )
        self.list_view_btn.pack(side="left", padx=3)
        
        # Búsqueda local
        local_search_frame = ctk.CTkFrame(view_frame, fg_color="transparent")
        local_search_frame.pack(side="right", padx=3)
        
        ctk.CTkLabel(local_search_frame, text="🔍 Filtro local:", font=ctk.CTkFont(size=10)).pack(side="left", padx=3)
        
        self.local_search_entry = ctk.CTkEntry(
            local_search_frame,
            placeholder_text="Filtrar mods...",
            height=28,
            width=150,
            font=ctk.CTkFont(size=10)
        )
        self.local_search_entry.pack(side="left", padx=3)
        self.local_search_entry.bind("<KeyRelease>", self.on_local_search_change)
    
    def create_stats_frame(self, parent):
        """Crear frame de estadísticas rápidas"""
        stats_frame = ctk.CTkFrame(parent, corner_radius=8)
        stats_frame.pack(fill="x", padx=5, pady=5)
        
        # Título de estadísticas
        stats_title = ctk.CTkLabel(
            stats_frame,
            text="📊 Estadísticas Rápidas",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        stats_title.pack(pady=5)
        
        # Frame de estadísticas
        stats_content_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_content_frame.pack(fill="x", padx=8, pady=5)
        
        # Estadísticas en columnas
        self.favorites_count_label = ctk.CTkLabel(
            stats_content_frame,
            text="⭐ Favoritos: 0",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#FF9800",
            corner_radius=6,
            padx=10,
            pady=5
        )
        self.favorites_count_label.pack(side="left", padx=5)
        
        self.installed_count_label = ctk.CTkLabel(
            stats_content_frame,
            text="📦 Instalados: 0",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#2196F3",
            corner_radius=6,
            padx=10,
            pady=5
        )
        self.installed_count_label.pack(side="left", padx=5)
        
        self.search_count_label = ctk.CTkLabel(
            stats_content_frame,
            text="🔍 Resultados: 0",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#4CAF50",
            corner_radius=6,
            padx=10,
            pady=5
        )
        self.search_count_label.pack(side="left", padx=5)
    
    def create_mods_display_frame(self, parent):
        """Crear frame principal para mostrar mods"""
        self.mods_display_frame = ctk.CTkFrame(parent, corner_radius=8)
        self.mods_display_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Título dinámico
        self.mods_title_label = ctk.CTkLabel(
            self.mods_display_frame,
            text="📋 Mods Disponibles",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.mods_title_label.pack(pady=5)
        
        # Frame para el contenido de mods
        self.mods_content_frame = ctk.CTkFrame(self.mods_display_frame, fg_color="transparent")
        self.mods_content_frame.pack(fill="both", expand=True, padx=8, pady=5)
        
        # Configurar grid para vista en cuadrícula
        self.mods_content_frame.grid_columnconfigure(0, weight=1)
        self.mods_content_frame.grid_columnconfigure(1, weight=1)
        self.mods_content_frame.grid_columnconfigure(2, weight=1)
        self.mods_content_frame.grid_columnconfigure(3, weight=1)
    
    def create_installed_info_frame(self, parent):
        """Crear frame de información de mods instalados"""
        installed_info_frame = ctk.CTkFrame(parent, corner_radius=8)
        installed_info_frame.pack(fill="x", padx=5, pady=5)
        
        # Título
        info_title = ctk.CTkLabel(
            installed_info_frame,
            text="⚙️ Configuración del Servidor",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        info_title.pack(pady=5)
        
        # Frame de contenido
        content_frame = ctk.CTkFrame(installed_info_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=8, pady=5)
        
        # Información del servidor actual
        server_info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        server_info_frame.pack(fill="x", pady=3)
        
        ctk.CTkLabel(
            server_info_frame,
            text="🎮 Servidor:",
            font=ctk.CTkFont(size=10, weight="bold")
        ).pack(side="left", padx=3)
        
        self.server_info_label = ctk.CTkLabel(
            server_info_frame,
            text="No seleccionado",
            font=ctk.CTkFont(size=10),
            fg_color="#FF9800",
            corner_radius=4,
            padx=6,
            pady=2
        )
        self.server_info_label.pack(side="left", padx=3)
        
        # Entry con los IDs de mods
        mods_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        mods_frame.pack(fill="x", pady=3)
        
        ctk.CTkLabel(
            mods_frame,
            text="📋 IDs de Mods:",
            font=ctk.CTkFont(size=10, weight="bold")
        ).pack(side="left", padx=3)
        
        self.mods_ids_entry = ctk.CTkEntry(
            mods_frame,
            placeholder_text="IDs separados por comas (ej: 956565,854554)",
            height=28,
            font=ctk.CTkFont(size=10)
        )
        self.mods_ids_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Botones de acción
        buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=3)
        
        apply_button = ctk.CTkButton(
            buttons_frame,
            text="✅ Aplicar al Servidor",
            command=self.apply_mods_to_server,
            height=28,
            width=120,
            font=ctk.CTkFont(size=10),
            fg_color="#4CAF50",
            hover_color="#388E3C"
        )
        apply_button.pack(side="left", padx=3)
        
        clear_button = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Limpiar Mods",
            command=self.clear_mods,
            height=28,
            width=100,
            font=ctk.CTkFont(size=10),
            fg_color="#f44336",
            hover_color="#d32f2f"
        )
        clear_button.pack(side="left", padx=3)
        
        # NUEVO: Botón para limpiar duplicados
        clear_duplicates_button = ctk.CTkButton(
            buttons_frame,
            text="🧹 Limpiar Duplicados",
            command=self.clean_duplicates_manually,
            height=28,
            width=130,
            font=ctk.CTkFont(size=10),
            fg_color="#9C27B0",
            hover_color="#7B1FA2"
        )
        clear_duplicates_button.pack(side="left", padx=3)
        
        refresh_button = ctk.CTkButton(
            buttons_frame,
            text="🔄 Actualizar",
            command=self.refresh_mods_display,
            height=28,
            width=100,
            font=ctk.CTkFont(size=10),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        refresh_button.pack(side="left", padx=3)
    
    def set_filter(self, filter_type):
        """Establecer filtro activo"""
        self.current_filter = filter_type
        
        # Actualizar colores de botones
        self.all_filter_btn.configure(fg_color="#607D8B")
        self.favorites_filter_btn.configure(fg_color="#607D8B")
        self.installed_filter_btn.configure(fg_color="#607D8B")
        
        if filter_type == "all":
            self.all_filter_btn.configure(fg_color="#4CAF50")
        elif filter_type == "favorites":
            self.favorites_filter_btn.configure(fg_color="#FF9800")
        elif filter_type == "installed":
            self.installed_filter_btn.configure(fg_color="#2196F3")
        
        # Actualizar título y contenido
        self.refresh_mods_display()
    
    def set_view(self, view_type):
        """Establecer tipo de vista"""
        self.current_view = view_type
        
        # Actualizar colores de botones
        self.grid_view_btn.configure(fg_color="#607D8B")
        self.list_view_btn.configure(fg_color="#607D8B")
        
        if view_type == "grid":
            self.grid_view_btn.configure(fg_color="#9C27B0")
        else:
            self.list_view_btn.configure(fg_color="#9C27B0")
        
        # Actualizar vista
        self.refresh_mods_display()
    
    def on_local_search_change(self, event=None):
        """Filtrar mods localmente"""
        self.search_filter = self.local_search_entry.get().lower()
        self.refresh_mods_display()
    
    def refresh_mods_display(self):
        """Refrescar la visualización de mods"""
        try:
            # Limpiar contenido anterior
            for widget in self.mods_content_frame.winfo_children():
                widget.destroy()
            
            # Obtener mods según el filtro
            mods_to_show = self.get_mods_for_current_filter()
            
            # Aplicar filtro local
            if self.search_filter:
                mods_to_show = [mod for mod in mods_to_show 
                              if self.search_filter in mod.get("name", "").lower() 
                              or self.search_filter in mod.get("summary", "").lower()]
            
            # Actualizar título y estadísticas
            self.update_display_title(len(mods_to_show))
            self.update_stats()
            
            if not mods_to_show:
                self.show_empty_state()
                return
            
            # Mostrar mods según la vista
            if self.current_view == "grid":
                self.display_mods_grid(mods_to_show)
            else:
                self.display_mods_list(mods_to_show)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al refrescar visualización: {e}")
    
    def get_mods_for_current_filter(self):
        """Obtener mods según el filtro actual"""
        if self.current_filter == "favorites":
            return self.favorite_mods
        elif self.current_filter == "installed":
            return self.installed_mods
        elif self.current_filter == "search":
            return self.search_results
        else:  # "all"
            all_mods = []
            all_mods.extend(self.favorite_mods)
            all_mods.extend(self.installed_mods)
            all_mods.extend(self.search_results)
            # Eliminar duplicados
            seen_ids = set()
            unique_mods = []
            for mod in all_mods:
                mod_id = str(mod.get("id", ""))
                if mod_id not in seen_ids:
                    seen_ids.add(mod_id)
                    unique_mods.append(mod)
            return unique_mods
    
    def update_display_title(self, count):
        """Actualizar título de la visualización"""
        filter_names = {
            "all": "Todos los Mods",
            "favorites": "Mods Favoritos",
            "installed": "Mods Instalados",
            "search": "Resultados de Búsqueda"
        }
        
        title = f"📋 {filter_names.get(self.current_filter, 'Mods')} ({count})"
        self.mods_title_label.configure(text=title)
    
    def update_stats(self):
        """Actualizar estadísticas"""
        self.favorites_count_label.configure(text=f"⭐ Favoritos: {len(self.favorite_mods)}")
        self.installed_count_label.configure(text=f"📦 Instalados: {len(self.installed_mods)}")
        self.search_count_label.configure(text=f"🔍 Resultados: {len(self.search_results)}")
        
        # Actualizar información del servidor
        if self.current_server and self.current_map:
            self.server_info_label.configure(text=f"{self.current_server} - {self.current_map}")
        else:
            self.server_info_label.configure(text="No seleccionado")
    
    def show_empty_state(self):
        """Mostrar estado vacío"""
        empty_frame = ctk.CTkFrame(self.mods_content_frame, fg_color="transparent")
        empty_frame.pack(expand=True, pady=50)
        
        empty_label = ctk.CTkLabel(
            empty_frame,
            text="📭 No hay mods para mostrar\n\n" + 
                 ("💡 Busca mods usando la barra de búsqueda" if self.current_filter == "all" else
                  "⭐ Marca mods como favoritos desde la búsqueda" if self.current_filter == "favorites" else
                  "📦 Instala mods desde la búsqueda" if self.current_filter == "installed" else
                  "🔍 No se encontraron resultados para tu búsqueda"),
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        empty_label.pack()
    
    def display_mods_grid(self, mods):
        """Mostrar mods en vista de cuadrícula"""
        row = 0
        col = 0
        max_cols = 4
        
        for mod in mods:
            mod_card = self.create_compact_mod_card(mod)
            mod_card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def display_mods_list(self, mods):
        """Mostrar mods en vista de lista"""
        for mod in mods:
            mod_card = self.create_list_mod_card(mod)
            mod_card.pack(fill="x", padx=5, pady=5)
    
    def create_compact_mod_card(self, mod):
        """Crear tarjeta compacta para vista de cuadrícula"""
        # Frame principal
        mod_frame = ctk.CTkFrame(self.mods_content_frame, corner_radius=6, border_width=1)
        
        # Información del mod
        mod_id = mod.get("id", "")
        mod_name = mod.get("name", "Sin nombre")
        download_count = mod.get("downloadCount", 0)
        
        # Header con nombre
        name_label = ctk.CTkLabel(
            mod_frame,
            text=mod_name[:20] + "..." if len(mod_name) > 20 else mod_name,
            font=ctk.CTkFont(size=10, weight="bold"),
            anchor="w"
        )
        name_label.pack(anchor="w", padx=5, pady=(5, 1))
        
        # ID del mod
        id_label = ctk.CTkLabel(
            mod_frame,
            text=f"ID: {mod_id}",
            font=ctk.CTkFont(size=8),
            text_color=("gray", "lightgray")
        )
        id_label.pack(anchor="w", padx=5, pady=1)
        
        # Estadísticas
        stats_frame = ctk.CTkFrame(mod_frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=5, pady=1)
        
        downloads_label = ctk.CTkLabel(
            stats_frame,
            text=f"📥 {download_count:,}",
            font=ctk.CTkFont(size=8),
            fg_color="#2196F3",
            corner_radius=2,
            padx=3,
            pady=1
        )
        downloads_label.pack(side="left")
        
        # Estado del mod
        is_favorite = any(str(fav.get("id", "")) == str(mod_id) for fav in self.favorite_mods)
        is_installed = any(str(inst.get("id", "")) == str(mod_id) for inst in self.installed_mods)
        
        if is_favorite:
            fav_label = ctk.CTkLabel(
                stats_frame,
                text="⭐",
                font=ctk.CTkFont(size=10)
            )
            fav_label.pack(side="right", padx=1)
        
        if is_installed:
            inst_label = ctk.CTkLabel(
                stats_frame,
                text="📦",
                font=ctk.CTkFont(size=10)
            )
            inst_label.pack(side="right", padx=1)
        
        # Botones de acción
        buttons_frame = ctk.CTkFrame(mod_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=5, pady=(3, 5))
        
        # Botón de favorito
        fav_btn = ctk.CTkButton(
            buttons_frame,
            text="⭐" if not is_favorite else "💛",
            command=lambda m=mod: self.toggle_favorite(m),
            width=24,
            height=20,
            font=ctk.CTkFont(size=8),
            fg_color="#FFD700" if is_favorite else "#4A4A4A",
            hover_color="#FFC107" if is_favorite else "#666666"
        )
        fav_btn.pack(side="left", padx=1)
        
        # Botón de instalar/desinstalar
        if is_installed:
            install_btn = ctk.CTkButton(
                buttons_frame,
                text="✅",
                command=lambda m=mod: self.uninstall_mod(m),
                width=24,
                height=20,
                font=ctk.CTkFont(size=8),
                fg_color="#2E7D32",
                hover_color="#1B5E20"
            )
            install_btn.pack(side="left", padx=1)
        else:
            install_btn = ctk.CTkButton(
                buttons_frame,
                text="📥",
                command=lambda m=mod: self.install_mod(m),
                width=24,
                height=20,
                font=ctk.CTkFont(size=8),
                fg_color="#1976D2",
                hover_color="#1565C0"
            )
            install_btn.pack(side="left", padx=1)
        
        # Botón de información
        info_btn = ctk.CTkButton(
            buttons_frame,
            text="ℹ️",
            command=lambda m=mod: self.show_mod_info(m),
            width=24,
            height=20,
            font=ctk.CTkFont(size=8),
            fg_color="#9C27B0",
            hover_color="#7B1FA2"
        )
        info_btn.pack(side="left", padx=1)
        
        return mod_frame
    
    def create_list_mod_card(self, mod):
        """Crear tarjeta de lista para vista de lista"""
        # Frame principal
        mod_frame = ctk.CTkFrame(self.mods_content_frame, corner_radius=6, border_width=1)
        
        # Frame de contenido horizontal
        content_frame = ctk.CTkFrame(mod_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=6, pady=5)
        
        # Información del mod
        mod_id = mod.get("id", "")
        mod_name = mod.get("name", "Sin nombre")
        mod_summary = mod.get("summary", "Sin descripción")
        download_count = mod.get("downloadCount", 0)
        
        # Columna izquierda - Información
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)
        
        # Nombre del mod
        name_label = ctk.CTkLabel(
            info_frame,
            text=f"🎮 {mod_name}",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")
        
        # Descripción
        if mod_summary:
            desc_text = mod_summary[:80] + "..." if len(mod_summary) > 80 else mod_summary
            desc_label = ctk.CTkLabel(
                info_frame,
                text=desc_text,
                font=ctk.CTkFont(size=9),
                anchor="w",
                text_color=("gray", "lightgray")
            )
            desc_label.pack(anchor="w", pady=1)
        
        # Estadísticas
        stats_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        stats_frame.pack(anchor="w", pady=3)
        
        # ID del mod
        id_label = ctk.CTkLabel(
            stats_frame,
            text=f"ID: {mod_id}",
            font=ctk.CTkFont(size=8, weight="bold"),
            fg_color="#607D8B",
            corner_radius=2,
            padx=4,
            pady=1
        )
        id_label.pack(side="left", padx=(0, 3))
        
        # Descargas
        downloads_label = ctk.CTkLabel(
            stats_frame,
            text=f"📥 {download_count:,}",
            font=ctk.CTkFont(size=8),
            fg_color="#2196F3",
            corner_radius=2,
            padx=4,
            pady=1
        )
        downloads_label.pack(side="left", padx=(0, 3))
        
        # Estado del mod
        is_favorite = any(fav.get("id") == str(mod_id) for fav in self.favorite_mods)
        is_installed = any(inst.get("id") == str(mod_id) for inst in self.installed_mods)
        
        if is_favorite:
            fav_status = ctk.CTkLabel(
                stats_frame,
                text="⭐",
                font=ctk.CTkFont(size=8),
                fg_color="#FF9800",
                corner_radius=2,
                padx=4,
                pady=1
            )
            fav_status.pack(side="left", padx=(0, 3))
        
        if is_installed:
            inst_status = ctk.CTkLabel(
                stats_frame,
                text="📦",
                font=ctk.CTkFont(size=8),
                fg_color="#4CAF50",
                corner_radius=2,
                padx=4,
                pady=1
            )
            inst_status.pack(side="left", padx=(0, 3))
        
        # Columna derecha - Botones
        buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(side="right", padx=(6, 0))
        
        # Botón de favorito
        fav_btn = ctk.CTkButton(
            buttons_frame,
            text="⭐" if not is_favorite else "💛",
            command=lambda m=mod: self.toggle_favorite(m),
            width=24,
            height=20,
            font=ctk.CTkFont(size=8),
            fg_color="#FFD700" if is_favorite else "#4A4A4A",
            hover_color="#FFC107" if is_favorite else "#666666"
        )
        fav_btn.pack(pady=1)
        
        # Botón de instalar/desinstalar
        if is_installed:
            install_btn = ctk.CTkButton(
                buttons_frame,
                text="✅",
                command=lambda m=mod: self.uninstall_mod(m),
                width=24,
                height=20,
                font=ctk.CTkFont(size=8),
                fg_color="#2E7D32",
                hover_color="#1B5E20"
            )
            install_btn.pack(pady=1)
        else:
            install_btn = ctk.CTkButton(
                buttons_frame,
                text="📥",
                command=lambda m=mod: self.install_mod(m),
                width=24,
                height=20,
                font=ctk.CTkFont(size=8),
                fg_color="#1976D2",
                hover_color="#1565C0"
            )
            install_btn.pack(pady=1)
        
        # Botón de información
        info_btn = ctk.CTkButton(
            buttons_frame,
            text="ℹ️",
            command=lambda m=mod: self.show_mod_info(m),
            width=24,
            height=20,
            font=ctk.CTkFont(size=8),
            fg_color="#9C27B0",
            hover_color="#7B1FA2"
        )
        info_btn.pack(pady=1)
        
        return mod_frame
    
    def show_mod_info(self, mod):
        """Mostrar información detallada del mod"""
        # Crear ventana de información
        info_window = ctk.CTkToplevel(self)
        info_window.title(f"Información del Mod: {mod.get('name', 'Sin nombre')}")
        info_window.geometry("600x500")
        info_window.resizable(False, False)
        
        # Frame principal
        main_frame = ctk.CTkFrame(info_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text=f"🎮 {mod.get('name', 'Sin nombre')}",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Información del mod
        info_text = f"""
📋 ID: {mod.get('id', 'N/A')}
📥 Descargas: {mod.get('downloadCount', 0):,}
📅 Última modificación: {mod.get('dateModified', 'N/A')}
🔗 Categoría: {mod.get('categorySection', {}).get('name', 'N/A')}

📝 Descripción:
{mod.get('summary', 'Sin descripción')}

🌐 Enlaces:
• CurseForge: https://www.curseforge.com/ark-survival-ascended/mods/{mod.get('slug', '')}
        """
        
        info_label = ctk.CTkLabel(
            main_frame,
            text=info_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        info_label.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Botones de acción
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=20)
        
        # Botón de abrir en navegador
        open_btn = ctk.CTkButton(
            buttons_frame,
            text="🌐 Abrir en CurseForge",
            command=lambda: self.open_curseforge_page(mod),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        open_btn.pack(side="left", padx=5)
        
        # Botón de copiar ID
        copy_btn = ctk.CTkButton(
            buttons_frame,
            text="📋 Copiar ID",
            command=lambda: self.copy_mod_id(mod),
            fg_color="#4CAF50",
            hover_color="#388E3C"
        )
        copy_btn.pack(side="left", padx=5)
        
        # Botón de cerrar
        close_btn = ctk.CTkButton(
            buttons_frame,
            text="❌ Cerrar",
            command=info_window.destroy,
            fg_color="#f44336",
            hover_color="#d32f2f"
        )
        close_btn.pack(side="right", padx=5)
    
    def search_mods(self):
        """Buscar mods en CurseForge"""
        query = self.search_entry.get().strip()
        if not query:
            self.show_message("❌ Ingresa un término de búsqueda", "error")
            return
            
        # Mostrar indicador de carga
        self.search_status_label.configure(text="🔄 Buscando mods...")
        
        # Realizar búsqueda en hilo separado
        threading.Thread(target=self._search_mods_thread, args=(query,), daemon=True).start()
        
    def _search_mods_thread(self, query):
        """Hilo para buscar mods"""
        try:
            headers = {
                "x-api-key": self.api_key,
                "Accept": "application/json"
            }
            
            params = {
                "gameId": self.game_id,
                "searchFilter": query,
                "sortField": 6,  # Popularidad
                "sortOrder": "desc",
                "pageSize": 20
            }
            
            response = requests.get(f"{self.base_url}/mods/search", headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                mods = data.get("data", [])
                
                # Actualizar UI en hilo principal
                self._safe_schedule_ui_update(lambda: self.display_search_results(mods))
            else:
                self._safe_schedule_ui_update(lambda: self.search_status_label.configure(f"❌ Error en la búsqueda: {response.status_code}"))
                
        except Exception as e:
            self.logger.error(f"Error al buscar mods: {e}")
            self._safe_schedule_ui_update(lambda: self.search_status_label.configure("❌ Error de conexión"))
            
    def load_popular_mods(self):
        """Cargar mods populares"""
        self.search_status_label.configure(text="🔄 Cargando mods populares...")
        threading.Thread(target=self._load_popular_mods_thread, daemon=True).start()
        
    def _load_popular_mods_thread(self):
        """Hilo para cargar mods populares"""
        try:
            headers = {
                "x-api-key": self.api_key,
                "Accept": "application/json"
            }
            
            params = {
                "gameId": self.game_id,
                "sortField": 6,  # Popularidad
                "sortOrder": "desc",
                "pageSize": 20
            }
            
            response = requests.get(f"{self.base_url}/mods/search", headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                mods = data.get("data", [])
                
                # Actualizar UI en hilo principal
                self._safe_schedule_ui_update(lambda: self.display_search_results(mods))
            else:
                self._safe_schedule_ui_update(lambda: self.search_status_label.configure(f"❌ Error al cargar mods populares: {response.status_code}"))
                
        except Exception as e:
            self.logger.error(f"Error al cargar mods populares: {e}")
            self._safe_schedule_ui_update(lambda: self.search_status_label.configure("❌ Error de conexión"))
    
    def display_search_results(self, mods):
        """Mostrar resultados de búsqueda"""
        # Guardar los resultados actuales
        self.search_results = mods
        
        # Actualizar la pestaña de resultados
        self.set_filter("search")
        self.refresh_mods_display()
        
        # Actualizar estadísticas
        self.update_stats()
        
        # Mostrar mensaje de bienvenida
        if self.search_results:
            status_msg = "✅ Mods encontrados: "
            status_msg += f"{len(self.search_results)} mods"
            self.show_message(status_msg, "success")
        else:
            self.show_message("💡 No se encontraron mods para tu búsqueda.", "info")
    
    def install_mod(self, mod):
        """Instalar mod"""
        try:
            mod_id = str(mod.get("id", ""))
            mod_name = mod.get("name", "Sin nombre")
            
            # Verificar si ya está instalado
            if any(inst.get("id") == mod_id for inst in self.installed_mods):
                self.show_message(f"⚠️ El mod '{mod_name}' ya está instalado", "warning")
                return
            
            # Agregar a la lista de instalados
            self.installed_mods.append(mod)
            self.save_installed_mods()
            
            # Actualizar entrada de IDs
            self.update_mods_ids_entry()
            
            # Actualizar visualización
            self.refresh_mods_display()
            self.update_stats()
            
            self.show_message(f"✅ Mod '{mod_name}' instalado correctamente", "success")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al instalar mod: {e}")
            self.show_message(f"❌ Error al instalar mod: {e}", "error")
    
    def uninstall_mod(self, mod):
        """Desinstalar mod"""
        try:
            mod_id = str(mod.get("id", ""))
            mod_name = mod.get("name", "Sin nombre")
            
            # Remover de la lista de instalados - mejorar comparación
            self.installed_mods = [inst for inst in self.installed_mods if str(inst.get("id", "")) != mod_id]
            self.save_installed_mods()
            
            # Actualizar entrada de IDs
            self.update_mods_ids_entry()
            
            # Actualizar visualización
            self.refresh_mods_display()
            self.update_stats()
            
            self.show_message(f"✅ Mod '{mod_name}' desinstalado correctamente", "success")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al desinstalar mod: {e}")
            self.show_message(f"❌ Error al desinstalar mod: {e}", "error")
    
    def toggle_favorite(self, mod):
        """Alternar estado de favorito"""
        try:
            mod_id = str(mod.get("id", ""))
            mod_name = mod.get("name", "Sin nombre")
            
            # Verificar si ya está en favoritos - mejorar comparación
            is_favorite = any(str(fav.get("id", "")) == mod_id for fav in self.favorite_mods)
            
            if is_favorite:
                # Remover de favoritos
                self.favorite_mods = [fav for fav in self.favorite_mods if str(fav.get("id", "")) != mod_id]
                self.save_favorite_mods()
                self.show_message(f"💔 Mod '{mod_name}' removido de favoritos", "info")
            else:
                # Agregar a favoritos
                self.favorite_mods.append(mod)
                self.save_favorite_mods()
                self.show_message(f"⭐ Mod '{mod_name}' agregado a favoritos", "success")
            
            # Actualizar visualización
            self.refresh_mods_display()
            self.update_stats()
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al alternar favorito: {e}")
            self.show_message(f"❌ Error al alternar favorito: {e}", "error")
    
    def open_curseforge_page(self, mod):
        """Abrir página del mod en CurseForge"""
        try:
            mod_slug = mod.get("slug", "")
            if mod_slug:
                url = f"https://www.curseforge.com/ark-survival-ascended/mods/{mod_slug}"
                webbrowser.open(url)
            else:
                self.show_message("❌ No se pudo abrir la página del mod", "error")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al abrir página del mod: {e}")
            self.show_message(f"❌ Error al abrir página: {e}", "error")
    
    def copy_mod_id(self, mod):
        """Copiar ID del mod al portapapeles"""
        try:
            mod_id = str(mod.get("id", ""))
            if mod_id:
                self.clipboard_clear()
                self.clipboard_append(mod_id)
                self.show_message(f"📋 ID del mod copiado: {mod_id}", "success")
            else:
                self.show_message("❌ No se pudo copiar el ID del mod", "error")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al copiar ID del mod: {e}")
            self.show_message(f"❌ Error al copiar ID: {e}", "error")
    
    def refresh_favorites_tab(self):
        """Actualizar pestaña de favoritos (método legacy para compatibilidad)"""
        # Este método ya no se usa, pero se mantiene para compatibilidad
        pass
    
    def create_favorite_card(self, parent, mod):
        """Crear tarjeta de favorito (método legacy para compatibilidad)"""
        # Este método ya no se usa, pero se mantiene para compatibilidad
        pass
    
    def remove_favorite(self, mod):
        """Remover de favoritos (método legacy para compatibilidad)"""
        # Este método ya no se usa, pero se mantiene para compatibilidad
        pass
    
    def refresh_installed_tab(self):
        """Actualizar pestaña de instalados (método legacy para compatibilidad)"""
        # Este método ya no se usa, pero se mantiene para compatibilidad
        pass
    
    def create_installed_card(self, parent, mod):
        """Crear tarjeta de instalado (método legacy para compatibilidad)"""
        # Este método ya no se usa, pero se mantiene para compatibilidad
        pass
    
    def uninstall_mod_from_search(self, mod):
        """Desinstalar mod desde resultados de búsqueda (método legacy para compatibilidad)"""
        # Este método ya no se usa, pero se mantiene para compatibilidad
        pass
    
    def install_mod_and_refresh(self, mod, buttons_frame):
        """Instalar mod y refrescar (método legacy para compatibilidad)"""
        # Este método ya no se usa, pero se mantiene para compatibilidad
        pass
    
    def uninstall_mod_from_search_and_refresh(self, mod, buttons_frame):
        """Desinstalar mod y refrescar (método legacy para compatibilidad)"""
        # Este método ya no se usa, pero se mantiene para compatibilidad
        pass
    
    def toggle_favorite_and_refresh(self, mod, buttons_frame):
        """Alternar favorito y refrescar (método legacy para compatibilidad)"""
        # Este método ya no se usa, pero se mantiene para compatibilidad
        pass
    
    def refresh_mod_card_buttons(self, mod, buttons_frame):
        """Refrescar botones de tarjeta de mod (método legacy para compatibilidad)"""
        # Este método ya no se usa, pero se mantiene para compatibilidad
        pass
    
    def install_mod_and_refresh_favorites(self, mod):
        """Instalar mod y refrescar favoritos (método legacy para compatibilidad)"""
        # Este método ya no se usa, pero se mantiene para compatibilidad
        pass
    
    def uninstall_mod_and_refresh_favorites(self, mod):
        """Desinstalar mod y refrescar favoritos (método legacy para compatibilidad)"""
        # Este método ya no se usa, pero se mantiene para compatibilidad
        pass
    
    def update_mods_ids_entry(self):
        """Actualizar el campo de IDs de mods"""
        mod_ids = [str(mod.get("id", "")) for mod in self.installed_mods if mod.get("id")]
        ids_text = ",".join(mod_ids)
        
        self.mods_ids_entry.delete(0, "end")
        if ids_text:
            self.mods_ids_entry.insert(0, ids_text)
            
    def apply_mods_to_server(self):
        """Aplicar mods al servidor"""
        try:
            # Obtener IDs de mods instalados
            mod_ids = [str(mod.get("id", "")) for mod in self.installed_mods if mod.get("id")]
            
            if not mod_ids:
                self.show_message("⚠️ No hay mods instalados para aplicar", "warning")
                return
            
            # Actualizar entrada de IDs
            self.mods_ids_entry.delete(0, "end")
            self.mods_ids_entry.insert(0, ",".join(mod_ids))
            
            # Actualizar configuración específica del servidor/mapa
            if self.config_manager and self.current_server and self.current_map:
                server_map_key = f"{self.current_server}_{self.current_map}"
                config_key = f"mod_ids_{server_map_key}"
                
                # Guardar en la configuración específica del servidor/mapa
                self.config_manager.set("server", config_key, ",".join(mod_ids))
                
                if self.logger:
                    self.logger.info(f"Mods aplicados a {self.current_server} - {self.current_map}: {','.join(mod_ids)}")
            else:
                # Solo aplicar a configuración general si no hay contexto específico
                # Esto debería ser raro, normalmente siempre hay un servidor/mapa seleccionado
                if self.config_manager:
                    if self.logger:
                        self.logger.warning("No hay contexto de servidor/mapa específico, aplicando a configuración general")
                    self.config_manager.set("server", "mod_ids", ",".join(mod_ids))
                    
                if self.logger:
                    self.logger.info(f"Mods aplicados a configuración general: {','.join(mod_ids)}")
            
            self.show_message(f"✅ {len(mod_ids)} mods aplicados al servidor", "success")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al aplicar mods: {e}")
            self.show_message(f"❌ Error al aplicar mods: {e}", "error")
    
    def apply_mods_to_server_silently(self):
        """Aplicar mods al servidor sin mostrar mensajes (para uso automático)"""
        try:
            # Obtener IDs de mods instalados
            mod_ids = [str(mod.get("id", "")) for mod in self.installed_mods if mod.get("id")]
            
            if not mod_ids:
                return
            
            # Actualizar entrada de IDs
            self.mods_ids_entry.delete(0, "end")
            self.mods_ids_entry.insert(0, ",".join(mod_ids))
            
            # Actualizar configuración específica del servidor/mapa
            if self.config_manager and self.current_server and self.current_map:
                server_map_key = f"{self.current_server}_{self.current_map}"
                config_key = f"mod_ids_{server_map_key}"
                
                # Guardar en la configuración específica del servidor/mapa
                self.config_manager.set("server", config_key, ",".join(mod_ids))
                
                if self.logger:
                    self.logger.info(f"Mods aplicados automáticamente a {self.current_server} - {self.current_map}: {','.join(mod_ids)}")
            else:
                # Solo aplicar a configuración general si no hay contexto específico
                # Esto debería ser raro, normalmente siempre hay un servidor/mapa seleccionado
                if self.config_manager:
                    if self.logger:
                        self.logger.warning("No hay contexto de servidor/mapa específico, aplicando automáticamente a configuración general")
                    self.config_manager.set("server", "mod_ids", ",".join(mod_ids))
                    
                if self.logger:
                    self.logger.info(f"Mods aplicados automáticamente a configuración general: {','.join(mod_ids)}")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al aplicar mods automáticamente: {e}")
    
    def clear_mods(self):
        """Limpiar todos los mods"""
        try:
            if not self.installed_mods:
                self.show_message("ℹ️ No hay mods instalados para limpiar", "info")
                return
            
            # Confirmar acción
            if messagebox.askyesno("Confirmar Limpieza", 
                                  f"¿Estás seguro de que quieres remover todos los {len(self.installed_mods)} mods instalados?"):
                
                # Limpiar lista de instalados
                self.installed_mods.clear()
                self.save_installed_mods()
                
                # Limpiar entrada de IDs
                self.mods_ids_entry.delete(0, "end")
                
                # Limpiar configuración específica del servidor/mapa
                if self.config_manager and self.current_server and self.current_map:
                    server_map_key = f"{self.current_server}_{self.current_map}"
                    config_key = f"mod_ids_{server_map_key}"
                    
                    # Limpiar la configuración específica del servidor/mapa
                    self.config_manager.set("server", config_key, "")
                    
                    if self.logger:
                        self.logger.info(f"Configuración de mods limpiada para {self.current_server} - {self.current_map}")
                else:
                    # Solo limpiar configuración general si no hay contexto específico
                    # Esto debería ser raro, normalmente siempre hay un servidor/mapa seleccionado
                    if self.config_manager:
                        if self.logger:
                            self.logger.warning("No hay contexto de servidor/mapa específico, limpiando configuración general")
                        self.config_manager.set("server", "mod_ids", "")
                        
                    if self.logger:
                        self.logger.info("Configuración general de mods limpiada")
                
                # Actualizar visualización
                self.refresh_mods_display()
                self.update_stats()
                
                self.show_message("🧹 Lista de mods limpiada completamente", "success")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al limpiar mods: {e}")
            self.show_message(f"❌ Error al limpiar mods: {e}", "error")
    
    def clear_mods_silently(self):
        """Limpiar configuración de mods sin mostrar mensajes (para uso automático)"""
        try:
            # Limpiar entrada de IDs
            self.mods_ids_entry.delete(0, "end")
            
            # Limpiar configuración específica del servidor/mapa
            if self.config_manager and self.current_server and self.current_map:
                server_map_key = f"{self.current_server}_{self.current_map}"
                config_key = f"mod_ids_{server_map_key}"
                
                # Limpiar la configuración específica del servidor/mapa
                self.config_manager.set("server", config_key, "")
                
                if self.logger:
                    self.logger.info(f"Configuración de mods limpiada automáticamente para {self.current_server} - {self.current_map}")
            else:
                # Solo limpiar configuración general si no hay contexto específico
                # Esto debería ser raro, normalmente siempre hay un servidor/mapa seleccionado
                if self.config_manager:
                    if self.logger:
                        self.logger.warning("No hay contexto de servidor/mapa específico, limpiando automáticamente configuración general")
                    self.config_manager.set("server", "mod_ids", "")
                    
                if self.logger:
                    self.logger.info("Configuración general de mods limpiada automáticamente")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al limpiar mods automáticamente: {e}")
    
    def remove_duplicate_mods(self):
        """Remover mods duplicados basándose en su ID"""
        try:
            if not self.installed_mods:
                return 0
            
            # Identificar duplicados
            seen_ids = set()
            unique_mods = []
            duplicates_count = 0
            
            for mod in self.installed_mods:
                mod_id = str(mod.get("id", ""))
                if mod_id and mod_id not in seen_ids:
                    seen_ids.add(mod_id)
                    unique_mods.append(mod)
                elif mod_id:
                    duplicates_count += 1
            
            # Actualizar lista solo si hay duplicados
            if duplicates_count > 0:
                self.installed_mods = unique_mods
                self.save_installed_mods()
                
                if self.logger:
                    self.logger.info(f"Eliminados {duplicates_count} mods duplicados. Mods únicos: {len(unique_mods)}")
            
            return duplicates_count
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al remover mods duplicados: {e}")
            return 0

    def clean_duplicates_manually(self):
        """Limpiar duplicados manualmente (llamado por el botón)"""
        try:
            duplicates_removed = self.remove_duplicate_mods()
            
            if duplicates_removed > 0:
                # Actualizar visualización
                self.refresh_mods_display()
                self.update_mods_ids_entry()
                self.update_stats()
                
                self.show_message(f"🧹 Se eliminaron {duplicates_removed} mods duplicados", "success")
            else:
                self.show_message("ℹ️ No se encontraron mods duplicados", "info")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al limpiar duplicados manualmente: {e}")
            self.show_message(f"❌ Error al limpiar duplicados: {e}", "error")

    def _clean_duplicates_internal(self):
        """Eliminar duplicados en listas basadas en ID; devuelve (rem_fav, rem_inst)"""
        removed_fav = 0
        removed_inst = 0
        try:
            # Favoritos
            seen = set()
            new_favs = []
            for m in self.favorite_mods:
                mid = str(m.get("id", ""))
                if mid and mid not in seen:
                    seen.add(mid)
                    new_favs.append(m)
            removed_fav = max(0, len(self.favorite_mods) - len(new_favs))
            self.favorite_mods = new_favs

            # Instalados
            seen = set()
            new_inst = []
            for m in self.installed_mods:
                mid = str(m.get("id", ""))
                if mid and mid not in seen:
                    seen.add(mid)
                    new_inst.append(m)
            removed_inst = max(0, len(self.installed_mods) - len(new_inst))
            self.installed_mods = new_inst
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error interno al limpiar duplicados: {e}")
        return removed_fav, removed_inst

    def load_current_server_map(self):
        """Cargar servidor y mapa actuales"""
        try:
            # Obtener del MainWindow si está disponible
            if hasattr(self.main_window, 'selected_server') and self.main_window.selected_server:
                self.current_server = self.main_window.selected_server
                
                # Obtener mapa del servidor
                if hasattr(self.main_window, 'selected_map') and self.main_window.selected_map:
                    self.current_map = self.main_window.selected_map
                else:
                    self.current_map = "Sin mapa"
                    
                if self.logger:
                    self.logger.info(f"Servidor y mapa cargados: {self.current_server} - {self.current_map}")
            else:
                if self.logger:
                    self.logger.info("No hay servidor seleccionado en MainWindow")
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al cargar servidor/mapa: {e}")
    
    def restore_server_map_selection(self):
        """Restaurar selección de servidor y mapa"""
        try:
            # Intentar restaurar desde MainWindow
            if hasattr(self.main_window, 'selected_server') and self.main_window.selected_server:
                self.current_server = self.main_window.selected_server
                
                if hasattr(self.main_window, 'selected_map') and self.main_window.selected_map:
                    self.current_map = self.main_window.selected_map
                else:
                    self.current_map = "Sin mapa"
                    
                if self.logger:
                    self.logger.info(f"Selección restaurada: {self.current_server} - {self.current_map}")
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al restaurar selección: {e}")
    
    def update_server_map_context(self, server_name, map_name):
        """Actualizar contexto de servidor y mapa"""
        try:
            self.current_server = server_name
            self.current_map = map_name
            
            # Guardar contexto actual
            self.save_current_server_map()
            
            # Cargar mods específicos del servidor/mapa
            self.load_installed_mods()
            
            # Actualizar entrada de IDs con los mods del contexto actual
            self.update_mods_ids_entry()
            
            # Aplicar automáticamente los mods al servidor si hay mods instalados
            if self.installed_mods:
                self.apply_mods_to_server_silently()
            else:
                # Si no hay mods, limpiar la configuración del servidor
                self.clear_mods_silently()
            
            # Actualizar visualización
            self.refresh_mods_display()
            self.update_stats()
            
            if self.logger:
                self.logger.info(f"Contexto actualizado: {server_name} - {map_name} ({len(self.installed_mods)} mods cargados y aplicados automáticamente)")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al actualizar contexto: {e}")
    
    def save_current_server_map(self):
        """Guardar contexto actual de servidor y mapa"""
        try:
            if self.current_server and self.current_map:
                context_data = {
                    "server": self.current_server,
                    "map": self.current_map,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Guardar en archivo
                context_file = os.path.join(self.get_data_directory(), "current_server_map.json")
                with open(context_file, 'w', encoding='utf-8') as f:
                    json.dump(context_data, f, indent=2, ensure_ascii=False)
                    
                if self.logger:
                    self.logger.info(f"Contexto guardado: {self.current_server} - {self.current_map}")
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al guardar contexto: {e}")
    
    def get_mods_key(self):
        """Obtener clave para mods del servidor/mapa actual"""
        if self.current_server and self.current_map:
            return f"{self.current_server}_{self.current_map}"
        return "default"
    
    def load_installed_mods(self):
        """Cargar mods instalados del servidor/mapa actual"""
        try:
            mods_key = self.get_mods_key()
            mods_file = os.path.join(self.get_data_directory(), f"installed_mods_{mods_key}.json")
            
            if os.path.exists(mods_file):
                with open(mods_file, 'r', encoding='utf-8') as f:
                    self.installed_mods = json.load(f)
                
                # NUEVO: Limpiar duplicados automáticamente al cargar
                duplicates_removed = self.remove_duplicate_mods()
                
                if self.logger:
                    self.logger.info(f"Mods instalados cargados: {len(self.installed_mods)} mods para {mods_key}")
                    if duplicates_removed > 0:
                        self.logger.info(f"Se eliminaron automáticamente {duplicates_removed} duplicados")
            else:
                self.installed_mods = []
                if self.logger:
                    self.logger.info(f"No se encontró archivo de mods instalados para {mods_key}")
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al cargar mods instalados: {e}")
            self.installed_mods = []
    
    def save_installed_mods(self):
        """Guardar mods instalados del servidor/mapa actual"""
        try:
            mods_key = self.get_mods_key()
            mods_file = os.path.join(self.get_data_directory(), f"installed_mods_{mods_key}.json")
            
            with open(mods_file, 'w', encoding='utf-8') as f:
                json.dump(self.installed_mods, f, indent=2, ensure_ascii=False)
                
            if self.logger:
                self.logger.info(f"Mods instalados guardados: {len(self.installed_mods)} mods para {mods_key}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al guardar mods instalados: {e}")
    
    def load_favorite_mods(self):
        """Cargar mods favoritos (globales)"""
        try:
            favorites_file = os.path.join(self.get_data_directory(), "favorite_mods.json")
            
            if os.path.exists(favorites_file):
                with open(favorites_file, 'r', encoding='utf-8') as f:
                    self.favorite_mods = json.load(f)
                    
                if self.logger:
                    self.logger.info(f"Mods favoritos cargados: {len(self.favorite_mods)} mods")
            else:
                self.favorite_mods = []
                if self.logger:
                    self.logger.info("No se encontró archivo de mods favoritos")
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al cargar mods favoritos: {e}")
            self.favorite_mods = []
    
    def save_favorite_mods(self):
        """Guardar mods favoritos (globales)"""
        try:
            favorites_file = os.path.join(self.get_data_directory(), "favorite_mods.json")
            
            with open(favorites_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorite_mods, f, indent=2, ensure_ascii=False)
                
            if self.logger:
                self.logger.info(f"Mods favoritos guardados: {len(self.favorite_mods)} mods")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al guardar mods favoritos: {e}")
    
    def show_message(self, message, msg_type="info"):
        """Mostrar mensaje al usuario"""
        try:
            # Crear ventana de mensaje
            msg_window = ctk.CTkToplevel(self)
            msg_window.title("Mensaje")
            msg_window.geometry("400x200")
            msg_window.resizable(False, False)
            
            # Configurar colores según tipo
            colors = {
                "info": ("#2196F3", "#1976D2"),
                "success": ("#4CAF50", "#388E3C"),
                "warning": ("#FF9800", "#F57C00"),
                "error": ("#f44336", "#d32f2f")
            }
            
            fg_color, hover_color = colors.get(msg_type, colors["info"])
            
            # Frame principal
            main_frame = ctk.CTkFrame(msg_window)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Icono según tipo
            icons = {
                "info": "ℹ️",
                "success": "✅",
                "warning": "⚠️",
                "error": "❌"
            }
            
            icon_label = ctk.CTkLabel(
                main_frame,
                text=icons.get(msg_type, "ℹ️"),
                font=ctk.CTkFont(size=48)
            )
            icon_label.pack(pady=(0, 20))
            
            # Mensaje
            message_label = ctk.CTkLabel(
                main_frame,
                text=message,
                font=ctk.CTkFont(size=14),
                justify="center",
                wraplength=350
            )
            message_label.pack(pady=(0, 20))
            
            # Botón de cerrar
            close_btn = ctk.CTkButton(
                main_frame,
                text="Cerrar",
                command=msg_window.destroy,
                fg_color=fg_color,
                hover_color=hover_color
            )
            close_btn.pack()
            
            # Auto-cerrar después de unos segundos según el tipo de mensaje
            auto_close_times = {
                "success": 2000,  # 2 segundos
                "info": 3000,     # 3 segundos
                "warning": 4000,  # 4 segundos
                "error": 5000     # 5 segundos
            }
            
            auto_close_time = auto_close_times.get(msg_type, 3000)
            try:
                if msg_window.winfo_exists():
                    msg_window.after(auto_close_time, lambda: msg_window.destroy() if msg_window.winfo_exists() else None)
            except Exception:
                pass
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al mostrar mensaje: {e}")
            # Fallback simple
            try:
                messagebox.showinfo("Mensaje", message)
            except:
                pass
    
    def toggle_startup_messages(self):
        """Alternar configuración de mensajes de inicio"""
        self.show_startup_messages = self.startup_messages_switch.get()
        self.save_startup_messages_setting()
        
        # Mostrar mensaje de confirmación
        status = "activados" if self.show_startup_messages else "desactivados"
        self.show_message(f"Mensajes de inicio {status}", "success")
        
        if self.logger:
            self.logger.info(f"Mensajes de inicio {status}")
    
    def load_startup_messages_setting(self):
        """Cargar configuración de mensajes de inicio"""
        try:
            data_dir = self.get_data_directory()
            settings_file = os.path.join(data_dir, "app_settings.json")
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.show_startup_messages = settings.get("show_startup_messages", True)
            else:
                self.show_startup_messages = True
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error cargando configuración de mensajes de inicio: {e}")
            self.show_startup_messages = True
    
    def save_startup_messages_setting(self):
        """Guardar configuración de mensajes de inicio"""
        try:
            data_dir = self.get_data_directory()
            settings_file = os.path.join(data_dir, "app_settings.json")
            
            # Cargar configuración existente o crear nueva
            settings = {}
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            # Actualizar configuración
            settings["show_startup_messages"] = self.show_startup_messages
            
            # Guardar configuración
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error guardando configuración de mensajes de inicio: {e}")
    
    def get_startup_messages_setting(self):
        """Obtener configuración actual de mensajes de inicio"""
        return self.show_startup_messages
