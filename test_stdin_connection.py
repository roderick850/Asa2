import subprocess
import time
import os
import sys
from utils.config_manager import ConfigManager

def test_stdin_connection():
    """Prueba la conexión stdin del servidor ARK"""
    
    try:
        # Cargar configuración
        print("📋 Cargando configuración...")
        config = ConfigManager()
        
        # Obtener ruta del servidor desde la configuración
        server_name = config.get("app", "last_server", default="Prueba")
        print(f"🔍 Servidor actual: {server_name}")
        
        # Buscar la ruta del ejecutable del servidor
        server_path = config.get("server", f"executable_path_{server_name.lower()}")
        print(f"🔍 Ruta configurada: {server_path}")
        
        if not server_path:
            print(f"❌ Error: No se encontró configuración para el servidor '{server_name}'")
            print("📋 Configuraciones de ejecutables disponibles:")
            # Mostrar todas las configuraciones de ejecutables
            for key in config.config.options('server') if config.config.has_section('server') else []:
                if key.startswith('executable_path_'):
                    server_key = key.replace('executable_path_', '')
                    path = config.get('server', key)
                    print(f"  - {server_key}: {path}")
            return False
            
        if not os.path.exists(server_path):
            print(f"❌ Error: No se encontró el archivo del servidor en: {server_path}")
            return False
    
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        return False
    
    print(f"🔧 Usando servidor: {server_name}")
    print(f"📁 Ruta del servidor: {server_path}")
    
    # Configurar argumentos del servidor
    map_name = config.get("server", "current_map", default="TheIsland_WP")
    session_name = config.get("servers", f"{server_name}_session_name", default="TestServer")
    
    args = [
        f"{map_name}?listen?SessionName={session_name}",
        "-server",
        "-log"
    ]
    
    print(f"🗺️ Mapa: {map_name}")
    print(f"🏷️ Nombre de sesión: {session_name}")
    print(f"⚙️ Argumentos: {args}")
    
    try:
        # Iniciar el servidor con stdin habilitado
        print("\n🚀 Iniciando servidor con stdin habilitado...")
        
        server_dir = os.path.dirname(server_path)
        
        server = subprocess.Popen(
            [server_path] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=server_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE  # Mostrar consola del servidor
        )
        
        print(f"✅ Servidor iniciado con PID: {server.pid}")
        print("📝 Esperando que el servidor se inicialice...")
        
        # Esperar un poco para que el servidor se inicialice
        time.sleep(10)
        
        # Verificar si el proceso sigue ejecutándose
        if server.poll() is not None:
            print(f"❌ El servidor se detuvo inmediatamente. Código de salida: {server.poll()}")
            return False
        
        print("\n🎮 Servidor listo. Probando comandos...")
        
        # Crear archivo de comandos de prueba
        comandos_file = "test_commands.txt"
        
        # Lista de comandos de prueba
        test_commands = [
            "listplayers",
            "saveworld",
            "broadcast Prueba de conexión stdin"
        ]
        
        print("\n📋 Comandos de prueba:")
        for i, cmd in enumerate(test_commands, 1):
            print(f"  {i}. {cmd}")
        
        # Ejecutar comandos de prueba
        for i, cmd in enumerate(test_commands, 1):
            print(f"\n📤 Enviando comando {i}/{len(test_commands)}: {cmd}")
            
            try:
                server.stdin.write(cmd + "\n")
                server.stdin.flush()
                print(f"✅ Comando enviado exitosamente")
                
                # Esperar un poco entre comandos
                time.sleep(3)
                
                # Verificar si el proceso sigue ejecutándose
                if server.poll() is not None:
                    print(f"❌ El servidor se detuvo después del comando. Código: {server.poll()}")
                    break
                    
            except Exception as e:
                print(f"❌ Error enviando comando: {e}")
                break
        
        print("\n🔄 Prueba de bucle de comandos (como tu script original)...")
        
        # Simular el bucle de tu script original
        loop_count = 0
        max_loops = 6  # 30 segundos de prueba (5 segundos * 6)
        
        while loop_count < max_loops:
            # Crear archivo de comandos temporal
            with open(comandos_file, "w", encoding="utf-8") as f:
                f.write(f"broadcast Loop {loop_count + 1} - Prueba stdin\n")
            
            # Leer y procesar comandos
            if os.path.exists(comandos_file):
                with open(comandos_file, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                
                if lines:
                    for cmd in lines:
                        print(f"📤 Enviando desde archivo: {cmd}")
                        try:
                            server.stdin.write(cmd + "\n")
                            server.stdin.flush()
                            print(f"✅ Comando enviado")
                        except Exception as e:
                            print(f"❌ Error: {e}")
                            break
                    
                    # Limpiar archivo
                    open(comandos_file, "w").close()
            
            # Verificar estado del servidor
            if server.poll() is not None:
                print(f"❌ El servidor se detuvo. Código: {server.poll()}")
                break
            
            loop_count += 1
            print(f"⏳ Esperando... ({loop_count}/{max_loops})")
            time.sleep(5)
        
        print("\n🏁 Prueba completada")
        
        # Limpiar archivo de comandos
        if os.path.exists(comandos_file):
            os.remove(comandos_file)
        
        # Detener el servidor
        print("\n🛑 Deteniendo servidor...")
        try:
            server.stdin.write("quit\n")
            server.stdin.flush()
            server.wait(timeout=10)
        except:
            server.terminate()
            server.wait(timeout=5)
        
        print("✅ Prueba de stdin completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Iniciando prueba de conexión stdin del servidor ARK")
    print("=" * 60)
    
    success = test_stdin_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ RESULTADO: La conexión stdin funciona correctamente")
    else:
        print("❌ RESULTADO: Hay problemas con la conexión stdin")
    
    print("\n🔚 Fin del script")