import configparser
import os
from pathlib import Path

# Ruta del archivo GameUserSettings.ini
gus_path = Path(r"D:\ASA\Prueba\ShooterGame\Saved\Config\WindowsServer\GameUserSettings.ini")

# Campos que deberían estar en GameUserSettings.ini según default_values
expected_gus_fields = {
    # De default_values en ini_config_panel.py - [ServerSettings]
    "MaxNumbersofPlayersInTribe": "10",
    "MaxAlliancesPerTribe": "10", 
    "MaxTribeLogs": "100",
    "PreventTribeAlliances": "False",
    "TribeNameChangeCooldown": "15.0",
    "AllowAnyoneBabyImprintCuddle": "False",
    "PreventMateBoost": "False",
    "MaxTamedDinos": "5000",
    "MaxTamedDinos_SoftTameLimit": "4000",
    "MaxTamedDinos_SoftTameLimit_CountdownForDeletionDuration": "604800.0",
    "MaxPersonalTamedDinos": "500",
    "DifficultyOffset": "1.0",
    "OverrideOfficialDifficulty": "5.0",
    "XPMultiplier": "1.0",
    "TamingSpeedMultiplier": "1.0",
    "DinoCountMultiplier": "1.0",
    "HarvestAmountMultiplier": "1.0",
    "HarvestHealthMultiplier": "1.0",
    "PlayerHarvestingDamageMultiplier": "1.0",
    "DinoHarvestingDamageMultiplier": "1.0",
    "ResourcesRespawnPeriodMultiplier": "1.0",
    "ResourceNoReplenishRadiusPlayers": "1.0",
    "ResourceNoReplenishRadiusStructures": "1.0",
    "CropGrowthSpeedMultiplier": "1.0",
    "CropDecaySpeedMultiplier": "1.0",
    "PoopIntervalMultiplier": "1.0",
    "MatingIntervalMultiplier": "1.0",
    "LayEggIntervalMultiplier": "1.0",
    "BabyMatureSpeedMultiplier": "1.0",
    "BabyFoodConsumptionSpeedMultiplier": "1.0",
    "PlayerCharacterWaterDrainMultiplier": "1.0",
    "PlayerCharacterFoodDrainMultiplier": "1.0",
    "DinoCharacterFoodDrainMultiplier": "1.0",
    "PlayerCharacterStaminaDrainMultiplier": "1.0",
    "DinoCharacterStaminaDrainMultiplier": "1.0",
    "PlayerCharacterHealthRecoveryMultiplier": "1.0",
    "DinoCharacterHealthRecoveryMultiplier": "1.0",
    "ServerPVE": "False",
    "ServerHardcore": "False",
    "ServerCrosshair": "True",
    "ShowMapPlayerLocation": "True",
    "ShowFloatingDamageText": "True",
    "AllowHitMarkers": "True",
    "DayCycleSpeedScale": "1.0",
    "NightTimeSpeedScale": "1.0",
    "DayTimeSpeedScale": "1.0"
}

print("=== DEBUG CAMPOS FALTANTES ===\n")
print(f"Archivo GameUserSettings.ini: {gus_path}")
print(f"Existe: {gus_path.exists()}\n")

if gus_path.exists():
    # Cargar archivo actual
    config = configparser.ConfigParser()
    config.optionxform = str  # Preservar mayúsculas/minúsculas
    
    try:
        config.read(gus_path, encoding='utf-8')
        
        print(f"Secciones encontradas: {list(config.sections())}\n")
        
        # Verificar qué campos faltan en [ServerSettings]
        missing_fields = []
        present_fields = []
        
        if config.has_section('ServerSettings'):
            server_settings = dict(config.items('ServerSettings'))
            print(f"[ServerSettings] tiene {len(server_settings)} campos\n")
            
            for field_name, expected_value in expected_gus_fields.items():
                if field_name in server_settings:
                    present_fields.append(field_name)
                    actual_value = server_settings[field_name]
                    print(f"✅ {field_name} = {actual_value} (esperado: {expected_value})")
                else:
                    missing_fields.append(field_name)
                    print(f"❌ {field_name} - FALTANTE (esperado: {expected_value})")
        else:
            print("❌ Sección [ServerSettings] no existe")
            missing_fields = list(expected_gus_fields.keys())
        
        print(f"\n📊 RESUMEN:")
        print(f"   Campos presentes: {len(present_fields)}/{len(expected_gus_fields)}")
        print(f"   Campos faltantes: {len(missing_fields)}")
        
        if missing_fields:
            print(f"\n❌ CAMPOS FALTANTES:")
            for field in missing_fields:
                print(f"   - {field}")
        
        # Verificar si hay campos duplicados en otras secciones
        print(f"\n🔍 BUSCANDO CAMPOS EN OTRAS SECCIONES:")
        for field_name in missing_fields:
            found_elsewhere = False
            for section_name in config.sections():
                if section_name != 'ServerSettings' and field_name in config[section_name]:
                    value = config[section_name][field_name]
                    print(f"   ⚠️ {field_name} encontrado en [{section_name}] = {value}")
                    found_elsewhere = True
            
            if not found_elsewhere:
                print(f"   ❌ {field_name} no encontrado en ninguna sección")
                
    except Exception as e:
        print(f"❌ Error al leer el archivo: {e}")
else:
    print("❌ El archivo no existe")

print("\n=== FIN DEBUG CAMPOS FALTANTES ===")