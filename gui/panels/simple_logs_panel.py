import customtkinter as ctk
import os
from datetime import datetime

class SimpleLogsPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger, main_window=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        
        self.create_widgets()
        
        # Mostrar contenido por defecto después de crear widgets
        self.after(100, self.show_default_content)
        
    def create_widgets(self):
        """Crear widgets simples y funcionales"""
        # Configurar grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # El textbox debe expandirse
        
        # Título
        title_label = ctk.CTkLabel(
            self, 
            text="📋 Logs del Servidor ARK", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(10, 5), sticky="w", padx=20)
        
        # Frame para botones
        buttons_frame = ctk.CTkFrame(self)
        buttons_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        # Botones simples
        ctk.CTkButton(
            buttons_frame,
            text="🎮 Eventos Servidor",
            command=self.show_server_events,
            width=140,
            height=35
        ).pack(side="left", padx=5, pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text="📋 Log Aplicación",
            command=self.show_app_log,
            width=140,
            height=35
        ).pack(side="left", padx=5, pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text="🔄 Actualizar",
            command=self.refresh_current,
            width=100,
            height=35,
            fg_color="orange",
            hover_color="darkorange"
        ).pack(side="left", padx=5, pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text="🗑️ Limpiar",
            command=self.clear_display,
            width=100,
            height=35,
            fg_color="red",
            hover_color="darkred"
        ).pack(side="left", padx=5, pady=10)
        
        # Área de texto principal
        self.log_display = ctk.CTkTextbox(self, wrap="none", font=ctk.CTkFont(family="Consolas", size=11))
        self.log_display.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Variable para el contenido actual
        self.current_view = "default"
    
    def show_default_content(self):
        """Mostrar contenido por defecto"""
        content = """🎮 PANEL DE LOGS - ARK SERVER MANAGER
==============================================

📋 ESTADO ACTUAL:
✅ Sistema de logging operativo
✅ Panel de logs cargado correctamente
✅ Conexión con aplicación establecida

🔍 TIPOS DE LOGS DISPONIBLES:

🎮 EVENTOS SERVIDOR:
   • Inicio y parada del servidor
   • Actualizaciones de servidor
   • Reinicios automáticos y manuales
   • Comandos RCON ejecutados
   • Operaciones de backup
   • Gestión de mods

📋 LOG APLICACIÓN:
   • Mensajes del sistema
   • Errores y warnings
   • Estado de conexiones
   • Información de configuración

📂 UBICACIÓN DE ARCHIVOS:
   • Eventos servidor: logs/server_events/server_events_YYYY-MM-DD.log
   • Log aplicación: logs/app.log

🚀 INSTRUCCIONES:
1. Haz clic en "🎮 Eventos Servidor" para ver eventos específicos del servidor
2. Haz clic en "📋 Log Aplicación" para ver el log general de la app
3. Usa "🔄 Actualizar" para refrescar el contenido
4. Usa "🗑️ Limpiar" para limpiar la pantalla

💡 TIP: Los eventos se registran automáticamente cuando realizas acciones en la aplicación.
"""
        self.log_display.delete("1.0", "end")
        self.log_display.insert("1.0", content)
        self.current_view = "default"
    
    def show_server_events(self):
        """Mostrar eventos del servidor"""
        try:
            self.log_display.delete("1.0", "end")
            
            if self.main_window and hasattr(self.main_window, 'get_server_events'):
                events = self.main_window.get_server_events(24)
                
                if events:
                    header = "🎮 EVENTOS DEL SERVIDOR - ÚLTIMAS 24 HORAS\n"
                    header += "=" * 60 + "\n\n"
                    
                    # Mostrar eventos más recientes primero
                    recent_events = events[-50:] if len(events) > 50 else events
                    recent_events.reverse()
                    
                    content = header + '\n'.join(recent_events)
                    self.log_display.insert("1.0", content)
                else:
                    self.log_display.insert("1.0", """🎮 EVENTOS DEL SERVIDOR
==============================

📋 No hay eventos registrados todavía.

Los eventos aparecerán aquí cuando:
• 🚀 Inicies el servidor
• ⏹️ Detengas el servidor  
• 🔄 Reinicies el servidor
• 📥 Actualices el servidor
• 🎮 Ejecutes comandos RCON
• 💾 Realices backups
• 🕐 Ocurran reinicios automáticos

💡 Realiza alguna acción en el servidor y luego actualiza esta vista.
""")
            else:
                self.log_display.insert("1.0", "❌ No se puede acceder al sistema de eventos del servidor")
            
            self.current_view = "server_events"
            
        except Exception as e:
            self.log_display.delete("1.0", "end")
            self.log_display.insert("1.0", f"❌ Error al cargar eventos del servidor:\n{e}")
    
    def show_app_log(self):
        """Mostrar log de la aplicación"""
        try:
            self.log_display.delete("1.0", "end")
            
            app_log_path = "logs/app.log"
            if os.path.exists(app_log_path):
                with open(app_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Mostrar las últimas 100 líneas
                recent_lines = lines[-100:] if len(lines) > 100 else lines
                
                header = "📋 LOG DE LA APLICACIÓN - ÚLTIMAS 100 LÍNEAS\n"
                header += "=" * 60 + "\n\n"
                
                content = header + ''.join(recent_lines)
                self.log_display.insert("1.0", content)
                
                # Scrollear al final para ver lo más reciente
                self.log_display.see("end")
            else:
                self.log_display.insert("1.0", "❌ No se encontró el archivo de log: logs/app.log")
            
            self.current_view = "app_log"
            
        except Exception as e:
            self.log_display.delete("1.0", "end")
            self.log_display.insert("1.0", f"❌ Error al cargar log de la aplicación:\n{e}")
    
    def refresh_current(self):
        """Actualizar la vista actual"""
        if self.current_view == "server_events":
            self.show_server_events()
        elif self.current_view == "app_log":
            self.show_app_log()
        else:
            self.show_default_content()
    
    def clear_display(self):
        """Limpiar la pantalla"""
        self.log_display.delete("1.0", "end")
        self.log_display.insert("1.0", "🗑️ Pantalla limpiada.\n\nHaz clic en un botón para mostrar contenido.")
        self.current_view = "cleared"
