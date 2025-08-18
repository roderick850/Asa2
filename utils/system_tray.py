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
                # Redimensionar a 32x32 para mejor visibilidad en la bandeja
                image = image.resize((32, 32), Image.Resampling.LANCZOS)
                # Convertir a RGBA para compatibilidad
                if image.mode != 'RGBA':
                    image = image.convert('RGBA')
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
        import sys
        
        # Determinar directorio base (para ejecutables empaquetados)
        if getattr(sys, 'frozen', False):
            # Si está ejecutándose como ejecutable empaquetado
            base_dir = os.path.dirname(sys.executable)
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller temp folder
                temp_dir = sys._MEIPASS
            else:
                temp_dir = base_dir
        else:
            # Si está ejecutándose como script
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            temp_dir = base_dir
        
        # Posibles ubicaciones del icono
        possible_paths = [
            # En el directorio del ejecutable
            os.path.join(base_dir, "ico", "ArkManager.ico"),
            os.path.join(base_dir, "ArkManager.ico"),
            
            # En el directorio temporal de PyInstaller
            os.path.join(temp_dir, "ico", "ArkManager.ico"),
            os.path.join(temp_dir, "ArkManager.ico"),
            
            # Rutas relativas (para desarrollo)
            "ico/ArkManager.ico",
            "icons/ArkManager.ico", 
            "assets/ArkManager.ico",
            "ArkManager.ico"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.logger.info(f"Icono encontrado en: {path}")
                return path
        
        self.logger.warning("No se encontró archivo de icono, usando icono por defecto")
        return None
    
    def create_default_icon(self):
        """Crear un icono por defecto"""
        # Crear una imagen simple 32x32 con diseño más llamativo
        image = Image.new('RGBA', (32, 32), (0, 120, 215, 255))  # Azul
        
        # Agregar un diseño simple (rectángulo blanco en el centro)
        try:
            from PIL import ImageDraw
            draw = ImageDraw.Draw(image)
            # Dibujar un rectángulo blanco en el centro
            draw.rectangle([8, 8, 24, 24], fill=(255, 255, 255, 255))
            # Dibujar un punto azul en el centro para representar ARK
            draw.rectangle([14, 14, 18, 18], fill=(0, 120, 215, 255))
        except:
            # Si falla, usar solo el color sólido
            pass
            
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
        if not self.tray_available:
            self.logger.warning("pystray no disponible, bandeja del sistema deshabilitada")
            return False
        
        # Verificar si ya hay un icono activo
        if self.tray_icon is not None:
            self.logger.warning("Ya hay un icono de bandeja activo, no se creará otro")
            return True
            
        if not self.create_tray_icon():
            self.logger.error("No se pudo crear el icono de bandeja")
            return False
            
        try:
            # Verificar que el icono se creó correctamente
            if not self.tray_icon:
                self.logger.error("Icono de bandeja es None")
                return False
            
            # Ejecutar en un hilo separado con manejo de errores mejorado
            def run_tray():
                try:
                    self.logger.info("Iniciando hilo de bandeja del sistema...")
                    self.tray_icon.run()
                except Exception as e:
                    self.logger.error(f"Error en hilo de bandeja: {e}")
            
            tray_thread = threading.Thread(target=run_tray, daemon=True)
            tray_thread.start()
            
            # Esperar un momento para verificar que se inició correctamente
            time.sleep(0.5)
            
            self.logger.info("Bandeja del sistema iniciada correctamente")
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
    
    def _safe_after(self, delay, func):
        """Ejecutar función de forma segura en el hilo principal de Tkinter"""
        try:
            # Verificar si el hilo principal está disponible
            if hasattr(self.main_window, 'root') and self.main_window.root:
                self.main_window.root.after(delay, func)
            else:
                self.logger.warning("No se puede ejecutar función: ventana principal no disponible")
        except RuntimeError as e:
            if "main thread is not in main loop" in str(e):
                self.logger.warning(f"No se puede ejecutar función desde hilo secundario: {func}")
                # Intentar ejecutar directamente si es posible
                try:
                    func()
                except Exception as direct_error:
                    self.logger.error(f"Error ejecutando función directamente: {direct_error}")
            else:
                self.logger.error(f"Error en _safe_after: {e}")
        except Exception as e:
            self.logger.error(f"Error inesperado en _safe_after: {e}")
    
    def show_window(self, icon=None, item=None):
        """Mostrar ventana principal desde la bandeja"""
        try:
            if self.is_hidden and hasattr(self.main_window, 'root') and self.main_window.root:
                self.main_window.root.deiconify()
                self.main_window.root.lift()
                self.main_window.root.focus_force()
                self.is_hidden = False
        except RuntimeError as e:
            if "main thread is not in main loop" in str(e):
                self.logger.warning("No se puede mostrar ventana: hilo principal no disponible")
            else:
                self.logger.error(f"Error mostrando ventana: {e}")
        except Exception as e:
            self.logger.error(f"Error inesperado mostrando ventana: {e}")
    
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
                self._safe_after(0, self.main_window.server_panel.start_server)
                self.show_notification("Servidor", "Iniciando servidor...")
        except Exception as e:
            self.logger.error(f"Error al iniciar servidor desde bandeja: {e}")
    
    def stop_server(self, icon=None, item=None):
        """Detener servidor desde la bandeja"""
        try:
            if hasattr(self.main_window, 'server_panel'):
                self._safe_after(0, self.main_window.server_panel.stop_server)
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
                self._safe_after(0, lambda: self.main_window.backup_panel.manual_backup())
                self.show_notification("Backup", "Iniciando backup manual...")
        except Exception as e:
            self.logger.error(f"Error al hacer backup desde bandeja: {e}")
    
    def show_settings(self, icon=None, item=None):
        """Mostrar configuraciones"""
        self.show_window()
        # Mostrar diálogo de configuraciones
        self._safe_after(100, self.main_window.show_configuracion)
    
    def show_about(self, icon=None, item=None):
        """Mostrar información acerca de"""
        self.show_window()
        self._safe_after(100, self.main_window.show_ayuda)
    
    def quit_application(self, icon=None, item=None):
        """Salir de la aplicación completamente"""
        try:
            if self.app_settings.get_setting("confirm_exit"):
                # Mostrar ventana para confirmar
                self.show_window()
                self._safe_after(100, self.main_window.salir_aplicacion)
            else:
                self.stop_tray()
                # Usar _safe_after para quit también
                self._safe_after(0, self.main_window.root.quit)
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
                self.logger.info("Deteniendo icono de bandeja...")
                self.tray_icon.stop()
                self.tray_icon = None
                self.is_hidden = False
                self.logger.info("Bandeja del sistema detenida correctamente")
            except Exception as e:
                self.logger.error(f"Error al detener bandeja: {e}")
                # Forzar limpieza en caso de error
                self.tray_icon = None
                self.is_hidden = False
    
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
    
    def cleanup_duplicate_icons(self):
        """Limpiar iconos duplicados si existen"""
        try:
            if self.tray_icon:
                self.logger.info("Limpiando posibles iconos duplicados...")
                # Detener el icono actual si existe
                self.stop_tray()
                # Esperar un momento para que se limpie
                import time
                time.sleep(0.5)
                self.logger.info("Limpieza de iconos completada")
        except Exception as e:
            self.logger.error(f"Error al limpiar iconos duplicados: {e}")
    
    def restart_tray(self):
        """Reiniciar el sistema de bandeja (útil para resolver duplicados)"""
        try:
            self.logger.info("Reiniciando sistema de bandeja...")
            self.cleanup_duplicate_icons()
            return self.start_tray()
        except Exception as e:
            self.logger.error(f"Error al reiniciar bandeja: {e}")
            return False
