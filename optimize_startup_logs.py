#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para optimizar los logs de inicio de la aplicación
Implementa las mejoras identificadas en el análisis de rendimiento
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

def optimize_logger():
    """Optimizar el sistema de logging para inicio más rápido"""
    logger_file = Path("utils/logger.py")
    
    print("🔧 OPTIMIZANDO SISTEMA DE LOGGING")
    print("=" * 50)
    
    # Leer archivo actual
    with open(logger_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Crear versión optimizada
    optimized_content = content.replace(
        '''    def info(self, message):
        """Registrar mensaje informativo"""
        # En ejecutable, filtrar mensajes: solo los importantes
        if is_compiled():
            # Solo mostrar mensajes críticos del usuario (no debug técnico)
            critical_keywords = [
                "Auto-iniciando servidor", "Servidor iniciado", "Servidor detenido",
                "Error en auto-inicio", "Auto-inicio cancelado", "Conectado", "Desconectado",
                "Backup completado", "Error crítico", "Instalación completada"
            ]
            
            # Verificar si es un mensaje importante para el usuario
            if any(keyword in message for keyword in critical_keywords):
                self.logger.warning(message)  # Usar WARNING para asegurar que se muestre
        else:
            # En desarrollo, mostrar todos los mensajes info
            self.logger.info(message)''',
        '''    def info(self, message):
        """Registrar mensaje informativo"""
        # En ejecutable, filtrar mensajes: solo los críticos para el usuario
        if is_compiled():
            # Solo mostrar mensajes críticos del usuario (no debug técnico)
            critical_keywords = [
                "Auto-iniciando servidor", "Servidor iniciado", "Servidor detenido",
                "Error en auto-inicio", "Auto-inicio cancelado", "Conectado", "Desconectado",
                "Backup completado", "Error crítico", "Instalación completada",
                "✅ Aplicación iniciada", "❌ Error crítico"
            ]
            
            # Filtrar mensajes de inicio verbosos
            startup_noise = [
                "Sistema de configuración inicializado", "Configuraciones de aplicación aplicadas",
                "Cargando última configuración", "Auto-inicio manual:", "Auto-inicio con Windows:",
                "Último servidor cargado:", "Último mapa cargado:", "Panel de", "inicializado",
                "Diagnóstico fallback", "started_with_windows:", "system_tray disponible:",
                "Configuración manual:", "Inicio manual detectado", "Ruta de backup configurada:",
                "No se encontró archivo de mods", "Iniciando hilo de bandeja"
            ]
            
            # Si es ruido de inicio, omitir completamente
            if any(noise in message for noise in startup_noise):
                return
            
            # Verificar si es un mensaje importante para el usuario
            if any(keyword in message for keyword in critical_keywords):
                self.logger.warning(message)  # Usar WARNING para asegurar que se muestre
        else:
            # En desarrollo, mostrar todos los mensajes info
            self.logger.info(message)''')
    
    # Crear backup
    backup_file = logger_file.with_suffix('.py.backup')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Backup creado: {backup_file}")
    
    # Escribir versión optimizada
    with open(logger_file, 'w', encoding='utf-8') as f:
        f.write(optimized_content)
    print(f"✅ Logger optimizado: {logger_file}")
    
def optimize_main_window():
    """Optimizar mensajes INFO en MainWindow"""
    main_window_file = Path("gui/main_window.py")
    
    print("\n🔧 OPTIMIZANDO MAIN WINDOW")
    print("=" * 50)
    
    # Leer archivo actual
    with open(main_window_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Lista de optimizaciones
    optimizations = [
        # Reducir mensajes de configuración verbosos
        ('self.logger.info(f"📋 Auto-inicio manual: {auto_start_manual}")', 
         '# self.logger.info(f"📋 Auto-inicio manual: {auto_start_manual}")  # Optimizado: reducir ruido'),
        
        ('self.logger.info(f"🖥️ Auto-inicio con Windows: {auto_start_windows}")', 
         '# self.logger.info(f"🖥️ Auto-inicio con Windows: {auto_start_windows}")  # Optimizado: reducir ruido'),
        
        ('self.logger.info(f"🖥️ Último servidor cargado: {last_server}")', 
         '# self.logger.info(f"🖥️ Último servidor cargado: {last_server}")  # Optimizado: reducir ruido'),
        
        ('self.logger.info(f"🗺️ Último mapa cargado: {last_map}")', 
         '# self.logger.info(f"🗺️ Último mapa cargado: {last_map}")  # Optimizado: reducir ruido'),
        
        # Simplificar mensajes de auto-inicio
        ('self.logger.info(f"🔍 MainWindow: Inicio con Windows detectado, auto_start_server_with_windows = {should_auto_start}")', 
         '# self.logger.info(f"🔍 MainWindow: Inicio con Windows detectado, auto_start_server_with_windows = {should_auto_start}")  # Optimizado'),
        
        ('self.logger.info(f"🔍 MainWindow: Inicio manual detectado, auto_start_server = {should_auto_start}")', 
         '# self.logger.info(f"🔍 MainWindow: Inicio manual detectado, auto_start_server = {should_auto_start}")  # Optimizado'),
        
        ('self.logger.info("🚀 MainWindow: Auto-inicio del servidor habilitado, continuando...")', 
         '# self.logger.info("🚀 MainWindow: Auto-inicio del servidor habilitado, continuando...")  # Optimizado'),
        
        # Agrupar mensajes de diagnóstico
        ('self.logger.info("🔍 Diagnóstico fallback auto-inicio:")', 
         '# Diagnóstico agrupado - solo en desarrollo'),
        
        ('self.logger.info(f"   - started_with_windows: {self.started_with_windows}")', 
         ''),
        
        ('self.logger.info(f"   - auto_start_server: {self.app_settings.get_setting(\'auto_start_server\')}")', 
         ''),
        
        ('self.logger.info(f"   - auto_start_server_with_windows: {self.app_settings.get_setting(\'auto_start_server_with_windows\')}")', 
         ''),
        
        ('self.logger.info(f"   - system_tray disponible: {hasattr(self, \'system_tray\') and self.system_tray is not None}")', 
         ''),
        
        ('self.logger.info(f"   - Configuración manual: {should_auto_start}")', 
         ''),
    ]
    
    # Aplicar optimizaciones
    modified = False
    for old_text, new_text in optimizations:
        if old_text in content:
            content = content.replace(old_text, new_text)
            modified = True
            print(f"✅ Optimizado: {old_text[:50]}...")
    
    if modified:
        # Crear backup
        backup_file = main_window_file.with_suffix('.py.backup')
        with open(main_window_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(original_content)
        print(f"💾 Backup creado: {backup_file}")
        
        # Escribir versión optimizada
        with open(main_window_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ MainWindow optimizado: {main_window_file}")
    else:
        print("ℹ️ No se encontraron patrones para optimizar en MainWindow")

def optimize_panels():
    """Optimizar mensajes en paneles"""
    print("\n🔧 OPTIMIZANDO PANELES")
    print("=" * 50)
    
    panels_dir = Path("gui/panels")
    panel_files = list(panels_dir.glob("*.py"))
    
    optimizations_applied = 0
    
    for panel_file in panel_files:
        try:
            with open(panel_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Optimizaciones comunes para paneles
            panel_optimizations = [
                ('self.logger.info("Panel de', '# self.logger.info("Panel de'),  # Comentar mensajes de inicialización
                ('self.logger.info("Sistema de logs funcionando")', '# self.logger.info("Sistema de logs funcionando")  # Optimizado'),
                ('self.logger.info("Listo para recibir comandos")', '# self.logger.info("Listo para recibir comandos")  # Optimizado'),
                ('self.logger.info("Área de logs activa")', '# self.logger.info("Área de logs activa")  # Optimizado'),
                ('self.logger.info("Monitoreo del sistema iniciado")', '# self.logger.info("Monitoreo del sistema iniciado")  # Optimizado'),
            ]
            
            for old_text, new_text in panel_optimizations:
                if old_text in content:
                    content = content.replace(old_text, new_text)
                    optimizations_applied += 1
            
            # Si se hicieron cambios, guardar
            if content != original_content:
                # Crear backup
                backup_file = panel_file.with_suffix('.py.backup')
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                # Escribir versión optimizada
                with open(panel_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ Optimizado: {panel_file.name}")
                
        except Exception as e:
            print(f"⚠️ Error procesando {panel_file.name}: {e}")
    
    print(f"📊 Total de optimizaciones aplicadas en paneles: {optimizations_applied}")

def create_startup_summary():
    """Crear un mensaje de resumen de inicio optimizado"""
    print("\n🔧 CREANDO MENSAJE DE RESUMEN")
    print("=" * 50)
    
    # Agregar al final de main_window.py un método para mostrar resumen
    main_window_file = Path("gui/main_window.py")
    
    with open(main_window_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar el final de la clase MainWindow
    if "def restore_from_tray(self):" in content:
        # Agregar método de resumen después del último método
        summary_method = '''
    
    def show_startup_summary(self):
        """Mostrar resumen optimizado del inicio"""
        try:
            # Solo mostrar un mensaje de resumen en lugar de muchos INFO
            server_name = getattr(self, 'selected_server', 'No configurado')
            map_name = getattr(self, 'selected_map', 'No configurado')
            auto_start = self.app_settings.get_setting("auto_start_server") if hasattr(self, 'app_settings') else False
            
            summary = f"✅ Aplicación iniciada | Servidor: {server_name} | Mapa: {map_name} | Auto-inicio: {'Sí' if auto_start else 'No'}"
            self.logger.info(summary)
            
            # Mostrar en logs de la aplicación si está disponible
            if hasattr(self, 'add_log_message'):
                self.add_log_message(summary)
                
        except Exception as e:
            self.logger.error(f"Error en resumen de inicio: {e}")'''
        
        # Insertar antes del final de la clase
        insert_pos = content.rfind("        except Exception as e:")
        if insert_pos != -1:
            # Encontrar el final del método restore_from_tray
            end_pos = content.find("\n\n", insert_pos)
            if end_pos != -1:
                content = content[:end_pos] + summary_method + content[end_pos:]
                
                with open(main_window_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("✅ Método de resumen agregado a MainWindow")
            else:
                print("⚠️ No se pudo encontrar posición para insertar método")
        else:
            print("⚠️ No se pudo encontrar patrón de inserción")
    else:
        print("⚠️ No se encontró método restore_from_tray para referencia")

def main():
    """Ejecutar todas las optimizaciones"""
    print("🚀 OPTIMIZADOR DE LOGS DE INICIO")
    print("=" * 60)
    print("Este script optimizará los logs para un inicio más rápido")
    print()
    
    try:
        # Optimizar logger
        optimize_logger()
        
        # Optimizar main window
        optimize_main_window()
        
        # Optimizar paneles
        optimize_panels()
        
        # Crear resumen de inicio
        create_startup_summary()
        
        print("\n✅ OPTIMIZACIÓN COMPLETADA")
        print("=" * 60)
        print("Cambios realizados:")
        print("• Logger filtrado para reducir ruido de inicio")
        print("• Mensajes verbosos de configuración comentados")
        print("• Mensajes de diagnóstico de auto-inicio simplificados")
        print("• Mensajes de inicialización de paneles optimizados")
        print("• Método de resumen de inicio agregado")
        print()
        print("💡 Para revertir cambios, usa los archivos .backup creados")
        print("🚀 Reinicia la aplicación para ver las mejoras")
        
    except Exception as e:
        print(f"❌ Error durante la optimización: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()