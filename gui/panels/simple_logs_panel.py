import customtkinter as ctk
import os
from datetime import datetime

class SimpleLogsPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger, main_window=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        
        # Configurar el frame principal para expandirse
        self.pack(fill="both", expand=True)
        
        self.create_widgets()
        
        # Mostrar contenido por defecto inmediatamente y después con delay
        try:
            # Intentar inmediatamente
            self.show_default_content()
            # Reintentar después de que se construya la GUI
            self.after(100, self.show_default_content)
            self.after(1000, self.show_default_content)  # Otro intento por si falla
            
            # Agregar mensaje de prueba inmediato
            if self.logger:
                self.logger.info("SimpleLogsPanel inicializado correctamente")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al mostrar contenido por defecto: {e}")
            # Intentar agregar mensaje mínimo
            try:
                if hasattr(self, 'log_display'):
                    self.add_message("Panel de logs inicializado", "info")
            except:
                pass
        
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
        try:
            content = """🎮 PANEL DE LOGS - ARK SERVER MANAGER
==============================================

✅ Panel de logs cargado correctamente
✅ Sistema operativo

📋 ESTADO: Sistema funcionando normalmente

🔍 OPCIONES DISPONIBLES:
• 🎮 Eventos Servidor - Ver actividad del servidor
• 📋 Log Aplicación - Ver registro general
• 🔄 Actualizar - Refrescar contenido
• 🗑️ Limpiar - Limpiar pantalla

💡 Haz clic en los botones superiores para ver información específica.
💡 Los errores y mensajes aparecerán aquí automáticamente.
"""
            
            if hasattr(self, 'log_display') and self.log_display:
                self.log_display.delete("1.0", "end")
                self.log_display.insert("1.0", content)
                self.current_view = "default"
                if self.logger:
                    self.logger.info("Contenido por defecto mostrado en panel de logs")
            else:
                if self.logger:
                    self.logger.error("log_display no está disponible")
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error en show_default_content: {e}")
            # Intentar crear contenido mínimo
            try:
                if hasattr(self, 'log_display') and self.log_display:
                    self.log_display.insert("1.0", "📋 Panel de logs cargado\n✅ Sistema funcionando")
            except:
                pass
    
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
    
    def add_message(self, message, message_type="info"):
        """Agregar un mensaje al panel de logs desde otros componentes"""
        try:
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            
            # Determinar el icono según el tipo de mensaje
            if message_type == "error":
                icon = "❌"
            elif message_type == "success":
                icon = "✅"
            elif message_type == "warning":
                icon = "⚠️"
            elif message_type == "info":
                icon = "ℹ️"
            else:
                icon = "📝"
            
            # Crear el mensaje completo
            full_message = f"{timestamp} {icon} {message}\n"
            
            # Insertar el mensaje
            current_content = self.log_display.get("1.0", "end")
            if current_content.strip():
                self.log_display.insert("end", full_message)
            else:
                # Si está vacío, empezar con header
                header = "🔄 MENSAJES EN TIEMPO REAL\n" + "=" * 50 + "\n\n"
                self.log_display.insert("1.0", header + full_message)
            
            # Hacer scroll al final
            self.log_display.see("end")
            
            self.current_view = "realtime"
            
        except Exception as e:
            # Fallback silencioso para evitar errores en cascada
            pass