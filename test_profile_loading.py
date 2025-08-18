#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para diagnosticar el problema de carga de perfiles
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_profiles import ConfigProfileManager
from utils.logger import Logger

def test_profile_loading():
    """Probar la carga de perfiles con logging detallado"""
    
    # Configurar logger
    logger = Logger()
    
    # Crear gestor de perfiles
    profile_manager = ConfigProfileManager(logger)
    
    print("=== PRUEBA DE CARGA DE PERFILES ===")
    print()
    
    # Listar perfiles disponibles
    profiles = profile_manager.get_profiles_list()
    print(f"Perfiles disponibles: {len(profiles)}")
    for profile in profiles:
        print(f"  - {profile['display_name']}: {profile.get('files', [])}")
    print()
    
    if not profiles:
        print("❌ No hay perfiles disponibles para probar")
        return
    
    # Usar el primer perfil para la prueba
    test_profile = profiles[0]
    profile_name = test_profile['display_name']
    
    print(f"🧪 Probando carga del perfil: {profile_name}")
    print()
    
    # Definir rutas de destino de prueba
    test_dir = Path("test_profile_output")
    test_dir.mkdir(exist_ok=True)
    
    gameusersettings_dest = str(test_dir / "GameUserSettings.ini")
    game_ini_dest = str(test_dir / "Game.ini")
    
    print(f"Rutas de destino:")
    print(f"  GameUserSettings: {gameusersettings_dest}")
    print(f"  Game.ini: {game_ini_dest}")
    print()
    
    # Intentar cargar el perfil
    print("🔄 Iniciando carga del perfil...")
    print("=" * 50)
    
    success = profile_manager.load_profile(
        profile_name=profile_name,
        gameusersettings_dest=gameusersettings_dest,
        game_ini_dest=game_ini_dest
    )
    
    print("=" * 50)
    print(f"Resultado: {'✅ Éxito' if success else '❌ Error'}")
    print()
    
    # Verificar qué archivos se copiaron realmente
    print("📁 Verificando archivos copiados:")
    
    gus_exists = os.path.exists(gameusersettings_dest)
    game_exists = os.path.exists(game_ini_dest)
    
    print(f"  GameUserSettings.ini: {'✅ Copiado' if gus_exists else '❌ No copiado'}")
    print(f"  Game.ini: {'✅ Copiado' if game_exists else '❌ No copiado'}")
    
    if gus_exists:
        size = os.path.getsize(gameusersettings_dest)
        print(f"    Tamaño: {size} bytes")
    
    if game_exists:
        size = os.path.getsize(game_ini_dest)
        print(f"    Tamaño: {size} bytes")
    
    print()
    
    # Limpiar archivos de prueba
    try:
        if gus_exists:
            os.remove(gameusersettings_dest)
        if game_exists:
            os.remove(game_ini_dest)
        test_dir.rmdir()
        print("🧹 Archivos de prueba limpiados")
    except Exception as e:
        print(f"⚠️ Error al limpiar archivos de prueba: {e}")

if __name__ == "__main__":
    test_profile_loading()