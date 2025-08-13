import subprocess
import time
import os
import configparser
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    """Cargar configuración desde config.ini"""
    config = configparser.ConfigParser()
    config_path = "config.ini"
    
    if not os.path.exists(config_path):
        logger.error(f"Archivo de configuración no encontrado: {config_path}")
        return None
    
    config.read(config_path, encoding='utf-8')
    return config

def get_server_config(config):
    """Obtener configuración del servidor desde config.ini"""
    try:
        # Obtener el servidor actual desde la sección [app]
        server_name = config.get('app', 'last_server', fallback=None)
        if not server_name:
            logger.error("No se encontró 'last_server' en la configuración")
            return None, None, None
        
        # Obtener la ruta del ejecutable del servidor
        server_key = f"executable_path_{server_name.lower()}"
        server_path = config.get('server', server_key, fallback=None)
        
        if not server_path or not os.path.exists(server_path):
            logger.error(f"Ruta del servidor no válida: {server_path}")
            return None, None, None
        
        # Obtener el mapa actual
        current_map = config.get('app', 'last_map', fallback='TheIsland_WP')
        
        logger.info(f"Configuración cargada:")
        logger.info(f"  Servidor: {server_name}")
        logger.info(f"  Ejecutable: {server_path}")
        logger.info(f"  Mapa: {current_map}")
        
        return server_name, server_path, current_map
        
    except Exception as e:
        logger.error(f"Error al obtener configuración del servidor: {e}")
        return None, None, None

def build_server_args(config, map_name):
    """Construir argumentos del servidor basados en la configuración"""
    args = []
    
    # Mapa base
    if map_name:
        # Mapear nombres amigables a identificadores técnicos
        map_mapping = {
            'The Island': 'TheIsland_WP',
            'The Center': 'TheCenter_WP', 
            'Scorched Earth': 'ScorchedEarth_WP',
            'Ragnarok': 'Ragnarok_WP',
            'Aberration': 'Aberration_WP',
            'Extinction': 'Extinction_WP',
            'Genesis': 'Genesis_WP',
            'Genesis 2': 'Gen2_WP',
            'Crystal Isles': 'CrystalIsles_WP',
            'Lost Island': 'LostIsland_WP',
            'Fjordur': 'Fjordur_WP',
            'Valguero': 'Valguero_WP'
        }
        
        technical_map = map_mapping.get(map_name, map_name)
        args.append(f"{technical_map}?listen?SessionName=MiServidor")
    
    # Argumentos básicos del servidor
    args.extend(["-server", "-log"])
    
    # Agregar argumentos adicionales desde la configuración si existen
    try:
        if config.has_section('server_args'):
            for key, value in config.items('server_args'):
                if value.strip():
                    args.append(f"-{key}={value}")
    except Exception as e:
        logger.warning(f"Error al cargar argumentos adicionales: {e}")
    
    return args

def start_server_with_stdin(server_path, args):
    """Iniciar el servidor con stdin habilitado"""
    try:
        logger.info(f"Iniciando servidor: {server_path}")
        logger.info(f"Argumentos: {' '.join(args)}")
        
        # Iniciar el servidor con stdin habilitado
        server = subprocess.Popen(
            [server_path] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=os.path.dirname(server_path)
        )
        
        logger.info(f"Servidor iniciado con PID: {server.pid}")
        
        # Esperar un momento para que el servidor se inicialice
        logger.info("Esperando 10 segundos para que el servidor se inicialice...")
        time.sleep(10)
        
        # Verificar si el servidor sigue ejecutándose
        if server.poll() is not None:
            logger.error(f"El servidor se detuvo durante la inicialización con código: {server.poll()}")
            return None
        
        logger.info("Servidor inicializado correctamente")
        return server
        
    except Exception as e:
        logger.error(f"Error al iniciar servidor: {e}")
        return None

def monitor_commands_file(server, commands_file="comandos.txt"):
    """Monitorear archivo de comandos y enviarlos al servidor"""
    logger.info(f"Monitoreando archivo de comandos: {commands_file}")
    
    while True:
        try:
            if os.path.exists(commands_file):
                with open(commands_file, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                
                if lines:
                    logger.info(f"Encontrados {len(lines)} comandos para enviar")
                    for cmd in lines:
                        logger.info(f"Enviando comando: {cmd}")
                        server.stdin.write(cmd + "\n")
                        server.stdin.flush()
                    
                    # Limpiar el archivo después de procesar los comandos
                    open(commands_file, "w").close()
                    logger.info("Archivo de comandos limpiado")
            
            # Verificar si el servidor sigue ejecutándose
            if server.poll() is not None:
                logger.error(f"El servidor se detuvo con código: {server.poll()}")
                break
            
            time.sleep(5)  # Revisar cada 5 segundos
            
        except KeyboardInterrupt:
            logger.info("Deteniendo monitoreo por interrupción del usuario")
            break
        except Exception as e:
            logger.error(f"Error en monitoreo de comandos: {e}")
            time.sleep(5)

def main():
    """Función principal"""
    logger.info("=== Iniciando Fix de Conexión STDIN ===")
    
    # Cargar configuración
    config = load_config()
    if not config:
        logger.error("No se pudo cargar la configuración")
        return
    
    # Obtener configuración del servidor
    server_name, server_path, map_name = get_server_config(config)
    if not server_path:
        logger.error("No se pudo obtener la configuración del servidor")
        return
    
    # Construir argumentos del servidor
    args = build_server_args(config, map_name)
    
    # Iniciar servidor con stdin
    server = start_server_with_stdin(server_path, args)
    if not server:
        logger.error("No se pudo iniciar el servidor")
        return
    
    logger.info("Servidor iniciado exitosamente con stdin habilitado")
    logger.info("Para enviar comandos, escriba los comandos en el archivo 'comandos.txt'")
    logger.info("Presione Ctrl+C para detener")
    
    try:
        # Monitorear archivo de comandos
        monitor_commands_file(server)
    except KeyboardInterrupt:
        logger.info("Deteniendo servidor...")
    finally:
        if server and server.poll() is None:
            server.terminate()
            logger.info("Servidor detenido")

if __name__ == "__main__":
    main()