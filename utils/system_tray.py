"""
Sistema de bandeja del sistema para Ark Server Manager
"""

import sys
import os
import tkinter as tk
from PIL import Image, ImageTk
import threading
import time


class SystemTray:
    """Gestor de bandeja del sistema"""
    
    def __init__(self, main_window, app_settings, logger):
        self.main_window = main_window
        self.app_settings = app_settings
        self.logger = logger
        self.tray_icon = None
        self.tray_menu = None
        self.is_hidden = False
        
        # Intentar importar pystray
        try:
            import pystray
            self.pystray = pystray
            self.tray_available = True
        except ImportError:
            self.logger.warning("pystray no está disponible. Funcionalidad de bandeja deshabilitada.")
            self.tray_available = False
    
    def create_tray_icon(self):
        """Crear el icono de la bandeja del sistema"""
        if not self.tray_available:
            return False
            
        try:
            # Buscar el icono
            icon_path = self.find_icon_file()
            
            if icon_path and os.path.exists(icon_path):
                # Cargar imagen del icono
                image = Image.open(icon_path)
                # Redimensionar a 16x16 para la bandeja
                image = image.resize((16, 16), Image.Resampling.LANCZOS)
            else:
                # Crear un icono simple si no se encuentra el archivo
                image = self.create_default_icon()
            
            # Crear menú contextual
            menu = self.create_tray_menu()
            
            # Crear el icono de la bandeja
            self.tray_icon = self.pystray.Icon(
                "ArkServerManager",
                image,
                "Ark Server Manager",
                menu
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al crear icono de bandeja: {e}")
            return False
    
    def find_icon_file(self):
        """Buscar el archivo de icono"""
        possible_paths = [
            "ico/ArkManager.ico",
            "icons/ArkManager.ico",
            "assets/ArkManager.ico",
            "ArkManager.ico"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def create_default_icon(self):
        """Crear un icono por defecto"""
        # Crear una imagen simple 16x16
        image = Image.new('RGBA', (16, 16), (0, 120, 215, 255))  # Azul
        return image
    
    def create_tray_menu(self):
        """Crear menú contextual de la bandeja"""
        if not self.tray_available:
            return None
            
        return self.pystray.Menu(
            self.pystray.MenuItem(
                "🏠 Mostrar Ventana",
                self.show_window,
                default=True
            ),
            self.pystray.MenuItem(
                "🎮 Iniciar Servidor",
                self.start_server,
                enabled=lambda item: self.can_start_server()
            ),
            self.pystray.MenuItem(
                "⏹️ Detener Servidor",
                self.stop_server,
                enabled=lambda item: self.can_stop_server()
            ),
            self.pystray.Menu.SEPARATOR,
            self.pystray.MenuItem(
                "📊 Estado del Servidor",
                self.show_server_status
            ),
            self.pystray.MenuItem(
                "💾 Backup Manual",
                self.manual_backup
            ),
            self.pystray.Menu.SEPARATOR,
            self.pystray.MenuItem(
                "⚙️ Configuraciones",
                self.show_settings
            ),
            self.pystray.MenuItem(
                "❓ Acerca de",
                self.show_about
            ),
            self.pystray.Menu.SEPARATOR,
            self.pystray.MenuItem(
                "🚪 Salir",
                self.quit_application
            )
        )
    
    def start_tray(self):
        """Iniciar la bandeja del sistema"""
        if not self.tray_available or not self.create_tray_icon():
            return False
            
        try:
            # Ejecutar en un hilo separado
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
            
            self.logger.info("Bandeja del sistema iniciada")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al iniciar bandeja del sistema: {e}")
            return False
    
    def hide_to_tray(self):
        """Ocultar ventana principal a la bandeja"""
        if self.tray_available and self.tray_icon:
            self.main_window.root.withdraw()
            self.is_hidden = True
            self.show_notification("Ark Server Manager", "Aplicación minimizada a la bandeja del sistema")
    
    def show_window(self, icon=None, item=None):
        """Mostrar ventana principal desde la bandeja"""
        if self.is_hidden:
            self.main_window.root.deiconify()
            self.main_window.root.lift()
            self.main_window.root.focus_force()
            self.is_hidden = False
    
    def can_start_server(self):
        """Verificar si se puede iniciar el servidor"""
        try:
            if hasattr(self.main_window, 'server_panel'):
                return not self.main_window.server_panel.is_server_running()
            return True
        except:
            return True
    
    def can_stop_server(self):
        """Verificar si se puede detener el servidor"""
        try:
            if hasattr(self.main_window, 'server_panel'):
                return self.main_window.server_panel.is_server_running()
            return False
        except:
            return False
    
    def start_server(self, icon=None, item=None):
        """Iniciar servidor desde la bandeja"""
        try:
            if hasattr(self.main_window, 'server_panel'):
                self.main_window.root.after(0, self.main_window.server_panel.start_server)
                self.show_notification("Servidor", "Iniciando servidor...")
        except Exception as e:
            self.logger.error(f"Error al iniciar servidor desde bandeja: {e}")
    
    def stop_server(self, icon=None, item=None):
        """Detener servidor desde la bandeja"""
        try:
            if hasattr(self.main_window, 'server_panel'):
                self.main_window.root.after(0, self.main_window.server_panel.stop_server)
                self.show_notification("Servidor", "Deteniendo servidor...")
        except Exception as e:
            self.logger.error(f"Error al detener servidor desde bandeja: {e}")
    
    def show_server_status(self, icon=None, item=None):
        """Mostrar estado del servidor"""
        try:
            # Esto mostraría la ventana y iría a la pestaña de estado
            self.show_window()
            # Opcional: cambiar a pestaña específica
        except Exception as e:
            self.logger.error(f"Error al mostrar estado: {e}")
    
    def manual_backup(self, icon=None, item=None):
        """Realizar backup manual desde la bandeja"""
        try:
            if hasattr(self.main_window, 'backup_panel'):
                self.main_window.root.after(0, lambda: self.main_window.backup_panel.manual_backup())
                self.show_notification("Backup", "Iniciando backup manual...")
        except Exception as e:
            self.logger.error(f"Error al hacer backup desde bandeja: {e}")
    
    def show_settings(self, icon=None, item=None):
        """Mostrar configuraciones"""
        self.show_window()
        # Mostrar diálogo de configuraciones
        self.main_window.root.after(100, self.main_window.show_configuracion)
    
    def show_about(self, icon=None, item=None):
        """Mostrar información acerca de"""
        self.show_window()
        self.main_window.root.after(100, self.main_window.show_ayuda)
    
    def quit_application(self, icon=None, item=None):
        """Salir de la aplicación completamente"""
        try:
            if self.app_settings.get_setting("confirm_exit"):
                # Mostrar ventana para confirmar
                self.show_window()
                self.main_window.root.after(100, self.main_window.salir_aplicacion)
            else:
                self.stop_tray()
                self.main_window.root.quit()
        except Exception as e:
            self.logger.error(f"Error al salir desde bandeja: {e}")
    
    def show_notification(self, title, message, duration=3):
        """Mostrar notificación de la bandeja"""
        if self.tray_available and self.tray_icon:
            try:
                self.tray_icon.notify(message, title)
            except:
                # Fallback a notificación del sistema de Windows
                self.show_windows_notification(title, message)
    
    def show_windows_notification(self, title, message):
        """Mostrar notificación nativa de Windows"""
        try:
            import win10toast
            toaster = win10toast.ToastNotifier()
            toaster.show_toast(title, message, duration=3)
        except ImportError:
            # Si no está disponible, registrar en logs
            self.logger.info(f"Notificación: {title} - {message}")
    
    def stop_tray(self):
        """Detener la bandeja del sistema"""
        if self.tray_icon:
            try:
                self.tray_icon.stop()
                self.tray_icon = None
                self.logger.info("Bandeja del sistema detenida")
            except Exception as e:
                self.logger.error(f"Error al detener bandeja: {e}")
    
    def update_icon_status(self, server_running=False):
        """Actualizar el icono según el estado del servidor"""
        if not self.tray_available or not self.tray_icon:
            return
            
        try:
            # Cambiar el título del icono según el estado
            if server_running:
                self.tray_icon.title = "Ark Server Manager - Servidor Ejecutándose"
            else:
                self.tray_icon.title = "Ark Server Manager - Servidor Detenido"
        except Exception as e:
            self.logger.error(f"Error al actualizar icono: {e}")
    
    def is_available(self):
        """Verificar si la funcionalidad de bandeja está disponible"""
        return self.tray_available
