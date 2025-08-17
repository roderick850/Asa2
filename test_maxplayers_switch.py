#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para verificar el funcionamiento del switch de MaxPlayers
"""

import sys
import os
import time

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager

def convert_string_to_bool(value):
    """Convertir string a boolean como lo hace la aplicación real"""
    if isinstance(value, str):
        return value.lower() == 'true'
    return value

def test_maxplayers_switch():
    """Probar el guardado automático del switch de MaxPlayers"""
    print("🧪 INICIANDO TEST DEL SWITCH MAXPLAYERS (SIMULANDO APLICACIÓN REAL)")
    print("=" * 70)
    
    # Inicializar componentes
    config_manager = ConfigManager()
    
    print("\n📋 PASO 1: Verificar estado inicial")
    initial_state_raw = config_manager.get("server", "maxplayers_as_arg", False)
    initial_state = convert_string_to_bool(initial_state_raw)
    print(f"   Estado inicial (raw): {initial_state_raw} (tipo: {type(initial_state_raw)})")
    print(f"   Estado inicial (convertido): {initial_state} (tipo: {type(initial_state)})")
    
    print("\n📋 PASO 2: Simular cambio a True (como lo hace el callback)")
    # Simular el callback on_maxplayers_switch_change
    config_manager.set("server", "maxplayers_as_arg", True)
    config_manager.save()
    
    # Verificar que se guardó (como lo hace la aplicación al cargar)
    saved_state_raw = config_manager.get("server", "maxplayers_as_arg", False)
    saved_state = convert_string_to_bool(saved_state_raw)
    print(f"   Estado después de cambiar a True (raw): {saved_state_raw} (tipo: {type(saved_state_raw)})")
    print(f"   Estado después de cambiar a True (convertido): {saved_state} (tipo: {type(saved_state)})")
    
    print("\n📋 PASO 3: Simular cambio a False (como lo hace el callback)")
    config_manager.set("server", "maxplayers_as_arg", False)
    config_manager.save()
    
    # Verificar que se guardó
    final_state_raw = config_manager.get("server", "maxplayers_as_arg", False)
    final_state = convert_string_to_bool(final_state_raw)
    print(f"   Estado después de cambiar a False (raw): {final_state_raw} (tipo: {type(final_state_raw)})")
    print(f"   Estado después de cambiar a False (convertido): {final_state} (tipo: {type(final_state)})")
    
    print("\n📋 PASO 4: Verificar persistencia (simulando reinicio de aplicación)")
    # Crear un nuevo config_manager para simular reinicio
    new_config_manager = ConfigManager()
    persistent_state_raw = new_config_manager.get("server", "maxplayers_as_arg", None)
    persistent_state = convert_string_to_bool(persistent_state_raw) if persistent_state_raw is not None else None
    print(f"   Estado después de 'reinicio' (raw): {persistent_state_raw} (tipo: {type(persistent_state_raw)})")
    print(f"   Estado después de 'reinicio' (convertido): {persistent_state} (tipo: {type(persistent_state)})")
    
    print("\n📋 PASO 5: Test completo - Simular flujo real de la aplicación")
    # Simular el flujo completo: cambiar a True, reiniciar, verificar
    print("   5.1 - Establecer True y guardar")
    config_manager.set("server", "maxplayers_as_arg", True)
    config_manager.save()
    
    print("   5.2 - Simular reinicio y cargar configuración")
    restart_config_manager = ConfigManager()
    loaded_value_raw = restart_config_manager.get("server", "maxplayers_as_arg", False)
    loaded_value = convert_string_to_bool(loaded_value_raw)
    
    print(f"   Valor cargado después de reinicio (raw): {loaded_value_raw}")
    print(f"   Valor cargado después de reinicio (convertido): {loaded_value}")
    
    # Resultados
    print("\n" + "=" * 70)
    print("📊 RESULTADOS DEL TEST:")
    
    results = {
        "cambio_a_true": saved_state == True,
        "cambio_a_false": final_state == False,
        "persistencia": persistent_state == False,  # El último valor guardado fue False
        "flujo_completo": loaded_value == True  # El test final guardó True
    }
    
    for test_name, passed in results.items():
        status = "✅ PASÓ" if passed else "❌ FALLÓ"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    print("\n" + "=" * 70)
    if all(results.values()):
        print("🎯 RESULTADO GENERAL: ✅ TODOS LOS TESTS PASARON")
        print("\n✨ El switch de MaxPlayers funciona correctamente:")
        print("   - Se guarda automáticamente cuando cambia")
        print("   - Se convierte correctamente de string a boolean")
        print("   - Persiste después de reiniciar la aplicación")
    else:
        print("🎯 RESULTADO GENERAL: ❌ ALGUNOS TESTS FALLARON")
        print("\n⚠️ Hay problemas con el switch de MaxPlayers:")
        if not results["cambio_a_true"]:
            print("   - Cambio a True no funciona correctamente")
        if not results["cambio_a_false"]:
            print("   - Cambio a False no funciona correctamente")
        if not results["persistencia"]:
            print("   - Persistencia no funciona correctamente")
        if not results["flujo_completo"]:
            print("   - El flujo completo no funciona correctamente")

if __name__ == "__main__":
    try:
        test_maxplayers_switch()
    except Exception as e:
        print(f"\n❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()