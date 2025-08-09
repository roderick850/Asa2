import customtkinter as ctk
import os
import subprocess
import platform

class LogsPanelNew(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger, main_window=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        
        # Configurar grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # El área de texto debe expandirse
        
        # Configurar pack para que llene el área disponible
        self.pack(fill="both", expand=True)
        
        # Título grande
        title = ctk.CTkLabel(
            self, 
            text="📋 PANEL DE LOGS - ARK SERVER MANAGER", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.grid(row=0, column=0, pady=(10, 5), sticky="ew")
        
        # Frame para botones de control
        buttons_frame = ctk.CTkFrame(self)
        buttons_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        # Botones de control
        ctk.CTkButton(
            buttons_frame,
            text="🔄 Actualizar Logs",
            command=self.load_content,
            width=120,
            height=35,
            fg_color="green",
            hover_color="darkgreen"
        ).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="📂 Abrir Carpeta Logs",
            command=self.open_logs_folder,
            width=140,
            height=35,
            fg_color="blue",
            hover_color="darkblue"
        ).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="🎮 Eventos Servidor",
            command=self.open_server_events_folder,
            width=140,
            height=35,
            fg_color="orange",
            hover_color="darkorange"
        ).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="🗑️ Limpiar Vista",
            command=self.clear_content,
            width=110,
            height=35,
            fg_color="red",
            hover_color="darkred"
        ).pack(side="left", padx=5, pady=5)
        
        # Área de texto principal
        self.text_area = ctk.CTkTextbox(
            self, 
            height=400,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.text_area.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Mostrar contenido inmediatamente
        self.load_content()
    
    def load_content(self):
        """Cargar contenido inmediato en el panel"""
        content = """🎮 PANEL DE LOGS - ARK SERVER MANAGER
════════════════════════════════════════════════

✅ ESTADO: Panel de logs funcionando correctamente
📅 FECHA: """ + str(os.popen('date /t').read().strip()) + """
🕐 HORA: """ + str(os.popen('time /t').read().strip()) + """

📋 LOG DE LA APLICACIÓN:
═════════════════════════════

"""
        
        # Agregar contenido del log de la aplicación
        try:
            if os.path.exists("logs/app.log"):
                with open("logs/app.log", 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                # Mostrar las últimas 20 líneas
                recent_lines = lines[-20:] if len(lines) > 20 else lines
                content += "\n".join(recent_lines)
            else:
                content += "❌ No se encontró logs/app.log"
        except Exception as e:
            content += f"❌ Error al leer logs: {e}"
        
        # Agregar eventos del servidor si existen
        content += "\n\n🎮 EVENTOS DEL SERVIDOR:\n═══════════════════════════\n\n"
        
        try:
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            events_file = f"logs/server_events/server_events_{today}.log"
            
            if os.path.exists(events_file):
                with open(events_file, 'r', encoding='utf-8', errors='ignore') as f:
                    events = f.readlines()
                    
                recent_events = events[-10:] if len(events) > 10 else events
                content += "\n".join(recent_events)
            else:
                content += f"❌ No se encontró {events_file}"
        except Exception as e:
            content += f"❌ Error al leer eventos: {e}"
        
        # Insertar contenido en el área de texto
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", content)
    
    def open_logs_folder(self):
        """Abrir la carpeta principal de logs"""
        try:
            logs_path = os.path.abspath("logs")
            
            # Crear la carpeta si no existe
            if not os.path.exists(logs_path):
                os.makedirs(logs_path)
            
            # Abrir según el sistema operativo
            if platform.system() == "Windows":
                os.startfile(logs_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", logs_path])
            else:  # Linux
                subprocess.run(["xdg-open", logs_path])
                
            # Registrar en log
            if self.logger:
                self.logger.info(f"Carpeta de logs abierta: {logs_path}")
                
        except Exception as e:
            error_msg = f"Error al abrir carpeta de logs: {e}"
            if self.logger:
                self.logger.error(error_msg)
            
            # Mostrar error en el área de texto
            self.text_area.insert("end", f"\n\n❌ {error_msg}")
    
    def open_server_events_folder(self):
        """Abrir la carpeta de eventos del servidor"""
        try:
            events_path = os.path.abspath("logs/server_events")
            
            # Crear la carpeta si no existe
            if not os.path.exists(events_path):
                os.makedirs(events_path)
            
            # Abrir según el sistema operativo
            if platform.system() == "Windows":
                os.startfile(events_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", events_path])
            else:  # Linux
                subprocess.run(["xdg-open", events_path])
                
            # Registrar en log
            if self.logger:
                self.logger.info(f"Carpeta de eventos del servidor abierta: {events_path}")
                
        except Exception as e:
            error_msg = f"Error al abrir carpeta de eventos: {e}"
            if self.logger:
                self.logger.error(error_msg)
            
            # Mostrar error en el área de texto
            self.text_area.insert("end", f"\n\n❌ {error_msg}")
    
    def clear_content(self):
        """Limpiar el contenido del área de texto"""
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", """🗑️ VISTA LIMPIADA
═══════════════════

✅ Contenido anterior eliminado.
💡 Haz clic en "🔄 Actualizar Logs" para mostrar contenido nuevamente.
📂 Usa "📂 Abrir Carpeta Logs" para acceder a los archivos directamente.
🎮 Usa "🎮 Eventos Servidor" para ver la carpeta de eventos específicos.

📍 RUTAS DE ARCHIVOS:
• Log principal: logs/app.log
• Eventos servidor: logs/server_events/server_events_YYYY-MM-DD.log
""")
