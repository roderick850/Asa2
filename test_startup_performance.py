#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar el rendimiento del inicio de la aplicación
Identifica qué componentes están causando lentitud durante el arranque
"""

import time
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

def measure_time(func_name):
    """Decorador para medir tiempo de ejecución"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            print(f"⏱️ {func_name}: {duration:.3f} segundos")
            return result
        return wrapper
    return decorator

class StartupAnalyzer:
    def __init__(self):
        self.start_time = time.time()
        self.checkpoints = []
        
    def checkpoint(self, name):
        """Registrar un punto de control con tiempo"""
        current_time = time.time()
        elapsed = current_time - self.start_time
        self.checkpoints.append((name, elapsed))
        print(f"📍 {name}: {elapsed:.3f}s")
        
    def analyze_imports(self):
        """Analizar tiempo de importación de módulos"""
        print("\n🔍 ANÁLISIS DE IMPORTACIONES:")
        print("=" * 50)
        
        # Medir importaciones críticas
        start = time.time()
        import customtkinter as ctk
        print(f"📦 customtkinter: {time.time() - start:.3f}s")
        
        start = time.time()
        from utils.config_manager import ConfigManager
        print(f"📦 ConfigManager: {time.time() - start:.3f}s")
        
        start = time.time()
        from utils.logger import Logger
        print(f"📦 Logger: {time.time() - start:.3f}s")
        
        start = time.time()
        from utils.app_settings import AppSettings
        print(f"📦 AppSettings: {time.time() - start:.3f}s")
        
        start = time.time()
        from gui.main_window import MainWindow
        print(f"📦 MainWindow: {time.time() - start:.3f}s")
        
    def analyze_initialization(self):
        """Analizar inicialización de componentes"""
        print("\n🔍 ANÁLISIS DE INICIALIZACIÓN:")
        print("=" * 50)
        
        # Configurar CustomTkinter
        start = time.time()
        import customtkinter as ctk
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        print(f"🎨 Configuración CTk: {time.time() - start:.3f}s")
        
        # Inicializar ConfigManager
        start = time.time()
        from utils.config_manager import ConfigManager
        config_manager = ConfigManager()
        config_manager.load_config()
        print(f"⚙️ ConfigManager init: {time.time() - start:.3f}s")
        
        # Inicializar Logger
        start = time.time()
        from utils.logger import Logger
        logger = Logger()
        print(f"📝 Logger init: {time.time() - start:.3f}s")
        
        # Crear ventana principal
        start = time.time()
        root = ctk.CTk()
        root.title("Test")
        root.geometry("1200x900")
        print(f"🪟 Ventana CTk: {time.time() - start:.3f}s")
        
        # Inicializar AppSettings
        start = time.time()
        from utils.app_settings import AppSettings
        app_settings = AppSettings(config_manager, logger)
        print(f"📋 AppSettings init: {time.time() - start:.3f}s")
        
        # Simular carga de configuraciones
        start = time.time()
        # Simular operaciones que hace load_last_configuration
        last_server = config_manager.get("app", "last_server", "")
        last_map = config_manager.get("app", "last_map", "")
        auto_start_manual = app_settings.get_setting("auto_start_server")
        auto_start_windows = app_settings.get_setting("auto_start_server_with_windows")
        print(f"📂 Carga configuraciones: {time.time() - start:.3f}s")
        
        root.destroy()
        
    def analyze_file_operations(self):
        """Analizar operaciones de archivos"""
        print("\n🔍 ANÁLISIS DE ARCHIVOS:")
        print("=" * 50)
        
        # Verificar archivos de configuración
        config_files = [
            "config.ini",
            "data/app_settings.json",
            "data/favorite_mods.json",
            "data/backup_config.json",
            "data/restart_history.json"
        ]
        
        for file_path in config_files:
            start = time.time()
            exists = os.path.exists(file_path)
            if exists:
                # Simular lectura
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    size = len(content)
                except:
                    size = 0
            else:
                size = 0
            duration = time.time() - start
            status = "✅" if exists else "❌"
            print(f"📄 {file_path}: {duration:.3f}s {status} ({size} chars)")
            
    def run_full_analysis(self):
        """Ejecutar análisis completo"""
        print("🚀 ANÁLISIS DE RENDIMIENTO DEL INICIO")
        print("=" * 60)
        print(f"🕐 Inicio del análisis: {time.strftime('%H:%M:%S')}")
        
        self.checkpoint("Inicio del análisis")
        
        # Analizar importaciones
        self.analyze_imports()
        self.checkpoint("Importaciones completadas")
        
        # Analizar inicialización
        self.analyze_initialization()
        self.checkpoint("Inicialización completada")
        
        # Analizar archivos
        self.analyze_file_operations()
        self.checkpoint("Operaciones de archivos completadas")
        
        # Resumen final
        print("\n📊 RESUMEN DE TIEMPOS:")
        print("=" * 50)
        for i, (name, elapsed) in enumerate(self.checkpoints):
            if i > 0:
                prev_elapsed = self.checkpoints[i-1][1]
                delta = elapsed - prev_elapsed
                print(f"📍 {name}: {elapsed:.3f}s (Δ {delta:.3f}s)")
            else:
                print(f"📍 {name}: {elapsed:.3f}s")
                
        total_time = time.time() - self.start_time
        print(f"\n⏱️ TIEMPO TOTAL: {total_time:.3f} segundos")
        
        # Recomendaciones
        print("\n💡 RECOMENDACIONES:")
        print("=" * 50)
        if total_time > 3.0:
            print("🐌 El inicio es lento (>3s). Posibles optimizaciones:")
            print("   • Reducir mensajes INFO durante el inicio")
            print("   • Cargar configuraciones de forma asíncrona")
            print("   • Diferir inicialización de paneles no críticos")
            print("   • Optimizar carga de archivos de configuración")
        elif total_time > 1.5:
            print("⚠️ El inicio es moderadamente lento (>1.5s). Considerar:")
            print("   • Filtrar mensajes de log no esenciales")
            print("   • Optimizar carga de configuraciones")
        else:
            print("✅ El tiempo de inicio es aceptable (<1.5s)")

def main():
    analyzer = StartupAnalyzer()
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main()