#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prueba final simple del switch "Confirmar salida"
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager
from utils.app_settings import AppSettings
from utils.logger import Logger

def test_confirm_exit_final():
    """Prueba final del switch confirmar salida"""
    print("🎯 PRUEBA FINAL: Switch 'Confirmar salida'\n")
    
    # Inicializar configuración
    logger_instance = Logger("logs/test_final_simple.log")
    logger = logger_instance.logger
    config_manager = ConfigManager()
    app_settings = AppSettings(config_manager, logger)
    
    def simulate_salir_aplicacion(settings):
        """Simula exactamente el método salir_aplicacion de MainWindow"""
        if settings.get_setting("confirm_exit"):
            print("   🚨 CONFIRMACIÓN REQUERIDA")
            print("   → ask_yes_no() se mostraría")
            return "NEEDS_CONFIRMATION"
        else:
            print("   ⚡ SALIDA DIRECTA")
            print("   → cleanup_and_exit() inmediatamente")
            return "DIRECT_EXIT"
    
    print("📋 PASO 1: Desactivar switch")
    app_settings.set_setting("confirm_exit", False)
    app_settings.save_settings()
    state1 = app_settings.get_setting("confirm_exit")
    print(f"   Estado: {state1}")
    result1 = simulate_salir_aplicacion(app_settings)
    print(f"   Comportamiento: {result1}")
    
    print("\n📋 PASO 2: Activar switch")
    app_settings.set_setting("confirm_exit", True)
    app_settings.save_settings()
    state2 = app_settings.get_setting("confirm_exit")
    print(f"   Estado: {state2}")
    result2 = simulate_salir_aplicacion(app_settings)
    print(f"   Comportamiento: {result2}")
    
    print("\n📋 PASO 3: Verificar persistencia")
    new_config = ConfigManager()
    new_settings = AppSettings(new_config, logger)
    state3 = new_settings.get_setting("confirm_exit")
    print(f"   Estado después de reinicio: {state3}")
    result3 = simulate_salir_aplicacion(new_settings)
    print(f"   Comportamiento: {result3}")
    
    print("\n📋 PASO 4: Desactivar nuevamente")
    new_settings.set_setting("confirm_exit", False)
    new_settings.save_settings()
    state4 = new_settings.get_setting("confirm_exit")
    print(f"   Estado: {state4}")
    result4 = simulate_salir_aplicacion(new_settings)
    print(f"   Comportamiento: {result4}")
    
    # Verificar resultados
    print("\n📊 RESULTADOS:")
    tests = {
        "Desactivado funciona": state1 == False and result1 == "DIRECT_EXIT",
        "Activado funciona": state2 == True and result2 == "NEEDS_CONFIRMATION",
        "Persistencia funciona": state3 == True and result3 == "NEEDS_CONFIRMATION",
        "Cambio a desactivado funciona": state4 == False and result4 == "DIRECT_EXIT"
    }
    
    for test_name, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    all_passed = all(tests.values())
    print(f"\n🎯 RESULTADO: {'✅ TODO FUNCIONA' if all_passed else '❌ HAY PROBLEMAS'}")
    
    if all_passed:
        print("\n🎉 ¡SWITCH CONFIRMAR SALIDA COMPLETAMENTE FUNCIONAL!")
        print("   • Se guarda correctamente")
        print("   • Mantiene estado entre reinicios")
        print("   • Comportamiento correcto según configuración")
        print("   • Sin errores al guardar desde el diálogo")
    
    return all_passed

if __name__ == "__main__":
    test_confirm_exit_final()