#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la funcionalidad de ocultar/mostrar consola del servidor
Después de las correcciones realizadas.
"""

import sys
import os
import time
import logging
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from utils.config_manager import ConfigManager
from utils.server_manager import ServerManager

def test_console_functionality():
    """Prueba la funcionalidad de ocultar/mostrar consola"""
    print("=== Test de funcionalidad de consola ===")
    
    # Configurar logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        # Inicializar componentes
        config_manager = ConfigManager()
        server_manager = ServerManager(config_manager)
        
        print("✅ Componentes inicializados correctamente")
        
        # Verificar si hay servidor ejecutándose
        is_running = server_manager.is_server_running()
        print(f"📊 Estado del servidor: {'Ejecutándose' if is_running else 'No ejecutándose'}")
        
        if not is_running:
            print("⚠️ No hay servidor ejecutándose. La funcionalidad se aplicará al iniciar el servidor.")
            print("💡 Para probar completamente, inicia un servidor primero.")
            return
        
        # Buscar ventana de consola
        print("🔍 Buscando ventana de consola del servidor...")
        found = server_manager._find_server_console_window()
        
        if not found:
            print("❌ No se pudo encontrar la ventana de consola del servidor")
            return
        
        print(f"✅ Ventana de consola encontrada: HWND={server_manager.server_console_hwnd}")
        
        # Probar ocultar consola
        print("\n🙈 Probando ocultar consola...")
        hide_result = server_manager.hide_server_console()
        print(f"Resultado: {'✅ Éxito' if hide_result else '❌ Falló'}")
        
        if hide_result:
            time.sleep(2)
            
            # Probar mostrar consola
            print("\n👁️ Probando mostrar consola...")
            show_result = server_manager.show_server_console()
            print(f"Resultado: {'✅ Éxito' if show_result else '❌ Falló'}")
        
        print("\n=== Test completado ===")
        
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()

def test_imports():
    """Verifica que todas las importaciones necesarias funcionen"""
    print("=== Test de importaciones ===")
    
    try:
        import ctypes
        print("✅ ctypes importado correctamente")
        
        from ctypes import wintypes
        print("✅ ctypes.wintypes importado correctamente")
        
        # Probar acceso a APIs de Windows
        user32 = ctypes.windll.user32
        print("✅ user32 accesible")
        
        kernel32 = ctypes.windll.kernel32
        print("✅ kernel32 accesible")
        
        # Probar constantes
        SW_HIDE = 0
        SW_SHOW = 5
        print("✅ Constantes definidas")
        
        print("✅ Todas las importaciones funcionan correctamente")
        
    except Exception as e:
        print(f"❌ Error en importaciones: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Iniciando tests de funcionalidad de consola...\n")
    
    # Test de importaciones
    test_imports()
    print()
    
    # Test de funcionalidad
    test_console_functionality()
    
    print("\n🏁 Tests completados")