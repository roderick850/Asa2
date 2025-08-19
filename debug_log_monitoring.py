#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para verificar el monitoreo de logs
"""

import os
import json
from datetime import datetime

def check_log_files():
    """Verificar si existen los archivos de log de los servidores"""
    print("=== DIAGNÓSTICO DE ARCHIVOS DE LOG ===")
    print(f"Fecha: {datetime.now()}")
    print()
    
    # Root path desde config.ini
    root_path = "D:/ASA"
    print(f"📁 Root path: {root_path}")
    print()
    
    # Verificar cluster config
    cluster_config_path = "data/cluster_config.json"
    if not os.path.exists(cluster_config_path):
        print(f"❌ No se encontró el archivo de configuración del cluster: {cluster_config_path}")
        return
    
    with open(cluster_config_path, 'r', encoding='utf-8') as f:
        cluster_config = json.load(f)
    
    servers = cluster_config.get('servers', {})
    print(f"🌐 Servidores encontrados en cluster_config: {len(servers)}")
    
    for server_name, server_info in servers.items():
        print(f"\n--- Servidor: {server_name} ---")
        print(f"Mapa: {server_info.get('map', 'Unknown')}")
        
        # Construir ruta de logs
        logs_dir = os.path.join(root_path, server_name, "ShooterGame", "Saved", "Logs")
        print(f"📂 Directorio de logs: {logs_dir}")
        
        if os.path.exists(logs_dir):
            print("✅ Directorio de logs existe")
            
            # Listar archivos de log
            log_files = []
            try:
                for file in os.listdir(logs_dir):
                    if file.startswith("ShooterGame") and file.endswith(".log") and not file.endswith("backup"):
                        file_path = os.path.join(logs_dir, file)
                        file_size = os.path.getsize(file_path)
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        log_files.append((file, file_size, file_mtime))
                
                if log_files:
                    print(f"📄 Archivos de log encontrados: {len(log_files)}")
                    # Ordenar por fecha de modificación
                    log_files.sort(key=lambda x: x[2], reverse=True)
                    
                    for i, (filename, size, mtime) in enumerate(log_files[:3]):  # Mostrar solo los 3 más recientes
                        status = "🟢 MÁS RECIENTE" if i == 0 else "🟡 ANTERIOR"
                        print(f"  {status} {filename}")
                        print(f"    Tamaño: {size:,} bytes")
                        print(f"    Modificado: {mtime}")
                        
                        # Verificar si el archivo se puede leer
                        file_path = os.path.join(logs_dir, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                f.seek(0, 2)  # Ir al final
                                file_end_pos = f.tell()
                                if file_end_pos > 100:
                                    f.seek(file_end_pos - 100)  # Leer últimos 100 caracteres
                                    last_content = f.read().strip()
                                    if last_content:
                                        print(f"    ✅ Archivo legible - Últimos caracteres: ...{last_content[-50:]}")
                                    else:
                                        print(f"    ⚠️ Archivo vacío o solo espacios")
                                else:
                                    print(f"    ⚠️ Archivo muy pequeño ({file_end_pos} bytes)")
                        except Exception as e:
                            print(f"    ❌ Error leyendo archivo: {e}")
                else:
                    print("❌ No se encontraron archivos de log ShooterGame*.log")
                    # Mostrar todos los archivos en el directorio
                    all_files = os.listdir(logs_dir)
                    print(f"📋 Archivos en el directorio ({len(all_files)}):")
                    for file in all_files[:10]:  # Mostrar solo los primeros 10
                        print(f"  - {file}")
                    if len(all_files) > 10:
                        print(f"  ... y {len(all_files) - 10} más")
                        
            except Exception as e:
                print(f"❌ Error listando archivos: {e}")
        else:
            print("❌ Directorio de logs NO existe")
            
            # Verificar directorios padre
            parent_dirs = [
                os.path.join(root_path, server_name),
                os.path.join(root_path, server_name, "ShooterGame"),
                os.path.join(root_path, server_name, "ShooterGame", "Saved")
            ]
            
            for parent_dir in parent_dirs:
                if os.path.exists(parent_dir):
                    print(f"  ✅ Existe: {parent_dir}")
                else:
                    print(f"  ❌ NO existe: {parent_dir}")
                    break

if __name__ == "__main__":
    check_log_files()