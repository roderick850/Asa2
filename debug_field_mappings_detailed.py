import configparser
import os
from pathlib import Path

# Ruta del archivo GameUserSettings.ini (según los logs de la aplicación)
gus_path = Path(r"D:\ASA\Prueba\ShooterGame\Saved\Config\WindowsServer\GameUserSettings.ini")

print("=== DEBUG FIELD MAPPINGS DETALLADO ===")
print(f"Archivo GameUserSettings.ini: {gus_path}")
print(f"Existe: {gus_path.exists()}")

if gus_path.exists():
    # Cargar archivo
    config = configparser.ConfigParser()
    config.optionxform = str  # Preservar mayúsculas/minúsculas
    
    try:
        config.read(gus_path, encoding='utf-8')
        
        print(f"\nSecciones encontradas: {list(config.sections())}")
        
        # Campos específicos que deberían estar en GameUserSettings
        test_fields = [
            'MaxNumbersofPlayersInTribe',
            'MaxAlliancesPerTribe', 
            'TribeNameChangeCooldown',
            'AllianceNameChangeCooldown',
            'TamingSpeedMultiplier',
            'HarvestAmountMultiplier',
            'DifficultyOffset',
            'OverrideOfficialDifficulty',
            'XPMultiplier',
            'PlayerCharacterWaterDrainMultiplier',
            'DinoCharacterFoodDrainMultiplier'
        ]
        
        print("\n🔍 BUSCANDO CAMPOS EN TODAS LAS SECCIONES:")
        
        # Buscar cada campo en todas las secciones
        for field in test_fields:
            found = False
            for section_name in config.sections():
                section = config[section_name]
                if field in section:
                    print(f"  ✅ {field} encontrado en [{section_name}] = {section[field]}")
                    found = True
                    break
            
            if not found:
                print(f"  ❌ {field} - NO ENCONTRADO en ninguna sección")
        
        print("\n📊 RESUMEN POR SECCIÓN:")
        total_fields = 0
        for section_name in config.sections():
            section = config[section_name]
            field_count = len(section)
            total_fields += field_count
            print(f"  [{section_name}]: {field_count} campos")
            
            # Si es ServerSettings, mostrar todos los campos
            if section_name == 'ServerSettings':
                if field_count > 0:
                    print("    Campos en ServerSettings:")
                    for key, value in section.items():
                        print(f"      {key} = {value}")
                else:
                    print("    ⚠️ ServerSettings está vacía")
        
        print(f"\n📈 Total de campos en el archivo: {total_fields}")
        
        # Buscar campos que contengan palabras clave
        print("\n🔎 CAMPOS QUE CONTIENEN PALABRAS CLAVE:")
        keywords = ['Max', 'Taming', 'Harvest', 'Multiplier', 'Tribe', 'Player']
        
        for section_name in config.sections():
            section = config[section_name]
            matching_fields = []
            
            for key in section.keys():
                for keyword in keywords:
                    if keyword.lower() in key.lower():
                        matching_fields.append(f"{key} = {section[key]}")
                        break
            
            if matching_fields:
                print(f"\n  [{section_name}]:")
                for field in matching_fields[:10]:  # Mostrar máximo 10
                    print(f"    {field}")
                if len(matching_fields) > 10:
                    print(f"    ... y {len(matching_fields) - 10} campos más")
                    
    except Exception as e:
        print(f"Error al leer archivo: {e}")
else:
    print("❌ Archivo no existe")

print("\n=== FIN DEBUG DETALLADO ===")