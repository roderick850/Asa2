#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para detectar procesos de ARK Server
"""

import psutil
import sys
import time

def find_ark_processes():
    """Buscar todos los procesos relacionados con ARK"""
    print("🔍 Buscando procesos de ARK...")
    print("=" * 50)
    
    ark_processes = []
    all_processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
            try:
                proc_info = proc.info
                all_processes.append(proc_info)
                
                # Buscar procesos que contengan 'ark' en el nombre
                if proc_info['name']:
                    name_lower = proc_info['name'].lower()
                    if 'ark' in name_lower or 'ascended' in name_lower or 'shootergame' in name_lower:
                        ark_processes.append(proc_info)
                        print(f"✅ Proceso ARK encontrado:")
                        print(f"   PID: {proc_info['pid']}")
                        print(f"   Nombre: {proc_info['name']}")
                        print(f"   Ejecutable: {proc_info.get('exe', 'N/A')}")
                        print(f"   Línea de comandos: {proc_info.get('cmdline', 'N/A')}")
                        print("-" * 30)
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
    except Exception as e:
        print(f"❌ Error al enumerar procesos: {e}")
        return [], []
    
    return ark_processes, all_processes

def test_specific_detection():
    """Probar detección específica como en server_manager.py"""
    print("\n🧪 Probando detección específica...")
    print("=" * 50)
    
    found = False
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and 'ArkAscendedServer.exe' in proc.info['name']:
                    print(f"✅ Servidor detectado por método específico:")
                    print(f"   PID: {proc.info['pid']}")
                    print(f"   Nombre: {proc.info['name']}")
                    found = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
    except Exception as e:
        print(f"❌ Error en detección específica: {e}")
        
    if not found:
        print("❌ No se encontró ArkAscendedServer.exe con el método específico")
        
    return found

def show_process_stats():
    """Mostrar estadísticas de procesos"""
    try:
        total_processes = len(list(psutil.process_iter()))
        print(f"\n📊 Total de procesos en el sistema: {total_processes}")
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")

def main():
    print("🎮 Diagnóstico de Detección de Servidor ARK")
    print("=" * 60)
    
    # Mostrar estadísticas del sistema
    show_process_stats()
    
    # Buscar procesos de ARK
    ark_processes, all_processes = find_ark_processes()
    
    # Probar detección específica
    specific_found = test_specific_detection()
    
    # Resumen
    print("\n📋 RESUMEN:")
    print("=" * 30)
    print(f"Procesos ARK encontrados (búsqueda amplia): {len(ark_processes)}")
    print(f"Detección específica exitosa: {'Sí' if specific_found else 'No'}")
    
    if ark_processes:
        print("\n🔍 Detalles de procesos ARK:")
        for i, proc in enumerate(ark_processes, 1):
            print(f"{i}. {proc['name']} (PID: {proc['pid']})")
    else:
        print("\n⚠️ No se encontraron procesos de ARK ejecutándose")
        print("\n💡 Sugerencias:")
        print("   1. Asegúrate de que el servidor ARK esté ejecutándose")
        print("   2. Verifica que el proceso se llame 'ArkAscendedServer.exe'")
        print("   3. Ejecuta este script como administrador si es necesario")
    
    print("\n✅ Diagnóstico completado")

if __name__ == "__main__":
    main()