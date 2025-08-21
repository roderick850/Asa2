#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager
from utils.logger import Logger
from utils.player_monitor import PlayerMonitor

def test_regex_patterns():
    """Probar los patrones regex con líneas de ejemplo"""
    print("=== PROBANDO PATRONES REGEX ===")
    
    # Patrones del PlayerMonitor
    join_pattern = re.compile(
        r'\[\d{2}:\d{2}:\d{2}\]\s*\[\d{2}:\d{2}:\d{2}\].*?:\s*(\w+)\s+\[UniqueNetId:([a-f0-9]+)\s+Platform:(\w+|None)\]\s+joined this ARK!'
    )
    left_pattern = re.compile(
        r'\[\d{2}:\d{2}:\d{2}\]\s*\[\d{2}:\d{2}:\d{2}\].*?:\s*(\w+)\s+\[UniqueNetId:([a-f0-9]+)\s+Platform:(\w+|None)\]\s+left this ARK!'
    )
    
    # Líneas de ejemplo basadas en el formato documentado
    test_lines = [
        "[16:24:46] [16:24:46] [2025.08.19-19.24.45:849][105]2025.08.19_19.24.45: Roderick850 [UniqueNetId:000288e061254539979667bfc309d848 Platform:None] joined this ARK!",
        "[16:25:30] [16:25:30] [2025.08.19-19.25.30:123][106]2025.08.19_19.25.30: TestPlayer [UniqueNetId:123456789abcdef0123456789abcdef01 Platform:Steam] joined this ARK!",
        "[16:30:15] [16:30:15] [2025.08.19-19.30.15:456][107]2025.08.19_19.30.15: Roderick850 [UniqueNetId:000288e061254539979667bfc309d848 Platform:None] left this ARK!"
    ]
    
    for i, line in enumerate(test_lines, 1):
        print(f"\nLínea {i}: {line[:80]}...")
        
        join_match = join_pattern.search(line)
        left_match = left_pattern.search(line)
        
        if join_match:
            player_name, unique_id, platform = join_match.groups()
            print(f"  ✅ JOIN detectado: {player_name} (ID: {unique_id[:8]}..., Platform: {platform})")
        elif left_match:
            player_name, unique_id, platform = left_match.groups()
            print(f"  ✅ LEFT detectado: {player_name} (ID: {unique_id[:8]}..., Platform: {platform})")
        else:
            print(f"  ❌ No se detectó evento")

def test_log_file_access():
    """Verificar acceso al archivo de log"""
    print("\n=== VERIFICANDO ARCHIVO DE LOG ===")
    
    config_manager = ConfigManager()
    root_path = config_manager.get("server", "root_path", "")
    last_server = config_manager.get("app", "last_server", "")
    
    if not root_path or not last_server:
        print("❌ No hay configuración de servidor")
        return None, None
    
    server_path = os.path.join(root_path, last_server)
    log_path = os.path.join(server_path, "ShooterGame", "Saved", "Logs", "ShooterGame.log")
    
    print(f"Servidor: {last_server}")
    print(f"Ruta del servidor: {server_path}")
    print(f"Ruta del log: {log_path}")
    print(f"Servidor existe: {os.path.exists(server_path)}")
    print(f"Directorio de logs existe: {os.path.exists(os.path.dirname(log_path))}")
    print(f"Archivo de log existe: {os.path.exists(log_path)}")
    
    if os.path.exists(log_path):
        try:
            stat = os.stat(log_path)
            print(f"Tamaño del archivo: {stat.st_size} bytes")
            print(f"Última modificación: {time.ctime(stat.st_mtime)}")
            
            # Leer las últimas 10 líneas
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                if lines:
                    print(f"\nÚltimas 5 líneas del log:")
                    for line in lines[-5:]:
                        print(f"  {line.strip()[:100]}...")
                else:
                    print("  El archivo está vacío")
                    
        except Exception as e:
            print(f"❌ Error leyendo archivo de log: {e}")
    
    return last_server, log_path

def test_player_monitor():
    """Probar el PlayerMonitor en tiempo real"""
    print("\n=== PROBANDO PLAYER MONITOR ===")
    
    server_name, log_path = test_log_file_access()
    if not server_name or not log_path or not os.path.exists(log_path):
        print("❌ No se puede probar PlayerMonitor sin archivo de log válido")
        return
    
    logger_instance = Logger()
    logger = logger_instance.setup_logger()
    
    player_monitor = PlayerMonitor(logger)
    
    # Callbacks de prueba
    def on_player_join(player_event):
        print(f"🎮 CALLBACK JOIN: {player_event.player_name} se unió a {player_event.server_name}")
    
    def on_player_left(player_event):
        print(f"🚪 CALLBACK LEFT: {player_event.player_name} salió de {player_event.server_name}")
    
    def on_count_changed(server_name, count):
        print(f"📊 CALLBACK COUNT: {server_name} tiene {count} jugadores")
    
    # Registrar callbacks
    player_monitor.register_callback('join', on_player_join)
    player_monitor.register_callback('left', on_player_left)
    player_monitor.register_callback('count_changed', on_count_changed)
    
    # Agregar servidor y iniciar monitoreo
    player_monitor.add_server(server_name, log_path)
    player_monitor.start_monitoring()
    
    print(f"✅ Monitoreo iniciado para {server_name}")
    print(f"Estado del monitoreo: {player_monitor.monitoring}")
    print(f"Servidores monitoreados: {player_monitor.get_all_servers()}")
    print(f"Conteo inicial: {player_monitor.get_player_count(server_name)}")
    
    # Simular líneas de log para probar
    print("\n=== SIMULANDO EVENTOS ===")
    test_lines = [
        "[16:24:46] [16:24:46] [2025.08.19-19.24.45:849][105]2025.08.19_19.24.45: TestPlayer1 [UniqueNetId:000288e061254539979667bfc309d848 Platform:Steam] joined this ARK!",
        "[16:25:30] [16:25:30] [2025.08.19-19.25.30:123][106]2025.08.19_19.25.30: TestPlayer2 [UniqueNetId:123456789abcdef0123456789abcdef01 Platform:None] joined this ARK!"
    ]
    
    for line in test_lines:
        print(f"Procesando: {line[:50]}...")
        player_monitor.process_log_line(server_name, line)
        time.sleep(1)
    
    print(f"\nConteo final: {player_monitor.get_player_count(server_name)}")
    print(f"Jugadores en línea: {player_monitor.get_online_players_list(server_name)}")
    
    # Monitorear por un momento
    print("\nMonitoreando archivo real por 10 segundos...")
    time.sleep(10)
    
    player_monitor.stop_monitoring()
    print("Monitoreo detenido")

def main():
    print("🔍 DIAGNÓSTICO DEL PLAYER MONITOR")
    print("=" * 50)
    
    # Probar patrones regex
    test_regex_patterns()
    
    # Verificar archivo de log
    test_log_file_access()
    
    # Probar PlayerMonitor
    test_player_monitor()
    
    print("\n✅ Diagnóstico completado")

if __name__ == "__main__":
    main()