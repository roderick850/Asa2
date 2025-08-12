#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar los mensajes INFO durante el inicio de la aplicación
Identifica qué mensajes están causando lentitud y cuáles se pueden optimizar
"""

import time
import sys
import os
import threading
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

class LogAnalyzer:
    def __init__(self):
        self.start_time = time.time()
        self.log_messages = []
        self.original_info = None
        
    def intercept_logger(self):
        """Interceptar mensajes del logger para análisis"""
        from utils.logger import Logger
        
        # Crear una instancia del logger
        logger = Logger()
        
        # Guardar el método original
        self.original_info = logger.info
        
        # Crear método interceptor
        def intercepted_info(message):
            current_time = time.time()
            elapsed = current_time - self.start_time
            self.log_messages.append({
                'time': elapsed,
                'message': message,
                'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3]
            })
            print(f"[{elapsed:.3f}s] INFO: {message}")
            # Llamar al método original
            return self.original_info(message)
        
        # Reemplazar el método
        logger.info = intercepted_info
        return logger
        
    def simulate_app_startup(self):
        """Simular el inicio de la aplicación con interceptación de logs"""
        print("🚀 SIMULANDO INICIO DE LA APLICACIÓN")
        print("=" * 60)
        print(f"🕐 Inicio: {time.strftime('%H:%M:%S')}")
        print()
        
        try:
            # Interceptar logger
            logger = self.intercept_logger()
            
            # Simular inicialización como en main.py
            print("📦 Importando módulos...")
            import customtkinter as ctk
            from utils.config_manager import ConfigManager
            from utils.app_settings import AppSettings
            from gui.main_window import MainWindow
            
            print("⚙️ Configurando CustomTkinter...")
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            
            print("🔧 Inicializando ConfigManager...")
            config_manager = ConfigManager()
            config_manager.load_config()
            logger.info("Sistema de configuración inicializado correctamente")
            
            print("🪟 Creando ventana principal...")
            root = ctk.CTk()
            root.title("Ark Survival Ascended - Administrador de Servidores")
            root.geometry("1200x900")
            root.minsize(800, 500)
            
            print("🏗️ Inicializando MainWindow...")
            # Esto debería generar muchos mensajes INFO
            main_window = MainWindow(root, config_manager, logger)
            
            print("✅ Inicialización completada")
            
            # No ejecutar mainloop, solo destruir
            root.destroy()
            
        except Exception as e:
            print(f"❌ Error durante la simulación: {e}")
            import traceback
            traceback.print_exc()
            
    def analyze_logs(self):
        """Analizar los mensajes de log capturados"""
        print("\n📊 ANÁLISIS DE MENSAJES INFO:")
        print("=" * 60)
        
        if not self.log_messages:
            print("❌ No se capturaron mensajes INFO")
            return
            
        print(f"📝 Total de mensajes INFO: {len(self.log_messages)}")
        print()
        
        # Mostrar todos los mensajes con tiempo
        print("🕐 CRONOLOGÍA DE MENSAJES:")
        print("-" * 50)
        for i, log in enumerate(self.log_messages, 1):
            print(f"{i:2d}. [{log['time']:6.3f}s] {log['message']}")
            
        # Analizar patrones
        print("\n🔍 ANÁLISIS DE PATRONES:")
        print("-" * 50)
        
        # Contar mensajes por categoría
        categories = {
            'configuración': 0,
            'carga': 0,
            'inicialización': 0,
            'auto-inicio': 0,
            'panel': 0,
            'otros': 0
        }
        
        for log in self.log_messages:
            msg = log['message'].lower()
            if any(word in msg for word in ['configuración', 'config', 'settings']):
                categories['configuración'] += 1
            elif any(word in msg for word in ['cargando', 'carga', 'load']):
                categories['carga'] += 1
            elif any(word in msg for word in ['inicializ', 'init', 'setup']):
                categories['inicialización'] += 1
            elif any(word in msg for word in ['auto-inicio', 'auto-start', 'auto_start']):
                categories['auto-inicio'] += 1
            elif any(word in msg for word in ['panel', 'tab']):
                categories['panel'] += 1
            else:
                categories['otros'] += 1
                
        for category, count in categories.items():
            if count > 0:
                print(f"📋 {category.capitalize()}: {count} mensajes")
                
        # Identificar mensajes que toman más tiempo
        print("\n⏱️ MENSAJES CON MAYOR IMPACTO EN TIEMPO:")
        print("-" * 50)
        
        if len(self.log_messages) > 1:
            # Calcular tiempo entre mensajes
            time_gaps = []
            for i in range(1, len(self.log_messages)):
                gap = self.log_messages[i]['time'] - self.log_messages[i-1]['time']
                time_gaps.append((gap, i-1, self.log_messages[i-1]['message']))
                
            # Ordenar por tiempo de gap
            time_gaps.sort(reverse=True)
            
            # Mostrar los 5 gaps más largos
            for gap, idx, message in time_gaps[:5]:
                if gap > 0.001:  # Solo mostrar gaps significativos
                    print(f"⏳ {gap:.3f}s después de: {message[:60]}...")
                    
    def generate_recommendations(self):
        """Generar recomendaciones de optimización"""
        print("\n💡 RECOMENDACIONES DE OPTIMIZACIÓN:")
        print("=" * 60)
        
        total_time = time.time() - self.start_time
        num_messages = len(self.log_messages)
        
        print(f"⏱️ Tiempo total de análisis: {total_time:.3f}s")
        print(f"📝 Mensajes INFO generados: {num_messages}")
        
        if num_messages > 20:
            print("\n🐌 PROBLEMA: Demasiados mensajes INFO durante el inicio")
            print("   Soluciones recomendadas:")
            print("   • Cambiar mensajes no críticos de INFO a DEBUG")
            print("   • Filtrar mensajes en modo ejecutable")
            print("   • Diferir mensajes no esenciales")
            print("   • Usar logging asíncrono para mensajes no críticos")
            
        if total_time > 2.0:
            print("\n⚠️ PROBLEMA: Inicio lento detectado")
            print("   Soluciones recomendadas:")
            print("   • Cargar configuraciones de forma lazy")
            print("   • Inicializar paneles bajo demanda")
            print("   • Usar threading para operaciones no críticas")
            
        # Recomendaciones específicas basadas en mensajes
        config_messages = [msg for msg in self.log_messages if 'config' in msg['message'].lower()]
        if len(config_messages) > 5:
            print("\n📋 OPTIMIZACIÓN: Muchos mensajes de configuración")
            print("   • Agrupar operaciones de configuración")
            print("   • Usar un solo mensaje de resumen")
            
        auto_start_messages = [msg for msg in self.log_messages if 'auto' in msg['message'].lower()]
        if len(auto_start_messages) > 3:
            print("\n🚀 OPTIMIZACIÓN: Mensajes de auto-inicio verbosos")
            print("   • Simplificar lógica de auto-inicio")
            print("   • Reducir mensajes de debug")
            
    def run_analysis(self):
        """Ejecutar análisis completo"""
        self.simulate_app_startup()
        self.analyze_logs()
        self.generate_recommendations()
        
def main():
    analyzer = LogAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()