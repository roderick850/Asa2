#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import time
import json
import os
from pathlib import Path

def check_console_threads():
    """Verificar hilos de monitoreo de consola activos"""
    print("=== DIAGNÓSTICO DE HILOS DE MONITOREO DE CONSOLA ===")
    print(f"Hilos activos totales: {threading.active_count()}")
    print("\nHilos activos:")
    
    for thread in threading.enumerate():
        print(f"  - {thread.name}: {thread.is_alive()} (daemon: {thread.daemon})")
        if 'monitor' in thread.name.lower() or 'log' in thread.name.lower():
            print(f"    *** HILO DE MONITOREO DETECTADO ***")
    
    print("\n=== VERIFICACIÓN DE ARCHIVOS DE LOG ===")
    
    # Leer configuración del cluster
    cluster_config_path = "data/cluster_config.json"
    if os.path.exists(cluster_config_path):
        with open(cluster_config_path, 'r', encoding='utf-8') as f:
            cluster_config = json.load(f)
        
        root_path = "D:/ASA"  # Desde config.ini
        
        for server_name, server_config in cluster_config.get('servers', {}).items():
            print(f"\n--- Servidor: {server_name} ---")
            
            # Construir ruta del log
            log_path = Path(root_path) / server_name / "ShooterGame" / "Saved" / "Logs" / "ShooterGame.log"
            print(f"Ruta del log: {log_path}")
            
            if log_path.exists():
                stat = log_path.stat()
                print(f"✅ Archivo existe")
                print(f"   Tamaño: {stat.st_size} bytes")
                print(f"   Modificado: {time.ctime(stat.st_mtime)}")
                
                # Leer últimas líneas
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        if lines:
                            print(f"   Total líneas: {len(lines)}")
                            print(f"   Última línea: {lines[-1].strip()[:100]}...")
                        else:
                            print(f"   ⚠️ Archivo vacío")
                except Exception as e:
                    print(f"   ❌ Error leyendo archivo: {e}")
            else:
                print(f"❌ Archivo no existe")
    else:
        print(f"❌ No se encontró {cluster_config_path}")

if __name__ == "__main__":
    check_console_threads()
    
    print("\n=== MONITOREO EN TIEMPO REAL (10 segundos) ===")
    for i in range(10):
        time.sleep(1)
        active_threads = [t.name for t in threading.enumerate() if 'monitor' in t.name.lower()]
        if active_threads:
            print(f"Segundo {i+1}: Hilos de monitoreo activos: {active_threads}")
        else:
            print(f"Segundo {i+1}: No hay hilos de monitoreo activos")
    
    print("\n=== DIAGNÓSTICO COMPLETADO ===")