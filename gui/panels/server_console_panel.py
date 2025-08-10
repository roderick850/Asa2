import customtkinter as ctk
import threading
import time
from datetime import datetime

class ServerConsolePanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, logger, main_window=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.main_window = main_window
        
        # Variables de estado
        self.console_active = False
        self.console_buffer = []
        self.max_buffer_lines = 1000  # Máximo de líneas en el buffer
        
        # Empaquetar el frame principal
        self.pack(fill="both", expand=True)
        
        self.create_widgets()
        
    def create_widgets(self):
        """Crear todos los widgets del panel de consola"""
        
        # Frame superior con controles
        control_frame = ctk.CTkFrame(self)
        control_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        # Título y estado
        title_label = ctk.CTkLabel(control_frame, text="🎮 Consola del Servidor", font=("Arial", 16, "bold"))
        title_label.pack(side="left", padx=10, pady=5)
        
        # Estado de la consola
        self.status_label = ctk.CTkLabel(control_frame, text="⏸️ Consola inactiva", font=("Arial", 12))
        self.status_label.pack(side="left", padx=20, pady=5)
        
        # Botones de control
        button_frame = ctk.CTkFrame(control_frame)
        button_frame.pack(side="right", padx=10, pady=5)
        
        # Botón limpiar consola
        self.clear_btn = ctk.CTkButton(
            button_frame, 
            text="🧹 Limpiar", 
            command=self.clear_console,
            width=100
        )
        self.clear_btn.pack(side="left", padx=5)
        
        # Botón exportar consola
        self.export_btn = ctk.CTkButton(
            button_frame, 
            text="📁 Exportar", 
            command=self.export_console,
            width=100
        )
        self.export_btn.pack(side="left", padx=5)
        
        # Botón auto-scroll
        self.auto_scroll_var = ctk.BooleanVar(value=True)
        self.auto_scroll_btn = ctk.CTkCheckBox(
            button_frame,
            text="📜 Auto-scroll",
            variable=self.auto_scroll_var,
            command=self.toggle_auto_scroll
        )
        self.auto_scroll_btn.pack(side="left", padx=10)
        
        # Frame principal de la consola
        console_frame = ctk.CTkFrame(self)
        console_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        # Texto de la consola
        self.console_text = ctk.CTkTextbox(
            console_frame,
            font=("Consolas", 10),
            wrap="word",
            state="disabled"
        )
        self.console_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar personalizado
        self.scrollbar = ctk.CTkScrollbar(console_frame, command=self.console_text.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.console_text.configure(yscrollcommand=self.scrollbar.set)
        
        # Frame inferior con información
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        # Información de líneas
        self.lines_label = ctk.CTkLabel(info_frame, text="Líneas: 0", font=("Arial", 10))
        self.lines_label.pack(side="left", padx=10, pady=5)
        
        # Última actualización
        self.last_update_label = ctk.CTkLabel(info_frame, text="Última actualización: Nunca", font=("Arial", 10))
        self.last_update_label.pack(side="left", padx=20, pady=5)
        
        # Tamaño del buffer
        self.buffer_label = ctk.CTkLabel(info_frame, text="Buffer: 0/1000", font=("Arial", 10))
        self.buffer_label.pack(side="right", padx=10, pady=5)
        
        # Inicializar consola
        self.update_info()
        
    def add_console_line(self, line, line_type="info"):
        """Agregar una línea a la consola"""
        try:
            # Obtener timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Formatear línea según el tipo
            if line_type == "error":
                formatted_line = f"[{timestamp}] ❌ {line}\n"
                color_tag = "error"
            elif line_type == "warning":
                formatted_line = f"[{timestamp}] ⚠️ {line}\n"
                color_tag = "warning"
            elif line_type == "success":
                formatted_line = f"[{timestamp}] ✅ {line}\n"
                color_tag = "success"
            elif line_type == "info":
                formatted_line = f"[{timestamp}] ℹ️ {line}\n"
                color_tag = "info"
            else:
                formatted_line = f"[{timestamp}] {line}\n"
                color_tag = "normal"
            
            # Agregar al buffer
            self.console_buffer.append({
                'text': formatted_line,
                'type': line_type,
                'timestamp': timestamp,
                'raw': line
            })
            
            # Limitar tamaño del buffer
            if len(self.console_buffer) > self.max_buffer_lines:
                self.console_buffer.pop(0)
            
            # Actualizar UI en el hilo principal
            self.after(0, self._update_console_ui, formatted_line, color_tag)
            
        except Exception as e:
            self.logger.error(f"Error al agregar línea a consola: {e}")
    
    def _update_console_ui(self, formatted_line, color_tag):
        """Actualizar la UI de la consola (debe ejecutarse en hilo principal)"""
        try:
            # Habilitar edición temporalmente
            self.console_text.configure(state="normal")
            
            # Insertar línea al final
            self.console_text.insert("end", formatted_line)
            
            # Aplicar colores si están disponibles
            if hasattr(self.console_text, 'tag_config'):
                # Configurar tags de color
                if color_tag == "error":
                    self.console_text.tag_config("error", foreground="red")
                elif color_tag == "warning":
                    self.console_text.tag_config("warning", foreground="orange")
                elif color_tag == "success":
                    self.console_text.tag_config("success", foreground="green")
                elif color_tag == "info":
                    self.console_text.tag_config("info", foreground="blue")
                
                # Aplicar tag a la línea
                start = f"{self.console_text.index('end-2c').split('.')[0]}.0"
                end = "end-1c"
                self.console_text.tag_add(color_tag, start, end)
            
            # Auto-scroll si está habilitado
            if self.auto_scroll_var.get():
                self.console_text.see("end")
            
            # Deshabilitar edición
            self.console_text.configure(state="disabled")
            
            # Actualizar información
            self.update_info()
            
        except Exception as e:
            self.logger.error(f"Error al actualizar UI de consola: {e}")
    
    def clear_console(self):
        """Limpiar la consola"""
        try:
            self.console_text.configure(state="normal")
            self.console_text.delete("1.0", "end")
            self.console_text.configure(state="disabled")
            
            # Limpiar buffer
            self.console_buffer.clear()
            
            # Actualizar información
            self.update_info()
            
            self.logger.info("Consola del servidor limpiada")
            
        except Exception as e:
            self.logger.error(f"Error al limpiar consola: {e}")
    
    def export_console(self):
        """Exportar la consola a un archivo"""
        try:
            from tkinter import filedialog
            import os
            
            # Obtener fecha y hora para el nombre del archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"server_console_{timestamp}.txt"
            
            # Abrir diálogo de guardado
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
                initialname=filename
            )
            
            if file_path:
                # Escribir contenido al archivo
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("=== CONSOLA DEL SERVIDOR ARK ===\n")
                    f.write(f"Exportado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for entry in self.console_buffer:
                        f.write(entry['text'])
                
                self.logger.info(f"Consola exportada a: {file_path}")
                
                # Mostrar mensaje de éxito
                self.show_export_success(file_path)
                
        except Exception as e:
            self.logger.error(f"Error al exportar consola: {e}")
    
    def show_export_success(self, file_path):
        """Mostrar mensaje de éxito al exportar"""
        try:
            # Crear ventana de confirmación
            dialog = ctk.CTkToplevel(self)
            dialog.title("✅ Exportación Exitosa")
            dialog.geometry("400x150")
            dialog.resizable(False, False)
            
            # Centrar ventana
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
            y = (dialog.winfo_screenheight() // 2) - (150 // 2)
            dialog.geometry(f"400x150+{x}+{y}")
            
            # Contenido
            success_label = ctk.CTkLabel(
                dialog, 
                text="✅ Consola exportada exitosamente",
                font=("Arial", 14, "bold")
            )
            success_label.pack(pady=(20, 10))
            
            path_label = ctk.CTkLabel(
                dialog, 
                text=f"📁 Archivo: {os.path.basename(file_path)}",
                font=("Arial", 12)
            )
            path_label.pack(pady=5)
            
            # Botón cerrar
            close_btn = ctk.CTkButton(
                dialog,
                text="Cerrar",
                command=dialog.destroy,
                width=100
            )
            close_btn.pack(pady=20)
            
            # Hacer la ventana modal
            dialog.transient(self)
            dialog.grab_set()
            dialog.focus_set()
            
        except Exception as e:
            self.logger.error(f"Error al mostrar diálogo de éxito: {e}")
    
    def toggle_auto_scroll(self):
        """Alternar auto-scroll"""
        if self.auto_scroll_var.get():
            self.console_text.see("end")
            self.logger.info("Auto-scroll habilitado")
        else:
            self.logger.info("Auto-scroll deshabilitado")
    
    def update_info(self):
        """Actualizar información de la consola"""
        try:
            # Líneas totales
            total_lines = len(self.console_buffer)
            self.lines_label.configure(text=f"Líneas: {total_lines}")
            
            # Tamaño del buffer
            self.buffer_label.configure(text=f"Buffer: {total_lines}/{self.max_buffer_lines}")
            
            # Última actualización
            if self.console_buffer:
                last_entry = self.console_buffer[-1]
                self.last_update_label.configure(text=f"Última actualización: {last_entry['timestamp']}")
            else:
                self.last_update_label.configure(text="Última actualización: Nunca")
                
        except Exception as e:
            self.logger.error(f"Error al actualizar información: {e}")
    
    def set_console_active(self, active):
        """Establecer estado activo/inactivo de la consola"""
        self.console_active = active
        
        if active:
            self.status_label.configure(text="🟢 Consola activa", text_color="green")
        else:
            self.status_label.configure(text="⏸️ Consola inactiva", text_color="gray")
    
    def get_console_content(self):
        """Obtener contenido actual de la consola"""
        return self.console_text.get("1.0", "end-1c")
    
    def add_server_output(self, output, output_type="info"):
        """Método público para agregar salida del servidor"""
        self.add_console_line(output, output_type)
    
    def add_server_event(self, event_type, message):
        """Agregar evento del servidor a la consola"""
        event_messages = {
            "start": f"🚀 Servidor iniciado: {message}",
            "stop": f"🛑 Servidor detenido: {message}",
            "restart": f"🔄 Servidor reiniciado: {message}",
            "update": f"📦 Actualización: {message}",
            "backup": f"💾 Backup: {message}",
            "save": f"💾 SaveWorld: {message}",
            "error": f"❌ Error: {message}",
            "warning": f"⚠️ Advertencia: {message}",
            "info": f"ℹ️ Info: {message}"
        }
        
        event_text = event_messages.get(event_type, f"📝 {event_type}: {message}")
        self.add_console_line(event_text, event_type)
