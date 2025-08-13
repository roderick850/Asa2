import configparser
import os
from pathlib import Path

# Ruta del archivo GameUserSettings.ini (según los logs de la aplicación)
gus_path = Path(r"D:\ASA\Prueba\ShooterGame\Saved\Config\WindowsServer\GameUserSettings.ini")

print("=== DEBUG FIELD MAPPINGS ===")
print(f"Archivo GameUserSettings.ini: {gus_path}")
print(f"Existe: {gus_path.exists()}")

if gus_path.exists():
    # Cargar archivo
    config = configparser.ConfigParser()
    config.optionxform = str  # Preservar mayúsculas/minúsculas
    
    try:
        config.read(gus_path, encoding='utf-8')
        
        print(f"\nSecciones encontradas: {list(config.sections())}")
        
        # Verificar sección ServerSettings específicamente
        if config.has_section('ServerSettings'):
            server_settings = dict(config.items('ServerSettings'))
            print(f"\n[ServerSettings] tiene {len(server_settings)} campos:")
            
            # Mostrar algunos campos específicos que deberían estar
            test_fields = [
                'MaxNumbersofPlayersInTribe',
                'MaxAlliancesPerTribe', 
                'TribeNameChangeCooldown',
                'AllianceNameChangeCooldown',
                'TamingSpeedMultiplier',
                'HarvestAmountMultiplier',
                'DifficultyOffset',
                'OverrideOfficialDifficulty'
            ]
            
            print("\nCampos específicos buscados:")
            for field in test_fields:
                if field in server_settings:
                    print(f"  ✅ {field} = {server_settings[field]}")
                else:
                    print(f"  ❌ {field} - NO ENCONTRADO")
            
            # Mostrar todos los campos que empiecen con 'Max' o 'Taming' o 'Harvest'
            print("\nCampos que empiezan con 'Max', 'Taming' o 'Harvest':")
            for key, value in server_settings.items():
                if key.startswith(('Max', 'Taming', 'Harvest')):
                    print(f"  {key} = {value}")
                    
        else:
            print("\n❌ Sección [ServerSettings] NO ENCONTRADA")
            
        # Mostrar todas las secciones y su contenido
        print("\n=== CONTENIDO COMPLETO ===")
        for section_name in config.sections():
            items = dict(config.items(section_name))
            print(f"\n[{section_name}] ({len(items)} campos):")
            for key, value in list(items.items())[:5]:  # Solo primeros 5
                print(f"  {key} = {value}")
            if len(items) > 5:
                print(f"  ... y {len(items) - 5} campos más")
                
    except Exception as e:
        print(f"Error al leer archivo: {e}")
else:
    print("❌ Archivo no existe")

print("\n=== FIN DEBUG ===")