"""
Gestor de configuraciones avanzadas de la aplicación
Maneja inicio automático, bandeja del sistema, etc.
"""

import json
import os
import sys
import winreg
from pathlib import Path


class AppSettings:
    """Gestor de configuraciones avanzadas de la aplicación"""
    
    def __init__(self, config_manager, logger):
        self.config_manager = config_manager
        self.logger = logger
        self.settings_file = "data/app_settings.json"
        self.app_name = "ArkServerManager"
        self.app_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
        
        # Configuraciones por defecto
        self.default_settings = {
            "startup_with_windows": False,
            "auto_start_server": False,
            "minimize_to_tray": False,
            "always_on_top": False,
            "minimize_on_start": False,
            "close_to_tray": False,
            "auto_check_updates": True,
            "start_minimized": False,
            "remember_window_position": True,
            "auto_backup_on_start": False,
            "confirm_exit": True,
            "hide_console": True,
            "theme_mode": "system",  # light, dark, system
            "auto_save_config": True,
            "notification_sound": True,
            "window_x": None,
            "window_y": None,
            "window_width": 1200,
            "window_height": 800,
            "selected_server_on_start": None,
            "selected_map_on_start": None
        }
        
        self.settings = self.load_settings()
        
    def load_settings(self):
        """Cargar configuraciones desde archivo"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                # Combinar con defaults para nuevas opciones
                settings = self.default_settings.copy()
                settings.update(loaded_settings)
                return settings
            else:
                return self.default_settings.copy()
        except Exception as e:
            self.logger.error(f"Error al cargar configuraciones: {e}")
            return self.default_settings.copy()
    
    def save_settings(self):
        """Guardar configuraciones a archivo"""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Configuraciones guardadas correctamente")
            return True
        except Exception as e:
            self.logger.error(f"Error al guardar configuraciones: {e}")
            return False
    
    def get_setting(self, key, default=None):
        """Obtener una configuración específica"""
        return self.settings.get(key, default if default is not None else self.default_settings.get(key))
    
    def set_setting(self, key, value):
        """Establecer una configuración específica"""
        self.settings[key] = value
        if self.get_setting("auto_save_config"):
            self.save_settings()
    
    def toggle_setting(self, key):
        """Alternar una configuración booleana"""
        current = self.get_setting(key, False)
        self.set_setting(key, not current)
        return not current
    
    def set_startup_with_windows(self, enabled):
        """Configurar inicio automático con Windows"""
        try:
            reg_key = winreg.HKEY_CURRENT_USER
            reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            with winreg.OpenKey(reg_key, reg_path, 0, winreg.KEY_ALL_ACCESS) as key:
                if enabled:
                    # Agregar entrada de registro
                    winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, f'"{self.app_path}" --minimized')
                    self.logger.info("Inicio automático con Windows habilitado")
                else:
                    # Eliminar entrada de registro
                    try:
                        winreg.DeleteValue(key, self.app_name)
                        self.logger.info("Inicio automático con Windows deshabilitado")
                    except FileNotFoundError:
                        pass  # Ya no existe
            
            self.set_setting("startup_with_windows", enabled)
            return True
            
        except Exception as e:
            self.logger.error(f"Error al configurar inicio automático: {e}")
            return False
    
    def is_startup_enabled(self):
        """Verificar si el inicio automático está habilitado"""
        try:
            reg_key = winreg.HKEY_CURRENT_USER
            reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            with winreg.OpenKey(reg_key, reg_path, 0, winreg.KEY_READ) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, self.app_name)
                    return True
                except FileNotFoundError:
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error al verificar inicio automático: {e}")
            return False
    
    def save_window_position(self, x, y, width, height):
        """Guardar posición y tamaño de ventana"""
        if self.get_setting("remember_window_position"):
            self.set_setting("window_x", x)
            self.set_setting("window_y", y)
            self.set_setting("window_width", width)
            self.set_setting("window_height", height)
    
    def get_window_geometry(self):
        """Obtener geometría guardada de la ventana"""
        x = self.get_setting("window_x")
        y = self.get_setting("window_y")
        width = self.get_setting("window_width", 1200)
        height = self.get_setting("window_height", 800)
        
        if x is not None and y is not None:
            return f"{width}x{height}+{x}+{y}"
        else:
            return f"{width}x{height}"
    
    def reset_to_defaults(self):
        """Restablecer configuraciones por defecto"""
        self.settings = self.default_settings.copy()
        self.save_settings()
        self.logger.info("Configuraciones restablecidas a valores por defecto")
    
    def export_settings(self, file_path):
        """Exportar configuraciones a un archivo"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Error al exportar configuraciones: {e}")
            return False
    
    def import_settings(self, file_path):
        """Importar configuraciones desde un archivo"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            # Validar que las claves son válidas
            valid_settings = {}
            for key, value in imported_settings.items():
                if key in self.default_settings:
                    valid_settings[key] = value
            
            self.settings.update(valid_settings)
            self.save_settings()
            self.logger.info("Configuraciones importadas correctamente")
            return True
        except Exception as e:
            self.logger.error(f"Error al importar configuraciones: {e}")
            return False
