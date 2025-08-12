#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de depuración para analizar el problema del switch de consola
"""

import os
import sys
import ctypes
from ctypes import wintypes
import psutil
import logging

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager
from utils.server_manager import ServerManager

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_console_switch.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def analyze_config():
    """Analizar la configuración actual"""
    logger.info("=== ANÁLISIS DE CONFIGURACIÓN ===")
    
    try:
        config_manager = ConfigManager()
        
        # Verificar archivo de configuración
        config_file = config_manager.config_file
        logger.info(f"Archivo de configuración: {config_file}")
        logger.info(f"Archivo existe: {os.path.exists(config_file)}")
        
        if os.path.exists(config_file):
            logger.info(f"Tamaño del archivo: {os.path.getsize(config_file)} bytes")
            
            # Leer contenido del archivo
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.info(f"Contenido del archivo:\n{content}")
        
        # Verificar configuración específica
        show_console = config_manager.get("app", "show_server_console", default="true")
        logger.info(f"show_server_console: {show_console} (tipo: {type(show_console)})")
        
        # Verificar otras configuraciones relacionadas
        sections = config_manager.config.sections()
        logger.info(f"Secciones disponibles: {sections}")
        
        for section in sections:
            items = dict(config_manager.config.items(section))
            logger.info(f"Sección [{section}]: {items}")
            
    except Exception as e:
        logger.error(f"Error analizando configuración: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def find_ark_processes():
    """Buscar procesos de ARK"""
    logger.info("=== BÚSQUEDA DE PROCESOS ARK ===")
    
    ark_processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                name = proc.info['name']
                if name and ('ark' in name.lower() or 'shootergame' in name.lower() or 'asa' in name.lower()):
                    ark_processes.append({
                        'pid': proc.info['pid'],
                        'name': name,
                        'cmdline': proc.info['cmdline']
                    })
                    logger.info(f"Proceso ARK encontrado: PID={proc.info['pid']}, Nombre={name}")
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
    except Exception as e:
        logger.error(f"Error buscando procesos: {e}")
    
    logger.info(f"Total procesos ARK encontrados: {len(ark_processes)}")
    return ark_processes

def analyze_windows(ark_processes):
    """Analizar ventanas del sistema"""
    logger.info("=== ANÁLISIS DE VENTANAS ===")
    
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        ark_windows = []
        all_windows = []
        
        def enum_windows_callback(hwnd, lparam):
            try:
                # Obtener información de la ventana
                window_text = ctypes.create_unicode_buffer(256)
                user32.GetWindowTextW(hwnd, window_text, 256)
                
                class_name = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, class_name, 256)
                
                # Obtener PID del proceso
                process_id = ctypes.c_ulong()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
                
                # Verificar si es visible
                is_visible = user32.IsWindowVisible(hwnd)
                
                window_info = {
                    'hwnd': hwnd,
                    'title': window_text.value,
                    'class_name': class_name.value,
                    'pid': process_id.value,
                    'is_visible': bool(is_visible)
                }
                
                all_windows.append(window_info)
                
                # Verificar si pertenece a un proceso ARK
                for ark_proc in ark_processes:
                    if process_id.value == ark_proc['pid']:
                        ark_windows.append(window_info)
                        logger.info(f"Ventana ARK: HWND={hwnd}, Título='{window_text.value}', Clase='{class_name.value}', Visible={is_visible}")
                        break
                
                # Buscar ventanas que podrían ser consolas
                title_lower = window_text.value.lower()
                class_lower = class_name.value.lower()
                
                if (any(keyword in title_lower for keyword in ['ark', 'shootergame', 'asa', 'ascended', 'server', 'console']) or
                    any(keyword in class_lower for keyword in ['consolewindowclass', 'cmd'])):
                    logger.info(f"Posible consola: HWND={hwnd}, Título='{window_text.value}', Clase='{class_name.value}', PID={process_id.value}, Visible={is_visible}")
                
            except Exception as e:
                logger.debug(f"Error procesando ventana {hwnd}: {e}")
            
            return True
        
        # Enumerar todas las ventanas
        user32.EnumWindows(
            ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(enum_windows_callback),
            0
        )
        
        logger.info(f"Total ventanas encontradas: {len(all_windows)}")
        logger.info(f"Ventanas ARK encontradas: {len(ark_windows)}")
        
        # Mostrar ventanas visibles con títulos relevantes
        relevant_windows = [w for w in all_windows if w['is_visible'] and w['title'] and 
                          any(keyword in w['title'].lower() for keyword in ['ark', 'shootergame', 'asa', 'console', 'cmd'])]
        
        logger.info(f"Ventanas relevantes visibles: {len(relevant_windows)}")
        for window in relevant_windows:
            logger.info(f"  - HWND={window['hwnd']}, Título='{window['title']}', PID={window['pid']}")
        
        return ark_windows
        
    except Exception as e:
        logger.error(f"Error analizando ventanas: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []

def test_server_manager():
    """Probar funcionalidad del ServerManager"""
    logger.info("=== PRUEBA DE SERVER MANAGER ===")
    
    try:
        config_manager = ConfigManager()
        server_manager = ServerManager(config_manager)
        
        # Verificar si hay servidor activo
        is_running = server_manager.is_server_running()
        logger.info(f"Servidor ejecutándose: {is_running}")
        
        if is_running:
            server_pid = server_manager.get_server_pid()
            logger.info(f"PID del servidor: {server_pid}")
        
        # Probar búsqueda de ventana de consola
        logger.info("Probando _find_server_console_window...")
        console_hwnd = server_manager._find_server_console_window()
        logger.info(f"HWND de consola encontrado: {console_hwnd}")
        
        if console_hwnd:
            # Verificar si la ventana es válida
            user32 = ctypes.windll.user32
            is_valid = user32.IsWindow(console_hwnd)
            is_visible = user32.IsWindowVisible(console_hwnd)
            
            logger.info(f"Ventana válida: {is_valid}")
            logger.info(f"Ventana visible: {is_visible}")
            
            # Obtener título de la ventana
            window_text = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(console_hwnd, window_text, 256)
            logger.info(f"Título de la ventana: '{window_text.value}'")
        
        # Probar funciones show/hide
        logger.info("Probando show_server_console...")
        try:
            result = server_manager.show_server_console()
            logger.info(f"Resultado show_server_console: {result}")
        except Exception as e:
            logger.error(f"Error en show_server_console: {e}")
        
        logger.info("Probando hide_server_console...")
        try:
            result = server_manager.hide_server_console()
            logger.info(f"Resultado hide_server_console: {result}")
        except Exception as e:
            logger.error(f"Error en hide_server_console: {e}")
            
    except Exception as e:
        logger.error(f"Error probando ServerManager: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def main():
    """Función principal de depuración"""
    logger.info("🔍 INICIANDO DEPURACIÓN DEL SWITCH DE CONSOLA")
    logger.info("=" * 60)
    
    # 1. Analizar configuración
    analyze_config()
    
    # 2. Buscar procesos ARK
    ark_processes = find_ark_processes()
    
    # 3. Analizar ventanas
    ark_windows = analyze_windows(ark_processes)
    
    # 4. Probar ServerManager
    test_server_manager()
    
    logger.info("=" * 60)
    logger.info("✅ DEPURACIÓN COMPLETADA")
    logger.info(f"📋 Log guardado en: debug_console_switch.log")
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE DEPURACIÓN")
    print("=" * 60)
    print(f"🔧 Procesos ARK encontrados: {len(ark_processes)}")
    print(f"🪟 Ventanas ARK encontradas: {len(ark_windows) if 'ark_windows' in locals() else 0}")
    print(f"📁 Log detallado: debug_console_switch.log")
    print("=" * 60)

if __name__ == "__main__":
    main()