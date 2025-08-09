#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar las configuraciones de auto-inicio
"""
import os
import sys
import json
from pathlib import Path

def check_config_files():
    """Verificar archivos de configuración"""
    print("🔍 === VERIFICACIÓN DE CONFIGURACIONES ===")
    
    # Verificar config.ini
    config_file = "config.ini"
    if os.path.exists(config_file):
        print(f"✅ {config_file} encontrado")
        
        # Leer config.ini
        import configparser
        config = configparser.ConfigParser()
        config.read(config_file)
        
        if 'app' in config:
            print("📋 Configuraciones en [app]:")
            for key, value in config['app'].items():
                print(f"   {key}: {value}")
        else:
            print("⚠️ Sección [app] no encontrada en config.ini")
    else:
        print(f"❌ {config_file} no encontrado")
    
    # Verificar data/app_settings.json
    settings_file = Path("data/app_settings.json")
    if settings_file.exists():
        print(f"✅ {settings_file} encontrado")
        
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Configuraciones importantes
            important_keys = [
                "startup_with_windows",
                "auto_start_server", 
                "auto_start_server_with_windows",
                "start_minimized",
                "minimize_to_tray"
            ]
            
            print("📋 Configuraciones importantes:")
            for key in important_keys:
                value = settings.get(key, "NO_CONFIGURADO")
                print(f"   {key}: {value}")
                
        except Exception as e:
            print(f"❌ Error leyendo {settings_file}: {e}")
    else:
        print(f"❌ {settings_file} no encontrado")
    
    print()

def check_windows_startup():
    """Verificar configuración de inicio con Windows"""
    print("🖥️ === VERIFICACIÓN DE INICIO CON WINDOWS ===")
    
    try:
        import winreg
        
        # Verificar registro
        reg_key = winreg.HKEY_CURRENT_USER
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "ArkServerManager"
        
        try:
            with winreg.OpenKey(reg_key, reg_path, 0, winreg.KEY_READ) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, app_name)
                    print(f"✅ Entrada en registro encontrada:")
                    print(f"   {value}")
                    
                    if "--windows-startup" in value:
                        print("✅ Argumento --windows-startup presente")
                    else:
                        print("⚠️ Argumento --windows-startup no encontrado")
                        
                except FileNotFoundError:
                    print("❌ No hay entrada en el registro")
        except Exception as e:
            print(f"❌ Error accediendo al registro: {e}")
            
    except ImportError:
        print("❌ No se puede verificar registro (no Windows)")
    
    # Verificar carpeta de inicio
    startup_folder = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    bat_file = startup_folder / "ArkServerManager.bat"
    
    if bat_file.exists():
        print(f"✅ Archivo .bat encontrado: {bat_file}")
        try:
            content = bat_file.read_text(encoding='utf-8')
            if "--windows-startup" in content:
                print("✅ Argumento --windows-startup presente en .bat")
            else:
                print("⚠️ Argumento --windows-startup no encontrado en .bat")
            print("📄 Contenido del archivo:")
            print(f"   {content.strip()}")
        except Exception as e:
            print(f"❌ Error leyendo archivo .bat: {e}")
    else:
        print(f"❌ Archivo .bat no encontrado: {bat_file}")
    
    print()

def check_last_server_config():
    """Verificar configuración del último servidor"""
    print("🎮 === VERIFICACIÓN DE ÚLTIMO SERVIDOR ===")
    
    # Verificar config.ini
    config_file = "config.ini"
    if os.path.exists(config_file):
        import configparser
        config = configparser.ConfigParser()
        config.read(config_file)
        
        if 'app' in config:
            last_server = config['app'].get('last_server', 'NO_CONFIGURADO')
            last_map = config['app'].get('last_map', 'NO_CONFIGURADO')
            
            print(f"🖥️ Último servidor: {last_server}")
            print(f"🗺️ Último mapa: {last_map}")
            
            if last_server != 'NO_CONFIGURADO' and last_map != 'NO_CONFIGURADO':
                print("✅ Configuración de servidor y mapa OK")
            else:
                print("⚠️ Falta configuración de servidor o mapa")
        else:
            print("❌ Sección [app] no encontrada")
    else:
        print("❌ config.ini no encontrado")
    
    print()

def main():
    """Función principal"""
    print("🔧 ARK SERVER MANAGER - VERIFICADOR DE CONFIGURACIONES")
    print("=" * 60)
    
    check_config_files()
    check_windows_startup()
    check_last_server_config()
    
    print("🎯 === RECOMENDACIONES ===")
    print("1. Si 'auto_start_server_with_windows' es False, el servidor NO se iniciará automáticamente")
    print("2. Si 'last_server' o 'last_map' están vacíos, el auto-inicio fallará")
    print("3. Si no hay entrada en registro/carpeta de inicio, la app no arrancará con Windows")
    print("4. Verifica que el argumento '--windows-startup' esté presente para detección correcta")
    print()
    print("💡 Para activar auto-inicio:")
    print("   - Ve a Configuración → Configuraciones Avanzadas")
    print("   - Activa 'Iniciar con Windows'")  
    print("   - Activa 'Auto-iniciar servidor (Con Windows)'")
    print("   - Selecciona un servidor y mapa en la pestaña Principal")
    print("=" * 60)

if __name__ == "__main__":
    main()
