#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico mejorado para el switch de consola del servidor
"""

import os
import sys
import ctypes
from ctypes import wintypes
import psutil
import time
import logging

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager
from utils.server_manager import ServerManager

# Configurar logging para ver mensajes de debug
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_console_switch():
    """Probar el funcionamiento del switch de consola"""
    print("=== DIAGNÓSTICO DEL SWITCH DE CONSOLA ===")
    print()
    
    # Inicializar managers
    config_manager = ConfigManager()
    server_manager = ServerManager(config_manager)
    
    print("1. Verificando si hay servidor ejecutándose...")
    
    # Buscar procesos del servidor
    server_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'ArkAscendedServer.exe' in proc.info['name']:
                server_processes.append(proc)
                print(f"   ✅ Proceso encontrado: PID {proc.info['pid']}, Nombre: {proc.info['name']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if not server_processes:
        print("   ❌ No se encontró ningún proceso del servidor ejecutándose")
        print("   💡 Inicia el servidor primero para probar el switch")
        return
    
    # Usar el primer proceso encontrado
    server_proc = server_processes[0]
    server_manager.server_pid = server_proc.info['pid']
    
    # Simular que tenemos un proceso del servidor
    class MockProcess:
        def __init__(self, pid):
            self.pid = pid
        def poll(self):
            return None if psutil.pid_exists(self.pid) else 1
    
    server_manager.server_process = MockProcess(server_proc.info['pid'])
    
    print(f"   ✅ Usando proceso con PID: {server_proc.info['pid']}")
    print()
    
    print("2. Buscando ventana de consola del servidor...")
    
    # Probar búsqueda de ventana
    found = server_manager._find_server_console_window()
    
    if found:
        print(f"   ✅ Ventana de consola encontrada: HWND = {server_manager.server_console_hwnd}")
        
        # Obtener información de la ventana
        try:
            window_text = ctypes.create_unicode_buffer(256)
            server_manager.user32.GetWindowTextW(server_manager.server_console_hwnd, window_text, 256)
            print(f"   📝 Título de la ventana: '{window_text.value}'")
            
            # Verificar si la ventana está visible
            is_visible = ctypes.windll.user32.IsWindowVisible(server_manager.server_console_hwnd)
            print(f"   👁️ Ventana visible: {'Sí' if is_visible else 'No'}")
            
        except Exception as e:
            print(f"   ⚠️ Error obteniendo información de ventana: {e}")
    else:
        print("   ❌ No se pudo encontrar la ventana de consola")
        print("   🔍 Listando todas las ventanas del proceso...")
        
        # Listar todas las ventanas del proceso para debug
        def enum_windows_callback(hwnd, lparam):
            try:
                window_pid = ctypes.c_ulong()
                server_manager.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
                
                if window_pid.value == server_proc.info['pid']:
                    window_text = ctypes.create_unicode_buffer(256)
                    server_manager.user32.GetWindowTextW(hwnd, window_text, 256)
                    
                    class_name = ctypes.create_unicode_buffer(256)
                    server_manager.user32.GetClassNameW(hwnd, class_name, 256)
                    
                    is_visible = ctypes.windll.user32.IsWindowVisible(hwnd)
                    
                    print(f"     - HWND: {hwnd}, Título: '{window_text.value}', Clase: '{class_name.value}', Visible: {is_visible}")
            except Exception as e:
                pass
            return True
        
        server_manager.user32.EnumWindows(
            ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(enum_windows_callback), 
            0
        )
        return
    
    print()
    print("3. Probando funciones de mostrar/ocultar...")
    
    # Probar ocultar
    print("   🙈 Probando ocultar consola...")
    result = server_manager.hide_server_console()
    if result:
        print("   ✅ Función hide_server_console() devolvió True")
        time.sleep(2)
        
        # Verificar si realmente se ocultó
        is_visible = ctypes.windll.user32.IsWindowVisible(server_manager.server_console_hwnd)
        print(f"   👁️ Ventana visible después de ocultar: {'Sí' if is_visible else 'No'}")
    else:
        print("   ❌ Función hide_server_console() devolvió False")
    
    print()
    
    # Probar mostrar
    print("   👁️ Probando mostrar consola...")
    result = server_manager.show_server_console()
    if result:
        print("   ✅ Función show_server_console() devolvió True")
        time.sleep(2)
        
        # Verificar si realmente se mostró
        is_visible = ctypes.windll.user32.IsWindowVisible(server_manager.server_console_hwnd)
        print(f"   👁️ Ventana visible después de mostrar: {'Sí' if is_visible else 'No'}")
    else:
        print("   ❌ Función show_server_console() devolvió False")
    
    print()
    print("4. Verificando configuración...")
    
    # Verificar configuración actual
    show_console_config = config_manager.get("app", "show_server_console", default="true")
    print(f"   ⚙️ Configuración show_server_console: '{show_console_config}'")
    
    print()
    print("=== FIN DEL DIAGNÓSTICO ===")
    print()
    print("💡 POSIBLES SOLUCIONES:")
    print("   - Si no se encuentra la ventana: Las palabras clave de búsqueda pueden no coincidir")
    print("   - Si las funciones devuelven False: Problema con las APIs de Windows")
    print("   - Si la ventana no cambia de visibilidad: El proceso puede tener restricciones")
    print("   - Verifica que el servidor se esté ejecutando con permisos adecuados")

if __name__ == "__main__":
    test_console_switch()