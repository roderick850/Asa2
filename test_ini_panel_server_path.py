#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar que el panel INI actualiza correctamente
la ruta del servidor cuando se cambia de servidor.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager
from utils.logger import Logger
from gui.panels.ini_config_panel import IniConfigPanel

class MockMainWindow:
    """Mock de MainWindow para pruebas"""
    def __init__(self):
        self.selected_server = None
        self.root = MockRoot()
        
class MockRoot:
    """Mock de tkinter root"""
    def after(self, delay, callback):
        # Ejecutar inmediatamente para pruebas
        callback()

def test_ini_panel_server_path():
    """Probar que el panel INI actualiza correctamente la ruta del servidor"""
    print("🧪 Iniciando pruebas del panel INI - actualización de ruta del servidor")
    
    # Crear directorio de prueba
    test_dir = "test_ini_panel_data"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    try:
        # Cambiar al directorio de prueba
        original_dir = os.getcwd()
        os.chdir(test_dir)
        
        # Crear estructura de servidores de prueba
        servers_root = "servers"
        os.makedirs(servers_root, exist_ok=True)
        
        # Crear dos servidores de prueba
        server1_path = os.path.join(servers_root, "TestServer1")
        server2_path = os.path.join(servers_root, "TestServer2")
        
        for server_path in [server1_path, server2_path]:
            config_dir = os.path.join(server_path, "ShooterGame", "Saved", "Config", "WindowsServer")
            os.makedirs(config_dir, exist_ok=True)
            
            # Crear archivos INI de prueba
            gus_file = os.path.join(config_dir, "GameUserSettings.ini")
            with open(gus_file, 'w', encoding='utf-8') as f:
                f.write(f"[ServerSettings]\nServerName={os.path.basename(server_path)}\nMaxPlayers=20\n")
            
            game_file = os.path.join(config_dir, "Game.ini")
            with open(game_file, 'w', encoding='utf-8') as f:
                f.write(f"[/script/shootergame.shootergamemode]\nDifficultyOffset=1.0\n")
        
        # Configurar config_manager
        config_manager = ConfigManager()
        config_manager.set("server", "root_path", os.path.abspath(servers_root))
        config_manager.set("server", "server_path", os.path.abspath(server1_path))  # Inicialmente servidor 1
        config_manager.save()
        
        # Configurar logger
        logger = Logger()
        
        # Crear mock de main_window
        main_window = MockMainWindow()
        main_window.selected_server = "TestServer1"
        
        # Crear panel INI
        print("📋 Creando panel INI...")
        ini_panel = IniConfigPanel(None, config_manager, logger, main_window)
        
        # Verificar que inicialmente carga el servidor 1
        print("🔍 Verificando carga inicial del servidor 1...")
        ini_panel.load_ini_paths()
        assert ini_panel.game_user_settings_path is not None, "GameUserSettings.ini no encontrado para servidor 1"
        assert "TestServer1" in ini_panel.game_user_settings_path, f"Ruta incorrecta: {ini_panel.game_user_settings_path}"
        print(f"✅ Servidor 1 cargado correctamente: {ini_panel.game_user_settings_path}")
        
        # Simular cambio de servidor actualizando server_path en config_manager
        print("🔄 Simulando cambio al servidor 2...")
        config_manager.set("server", "server_path", os.path.abspath(server2_path))
        main_window.selected_server = "TestServer2"
        
        # Recargar rutas INI
        ini_panel.load_ini_paths()
        
        # Verificar que ahora carga el servidor 2
        print("🔍 Verificando cambio al servidor 2...")
        assert ini_panel.game_user_settings_path is not None, "GameUserSettings.ini no encontrado para servidor 2"
        assert "TestServer2" in ini_panel.game_user_settings_path, f"Ruta incorrecta: {ini_panel.game_user_settings_path}"
        print(f"✅ Servidor 2 cargado correctamente: {ini_panel.game_user_settings_path}")
        
        # Probar el método de recarga automática
        print("🔄 Probando recarga automática...")
        ini_panel._last_server = "TestServer1"  # Simular que estaba en servidor 1
        main_window.selected_server = "TestServer2"  # Cambiar a servidor 2
        
        # Simular verificación de cambios
        ini_panel.check_for_server_changes()
        
        # Verificar que se actualizó correctamente
        assert ini_panel._last_server == "TestServer2", f"Servidor no actualizado: {ini_panel._last_server}"
        print("✅ Recarga automática funcionando correctamente")
        
        # Probar con servidor inexistente
        print("🔍 Probando con servidor inexistente...")
        config_manager.set("server", "server_path", os.path.abspath("servers/ServerInexistente"))
        ini_panel.load_ini_paths()
        
        # Debería manejar graciosamente el servidor inexistente
        print("✅ Manejo de servidor inexistente correcto")
        
        print("\n🎉 Todas las pruebas del panel INI pasaron exitosamente!")
        print("\n📋 Resumen de pruebas:")
        print("  ✅ Carga inicial del servidor 1")
        print("  ✅ Cambio correcto al servidor 2")
        print("  ✅ Recarga automática funcionando")
        print("  ✅ Manejo de servidores inexistentes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Limpiar
        os.chdir(original_dir)
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        print("🧹 Limpieza completada")

if __name__ == "__main__":
    success = test_ini_panel_server_path()
    sys.exit(0 if success else 1)