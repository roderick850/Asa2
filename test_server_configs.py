#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar el sistema de configuración por servidor
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager
from gui.panels.principal_panel import PrincipalPanel
import logging

class MockMainWindow:
    """Mock de MainWindow para las pruebas"""
    def __init__(self):
        self.selected_server = None
        
class MockEntry:
    """Mock de Entry widget para las pruebas"""
    def __init__(self, initial_value=""):
        self.value = initial_value
        
    def get(self):
        return self.value
        
    def delete(self, start, end):
        self.value = ""
        
    def insert(self, pos, text):
        self.value = text
        
class MockText:
    """Mock de Text widget para las pruebas"""
    def __init__(self, initial_value=""):
        self.value = initial_value
        
    def get(self, start, end):
        return self.value
        
    def delete(self, start, end):
        self.value = ""
        
    def insert(self, pos, text):
        self.value = text
        
class MockVar:
    """Mock de Variable para las pruebas"""
    def __init__(self, initial_value=False):
        self.value = initial_value
        
    def get(self):
        return self.value
        
    def set(self, value):
        self.value = value

def test_server_configs():
    """Probar el sistema de configuración por servidor"""
    print("🧪 Iniciando pruebas del sistema de configuración por servidor...")
    
    # Crear directorio de prueba
    test_dir = "test_data"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir, ignore_errors=True)
    os.makedirs(test_dir, exist_ok=True)
    
    # Cambiar al directorio de prueba
    original_dir = os.getcwd()
    os.chdir(test_dir)
    
    try:
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        # Crear ConfigManager
        config_manager = ConfigManager()
        
        # Crear mock de MainWindow
        main_window = MockMainWindow()
        
        # Crear PrincipalPanel
        panel = PrincipalPanel(None, config_manager, logger, main_window)
        
        # Simular widgets de entrada
        panel.session_name_entry = MockEntry()
        panel.server_password_entry = MockEntry()
        panel.admin_password_entry = MockEntry()
        panel.max_players_entry = MockEntry()
        panel.query_port_entry = MockEntry()
        panel.port_entry = MockEntry()
        panel.multihome_entry = MockEntry()
        panel.message_entry = MockEntry()
        panel.duration_entry = MockEntry()
        panel.custom_args_text = MockText()
        panel.maxplayers_as_arg_var = MockVar()
        
        # Test 1: Configurar Servidor1
        print("\n📝 Test 1: Configurando Servidor1...")
        panel.current_server = "Servidor1"
        panel.session_name_entry.value = "Mi Servidor ARK 1"
        panel.server_password_entry.value = "password123"
        panel.admin_password_entry.value = "admin123"
        panel.max_players_entry.value = "50"
        panel.message_entry.value = "Bienvenido al Servidor 1"
        panel.maxplayers_as_arg_var.value = True
        
        panel.save_server_config("Servidor1")
        print("✅ Configuración de Servidor1 guardada")
        
        # Test 2: Configurar Servidor2
        print("\n📝 Test 2: Configurando Servidor2...")
        panel.current_server = "Servidor2"
        panel.session_name_entry.value = "Mi Servidor ARK 2"
        panel.server_password_entry.value = "password456"
        panel.admin_password_entry.value = "admin456"
        panel.max_players_entry.value = "100"
        panel.message_entry.value = "Bienvenido al Servidor 2"
        panel.maxplayers_as_arg_var.value = False
        
        panel.save_server_config("Servidor2")
        print("✅ Configuración de Servidor2 guardada")
        
        # Test 3: Cambiar a Servidor1 y verificar carga
        print("\n🔄 Test 3: Cambiando a Servidor1...")
        
        # Limpiar campos primero
        panel.session_name_entry.value = ""
        panel.server_password_entry.value = ""
        panel.admin_password_entry.value = ""
        panel.max_players_entry.value = ""
        panel.message_entry.value = ""
        panel.maxplayers_as_arg_var.value = False
        
        # Cargar configuración de Servidor1
        panel.load_server_config("Servidor1")
        
        # Verificar valores
        assert panel.session_name_entry.get() == "Mi Servidor ARK 1", f"Session name incorrecto: {panel.session_name_entry.get()}"
        assert panel.server_password_entry.get() == "password123", f"Server password incorrecto: {panel.server_password_entry.get()}"
        assert panel.admin_password_entry.get() == "admin123", f"Admin password incorrecto: {panel.admin_password_entry.get()}"
        assert panel.max_players_entry.get() == "50", f"Max players incorrecto: {panel.max_players_entry.get()}"
        assert panel.message_entry.get() == "Bienvenido al Servidor 1", f"Message incorrecto: {panel.message_entry.get()}"
        assert panel.maxplayers_as_arg_var.get() == True, f"MaxPlayers switch incorrecto: {panel.maxplayers_as_arg_var.get()}"
        
        print("✅ Configuración de Servidor1 cargada correctamente")
        
        # Test 4: Cambiar a Servidor2 y verificar carga
        print("\n🔄 Test 4: Cambiando a Servidor2...")
        
        # Cargar configuración de Servidor2
        panel.load_server_config("Servidor2")
        
        # Verificar valores
        assert panel.session_name_entry.get() == "Mi Servidor ARK 2", f"Session name incorrecto: {panel.session_name_entry.get()}"
        assert panel.server_password_entry.get() == "password456", f"Server password incorrecto: {panel.server_password_entry.get()}"
        assert panel.admin_password_entry.get() == "admin456", f"Admin password incorrecto: {panel.admin_password_entry.get()}"
        assert panel.max_players_entry.get() == "100", f"Max players incorrecto: {panel.max_players_entry.get()}"
        assert panel.message_entry.get() == "Bienvenido al Servidor 2", f"Message incorrecto: {panel.message_entry.get()}"
        assert panel.maxplayers_as_arg_var.get() == False, f"MaxPlayers switch incorrecto: {panel.maxplayers_as_arg_var.get()}"
        
        print("✅ Configuración de Servidor2 cargada correctamente")
        
        # Test 5: Verificar archivo JSON
        print("\n📄 Test 5: Verificando archivo de configuración...")
        
        config_file = "data/principal_server_configs.json"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                configs = json.load(f)
                
            assert "Servidor1" in configs, "Servidor1 no encontrado en configuraciones"
            assert "Servidor2" in configs, "Servidor2 no encontrado en configuraciones"
            
            server1_config = configs["Servidor1"]
            assert server1_config["session_name"] == "Mi Servidor ARK 1", "Session name de Servidor1 incorrecto en JSON"
            assert server1_config["maxplayers_as_arg"] == True, "MaxPlayers switch de Servidor1 incorrecto en JSON"
            
            server2_config = configs["Servidor2"]
            assert server2_config["session_name"] == "Mi Servidor ARK 2", "Session name de Servidor2 incorrecto en JSON"
            assert server2_config["maxplayers_as_arg"] == False, "MaxPlayers switch de Servidor2 incorrecto en JSON"
            
            print("✅ Archivo de configuración JSON correcto")
        else:
            raise AssertionError("Archivo de configuración no encontrado")
        
        # Test 6: Probar update_server_info
        print("\n🔄 Test 6: Probando update_server_info...")
        
        # Configurar valores en Servidor2
        panel.current_server = "Servidor2"
        panel.session_name_entry.value = "Servidor 2 Modificado"
        panel.server_password_entry.value = "newpassword"
        
        # Cambiar a Servidor1 usando update_server_info
        panel.update_server_info("Servidor1", "TheIsland")
        
        # Verificar que se guardó la configuración de Servidor2 y se cargó la de Servidor1
        # Recargar configuraciones para verificar
        panel.load_all_server_configs()
        
        # Verificar que Servidor2 se guardó con los nuevos valores
        if "Servidor2" in panel.server_configs:
            server2_config = panel.server_configs["Servidor2"]
            assert server2_config["session_name"] == "Servidor 2 Modificado", "Servidor2 no se guardó correctamente al cambiar"
            print("✅ Configuración de Servidor2 guardada automáticamente al cambiar")
        
        # Verificar que se cargó Servidor1
        assert panel.session_name_entry.get() == "Mi Servidor ARK 1", "Servidor1 no se cargó correctamente"
        print("✅ Configuración de Servidor1 cargada automáticamente al cambiar")
        
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("\n📊 Resumen de pruebas:")
        print("✅ Guardado de configuración por servidor")
        print("✅ Carga de configuración por servidor")
        print("✅ Persistencia en archivo JSON")
        print("✅ Cambio automático entre servidores")
        print("✅ Guardado automático al cambiar servidor")
        print("✅ Switch de MaxPlayers por servidor")
        
    finally:
        # Restaurar directorio original
        os.chdir(original_dir)
        # Limpiar directorio de prueba
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)
        
if __name__ == "__main__":
    test_server_configs()