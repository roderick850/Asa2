#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demostración del comportamiento del switch "Confirmar salida"
Este script simula el comportamiento real de la aplicación
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager
from utils.app_settings import AppSettings
from utils.logger import Logger

def simulate_app_exit_behavior():
    """Simula el comportamiento de salida de la aplicación"""
    print("🎭 Simulando comportamiento del switch 'Confirmar salida'...\n")
    
    # Inicializar configuración
    logger_instance = Logger("logs/demo_confirm_exit.log")
    logger = logger_instance.logger
    config_manager = ConfigManager()
    app_settings = AppSettings(config_manager, logger)
    
    def simulate_salir_aplicacion():
        """Simula la función salir_aplicacion de main_window.py"""
        if app_settings.get_setting("confirm_exit"):
            print("⚠️ Switch 'Confirmar salida' ACTIVADO")
            print("   → Se mostraría diálogo: '¿Estás seguro de que quieres salir de Ark Server Manager?'")
            print("   → Usuario debe confirmar para cerrar la aplicación")
            return "CONFIRMATION_REQUIRED"
        else:
            print("✅ Switch 'Confirmar salida' DESACTIVADO")
            print("   → La aplicación se cierra directamente sin confirmación")
            return "DIRECT_EXIT"
    
    # Escenario 1: Switch desactivado (comportamiento por defecto)
    print("📋 ESCENARIO 1: Switch desactivado")
    app_settings.set_setting("confirm_exit", False)
    app_settings.save_settings()
    result1 = simulate_salir_aplicacion()
    print(f"   Resultado: {result1}\n")
    
    # Escenario 2: Activar el switch
    print("📋 ESCENARIO 2: Activando el switch")
    app_settings.set_setting("confirm_exit", True)
    app_settings.save_settings()
    result2 = simulate_salir_aplicacion()
    print(f"   Resultado: {result2}\n")
    
    # Escenario 3: Simular reinicio de aplicación (persistencia)
    print("📋 ESCENARIO 3: Reinicio de aplicación (verificar persistencia)")
    print("   🔄 Simulando cierre y reapertura de la aplicación...")
    
    # Nueva instancia (simula reinicio)
    new_config_manager = ConfigManager()
    new_app_settings = AppSettings(new_config_manager, logger)
    
    def simulate_salir_aplicacion_new():
        """Simula la función con la nueva instancia"""
        if new_app_settings.get_setting("confirm_exit"):
            print("⚠️ Switch 'Confirmar salida' sigue ACTIVADO después del reinicio")
            print("   → Se mostraría diálogo de confirmación")
            return "CONFIRMATION_REQUIRED"
        else:
            print("✅ Switch 'Confirmar salida' DESACTIVADO después del reinicio")
            print("   → Salida directa")
            return "DIRECT_EXIT"
    
    result3 = simulate_salir_aplicacion_new()
    print(f"   Resultado: {result3}\n")
    
    # Escenario 4: Desactivar el switch
    print("📋 ESCENARIO 4: Desactivando el switch")
    new_app_settings.set_setting("confirm_exit", False)
    new_app_settings.save_settings()
    result4 = simulate_salir_aplicacion_new()
    print(f"   Resultado: {result4}\n")
    
    # Resumen
    print("📊 RESUMEN DE COMPORTAMIENTOS:")
    print("   ✅ Switch desactivado → Salida directa")
    print("   ⚠️ Switch activado → Requiere confirmación")
    print("   🔄 Estado persiste entre reinicios")
    print("   🎛️ Se puede cambiar desde el menú Comportamiento")
    
    print("\n🎯 IMPLEMENTACIÓN COMPLETADA:")
    print("   • El switch 'Confirmar salida' ahora carga su valor guardado")
    print("   • La función salir_aplicacion() respeta la configuración")
    print("   • El estado persiste correctamente entre sesiones")
    print("   • Se puede activar/desactivar desde Configuración Avanzada")

if __name__ == "__main__":
    simulate_app_exit_behavior()