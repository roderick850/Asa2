#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎮 Ejemplo de Integración de Consola con Sistema RCON

Este archivo demuestra cómo integrar la nueva consola del servidor
con el sistema RCON existente para una gestión completa del servidor ARK.
"""

import sys
import os
import time
import threading
from datetime import datetime

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.panels.working_logs_panel import WorkingLogsPanel
from utils.config_manager import ConfigManager
from utils.logger import Logger

class ConsoleRconIntegration:
    """Clase de ejemplo para integrar consola con RCON"""
    
    def __init__(self):
        """Inicializar la integración"""
        self.logger = Logger("console_integration")
        self.config_manager = ConfigManager(self.logger)
        
        # Simular panel de logs (en una aplicación real sería el panel real)
        self.logs_panel = None
        
        # Configuración del servidor
        self.server_config = {
            "ip": "192.168.1.100",
            "rcon_port": 32330,
            "rcon_password": "tu_password_rcon",
            "query_port": 27015,
            "game_port": 7777
        }
        
        self.logger.info("Sistema de integración consola-RCON inicializado")
    
    def setup_logs_panel(self, parent_widget):
        """Configurar el panel de logs con consola integrada"""
        try:
            self.logs_panel = WorkingLogsPanel(
                parent=parent_widget,
                config_manager=self.config_manager,
                logger=self.logger
            )
            
            self.logger.info("Panel de logs con consola integrada configurado")
            return self.logs_panel
            
        except Exception as e:
            self.logger.error(f"Error configurando panel de logs: {e}")
            return None
    
    def connect_to_server(self):
        """Conectar la consola al servidor ARK"""
        try:
            if not self.logs_panel:
                self.logger.error("Panel de logs no configurado")
                return False
            
            self.logger.info(f"Conectando a servidor {self.server_config['ip']}:{self.server_config['rcon_port']}")
            
            # Conectar usando el panel de logs
            self.logs_panel.connect_to_server_console(
                server_ip=self.server_config['ip'],
                rcon_port=self.server_config['rcon_port'],
                rcon_password=self.server_config['rcon_password']
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error conectando al servidor: {e}")
            return False
    
    def send_server_commands(self):
        """Enviar comandos de ejemplo al servidor"""
        if not self.logs_panel:
            return
        
        commands = [
            "listplayers",
            "saveworld",
            "broadcast ¡Servidor funcionando correctamente!",
            "getworldtime",
            "getserverinfo"
        ]
        
        for command in commands:
            self.logs_panel.send_rcon_command(command)
            time.sleep(2)  # Esperar entre comandos
    
    def monitor_server_activity(self):
        """Monitorear actividad del servidor en tiempo real"""
        if not self.logs_panel:
            return
        
        def monitor_loop():
            while True:
                try:
                    # Obtener estadísticas de la consola
                    stats = self.logs_panel.get_console_statistics()
                    
                    if stats.get('console_active'):
                        self.logger.info(f"Consola activa - Líneas: {stats.get('total_lines', 0)}")
                        
                        # Simular eventos del servidor
                        events = [
                            "👥 Jugador conectado: Player123",
                            "🌍 Cambio de mapa: TheIsland -> ScorchedEarth",
                            "💾 Backup automático completado",
                            "🦖 Dino salvaje eliminado: Rex_Alpha_001",
                            "🏗️ Nueva estructura construida por Player456"
                        ]
                        
                        import random
                        event = random.choice(events)
                        self.logs_panel.add_server_event("MONITORING", event)
                    
                    time.sleep(10)  # Actualizar cada 10 segundos
                    
                except Exception as e:
                    self.logger.error(f"Error en monitoreo: {e}")
                    break
        
        # Ejecutar monitoreo en hilo separado
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        self.logger.info("Monitoreo de actividad del servidor iniciado")
    
    def export_console_data(self):
        """Exportar datos de la consola"""
        if not self.logs_panel:
            return
        
        try:
            # Exportar consola completa
            self.logs_panel.export_console()
            
            # Exportar con timestamp personalizado
            self.logs_panel.export_console_with_timestamp(include_timestamp=True)
            
            self.logger.info("Datos de consola exportados correctamente")
            
        except Exception as e:
            self.logger.error(f"Error exportando consola: {e}")
    
    def get_server_status_summary(self):
        """Obtener resumen del estado del servidor"""
        if not self.logs_panel:
            return "Panel no configurado"
        
        try:
            stats = self.logs_panel.get_console_statistics()
            status = self.logs_panel.get_server_status()
            
            summary = {
                "consola_activa": stats.get('console_active', False),
                "estado_servidor": status,
                "lineas_totales": stats.get('total_lines', 0),
                "tamaño_buffer": stats.get('buffer_size', 0),
                "auto_scroll": stats.get('auto_scroll', False),
                "tiempo_activo": stats.get('uptime', None)
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error obteniendo resumen: {e}")
            return {"error": str(e)}
    
    def cleanup(self):
        """Limpiar recursos y desconectar"""
        try:
            if self.logs_panel:
                self.logs_panel.disconnect_from_server()
                self.logs_panel.clear_console()
            
            self.logger.info("Sistema de integración limpiado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error en limpieza: {e}")

def main():
    """Función principal de demostración"""
    print("🎮 Ejemplo de Integración Consola-RCON para ARK Server Manager")
    print("=" * 70)
    
    # Crear instancia de integración
    integration = ConsoleRconIntegration()
    
    try:
        # Simular configuración del panel (en una app real sería un widget real)
        class MockParent:
            def pack(self, **kwargs): pass
            def grid(self, **kwargs): pass
        
        mock_parent = MockParent()
        
        # Configurar panel de logs
        logs_panel = integration.setup_logs_panel(mock_parent)
        
        if logs_panel:
            print("✅ Panel de logs configurado correctamente")
            
            # Conectar al servidor
            if integration.connect_to_server():
                print("✅ Conectado al servidor ARK")
                
                # Iniciar monitoreo
                integration.monitor_server_activity()
                
                # Simular envío de comandos
                print("📤 Enviando comandos de ejemplo...")
                integration.send_server_commands()
                
                # Esperar un poco para ver la actividad
                time.sleep(15)
                
                # Obtener resumen del estado
                summary = integration.get_server_status_summary()
                print(f"📊 Resumen del estado: {summary}")
                
                # Exportar datos
                print("📁 Exportando datos de consola...")
                integration.export_console_data()
                
            else:
                print("❌ Error conectando al servidor")
        else:
            print("❌ Error configurando panel de logs")
    
    except Exception as e:
        print(f"❌ Error en demostración: {e}")
    
    finally:
        # Limpiar recursos
        integration.cleanup()
        print("🧹 Recursos limpiados")

if __name__ == "__main__":
    main()
