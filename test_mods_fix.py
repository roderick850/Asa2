#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar la corrección del problema de mods en argumentos de salida
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager
from utils.logger import Logger
from gui.panels.principal_panel import PrincipalPanel
import tkinter as tk

def test_mods_arguments():
    """Probar que los argumentos no incluyen mods cuando no están configurados"""
    print("=== Prueba de Corrección de Mods en Argumentos ===")
    
    # Crear instancias necesarias
    config_manager = ConfigManager()
    logger = Logger()
    
    # Crear ventana temporal para el panel
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana
    
    try:
        # Crear panel principal
        panel = PrincipalPanel(root, config_manager, logger)
        
        # Obtener configuración actual
        current_server = config_manager.get("app", "last_server", "")
        current_map = config_manager.get("app", "last_map", "")
        
        print(f"Servidor actual: {current_server}")
        print(f"Mapa actual: {current_map}")
        
        # Verificar configuración de mods para el servidor/mapa actual
        if current_server and current_map:
            server_map_key = f"{current_server}_{current_map}"
            mod_ids_key = f"mod_ids_{server_map_key}"
            mod_ids = config_manager.get("server", mod_ids_key, "").strip()
            
            print(f"Clave de configuración: {mod_ids_key}")
            print(f"Mods configurados: '{mod_ids}'")
            
            # Verificar configuración general (no debería usarse)
            general_mod_ids = config_manager.get("server", "mod_ids", "").strip()
            print(f"Mods configuración general: '{general_mod_ids}'")
            
            # Simular la construcción de argumentos
            panel.selected_server = current_server
            panel.selected_map = current_map
            
            # Construir argumentos
            args = panel.build_server_arguments()
            
            print("\n=== Argumentos Generados ===")
            for i, arg in enumerate(args):
                print(f"{i+1}: {arg}")
            
            # Verificar si hay argumentos de mods
            mods_args = [arg for arg in args if arg.startswith("-mods=")]
            
            print("\n=== Análisis de Resultados ===")
            if mods_args:
                print(f"❌ PROBLEMA: Se encontraron argumentos de mods: {mods_args}")
                print(f"   Esto indica que el fallback sigue activo")
                return False
            else:
                if mod_ids:
                    print(f"✅ CORRECTO: Hay mods configurados ({mod_ids}) y aparecen en argumentos")
                else:
                    print(f"✅ CORRECTO: No hay mods configurados y no aparecen en argumentos")
                return True
        else:
            print("❌ ERROR: No hay servidor o mapa configurado")
            return False
            
    except Exception as e:
        print(f"❌ ERROR durante la prueba: {e}")
        return False
    finally:
        root.destroy()

def test_different_server_configs():
    """Probar diferentes configuraciones de servidor"""
    print("\n=== Prueba de Diferentes Configuraciones ===")
    
    config_manager = ConfigManager()
    
    # Mostrar todas las configuraciones de mods
    print("\nConfiguraciones de mods encontradas:")
    
    # Leer todas las claves de la sección server
    try:
        config = config_manager.config
        if 'server' in config:
            for key, value in config['server'].items():
                if key.startswith('mod_ids'):
                    print(f"  {key} = '{value}'")
    except Exception as e:
        print(f"Error al leer configuraciones: {e}")

if __name__ == "__main__":
    print("Iniciando pruebas de corrección de mods...\n")
    
    # Ejecutar pruebas
    success = test_mods_arguments()
    test_different_server_configs()
    
    print("\n=== Resumen ===")
    if success:
        print("✅ La corrección funciona correctamente")
        print("   Los mods solo aparecen cuando están configurados específicamente")
    else:
        print("❌ La corrección necesita más trabajo")
        print("   Revisar la lógica de fallback")
    
    print("\nPrueba completada.")