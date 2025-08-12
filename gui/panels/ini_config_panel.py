import customtkinter as ctk
import configparser
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple
import logging
import tkinter as tk


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
        self.id = self.widget.after(800, self.showtip)  # Aumentar delay a 800ms

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
        self.id = None

    def schedule_hide(self):
        self.cancel_hide()
        self.hide_id = self.widget.after(100, self.hidetip)  # Ocultar rápidamente

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
            tw.after(5000, self.hidetip)  # Auto-ocultar después de 5 segundos
            
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


class IniConfigPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger, main_window=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        
        # Rutas de archivos INI
        self.game_user_settings_path = None
        self.game_ini_path = None
        
        # Datos de configuración
        self.ini_data = {}
        self.original_values = {}
        self.changed_values = {}
        self.field_mappings = {}  # Mapeo de campos a secciones/archivos
        
        # Para preservar formato original
        self.original_file_content = {}  # Contenido original línea por línea
        self.case_sensitive_keys = {}    # Mapeo de claves con formato original
        
        # Empaquetar el frame principal
        self.pack(fill="both", expand=True)
        
        self.create_widgets()
        self.load_ini_paths()
        self.load_ini_files()
        # Poblar los campos después de que se hayan creado todos los widgets
        self.populate_form_fields()
        
        # Configurar auto-recarga cuando cambie el servidor
        self.setup_auto_reload()
        
    def create_widgets(self):
        """Crear todos los widgets del panel"""
        # Frame principal con scroll
        self.main_scrollable_frame = ctk.CTkScrollableFrame(self)
        self.main_scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título principal
        title_frame = ctk.CTkFrame(self.main_scrollable_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="⚙️ Configuración de Archivos INI",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side="left")
        
        # Botones de control
        control_frame = ctk.CTkFrame(self.main_scrollable_frame, fg_color="transparent")
        control_frame.pack(fill="x", pady=(0, 20))
        
        self.reload_button = ctk.CTkButton(
            control_frame,
            text="🔄 Recargar Archivos",
            command=self.reload_ini_files,
            width=150,
            height=35
        )
        self.reload_button.pack(side="left", padx=(0, 10))
        
        self.force_reload_button = ctk.CTkButton(
            control_frame,
            text="🔄 Forzar Recarga",
            command=self.force_reload_ini,
            width=150,
            height=35,
            fg_color=("orange", "darkorange")
        )
        self.force_reload_button.pack(side="left", padx=(0, 10))
        
        self.save_all_button = ctk.CTkButton(
            control_frame,
            text="💾 Guardar Todos los Cambios",
            command=self.save_all_changes,
            width=200,
            height=35,
            fg_color=("green", "darkgreen")
        )
        self.save_all_button.pack(side="left", padx=(0, 10))
        
        self.discard_button = ctk.CTkButton(
            control_frame,
            text="❌ Descartar Cambios",
            command=self.discard_changes,
            width=150,
            height=35,
            fg_color=("red", "darkred")
        )
        self.discard_button.pack(side="left", padx=(0, 10))
        
        # Indicador de estado
        self.status_label = ctk.CTkLabel(
            control_frame,
            text="✅ Archivos cargados correctamente",
            font=ctk.CTkFont(size=12),
            fg_color=("lightgreen", "darkgreen"),
            corner_radius=5,
            padx=10,
            pady=5
        )
        self.status_label.pack(side="right", padx=(10, 0))
        
        # Crear pestañas internas
        self.create_internal_tabs()
        
        # Frame de información
        info_frame = ctk.CTkFrame(self.main_scrollable_frame)
        
        # Información de archivos INI
        self.ini_info_label = ctk.CTkLabel(
            info_frame,
            text="📁 Información de archivos INI",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.ini_info_label.pack(pady=5)
        
        self.ini_status_label = ctk.CTkLabel(
            info_frame,
            text="⏳ Cargando información...",
            font=ctk.CTkFont(size=11)
        )
        self.ini_status_label.pack(pady=2)
        info_frame.pack(fill="x", pady=(0, 20))
        
        info_label = ctk.CTkLabel(
            info_frame,
            text="ℹ️ Los cambios se guardan automáticamente. Usa 'Guardar Todos los Cambios' para asegurar la persistencia.",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray70")
        )
        info_label.pack(pady=10)
        
    def create_internal_tabs(self):
        """Crear las pestañas internas para GUS y Game.ini"""
        # Frame para las pestañas
        self.tabs_frame = ctk.CTkFrame(self.main_scrollable_frame)
        self.tabs_frame.pack(fill="x", pady=(0, 20))
        
        # Botones de pestañas
        self.gus_tab_button = ctk.CTkButton(
            self.tabs_frame,
            text="📋 GameUserSettings.ini",
            command=lambda: self.switch_tab("gus"),
            width=200,
            height=35,
            fg_color=("blue", "darkblue")
        )
        self.gus_tab_button.pack(side="left", padx=(0, 5))
        
        self.game_tab_button = ctk.CTkButton(
            self.tabs_frame,
            text="🎮 Game.ini",
            command=lambda: self.switch_tab("game"),
            width=200,
            height=35,
            fg_color=("gray", "darkgray")
        )
        self.game_tab_button.pack(side="left", padx=(0, 5))
        
        # Frame para el contenido de las pestañas
        self.content_frame = ctk.CTkFrame(self.main_scrollable_frame)
        self.content_frame.pack(fill="x", pady=(0, 20))
        
        # Crear contenido de ambas pestañas
        self.create_gus_content()
        self.create_game_content()
        
        # Mostrar pestaña GUS por defecto
        self.current_tab = "gus"
        self.show_tab_content("gus")
        
    def switch_tab(self, tab_name):
        """Cambiar entre pestañas"""
        self.current_tab = tab_name
        self.show_tab_content(tab_name)
        
        # Actualizar colores de botones
        if tab_name == "gus":
            self.gus_tab_button.configure(fg_color=("blue", "darkblue"))
            self.game_tab_button.configure(fg_color=("gray", "darkgray"))
        else:
            self.gus_tab_button.configure(fg_color=("gray", "darkgray"))
            self.game_tab_button.configure(fg_color=("blue", "darkblue"))
            
    def show_tab_content(self, tab_name):
        """Mostrar el contenido de la pestaña seleccionada"""
        # Ocultar todo el contenido
        for widget in self.content_frame.winfo_children():
            widget.pack_forget()
            
        # Mostrar contenido de la pestaña seleccionada
        if tab_name == "gus":
            self.gus_content_frame.pack(fill="both", expand=True)
        else:
            self.game_content_frame.pack(fill="both", expand=True)
            
    def create_gus_content(self):
        """Crear contenido para GameUserSettings.ini"""
        self.gus_content_frame = ctk.CTkFrame(self.content_frame)
        
        # Crear acordeones para GUS
        self.create_gus_accordions()
        
    def create_game_content(self):
        """Crear contenido para Game.ini"""
        self.game_content_frame = ctk.CTkFrame(self.content_frame)
        
        # Crear acordeones para Game.ini
        self.create_game_accordions()
        
    def create_gus_accordions(self):
        """Crear acordeones para GameUserSettings.ini"""
        # Configuración de categorías para GUS
        self.gus_categories = {
            "PlayersAndTribes": {
                "title": "👥 Jugadores y Tribus",
                "description": "Configuración de jugadores, tribus y límites",
                "icon": "👥",
                "ini_section": "ServerSettings",
                "ini_file": "GameUserSettings"
            },
            "DifficultyAndProgression": {
                "title": "🎯 Dificultad y Progresión",
                "description": "Configuración de dificultad, XP y multiplicadores",
                "icon": "🎯",
                "ini_section": "ServerSettings",
                "ini_file": "GameUserSettings"
            },
            "NotificationsAndHUD": {
                "title": "🖥️ Notificaciones y HUD",
                "description": "Configuración de interfaz y notificaciones",
                "icon": "🖥️",
                "ini_section": "ServerSettings",
                "ini_file": "GameUserSettings"
            },
            "DayNightAndClimate": {
                "title": "🌅 Ciclo Día/Noche y Clima",
                "description": "Configuración de tiempo, clima y temperatura",
                "icon": "🌅",
                "ini_section": "ServerSettings",
                "ini_file": "GameUserSettings"
            },
            "HarvestingAndResources": {
                "title": "🌾 Recolección y Recursos",
                "description": "Configuración de recolección, recursos y crecimiento",
                "icon": "🌾",
                "ini_section": "ServerSettings",
                "ini_file": "GameUserSettings"
            },
            "BreedingAndReproduction": {
                "title": "💕 Crianza y Reproducción",
                "description": "Configuración de apareamiento, huevos y bebés",
                "icon": "💕",
                "ini_section": "ServerSettings",
                "ini_file": "GameUserSettings"
            },
            "TamingAndDinos": {
                "title": "🦕 Domesticación y Dinos",
                "description": "Configuración de domesticación y comportamiento de dinos",
                "icon": "🦕",
                "ini_section": "ServerSettings",
                "ini_file": "GameUserSettings"
            },
            "StructuresAndBuilding": {
                "title": "🏗️ Estructuras y Construcción",
                "description": "Configuración de construcción y estructuras",
                "icon": "🏗️",
                "ini_section": "ServerSettings",
                "ini_file": "GameUserSettings"
            },
            "DefensesAndTurrets": {
                "title": "🔫 Defensas y Torretas",
                "description": "Configuración de defensas automáticas",
                "icon": "🔫",
                "ini_section": "ServerSettings",
                "ini_file": "GameUserSettings"
            },
            "LootAndQuality": {
                "title": "💎 Loot y Calidad",
                "description": "Configuración de loot y calidad de ítems",
                "icon": "💎",
                "ini_section": "ServerSettings",
                "ini_file": "GameUserSettings"
            },
            "ItemsAndCrafting": {
                "title": "⚒️ Ítems y Crafteo",
                "description": "Configuración de ítems y habilidades de crafteo",
                "icon": "⚒️",
                "ini_section": "ServerSettings",
                "ini_file": "GameUserSettings"
            },
            "DecayAndTimes": {
                "title": "⏳ Decay y Tiempos",
                "description": "Configuración de descomposición y tiempos",
                "icon": "⏳",
                "ini_section": "ServerSettings",
                "ini_file": "GameUserSettings"
            },
            "PvEPvPAndRules": {
                "title": "⚔️ PvE, PvP y Reglas",
                "description": "Configuración de modos de juego y reglas del servidor",
                "icon": "⚔️",
                "ini_section": "ServerSettings",
                "ini_file": "GameUserSettings"
            },
            "SaveAndOthers": {
                "title": "💾 Guardado y Otros",
                "description": "Configuración de guardado y opciones adicionales",
                "icon": "💾",
                "ini_section": "ServerSettings",
                "ini_file": "GameUserSettings"
            },
            "NotificationsAndLogs": {
                "title": "📝 Notificaciones y Logs",
                "description": "Configuración de logs y notificaciones del servidor",
                "icon": "📝",
                "ini_section": "ServerSettings",
                "ini_file": "GameUserSettings"
            },
            "StasisAndOptimization": {
                "title": "⚡ Stasis y Optimización",
                "description": "Configuración de optimización y rendimiento",
                "icon": "⚡",
                "ini_section": "ServerSettings",
                "ini_file": "GameUserSettings"
            }
        }
        
        # Frame para los acordeones
        self.gus_accordions_frame = ctk.CTkFrame(self.gus_content_frame)
        self.gus_accordions_frame.pack(fill="x", pady=(0, 20))
        
        # Crear acordeones
        self.gus_accordion_widgets = {}
        
        for i, (category, info) in enumerate(self.gus_categories.items()):
            # Crear frame del acordeón
            accordion_frame = ctk.CTkFrame(self.gus_accordions_frame)
            accordion_frame.pack(fill="x", pady=(0, 10))
            
            # Header del acordeón
            header_frame = ctk.CTkFrame(accordion_frame, fg_color="transparent")
            header_frame.pack(fill="x", padx=10, pady=5)
            
            # Botón de expansión
            expand_button = ctk.CTkButton(
                header_frame,
                text=f"{info['icon']} {info['title']}",
                command=lambda cat=category: self.toggle_gus_accordion(cat),
                fg_color="transparent",
                text_color=("black", "white"),
                hover_color=("gray80", "gray30"),
                anchor="w",
                height=40
            )
            expand_button.pack(side="left", fill="x", expand=True)
            
            # Descripción
            desc_label = ctk.CTkLabel(
                header_frame,
                text=info['description'],
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray70")
            )
            desc_label.pack(side="right", padx=(10, 0))
            
            # Contenido del acordeón (inicialmente oculto)
            content_frame = ctk.CTkFrame(accordion_frame, fg_color="transparent")
            content_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            # Frame para los campos del formulario
            form_frame = ctk.CTkFrame(content_frame)
            form_frame.pack(fill="x", padx=10, pady=10)
            
            # Crear campos del formulario
            self.create_gus_form_fields(form_frame, category)
            
            # Guardar referencia
            self.gus_accordion_widgets[category] = {
                'frame': accordion_frame,
                'content': content_frame,
                'expanded': False,
                'form_frame': form_frame
            }
            
            # Ocultar contenido inicialmente
            content_frame.pack_forget()
            
    def create_gus_form_fields(self, form_frame, category):
        """Crear campos del formulario para GameUserSettings.ini"""
        if category == "PlayersAndTribes":
            fields = [
                ("MaxNumbersofPlayersInTribe", "Máximo de jugadores por tribu", "int"),
                ("MaxAlliancesPerTribe", "Máximo de alianzas por tribu", "int"),
                ("MaxTribeLogs", "Máximo de logs de tribu", "int"),
                ("PreventTribeAlliances", "Prevenir alianzas tribales", "bool"),
                ("TribeNameChangeCooldown", "Tiempo de espera para cambio de nombre de tribu", "float"),
                ("AllowAnyoneBabyImprintCuddle", "Permitir a cualquiera mimar bebés", "bool"),
                ("PreventMateBoost", "Prevenir boost de pareja", "bool"),
                ("MaxTamedDinos", "Máximo de dinos domesticados", "int"),
                ("MaxTamedDinos_SoftTameLimit", "Límite suave de dinos domesticados", "int"),
                ("MaxTamedDinos_SoftTameLimit_CountdownForDeletionDuration", "Duración cuenta regresiva para eliminación", "float"),
                ("MaxPersonalTamedDinos", "Máximo de dinos domesticados personales", "int")
            ]
        elif category == "DifficultyAndProgression":
            fields = [
                ("DifficultyOffset", "Offset de dificultad", "float"),
                ("OverrideOfficialDifficulty", "Anular dificultad oficial", "float"),
                ("XPMultiplier", "Multiplicador de XP", "float"),
                ("TamingSpeedMultiplier", "Multiplicador de velocidad de domesticación", "float"),
                ("DinoCountMultiplier", "Multiplicador de cantidad de dinos", "float"),
                ("OverrideSecondsUntilBuriedTreasureAutoReveals", "Segundos hasta auto-revelar tesoro enterrado", "int"),
                ("ServerHardcore", "Servidor hardcore", "bool")
            ]
        elif category == "NotificationsAndHUD":
            fields = [
                ("ServerCrosshair", "Mira del servidor", "bool"),
                ("ShowMapPlayerLocation", "Mostrar ubicación del jugador en mapa", "bool"),
                ("serverForceNoHud", "Forzar sin HUD", "bool"),
                ("ShowFloatingDamageText", "Mostrar texto de daño flotante", "bool"),
                ("AllowHideDamageSourceFromLogs", "Permitir ocultar fuente de daño en logs", "bool"),
                ("AllowHitMarkers", "Permitir marcadores de impacto", "bool"),
                ("bShowStatusNotificationMessages", "Mostrar mensajes de notificación de estado", "bool"),
                ("bShowChatBox", "Mostrar caja de chat", "bool"),
                ("bShowInfoButtons", "Mostrar botones de información", "bool")
            ]
        elif category == "DayNightAndClimate":
            fields = [
                ("DayCycleSpeedScale", "Escala de velocidad del ciclo diario", "float"),
                ("NightTimeSpeedScale", "Escala de velocidad nocturna", "float"),
                ("DayTimeSpeedScale", "Escala de velocidad diurna", "float"),
                ("BaseTemperatureMultiplier", "Multiplicador de temperatura base", "float"),
                ("DisableWeatherFog", "Deshabilitar niebla climática", "bool"),
                ("EnablePVEGamma", "Habilitar gamma PVE", "bool")
            ]
        elif category == "HarvestingAndResources":
            fields = [
                ("HarvestAmountMultiplier", "Multiplicador de cantidad de recolección", "float"),
                ("HarvestHealthMultiplier", "Multiplicador de salud de recolección", "float"),
                ("PlayerHarvestingDamageMultiplier", "Multiplicador de daño de recolección del jugador", "float"),
                ("DinoHarvestingDamageMultiplier", "Multiplicador de daño de recolección de dinos", "float"),
                ("ResourcesRespawnPeriodMultiplier", "Multiplicador de período de respawn de recursos", "float"),
                ("ResourceNoReplenishRadiusPlayers", "Radio de no reabastecimiento de recursos - jugadores", "float"),
                ("ResourceNoReplenishRadiusStructures", "Radio de no reabastecimiento de recursos - estructuras", "float"),
                ("StructurePreventResourceRadiusMultiplier", "Multiplicador de radio de prevención de recursos por estructuras", "float"),
                ("UseOptimizedHarvestingHealth", "Usar salud de recolección optimizada", "bool"),
                ("ClampResourceHarvestDamage", "Limitar daño de recolección de recursos", "bool"),
                ("CropGrowthSpeedMultiplier", "Multiplicador de velocidad de crecimiento de cultivos", "float"),
                ("CropDecaySpeedMultiplier", "Multiplicador de velocidad de descomposición de cultivos", "float"),
                ("PoopIntervalMultiplier", "Multiplicador de intervalo de excremento", "float"),
                ("HairGrowthSpeedMultiplier", "Multiplicador de velocidad de crecimiento de cabello", "float")
            ]
        elif category == "BreedingAndReproduction":
            fields = [
                ("BabyImprintingStatScaleMultiplier", "Multiplicador de escala de estadísticas de impronta de bebés", "float"),
                ("BabyImprintAmountMultiplier", "Multiplicador de cantidad de impronta de bebés", "float"),
                ("MatingIntervalMultiplier", "Multiplicador de intervalo de apareamiento", "float"),
                ("MatingSpeedMultiplier", "Multiplicador de velocidad de apareamiento", "float"),
                ("LayEggIntervalMultiplier", "Multiplicador de intervalo de puesta de huevos", "float"),
                ("EggHatchSpeedMultiplier", "Multiplicador de velocidad de eclosión de huevos", "float"),
                ("BabyMatureSpeedMultiplier", "Multiplicador de velocidad de maduración de bebés", "float"),
                ("BabyCuddleIntervalMultiplier", "Multiplicador de intervalo de mimos de bebés", "float"),
                ("BabyCuddleGracePeriodMultiplier", "Multiplicador de período de gracia de mimos de bebés", "float"),
                ("BabyCuddleLoseImprintQualitySpeedMultiplier", "Multiplicador de velocidad de pérdida de calidad de impronta", "float"),
                ("BabyFoodConsumptionSpeedMultiplier", "Multiplicador de velocidad de consumo de comida de bebés", "float"),
                ("DisableImprintDinoBuff", "Deshabilitar buff de impronta de dinos", "bool")
            ]
        elif category == "TamingAndDinos":
            fields = [
                ("PassiveTameIntervalMultiplier", "Multiplicador de intervalo de domesticación pasiva", "float"),
                ("bAllowTamedDinoRiding", "Permitir montar dinos domesticados", "bool"),
                ("bDisableDinoRiding", "Deshabilitar montar dinos", "bool"),
                ("bDisableDinoTaming", "Deshabilitar domesticación de dinos", "bool"),
                ("bUseTameLimitForStructuresOnly", "Usar límite de domesticación solo para estructuras", "bool"),
                ("bForceCanRideFliers", "Forzar poder montar voladores", "bool"),
                ("ForceAllowCaveFlyers", "Forzar permitir voladores en cuevas", "bool"),
                ("AllowFlyingStaminaRecovery", "Permitir recuperación de stamina volando", "bool"),
                ("bAllowFlyerCarryPvE", "Permitir carga de voladores en PvE", "bool"),
                ("bFlyerPlatformAllowUnalignedDinoBasing", "Permitir dinos no alineados en plataforma de voladores", "bool"),
                ("TamedDinoCharacterFoodDrainMultiplier", "Multiplicador de drenaje de comida de dinos domesticados", "float"),
                ("TamedDinoTorporDrainMultiplier", "Multiplicador de drenaje de torpor de dinos domesticados", "float"),
                ("WildDinoCharacterFoodDrainMultiplier", "Multiplicador de drenaje de comida de dinos salvajes", "float"),
                ("WildDinoTorporDrainMultiplier", "Multiplicador de drenaje de torpor de dinos salvajes", "float"),
                ("DinoCharacterFoodDrainMultiplier", "Multiplicador de drenaje de comida de personaje dino", "float"),
                ("DinoCharacterStaminaDrainMultiplier", "Multiplicador de drenaje de stamina de personaje dino", "float"),
                ("DinoCharacterHealthRecoveryMultiplier", "Multiplicador de recuperación de salud de personaje dino", "float"),
                ("PlayerCharacterWaterDrainMultiplier", "Multiplicador de drenaje de agua del jugador", "float"),
                ("PlayerCharacterFoodDrainMultiplier", "Multiplicador de drenaje de comida del jugador", "float"),
                ("PlayerCharacterStaminaDrainMultiplier", "Multiplicador de drenaje de stamina del jugador", "float"),
                ("PlayerCharacterHealthRecoveryMultiplier", "Multiplicador de recuperación de salud del jugador", "float"),
                ("RaidDinoCharacterFoodDrainMultiplier", "Multiplicador de drenaje de comida de dinos de raid", "float")
            ]
        elif category == "StructuresAndBuilding":
            fields = [
                ("StructureDamageMultiplier", "Multiplicador de daño a estructuras", "float"),
                ("StructureResistanceMultiplier", "Multiplicador de resistencia de estructuras", "float"),
                ("StructureDamageRepairCooldown", "Tiempo de espera para reparar daño a estructuras", "float"),
                ("MaxStructuresInRange", "Máximo de estructuras en rango", "int"),
                ("TheMaxStructuresInRange", "El máximo de estructuras en rango", "int"),
                ("bForceAllStructureLocking", "Forzar bloqueo de todas las estructuras", "bool"),
                ("bDisableStructurePlacementCollision", "Deshabilitar colisión de colocación de estructuras", "bool"),
                ("bAllowPlatformSaddleMultiFloors", "Permitir múltiples pisos en silla de plataforma", "bool"),
                ("PlatformSaddleBuildAreaBoundsMultiplier", "Multiplicador de límites de área de construcción de silla de plataforma", "float"),
                ("MaxPlatformSaddleStructureLimit", "Límite máximo de estructuras en silla de plataforma", "int"),
                ("PersonalTamedDinosSaddleStructureCost", "Costo de estructura de silla de dinos domesticados personales", "int"),
                ("DestroyUnconnectedWaterPipes", "Destruir tuberías de agua desconectadas", "bool"),
                ("OverrideStructurePlatformPrevention", "Anular prevención de plataforma de estructuras", "bool"),
                ("EnableExtraStructurePreventionVolumes", "Habilitar volúmenes de prevención de estructura extra", "bool"),
                ("bIgnoreStructuresPreventionVolumes", "Ignorar volúmenes de prevención de estructuras", "bool"),
                ("bGenesisUseStructuresPreventionVolumes", "Genesis usar volúmenes de prevención de estructuras", "bool"),
                ("AlwaysAllowStructurePickup", "Siempre permitir recogida de estructuras", "bool"),
                ("StructurePickupTimeAfterPlacement", "Tiempo de recogida de estructura después de colocación", "float"),
                ("StructurePickupHoldDuration", "Duración de mantener para recoger estructura", "float"),
                ("AllowIntegratedSPlusStructures", "Permitir estructuras S+ integradas", "bool"),
                ("AutoDestroyOldStructuresMultiplier", "Multiplicador de auto-destrucción de estructuras viejas", "float"),
                ("AutoDestroyStructures", "Auto-destruir estructuras", "bool"),
                ("OnlyAutoDestroyCoreStructures", "Solo auto-destruir estructuras centrales", "bool"),
                ("OnlyDecayUnsnappedCoreStructures", "Solo decaer estructuras centrales no conectadas", "bool")
            ]
        elif category == "DefensesAndTurrets":
            fields = [
                ("bPassiveDefensesDamageRiderlessDinos", "Defensas pasivas dañan dinos sin jinete", "bool"),
                ("bLimitTurretsInRange", "Limitar torretas en rango", "bool"),
                ("LimitTurretsRange", "Rango límite de torretas", "int"),
                ("LimitTurretsNum", "Número límite de torretas", "int"),
                ("bHardLimitTurretsInRange", "Límite estricto de torretas en rango", "bool")
            ]
        elif category == "LootAndQuality":
            fields = [
                ("SupplyCrateLootQualityMultiplier", "Multiplicador de calidad de loot de cajas de suministro", "float"),
                ("FishingLootQualityMultiplier", "Multiplicador de calidad de loot de pesca", "float"),
                ("bDisableLootCrates", "Deshabilitar cajas de loot", "bool"),
                ("RandomSupplyCratePoints", "Puntos de cajas de suministro aleatorias", "bool")
            ]
        elif category == "ItemsAndCrafting":
            fields = [
                ("ItemStackSizeMultiplier", "Multiplicador de tamaño de pila de ítems", "float"),
                ("CraftingSkillBonusMultiplier", "Multiplicador de bonus de habilidad de crafteo", "float")
            ]
        elif category == "DecayAndTimes":
            fields = [
                ("GlobalItemDecompositionTimeMultiplier", "Multiplicador de tiempo de descomposición global de ítems", "float"),
                ("GlobalCorpseDecompositionTimeMultiplier", "Multiplicador de tiempo de descomposición global de cadáveres", "float"),
                ("GlobalSpoilingTimeMultiplier", "Multiplicador de tiempo de descomposición global", "float"),
                ("UseCorpseLifeSpanMultiplier", "Multiplicador de duración de vida de cadáveres", "float"),
                ("ClampItemSpoilingTimes", "Limitar tiempos de descomposición de ítems", "bool"),
                ("FastDecayInterval", "Intervalo de decaimiento rápido", "float"),
                ("AutoDestroyDecayedDinos", "Auto-destruir dinos decaídos", "bool")
            ]
        elif category == "PvEPvPAndRules":
            fields = [
                ("ServerPVE", "Servidor PvE", "bool"),
                ("PvEDinoDecayPeriodMultiplier", "Multiplicador de período de decaimiento de dinos PvE", "float"),
                ("bPvPDinoDecay", "Decaimiento de dinos PvP", "bool"),
                ("PvEStructureDecayPeriodMultiplier", "Multiplicador de período de decaimiento de estructuras PvE", "float"),
                ("PvEStructureDecayDestructionPeriod", "Período de destrucción por decaimiento de estructuras PvE", "float"),
                ("PvEAllowStructuresAtSupplyDrops", "Permitir estructuras en drops de suministro PvE", "bool"),
                ("bPvEDisableFriendlyFire", "Deshabilitar fuego amigo PvE", "bool"),
                ("bPvEAllowTribeWar", "Permitir guerra tribal PvE", "bool"),
                ("bPvEAllowTribeWarCancel", "Permitir cancelar guerra tribal PvE", "bool")
            ]
        elif category == "SaveAndOthers":
            fields = [
                ("AutoSavePeriodMinutes", "Período de auto-guardado en minutos", "float"),
                ("PreventSpawnAnimations", "Prevenir animaciones de spawn", "bool"),
                ("PreventDiseases", "Prevenir enfermedades", "bool"),
                ("NonPermanentDiseases", "Enfermedades no permanentes", "bool"),
                ("ServerAutoForceRespawnWildDinosInterval", "Intervalo de auto-forzar respawn de dinos salvajes", "float"),
                ("AllowCrateSpawnsOnTopOfStructures", "Permitir spawn de cajas encima de estructuras", "bool"),
                ("CrossARKAllowForeignDinoDownloads", "Permitir descargas de dinos extranjeros Cross-ARK", "bool"),
                ("noTributeDownloads", "Sin descargas de tributo", "bool"),
                ("PreventDownloadSurvivors", "Prevenir descarga de sobrevivientes", "bool"),
                ("PreventDownloadItems", "Prevenir descarga de ítems", "bool"),
                ("PreventDownloadDinos", "Prevenir descarga de dinos", "bool"),
                ("PreventUploadSurvivors", "Prevenir subida de sobrevivientes", "bool"),
                ("PreventUploadItems", "Prevenir subida de ítems", "bool"),
                ("PreventUploadDinos", "Prevenir subida de dinos", "bool"),
                ("MaxTributeDinos", "Máximo de dinos tributo", "int"),
                ("MaxTributeItems", "Máximo de ítems tributo", "int"),
                ("TributeItemExpirationSeconds", "Segundos de expiración de ítems tributo", "int"),
                ("TributeDinoExpirationSeconds", "Segundos de expiración de dinos tributo", "int"),
                ("TributeCharacterExpirationSeconds", "Segundos de expiración de personajes tributo", "int"),
                ("MinimumDinoReuploadInterval", "Intervalo mínimo de re-subida de dinos", "float")
            ]
        elif category == "NotificationsAndLogs":
            fields = [
                ("alwaysNotifyPlayerJoined", "Siempre notificar jugador unido", "bool"),
                ("alwaysNotifyPlayerLeft", "Siempre notificar jugador que se fue", "bool"),
                ("AdminLogging", "Logging de administrador", "bool")
            ]
        elif category == "StasisAndOptimization":
            fields = [
                ("NPCNetworkStasisRangeScalePlayerCountStart", "Inicio de escala de rango de stasis de red NPC por conteo de jugadores", "int"),
                ("NPCNetworkStasisRangeScalePlayerCountEnd", "Fin de escala de rango de stasis de red NPC por conteo de jugadores", "int"),
                ("NPCNetworkStasisRangeScalePercentEnd", "Porcentaje final de escala de rango de stasis de red NPC", "float")
            ]
        else:
            fields = []
        
        # Crear campos para esta categoría en 2 columnas
        self.create_fields_grid(form_frame, fields, category, "GameUserSettings")
        
    def toggle_gus_accordion(self, category):
        """Alternar la expansión de un acordeón de GUS"""
        accordion = self.gus_accordion_widgets[category]
        
        if accordion['expanded']:
            # Contraer
            accordion['content'].pack_forget()
            accordion['expanded'] = False
        else:
            # Expandir
            accordion['content'].pack(fill="x", padx=10, pady=(0, 10))
            accordion['expanded'] = True
            # Poblar los campos cuando se expande
            self.populate_category_fields(category)
            
    def create_game_accordions(self):
        """Crear acordeones para Game.ini"""
        # Configuración de categorías para Game.ini
        self.game_categories = {
            "ExperienceAndLevels": {
                "title": "⭐ Experiencia y Niveles",
                "description": "Configuración de XP, niveles y multiplicadores de experiencia",
                "icon": "⭐",
                "ini_section": "/Script/ShooterGame.ShooterGameMode",
                "ini_file": "Game"
            },
            "StatsAndMultipliers": {
                "title": "📊 Estadísticas y Multiplicadores",
                "description": "Multiplicadores de estadísticas por nivel y daño",
                "icon": "📊",
                "ini_section": "/Script/ShooterGame.ShooterGameMode",
                "ini_file": "Game"
            },
            "BreedingAndReproduction": {
                "title": "💕 Crianza y Reproducción",
                "description": "Configuración de apareamiento, huevos, bebés e impronta",
                "icon": "💕",
                "ini_section": "/Script/ShooterGame.ShooterGameMode",
                "ini_file": "Game"
            },
            "TamingAndDinos": {
                "title": "🦕 Domesticación y Dinos",
                "description": "Configuración de domesticación, montar y comportamiento de dinos",
                "icon": "🦕",
                "ini_section": "/Script/ShooterGame.ShooterGameMode",
                "ini_file": "Game"
            },
            "ResourcesAndGrowth": {
                "title": "🌱 Recursos y Crecimiento",
                "description": "Recolección, recursos, cultivos y crecimiento",
                "icon": "🌱",
                "ini_section": "/Script/ShooterGame.ShooterGameMode",
                "ini_file": "Game"
            },
            "LootAndRecipes": {
                "title": "💎 Loot y Recetas",
                "description": "Calidad de loot y recetas personalizadas",
                "icon": "💎",
                "ini_section": "/Script/ShooterGame.ShooterGameMode",
                "ini_file": "Game"
            },
            "TimesAndDecay": {
                "title": "⏰ Tiempos y Descomposición",
                "description": "Configuración de durabilidad, descomposición y tiempos",
                "icon": "⏰",
                "ini_section": "/Script/ShooterGame.ShooterGameMode",
                "ini_file": "Game"
            },
            "PlatformsAndStructures": {
                "title": "🏗️ Plataformas y Estructuras",
                "description": "Configuración de construcción y estructuras",
                "icon": "🏗️",
                "ini_section": "/Script/ShooterGame.ShooterGameMode",
                "ini_file": "Game"
            },
            "DefensesAndTurrets": {
                "title": "🔫 Defensas y Torretas",
                "description": "Configuración de defensas automáticas y torretas",
                "icon": "🔫",
                "ini_section": "/Script/ShooterGame.ShooterGameMode",
                "ini_file": "Game"
            },
            "PlayersAndTribes": {
                "title": "👥 Jugadores y Tribus",
                "description": "Configuración de jugadores, tribus y PvP",
                "icon": "👥",
                "ini_section": "/Script/ShooterGame.ShooterGameMode",
                "ini_file": "Game"
            },
            "GameModeAndGeneral": {
                "title": "🎮 Modo de Juego General",
                "description": "Opciones generales del modo de juego",
                "icon": "🎮",
                "ini_section": "/Script/ShooterGame.ShooterGameMode",
                "ini_file": "Game"
            }
        }
        
        # Frame para los acordeones
        self.game_accordions_frame = ctk.CTkFrame(self.game_content_frame)
        self.game_accordions_frame.pack(fill="x", pady=(0, 20))
        
        # Crear acordeones
        self.game_accordion_widgets = {}
        
        for i, (category, info) in enumerate(self.game_categories.items()):
            # Crear frame del acordeón
            accordion_frame = ctk.CTkFrame(self.game_accordions_frame)
            accordion_frame.pack(fill="x", pady=(0, 10))
            
            # Header del acordeón
            header_frame = ctk.CTkFrame(accordion_frame, fg_color="transparent")
            header_frame.pack(fill="x", padx=10, pady=5)
            
            # Botón de expansión
            expand_button = ctk.CTkButton(
                header_frame,
                text=f"{info['icon']} {info['title']}",
                command=lambda cat=category: self.toggle_game_accordion(cat),
                fg_color="transparent",
                text_color=("black", "white"),
                hover_color=("gray80", "gray30"),
                anchor="w",
                height=40
            )
            expand_button.pack(side="left", fill="x", expand=True)
            
            # Descripción
            desc_label = ctk.CTkLabel(
                header_frame,
                text=info['description'],
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray70")
            )
            desc_label.pack(side="right", padx=(10, 0))
            
            # Contenido del acordeón (inicialmente oculto)
            content_frame = ctk.CTkFrame(accordion_frame, fg_color="transparent")
            content_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            # Frame para los campos del formulario
            form_frame = ctk.CTkFrame(content_frame)
            form_frame.pack(fill="x", padx=10, pady=10)
            
            # Crear campos del formulario
            self.create_game_form_fields(form_frame, category)
            
            # Guardar referencia
            self.game_accordion_widgets[category] = {
                'frame': accordion_frame,
                'content': content_frame,
                'expanded': False,
                'form_frame': form_frame
            }
            
            # Ocultar contenido inicialmente
            content_frame.pack_forget()
            
    def create_game_form_fields(self, form_frame, category):
        """Crear campos del formulario para Game.ini"""
        if category == "ExperienceAndLevels":
            fields = [
                ("LevelExperienceRampOverrides", "Curva de experiencia por nivel", "string"),
                ("OverrideMaxExperiencePointsPlayer", "XP máximo de jugador", "int"),
                ("OverrideMaxExperiencePointsDino", "XP máximo de dino", "int"),
                ("TamedDinoCharacterLevelCount", "Niveles máximos de dino domesticado", "int"),
                ("CraftXPMultiplier", "Multiplicador de XP por crafteo", "float"),
                ("GenericXPMultiplier", "Multiplicador genérico de XP", "float"),
                ("HarvestXPMultiplier", "Multiplicador de XP por recolección", "float"),
                ("KillXPMultiplier", "Multiplicador de XP por matanza", "float"),
                ("SpecialXPMultiplier", "Multiplicador especial de XP", "float"),
                ("TamedDinoXPMultiplier", "Multiplicador de XP de dino domesticado", "float")
            ]
        elif category == "StatsAndMultipliers":
            fields = [
                ("PerLevelStatsMultiplier_Player[7]", "Multiplicador de estadística por nivel - Jugador [7]", "float"),
                ("PerLevelStatsMultiplier_DinoTamed[7]", "Multiplicador de estadística por nivel - Dino domesticado [7]", "float"),
                ("PlayerHarvestingDamageMultiplier", "Multiplicador de daño de recolección del jugador", "float"),
                ("DinoHarvestingDamageMultiplier", "Multiplicador de daño de recolección de dinos", "float"),
                ("DinoTurretDamageMultiplier", "Multiplicador de daño de torretas de dinos", "float")
            ]
        elif category == "BreedingAndReproduction":
            fields = [
                ("BabyImprintingStatScaleMultiplier", "Multiplicador de estadísticas de impronta", "float"),
                ("BabyImprintAmountMultiplier", "Multiplicador de cantidad de impronta", "float"),
                ("MatingIntervalMultiplier", "Multiplicador de intervalo de apareamiento", "float"),
                ("MatingSpeedMultiplier", "Multiplicador de velocidad de apareamiento", "float"),
                ("LayEggIntervalMultiplier", "Multiplicador de intervalo de puesta de huevos", "float"),
                ("EggHatchSpeedMultiplier", "Multiplicador de velocidad de eclosión", "float"),
                ("BabyMatureSpeedMultiplier", "Multiplicador de velocidad de maduración", "float"),
                ("BabyCuddleIntervalMultiplier", "Multiplicador de intervalo de mimos", "float"),
                ("BabyCuddleGracePeriodMultiplier", "Multiplicador de período de gracia de mimos", "float"),
                ("BabyCuddleLoseImprintQualitySpeedMultiplier", "Multiplicador de pérdida de calidad de impronta", "float"),
                ("BabyFoodConsumptionSpeedMultiplier", "Multiplicador de consumo de comida de bebés", "float")
            ]
        elif category == "TamingAndDinos":
            fields = [
                ("bAllowTamedDinoRiding", "Permitir montar dinos domesticados", "bool"),
                ("TamedDinoRidingWaitTime", "Tiempo de espera para montar dino domesticado", "float"),
                ("bDisableDinoRiding", "Deshabilitar montar dinos", "bool"),
                ("bDisableDinoTaming", "Deshabilitar domesticación de dinos", "bool"),
                ("bAllowFlyerSpeedLeveling", "Permitir nivelar velocidad de voladores", "bool"),
                ("bFlyerPlatformAllowUnalignedDinoBasing", "Permitir dinos no alineados en plataforma de voladores", "bool"),
                ("TamedDinoCharacterFoodDrainMultiplier", "Multiplicador de drenaje de comida de dino domesticado", "float"),
                ("TamedDinoTorporDrainMultiplier", "Multiplicador de drenaje de torpor de dino domesticado", "float"),
                ("WildDinoCharacterFoodDrainMultiplier", "Multiplicador de drenaje de comida de dino salvaje", "float"),
                ("WildDinoTorporDrainMultiplier", "Multiplicador de drenaje de torpor de dino salvaje", "float"),
                ("PassiveTameIntervalMultiplier", "Multiplicador de intervalo de tameo pasivo", "float")
            ]
        elif category == "ResourcesAndGrowth":
            fields = [
                ("ResourceNoReplenishRadiusPlayers", "Radio de no reabastecimiento de recursos - jugadores", "float"),
                ("ResourceNoReplenishRadiusStructures", "Radio de no reabastecimiento de recursos - estructuras", "float"),
                ("CropGrowthSpeedMultiplier", "Multiplicador de crecimiento de cultivos", "float"),
                ("CropDecaySpeedMultiplier", "Multiplicador de descomposición de cultivos", "float"),
                ("PoopIntervalMultiplier", "Multiplicador de intervalo de excremento", "float")
            ]
        elif category == "LootAndRecipes":
            fields = [
                ("SupplyCrateLootQualityMultiplier", "Multiplicador de calidad de loot de cajas de suministro", "float"),
                ("FishingLootQualityMultiplier", "Multiplicador de calidad de loot de pesca", "float"),
                ("bAllowCustomRecipes", "Permitir recetas personalizadas", "bool"),
                ("CustomRecipeEffectivenessMultiplier", "Multiplicador de efectividad de recetas personalizadas", "float"),
                ("CustomRecipeSkillMultiplier", "Multiplicador de habilidad de recetas personalizadas", "float")
            ]
        elif category == "TimesAndDecay":
            fields = [
                ("UseCorpseLifeSpanMultiplier", "Multiplicador de duración de cadáveres", "float"),
                ("GlobalPoweredBatteryDurabilityDecreasePerSecond", "Disminución de durabilidad de batería por segundo", "float"),
                ("GlobalItemDecompositionTimeMultiplier", "Multiplicador de tiempo de descomposición de ítems", "float"),
                ("GlobalCorpseDecompositionTimeMultiplier", "Multiplicador de tiempo de descomposición de cadáveres", "float"),
                ("GlobalSpoilingTimeMultiplier", "Multiplicador de tiempo de descomposición de comida", "float"),
                ("StructureDamageRepairCooldown", "Tiempo de espera para reparar daño a estructuras", "float"),
                ("FastDecayInterval", "Intervalo de decaimiento rápido", "float"),
                ("BaseTemperatureMultiplier", "Multiplicador de temperatura base", "float"),
                ("HairGrowthSpeedMultiplier", "Multiplicador de crecimiento de cabello", "float")
            ]
        elif category == "PlatformsAndStructures":
            fields = [
                ("bAllowPlatformSaddleMultiFloors", "Permitir múltiples pisos en silla de plataforma", "bool"),
                ("PlatformSaddleBuildAreaBoundsMultiplier", "Multiplicador de área de construcción en silla de plataforma", "float"),
                ("bDisableStructurePlacementCollision", "Deshabilitar colisión de colocación de estructuras", "bool")
            ]
        elif category == "DefensesAndTurrets":
            fields = [
                ("bPassiveDefensesDamageRiderlessDinos", "Defensas pasivas dañan dinos sin jinete", "bool"),
                ("bLimitTurretsInRange", "Limitar torretas en rango", "bool"),
                ("LimitTurretsRange", "Rango de torretas", "int"),
                ("LimitTurretsNum", "Número de torretas", "int"),
                ("bHardLimitTurretsInRange", "Límite estricto de torretas en rango", "bool"),
                ("bUseTameLimitForStructuresOnly", "Usar límite de domesticación solo para estructuras", "bool")
            ]
        elif category == "PlayersAndTribes":
            fields = [
                ("MaxTribeLogs", "Máximo de logs de tribu", "int"),
                ("bDisableFriendlyFire", "Deshabilitar fuego amigo", "bool"),
                ("bPvEDisableFriendlyFire", "Deshabilitar fuego amigo en PvE", "bool"),
                ("bPvEAllowTribeWar", "Permitir guerra tribal en PvE", "bool"),
                ("bPvEAllowTribeWarCancel", "Permitir cancelar guerra tribal en PvE", "bool"),
                ("KickIdlePlayersPeriod", "Período para expulsar jugadores inactivos", "int")
            ]
        elif category == "GameModeAndGeneral":
            fields = [
                ("bAutoUnlockAllEngrams", "Desbloquear todos los engramas automáticamente", "bool"),
                ("bDisableGenesisMissions", "Deshabilitar misiones Genesis", "bool"),
                ("bShowCreativeMode", "Mostrar modo creativo", "bool"),
                ("bAllowUnlimitedRespecs", "Permitir respecs ilimitados", "bool"),
                ("bDisableLootCrates", "Deshabilitar cajas de loot", "bool"),
                ("bUseCorpseLocator", "Usar localizador de cadáveres", "bool"),
                ("bAutoPvETimer", "Auto temporizador PvE", "bool"),
                ("bAutoPvEUseSystemTime", "Usar hora del sistema para PvE", "bool"),
                ("AutoPvEStartTimeSeconds", "Hora de inicio PvE (segundos)", "int"),
                ("AutoPvEStopTimeSeconds", "Hora de fin PvE (segundos)", "int")
            ]
        else:
            fields = []
        
        # Crear campos para esta categoría en 2 columnas
        self.create_fields_grid(form_frame, fields, category, "Game")
        
    def toggle_game_accordion(self, category):
        """Alternar la expansión de un acordeón de Game.ini"""
        accordion = self.game_accordion_widgets[category]
        
        if accordion['expanded']:
            # Contraer
            accordion['content'].pack_forget()
            accordion['expanded'] = False
        else:
            # Expandir
            accordion['content'].pack(fill="x", padx=10, pady=(0, 10))
            accordion['expanded'] = True
            # Poblar los campos cuando se expande
            self.populate_category_fields(category)
            
    def create_fields_grid(self, form_frame, fields, category, file_type):
        """Crear campos del formulario en una cuadrícula de 2 columnas"""
        # Configurar columnas para el layout de 2 columnas
        form_frame.grid_columnconfigure(0, weight=1)  # Primera columna de etiquetas
        form_frame.grid_columnconfigure(1, weight=1)  # Primera columna de campos
        form_frame.grid_columnconfigure(2, weight=0)  # Controles primera columna
        form_frame.grid_columnconfigure(3, weight=1)  # Segunda columna de etiquetas
        form_frame.grid_columnconfigure(4, weight=1)  # Segunda columna de campos
        form_frame.grid_columnconfigure(5, weight=0)  # Controles segunda columna
        
        # Crear campos para esta categoría en 2 columnas
        for i, (field_name, field_label, field_type) in enumerate(fields):
            # Calcular posición en la cuadrícula (2 columnas)
            grid_row = i // 2
            grid_col = (i % 2) * 3  # Cada campo ocupa 3 columnas
            
            # Etiqueta del campo
            label = ctk.CTkLabel(
                form_frame,
                text=field_label,
                font=ctk.CTkFont(size=11),
                anchor="w"
            )
            label.grid(row=grid_row, column=grid_col, padx=(10, 5), pady=3, sticky="w")
            
            # Campo de entrada según el tipo
            if field_type == "bool":
                # Switch para booleanos
                var = ctk.BooleanVar()
                field_widget = ctk.CTkSwitch(
                    form_frame,
                    text="",
                    variable=var,
                    command=lambda name=field_name, var=var: self.on_field_change(name, var.get())
                )
                field_widget.grid(row=grid_row, column=grid_col + 1, padx=5, pady=3, sticky="w")
                
            elif field_type == "int":
                # Campo numérico con incrementadores
                field_widget = ctk.CTkEntry(
                    form_frame,
                    placeholder_text="0",
                    width=120
                )
                field_widget.grid(row=grid_row, column=grid_col + 1, padx=5, pady=3, sticky="w")
                
                # Botones de incremento/decremento
                inc_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
                inc_frame.grid(row=grid_row, column=grid_col + 2, padx=(2, 10), pady=3)
                
                inc_btn = ctk.CTkButton(
                    inc_frame,
                    text="+",
                    width=25,
                    height=22,
                    command=lambda w=field_widget: self.increment_value(w, 1)
                )
                inc_btn.pack(side="left", padx=(0, 1))
                
                dec_btn = ctk.CTkButton(
                    inc_frame,
                    text="-",
                    width=25,
                    height=22,
                    command=lambda w=field_widget: self.increment_value(w, -1)
                )
                dec_btn.pack(side="left")
                
                # Binding para cambios
                field_widget.bind("<KeyRelease>", lambda e, name=field_name, w=field_widget: self.on_field_change(name, w.get()))
                
            elif field_type == "float":
                # Campo numérico para flotantes con incrementadores
                field_widget = ctk.CTkEntry(
                    form_frame,
                    placeholder_text="0.0",
                    width=120
                )
                field_widget.grid(row=grid_row, column=grid_col + 1, padx=5, pady=3, sticky="w")
                
                # Botones de incremento/decremento para flotantes también
                inc_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
                inc_frame.grid(row=grid_row, column=grid_col + 2, padx=(2, 10), pady=3)
                
                inc_btn = ctk.CTkButton(
                    inc_frame,
                    text="+",
                    width=25,
                    height=22,
                    command=lambda w=field_widget: self.increment_value(w, 0.1)
                )
                inc_btn.pack(side="left", padx=(0, 1))
                
                dec_btn = ctk.CTkButton(
                    inc_frame,
                    text="-",
                    width=25,
                    height=22,
                    command=lambda w=field_widget: self.increment_value(w, -0.1)
                )
                dec_btn.pack(side="left")
                
                # Binding para cambios
                field_widget.bind("<KeyRelease>", lambda e, name=field_name, w=field_widget: self.on_field_change(name, w.get()))
                
            else:  # string
                # Campo de texto
                field_widget = ctk.CTkEntry(
                    form_frame,
                    placeholder_text="Valor",
                    width=150
                )
                field_widget.grid(row=grid_row, column=grid_col + 1, padx=5, pady=3, sticky="w")
                
                # Binding para cambios
                field_widget.bind("<KeyRelease>", lambda e, name=field_name, w=field_widget: self.on_field_change(name, w.get()))
            
            # Agregar tooltip con descripción al campo
            tooltip_text = f"{field_name}\n\n{field_label}"
            if hasattr(field_widget, '_tkinter_widget'):
                # Para widgets de CustomTkinter, usar el widget interno de tkinter
                ToolTip(field_widget, tooltip_text)
            else:
                # Para widgets normales
                ToolTip(field_widget, tooltip_text)
            
            # También agregar tooltip a la etiqueta
            label_tooltip_text = f"Variable: {field_name}\nDescripción: {field_label}"
            ToolTip(label, label_tooltip_text)
            
            # Guardar referencia al widget y mapeo
            if not hasattr(self, 'field_widgets'):
                self.field_widgets = {}
            if category not in self.field_widgets:
                self.field_widgets[category] = {}
            
            self.field_widgets[category][field_name] = field_widget
            
            # Mapear campo a su sección y archivo INI
            if file_type == "GameUserSettings":
                category_info = self.gus_categories.get(category, {})
            else:
                category_info = self.game_categories.get(category, {})
                
            if category_info:
                self.field_mappings[field_name] = {
                    'section': category_info['ini_section'],
                    'file': category_info['ini_file']
                }
        
        # Configurar el peso de las filas
        total_rows = (len(fields) + 1) // 2  # Calcular filas necesarias para 2 columnas
        for i in range(total_rows):
            form_frame.grid_rowconfigure(i, weight=0)
            
    def increment_value(self, widget, delta):
        """Incrementar o decrementar valor numérico"""
        try:
            current_value = float(widget.get() or "0")
            new_value = current_value + delta
            widget.delete(0, "end")
            widget.insert(0, str(new_value))
            
            # Obtener el nombre del campo
            for category, fields in self.field_widgets.items():
                for field_name, field_widget in fields.items():
                    if field_widget == widget:
                        self.on_field_change(field_name, new_value)
                        break
        except ValueError:
            pass
            
    def on_field_change(self, field_name, value):
        """Manejar cambios en los campos del formulario"""
        # Marcar como cambiado
        self.changed_values[field_name] = value
        
        # Actualizar estado visual
        self.update_status_indicator()
        
        # Guardar automáticamente después de un pequeño retraso
        self.after(1000, self.auto_save_changes)
        
    def update_status_indicator(self):
        """Actualizar el indicador de estado"""
        if self.changed_values:
            self.status_label.configure(
                text=f"⚠️ {len(self.changed_values)} cambios pendientes",
                fg_color=("orange", "darkorange")
            )
            self.save_all_button.configure(
                text=f"💾 Guardar {len(self.changed_values)} Cambios",
                fg_color=("orange", "darkorange")
            )
        else:
            self.status_label.configure(
                text="✅ Archivos cargados correctamente",
                fg_color=("lightgreen", "darkgreen")
            )
            self.save_all_button.configure(
                text="💾 Guardar Todos los Cambios",
                fg_color=("green", "darkgreen")
            )
            
        # Actualizar información de archivos INI
        self.update_ini_info()
            
    def update_ini_info(self):
        """Actualizar información de archivos INI"""
        try:
            info_text = []
            
            if self.game_user_settings_path:
                if os.path.exists(self.game_user_settings_path):
                    info_text.append(f"✅ GameUserSettings.ini: {os.path.basename(self.game_user_settings_path)}")
                else:
                    info_text.append(f"❌ GameUserSettings.ini: No encontrado")
            else:
                info_text.append("❌ GameUserSettings.ini: Ruta no configurada")
                
            if self.game_ini_path:
                if os.path.exists(self.game_ini_path):
                    info_text.append(f"✅ Game.ini: {os.path.basename(self.game_ini_path)}")
                else:
                    info_text.append(f"❌ Game.ini: No encontrado")
            else:
                info_text.append("❌ Game.ini: Ruta no configurada")
                
            if info_text:
                self.ini_status_label.configure(text="\n".join(info_text))
            else:
                self.ini_status_label.configure(text="❌ No se encontraron archivos INI")
                
        except Exception as e:
            self.logger.error(f"Error al actualizar información INI: {e}")
            self.ini_status_label.configure(text=f"❌ Error al cargar información: {str(e)}")
            
    def load_ini_paths(self):
        """Cargar las rutas de los archivos INI"""
        try:
            # Obtener la ruta del servidor desde la configuración
            server_path = self.config_manager.get("server", "server_path", default="")
            root_path = self.config_manager.get("server", "root_path", default="")
            last_server = self.config_manager.get("app", "last_server", default="")
            
            # Determinar la ruta del servidor
            if server_path:
                server_dir = Path(server_path)
            elif root_path and last_server:
                # Usar root_path + last_server como fallback
                server_dir = Path(root_path) / last_server
            else:
                # Último fallback: buscar en rutas comunes
                possible_paths = [
                    Path("D:/ASA/Prueba"),
                    Path("D:/ASA/Prueba2"),
                    Path("C:/Users/roder/OneDrive/Desktop/Nuevacarpeta/servers"),
                    Path("C:/Users/roder/OneDrive/Desktop/Nuevacarpeta/ARK_Server/ARK_Server")
                ]
                
                for path in possible_paths:
                    if path.exists():
                        server_dir = path
                        break
                else:
                    server_dir = None
            
            if server_dir and server_dir.exists():
                # Buscar GameUserSettings.ini
                gus_path = server_dir / "ShooterGame" / "Saved" / "Config" / "WindowsServer" / "GameUserSettings.ini"
                if gus_path.exists():
                    self.game_user_settings_path = str(gus_path)
                    self.logger.info(f"GameUserSettings.ini encontrado en: {gus_path}")
                else:
                    self.logger.warning(f"GameUserSettings.ini no encontrado en: {gus_path}")
                
                # Buscar Game.ini
                game_ini_path = server_dir / "ShooterGame" / "Saved" / "Config" / "WindowsServer" / "Game.ini"
                if game_ini_path.exists():
                    self.game_ini_path = str(game_ini_path)
                    self.logger.info(f"Game.ini encontrado en: {game_ini_path}")
                else:
                    self.logger.warning(f"Game.ini no encontrado en: {game_ini_path}")
                    
            else:
                self.logger.warning(f"No se pudo determinar la ruta del servidor. server_dir: {server_dir}")
                    
            self.logger.info(f"Rutas INI cargadas - GUS: {self.game_user_settings_path}, Game: {self.game_ini_path}")
            
        except Exception as e:
            self.logger.error(f"Error al cargar rutas INI: {e}")
    
    def setup_auto_reload(self):
        """Configurar auto-recarga de archivos INI"""
        try:
            # Programar recarga periódica cada 2 segundos para detectar cambios de servidor
            if hasattr(self, 'main_window') and self.main_window:
                self.main_window.root.after(2000, self.check_for_server_changes)
        except Exception as e:
            self.logger.error(f"Error configurando auto-recarga: {e}")
    
    def check_for_server_changes(self):
        """Verificar si el servidor seleccionado ha cambiado"""
        try:
            if hasattr(self, 'main_window') and self.main_window:
                current_server = getattr(self.main_window, 'selected_server', None)
                
                # Debug: mostrar servidor actual
                if hasattr(self, '_last_server'):
                    self.logger.debug(f"🔄 Verificando cambios - Servidor anterior: {self._last_server}, Servidor actual: {current_server}")
                else:
                    self.logger.debug(f"🔄 Primera verificación - Servidor actual: {current_server}")
                
                # Verificar si el servidor cambió
                if not hasattr(self, '_last_server') or self._last_server != current_server:
                    self._last_server = current_server
                    if current_server:
                        self.logger.info(f"🔄 Servidor cambió a: {current_server}, recargando archivos INI...")
                        self.reload_for_new_server()
                    else:
                        self.logger.debug("Servidor no seleccionado, esperando...")
                else:
                    self.logger.debug(f"✅ Servidor sin cambios: {current_server}")
                
                # Programar próxima verificación
                self.main_window.root.after(2000, self.check_for_server_changes)
            else:
                self.logger.debug("MainWindow no disponible, esperando...")
                # Programar próxima verificación incluso si no hay main_window
                if hasattr(self, 'root') and self.root:
                    self.root.after(2000, self.check_for_server_changes)
        except Exception as e:
            self.logger.error(f"❌ Error verificando cambios de servidor: {e}")
            import traceback
            self.logger.error(f"Traceback completo: {traceback.format_exc()}")
    
    def reload_for_new_server(self):
        """Recargar archivos INI para el nuevo servidor seleccionado"""
        try:
            self.logger.info("🔄 Iniciando recarga de archivos INI para nuevo servidor...")
            
            # Limpiar datos de formato anterior
            self.original_file_content.clear()
            self.case_sensitive_keys.clear()
            self.logger.debug("Datos de formato anterior limpiados")
            
            # Recargar rutas y archivos
            self.logger.debug("Recargando rutas INI...")
            self.load_ini_paths()
            self.logger.debug("Recargando archivos INI...")
            self.load_ini_files()
            
            # Repoblar todos los campos
            self.logger.debug("Repoblando campos del formulario...")
            self.populate_form_fields()
            
            self.logger.info("✅ Archivos INI recargados para el nuevo servidor")
            
            # Actualizar indicador de estado
            if hasattr(self, 'status_label'):
                self.status_label.configure(
                    text="🔄 Archivos INI recargados para nuevo servidor",
                    fg_color=("blue", "darkblue")
                )
                
        except Exception as e:
            self.logger.error(f"❌ Error recargando archivos INI: {e}")
            import traceback
            self.logger.error(f"Traceback completo: {traceback.format_exc()}")
    
    def force_reload_ini(self):
        """Forzar recarga manual de archivos INI"""
        try:
            self.reload_for_new_server()
            # Mostrar mensaje de confirmación
            if hasattr(self, 'status_label'):
                self.status_label.configure(
                    text="✅ Archivos INI recargados manualmente",
                    fg_color=("green", "darkgreen")
                )
        except Exception as e:
            self.logger.error(f"Error en recarga manual: {e}")
            
    def load_ini_files(self):
        """Cargar y parsear archivos INI"""
        try:
            self.ini_data = {}
            self.original_values = {}
            
            # Cargar GameUserSettings.ini
            if self.game_user_settings_path and os.path.exists(self.game_user_settings_path):
                self.load_single_ini_file(self.game_user_settings_path, "GameUserSettings")
                
            # Cargar Game.ini
            if self.game_ini_path and os.path.exists(self.game_ini_path):
                self.load_single_ini_file(self.game_ini_path, "Game")
                
            # Los valores se cargarán automáticamente después de crear los widgets
            # No llamar populate_form_fields aquí, se hará después de crear los widgets
            
            self.logger.info("Archivos INI cargados correctamente")
            self.update_status_indicator()
            
        except Exception as e:
            self.logger.error(f"Error al cargar archivos INI: {e}")
            self.status_label.configure(
                text=f"❌ Error al cargar archivos: {str(e)}",
                fg_color=("red", "darkred")
            )
            
    def load_single_ini_file(self, file_path, file_type):
        """Cargar un archivo INI específico preservando formato original"""
        try:
            self.logger.info(f"Cargando archivo {file_type} desde: {file_path}")
            
            # Leer contenido original línea por línea para preservar formato
            with open(file_path, 'r', encoding='utf-8') as f:
                original_lines = f.readlines()
            
            self.logger.debug(f"Archivo {file_type} leído, {len(original_lines)} líneas")
            
            # Guardar contenido original
            self.original_file_content[file_type] = original_lines
            
            # Crear un configparser que preserve las mayúsculas y sea tolerante a errores
            config = configparser.RawConfigParser()
            config.optionxform = str  # Preservar mayúsculas y minúsculas
            
            # Intentar cargar con manejo de errores más robusto
            try:
                config.read(file_path, encoding='utf-8')
            except configparser.DuplicateOptionError as e:
                self.logger.warning(f"Archivo {file_type} tiene opciones duplicadas, intentando cargar manualmente: {e}")
                # Cargar manualmente línea por línea para evitar errores de duplicados
                config = self.load_ini_manually(original_lines, file_type)
            except Exception as e:
                self.logger.error(f"Error al parsear {file_type}, intentando carga manual: {e}")
                config = self.load_ini_manually(original_lines, file_type)
            
            self.ini_data[file_type] = config
            
            self.logger.info(f"Archivo {file_type} parseado, secciones encontradas: {list(config.sections())}")
            
            # Construir mapeo de claves con formato original
            if file_type not in self.case_sensitive_keys:
                self.case_sensitive_keys[file_type] = {}
            
            # Guardar valores originales con mapeo completo
            total_fields = 0
            for section in config.sections():
                if section not in self.case_sensitive_keys[file_type]:
                    self.case_sensitive_keys[file_type][section] = {}
                
                section_fields = list(config.items(section))
                self.logger.debug(f"Sección {section} tiene {len(section_fields)} campos")
                total_fields += len(section_fields)
                    
                for key, value in config.items(section):
                    # Guardar la clave original con su formato
                    self.case_sensitive_keys[file_type][section][key.lower()] = key
                    
                    full_key = f"{section}.{key}"
                    self.original_values[full_key] = value
                    # También guardar solo el nombre del campo para búsquedas
                    self.original_values[key] = value
                    self.original_values[key.lower()] = value  # Para búsquedas insensibles a mayúsculas
                    
            self.logger.info(f"Archivo {file_type} cargado preservando formato original. Total campos: {total_fields}")
                    
        except Exception as e:
            self.logger.error(f"Error al cargar {file_type}: {e}")
            import traceback
            self.logger.error(f"Traceback completo: {traceback.format_exc()}")
            
    def load_ini_manually(self, lines, file_type):
        """Cargar archivo INI manualmente para evitar errores de duplicados"""
        try:
            config = configparser.RawConfigParser()
            config.optionxform = str
            
            current_section = None
            seen_options = set()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Líneas vacías o comentarios
                if not line or line.startswith(';') or line.startswith('#'):
                    continue
                
                # Nueva sección
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    if not config.has_section(current_section):
                        config.add_section(current_section)
                    seen_options.clear()
                    continue
                
                # Opción key=value
                if '=' in line and current_section:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Evitar duplicados
                    option_key = f"{current_section}.{key}"
                    if option_key not in seen_options:
                        config.set(current_section, key, value)
                        seen_options.add(option_key)
                    else:
                        self.logger.warning(f"Omitiendo opción duplicada en línea {line_num}: {key}")
            
            self.logger.info(f"Archivo {file_type} cargado manualmente, secciones: {list(config.sections())}")
            return config
            
        except Exception as e:
            self.logger.error(f"Error en carga manual de {file_type}: {e}")
            # Crear config vacío como fallback
            return configparser.RawConfigParser()
            
    def populate_form_fields(self):
        """Poblar los campos del formulario con valores actuales"""
        try:
            # Verificar que los widgets se hayan creado
            if not hasattr(self, 'field_widgets') or not self.field_widgets:
                self.logger.debug("Los widgets aún no se han creado, esperando...")
                return
                
            for category, fields in self.field_widgets.items():
                for field_name, field_widget in fields.items():
                    # Buscar el valor en los datos INI
                    value = self.find_field_value(field_name)
                    if value is not None:
                        self.set_field_value(field_widget, value)
                        self.logger.debug(f"Campo {field_name} poblado con valor: {value}")
                    else:
                        self.logger.debug(f"No se encontró valor para el campo: {field_name}")
                        
        except Exception as e:
            self.logger.error(f"Error al poblar campos: {e}")
            
    def populate_category_fields(self, category):
        """Poblar los campos de una categoría específica"""
        try:
            if not hasattr(self, 'field_widgets') or category not in self.field_widgets:
                return
                
            fields = self.field_widgets[category]
            for field_name, field_widget in fields.items():
                # Buscar el valor en los datos INI
                value = self.find_field_value(field_name)
                if value is not None:
                    self.set_field_value(field_widget, value)
                    self.logger.debug(f"Campo {field_name} de categoría {category} poblado con valor: {value}")
                else:
                    self.logger.debug(f"No se encontró valor para el campo: {field_name} en categoría {category}")
                    
        except Exception as e:
            self.logger.error(f"Error al poblar campos de categoría {category}: {e}")
            
    def find_field_value(self, field_name):
        """Buscar el valor de un campo en los archivos INI"""
        # Debug: mostrar qué se está buscando
        self.logger.debug(f"Buscando valor para campo: {field_name}")
        
        # Primero buscar en el mapeo de campos para encontrar la sección correcta
        if field_name in self.field_mappings:
            mapping = self.field_mappings[field_name]
            target_file = mapping['file']
            target_section = mapping['section']
            
            self.logger.debug(f"Campo {field_name} mapeado a: archivo={target_file}, sección={target_section}")
            
            # Buscar en el archivo y sección específicos
            if target_file in self.ini_data:
                config = self.ini_data[target_file]
                self.logger.debug(f"Archivo {target_file} encontrado, secciones disponibles: {list(config.sections())}")
                
                if target_section in config:
                    self.logger.debug(f"Sección {target_section} encontrada, campos disponibles: {list(config[target_section].keys())}")
                    if field_name in config[target_section]:
                        value = config[target_section][field_name]
                        self.logger.debug(f"Valor encontrado para {field_name}: {value}")
                        return value
                    else:
                        self.logger.debug(f"Campo {field_name} no encontrado en sección {target_section}")
                else:
                    self.logger.debug(f"Sección {target_section} no encontrada en archivo {target_file}")
            else:
                self.logger.debug(f"Archivo {target_file} no encontrado en ini_data")
        else:
            self.logger.debug(f"Campo {field_name} no tiene mapeo")
        
        # Fallback: buscar en todas las secciones de todos los archivos
        self.logger.debug("Intentando búsqueda fallback...")
        for file_type, config in self.ini_data.items():
            self.logger.debug(f"Revisando archivo {file_type}, secciones: {list(config.sections())}")
            for section in config.sections():
                if field_name in config[section]:
                    value = config[section][field_name]
                    self.logger.debug(f"Valor encontrado en fallback: {field_name} = {value} (archivo: {file_type}, sección: {section})")
                    return value
        
        # Si no se encuentra, buscar en valores originales
        self.logger.debug("Buscando en valores originales...")
        for key, value in self.original_values.items():
            if key.endswith(f".{field_name}"):
                self.logger.debug(f"Valor encontrado en originales: {key} = {value}")
                return value
                
        self.logger.debug(f"Campo {field_name} no encontrado en ningún lugar")
        return None
        
    def set_field_value(self, widget, value):
        """Establecer el valor de un campo del formulario"""
        try:
            if isinstance(widget, ctk.CTkSwitch):
                # Para switches booleanos
                bool_value = str(value).lower() in ('true', '1', 'yes', 'on')
                if bool_value:
                    widget.select()
                else:
                    widget.deselect()
                self.logger.debug(f"Switch {widget} configurado a: {bool_value}")
            else:
                # Para campos de texto/número
                widget.delete(0, "end")
                widget.insert(0, str(value))
                self.logger.debug(f"Campo {widget} configurado a: {value}")
        except Exception as e:
            self.logger.debug(f"Error al establecer valor en widget: {e}")
            
    def auto_save_changes(self):
        """Guardar cambios automáticamente"""
        if self.changed_values:
            self.save_changes_to_ini()
            
    def save_all_changes(self):
        """Guardar todos los cambios pendientes"""
        if self.changed_values:
            self.save_changes_to_ini()
            self.changed_values.clear()
            self.update_status_indicator()
            self.status_label.configure(
                text="✅ Cambios guardados correctamente",
                fg_color=("lightgreen", "darkgreen")
            )
        else:
            self.status_label.configure(
                text="ℹ️ No hay cambios pendientes",
                fg_color=("lightblue", "darkblue")
            )
            
    def save_changes_to_ini(self):
        """Guardar cambios en los archivos INI preservando formato"""
        try:
            # Aplicar cambios a los datos INI
            for field_name, value in self.changed_values.items():
                self.apply_change_to_ini(field_name, value)
                
            # Guardar archivos preservando formato
            self.save_ini_files()
            
            self.logger.info(f"Guardados {len(self.changed_values)} cambios en archivos INI")
            
        except Exception as e:
            self.logger.error(f"Error al guardar cambios: {e}")
            self.status_label.configure(
                text=f"❌ Error al guardar: {str(e)}",
                fg_color=("red", "darkred")
            )
            
    def apply_change_to_ini(self, field_name, value):
        """Aplicar un cambio a los datos INI"""
        if field_name in self.field_mappings:
            mapping = self.field_mappings[field_name]
            target_file = mapping['file']
            target_section = mapping['section']
            
            # Aplicar cambio
            if target_file in self.ini_data:
                if target_section not in self.ini_data[target_file]:
                    self.ini_data[target_file].add_section(target_section)
                self.ini_data[target_file][target_section][field_name] = str(value)
                
                # Actualizar valores originales
                full_key = f"{target_section}.{field_name}"
                self.original_values[full_key] = str(value)
                self.original_values[field_name] = str(value)
        
    def save_ini_files(self):
        """Guardar archivos INI preservando formato"""
        try:
            # Guardar GameUserSettings.ini
            if "GameUserSettings" in self.ini_data:
                self.save_single_ini_file(self.game_user_settings_path, self.ini_data["GameUserSettings"])
                
            # Guardar Game.ini
            if "Game" in self.ini_data:
                self.save_single_ini_file(self.game_ini_path, self.ini_data["Game"])
                
        except Exception as e:
            self.logger.error(f"Error al guardar archivos INI: {e}")
            raise
            
    def save_single_ini_file(self, file_path, config):
        """Guardar un archivo INI específico preservando formato original"""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Determinar el tipo de archivo
            file_type = "Game" if "Game.ini" in file_path else "GameUserSettings"
            
            # Si tenemos contenido original, preservar formato
            if file_type in self.original_file_content:
                self.save_ini_preserving_format(file_path, file_type, config)
            else:
                # Fallback al método original
                with open(file_path, 'w', encoding='utf-8') as f:
                    config.write(f, space_around_delimiters=False)
                
        except Exception as e:
            self.logger.error(f"Error al guardar {file_path}: {e}")
            raise
    
    def save_ini_preserving_format(self, file_path, file_type, config):
        """Guardar INI preservando formato original y solo modificando valores cambiados"""
        try:
            original_lines = self.original_file_content[file_type]
            modified_lines = []
            
            current_section = None
            
            for line in original_lines:
                original_line = line
                stripped_line = line.strip()
                
                # Detectar sección
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
                    
                    # Buscar si este campo tiene un valor modificado
                    modified_value = None
                    for field_name, new_value in self.changed_values.items():
                        if field_name in self.field_mappings:
                            mapping = self.field_mappings[field_name]
                            if (mapping['file'] == file_type and 
                                mapping['section'] == current_section and
                                field_name.lower() == original_key.lower()):
                                modified_value = str(new_value)
                                break
                    
                    if modified_value is not None:
                        # Preservar espacios y formato original, solo cambiar el valor
                        prefix = line[:line.find('=') + 1]
                        suffix = '\n' if line.endswith('\n') else ''
                        modified_line = f"{prefix}{modified_value}{suffix}"
                        modified_lines.append(modified_line)
                        self.logger.debug(f"Modificado: {original_key} = {modified_value}")
                    else:
                        # Mantener línea original
                        modified_lines.append(original_line)
                else:
                    # Mantener línea original
                    modified_lines.append(original_line)
            
            # Escribir archivo modificado
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(modified_lines)
                
            self.logger.info(f"Archivo {file_path} guardado preservando formato original")
            
        except Exception as e:
            self.logger.error(f"Error preservando formato de {file_path}: {e}")
            # Fallback al método original
            with open(file_path, 'w', encoding='utf-8') as f:
                config.write(f, space_around_delimiters=False)
            
    def reload_ini_files(self):
        """Recargar archivos INI desde disco"""
        try:
            self.logger.info("Recargando archivos INI...")
            
            # Limpiar cambios pendientes
            self.changed_values.clear()
            self.original_file_content.clear()
            self.case_sensitive_keys.clear()
            
            # Recargar rutas
            self.load_ini_paths()
            
            # Recargar archivos
            self.load_ini_files()
            
            # Poblar campos
            self.populate_form_fields()
            
            self.status_label.configure(
                text="✅ Archivos recargados correctamente",
                fg_color=("lightgreen", "darkgreen")
            )
            
            self.logger.info("Archivos INI recargados correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al recargar archivos INI: {e}")
            self.status_label.configure(
                text=f"❌ Error al recargar: {str(e)}",
                fg_color=("red", "darkred")
            )
            
    def force_reload_ini(self):
        """Forzar recarga completa de archivos INI"""
        try:
            self.logger.info("Forzando recarga completa de archivos INI...")
            
            # Limpiar todo
            self.changed_values.clear()
            self.ini_data.clear()
            self.original_values.clear()
            self.original_file_content.clear()
            self.case_sensitive_keys.clear()
            
            # Recargar rutas
            self.load_ini_paths()
            
            # Recargar archivos
            self.load_ini_files()
            
            # Poblar campos
            self.populate_form_fields()
            
            self.status_label.configure(
                text="✅ Recarga forzada completada",
                fg_color=("lightgreen", "darkgreen")
            )
            
            self.logger.info("Recarga forzada de archivos INI completada")
            
        except Exception as e:
            self.logger.error(f"Error en recarga forzada: {e}")
            self.status_label.configure(
                text=f"❌ Error en recarga forzada: {str(e)}",
                fg_color=("red", "darkred")
            )
            
    def discard_changes(self):
        """Descartar cambios pendientes"""
        if self.changed_values:
            self.changed_values.clear()
            self.populate_form_fields()  # Restaurar valores originales
            self.update_status_indicator()
            
            self.status_label.configure(
                text="✅ Cambios descartados",
                fg_color=("lightgreen", "darkgreen")
            )
            
            self.logger.info("Cambios descartados correctamente")
        else:
            self.status_label.configure(
                text="ℹ️ No hay cambios para descartar",
                fg_color=("lightblue", "darkblue")
            )
