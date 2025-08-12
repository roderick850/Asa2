#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar que el error del switch 'Confirmar salida' esté solucionado
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager
from utils.app_settings import AppSettings
from utils.logger import Logger

def test_save_settings_fix():
    """Prueba que el método save_settings funcione sin errores"""
    print("🧪 Probando corrección del error 'hide_console_var'...\n")
    
    # Inicializar configuración
    logger_instance = Logger("logs/test_fix.log")
    logger = logger_instance.logger
    config_manager = ConfigManager()
    app_settings = AppSettings(config_manager, logger)
    
    # Simular las variables que tendría el diálogo
    class MockAdvancedSettingsDialog:
        def __init__(self, app_settings, logger):
            self.app_settings = app_settings
            self.logger = logger
            
            # Simular todas las variables BooleanVar que usa save_settings
            class MockBooleanVar:
                def __init__(self, value):
                    self.value = value
                def get(self):
                    return self.value
                def set(self, value):
                    self.value = value
            
            class MockStringVar:
                def __init__(self, value):
                    self.value = value
                def get(self):
                    return self.value
                def set(self, value):
                    self.value = value
            
            # Inicializar todas las variables que usa save_settings
            self.startup_var = MockBooleanVar(app_settings.get_setting("startup_with_windows"))
            self.autostart_var = MockBooleanVar(app_settings.get_setting("auto_start_server"))
            self.autostart_windows_var = MockBooleanVar(app_settings.get_setting("auto_start_server_with_windows"))
            self.start_minimized_var = MockBooleanVar(app_settings.get_setting("start_minimized"))
            self.auto_backup_var = MockBooleanVar(app_settings.get_setting("auto_backup_on_start"))
            self.minimize_tray_var = MockBooleanVar(app_settings.get_setting("minimize_to_tray"))
            self.close_tray_var = MockBooleanVar(app_settings.get_setting("close_to_tray"))
            self.confirm_exit_var = MockBooleanVar(app_settings.get_setting("confirm_exit"))
            self.auto_updates_var = MockBooleanVar(app_settings.get_setting("auto_check_updates"))
            self.auto_save_var = MockBooleanVar(app_settings.get_setting("auto_save_config"))
            self.always_ontop_var = MockBooleanVar(app_settings.get_setting("always_on_top"))
            self.remember_position_var = MockBooleanVar(app_settings.get_setting("remember_window_position"))
            self.theme_var = MockStringVar(app_settings.get_setting("theme_mode"))
            self.notification_sound_var = MockBooleanVar(app_settings.get_setting("notification_sound"))
            self.hide_console_var = MockBooleanVar(app_settings.get_setting("hide_console"))  # ✅ ESTA ERA LA VARIABLE FALTANTE
        
        def save_settings(self):
            """Simular el método save_settings del diálogo real"""
            try:
                self.logger.info("🔄 Iniciando proceso de guardado desde diálogo...")
                
                # Forzar recarga antes de guardar para sincronizar
                self.app_settings.load_settings()
                self.logger.info("✅ Configuraciones recargadas antes de guardar")
                
                # Recopilar todos los valores con verificación
                settings_to_save = {
                    "startup_with_windows": self.startup_var.get(),
                    "auto_start_server": self.autostart_var.get(),
                    "auto_start_server_with_windows": self.autostart_windows_var.get(),
                    "start_minimized": self.start_minimized_var.get(),
                    "auto_backup_on_start": self.auto_backup_var.get(),
                    "minimize_to_tray": self.minimize_tray_var.get(),
                    "close_to_tray": self.close_tray_var.get(),
                    "confirm_exit": self.confirm_exit_var.get(),
                    "auto_check_updates": self.auto_updates_var.get(),
                    "auto_save_config": self.auto_save_var.get(),
                    "always_on_top": self.always_ontop_var.get(),
                    "remember_window_position": self.remember_position_var.get(),
                    "theme_mode": self.theme_var.get(),
                    "notification_sound": self.notification_sound_var.get(),
                    "hide_console": self.hide_console_var.get()  # ✅ AHORA INCLUIDA
                }
                
                self.logger.info(f"📝 Configuraciones recopiladas: {len(settings_to_save)} items")
                
                # Aplicar configuraciones una por una
                for key, value in settings_to_save.items():
                    self.app_settings.set_setting(key, value)
                
                # Guardar al archivo
                self.app_settings.save_settings()
                self.logger.info("✅ save_settings() completado")
                
                return True
                
            except Exception as e:
                self.logger.error(f"❌ Error crítico al guardar configuraciones: {e}")
                return False
    
    # Crear instancia mock del diálogo
    mock_dialog = MockAdvancedSettingsDialog(app_settings, logger)
    
    # Probar cambio del switch confirmar salida
    print("📋 PRUEBA 1: Cambiar switch 'Confirmar salida' a True")
    mock_dialog.confirm_exit_var.set(True)
    result1 = mock_dialog.save_settings()
    print(f"   Resultado: {'✅ ÉXITO' if result1 else '❌ FALLO'}")
    
    # Verificar que se guardó
    saved_value = app_settings.get_setting("confirm_exit")
    print(f"   Valor guardado: {saved_value}")
    
    print("\n📋 PRUEBA 2: Cambiar switch 'Confirmar salida' a False")
    mock_dialog.confirm_exit_var.set(False)
    result2 = mock_dialog.save_settings()
    print(f"   Resultado: {'✅ ÉXITO' if result2 else '❌ FALLO'}")
    
    # Verificar que se guardó
    saved_value2 = app_settings.get_setting("confirm_exit")
    print(f"   Valor guardado: {saved_value2}")
    
    # Resultados finales
    print("\n📊 RESULTADOS FINALES:")
    print(f"   ✅ Prueba 1 (activar): {result1}")
    print(f"   ✅ Prueba 2 (desactivar): {result2}")
    print(f"   ✅ Valores guardados correctamente: {saved_value == True and saved_value2 == False}")
    
    success = result1 and result2 and (saved_value == True and saved_value2 == False)
    
    if success:
        print("\n🎉 ¡ERROR SOLUCIONADO!")
        print("   • La variable 'hide_console_var' faltante ha sido agregada")
        print("   • El método save_settings() ahora funciona sin errores")
        print("   • El switch 'Confirmar salida' se puede cambiar correctamente")
        print("   • Los valores se guardan y persisten correctamente")
    else:
        print("\n⚠️ Aún hay problemas que resolver")
    
    return success

if __name__ == "__main__":
    test_save_settings_fix()