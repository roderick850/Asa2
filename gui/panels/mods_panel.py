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
        
        # Empaquetar el frame principal
        self.pack(fill="both", expand=True)
        
        self.create_widgets()
        self.load_favorite_mods()  # Los favoritos son globales
        self.load_current_server_map()  # Cargar último servidor/mapa
        self.load_installed_mods()  # Cargar mods del servidor/mapa actual
        
        # Actualizar UI inicial después de cargar datos
        self.after(100, self.refresh_initial_tabs)
    
    def get_data_directory(self):
        """Obtener directorio de datos correcto para ejecutable y desarrollo"""
        try:
            if hasattr(sys, '_MEIPASS'):
                # Si estamos en un ejecutable de PyInstaller
                base_dir = os.path.dirname(sys.executable)
            else:
                # Si estamos en desarrollo
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            return data_dir
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al obtener directorio de datos: {e}")
            # Fallback a directorio relativo
            fallback_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
            os.makedirs(fallback_dir, exist_ok=True)
            return fallback_dir
    
    def refresh_initial_tabs(self):
        """Refrescar pestañas con contenido inicial"""
        try:
            # Refrescar pestañas de favoritos e instalados
            self.refresh_favorites_tab()
            self.refresh_installed_tab()
            self.update_mods_ids_entry()
            
            # Mostrar mensaje de bienvenida
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
        # Configurar el grid principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Título
        title_label = ctk.CTkLabel(
            self, 
            text="🎮 Gestor de Mods - ARK Survival Ascended", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(10, 20), sticky="ew")
        
        # Frame de búsqueda
        self.create_search_frame()
        
        # Frame principal con pestañas
        self.create_tabs_frame()
        
        # Frame de mods instalados (parte inferior)
        self.create_installed_frame()
        
    def create_search_frame(self):
        """Crear frame de búsqueda"""
        search_frame = ctk.CTkFrame(self)
        search_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        search_frame.grid_columnconfigure(1, weight=1)
        
        # Label de búsqueda
        search_label = ctk.CTkLabel(search_frame, text="🔍 Buscar Mods:", font=("Arial", 12, "bold"))
        search_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Entry de búsqueda
        self.search_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="Buscar mods en CurseForge...",
            height=32
        )
        self.search_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.search_entry.bind("<Return>", lambda e: self.search_mods())
        
        # Botón de búsqueda
        search_button = ctk.CTkButton(
            search_frame,
            text="Buscar",
            command=self.search_mods,
            width=80,
            height=32,
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        search_button.grid(row=0, column=2, padx=10, pady=10)
        
        # Botón de mods populares
        popular_button = ctk.CTkButton(
            search_frame,
            text="Populares",
            command=self.load_popular_mods,
            width=80,
            height=32,
            fg_color="#FF9800",
            hover_color="#e68900"
        )
        popular_button.grid(row=0, column=3, padx=5, pady=10)
        
    def create_tabs_frame(self):
        """Crear frame de pestañas"""
        # Tabview principal
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        
        # Pestaña de búsqueda
        self.tab_search = self.tabview.add("🔍 Resultados")
        self.create_search_results_tab()
        
        # Pestaña de favoritos
        self.tab_favorites = self.tabview.add("⭐ Favoritos")
        self.create_favorites_tab()
        
        # Pestaña de instalados
        self.tab_installed = self.tabview.add("📦 Instalados")
        self.create_installed_tab()
        
    def create_search_results_tab(self):
        """Crear pestaña de resultados de búsqueda"""
        # Frame scrollable para resultados
        self.search_scroll_frame = ctk.CTkScrollableFrame(self.tab_search)
        self.search_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Label inicial
        self.search_status_label = ctk.CTkLabel(
            self.search_scroll_frame,
            text="💡 Usa la barra de búsqueda para encontrar mods\no haz clic en 'Populares' para ver los mods más descargados",
            font=("Arial", 12)
        )
        self.search_status_label.pack(pady=50)
        
    def create_favorites_tab(self):
        """Crear pestaña de favoritos"""
        # Frame scrollable para favoritos
        self.favorites_scroll_frame = ctk.CTkScrollableFrame(self.tab_favorites)
        self.favorites_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Label inicial
        self.favorites_status_label = ctk.CTkLabel(
            self.favorites_scroll_frame,
            text="⭐ MODS FAVORITOS\n\nTus mods favoritos aparecerán aquí.\nMarca mods como favoritos desde los resultados de búsqueda.\n\n🔍 Busca mods o haz clic en 'Populares' para empezar.",
            font=("Arial", 12),
            justify="center"
        )
        self.favorites_status_label.pack(pady=50)
        
    def create_installed_tab(self):
        """Crear pestaña de mods instalados"""
        # Frame scrollable para instalados
        self.installed_scroll_frame = ctk.CTkScrollableFrame(self.tab_installed)
        self.installed_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Label inicial
        self.installed_status_label = ctk.CTkLabel(
            self.installed_scroll_frame,
            text="📦 MODS INSTALADOS\n\nLos mods instalados para el servidor actual aparecerán aquí.\nInstala mods desde los resultados de búsqueda.\n\n💡 Los mods se guardan por servidor y mapa.",
            font=("Arial", 12),
            justify="center"
        )
        self.installed_status_label.pack(pady=50)
        
    def create_installed_frame(self):
        """Crear frame de información de mods instalados"""
        installed_info_frame = ctk.CTkFrame(self)
        installed_info_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        installed_info_frame.grid_columnconfigure(1, weight=1)
        
        # Label de información
        info_label = ctk.CTkLabel(
            installed_info_frame,
            text="📋 Mods para el servidor:",
            font=("Arial", 12, "bold")
        )
        info_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Entry con los IDs de mods
        self.mods_ids_entry = ctk.CTkEntry(
            installed_info_frame,
            placeholder_text="IDs de mods separados por comas (ej: 956565,854554)",
            height=32
        )
        self.mods_ids_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Botón para aplicar mods
        apply_button = ctk.CTkButton(
            installed_info_frame,
            text="Aplicar al Servidor",
            command=self.apply_mods_to_server,
            width=120,
            height=32,
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        apply_button.grid(row=0, column=2, padx=10, pady=10)
        
        # Botón para limpiar mods
        clear_button = ctk.CTkButton(
            installed_info_frame,
            text="Limpiar",
            command=self.clear_mods,
            width=80,
            height=32,
            fg_color="#f44336",
            hover_color="#d32f2f"
        )
        clear_button.grid(row=0, column=3, padx=5, pady=10)
        
    def search_mods(self):
        """Buscar mods en CurseForge"""
        query = self.search_entry.get().strip()
        if not query:
            self.show_message("❌ Ingresa un término de búsqueda", "error")
            return
            
        # Mostrar indicador de carga
        self.update_search_status("🔄 Buscando mods...")
        
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
                self.after(0, lambda: self.display_search_results(mods))
            else:
                self.after(0, lambda: self.update_search_status(f"❌ Error en la búsqueda: {response.status_code}"))
                
        except Exception as e:
            self.logger.error(f"Error al buscar mods: {e}")
            self.after(0, lambda: self.update_search_status("❌ Error de conexión"))
            
    def load_popular_mods(self):
        """Cargar mods populares"""
        self.update_search_status("🔄 Cargando mods populares...")
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
                self.after(0, lambda: self.display_search_results(mods))
            else:
                self.after(0, lambda: self.update_search_status(f"❌ Error al cargar mods populares: {response.status_code}"))
                
        except Exception as e:
            self.logger.error(f"Error al cargar mods populares: {e}")
            self.after(0, lambda: self.update_search_status("❌ Error de conexión"))
    
    def update_search_status(self, text):
        """Actualizar estado de búsqueda de forma segura"""
        try:
            if hasattr(self, 'search_status_label') and self.search_status_label.winfo_exists():
                self.search_status_label.configure(text=text)
        except:
            pass
            
    def display_search_results(self, mods):
        """Mostrar resultados de búsqueda"""
        # Guardar los resultados actuales
        self.search_results = mods
        
        # Limpiar resultados anteriores de forma segura
        try:
            for widget in self.search_scroll_frame.winfo_children():
                if widget.winfo_exists():
                    widget.destroy()
        except:
            pass
            
        if not mods:
            no_results_label = ctk.CTkLabel(
                self.search_scroll_frame,
                text="😔 No se encontraron mods",
                font=("Arial", 14)
            )
            no_results_label.pack(pady=50)
            return
            
        # Mostrar cada mod
        for mod in mods:
            try:
                self.create_mod_card(self.search_scroll_frame, mod)
            except Exception as e:
                self.logger.error(f"Error al crear tarjeta de mod: {e}")
                continue
            
        # Cambiar a pestaña de resultados
        try:
            self.tabview.set("🔍 Resultados")
        except:
            pass
        
    def create_mod_card(self, parent, mod):
        """Crear tarjeta de mod mejorada"""
        # Frame principal del mod con bordes más atractivos
        mod_frame = ctk.CTkFrame(parent, corner_radius=10, border_width=1)
        mod_frame.pack(fill="x", padx=5, pady=8)
        
        # Información básica
        mod_id = mod.get("id", "")
        mod_name = mod.get("name", "Sin nombre")
        mod_summary = mod.get("summary", "Sin descripción")
        download_count = mod.get("downloadCount", 0)
        date_modified = mod.get("dateModified", "")
        
        # Header frame con nombre e ID
        header_frame = ctk.CTkFrame(mod_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        # Nombre del mod más llamativo
        name_label = ctk.CTkLabel(
            header_frame,
            text=f"🎮 {mod_name}",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        name_label.pack(side="left", fill="x", expand=True)
        
        # ID destacado
        id_label = ctk.CTkLabel(
            header_frame,
            text=f"ID: {mod_id}",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray80", "gray20"),
            corner_radius=5,
            padx=8,
            pady=2
        )
        id_label.pack(side="right")
        
        # Descripción con mejor formato
        if mod_summary:
            desc_text = mod_summary[:150] + "..." if len(mod_summary) > 150 else mod_summary
            desc_label = ctk.CTkLabel(
                mod_frame,
                text=desc_text,
                font=ctk.CTkFont(size=11),
                anchor="w",
                wraplength=500,
                justify="left"
            )
            desc_label.pack(anchor="w", padx=15, pady=5, fill="x")
        
        # Frame de estadísticas
        stats_frame = ctk.CTkFrame(mod_frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=15, pady=5)
        
        # Descargas
        downloads_label = ctk.CTkLabel(
            stats_frame,
            text=f"📥 {download_count:,} descargas",
            font=ctk.CTkFont(size=10),
            fg_color=("lightblue", "darkblue"),
            corner_radius=3,
            padx=6,
            pady=2
        )
        downloads_label.pack(side="left", padx=(0, 5))
        
        # Fecha de modificación
        if date_modified:
            try:
                date_obj = datetime.fromisoformat(date_modified.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime("%d/%m/%Y")
                date_label = ctk.CTkLabel(
                    stats_frame,
                    text=f"📅 {formatted_date}",
                    font=ctk.CTkFont(size=10),
                    fg_color=("lightgreen", "darkgreen"),
                    corner_radius=3,
                    padx=6,
                    pady=2
                )
                date_label.pack(side="left", padx=(0, 5))
            except:
                pass
        
        # Verificar si está en favoritos o instalado
        is_favorite = any(fav.get("id") == str(mod_id) for fav in self.favorite_mods)
        is_installed = any(inst.get("id") == str(mod_id) for inst in self.installed_mods)
        
        if is_favorite:
            fav_status = ctk.CTkLabel(
                stats_frame,
                text="⭐ Favorito",
                font=ctk.CTkFont(size=10),
                fg_color=("orange", "darkorange"),
                corner_radius=3,
                padx=6,
                pady=2
            )
            fav_status.pack(side="left", padx=(0, 5))
            
        if is_installed:
            inst_status = ctk.CTkLabel(
                stats_frame,
                text="📦 Instalado",
                font=ctk.CTkFont(size=10),
                fg_color=("lightcoral", "darkred"),
                corner_radius=3,
                padx=6,
                pady=2
            )
            inst_status.pack(side="left", padx=(0, 5))
        
        # Frame de botones mejorado
        buttons_frame = ctk.CTkFrame(mod_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=15, pady=(10, 15))
        
        # Botón de instalar/desinstalar con estado visual claro
        is_mod_installed = any(inst.get("id") == str(mod_id) for inst in self.installed_mods)
        
        if is_mod_installed:
            install_text = "✅ Instalado"
            install_color = "#10B981"  # Verde para instalado
            install_hover = "#059669"
            install_command = lambda: self.uninstall_mod_from_search_and_refresh(mod, buttons_frame)
        else:
            install_text = "📦 Instalar"
            install_color = "#3B82F6"  # Azul para instalar
            install_hover = "#2563EB"
            install_command = lambda: self.install_mod_and_refresh(mod, buttons_frame)
        
        install_button = ctk.CTkButton(
            buttons_frame,
            text=install_text,
            command=install_command,
            width=110,
            height=32,
            fg_color=install_color,
            hover_color=install_hover,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        install_button.pack(side="left", padx=(0, 8))
        
        # Botón de favorito con colores dinámicos
        is_favorite = any(fav.get("id") == str(mod_id) for fav in self.favorite_mods)
        
        if is_favorite:
            fav_text = "⭐ Favorito"
            fav_color = "#FF6B35"  # Naranja brillante para favoritos
            fav_hover = "#E55A2B"
        else:
            fav_text = "☆ Agregar Fav"
            fav_color = "#64748B"  # Gris para no favoritos
            fav_hover = "#475569"
        
        favorite_button = ctk.CTkButton(
            buttons_frame,
            text=fav_text,
            command=lambda: self.toggle_favorite_and_refresh(mod, buttons_frame),
            width=110,
            height=32,
            fg_color=fav_color,
            hover_color=fav_hover,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        favorite_button.pack(side="left", padx=(0, 8))
        
        # Botón de ver en CurseForge
        view_button = ctk.CTkButton(
            buttons_frame,
            text="🌐 Abrir Página",
            command=lambda: self.open_curseforge_page(mod),
            width=110,
            height=32,
            fg_color="#2196F3",
            hover_color="#1976D2",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        view_button.pack(side="left", padx=(0, 8))
        
        # Botón de copiar ID
        copy_button = ctk.CTkButton(
            buttons_frame,
            text="📋 Copiar ID",
            command=lambda: self.copy_mod_id(mod),
            width=90,
            height=32,
            fg_color="#9C27B0",
            hover_color="#7B1FA2",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        copy_button.pack(side="left")
        
        # Separador
        separator = ctk.CTkFrame(parent, height=1)
        separator.pack(fill="x", padx=20, pady=2)
        
    def install_mod(self, mod):
        """Instalar mod"""
        mod_id = str(mod.get("id", ""))
        mod_name = mod.get("name", "Sin nombre")
        
        # Verificar si ya está instalado
        if any(installed.get("id") == mod_id for installed in self.installed_mods):
            self.show_message(f"✅ El mod '{mod_name}' ya está instalado", "info")
            return
            
        # Agregar a la lista de instalados
        self.installed_mods.append({
            "id": mod_id,
            "name": mod_name,
            "dateInstalled": datetime.now().isoformat()
        })
        
        # Guardar lista de instalados
        self.save_installed_mods()
        
        # Actualizar entry de IDs
        self.update_mods_ids_entry()
        
        # Actualizar pestaña de instalados
        self.refresh_installed_tab()
        
        self.show_message(f"✅ Mod '{mod_name}' instalado correctamente", "success")
        
    def toggle_favorite(self, mod):
        """Alternar estado de favorito"""
        mod_id = str(mod.get("id", ""))
        mod_name = mod.get("name", "Sin nombre")
        
        # Verificar si ya es favorito
        is_favorite = any(fav.get("id") == mod_id for fav in self.favorite_mods)
        
        if is_favorite:
            # Remover de favoritos
            self.favorite_mods = [fav for fav in self.favorite_mods if fav.get("id") != mod_id]
            self.show_message(f"☆ Mod '{mod_name}' removido de favoritos", "info")
        else:
            # Agregar a favoritos
            self.favorite_mods.append({
                "id": mod_id,
                "name": mod_name,
                "summary": mod.get("summary", ""),
                "downloadCount": mod.get("downloadCount", 0),
                "dateAdded": datetime.now().isoformat()
            })
            self.show_message(f"⭐ Mod '{mod_name}' agregado a favoritos", "success")
            
        # Guardar favoritos
        self.save_favorite_mods()
        
        # Actualizar pestañas
        self.refresh_favorites_tab()
        # NO refrescar resultados aquí para evitar errores de widgets
        
    def open_curseforge_page(self, mod):
        """Abrir página del mod en CurseForge"""
        mod_id = mod.get("id", "")
        mod_name = mod.get("name", "Sin nombre")
        if mod_id:
            # Usar el slug del mod si está disponible, sino usar el ID
            mod_slug = mod.get("slug", "")
            if mod_slug:
                url = f"https://www.curseforge.com/ark-survival-ascended/mods/{mod_slug}"
            else:
                url = f"https://www.curseforge.com/ark-survival-ascended/search?search={mod_name.replace(' ', '%20')}"
            
            webbrowser.open(url)
            self.show_message(f"🌐 Abriendo página de '{mod_name}'", "info")
    
    def copy_mod_id(self, mod):
        """Copiar ID del mod al portapapeles"""
        mod_id = str(mod.get("id", ""))
        mod_name = mod.get("name", "Sin nombre")
        
        if mod_id:
            try:
                # Copiar al portapapeles
                self.clipboard_clear()
                self.clipboard_append(mod_id)
                self.show_message(f"📋 ID copiado: {mod_id} ({mod_name})", "success")
            except Exception as e:
                self.logger.error(f"Error al copiar ID: {e}")
                self.show_message(f"❌ Error al copiar ID", "error")
            
    def refresh_favorites_tab(self):
        """Actualizar pestaña de favoritos"""
        # Limpiar contenido actual
        for widget in self.favorites_scroll_frame.winfo_children():
            widget.destroy()
            
        if not self.favorite_mods:
            self.favorites_status_label = ctk.CTkLabel(
                self.favorites_scroll_frame,
                text="⭐ Tus mods favoritos aparecerán aquí\nMarca mods como favoritos desde los resultados de búsqueda",
                font=("Arial", 12)
            )
            self.favorites_status_label.pack(pady=50)
            return
            
        # Mostrar favoritos
        for fav_mod in self.favorite_mods:
            self.create_favorite_card(self.favorites_scroll_frame, fav_mod)
            
    def create_favorite_card(self, parent, mod):
        """Crear tarjeta de mod favorito mejorada"""
        # Frame principal con diseño mejorado
        mod_frame = ctk.CTkFrame(parent, corner_radius=10, border_width=1)
        mod_frame.pack(fill="x", padx=5, pady=8)
        
        mod_name = mod.get("name", "Sin nombre")
        mod_id = str(mod.get("id", ""))
        download_count = mod.get("downloadCount", 0)
        
        # Header frame con nombre e ID
        header_frame = ctk.CTkFrame(mod_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        # Nombre del mod
        name_label = ctk.CTkLabel(
            header_frame,
            text=f"⭐ {mod_name}",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        name_label.pack(side="left", fill="x", expand=True)
        
        # ID destacado
        id_label = ctk.CTkLabel(
            header_frame,
            text=f"ID: {mod_id}",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray80", "gray20"),
            corner_radius=5,
            padx=8,
            pady=2
        )
        id_label.pack(side="right")
        
        # Frame de estadísticas
        stats_frame = ctk.CTkFrame(mod_frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=15, pady=5)
        
        # Descargas
        downloads_label = ctk.CTkLabel(
            stats_frame,
            text=f"📥 {download_count:,} descargas",
            font=ctk.CTkFont(size=10),
            fg_color=("lightblue", "darkblue"),
            corner_radius=3,
            padx=6,
            pady=2
        )
        downloads_label.pack(side="left", padx=(0, 5))
        
        # Estado de instalación
        is_installed = any(inst.get("id") == mod_id for inst in self.installed_mods)
        if is_installed:
            inst_status = ctk.CTkLabel(
                stats_frame,
                text="📦 Instalado",
                font=ctk.CTkFont(size=10),
                fg_color=("lightgreen", "darkgreen"),
                corner_radius=3,
                padx=6,
                pady=2
            )
            inst_status.pack(side="left", padx=(0, 5))
        
        # Botones mejorados
        buttons_frame = ctk.CTkFrame(mod_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=15, pady=(10, 15))
        
        # Botón de instalar/desinstalar según estado
        if is_installed:
            install_button = ctk.CTkButton(
                buttons_frame,
                text="✅ Instalado",
                command=lambda: self.uninstall_mod_and_refresh_favorites(mod),
                width=110,
                height=32,
                fg_color="#10B981",
                hover_color="#059669",
                font=ctk.CTkFont(size=11, weight="bold")
            )
        else:
            install_button = ctk.CTkButton(
                buttons_frame,
                text="📦 Instalar",
                command=lambda: self.install_mod_and_refresh_favorites(mod),
                width=110,
                height=32,
                fg_color="#3B82F6",
                hover_color="#2563EB",
                font=ctk.CTkFont(size=11, weight="bold")
            )
        install_button.pack(side="left", padx=(0, 8))
        
        # Remover de favoritos
        remove_button = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Quitar Fav",
            command=lambda: self.remove_favorite(mod),
            width=100,
            height=32,
            fg_color="#f44336",
            hover_color="#d32f2f",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        remove_button.pack(side="left", padx=(0, 8))
        
        # Botón de abrir página
        view_button = ctk.CTkButton(
            buttons_frame,
            text="🌐 Ver Página",
            command=lambda: self.open_curseforge_page(mod),
            width=100,
            height=32,
            fg_color="#2196F3",
            hover_color="#1976D2",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        view_button.pack(side="left")
        
    def remove_favorite(self, mod):
        """Remover de favoritos"""
        mod_id = str(mod.get("id", ""))
        self.favorite_mods = [fav for fav in self.favorite_mods if fav.get("id") != mod_id]
        self.save_favorite_mods()
        self.refresh_favorites_tab()
        
    def refresh_installed_tab(self):
        """Actualizar pestaña de instalados"""
        # Limpiar contenido actual
        for widget in self.installed_scroll_frame.winfo_children():
            widget.destroy()
            
        if not self.installed_mods:
            self.installed_status_label = ctk.CTkLabel(
                self.installed_scroll_frame,
                text="📦 MODS INSTALADOS\n\nNo hay mods instalados para este servidor.\nInstala mods desde los resultados de búsqueda.\n\n💡 Los mods se guardan por servidor y mapa.",
                font=("Arial", 12),
                justify="center"
            )
            self.installed_status_label.pack(pady=50)
            return
            
        # Mostrar instalados
        for installed_mod in self.installed_mods:
            self.create_installed_card(self.installed_scroll_frame, installed_mod)
            
    def create_installed_card(self, parent, mod):
        """Crear tarjeta de mod instalado"""
        mod_frame = ctk.CTkFrame(parent)
        mod_frame.pack(fill="x", padx=5, pady=5)
        
        mod_name = mod.get("name", "Sin nombre")
        mod_id = mod.get("id", "")
        date_installed = mod.get("dateInstalled", "")
        
        # Formato de fecha
        date_text = ""
        if date_installed:
            try:
                date_obj = datetime.fromisoformat(date_installed)
                date_text = f" | 📅 Instalado: {date_obj.strftime('%d/%m/%Y')}"
            except:
                pass
        
        # Nombre
        name_label = ctk.CTkLabel(
            mod_frame,
            text=f"📦 {mod_name}",
            font=("Arial", 14, "bold"),
            anchor="w"
        )
        name_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Información
        info_text = f"🆔 ID: {mod_id}{date_text}"
        info_label = ctk.CTkLabel(
            mod_frame,
            text=info_text,
            font=("Arial", 10),
            text_color="gray"
        )
        info_label.pack(anchor="w", padx=10, pady=5)
        
        # Botón de desinstalar
        uninstall_button = ctk.CTkButton(
            mod_frame,
            text="🗑️ Desinstalar",
            command=lambda: self.uninstall_mod(mod),
            width=100,
            height=28,
            fg_color="#f44336",
            hover_color="#d32f2f"
        )
        uninstall_button.pack(anchor="w", padx=10, pady=10)
        
    def uninstall_mod(self, mod):
        """Desinstalar mod desde la pestaña de instalados"""
        mod_id = str(mod.get("id", ""))
        mod_name = mod.get("name", "Sin nombre")
        
        # Remover de la lista
        self.installed_mods = [inst for inst in self.installed_mods if inst.get("id") != mod_id]
        
        # Guardar cambios
        self.save_installed_mods()
        
        # Actualizar UI
        self.update_mods_ids_entry()
        self.refresh_installed_tab()
        
        self.show_message(f"🗑️ Mod '{mod_name}' desinstalado", "info")
    
    def uninstall_mod_from_search(self, mod):
        """Desinstalar mod desde resultados de búsqueda"""
        mod_id = str(mod.get("id", ""))
        mod_name = mod.get("name", "Sin nombre")
        
        # Verificar si está instalado
        if not any(inst.get("id") == mod_id for inst in self.installed_mods):
            self.show_message(f"❌ El mod '{mod_name}' no está instalado", "error")
            return
        
        # Remover de la lista
        self.installed_mods = [inst for inst in self.installed_mods if inst.get("id") != mod_id]
        
        # Guardar cambios
        self.save_installed_mods()
        
        # Actualizar UI
        self.update_mods_ids_entry()
        self.refresh_installed_tab()
        
        self.show_message(f"🗑️ Mod '{mod_name}' desinstalado correctamente", "success")
    
    def install_mod_and_refresh(self, mod, buttons_frame):
        """Instalar mod y refrescar botones"""
        self.install_mod(mod)
        # Refrescar solo esta tarjeta específica
        self.refresh_mod_card_buttons(mod, buttons_frame)
    
    def uninstall_mod_from_search_and_refresh(self, mod, buttons_frame):
        """Desinstalar mod y refrescar botones"""
        self.uninstall_mod_from_search(mod)
        # Refrescar solo esta tarjeta específica
        self.refresh_mod_card_buttons(mod, buttons_frame)
    
    def toggle_favorite_and_refresh(self, mod, buttons_frame):
        """Alternar favorito y refrescar botones"""
        self.toggle_favorite(mod)
        # Refrescar solo esta tarjeta específica
        self.refresh_mod_card_buttons(mod, buttons_frame)
    
    def refresh_mod_card_buttons(self, mod, buttons_frame):
        """Refrescar solo los botones de una tarjeta específica"""
        try:
            mod_id = str(mod.get("id", ""))
            
            # Buscar y actualizar el botón de instalar
            for widget in buttons_frame.winfo_children():
                if isinstance(widget, ctk.CTkButton):
                    widget_text = widget.cget("text")
                    
                    # Actualizar botón de instalar
                    if "Instalar" in widget_text or "Instalado" in widget_text:
                        is_installed = any(inst.get("id") == mod_id for inst in self.installed_mods)
                        if is_installed:
                            widget.configure(text="✅ Instalado", fg_color="#10B981", hover_color="#059669")
                        else:
                            widget.configure(text="📦 Instalar", fg_color="#3B82F6", hover_color="#2563EB")
                    
                    # Actualizar botón de favorito
                    elif "Favorito" in widget_text or "Agregar Fav" in widget_text:
                        is_favorite = any(fav.get("id") == mod_id for fav in self.favorite_mods)
                        if is_favorite:
                            widget.configure(text="⭐ Favorito", fg_color="#FF6B35", hover_color="#E55A2B")
                        else:
                            widget.configure(text="☆ Agregar Fav", fg_color="#64748B", hover_color="#475569")
        except Exception as e:
            self.logger.error(f"Error al refrescar botones: {e}")
    
    def install_mod_and_refresh_favorites(self, mod):
        """Instalar mod y refrescar favoritos"""
        self.install_mod(mod)
        self.refresh_favorites_tab()
    
    def uninstall_mod_and_refresh_favorites(self, mod):
        """Desinstalar mod y refrescar favoritos"""
        self.uninstall_mod_from_search(mod)
        self.refresh_favorites_tab()
        
    def update_mods_ids_entry(self):
        """Actualizar el campo de IDs de mods"""
        mod_ids = [mod.get("id", "") for mod in self.installed_mods if mod.get("id")]
        ids_text = ",".join(mod_ids)
        
        self.mods_ids_entry.delete(0, "end")
        if ids_text:
            self.mods_ids_entry.insert(0, ids_text)
            
    def apply_mods_to_server(self):
        """Aplicar mods al servidor actual"""
        mod_ids = self.mods_ids_entry.get().strip()
        
        if not mod_ids:
            self.show_message("❌ No hay mods para aplicar al servidor", "error")
            return
            
        # Guardar los IDs en la configuración con clave específica del servidor/mapa
        mods_key = self.get_mods_key()
        config_key = f"mod_ids_{mods_key}"
        self.config_manager.set("server", config_key, mod_ids)
        
        # También guardar en la clave general para compatibilidad
        self.config_manager.set("server", "mod_ids", mod_ids)
        self.config_manager.save()
        
        server_info = f"{self.current_server} - {self.current_map}" if self.current_server and self.current_map else "servidor actual"
        self.show_message(f"✅ Mods aplicados a {server_info}: {mod_ids}", "success")
        
    def clear_mods(self):
        """Limpiar todos los mods instalados"""
        # Limpiar el campo de IDs
        self.mods_ids_entry.delete(0, "end")
        
        # Limpiar la configuración
        self.config_manager.set("server", "mod_ids", "")
        self.config_manager.save()
        
        # Limpiar la lista de mods instalados
        self.installed_mods.clear()
        self.save_installed_mods()
        
        # Refrescar la pestaña de instalados
        self.refresh_installed_tab()
        
        # Refrescar los favoritos para que actualicen su estado visual
        self.refresh_favorites_tab()
        
        self.show_message("🧹 Lista de mods limpiada completamente", "success")
    
    def load_current_server_map(self):
        """Cargar el último servidor y mapa seleccionado"""
        try:
            self.current_server = self.config_manager.get("app", "last_server", "")
            self.current_map = self.config_manager.get("app", "last_map", "")
            
            if self.current_server and self.current_map:
                self.logger.info(f"Cargando configuración para servidor: {self.current_server}, mapa: {self.current_map}")
                
                # Notificar al main_window para que actualice los dropdowns
                if hasattr(self, 'main_window') and self.main_window:
                    self.main_window.after(100, lambda: self.restore_server_map_selection())
                    
        except Exception as e:
            self.logger.error(f"Error al cargar servidor/mapa actual: {e}")
    
    def restore_server_map_selection(self):
        """Restaurar la selección de servidor y mapa en los dropdowns"""
        try:
            if hasattr(self.main_window, 'server_dropdown') and self.main_window.server_dropdown:
                # Verificar si el servidor existe en la lista
                servers = [self.main_window.server_dropdown.cget("values")]
                if servers and self.current_server in servers[0]:
                    self.main_window.server_dropdown.set(self.current_server)
                    
            if hasattr(self.main_window, 'map_dropdown') and self.main_window.map_dropdown:
                # Verificar si el mapa existe en la lista
                maps = [self.main_window.map_dropdown.cget("values")]
                if maps and self.current_map in maps[0]:
                    self.main_window.map_dropdown.set(self.current_map)
                    
            # Actualizar la información interna
            if self.current_server and self.current_map:
                self.update_server_map_context(self.current_server, self.current_map)
                
        except Exception as e:
            self.logger.error(f"Error al restaurar selección: {e}")
    
    def update_server_map_context(self, server_name, map_name):
        """Actualizar el contexto actual del servidor/mapa"""
        old_server = self.current_server
        old_map = self.current_map
        
        self.current_server = server_name
        self.current_map = map_name
        
        # Guardar la selección actual
        self.save_current_server_map()
        
        # Si cambió el servidor o mapa, recargar mods
        if old_server != server_name or old_map != map_name:
            self.load_installed_mods()
            self.refresh_installed_tab()
            self.refresh_favorites_tab()
            self.update_mods_ids_entry()
            
            self.show_message(f"📍 Cambiado a: {server_name} - {map_name}", "info")
    
    def save_current_server_map(self):
        """Guardar el servidor y mapa actual"""
        try:
            if self.current_server:
                self.config_manager.set("app", "last_server", self.current_server)
            if self.current_map:
                self.config_manager.set("app", "last_map", self.current_map)
            self.config_manager.save()
        except Exception as e:
            self.logger.error(f"Error al guardar servidor/mapa actual: {e}")
    
    def get_mods_key(self):
        """Obtener clave única para los mods del servidor/mapa actual"""
        if self.current_server and self.current_map:
            return f"{self.current_server}_{self.current_map}"
        return "default"
        
    def load_installed_mods(self):
        """Cargar mods instalados desde archivo por servidor/mapa"""
        try:
            data_dir = self.get_data_directory()
            mods_file = os.path.join(data_dir, "installed_mods_by_server.json")
            
            all_mods = {}
            if os.path.exists(mods_file):
                with open(mods_file, 'r', encoding='utf-8') as f:
                    all_mods = json.load(f)
            
            # Cargar mods específicos del servidor/mapa actual
            mods_key = self.get_mods_key()
            self.installed_mods = all_mods.get(mods_key, [])
            
            # Actualizar entry con IDs del servidor/mapa actual
            self.update_mods_ids_entry()
            
            self.logger.info(f"Cargados {len(self.installed_mods)} mods para {mods_key}")
                
        except Exception as e:
            self.logger.error(f"Error al cargar mods instalados: {e}")
            self.installed_mods = []
            
    def save_installed_mods(self):
        """Guardar mods instalados a archivo por servidor/mapa"""
        try:
            data_dir = self.get_data_directory()
            mods_file = os.path.join(data_dir, "installed_mods_by_server.json")
            
            # Cargar archivo existente
            all_mods = {}
            if os.path.exists(mods_file):
                with open(mods_file, 'r', encoding='utf-8') as f:
                    all_mods = json.load(f)
            
            # Actualizar mods del servidor/mapa actual
            mods_key = self.get_mods_key()
            all_mods[mods_key] = self.installed_mods
            
            # Guardar archivo completo
            with open(mods_file, 'w', encoding='utf-8') as f:
                json.dump(all_mods, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Guardados {len(self.installed_mods)} mods para {mods_key}")
                
        except Exception as e:
            self.logger.error(f"Error al guardar mods instalados: {e}")
            
    def load_favorite_mods(self):
        """Cargar mods favoritos desde archivo"""
        try:
            data_dir = self.get_data_directory()
            favs_file = os.path.join(data_dir, "favorite_mods.json")
            
            if os.path.exists(favs_file):
                with open(favs_file, 'r', encoding='utf-8') as f:
                    self.favorite_mods = json.load(f)
                    
        except Exception as e:
            self.logger.error(f"Error al cargar mods favoritos: {e}")
            
    def save_favorite_mods(self):
        """Guardar mods favoritos a archivo"""
        try:
            data_dir = self.get_data_directory()
            favs_file = os.path.join(data_dir, "favorite_mods.json")
            
            with open(favs_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorite_mods, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error al guardar mods favoritos: {e}")
            
    def show_message(self, message, msg_type="info"):
        """Mostrar mensaje temporal"""
        # Si tenemos main_window, usar su sistema de logs
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'add_log_message'):
            # Mapear tipos de mensaje a iconos
            icons = {
                "success": "✅",
                "error": "❌", 
                "info": "ℹ️",
                "warning": "⚠️"
            }
            icon = icons.get(msg_type, "📝")
            self.main_window.add_log_message(f"{icon} {message}")
        else:
            # Fallback: crear ventana temporal para mostrar mensajes
            msg_window = ctk.CTkToplevel(self)
            msg_window.title("Gestor de Mods")
            msg_window.geometry("400x100")
            msg_window.transient(self)
            msg_window.grab_set()
            
            # Centrar ventana
            msg_window.geometry("+%d+%d" % (
                self.winfo_rootx() + 50,
                self.winfo_rooty() + 50
            ))
            
            # Color según tipo
            colors = {
                "success": "#4CAF50",
                "error": "#f44336",
                "info": "#2196F3",
                "warning": "#FF9800"
            }
            
            color = colors.get(msg_type, "#2196F3")
            
            # Label con mensaje
            msg_label = ctk.CTkLabel(
                msg_window,
                text=message,
                font=("Arial", 12),
                text_color="white"
            )
            msg_label.pack(expand=True, fill="both", padx=20, pady=20)
            
            # Botón OK
            ok_button = ctk.CTkButton(
                msg_window,
                text="OK",
                command=msg_window.destroy,
                fg_color=color,
                width=80,
                height=30
            )
            ok_button.pack(pady=10)
            
            # Auto cerrar después de 3 segundos para mensajes de éxito/info
            if msg_type in ["success", "info"]:
                self.after(3000, lambda: msg_window.destroy() if msg_window.winfo_exists() else None)
