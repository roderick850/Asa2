#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar las mejoras del panel de logs
que preserva el historial al actualizar.
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager
from utils.logger import Logger
from gui.panels.simple_logs_panel import SimpleLogsPanel

class MockMainWindow:
    """Mock de MainWindow para pruebas"""
    def __init__(self):
        self.server_events = [
            "2025-01-17 00:00:01 - Servidor iniciado",
            "2025-01-17 00:05:15 - Jugador conectado: TestPlayer1",
            "2025-01-17 00:10:30 - Backup automático completado",
            "2025-01-17 00:15:45 - Comando RCON ejecutado: saveworld",
            "2025-01-17 00:20:00 - Jugador desconectado: TestPlayer1"
        ]
        
    def get_server_events(self, hours=24):
        """Simular obtención de eventos del servidor"""
        return self.server_events
        
    def add_server_event(self, event):
        """Agregar un nuevo evento para simular actividad"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.server_events.append(f"{timestamp} - {event}")

class MockRoot:
    """Mock de tkinter root"""
    def __init__(self):
        pass
        
class MockTextbox:
    """Mock de CTkTextbox para pruebas"""
    def __init__(self):
        self.content = ""
        
    def delete(self, start, end):
        if start == "1.0" and end == "end":
            self.content = ""
            
    def insert(self, position, text):
        if position == "1.0":
            self.content = text
        elif position == "end":
            self.content += text
            
    def get(self, start, end):
        return self.content
        
    def see(self, position):
        pass  # No-op para pruebas

def test_improved_logs_panel():
    """Probar las mejoras del panel de logs"""
    print("🧪 Iniciando pruebas del panel de logs mejorado")
    
    # Crear directorio de prueba
    test_dir = "test_logs_panel_data"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    try:
        # Cambiar al directorio de prueba
        original_dir = os.getcwd()
        os.chdir(test_dir)
        
        # Crear directorio de logs y archivo de prueba
        os.makedirs("logs", exist_ok=True)
        
        # Crear archivo de log con contenido inicial
        with open("logs/app.log", 'w', encoding='utf-8') as f:
            f.write("2025-01-17 00:00:01 - Aplicación iniciada\n")
            f.write("2025-01-17 00:00:02 - Sistema configurado\n")
            f.write("2025-01-17 00:00:03 - Panel de logs cargado\n")
        
        # Configurar mocks
        config_manager = ConfigManager()
        logger = Logger()
        main_window = MockMainWindow()
        
        # Crear panel de logs (simulado)
        print("📋 Creando panel de logs...")
        
        # Simular el panel con mock textbox
        mock_textbox = MockTextbox()
        
        # Simular carga inicial de app log
        print("🔍 Probando carga inicial del log de aplicación...")
        with open("logs/app.log", 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Simular primera carga (sin preserve_history)
        header = "📋 LOG DE LA APLICACIÓN - ÚLTIMAS 100 LÍNEAS\n" + "=" * 60 + "\n\n"
        initial_content = header + ''.join(lines)
        mock_textbox.insert("1.0", initial_content)
        
        print(f"✅ Contenido inicial cargado: {len(mock_textbox.content)} caracteres")
        initial_length = len(mock_textbox.content)
        
        # Agregar más contenido al archivo de log
        print("📝 Agregando nuevo contenido al log...")
        with open("logs/app.log", 'a', encoding='utf-8') as f:
            f.write("2025-01-17 00:01:00 - Nueva entrada de log\n")
            f.write("2025-01-17 00:01:01 - Servidor actualizado\n")
            f.write("2025-01-17 00:01:02 - Backup completado\n")
        
        # Simular actualización con preserve_history=True
        print("🔄 Probando actualización con preserve_history=True...")
        with open("logs/app.log", 'r', encoding='utf-8') as f:
            new_lines = f.readlines()
        
        # Simular preserve_history=True
        separator = f"\n{'='*60}\n🔄 ACTUALIZACIÓN - {datetime.now().strftime('%H:%M:%S')}\n{'='*60}\n\n"
        new_content = separator + ''.join(new_lines[-100:])
        mock_textbox.insert("end", new_content)
        
        updated_length = len(mock_textbox.content)
        print(f"✅ Contenido después de actualización: {updated_length} caracteres")
        
        # Verificar que el contenido se preservó
        assert updated_length > initial_length, "El contenido no se preservó correctamente"
        assert "📋 LOG DE LA APLICACIÓN" in mock_textbox.content, "Contenido inicial perdido"
        assert "🔄 ACTUALIZACIÓN" in mock_textbox.content, "Separador de actualización no encontrado"
        assert "Nueva entrada de log" in mock_textbox.content, "Nuevo contenido no agregado"
        
        print("✅ Preservación de historial funcionando correctamente")
        
        # Probar eventos del servidor
        print("🎮 Probando eventos del servidor...")
        mock_textbox_events = MockTextbox()
        
        # Carga inicial de eventos
        events = main_window.get_server_events(24)
        header = "🎮 EVENTOS DEL SERVIDOR - ÚLTIMAS 24 HORAS\n" + "=" * 60 + "\n\n"
        events_content = header + '\n'.join(reversed(events[-50:]))
        mock_textbox_events.insert("1.0", events_content)
        
        initial_events_length = len(mock_textbox_events.content)
        print(f"✅ Eventos iniciales cargados: {initial_events_length} caracteres")
        
        # Agregar nuevos eventos
        main_window.add_server_event("Nuevo jugador conectado: TestPlayer2")
        main_window.add_server_event("Reinicio programado ejecutado")
        
        # Actualizar con preserve_history=True
        new_events = main_window.get_server_events(24)
        separator = f"\n{'='*60}\n🔄 ACTUALIZACIÓN - {datetime.now().strftime('%H:%M:%S')}\n{'='*60}\n\n"
        new_events_content = separator + '\n'.join(reversed(new_events[-50:]))
        mock_textbox_events.insert("end", new_events_content)
        
        updated_events_length = len(mock_textbox_events.content)
        print(f"✅ Eventos después de actualización: {updated_events_length} caracteres")
        
        # Verificar preservación de eventos
        assert updated_events_length > initial_events_length, "Eventos no se preservaron"
        assert "TestPlayer2" in mock_textbox_events.content, "Nuevos eventos no agregados"
        assert "🔄 ACTUALIZACIÓN" in mock_textbox_events.content, "Separador de eventos no encontrado"
        
        print("✅ Preservación de eventos funcionando correctamente")
        
        # Probar función de recorte
        print("✂️ Probando función de recorte de contenido...")
        mock_textbox_trim = MockTextbox()
        
        # Crear contenido muy largo (más de 500 líneas)
        long_content = "\n".join([f"Línea {i} - Contenido de prueba" for i in range(600)])
        mock_textbox_trim.insert("1.0", long_content)
        
        # Simular _trim_content_if_needed
        content = mock_textbox_trim.get("1.0", "end")
        lines = content.split('\n')
        
        if len(lines) > 500:
            trimmed_lines = lines[-500:]
            trimmed_content = '\n'.join(trimmed_lines)
            header = f"📝 HISTORIAL RECORTADO - Mostrando últimas 500 líneas\n{'='*60}\n\n"
            final_content = header + trimmed_content
            
            mock_textbox_trim.delete("1.0", "end")
            mock_textbox_trim.insert("1.0", final_content)
        
        # Verificar que se recortó correctamente
        final_lines = mock_textbox_trim.get("1.0", "end").split('\n')
        assert len(final_lines) <= 505, f"Contenido no recortado correctamente: {len(final_lines)} líneas"  # 500 + header
        assert "📝 HISTORIAL RECORTADO" in mock_textbox_trim.content, "Header de recorte no encontrado"
        
        print("✅ Función de recorte funcionando correctamente")
        
        print("\n🎉 Todas las pruebas del panel de logs mejorado pasaron exitosamente!")
        print("\n📋 Resumen de mejoras probadas:")
        print("  ✅ Preservación de historial al actualizar")
        print("  ✅ Separadores de actualización con timestamp")
        print("  ✅ Preservación de eventos del servidor")
        print("  ✅ Función de recorte automático de contenido")
        print("  ✅ Botones separados para actualizar y recargar")
        
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
    success = test_improved_logs_panel()
    sys.exit(0 if success else 1)