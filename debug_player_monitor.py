#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager
from utils.logger import Logger
from utils.player_monitor import PlayerMonitor

def main():
    # Inicializar logger
    logger_instance = Logger()
    logger = logger_instance.setup_logger()
    
    # Inicializar config manager
    config_manager = ConfigManager()
    
    # Obtener configuración del servidor
    root_path = config_manager.get("server", "root_path", "")
    last_server = config_manager.get("app", "last_server", "")
    
    print(f"Root path: {root_path}")
    print(f"Last server: {last_server}")
    
    if not root_path or not last_server:
        print("❌ No hay configuración de servidor")
        return
    
    # Construir ruta del servidor
    server_path = os.path.join(root_path, last_server)
    log_path = os.path.join(server_path, "ShooterGame", "Saved", "Logs", "ShooterGame.log")
    
    print(f"Server path: {server_path}")
    print(f"Log path: {log_path}")
    print(f"Server path exists: {os.path.exists(server_path)}")
    print(f"Log directory exists: {os.path.exists(os.path.dirname(log_path))}")
    print(f"Log file exists: {os.path.exists(log_path)}")
    
    # Configurar PlayerMonitor
    player_monitor = PlayerMonitor()
    
    def on_player_join(player_event):
        print(f"🎮 Jugador se unió: {player_event.player_name} en {player_event.server_name}")
    
    def on_player_left(player_event):
        print(f"🚪 Jugador se fue: {player_event.player_name} de {player_event.server_name}")
    
    def on_count_changed(server_name, count):
        print(f"📊 Conteo cambiado en {server_name}: {count} jugadores")
    
    # Registrar callbacks
    player_monitor.register_callback('join', on_player_join)
    player_monitor.register_callback('left', on_player_left)
    player_monitor.register_callback('count_changed', on_count_changed)
    
    # Agregar servidor y iniciar monitoreo
    if os.path.exists(os.path.dirname(log_path)):
        player_monitor.add_server(last_server, log_path)
        player_monitor.start_monitoring()
        
        print(f"✅ Monitoreo iniciado para {last_server}")
        print(f"Servidores monitoreados: {player_monitor.get_all_servers()}")
        print(f"Estado del monitoreo: {player_monitor.monitoring}")
        print(f"Conteo actual: {player_monitor.get_player_count(last_server)}")
        
        # Mantener el script corriendo por un momento
        import time
        print("Monitoreando por 10 segundos...")
        time.sleep(10)
        
        player_monitor.stop_monitoring()
        print("Monitoreo detenido")
    else:
        print(f"❌ Directorio de logs no existe: {os.path.dirname(log_path)}")

if __name__ == "__main__":
    main()