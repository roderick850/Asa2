"""
Utilidad para limpiar archivos INI con opciones duplicadas
"""
import os
import configparser
from collections import OrderedDict


def clean_duplicate_options(ini_file_path, backup=True):
    """
    Limpia opciones duplicadas de un archivo INI
    
    Args:
        ini_file_path (str): Ruta al archivo INI
        backup (bool): Si crear un backup antes de limpiar
    
    Returns:
        bool: True si se limpiaron duplicados, False si no había duplicados o error
    """
    if not os.path.exists(ini_file_path):
        return False
    
    try:
        # Crear backup si se solicita
        if backup:
            backup_path = ini_file_path + '.backup'
            with open(ini_file_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
        
        # Leer archivo línea por línea y eliminar duplicados
        with open(ini_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        cleaned_lines = []
        current_section = None
        seen_options = {}
        duplicates_found = False
        
        for line in lines:
            stripped_line = line.strip()
            
            # Detectar nueva sección
            if stripped_line.startswith('[') and stripped_line.endswith(']'):
                current_section = stripped_line
                seen_options[current_section] = set()
                cleaned_lines.append(line)
                continue
            
            # Procesar opciones
            if '=' in stripped_line and not stripped_line.startswith(';') and not stripped_line.startswith('#'):
                option_name = stripped_line.split('=')[0].strip().lower()
                
                if current_section and option_name in seen_options[current_section]:
                    # Opción duplicada encontrada - omitir
                    duplicates_found = True
                    print(f"Eliminando duplicado: {option_name} en {current_section}")
                    continue
                else:
                    # Primera vez que vemos esta opción en esta sección
                    if current_section:
                        seen_options[current_section].add(option_name)
            
            cleaned_lines.append(line)
        
        # Escribir archivo limpio solo si encontramos duplicados
        if duplicates_found:
            with open(ini_file_path, 'w', encoding='utf-8') as f:
                f.writelines(cleaned_lines)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error al limpiar archivo INI: {e}")
        return False


def clean_gameusersettings_for_server(server_path, server_name):
    """
    Limpia el archivo GameUserSettings.ini específico de un servidor
    
    Args:
        server_path (str): Ruta base de los servidores
        server_name (str): Nombre del servidor
        
    Returns:
        bool: True si se limpió el archivo exitosamente
    """
    gameusersettings_path = os.path.join(
        server_path,
        server_name,
        "ShooterGame",
        "Saved",
        "Config",
        "WindowsServer",
        "GameUserSettings.ini"
    )
    
    if os.path.exists(gameusersettings_path):
        result = clean_duplicate_options(gameusersettings_path)
        if result:
            print(f"Archivo limpiado: {gameusersettings_path}")
        return result
    else:
        print(f"Archivo no encontrado: {gameusersettings_path}")
        return False


if __name__ == "__main__":
    # Ejemplo de uso
    clean_gameusersettings_for_server("D:/ASA", "Prueba")
