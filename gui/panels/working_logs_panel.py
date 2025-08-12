import customtkinter as ctk
import os
from datetime import datetime

class WorkingLogsPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger, main_window=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        
        # Asegurar que este frame se expanda
        self.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configurar grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.create_interface()
        self.load_initial_content()
        
    def create_interface(self):
        """Crear la interfaz básica"""
        # Título
        title = ctk.CTkLabel(
            self, 
            text="📋 Logs del Sistema ARK", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.grid(row=0, column=0, pady=10, sticky="w")
        
        # Frame de botones
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        # Botones
        ctk.CTkButton(
            button_frame,
            text="🎮 Eventos Servidor",
            command=self.show_server_events,
            width=130
        ).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(
            button_frame,
            text="📋 Log App",
            command=self.show_app_log,
            width=100
        ).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(
            button_frame,
            text="🔄 Actualizar",
            command=self.refresh_current,
            width=100,
            fg_color="orange"
        ).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(
            button_frame,
            text="🗑️ Limpiar",
            command=self.clear_logs,
            width=100,
            fg_color="red"
        ).pack(side="left", padx=5, pady=5)
        
        # Área principal de texto
        self.text_area = ctk.CTkTextbox(
            self,
            height=300,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.text_area.grid(row=2, column=0, sticky="nsew", pady=5)
        
        # Variable para tracking
        self.current_mode = "welcome"
        
    def load_initial_content(self):
        """Cargar contenido inicial"""
        content = f"""📋 LOGS DEL SISTEMA ARK - {datetime.now().strftime('%H:%M:%S')}
{'='*60}

✅ Panel de logs inicializado correctamente
✅ Sistema funcionando

🔍 OPCIONES DISPONIBLES:
• 🎮 Eventos Servidor - Ver actividad del servidor ARK
• 📋 Log App - Ver registro de la aplicación 
• 🔄 Actualizar - Refrescar la vista actual
• 🗑️ Limpiar - Limpiar la pantalla

💡 Los mensajes de error y eventos aparecen automáticamente aquí
💡 Haz clic en los botones para ver información específica

🚀 ¡Sistema listo para usar!
"""
        
        try:
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", content)
            if self.logger:
                # self.logger.info("Panel de logs cargado con éxito")  # Optimizado: reducir ruido
                pass
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error cargando contenido inicial: {e}")
    
    def show_server_events(self):
        """Mostrar eventos del servidor"""
        try:
            self.text_area.delete("1.0", "end")
            
            content = f"""🎮 EVENTOS DEL SERVIDOR ARK - {datetime.now().strftime('%H:%M:%S')}
{'='*60}

"""
            
            # Buscar archivo de eventos de hoy
            today = datetime.now().strftime('%Y-%m-%d')
            events_file = f"logs/server_events/server_events_{today}.log"
            
            if os.path.exists(events_file):
                try:
                    with open(events_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    if lines:
                        content += f"📂 Archivo: {events_file}\n"
                        content += f"📊 Total de eventos: {len(lines)}\n\n"
                        
                        # Mostrar últimos 20 eventos
                        recent = lines[-20:] if len(lines) > 20 else lines
                        content += "🔄 EVENTOS RECIENTES:\n\n"
                        content += "".join(recent)
                    else:
                        content += "📝 El archivo existe pero está vacío"
                        
                except Exception as e:
                    content += f"❌ Error leyendo archivo: {e}"
            else:
                content += f"📂 Buscando: {events_file}\n"
                content += "❌ No se encontró archivo de eventos para hoy\n\n"
                content += "💡 Los eventos aparecerán cuando:\n"
                content += "  • Inicies/detengas el servidor\n"
                content += "  • Realices backups\n"
                content += "  • Ejecutes comandos RCON\n"
                content += "  • Ocurran reinicios automáticos\n"
            
            self.text_area.insert("1.0", content)
            self.current_mode = "server_events"
            
        except Exception as e:
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", f"❌ Error mostrando eventos: {e}")
    
    def show_app_log(self):
        """Mostrar log de la aplicación"""
        try:
            self.text_area.delete("1.0", "end")
            
            content = f"""📋 LOG DE LA APLICACIÓN - {datetime.now().strftime('%H:%M:%S')}
{'='*60}

"""
            
            log_file = "logs/app.log"
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    if lines:
                        content += f"📂 Archivo: {log_file}\n"
                        content += f"📊 Total de líneas: {len(lines)}\n\n"
                        
                        # Mostrar últimas 30 líneas
                        recent = lines[-30:] if len(lines) > 30 else lines
                        content += "🔄 ENTRADAS RECIENTES:\n\n"
                        content += "".join(recent)
                    else:
                        content += "📝 El archivo existe pero está vacío"
                        
                except Exception as e:
                    content += f"❌ Error leyendo archivo: {e}"
            else:
                content += f"❌ No se encontró: {log_file}\n"
                content += "💡 El archivo se creará automáticamente cuando la app registre eventos"
            
            self.text_area.insert("1.0", content)
            self.current_mode = "app_log"
            
        except Exception as e:
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", f"❌ Error mostrando log: {e}")
    
    def refresh_current(self):
        """Actualizar la vista actual"""
        if self.current_mode == "server_events":
            self.show_server_events()
        elif self.current_mode == "app_log":
            self.show_app_log()
        else:
            self.load_initial_content()
    
    def clear_logs(self):
        """Limpiar pantalla"""
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", f"🗑️ Pantalla limpiada - {datetime.now().strftime('%H:%M:%S')}\n\nHaz clic en un botón para mostrar contenido.")
        self.current_mode = "cleared"
    
    def add_message(self, message, msg_type="info"):
        """Agregar mensaje desde otros componentes"""
        try:
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            
            icons = {
                "error": "❌",
                "success": "✅", 
                "warning": "⚠️",
                "info": "ℹ️"
            }
            
            icon = icons.get(msg_type, "📝")
            full_msg = f"{timestamp} {icon} {message}\n"
            
            # Si no hay contenido o es el welcome, limpiar primero
            current = self.text_area.get("1.0", "end").strip()
            if not current or "Sistema listo para usar!" in current:
                header = f"🔄 MENSAJES EN TIEMPO REAL - {datetime.now().strftime('%H:%M:%S')}\n{'='*50}\n\n"
                self.text_area.delete("1.0", "end")
                self.text_area.insert("1.0", header + full_msg)
            else:
                self.text_area.insert("end", full_msg)
            
            # Scroll al final
            self.text_area.see("end")
            self.current_mode = "realtime"
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error agregando mensaje: {e}")
