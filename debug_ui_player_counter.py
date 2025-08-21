#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import traceback
from datetime import datetime

# Detectar si estamos ejecutando desde un ejecutable compilado
def is_compiled():
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

# Buscar el directorio de desarrollo que contiene la carpeta utils
def find_development_directory():
    """Buscar el directorio que contiene la carpeta utils"""
    possible_paths = [
        # Directorio del script actual
        os.path.dirname(os.path.abspath(__file__)),
        # Directorio padre del script
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        # Rutas comunes de desarrollo
        r"c:\Users\roder\OneDrive\Desktop\Nuevacarpeta\Asa2",
        r"C:\Users\roder\OneDrive\Desktop\Nuevacarpeta\Asa2",
        # Directorio actual
        os.getcwd(),
        # Directorio padre del actual
        os.path.dirname(os.getcwd())
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.path.exists(os.path.join(path, 'utils')):
            return path
    
    return None

# Configurar paths según el entorno
if is_compiled():
    # Ejecutable compilado - usar directorio del ejecutable
    script_dir = os.path.dirname(sys.executable)
    # Los módulos están incluidos en el ejecutable
    sys.path.insert(0, sys._MEIPASS)
    development_dir = None
else:
    # Desarrollo - buscar directorio que contiene utils
    script_dir = os.path.dirname(os.path.abspath(__file__))
    development_dir = find_development_directory()
    
    if development_dir and development_dir != os.getcwd():
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📁 Cambiando directorio de trabajo...")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📂 Desde: {os.getcwd()}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📂 Hacia: {development_dir}")
        os.chdir(development_dir)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Directorio cambiado correctamente")
    
    # Agregar el directorio de desarrollo al path
    if development_dir:
        sys.path.insert(0, development_dir)
    sys.path.insert(0, script_dir)
    sys.path.insert(0, os.getcwd())

def log_message(message):
    """Función para logging con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    
def wait_for_input():
    """Esperar entrada del usuario para mantener consola abierta"""
    try:
        input("\n\n=== Presiona ENTER para cerrar la consola ===")
    except:
        time.sleep(30)  # Fallback si input() falla

def main():
    """Función principal de debug"""
    log_message("🚀 INICIANDO DEBUG UI PLAYER COUNTER")
    log_message("=" * 60)
    
    try:
        # Verificar entorno de ejecución
        if is_compiled():
            log_message("🔧 Ejecutando desde ejecutable compilado")
            log_message(f"📁 Directorio del ejecutable: {script_dir}")
        else:
            log_message("🔧 Ejecutando en modo desarrollo")
            log_message(f"📁 Directorio actual: {os.getcwd()}")
            log_message(f"📄 Script ubicado en: {script_dir}")
            
            if development_dir:
                log_message(f"📂 Directorio de desarrollo encontrado: {development_dir}")
            
            # Verificar que existe la carpeta utils
            utils_path = os.path.join(os.getcwd(), 'utils')
            if not os.path.exists(utils_path):
                log_message(f"❌ ERROR: No se encuentra la carpeta 'utils' en {os.getcwd()}")
                
                # Intentar buscar en el directorio de desarrollo
                if development_dir:
                    dev_utils_path = os.path.join(development_dir, 'utils')
                    if os.path.exists(dev_utils_path):
                        log_message(f"✅ Carpeta 'utils' encontrada en directorio de desarrollo: {dev_utils_path}")
                        os.chdir(development_dir)
                        log_message(f"📁 Cambiado a directorio de desarrollo: {development_dir}")
                    else:
                        log_message("💡 SOLUCIÓN: Copia el script al directorio de desarrollo del proyecto")
                        log_message(f"💡 Directorio correcto: c:\\Users\\roder\\OneDrive\\Desktop\\Nuevacarpeta\\Asa2")
                        return
                else:
                    log_message("💡 SOLUCIÓN: Copia el script al directorio de desarrollo del proyecto")
                    log_message(f"💡 Directorio correcto: c:\\Users\\roder\\OneDrive\\Desktop\\Nuevacarpeta\\Asa2")
                    return
            else:
                log_message(f"✅ Carpeta 'utils' encontrada en: {utils_path}")
        
        # Importar módulos necesarios
        log_message("📦 Importando módulos...")
        try:
            from utils.config_manager import ConfigManager
            from utils.logger import Logger
            from utils.player_monitor import PlayerMonitor
            log_message("✅ Módulos importados correctamente")
        except ImportError as e:
            log_message(f"❌ ERROR DE IMPORTACIÓN: {e}")
            if is_compiled():
                log_message("💡 Los módulos deberían estar incluidos en el ejecutable")
                log_message("💡 Verifica que el ejecutable se compiló correctamente")
            else:
                log_message("💡 Copia este script al directorio de desarrollo:")
                log_message("💡 c:\\Users\\roder\\OneDrive\\Desktop\\Nuevacarpeta\\Asa2")
            return
        
        # Inicializar componentes
        log_message("🔧 Inicializando componentes...")
        logger_instance = Logger()
        logger = logger_instance.setup_logger()
        config_manager = ConfigManager()
        log_message("✅ Componentes inicializados")
        
        # Obtener configuración
        log_message("📋 Obteniendo configuración...")
        root_path = config_manager.get("server", "root_path", "")
        last_server = config_manager.get("app", "last_server", "")
        
        log_message(f"📁 Root path: {root_path}")
        log_message(f"🖥️ Last server: {last_server}")
        
        if not root_path:
            log_message("❌ ERROR: No hay root_path configurado")
            log_message("💡 SOLUCIÓN: Configura la ruta de servidores en la aplicación")
            wait_for_input()
            return
            
        if not last_server:
            log_message("❌ ERROR: No hay servidor seleccionado")
            log_message("💡 SOLUCIÓN: Selecciona un servidor en la aplicación")
            wait_for_input()
            return
        
        # Verificar rutas
        log_message("🔍 Verificando rutas...")
        server_path = os.path.join(root_path, last_server)
        log_path = os.path.join(server_path, "ShooterGame", "Saved", "Logs", "ShooterGame.log")
        log_dir = os.path.dirname(log_path)
        
        log_message(f"📂 Server path: {server_path}")
        log_message(f"📄 Log path: {log_path}")
        log_message(f"📁 Log directory: {log_dir}")
        
        log_message(f"✅ Server path exists: {os.path.exists(server_path)}")
        log_message(f"✅ Log directory exists: {os.path.exists(log_dir)}")
        log_message(f"✅ Log file exists: {os.path.exists(log_path)}")
        
        if os.path.exists(log_path):
            stat = os.stat(log_path)
            mod_time = datetime.fromtimestamp(stat.st_mtime)
            size_mb = stat.st_size / (1024 * 1024)
            log_message(f"📊 Log file size: {size_mb:.2f} MB")
            log_message(f"🕒 Log file modified: {mod_time}")
        
        if not os.path.exists(log_dir):
            log_message("❌ ERROR: Directorio de logs no existe")
            log_message(f"💡 SOLUCIÓN: Verifica que el servidor {last_server} esté correctamente configurado")
            wait_for_input()
            return
        
        # Configurar PlayerMonitor
        log_message("🎮 Configurando PlayerMonitor...")
        player_monitor = PlayerMonitor()
        
        # Simular la configuración de MainWindow
        class MockServerPanel:
            def __init__(self, server_name):
                self.selected_server = server_name
                log_message(f"🎯 MockServerPanel creado para: {server_name}")
        
        class MockMainWindow:
            def __init__(self, server_name):
                self.server_panel = MockServerPanel(server_name)
                self.player_monitor = player_monitor
                self.logger = logger
                log_message(f"🏠 MockMainWindow creado")
                
            def update_player_counts(self):
                """Simular el método update_player_counts de MainWindow"""
                try:
                    log_message("📊 === ACTUALIZANDO CONTADORES ===")
                    
                    # Obtener conteo del servidor actual
                    current_server = getattr(self.server_panel, 'selected_server', None) if hasattr(self, 'server_panel') else None
                    current_count = 0
                    total_count = 0
                    
                    log_message(f"🔍 current_server = {current_server}")
                    
                    if current_server:
                        current_count = self.player_monitor.get_player_count(current_server)
                        log_message(f"🔍 current_count = {current_count}")
                    
                    # Obtener conteo total de todos los servidores
                    all_servers = self.player_monitor.get_all_servers()
                    log_message(f"🔍 all_servers = {all_servers}")
                    
                    for server in all_servers:
                        server_count = self.player_monitor.get_player_count(server)
                        total_count += server_count
                        log_message(f"🔍 {server} tiene {server_count} jugadores")
                    
                    log_message(f"📊 RESULTADO: Servidor actual: {current_count}, Total cluster: {total_count}")
                    log_message(f"🎯 UI debería mostrar: 👥 {current_count} y 🌐 {total_count}")
                    
                    # Mostrar jugadores en línea
                    if hasattr(self.player_monitor, 'online_players'):
                        online_players = self.player_monitor.online_players
                        log_message(f"👥 Jugadores en línea por servidor:")
                        for server_name, players in online_players.items():
                            log_message(f"   🖥️ {server_name}: {len(players)} jugadores")
                            for player_name in players.keys():
                                log_message(f"      👤 {player_name}")
                    
                    log_message("📊 === FIN ACTUALIZACIÓN ===")
                    
                except Exception as e:
                    log_message(f"❌ ERROR actualizando conteos: {e}")
                    log_message(f"🔍 Traceback: {traceback.format_exc()}")
        
        # Crear mock de MainWindow
        log_message("🏗️ Creando MockMainWindow...")
        mock_main = MockMainWindow(last_server)
        
        # Configurar callbacks
        log_message("🔗 Configurando callbacks...")
        
        def on_player_join(player_event):
            log_message(f"🎮 CALLBACK JOIN: {player_event.player_name} se unió a {player_event.server_name}")
            log_message(f"   📅 Timestamp: {player_event.timestamp}")
            log_message(f"   🆔 Unique ID: {player_event.unique_id}")
            log_message(f"   🎮 Platform: {player_event.platform}")
            mock_main.update_player_counts()
        
        def on_player_left(player_event):
            log_message(f"🚪 CALLBACK LEFT: {player_event.player_name} salió de {player_event.server_name}")
            log_message(f"   📅 Timestamp: {player_event.timestamp}")
            log_message(f"   🆔 Unique ID: {player_event.unique_id}")
            log_message(f"   🎮 Platform: {player_event.platform}")
            mock_main.update_player_counts()
        
        def on_count_changed(server_name, count):
            log_message(f"📊 CALLBACK COUNT: {server_name} tiene {count} jugadores")
            mock_main.update_player_counts()
        
        # Registrar callbacks
        player_monitor.register_callback('join', on_player_join)
        player_monitor.register_callback('left', on_player_left)
        player_monitor.register_callback('count_changed', on_count_changed)
        log_message("✅ Callbacks registrados")
        
        # Configurar monitoreo
        log_message("🚀 Iniciando monitoreo...")
        player_monitor.add_server(last_server, log_path)
        player_monitor.start_monitoring()
        
        log_message(f"✅ Monitoreo iniciado para {last_server}")
        log_message(f"🔍 Estado del monitoreo: {player_monitor.monitoring}")
        log_message(f"🔍 Servidores monitoreados: {player_monitor.get_all_servers()}")
        
        # Estado inicial
        log_message("\n🔍 === ESTADO INICIAL ===")
        mock_main.update_player_counts()
        
        # Simular eventos para probar
        log_message("\n🧪 === SIMULANDO EVENTOS DE PRUEBA ===")
        test_lines = [
            "[16:24:46] [16:24:46] [2025.08.19-19.24.45:849][105]2025.08.19_19.24.45: TestPlayer1 joined this ARK! (Steam)",
            "[16:25:30] [16:25:30] [2025.08.19-19.25.30:123][106]2025.08.19_19.25.30: TestPlayer2 joined this ARK! (Steam)",
            "[16:26:15] [16:26:15] [2025.08.19-19.26.15:456][107]2025.08.19_19.26.15: TestPlayer1 left this ARK! (Steam)"
        ]
        
        for i, line in enumerate(test_lines, 1):
            log_message(f"🧪 Procesando evento de prueba {i}/3: {line[:50]}...")
            if hasattr(player_monitor, '_process_log_line'):
                player_monitor._process_log_line(last_server, line)
            else:
                log_message("⚠️ Método _process_log_line no disponible")
            time.sleep(2)
        
        log_message("\n📊 === ESTADO DESPUÉS DE SIMULACIÓN ===")
        mock_main.update_player_counts()
        
        # Monitorear archivo real
        log_message("\n🔄 === MONITOREANDO ARCHIVO REAL ===")
        log_message("⏰ Monitoreando por 30 segundos...")
        log_message("💡 Si hay jugadores conectándose/desconectándose, deberías ver los eventos aquí")
        
        start_time = time.time()
        while time.time() - start_time < 30:
            remaining = int(30 - (time.time() - start_time))
            if remaining % 5 == 0:  # Mostrar cada 5 segundos
                log_message(f"⏳ Tiempo restante: {remaining} segundos")
                mock_main.update_player_counts()
            time.sleep(1)
        
        log_message("\n📊 === ESTADO FINAL ===")
        mock_main.update_player_counts()
        
        # Detener monitoreo
        log_message("🛑 Deteniendo monitoreo...")
        player_monitor.stop_monitoring()
        log_message("✅ Monitoreo detenido")
        
        log_message("\n🎉 === DEBUG COMPLETADO EXITOSAMENTE ===")
        
    except ImportError as e:
        log_message(f"❌ ERROR DE IMPORTACIÓN: {e}")
        log_message("💡 SOLUCIÓN: Verifica que estés ejecutando el script desde el directorio correcto")
        log_message(f"📁 Directorio actual: {os.getcwd()}")
        log_message(f"📄 Script ubicado en: {os.path.dirname(os.path.abspath(__file__))}")
        
    except Exception as e:
        log_message(f"❌ ERROR INESPERADO: {e}")
        log_message(f"🔍 Traceback completo:")
        log_message(traceback.format_exc())
        
    finally:
        log_message("\n" + "=" * 60)
        log_message("🏁 FIN DEL DEBUG")
        wait_for_input()

if __name__ == "__main__":
    main()