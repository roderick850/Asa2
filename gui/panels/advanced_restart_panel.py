import customtkinter as ctk
import os
import json
import threading
import time
import schedule
from datetime import datetime, timedelta
from tkinter import messagebox

class AdvancedRestartPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger, main_window):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        self.current_server_name = None
        
        # Archivos de configuración
        self.restart_config_file = "data/restart_config.json"
        self.restart_history_file = "data/restart_history.json"
        self.restart_configs = {}  # {server_name: {config_data}}
        self.restart_history = {}  # {server_name: [{restart_info}]}
        
        # Estado del programador
        self.restart_scheduler_enabled = False
        self.restart_scheduler_thread = None
        self.stop_restart_scheduler = threading.Event()
        

        
        self.create_widgets()
        self.load_all_restart_configs()
        self.load_restart_history()
        self.update_server_selection(self.main_window.selected_server if self.main_window else None)
        self.pack(fill="both", expand=True)

    def create_widgets(self):
        """Crear interfaz principal del panel de reinicios"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # 1. Título y estado
        self.create_header()
        
        # 2. Configuración de reinicios
        self.create_restart_config_section()
        
        # 3. Controles de reinicio
        self.create_restart_controls()

    def create_header(self):
        """Crear sección de título y estado"""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Título
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔄 Sistema de Reinicios Programados",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=5)
        
        # Frame para estado y próximo reinicio
        status_container = ctk.CTkFrame(header_frame)
        status_container.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        
        # Estado del sistema
        self.restart_status_label = ctk.CTkLabel(
            status_container,
            text="⏹️ Inactivo",
            font=ctk.CTkFont(size=12)
        )
        self.restart_status_label.pack(side="left", padx=(8, 15))
        
        # Próximo reinicio
        self.next_restart_info = ctk.CTkLabel(
            status_container,
            text="Próximo reinicio: Deshabilitado",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.next_restart_info.pack(side="left", padx=(0, 8))

    def create_restart_config_section(self):
        """Crear sección de configuración"""
        config_frame = ctk.CTkFrame(self)
        config_frame.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")
        config_frame.grid_columnconfigure(1, weight=1)
        
        # Título de configuración
        config_title = ctk.CTkLabel(
            config_frame,
            text="⚙️ Configuración de Reinicios",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        config_title.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Crear pestañas para organizar configuración
        self.config_tabview = ctk.CTkTabview(config_frame)
        self.config_tabview.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        # Pestaña Reinicios
        self.create_restart_schedule_tab()
        
        # Pestaña Actualizaciones
        self.create_update_schedule_tab()
        
        # Pestaña Opciones
        self.create_options_tab()
        
        # Pestaña Historial
        self.create_history_tab()

    def create_restart_schedule_tab(self):
        """Crear pestaña de programación de reinicios"""
        restart_tab = self.config_tabview.add("🔄 Reinicios")
        restart_tab.grid_columnconfigure(1, weight=1)
        
        # Habilitar reinicios programados
        self.restart_enabled_var = ctk.BooleanVar()
        self.restart_enabled_check = ctk.CTkCheckBox(
            restart_tab,
            text="Habilitar reinicios programados",
            variable=self.restart_enabled_var,
            command=self.on_restart_enabled_change
        )
        self.restart_enabled_check.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        # Selección de días de la semana
        days_label = ctk.CTkLabel(restart_tab, text="Días de la semana:", font=ctk.CTkFont(weight="bold"))
        days_label.grid(row=1, column=0, padx=10, pady=(10, 5), sticky="w")
        
        self.days_frame = ctk.CTkFrame(restart_tab)
        self.days_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        self.day_vars = {}
        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        for i, day in enumerate(days):
            var = ctk.BooleanVar()
            check = ctk.CTkCheckBox(self.days_frame, text=day, variable=var)
            check.grid(row=0, column=i, padx=5, pady=5)
            self.day_vars[day] = var
        
        # Horas de reinicio
        hours_label = ctk.CTkLabel(restart_tab, text="Horas de reinicio:", font=ctk.CTkFont(weight="bold"))
        hours_label.grid(row=3, column=0, padx=10, pady=(15, 5), sticky="w")
        
        self.hours_frame = ctk.CTkFrame(restart_tab)
        self.hours_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        # Lista de horas
        self.restart_hours_text = ctk.CTkTextbox(self.hours_frame, height=60)
        self.restart_hours_text.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.restart_hours_text.insert("0.0", "00:00, 06:00, 12:00, 18:00")
        
        hours_info = ctk.CTkLabel(
            self.hours_frame, 
            text="Formato: HH:MM separadas por comas (ej: 00:00, 06:00, 12:00, 18:00)",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        hours_info.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="w")
        
        self.hours_frame.grid_columnconfigure(0, weight=1)

    def create_update_schedule_tab(self):
        """Crear pestaña de programación de actualizaciones"""
        update_tab = self.config_tabview.add("📥 Actualizaciones")
        update_tab.grid_columnconfigure(1, weight=1)
        
        # Descripción del funcionamiento
        desc_label = ctk.CTkLabel(
            update_tab,
            text="Las actualizaciones se ejecutan automáticamente durante los reinicios programados",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="blue"
        )
        desc_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        # Opción 1: Actualizar siempre
        self.update_always_var = ctk.BooleanVar(value=True)
        self.update_always_check = ctk.CTkCheckBox(
            update_tab,
            text="Actualizar servidor en TODOS los reinicios automáticos",
            variable=self.update_always_var,
            command=self.on_update_mode_change
        )
        self.update_always_check.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        # Separador
        separator = ctk.CTkLabel(update_tab, text="── O ──", text_color="gray")
        separator.grid(row=2, column=0, columnspan=2, padx=10, pady=5)
        
        # Opción 2: Días específicos
        self.update_specific_days_var = ctk.BooleanVar()
        self.update_specific_days_check = ctk.CTkCheckBox(
            update_tab,
            text="Actualizar solo en días específicos:",
            variable=self.update_specific_days_var,
            command=self.on_update_mode_change
        )
        self.update_specific_days_check.grid(row=3, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        
        # Selección de días para actualizaciones
        self.update_days_frame = ctk.CTkFrame(update_tab)
        self.update_days_frame.grid(row=4, column=0, columnspan=2, padx=30, pady=5, sticky="ew")
        
        self.update_day_vars = {}
        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        for i, day in enumerate(days):
            var = ctk.BooleanVar()
            check = ctk.CTkCheckBox(self.update_days_frame, text=day, variable=var, state="disabled")
            check.grid(row=0, column=i, padx=5, pady=5)
            self.update_day_vars[day] = var
        
        # Información adicional
        info_label = ctk.CTkLabel(
            update_tab,
            text="💡 Las actualizaciones se ejecutan ANTES del reinicio:\n"
                 "1. Detener servidor\n"
                 "2. Actualizar servidor\n"
                 "3. Backup (si está habilitado)\n"
                 "4. Saveworld (si está habilitado)\n"
                 "5. Iniciar servidor",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            justify="left"
        )
        info_label.grid(row=5, column=0, columnspan=2, padx=10, pady=15, sticky="w")

    def create_options_tab(self):
        """Crear pestaña de opciones"""
        options_tab = self.config_tabview.add("⚙️ Opciones")
        options_tab.grid_columnconfigure(1, weight=1)
        
        # Backup antes del reinicio
        self.backup_before_restart_var = ctk.BooleanVar(value=True)
        self.backup_before_restart_check = ctk.CTkCheckBox(
            options_tab,
            text="Realizar backup antes del reinicio",
            variable=self.backup_before_restart_var
        )
        self.backup_before_restart_check.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        # Saveworld antes del reinicio
        self.saveworld_before_restart_var = ctk.BooleanVar(value=True)
        self.saveworld_before_restart_check = ctk.CTkCheckBox(
            options_tab,
            text="Ejecutar saveworld (RCON) antes del reinicio",
            variable=self.saveworld_before_restart_var
        )
        self.saveworld_before_restart_check.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        # Avisos por RCON
        rcon_warnings_label = ctk.CTkLabel(options_tab, text="Avisos por RCON:", font=ctk.CTkFont(weight="bold"))
        rcon_warnings_label.grid(row=2, column=0, columnspan=3, padx=10, pady=(15, 5), sticky="w")
        
        # Habilitar avisos RCON
        self.rcon_warnings_var = ctk.BooleanVar(value=True)
        self.rcon_warnings_check = ctk.CTkCheckBox(
            options_tab,
            text="Enviar avisos por RCON antes del reinicio",
            variable=self.rcon_warnings_var
        )
        self.rcon_warnings_check.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="w")
        
        # Intervalos de aviso
        intervals_label = ctk.CTkLabel(options_tab, text="Intervalos de aviso (minutos):")
        intervals_label.grid(row=4, column=0, padx=10, pady=(10, 5), sticky="w")
        
        self.warning_intervals_entry = ctk.CTkEntry(options_tab, placeholder_text="15, 10, 5, 2, 1")
        self.warning_intervals_entry.grid(row=4, column=1, columnspan=2, padx=10, pady=(10, 5), sticky="ew")
        self.warning_intervals_entry.insert(0, "15, 10, 5, 2, 1")
        
        intervals_info = ctk.CTkLabel(
            options_tab, 
            text="Separar con comas (ej: 15, 10, 5, 2, 1)",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        intervals_info.grid(row=5, column=1, columnspan=2, padx=10, pady=(0, 5), sticky="w")
        
        # Mensaje personalizado
        message_label = ctk.CTkLabel(options_tab, text="Mensaje de aviso:")
        message_label.grid(row=6, column=0, padx=10, pady=(10, 5), sticky="w")
        
        self.warning_message_text = ctk.CTkTextbox(options_tab, height=60)
        self.warning_message_text.grid(row=7, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        self.warning_message_text.insert("0.0", "⚠️ ATENCIÓN: El servidor se reiniciará en {time} minuto(s). Por favor, encuentra un lugar seguro.")
        
        message_info = ctk.CTkLabel(
            options_tab,
            text="Usa {time} para mostrar el tiempo restante",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        message_info.grid(row=8, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="w")
        
        # Botón guardar configuración
        save_config_button = ctk.CTkButton(
            options_tab,
            text="💾 Guardar Configuración",
            command=self.save_restart_config,
            width=200
        )
        save_config_button.grid(row=9, column=0, columnspan=3, padx=10, pady=20)

    def create_history_tab(self):
        """Crear pestaña de historial de reinicios"""
        history_tab = self.config_tabview.add("📚 Historial")
        history_tab.grid_columnconfigure(0, weight=1)
        history_tab.grid_rowconfigure(1, weight=1)
        
        # Título del historial
        self.history_title = ctk.CTkLabel(
            history_tab,
            text="📚 Historial de Reinicios",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.history_title.grid(row=0, column=0, pady=(5, 5))
        
        # Lista de reinicios con scroll
        self.history_scroll = ctk.CTkScrollableFrame(history_tab)
        self.history_scroll.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="nsew")
        self.history_scroll.grid_columnconfigure(0, weight=1)
        
        # Botones de gestión del historial
        history_buttons = ctk.CTkFrame(history_tab)
        history_buttons.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        
        refresh_history_button = ctk.CTkButton(
            history_buttons,
            text="🔄 Actualizar",
            command=self.refresh_restart_history,
            width=100
        )
        refresh_history_button.pack(side="left", padx=5, pady=5)
        
        clear_history_button = ctk.CTkButton(
            history_buttons,
            text="🗑️ Limpiar Historial",
            command=self.clear_restart_history,
            width=140
        )
        clear_history_button.pack(side="left", padx=5, pady=5)

    def create_restart_controls(self):
        """Crear controles de reinicio"""
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        # Botón reinicio manual
        self.manual_restart_button = ctk.CTkButton(
            controls_frame,
            text="🔄 Reinicio Manual",
            command=self.start_manual_restart,
            width=200,
            height=40,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.manual_restart_button.pack(side="left", padx=10, pady=10)
        
        # Estado del reinicio
        self.restart_progress_frame = ctk.CTkFrame(controls_frame)
        self.restart_progress_frame.pack(side="left", padx=10, pady=10, fill="x", expand=True)
        
        self.restart_progress_label = ctk.CTkLabel(
            self.restart_progress_frame,
            text="Listo para reinicio",
            font=ctk.CTkFont(size=11)
        )
        self.restart_progress_label.pack(pady=(5, 0))
        
        self.restart_progress_bar = ctk.CTkProgressBar(self.restart_progress_frame)
        self.restart_progress_bar.pack(fill="x", padx=10, pady=(0, 5))
        self.restart_progress_bar.set(0)

    def on_restart_enabled_change(self):
        """Llamado cuando se cambia el estado del programador de reinicios"""
        if self.restart_enabled_var.get():
            self.start_restart_scheduler()
        else:
            self.stop_restart_scheduler_func()

    def on_update_mode_change(self):
        """Llamado cuando cambia el modo de actualización"""
        # Habilitar/deshabilitar checkboxes de días según el modo
        if self.update_always_var.get():
            # Si "siempre" está marcado, desmarcar "días específicos" y deshabilitar
            self.update_specific_days_var.set(False)
            for day, var in self.update_day_vars.items():
                checkbox = None
                for widget in self.update_days_frame.winfo_children():
                    if hasattr(widget, 'cget') and widget.cget('text') == day:
                        checkbox = widget
                        break
                if checkbox:
                    checkbox.configure(state="disabled")
        elif self.update_specific_days_var.get():
            # Si "días específicos" está marcado, desmarcar "siempre" y habilitar
            self.update_always_var.set(False)
            for day, var in self.update_day_vars.items():
                checkbox = None
                for widget in self.update_days_frame.winfo_children():
                    if hasattr(widget, 'cget') and widget.cget('text') == day:
                        checkbox = widget
                        break
                if checkbox:
                    checkbox.configure(state="normal")
        else:
            # Si ninguno está marcado, deshabilitar días específicos
            for day, var in self.update_day_vars.items():
                checkbox = None
                for widget in self.update_days_frame.winfo_children():
                    if hasattr(widget, 'cget') and widget.cget('text') == day:
                        checkbox = widget
                        break
                if checkbox:
                    checkbox.configure(state="disabled")

    def start_restart_scheduler(self):
        """Iniciar programador de reinicios"""
        if self.restart_scheduler_enabled:
            return
            
        self.restart_scheduler_enabled = True
        self.stop_restart_scheduler.clear()
        
        self.restart_scheduler_thread = threading.Thread(
            target=self._restart_scheduler_worker,
            daemon=True
        )
        self.restart_scheduler_thread.start()
        
        self.after(0, lambda: self._safe_update_restart_status("🔄 Reinicios activos"))
        self.logger.info("Programador de reinicios iniciado")

    def stop_restart_scheduler_func(self):
        """Detener programador de reinicios"""
        self.restart_scheduler_enabled = False
        self.stop_restart_scheduler.set()
        
        if self.restart_scheduler_thread and self.restart_scheduler_thread.is_alive():
            self.restart_scheduler_thread.join(timeout=1)
        
        schedule.clear('restart')
        self.after(0, lambda: self._safe_update_restart_status("⏹️ Inactivo"))
        self.after(0, lambda: self._safe_update_next_restart("Próximo reinicio: Deshabilitado"))
        self.logger.info("Programador de reinicios detenido")

    def _restart_scheduler_worker(self):
        """Worker del programador de reinicios"""
        try:
            # Configurar trabajos de reinicio
            self._setup_restart_jobs()
            
            while self.restart_scheduler_enabled:
                schedule.run_pending()
                self._update_next_restart_display()
                time.sleep(30)  # Verificar cada 30 segundos
                
        except Exception as e:
            self.logger.error(f"Error en programador de reinicios: {e}")
            self.after(0, lambda: self._safe_update_restart_status("❌ Error en programador"))

    def _setup_restart_jobs(self):
        """Configurar trabajos de reinicio"""
        schedule.clear('restart')
        
        # Obtener días y horas seleccionados
        selected_days = [day for day, var in self.day_vars.items() if var.get()]
        hours_text = self.restart_hours_text.get("0.0", "end-1c").strip()
        
        if not selected_days or not hours_text:
            return
        
        try:
            hours = [h.strip() for h in hours_text.split(',') if h.strip()]
            
            for day in selected_days:
                for hour in hours:
                    # Convertir día al formato de schedule
                    day_map = {
                        "Lunes": "monday", "Martes": "tuesday", "Miércoles": "wednesday",
                        "Jueves": "thursday", "Viernes": "friday", "Sábado": "saturday",
                        "Domingo": "sunday"
                    }
                    
                    if day in day_map:
                        schedule.every().week.at(hour).do(
                            self._scheduled_restart
                        ).tag('restart')
            
            self.logger.info(f"Programados reinicios para {selected_days} a las {hours}")
            
        except Exception as e:
            self.logger.error(f"Error configurando trabajos de reinicio: {e}")

    def _scheduled_restart(self):
        """Ejecutar reinicio programado"""
        self.logger.info("Ejecutando reinicio programado")
        self.show_message("🔄 Ejecutando reinicio programado")
        
        # Registrar inicio del reinicio automático
        if hasattr(self.main_window, 'log_server_event'):
            self.main_window.log_server_event("custom_event", 
                event_name="Reinicio automático iniciado", 
                details=f"Reinicio programado según configuración")
        
        # Determinar si se debe actualizar
        should_update = self._should_update_today()
        
        restart_info = {
            "type": "programado",
            "datetime": datetime.now().isoformat(),
            "server": self.current_server_name or "Desconocido",
            "backup_done": False,
            "saveworld_done": False,
            "update_done": False,
            "success": False,
            "reason": "Reinicio programado",
            "warnings_sent": False,
            "update_requested": should_update
        }
        
        # Registrar con el sistema de eventos del servidor
        if hasattr(self.main_window, 'log_server_event'):
            self.main_window.log_server_event("automatic_restart_start", restart_info=restart_info)
        
        # Enviar avisos RCON antes del reinicio
        if self.rcon_warnings_var.get():
            self.after(0, lambda: self._send_rcon_warnings_and_restart(restart_info))
        else:
            self.after(0, lambda: self._execute_restart_sequence(restart_info))



    def _should_update_today(self):
        """Determinar si se debe actualizar el servidor hoy"""
        try:
            # Si está configurado para actualizar siempre
            if hasattr(self, 'update_always_var') and self.update_always_var.get():
                return True
            
            # Si está configurado para días específicos
            if hasattr(self, 'update_specific_days_var') and self.update_specific_days_var.get():
                # Obtener el día actual
                today = datetime.now().strftime('%A')  # Lunes, Martes, etc. en inglés
                
                # Mapear día en inglés a español
                day_map = {
                    'Monday': 'Lunes',
                    'Tuesday': 'Martes', 
                    'Wednesday': 'Miércoles',
                    'Thursday': 'Jueves',
                    'Friday': 'Viernes',
                    'Saturday': 'Sábado',
                    'Sunday': 'Domingo'
                }
                
                today_spanish = day_map.get(today, today)
                
                # Verificar si hoy está seleccionado para actualizaciones
                if today_spanish in self.update_day_vars:
                    return self.update_day_vars[today_spanish].get()
            
            # Por defecto, no actualizar
            return False
            
        except Exception as e:
            self.logger.error(f"Error determinando si actualizar hoy: {e}")
            return False

    def _send_rcon_warnings_and_restart(self, restart_info):
        """Enviar avisos RCON y luego ejecutar reinicio"""
        try:
            # Obtener intervalos de aviso
            intervals_text = self.warning_intervals_entry.get().strip()
            if not intervals_text:
                # Si no hay intervalos, ejecutar reinicio directamente
                self._execute_restart_sequence(restart_info)
                return
            
            # Parsear intervalos
            intervals = []
            for interval_str in intervals_text.split(','):
                try:
                    interval = int(interval_str.strip())
                    if interval > 0:
                        intervals.append(interval)
                except ValueError:
                    continue
            
            if not intervals:
                # Si no hay intervalos válidos, ejecutar reinicio directamente
                self._execute_restart_sequence(restart_info)
                return
            
            # Ordenar intervalos de mayor a menor
            intervals.sort(reverse=True)
            
            # Obtener mensaje personalizado
            message_template = self.warning_message_text.get("0.0", "end-1c").strip()
            if not message_template:
                message_template = "⚠️ ATENCIÓN: El servidor se reiniciará en {time} minuto(s). Por favor, encuentra un lugar seguro."
            
            self.logger.info(f"Enviando avisos RCON: {intervals} minutos antes del reinicio")
            self.show_message(f"📢 Enviando avisos RCON: {intervals} minutos antes del reinicio")
            
            # Programar avisos
            self._schedule_warnings(intervals, message_template, restart_info)
            
        except Exception as e:
            self.logger.error(f"Error al configurar avisos RCON: {e}")
            # En caso de error, ejecutar reinicio sin avisos
            self._execute_restart_sequence(restart_info)

    def _schedule_warnings(self, intervals, message_template, restart_info):
        """Programar avisos RCON"""
        if not intervals:
            # No hay más avisos, ejecutar reinicio
            restart_info["warnings_sent"] = True
            self._execute_restart_sequence(restart_info)
            return
        
        # Tomar el primer intervalo
        next_interval = intervals[0]
        remaining_intervals = intervals[1:]
        
        # Crear mensaje con tiempo específico
        message = message_template.replace("{time}", str(next_interval))
        
        # Enviar aviso inmediatamente
        self._send_rcon_message(message)
        
        # Programar siguiente aviso o reinicio
        if remaining_intervals:
            # Calcular tiempo hasta el siguiente aviso
            delay_minutes = next_interval - remaining_intervals[0]
            delay_seconds = delay_minutes * 60 * 1000  # Convertir a milisegundos
            
            self.logger.info(f"Próximo aviso en {delay_minutes} minutos")
            self.after(delay_seconds, lambda: self._schedule_warnings(remaining_intervals, message_template, restart_info))
        else:
            # Este es el último aviso, programar reinicio
            delay_seconds = next_interval * 60 * 1000  # Convertir a milisegundos
            
            self.logger.info(f"Reinicio programado en {next_interval} minutos")
            self.after(delay_seconds, lambda: self._execute_restart_sequence_after_warnings(restart_info))

    def _execute_restart_sequence_after_warnings(self, restart_info):
        """Ejecutar reinicio después de los avisos"""
        restart_info["warnings_sent"] = True
        self.logger.info("Todos los avisos RCON enviados, iniciando secuencia de reinicio")
        self.show_message("📢 Avisos RCON completados, iniciando reinicio")
        self._execute_restart_sequence(restart_info)

    def _send_rcon_message(self, message):
        """Enviar mensaje via RCON"""
        try:
            if hasattr(self.main_window, 'rcon_panel'):
                rcon_command = f'broadcast "{message}"'
                success = self.main_window.rcon_panel.execute_rcon_command(rcon_command)
                if success:
                    self.logger.info(f"Aviso RCON enviado: {message}")
                    self.show_message(f"📢 Aviso enviado: {message}")
                else:
                    self.logger.warning(f"No se pudo enviar aviso RCON: {message}")
                    self.show_message(f"⚠️ Error al enviar aviso: {message}")
            else:
                self.logger.warning("Panel RCON no disponible para enviar avisos")
        except Exception as e:
            self.logger.error(f"Error enviando mensaje RCON: {e}")
            self.show_message(f"❌ Error en aviso RCON: {e}")

    def start_manual_restart(self):
        """Iniciar reinicio manual"""
        # Preguntar si se quiere actualizar
        should_update = self.show_ctk_confirm(
            "Reinicio Manual",
            "¿Deseas actualizar el servidor antes del reinicio?"
        )
        
        # Preguntar si se quieren enviar avisos RCON
        should_send_warnings = False
        if self.rcon_warnings_var.get():
            should_send_warnings = self.show_ctk_confirm(
                "Avisos RCON",
                "¿Deseas enviar avisos RCON antes del reinicio manual?"
            )
        
        restart_info = {
            "type": "manual",
            "datetime": datetime.now().isoformat(),
            "server": self.current_server_name or "Desconocido",
            "backup_done": False,
            "saveworld_done": False,
            "update_done": False,
            "success": False,
            "reason": "Reinicio manual",
            "update_requested": should_update,
            "warnings_sent": False
        }
        
        # Enviar avisos RCON si se solicitó
        if should_send_warnings:
            self._send_rcon_warnings_and_restart(restart_info)
        else:
            self._execute_restart_sequence(restart_info)

    def _execute_restart_sequence(self, restart_info):
        """Ejecutar secuencia completa de reinicio"""
        try:
            self.restart_progress_bar.set(0.1)
            self.restart_progress_label.configure(text="Iniciando secuencia de reinicio...")
            
            # 1. Backup si está habilitado
            if self.backup_before_restart_var.get():
                self.restart_progress_label.configure(text="Realizando backup...")
                self.restart_progress_bar.set(0.2)
                if self._execute_backup():
                    restart_info["backup_done"] = True
                    self.logger.info("Backup completado antes del reinicio")
            
            # 2. Saveworld si está habilitado
            if self.saveworld_before_restart_var.get():
                self.restart_progress_label.configure(text="Guardando mundo (saveworld)...")
                self.restart_progress_bar.set(0.4)
                if self._execute_saveworld():
                    restart_info["saveworld_done"] = True
                    self.logger.info("Saveworld completado antes del reinicio")
            
            # 3. Detener servidor
            self.restart_progress_label.configure(text="Deteniendo servidor...")
            self.restart_progress_bar.set(0.6)
            if self._stop_server():
                self.logger.info("Servidor detenido para reinicio")
            
            # 4. Actualizar si se solicitó
            if restart_info.get("update_requested", False):
                self.restart_progress_label.configure(text="Actualizando servidor...")
                self.restart_progress_bar.set(0.7)
                if self._execute_update():
                    restart_info["update_done"] = True
                    self.logger.info("Actualización completada")
            
            # 5. Iniciar servidor
            self.restart_progress_label.configure(text="Iniciando servidor...")
            self.restart_progress_bar.set(0.9)
            if self._start_server():
                restart_info["success"] = True
                self.restart_progress_label.configure(text="✅ Reinicio completado exitosamente")
                self.restart_progress_bar.set(1.0)
                self.logger.info("Reinicio completado exitosamente")
                self.show_message("✅ Reinicio completado exitosamente")
            else:
                restart_info["success"] = False
                self.restart_progress_label.configure(text="❌ Error al iniciar servidor")
                self.logger.error("Error al iniciar servidor después del reinicio")
                self.show_message("❌ Error al iniciar servidor después del reinicio")
            
            # Registrar finalización del reinicio automático
            if hasattr(self.main_window, 'log_server_event'):
                self.main_window.log_server_event("automatic_restart_complete", restart_info=restart_info)
            
            # Guardar en historial
            self._save_restart_to_history(restart_info)
            
            # Resetear barra de progreso después de 5 segundos
            self.after(5000, lambda: self.restart_progress_bar.set(0))
            self.after(5000, lambda: self.restart_progress_label.configure(text="Listo para reinicio"))
            
        except Exception as e:
            self.logger.error(f"Error en secuencia de reinicio: {e}")
            self.restart_progress_label.configure(text="❌ Error en reinicio")
            self.show_message(f"❌ Error en reinicio: {e}")

    def _execute_update_sequence(self):
        """Ejecutar secuencia de actualización"""
        try:
            self.logger.info("Iniciando secuencia de actualización")
            
            # Detener servidor
            if self._stop_server():
                self.logger.info("Servidor detenido para actualización")
            
            # Actualizar
            if self._execute_update():
                self.logger.info("Actualización completada")
            
            # Iniciar servidor
            if self._start_server():
                self.logger.info("Servidor iniciado después de actualización")
                self.show_message("✅ Actualización completada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error en secuencia de actualización: {e}")
            self.show_message(f"❌ Error en actualización: {e}")

    def _execute_backup(self):
        """Ejecutar backup"""
        try:
            if hasattr(self.main_window, 'backup_panel') and hasattr(self.main_window.backup_panel, 'advanced_backup_panel'):
                backup_panel = self.main_window.backup_panel.advanced_backup_panel
                backup_panel.start_backup(is_manual=False)
                return True
        except Exception as e:
            self.logger.error(f"Error ejecutando backup: {e}")
        return False

    def _execute_saveworld(self):
        """Ejecutar saveworld via RCON"""
        try:
            if hasattr(self.main_window, 'rcon_panel'):
                rcon_panel = self.main_window.rcon_panel
                return rcon_panel.execute_rcon_command("saveworld")
        except Exception as e:
            self.logger.error(f"Error ejecutando saveworld: {e}")
        return False

    def _stop_server(self):
        """Detener servidor"""
        try:
            if hasattr(self.main_window, 'server_panel'):
                self.main_window.server_panel.stop_server()
                time.sleep(5)  # Esperar a que se detenga
                return True
        except Exception as e:
            self.logger.error(f"Error deteniendo servidor: {e}")
        return False

    def _start_server(self):
        """Iniciar servidor"""
        try:
            if hasattr(self.main_window, 'server_panel'):
                self.main_window.server_panel.start_server()
                return True
        except Exception as e:
            self.logger.error(f"Error iniciando servidor: {e}")
        return False

    def _execute_update(self):
        """Ejecutar actualización del servidor"""
        try:
            if hasattr(self.main_window, 'server_panel'):
                self.main_window.server_panel.update_server()
                return True
        except Exception as e:
            self.logger.error(f"Error actualizando servidor: {e}")
        return False

    def _save_restart_to_history(self, restart_info):
        """Guardar reinicio en historial"""
        try:
            server_name = restart_info.get("server", "Desconocido")
            
            if server_name not in self.restart_history:
                self.restart_history[server_name] = []
            
            self.restart_history[server_name].append(restart_info)
            
            # Mantener solo los últimos 50 reinicios por servidor
            if len(self.restart_history[server_name]) > 50:
                self.restart_history[server_name] = self.restart_history[server_name][-50:]
            
            self.save_restart_history()
            self.refresh_restart_history()
            
        except Exception as e:
            self.logger.error(f"Error guardando reinicio en historial: {e}")

    def _update_next_restart_display(self):
        """Actualizar display del próximo reinicio"""
        try:
            restart_jobs = [job for job in schedule.jobs if 'restart' in job.tags]
            if restart_jobs:
                next_job = min(restart_jobs, key=lambda x: x.next_run)
                next_time = next_job.next_run.strftime('%d/%m/%Y %H:%M:%S')
                self.after(0, lambda t=next_time: self._safe_update_next_restart(f"Próximo reinicio: {t}"))
            else:
                self.after(0, lambda: self._safe_update_next_restart("Próximo reinicio: No programado"))
        except Exception as e:
            self.logger.debug(f"Error actualizando próximo reinicio: {e}")

    def _safe_update_restart_status(self, text):
        """Actualizar estado de forma segura"""
        try:
            if hasattr(self, 'restart_status_label') and self.restart_status_label.winfo_exists():
                self.restart_status_label.configure(text=text)
        except Exception as e:
            self.logger.debug(f"Error actualizando status de reinicio: {e}")

    def _safe_update_next_restart(self, text):
        """Actualizar próximo reinicio de forma segura"""
        try:
            if hasattr(self, 'next_restart_info') and self.next_restart_info.winfo_exists():
                self.next_restart_info.configure(text=text)
        except Exception as e:
            self.logger.debug(f"Error actualizando próximo reinicio: {e}")

    def show_message(self, message):
        """Mostrar mensaje en el log de la aplicación"""
        try:
            if hasattr(self.main_window, 'add_log_message'):
                self.main_window.add_log_message(message)
        except Exception as e:
            self.logger.debug(f"Error mostrando mensaje: {e}")

    def show_ctk_confirm(self, title, message):
        """Mostrar diálogo de confirmación con CustomTkinter"""
        result = {"confirmed": False}
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("450x200")
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
        
        def on_no():
            result["confirmed"] = False
            dialog.destroy()
        
        yes_button = ctk.CTkButton(button_frame, text="Sí", command=on_yes, width=80)
        yes_button.pack(side="left", padx=5)
        
        no_button = ctk.CTkButton(button_frame, text="No", command=on_no, width=80)
        no_button.pack(side="left", padx=5)
        
        dialog.focus_set()
        dialog.wait_window()  # Esperar a que se cierre
        
        return result["confirmed"]

    def refresh_restart_history(self):
        """Actualizar display del historial"""
        try:
            # Limpiar historial actual
            for widget in self.history_scroll.winfo_children():
                widget.destroy()
            
            server_name = self.current_server_name or "Desconocido"
            history = self.restart_history.get(server_name, [])
            
            if not history:
                no_history_label = ctk.CTkLabel(
                    self.history_scroll,
                    text="No hay reinicios registrados",
                    text_color="gray"
                )
                no_history_label.pack(pady=20)
                return
            
            # Mostrar historial más reciente primero
            for i, restart in enumerate(reversed(history[-20:])):  # Últimos 20
                self._create_history_item(restart, i)
                
        except Exception as e:
            self.logger.error(f"Error actualizando historial: {e}")

    def _create_history_item(self, restart_info, index):
        """Crear item del historial"""
        item_frame = ctk.CTkFrame(self.history_scroll)
        item_frame.pack(fill="x", padx=5, pady=2)
        item_frame.grid_columnconfigure(1, weight=1)
        
        # Fecha y tipo
        datetime_obj = datetime.fromisoformat(restart_info["datetime"])
        date_str = datetime_obj.strftime("%d/%m/%Y %H:%M:%S")
        
        type_emoji = "🔄" if restart_info["type"] == "programado" else "👤"
        status_emoji = "✅" if restart_info["success"] else "❌"
        
        title_text = f"{type_emoji} {restart_info['type'].title()} - {date_str} {status_emoji}"
        
        title_label = ctk.CTkLabel(
            item_frame,
            text=title_text,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(5, 0))
        
        # Detalles
        details = []
        if restart_info.get("backup_done"):
            details.append("✅ Backup")
        if restart_info.get("saveworld_done"):
            details.append("✅ Saveworld")
        if restart_info.get("update_done"):
            details.append("✅ Actualización")
        if restart_info.get("warnings_sent"):
            details.append("📢 Avisos RCON")
        
        if details:
            details_text = " | ".join(details)
            details_label = ctk.CTkLabel(
                item_frame,
                text=details_text,
                font=ctk.CTkFont(size=10),
                text_color="green"
            )
            details_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 5))

    def clear_restart_history(self):
        """Limpiar historial de reinicios"""
        if self.show_ctk_confirm("Limpiar Historial", "¿Estás seguro de que quieres limpiar todo el historial de reinicios?"):
            server_name = self.current_server_name or "Desconocido"
            if server_name in self.restart_history:
                self.restart_history[server_name] = []
                self.save_restart_history()
                self.refresh_restart_history()
                self.logger.info("Historial de reinicios limpiado")

    def save_restart_config(self):
        """Guardar configuración de reinicios"""
        try:
            server_name = self.current_server_name or "default"
            
            config = {
                "restart_enabled": self.restart_enabled_var.get(),
                "update_always": self.update_always_var.get(),
                "update_specific_days": self.update_specific_days_var.get(),
                "restart_days": {day: var.get() for day, var in self.day_vars.items()},
                "update_days": {day: var.get() for day, var in self.update_day_vars.items()},
                "restart_hours": self.restart_hours_text.get("0.0", "end-1c").strip(),
                "backup_before_restart": self.backup_before_restart_var.get(),
                "saveworld_before_restart": self.saveworld_before_restart_var.get(),
                "rcon_warnings_enabled": self.rcon_warnings_var.get(),
                "warning_intervals": self.warning_intervals_entry.get(),
                "warning_message": self.warning_message_text.get("0.0", "end-1c").strip()
            }
            
            self.restart_configs[server_name] = config
            
            # Crear directorio si no existe
            os.makedirs("data", exist_ok=True)
            
            with open(self.restart_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.restart_configs, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuración de reinicios guardada para {server_name}")
            
            # Reiniciar scheduler si está activo
            if self.restart_enabled_var.get():
                self.stop_restart_scheduler_func()
                self.start_restart_scheduler()
            
        except Exception as e:
            self.logger.error(f"Error guardando configuración de reinicios: {e}")

    def load_all_restart_configs(self):
        """Cargar todas las configuraciones de reinicios"""
        try:
            if os.path.exists(self.restart_config_file):
                with open(self.restart_config_file, 'r', encoding='utf-8') as f:
                    self.restart_configs = json.load(f)
        except Exception as e:
            self.logger.error(f"Error cargando configuraciones de reinicios: {e}")
            self.restart_configs = {}

    def save_restart_history(self):
        """Guardar historial de reinicios"""
        try:
            os.makedirs("data", exist_ok=True)
            with open(self.restart_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.restart_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error guardando historial de reinicios: {e}")

    def load_restart_history(self):
        """Cargar historial de reinicios"""
        try:
            if os.path.exists(self.restart_history_file):
                with open(self.restart_history_file, 'r', encoding='utf-8') as f:
                    self.restart_history = json.load(f)
        except Exception as e:
            self.logger.error(f"Error cargando historial de reinicios: {e}")
            self.restart_history = {}

    def update_server_selection(self, server_name):
        """Actualizar selección de servidor"""
        self.current_server_name = server_name
        
        if server_name and server_name in self.restart_configs:
            self.load_server_config(server_name)
        
        self.refresh_restart_history()

    def load_server_config(self, server_name):
        """Cargar configuración específica del servidor"""
        try:
            config = self.restart_configs.get(server_name, {})
            
            # Cargar configuración de reinicios
            self.restart_enabled_var.set(config.get("restart_enabled", False))
            
            # Cargar configuración de actualizaciones
            self.update_always_var.set(config.get("update_always", True))
            self.update_specific_days_var.set(config.get("update_specific_days", False))
            
            # Cargar días seleccionados
            restart_days = config.get("restart_days", {})
            for day, var in self.day_vars.items():
                var.set(restart_days.get(day, False))
            
            update_days = config.get("update_days", {})
            for day, var in self.update_day_vars.items():
                var.set(update_days.get(day, False))
            
            # Cargar horas de reinicios
            restart_hours = config.get("restart_hours", "00:00, 06:00, 12:00, 18:00")
            self.restart_hours_text.delete("0.0", "end")
            self.restart_hours_text.insert("0.0", restart_hours)
            
            # Cargar opciones
            self.backup_before_restart_var.set(config.get("backup_before_restart", True))
            self.saveworld_before_restart_var.set(config.get("saveworld_before_restart", True))
            
            # Cargar opciones de avisos RCON
            self.rcon_warnings_var.set(config.get("rcon_warnings_enabled", True))
            
            warning_intervals = config.get("warning_intervals", "15, 10, 5, 2, 1")
            self.warning_intervals_entry.delete(0, "end")
            self.warning_intervals_entry.insert(0, warning_intervals)
            
            warning_message = config.get("warning_message", "⚠️ ATENCIÓN: El servidor se reiniciará en {time} minuto(s). Por favor, encuentra un lugar seguro.")
            self.warning_message_text.delete("0.0", "end")
            self.warning_message_text.insert("0.0", warning_message)
            
            # Aplicar estado de los checkboxes
            self.on_update_mode_change()
            
            self.logger.info(f"Configuración cargada para servidor: {server_name}")
            
        except Exception as e:
            self.logger.error(f"Error cargando configuración del servidor {server_name}: {e}")
