#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar que el switch "Confirmar salida" funcione correctamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager
from utils.app_settings import AppSettings
from utils.logger import Logger

def test_confirm_exit_functionality():
    """Prueba la funcionalidad del switch confirmar salida"""
    print("🧪 Probando funcionalidad del switch 'Confirmar salida'...\n")
    
    # Inicializar configuración
    logger_instance = Logger("logs/test_confirm_exit.log")
    logger = logger_instance.logger
    config_manager = ConfigManager()
    app_settings = AppSettings(config_manager, logger)
    
    # Verificar valor inicial
    initial_value = app_settings.get_setting("confirm_exit")
    print(f"📋 Valor inicial de 'confirm_exit': {initial_value}")
    
    # Simular activación del switch
    print("\n🔄 Simulando activación del switch...")
    app_settings.set_setting("confirm_exit", True)
    app_settings.save_settings()
    
    # Verificar que se guardó
    saved_value = app_settings.get_setting("confirm_exit")
    print(f"💾 Valor después de guardar: {saved_value}")
    
    # Simular reinicio de la aplicación (recargar configuración)
    print("\n🔄 Simulando reinicio de aplicación...")
    new_config_manager = ConfigManager()
    new_app_settings = AppSettings(new_config_manager, logger)
    
    # Verificar persistencia
    persisted_value = new_app_settings.get_setting("confirm_exit")
    print(f"🔄 Valor después del 'reinicio': {persisted_value}")
    
    # Simular desactivación del switch
    print("\n🔄 Simulando desactivación del switch...")
    new_app_settings.set_setting("confirm_exit", False)
    new_app_settings.save_settings()
    
    # Verificar desactivación
    final_value = new_app_settings.get_setting("confirm_exit")
    print(f"❌ Valor después de desactivar: {final_value}")
    
    # Resultados
    print("\n📊 RESULTADOS:")
    print(f"   ✅ Guardado correcto: {saved_value == True}")
    print(f"   ✅ Persistencia correcta: {persisted_value == True}")
    print(f"   ✅ Desactivación correcta: {final_value == False}")
    
    success = (saved_value == True and persisted_value == True and final_value == False)
    print(f"\n🎯 RESULTADO FINAL: {'✅ ÉXITO' if success else '❌ FALLO'}")
    
    if success:
        print("\n🎉 El switch 'Confirmar salida' funciona correctamente!")
        print("   - Se guarda correctamente cuando se activa")
        print("   - Persiste entre reinicios de la aplicación")
        print("   - Se puede desactivar correctamente")
    else:
        print("\n⚠️ Hay problemas con el switch 'Confirmar salida'")
    
    return success

if __name__ == "__main__":
    test_confirm_exit_functionality()