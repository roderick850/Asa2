import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
from utils.scheduled_commands import ScheduledCommand

class AddTaskDialog(ctk.CTkToplevel):
    """Diálogo para agregar nueva tarea programada"""
    
    def __init__(self, parent, scheduled_manager):
        super().__init__(parent)
        self.scheduled_manager = scheduled_manager
        self.parent = parent
        
        self.title("➕ Nueva Tarea Programada")
        self.geometry("500x600")
        self.resizable(False, False)
        
        # Centrar ventana
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title_label = ctk.CTkLabel(main_frame, text="⏰ Configurar Nueva Tarea", 
                                 font=("Arial", 18, "bold"))
        title_label.pack(pady=10)
        
        # Tipo de comando
        ctk.CTkLabel(main_frame, text="Tipo de Comando:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10,5))
        
        self.command_type = ctk.CTkOptionMenu(main_frame, values=[
            "broadcast", "saveworld", "listplayers", "kick", "ban", 
            "unban", "admincheat", "destroywilddinos", "time", "weather", "custom"
        ])
        self.command_type.pack(fill="x", padx=10, pady=5)
        self.command_type.set("broadcast")
        
        # Parámetros del comando
        ctk.CTkLabel(main_frame, text="Parámetros/Texto:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10,5))
        
        self.command_params = ctk.CTkTextbox(main_frame, height=80)
        self.command_params.pack(fill="x", padx=10, pady=5)
        self.command_params.insert("1.0", "Mensaje de ejemplo")
        
        # Fecha y hora
        datetime_frame = ctk.CTkFrame(main_frame)
        datetime_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(datetime_frame, text="📅 Fecha y Hora de Ejecución", 
                    font=("Arial", 12, "bold")).pack(pady=5)
        
        # Fecha
        date_frame = ctk.CTkFrame(datetime_frame)
        date_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(date_frame, text="Fecha (YYYY-MM-DD):").pack(side="left", padx=5)
        self.date_entry = ctk.CTkEntry(date_frame, width=120)
        self.date_entry.pack(side="left", padx=5)
        
        # Establecer fecha actual por defecto
        today = datetime.now().strftime("%Y-%m-%d")
        self.date_entry.insert(0, today)
        
        # Hora
        time_frame = ctk.CTkFrame(datetime_frame)
        time_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(time_frame, text="Hora (HH:MM:SS):").pack(side="left", padx=5)
        self.time_entry = ctk.CTkEntry(time_frame, width=100)
        self.time_entry.pack(side="left", padx=5)
        
        # Establecer hora actual + 1 minuto por defecto
        future_time = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M:%S")
        self.time_entry.insert(0, future_time)
        
        # Botones de tiempo rápido
        quick_time_frame = ctk.CTkFrame(datetime_frame)
        quick_time_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(quick_time_frame, text="⚡ Tiempo rápido:").pack(side="left", padx=5)
        
        ctk.CTkButton(quick_time_frame, text="+1 min", width=60,
                     command=lambda: self.set_quick_time(1)).pack(side="left", padx=2)
        ctk.CTkButton(quick_time_frame, text="+5 min", width=60,
                     command=lambda: self.set_quick_time(5)).pack(side="left", padx=2)
        ctk.CTkButton(quick_time_frame, text="+15 min", width=60,
                     command=lambda: self.set_quick_time(15)).pack(side="left", padx=2)
        ctk.CTkButton(quick_time_frame, text="+1 hora", width=60,
                     command=lambda: self.set_quick_time(60)).pack(side="left", padx=2)
        
        # Descripción opcional
        ctk.CTkLabel(main_frame, text="Descripción (opcional):", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10,5))
        
        self.description_entry = ctk.CTkEntry(main_frame, placeholder_text="Descripción de la tarea...")
        self.description_entry.pack(fill="x", padx=10, pady=5)
        
        # Botones
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", padx=10, pady=20)
        
        ctk.CTkButton(buttons_frame, text="✅ Crear Tarea", 
                     command=self.create_task, fg_color="green").pack(side="left", padx=10)
        
        ctk.CTkButton(buttons_frame, text="❌ Cancelar", 
                     command=self.destroy, fg_color="red").pack(side="right", padx=10)
        
    def set_quick_time(self, minutes):
        """Establecer tiempo rápido"""
        future_time = datetime.now() + timedelta(minutes=minutes)
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, future_time.strftime("%Y-%m-%d"))
        self.time_entry.delete(0, "end")
        self.time_entry.insert(0, future_time.strftime("%H:%M:%S"))
        
    def create_task(self):
        """Crear nueva tarea programada"""
        try:
            # Validar datos
            command_type = self.command_type.get()
            params = self.command_params.get("1.0", "end-1c").strip()
            date_str = self.date_entry.get().strip()
            time_str = self.time_entry.get().strip()
            description = self.description_entry.get().strip()
            
            if not params:
                messagebox.showerror("Error", "Los parámetros del comando son obligatorios")
                return
                
            # Construir comando completo
            if command_type == "custom":
                full_command = params
            else:
                full_command = f"{command_type} {params}"
            
            # Parsear fecha y hora
            datetime_str = f"{date_str} {time_str}"
            execution_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            
            # Verificar que la fecha sea futura
            if execution_time <= datetime.now():
                messagebox.showerror("Error", "La fecha y hora deben ser futuras")
                return
            
            # Crear comando programado
            scheduled_command = ScheduledCommand(
                command=full_command,
                execution_time=execution_time,
                description=description or f"Comando {command_type}"
            )
            
            # Agregar al manager
            self.scheduled_manager.add_command(scheduled_command)
            
            # Mostrar confirmación
            messagebox.showinfo("Éxito", 
                              f"Tarea creada exitosamente\n\n"
                              f"Comando: {full_command}\n"
                              f"Ejecución: {execution_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Cerrar diálogo
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Formato de fecha/hora inválido: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear tarea: {e}")

class TasksListDialog(ctk.CTkToplevel):
    """Diálogo para mostrar y gestionar tareas programadas"""
    
    def __init__(self, parent, scheduled_manager):
        super().__init__(parent)
        self.scheduled_manager = scheduled_manager
        self.parent = parent
        
        self.title("📋 Tareas Programadas")
        self.geometry("700x500")
        self.resizable(True, True)
        
        # Centrar ventana
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
        self.refresh_tasks()
        
    def create_widgets(self):
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title_label = ctk.CTkLabel(main_frame, text="📋 Lista de Tareas Programadas", 
                                 font=("Arial", 18, "bold"))
        title_label.pack(pady=10)
        
        # Botones de control
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(buttons_frame, text="🔄 Actualizar", 
                     command=self.refresh_tasks).pack(side="left", padx=5)
        
        ctk.CTkButton(buttons_frame, text="🗑️ Eliminar Seleccionada", 
                     command=self.delete_selected, fg_color="red").pack(side="left", padx=5)
        
        ctk.CTkButton(buttons_frame, text="🗑️ Limpiar Todas", 
                     command=self.clear_all_tasks, fg_color="darkred").pack(side="left", padx=5)
        
        # Lista de tareas
        self.tasks_textbox = ctk.CTkTextbox(main_frame, height=300)
        self.tasks_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Botón cerrar
        ctk.CTkButton(main_frame, text="❌ Cerrar", 
                     command=self.destroy).pack(pady=10)
        
    def refresh_tasks(self):
        """Actualizar lista de tareas"""
        self.tasks_textbox.delete("1.0", "end")
        
        tasks = self.scheduled_manager.get_pending_commands()
        
        if not tasks:
            self.tasks_textbox.insert("1.0", "📭 No hay tareas programadas")
            return
            
        content = f"📊 Total de tareas: {len(tasks)}\n\n"
        
        for i, task in enumerate(tasks, 1):
            time_left = task.execution_time - datetime.now()
            if time_left.total_seconds() > 0:
                hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                time_left_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                status = "⏳ Pendiente"
            else:
                time_left_str = "¡Ya debería haberse ejecutado!"
                status = "⚠️ Atrasada"
                
            content += f"{'='*50}\n"
            content += f"📝 Tarea #{i}\n"
            content += f"ID: {task.task_id}\n"
            content += f"Comando: {task.command}\n"
            content += f"Descripción: {task.description}\n"
            content += f"Ejecución: {task.execution_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            content += f"Estado: {status}\n"
            content += f"Tiempo restante: {time_left_str}\n\n"
            
        self.tasks_textbox.insert("1.0", content)
        
    def delete_selected(self):
        """Eliminar tarea seleccionada (por ID)"""
        # Diálogo simple para pedir ID
        dialog = ctk.CTkInputDialog(text="Ingresa el ID de la tarea a eliminar:", title="Eliminar Tarea")
        task_id = dialog.get_input()
        
        if task_id:
            try:
                if self.scheduled_manager.remove_command(task_id):
                    messagebox.showinfo("Éxito", f"Tarea {task_id} eliminada")
                    self.refresh_tasks()
                else:
                    messagebox.showerror("Error", f"No se encontró la tarea {task_id}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar tarea: {e}")
                
    def clear_all_tasks(self):
        """Limpiar todas las tareas"""
        if messagebox.askyesno("Confirmar", "¿Estás seguro de eliminar TODAS las tareas programadas?"):
            self.scheduled_manager.clear_all_commands()
            messagebox.showinfo("Éxito", "Todas las tareas han sido eliminadas")
            self.refresh_tasks()

class CommandHistoryDialog(ctk.CTkToplevel):
    """Diálogo para mostrar historial de comandos ejecutados"""
    
    def __init__(self, parent, scheduled_manager):
        super().__init__(parent)
        self.scheduled_manager = scheduled_manager
        self.parent = parent
        
        self.title("📊 Historial de Comandos")
        self.geometry("700x500")
        self.resizable(True, True)
        
        # Centrar ventana
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
        self.refresh_history()
        
    def create_widgets(self):
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title_label = ctk.CTkLabel(main_frame, text="📊 Historial de Comandos Ejecutados", 
                                 font=("Arial", 18, "bold"))
        title_label.pack(pady=10)
        
        # Botones de control
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(buttons_frame, text="🔄 Actualizar", 
                     command=self.refresh_history).pack(side="left", padx=5)
        
        ctk.CTkButton(buttons_frame, text="🗑️ Limpiar Historial", 
                     command=self.clear_history, fg_color="red").pack(side="left", padx=5)
        
        ctk.CTkButton(buttons_frame, text="💾 Exportar", 
                     command=self.export_history, fg_color="blue").pack(side="left", padx=5)
        
        # Historial
        self.history_textbox = ctk.CTkTextbox(main_frame, height=300)
        self.history_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Botón cerrar
        ctk.CTkButton(main_frame, text="❌ Cerrar", 
                     command=self.destroy).pack(pady=10)
        
    def refresh_history(self):
        """Actualizar historial"""
        self.history_textbox.delete("1.0", "end")
        
        history = self.scheduled_manager.get_command_history()
        
        if not history:
            self.history_textbox.insert("1.0", "📭 No hay historial de comandos")
            return
            
        content = f"📊 Total de comandos ejecutados: {len(history)}\n\n"
        
        # Mostrar los más recientes primero
        for i, entry in enumerate(reversed(history), 1):
            status_icon = "✅" if entry.get('success', True) else "❌"
            
            content += f"{'='*50}\n"
            content += f"{status_icon} Comando #{i}\n"
            content += f"Comando: {entry.get('command', 'N/A')}\n"
            content += f"Ejecutado: {entry.get('executed_at', 'N/A')}\n"
            content += f"Resultado: {entry.get('result', 'N/A')}\n"
            if not entry.get('success', True):
                content += f"Error: {entry.get('error', 'N/A')}\n"
            content += "\n"
            
        self.history_textbox.insert("1.0", content)
        
    def clear_history(self):
        """Limpiar historial"""
        if messagebox.askyesno("Confirmar", "¿Estás seguro de limpiar el historial de comandos?"):
            self.scheduled_manager.clear_command_history()
            messagebox.showinfo("Éxito", "Historial limpiado")
            self.refresh_history()
            
    def export_history(self):
        """Exportar historial a archivo"""
        try:
            from tkinter import filedialog
            import json
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
                title="Exportar Historial"
            )
            
            if filename:
                history = self.scheduled_manager.get_command_history()
                
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(history, f, indent=2, ensure_ascii=False, default=str)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"Historial de Comandos - Exportado: {datetime.now()}\n\n")
                        for i, entry in enumerate(history, 1):
                            f.write(f"Comando #{i}\n")
                            f.write(f"Comando: {entry.get('command', 'N/A')}\n")
                            f.write(f"Ejecutado: {entry.get('executed_at', 'N/A')}\n")
                            f.write(f"Éxito: {entry.get('success', True)}\n")
                            f.write(f"Resultado: {entry.get('result', 'N/A')}\n")
                            if not entry.get('success', True):
                                f.write(f"Error: {entry.get('error', 'N/A')}\n")
                            f.write("\n" + "="*50 + "\n\n")
                
                messagebox.showinfo("Éxito", f"Historial exportado a: {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar historial: {e}")