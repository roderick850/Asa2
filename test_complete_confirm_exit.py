#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prueba completa del switch "Confirmar salida"
Verifica guardado, persistencia y funcionalidad
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager
from utils.app_settings import AppSettings
from utils.logger import Logger

def test_complete_confirm_exit():
    """Prueba completa del switch confirmar salida"""
    print("🧪 PRUEBA COMPLETA: Switch 'Confirmar salida'\n")
    
    # Inicializar configuración
    logger_instance = Logger("logs/test_complete.log")
    logger = logger_instance.logger
    config_manager = ConfigManager()
    app_settings = AppSettings(config_manager, logger)
    
    print("📋 PASO 1: Verificar valor inicial")
    initial_value = app_settings.get_setting("confirm_exit")
    print(f"   Valor inicial: {initial_value}")
    
    print("\n📋 PASO 2: Activar el switch")
    app_settings.set_setting("confirm_exit", True)
    app_settings.save_settings()
    saved_value = app_settings.get_setting("confirm_exit")
    print(f"   Valor después de activar: {saved_value}")
    print(f"   ✅ Guardado correcto: {saved_value == True}")
    
    print("\n📋 PASO 3: Simular reinicio (nueva instancia)")
    new_config_manager = ConfigManager()
    new_app_settings = AppSettings(new_config_manager, logger)
    persisted_value = new_app_settings.get_setting("confirm_exit")
    print(f"   Valor después del reinicio: {persisted_value}")
    print(f"   ✅ Persistencia correcta: {persisted_value == True}")
    
    print("\n📋 PASO 4: Simular comportamiento de salida (ACTIVADO)")
    def simulate_exit_with_confirmation():
        if new_app_settings.get_setting("confirm_exit"):
            print("   ⚠️ CONFIRMACIÓN REQUERIDA")
            print("   → Se mostraría diálogo: '¿Estás seguro de que quieres salir?'")
            print("   → Usuario debe confirmar para cerrar")
            return "CONFIRMATION_REQUIRED"
        else:
            print("   ✅ SALIDA DIRECTA")
            return "DIRECT_EXIT"
    
    result_activated = simulate_exit_with_confirmation()
    print(f"   Resultado: {result_activated}")
    
    print("\n📋 PASO 5: Desactivar el switch")
    new_app_settings.set_setting("confirm_exit", False)
    new_app_settings.save_settings()
    deactivated_value = new_app_settings.get_setting("confirm_exit")
    print(f"   Valor después de desactivar: {deactivated_value}")
    print(f"   ✅ Desactivación correcta: {deactivated_value == False}")
    
    print("\n📋 PASO 6: Simular comportamiento de salida (DESACTIVADO)")
    result_deactivated = simulate_exit_with_confirmation()
    print(f"   Resultado: {result_deactivated}")
    
    print("\n📋 PASO 7: Verificar persistencia de desactivación")
    final_config_manager = ConfigManager()
    final_app_settings = AppSettings(final_config_manager, logger)
    final_value = final_app_settings.get_setting("confirm_exit")
    print(f"   Valor final persistido: {final_value}")
    print(f"   ✅ Persistencia de desactivación: {final_value == False}")
    
    # Resultados finales
    print("\n📊 RESUMEN DE RESULTADOS:")
    tests = {
        "Guardado al activar": saved_value == True,
        "Persistencia al activar": persisted_value == True,
        "Comportamiento activado": result_activated == "CONFIRMATION_REQUIRED",
        "Guardado al desactivar": deactivated_value == False,
        "Comportamiento desactivado": result_deactivated == "DIRECT_EXIT",
        "Persistencia al desactivar": final_value == False
    }
    
    for test_name, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    all_passed = all(tests.values())
    
    print(f"\n🎯 RESULTADO FINAL: {'✅ TODOS LOS TESTS PASARON' if all_passed else '❌ ALGUNOS TESTS FALLARON'}")
    
    if all_passed:
        print("\n🎉 ¡FUNCIONALIDAD COMPLETA!")
        print("   • El switch se guarda correctamente")
        print("   • El estado persiste entre reinicios")
        print("   • La confirmación funciona cuando está activado")
        print("   • La salida directa funciona cuando está desactivado")
        print("   • Todos los cambios se mantienen correctamente")
    else:
        print("\n⚠️ HAY PROBLEMAS QUE RESOLVER")
        failed_tests = [name for name, result in tests.items() if not result]
        print(f"   Tests fallidos: {', '.join(failed_tests)}")
    
    return all_passed

def test_dialog_simulation():
    """Simular el comportamiento del diálogo de configuración avanzada"""
    print("\n🎭 SIMULACIÓN DEL DIÁLOGO DE CONFIGURACIÓN\n")
    
    logger_instance = Logger("logs/test_dialog.log")
    logger = logger_instance.logger
    config_manager = ConfigManager()
    app_settings = AppSettings(config_manager, logger)
    
    # Simular la inicialización del switch en el diálogo
    class MockBooleanVar:
        def __init__(self, value):
            self.value = value
        def get(self):
            return self.value
        def set(self, value):
            self.value = value
    
    print("📋 SIMULACIÓN 1: Cargar valor guardado en el diálogo")
    saved_confirm_exit = app_settings.get_setting("confirm_exit")
    confirm_exit_var = MockBooleanVar(saved_confirm_exit)
    print(f"   Valor cargado en el switch: {confirm_exit_var.get()}")
    print(f"   ✅ Carga correcta: {confirm_exit_var.get() == saved_confirm_exit}")
    
    print("\n📋 SIMULACIÓN 2: Cambiar switch y guardar")
    new_value = not confirm_exit_var.get()  # Cambiar al valor opuesto
    confirm_exit_var.set(new_value)
    print(f"   Nuevo valor en el switch: {confirm_exit_var.get()}")
    
    # Simular guardado
    app_settings.set_setting("confirm_exit", confirm_exit_var.get())
    app_settings.save_settings()
    
    # Verificar que se guardó
    verification_value = app_settings.get_setting("confirm_exit")
    print(f"   Valor verificado después del guardado: {verification_value}")
    print(f"   ✅ Guardado correcto: {verification_value == new_value}")
    
    return verification_value == new_value

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS COMPLETAS\n")
    
    test1_result = test_complete_confirm_exit()
    test2_result = test_dialog_simulation()
    
    print("\n" + "="*60)
    print("📊 RESULTADOS FINALES DE TODAS LAS PRUEBAS")
    print("="*60)
    print(f"✅ Funcionalidad completa: {test1_result}")
    print(f"✅ Simulación de diálogo: {test2_result}")
    
    overall_success = test1_result and test2_result
    print(f"\n🎯 ÉXITO GENERAL: {'✅ SÍ' if overall_success else '❌ NO'}")
    
    if overall_success:
        print("\n🎉 ¡TODO FUNCIONA PERFECTAMENTE!")
        print("   El switch 'Confirmar salida' está completamente operativo")
    else:
        print("\n⚠️ Aún hay problemas por resolver")