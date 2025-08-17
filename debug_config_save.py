#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug del sistema de guardado de configuración
"""

import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager

def debug_config_save():
    """Debug del guardado de configuración"""
    print("🔍 DEBUG DEL SISTEMA DE GUARDADO")
    print("=" * 50)
    
    config_manager = ConfigManager()
    
    print("\n📋 PASO 1: Estado inicial")
    initial_value = config_manager.get("server", "maxplayers_as_arg", "NOT_FOUND")
    print(f"   Valor inicial: {initial_value}")
    
    print("\n📋 PASO 2: Establecer valor True")
    config_manager.set("server", "maxplayers_as_arg", True)
    
    # Verificar antes de guardar
    before_save = config_manager.get("server", "maxplayers_as_arg", "NOT_FOUND")
    print(f"   Valor antes de save(): {before_save}")
    
    # Guardar
    print("   Ejecutando save()...")
    config_manager.save()
    print("   save() completado")
    
    # Verificar después de guardar
    after_save = config_manager.get("server", "maxplayers_as_arg", "NOT_FOUND")
    print(f"   Valor después de save(): {after_save}")
    
    print("\n📋 PASO 3: Verificar archivo config.ini")
    config_file_path = config_manager.config_file
    print(f"   Ruta del archivo: {config_file_path}")
    
    if os.path.exists(config_file_path):
        print("   Contenido de la sección [server]:")
        with open(config_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Buscar la sección [server]
        lines = content.split('\n')
        in_server_section = False
        server_lines = []
        
        for line in lines:
            if line.strip() == '[server]':
                in_server_section = True
                server_lines.append(line)
            elif line.strip().startswith('[') and line.strip() != '[server]':
                in_server_section = False
            elif in_server_section:
                server_lines.append(line)
        
        for line in server_lines:
            if 'maxplayers_as_arg' in line.lower() or line.strip() == '':
                print(f"     {line}")
            elif line.strip():
                print(f"     {line[:50]}{'...' if len(line) > 50 else ''}")
    else:
        print("   ❌ Archivo config.ini no existe")
    
    print("\n📋 PASO 4: Crear nueva instancia y verificar")
    new_config_manager = ConfigManager()
    reloaded_value = new_config_manager.get("server", "maxplayers_as_arg", "NOT_FOUND")
    print(f"   Valor después de recargar: {reloaded_value}")
    
    print("\n📋 PASO 5: Verificar todas las claves en la sección server")
    server_section = config_manager.get_section("server")
    if server_section:
        print("   Claves encontradas en [server]:")
        for key, value in server_section.items():
            if 'maxplayers' in key.lower():
                print(f"     ✅ {key} = {value}")
            else:
                print(f"     {key} = {str(value)[:30]}{'...' if len(str(value)) > 30 else ''}")
    else:
        print("   ❌ No se pudo obtener la sección [server]")
    
    print("\n" + "=" * 50)
    print("🎯 RESUMEN:")
    print(f"   Valor se estableció correctamente: {before_save == True}")
    print(f"   Valor persistió después de save(): {after_save == True}")
    print(f"   Valor se mantiene después de recargar: {reloaded_value == True}")

if __name__ == "__main__":
    try:
        debug_config_save()
    except Exception as e:
        print(f"\n❌ Error durante el debug: {e}")
        import traceback
        traceback.print_exc()