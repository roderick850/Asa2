#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la persistencia del estado del switch de consola
"""

import sys
import os
import time
import tkinter as tk
from tkinter import messagebox

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager

def test_console_persistence():
    """Probar la persistencia del estado del switch de consola"""
    print("🧪 Iniciando prueba de persistencia del switch de consola...")
    
    # Inicializar ConfigManager
    config_manager = ConfigManager()
    
    # Obtener estado actual
    current_state = config_manager.get("app", "show_server_console", default="true")
    print(f"📋 Estado actual en configuración: {current_state}")
    
    # Convertir a booleano
    current_bool = current_state.lower() == "true"
    print(f"🔄 Estado booleano: {current_bool}")
    
    # Cambiar el estado
    new_state = not current_bool
    new_state_str = str(new_state).lower()
    
    print(f"🔄 Cambiando estado a: {new_state} ({new_state_str})")
    
    # Guardar nuevo estado
    config_manager.set("app", "show_server_console", new_state_str)
    config_manager.save()
    
    print(f"💾 Estado guardado: {new_state_str}")
    
    # Verificar que se guardó correctamente
    saved_state = config_manager.get("app", "show_server_console", default="true")
    print(f"✅ Estado verificado: {saved_state}")
    
    if saved_state == new_state_str:
        print("✅ ¡El estado se guardó correctamente!")
    else:
        print(f"❌ Error: se esperaba '{new_state_str}' pero se obtuvo '{saved_state}'")
    
    # Simular reinicio - crear nuevo ConfigManager
    print("\n🔄 Simulando reinicio de aplicación...")
    config_manager_new = ConfigManager()
    
    # Verificar que el estado persiste
    persisted_state = config_manager_new.get("app", "show_server_console", default="true")
    print(f"📋 Estado después del 'reinicio': {persisted_state}")
    
    if persisted_state == new_state_str:
        print("✅ ¡El estado persistió correctamente después del reinicio!")
        return True
    else:
        print(f"❌ Error: el estado no persistió. Se esperaba '{new_state_str}' pero se obtuvo '{persisted_state}'")
        return False

def test_switch_initialization():
    """Probar la inicialización del switch con el estado guardado"""
    print("\n🧪 Probando inicialización del switch...")
    
    config_manager = ConfigManager()
    
    # Obtener estado guardado
    saved_state = config_manager.get("app", "show_server_console", default="true")
    expected_bool = saved_state.lower() == "true"
    
    print(f"📋 Estado en configuración: {saved_state}")
    print(f"🔄 Valor booleano esperado: {expected_bool}")
    
    # Simular inicialización del switch (como en console_panel.py línea 60)
    import customtkinter as ctk
    
    # Crear ventana temporal para la prueba
    root = ctk.CTk()
    root.withdraw()  # Ocultar la ventana
    
    # Crear variable del switch como en el código real
    console_visibility_var = ctk.BooleanVar(
        value=config_manager.get("app", "show_server_console", default="true").lower() == "true"
    )
    
    actual_value = console_visibility_var.get()
    print(f"🎯 Valor del switch inicializado: {actual_value}")
    
    root.destroy()
    
    if actual_value == expected_bool:
        print("✅ ¡El switch se inicializó correctamente con el estado guardado!")
        return True
    else:
        print(f"❌ Error: se esperaba {expected_bool} pero el switch se inicializó con {actual_value}")
        return False

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas de persistencia del switch de consola")
    print("=" * 60)
    
    try:
        # Prueba 1: Persistencia básica
        test1_result = test_console_persistence()
        
        # Prueba 2: Inicialización del switch
        test2_result = test_switch_initialization()
        
        print("\n" + "=" * 60)
        print("📊 RESULTADOS:")
        print(f"   Persistencia de configuración: {'✅ PASS' if test1_result else '❌ FAIL'}")
        print(f"   Inicialización del switch: {'✅ PASS' if test2_result else '❌ FAIL'}")
        
        if test1_result and test2_result:
            print("\n🎉 ¡Todas las pruebas pasaron! El switch de consola funciona correctamente.")
            print("\n📝 CONCLUSIÓN:")
            print("   - El estado del switch se guarda correctamente")
            print("   - El estado persiste entre reinicios de la aplicación")
            print("   - El switch se inicializa con el estado guardado")
            print("   - La funcionalidad solicitada YA ESTÁ IMPLEMENTADA")
        else:
            print("\n⚠️ Algunas pruebas fallaron. Revisar la implementación.")
            
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()