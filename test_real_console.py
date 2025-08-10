#!/usr/bin/env python3
"""
Script de prueba para la consola RCON real del servidor ARK
"""

import sys
import os
import subprocess
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.panels.working_logs_panel import WorkingLogsPanel
from utils.config_manager import ConfigManager
from utils.logger import Logger
import customtkinter as ctk

def test_rcon_connection():
    """Probar conexión RCON directamente"""
    print("🔍 Probando conexión RCON...")
    
    # Buscar ejecutable RCON
    search_paths = [
        Path("rcon"),
        Path.cwd() / "rcon",
        Path(__file__).parent / "rcon",
    ]
    
    rcon_exe = None
    for search_path in search_paths:
        if search_path.exists():
            for file in search_path.glob("*.exe"):
                if "rcon" in file.name.lower():
                    rcon_exe = file
                    break
            if rcon_exe:
                break
    
    if not rcon_exe:
        print("❌ No se encontró ejecutable RCON")
        return False
    
    print(f"✅ Ejecutable RCON encontrado: {rcon_exe}")
    
    # Probar comando simple
    try:
        cmd = [
            str(rcon_exe),
            "-a", "127.0.0.1:27020",
            "-p", "test_password",
            "GetServerInfo"
        ]
        
        print(f"📤 Ejecutando: {' '.join(cmd[:-1])} [password oculto]")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(rcon_exe.parent),
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        print(f"📥 Código de retorno: {result.returncode}")
        print(f"📥 Salida: {result.stdout.strip()}")
        if result.stderr:
            print(f"❌ Error: {result.stderr.strip()}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Timeout en conexión RCON")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_console_panel():
    """Probar el panel de consola"""
    print("\n🎮 Probando panel de consola...")
    
    # Crear ventana de prueba
    root = ctk.CTk()
    root.title("Prueba Consola RCON Real")
    root.geometry("800x600")
    
    # Configuración básica
    config_manager = ConfigManager()
    logger = Logger()
    
    # Crear panel de logs
    logs_panel = WorkingLogsPanel(root, config_manager, logger, root)
    
    # Configurar servidor de prueba
    logs_panel.rcon_ip = "127.0.0.1"
    logs_panel.rcon_port = "27020"
    logs_panel.rcon_password = "test_password"
    
    print("✅ Panel de consola creado correctamente")
    print("💡 Usa la interfaz para probar la conexión RCON")
    
    # Ejecutar ventana
    root.mainloop()

def main():
    """Función principal"""
    print("🚀 PRUEBA DE CONSOLA RCON REAL")
    print("=" * 50)
    
    # Probar conexión RCON
    rcon_works = test_rcon_connection()
    
    if rcon_works:
        print("\n✅ Conexión RCON funcionando")
    else:
        print("\n❌ Conexión RCON falló")
        print("💡 Asegúrate de que:")
        print("   - El servidor ARK esté ejecutándose")
        print("   - RCON esté habilitado en el servidor")
        print("   - El puerto RCON sea correcto")
        print("   - El password RCON sea correcto")
    
    # Preguntar si probar la interfaz
    try:
        response = input("\n¿Probar interfaz de consola? (s/n): ").lower()
        if response in ['s', 'si', 'y', 'yes']:
            test_console_panel()
    except KeyboardInterrupt:
        print("\n👋 Prueba cancelada")
    except Exception as e:
        print(f"❌ Error en interfaz: {e}")

if __name__ == "__main__":
    main()


