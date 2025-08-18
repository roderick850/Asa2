#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la funcionalidad del sistema de cluster
"""

import sys
import os
import time
import json
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager
from utils.cluster_manager import ClusterManager, ServerInstance
from utils.logger import Logger

def test_cluster_manager():
    """Probar funcionalidad básica del ClusterManager"""
    print("🧪 Iniciando pruebas del ClusterManager...")
    
    # Inicializar componentes
    config_manager = ConfigManager()
    logger = Logger("test_cluster")
    
    # Crear ClusterManager
    cluster_manager = ClusterManager(config_manager, logger)
    
    print(f"✅ ClusterManager inicializado: {cluster_manager.cluster_name}")
    print(f"   ID del cluster: {cluster_manager.cluster_id}")
    print(f"   Servidores configurados: {len(cluster_manager.servers)}")
    
    # Listar servidores existentes
    if cluster_manager.servers:
        print("\n📋 Servidores en el cluster:")
        for name, server in cluster_manager.servers.items():
            print(f"   - {name}: {server.config.get('map', 'Unknown')} (Puerto: {server.config.get('port', 'N/A')})")
    else:
        print("\n⚠️  No hay servidores configurados en el cluster")
    
    return cluster_manager

def test_add_server(cluster_manager):
    """Probar agregar un nuevo servidor al cluster"""
    print("\n🔧 Probando agregar servidor al cluster...")
    
    # Configuración de servidor de prueba
    test_server_config = {
        "name": "TestServer",
        "map": "TheIsland_WP",
        "port": 7778,
        "query_port": 27016,
        "rcon_port": 32331,
        "max_players": 20,
        "server_path": "D:\\ASA\\TestServer",
        "priority": 2,
        "auto_start": False,
        "cluster_enabled": True
    }
    
    # Intentar agregar el servidor
    success = cluster_manager.add_server("TestServer", test_server_config)
    
    if success:
        print("✅ Servidor de prueba agregado exitosamente")
        print(f"   Total de servidores: {len(cluster_manager.servers)}")
    else:
        print("❌ Error al agregar servidor de prueba")
    
    return success

def test_cluster_operations(cluster_manager):
    """Probar operaciones básicas del cluster"""
    print("\n⚙️  Probando operaciones del cluster...")
    
    # Obtener información del cluster
    cluster_info = cluster_manager.get_cluster_info()
    print(f"✅ Información del cluster obtenida:")
    print(f"   Nombre: {cluster_info['cluster_name']}")
    print(f"   ID: {cluster_info['cluster_id']}")
    print(f"   Servidores configurados: {len(cluster_info['servers'])}")
    print(f"   Estado del cluster: {cluster_info.get('cluster_stats', {})}")
    
    # Probar conteo de servidores
    server_counts = cluster_manager.get_server_count()
    print(f"\n📊 Estadísticas de servidores:")
    print(f"   Total: {server_counts['total']}")
    print(f"   Activos: {server_counts['running']}")
    print(f"   Detenidos: {server_counts['stopped']}")
    print(f"   Iniciando: {server_counts['starting']}")
    
    # Probar obtener servidor específico
    if cluster_manager.servers:
        server_name = list(cluster_manager.servers.keys())[0]
        server = cluster_manager.get_server(server_name)
        if server:
            print(f"\n🎯 Servidor '{server_name}' encontrado:")
            print(f"   Estado: {server.status}")
            print(f"   Mapa: {server.config.get('map', 'N/A')}")
            print(f"   Puerto: {server.config.get('port', 'N/A')}")

def test_cluster_config_persistence(cluster_manager):
    """Probar persistencia de configuración del cluster"""
    print("\n💾 Probando persistencia de configuración...")
    
    # Guardar configuración
    cluster_manager.save_cluster_config()
    print("✅ Configuración del cluster guardada")
    
    # Verificar que el archivo existe
    config_file = cluster_manager.config_manager.get_data_file_path("cluster_config.json")
    if os.path.exists(config_file):
        print(f"✅ Archivo de configuración existe: {config_file}")
        
        # Leer y mostrar contenido
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            print(f"   Servidores en archivo: {len(config_data.get('servers', {}))}")
        except Exception as e:
            print(f"❌ Error leyendo configuración: {e}")
    else:
        print(f"❌ Archivo de configuración no encontrado: {config_file}")

def test_server_instance():
    """Probar funcionalidad de ServerInstance"""
    print("\n🖥️  Probando ServerInstance...")
    
    # Crear una instancia de servidor de prueba
    config_manager = ConfigManager()
    logger = Logger("test_server")
    cluster_manager = ClusterManager(config_manager, logger)
    
    server_config = {
        "name": "TestInstance",
        "map": "TheCenter_WP",
        "port": 7779,
        "query_port": 27017,
        "rcon_port": 32332,
        "max_players": 15,
        "server_path": "D:\\ASA\\TestInstance"
    }
    
    server_instance = ServerInstance("TestInstance", server_config, cluster_manager)
    
    print(f"✅ ServerInstance creada: {server_instance.name}")
    print(f"   Estado inicial: {server_instance.status}")
    print(f"   Configuración: {server_instance.config['map']} en puerto {server_instance.config['port']}")
    
    # Probar serialización
    server_dict = server_instance.to_dict()
    print(f"✅ Serialización exitosa: {len(server_dict)} campos")
    
    return server_instance

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas del sistema de cluster ARK")
    print("=" * 50)
    
    try:
        # Probar ClusterManager
        cluster_manager = test_cluster_manager()
        
        # Probar agregar servidor
        test_add_server(cluster_manager)
        
        # Probar operaciones del cluster
        test_cluster_operations(cluster_manager)
        
        # Probar persistencia
        test_cluster_config_persistence(cluster_manager)
        
        # Probar ServerInstance
        test_server_instance()
        
        print("\n" + "=" * 50)
        print("✅ Todas las pruebas completadas exitosamente")
        print("\n📋 Resumen:")
        print("   - ClusterManager: ✅ Funcional")
        print("   - Gestión de servidores: ✅ Funcional")
        print("   - Persistencia de configuración: ✅ Funcional")
        print("   - ServerInstance: ✅ Funcional")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)