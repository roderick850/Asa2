"""
Diálogos personalizados con CustomTkinter para reemplazar tkinter.messagebox
"""

import customtkinter as ctk


class CustomMessageBox:
    """Diálogo de mensaje personalizado con CustomTkinter"""
    
    def __init__(self, parent, title, message, dialog_type="info", buttons=None):
        self.parent = parent
        self.title = title
        self.message = message
        self.dialog_type = dialog_type
        self.result = None
        self.dialog = None
        
        # Configurar botones según el tipo
        if buttons is None:
            if dialog_type == "yesno":
                self.buttons = ["Sí", "No"]
            elif dialog_type == "error":
                self.buttons = ["OK"]
            elif dialog_type == "warning":
                self.buttons = ["OK"]
            else:  # info
                self.buttons = ["OK"]
        else:
            self.buttons = buttons
        
        # Iconos según el tipo
        self.icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "question": "❓",
            "yesno": "❓"
        }
        
    def show(self):
        """Mostrar el diálogo y retornar el resultado"""
        if self.dialog is not None:
            self.dialog.lift()
            return self.result
            
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("400x200")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Centrar en pantalla
        self.dialog.geometry("+400+300")
        
        # Configurar el grid
        self.dialog.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(0, weight=1)
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Icono y título
        icon = self.icons.get(self.dialog_type, "ℹ️")
        title_label = ctk.CTkLabel(
            main_frame,
            text=f"{icon} {self.title}",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(10, 5))
        
        # Mensaje
        message_label = ctk.CTkLabel(
            main_frame,
            text=self.message,
            font=("Arial", 12),
            wraplength=350,
            justify="center"
        )
        message_label.grid(row=1, column=0, pady=10, padx=20)
        
        # Frame de botones
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.grid(row=2, column=0, pady=(10, 20), sticky="ew")
        
        # Crear botones
        for i, button_text in enumerate(self.buttons):
            button = ctk.CTkButton(
                buttons_frame,
                text=button_text,
                command=lambda text=button_text: self.button_clicked(text),
                width=100
            )
            button.grid(row=0, column=i, padx=10, pady=10)
            buttons_frame.grid_columnconfigure(i, weight=1)
        
        # Manejar cierre de ventana
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Esperar hasta que se cierre el diálogo
        self.dialog.wait_window()
        
        return self.result
    
    def button_clicked(self, button_text):
        """Manejar click de botón"""
        self.result = button_text
        self.dialog.destroy()
    
    def on_close(self):
        """Manejar cierre de ventana"""
        self.result = "No" if "No" in self.buttons else self.buttons[-1]
        self.dialog.destroy()


def show_info(parent, title, message):
    """Mostrar diálogo de información"""
    dialog = CustomMessageBox(parent, title, message, "info")
    return dialog.show()


def show_warning(parent, title, message):
    """Mostrar diálogo de advertencia"""
    dialog = CustomMessageBox(parent, title, message, "warning")
    return dialog.show()


def show_error(parent, title, message):
    """Mostrar diálogo de error"""
    dialog = CustomMessageBox(parent, title, message, "error")
    return dialog.show()


def ask_yes_no(parent, title, message):
    """Mostrar diálogo de sí/no"""
    dialog = CustomMessageBox(parent, title, message, "yesno")
    result = dialog.show()
    return result == "Sí"


def ask_question(parent, title, message, buttons=None):
    """Mostrar diálogo con botones personalizados"""
    if buttons is None:
        buttons = ["Sí", "No"]
    dialog = CustomMessageBox(parent, title, message, "question", buttons)
    return dialog.show()


class CustomInputDialog:
    """Diálogo de entrada de texto personalizado"""
    
    def __init__(self, parent, title, prompt, default_value=""):
        self.parent = parent
        self.title = title
        self.prompt = prompt
        self.default_value = default_value
        self.result = None
        self.dialog = None
        
    def show(self):
        """Mostrar el diálogo y retornar el resultado"""
        if self.dialog is not None:
            self.dialog.lift()
            return self.result
            
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("400x180")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Centrar en pantalla
        self.dialog.geometry("+400+300")
        
        # Configurar el grid
        self.dialog.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(0, weight=1)
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text=f"💬 {self.title}",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(10, 5))
        
        # Prompt
        prompt_label = ctk.CTkLabel(
            main_frame,
            text=self.prompt,
            font=("Arial", 12)
        )
        prompt_label.grid(row=1, column=0, pady=5, padx=20)
        
        # Entry
        self.entry = ctk.CTkEntry(
            main_frame,
            width=300,
            placeholder_text=self.default_value
        )
        self.entry.grid(row=2, column=0, pady=10, padx=20, sticky="ew")
        self.entry.insert(0, self.default_value)
        
        # Frame de botones
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.grid(row=3, column=0, pady=(10, 20), sticky="ew")
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        # Botones
        ok_button = ctk.CTkButton(
            buttons_frame,
            text="OK",
            command=self.ok_clicked,
            width=100
        )
        ok_button.grid(row=0, column=0, padx=10, pady=10)
        
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancelar",
            command=self.cancel_clicked,
            width=100
        )
        cancel_button.grid(row=0, column=1, padx=10, pady=10)
        
        # Manejar Enter y Escape
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.cancel_clicked())
        
        # Focus en el entry
        self.entry.focus()
        
        # Manejar cierre de ventana
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel_clicked)
        
        # Esperar hasta que se cierre el diálogo
        self.dialog.wait_window()
        
        return self.result
    
    def ok_clicked(self):
        """Manejar click de OK"""
        self.result = self.entry.get()
        self.dialog.destroy()
    
    def cancel_clicked(self):
        """Manejar click de Cancelar"""
        self.result = None
        self.dialog.destroy()


def ask_string(parent, title, prompt, default_value=""):
    """Solicitar entrada de texto"""
    dialog = CustomInputDialog(parent, title, prompt, default_value)
    return dialog.show()


class CustomProgressDialog:
    """Diálogo de progreso personalizado"""
    
    def __init__(self, parent, title, message="Procesando..."):
        self.parent = parent
        self.title = title
        self.message = message
        self.dialog = None
        self.progress_bar = None
        self.status_label = None
        
    def show(self):
        """Mostrar el diálogo de progreso"""
        if self.dialog is not None:
            self.dialog.lift()
            return
            
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("400x150")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Centrar en pantalla
        self.dialog.geometry("+400+350")
        
        # Configurar el grid
        self.dialog.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(0, weight=1)
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text=f"⏳ {self.title}",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(10, 5))
        
        # Mensaje de estado
        self.status_label = ctk.CTkLabel(
            main_frame,
            text=self.message,
            font=("Arial", 12)
        )
        self.status_label.grid(row=1, column=0, pady=5, padx=20)
        
        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(main_frame, width=300)
        self.progress_bar.grid(row=2, column=0, pady=10, padx=20, sticky="ew")
        self.progress_bar.set(0)
        
        # Evitar que se cierre
        self.dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        
    def update_progress(self, value, status=None):
        """Actualizar progreso"""
        if self.progress_bar:
            self.progress_bar.set(value)
        if status and self.status_label:
            self.status_label.configure(text=status)
        if self.dialog:
            self.dialog.update()
    
    def close(self):
        """Cerrar el diálogo"""
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None
