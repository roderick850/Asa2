#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para identificar campos duplicados entre GameUserSettings.ini y Game.ini
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.panels.ini_config_panel import IniConfigPanel
import configparser

def analyze_duplicate_fields():
    """Analizar campos duplicados entre GameUserSettings.ini y Game.ini"""
    
    print("=== ANÁLISIS DE CAMPOS DUPLICADOS ===")
    print("Comparando definiciones entre GameUserSettings.ini y Game.ini\n")
    
    try:
        
        # Obtener campos de GameUserSettings.ini
        gus_fields = set()
        gus_categories = {
            "PlayersAndTribes": [
                "MaxNumbersofPlayersInTribe", "MaxAlliancesPerTribe", "MaxTribeLogs", 
                "PreventTribeAlliances", "TribeNameChangeCooldown", "AllowAnyoneBabyImprintCuddle",
                "PreventMateBoost", "MaxTamedDinos", "MaxTamedDinos_SoftTameLimit", 
                "MaxTamedDinos_SoftTameLimit_CountdownForDeletionDuration", "MaxPersonalTamedDinos"
            ],
            "DifficultyAndProgression": [
                "DifficultyOffset", "OverrideOfficialDifficulty", "XPMultiplier", "TamingSpeedMultiplier",
                "DinoCountMultiplier"
            ],
            "HarvestingAndResources": [
                "HarvestAmountMultiplier", "HarvestHealthMultiplier", "PlayerHarvestingDamageMultiplier",
                "DinoHarvestingDamageMultiplier", "ResourcesRespawnPeriodMultiplier", 
                "ResourceNoReplenishRadiusPlayers", "ResourceNoReplenishRadiusStructures",
                "StructurePreventResourceRadiusMultiplier", "UseOptimizedHarvestingHealth",
                "ClampResourceHarvestDamage", "CropGrowthSpeedMultiplier", "CropDecaySpeedMultiplier",
                "PoopIntervalMultiplier", "HairGrowthSpeedMultiplier"
            ],
            "BreedingAndReproduction": [
                "BabyImprintingStatScaleMultiplier", "BabyImprintAmountMultiplier", "BabyMatureSpeedMultiplier",
                "BabyCuddleIntervalMultiplier", "BabyCuddleGracePeriodMultiplier",
                "BabyCuddleLoseImprintQualitySpeedMultiplier", "BabyFoodConsumptionSpeedMultiplier",
                "DisableImprintDinoBuff"
            ],
            "TamingAndDinos": [
                "PassiveTameIntervalMultiplier", "bAllowTamedDinoRiding", "bDisableDinoRiding",
                "bDisableDinoTaming", "bUseTameLimitForStructuresOnly", "bForceCanRideFliers",
                "ForceAllowCaveFlyers", "AllowFlyingStaminaRecovery", "bAllowFlyerCarryPvE",
                "bFlyerPlatformAllowUnalignedDinoBasing", "TamedDinoCharacterFoodDrainMultiplier",
                "TamedDinoTorporDrainMultiplier", "WildDinoCharacterFoodDrainMultiplier",
                "WildDinoTorporDrainMultiplier", "DinoCharacterFoodDrainMultiplier",
                "DinoCharacterStaminaDrainMultiplier", "DinoCharacterHealthRecoveryMultiplier",
                "PlayerCharacterWaterDrainMultiplier", "PlayerCharacterFoodDrainMultiplier",
                "PlayerCharacterStaminaDrainMultiplier", "PlayerCharacterHealthRecoveryMultiplier",
                "RaidDinoCharacterFoodDrainMultiplier"
            ]
        }
        
        # Obtener campos de Game.ini
        game_categories = {
            "ExperienceAndLevels": [
                "LevelExperienceRampOverrides", "OverrideMaxExperiencePointsPlayer", 
                "OverrideMaxExperiencePointsDino", "TamedDinoCharacterLevelCount", "CraftXPMultiplier",
                "GenericXPMultiplier", "HarvestXPMultiplier", "KillXPMultiplier", "SpecialXPMultiplier",
                "TamedDinoXPMultiplier"
            ],
            "StatsAndMultipliers": [
                "PerLevelStatsMultiplier_Player[7]", "PerLevelStatsMultiplier_DinoTamed[7]",
                "DinoTurretDamageMultiplier"
            ],
            "BreedingAndReproduction": [
                "MatingIntervalMultiplier", "MatingSpeedMultiplier", "LayEggIntervalMultiplier",
                "EggHatchSpeedMultiplier"
            ],
            "TamingAndDinos": [
                "TamedDinoRidingWaitTime", "bAllowFlyerSpeedLeveling"
            ]
        }
        
        # Recopilar todos los campos de cada archivo
        all_gus_fields = set()
        for category, fields in gus_categories.items():
            all_gus_fields.update(fields)
            
        all_game_fields = set()
        for category, fields in game_categories.items():
            all_game_fields.update(fields)
            
        # Encontrar duplicados
        duplicates = all_gus_fields.intersection(all_game_fields)
        
        print(f"📊 RESUMEN:")
        print(f"   Campos en GameUserSettings.ini: {len(all_gus_fields)}")
        print(f"   Campos en Game.ini: {len(all_game_fields)}")
        print(f"   Campos duplicados: {len(duplicates)}\n")
        
        if duplicates:
            print("🔄 CAMPOS DUPLICADOS ENCONTRADOS:")
            print("=" * 50)
            
            for field in sorted(duplicates):
                # Encontrar en qué categorías aparece cada campo
                gus_cats = [cat for cat, fields in gus_categories.items() if field in fields]
                game_cats = [cat for cat, fields in game_categories.items() if field in fields]
                
                print(f"\n📝 {field}:")
                print(f"   GameUserSettings.ini -> Categoría: {', '.join(gus_cats)}")
                print(f"   Game.ini -> Categoría: {', '.join(game_cats)}")
                
            print("\n" + "=" * 50)
            print("\n💡 RECOMENDACIONES:")
            print("\nBasándose en la documentación oficial de ARK, estos campos deberían ir en:")
            
            recommendations = {
                # Campos de crianza y reproducción - van en Game.ini
                "BabyImprintingStatScaleMultiplier": "Game.ini (configuración de servidor)",
                "BabyImprintAmountMultiplier": "Game.ini (configuración de servidor)", 
                "MatingIntervalMultiplier": "Game.ini (configuración de servidor)",
                "MatingSpeedMultiplier": "Game.ini (configuración de servidor)",
                "LayEggIntervalMultiplier": "Game.ini (configuración de servidor)",
                "EggHatchSpeedMultiplier": "Game.ini (configuración de servidor)",
                "BabyMatureSpeedMultiplier": "Game.ini (configuración de servidor)",
                "BabyCuddleIntervalMultiplier": "Game.ini (configuración de servidor)",
                "BabyCuddleGracePeriodMultiplier": "Game.ini (configuración de servidor)",
                "BabyCuddleLoseImprintQualitySpeedMultiplier": "Game.ini (configuración de servidor)",
                "BabyFoodConsumptionSpeedMultiplier": "Game.ini (configuración de servidor)",
                "DisableImprintDinoBuff": "Game.ini (configuración de servidor)",
                
                # Campos de domesticación y dinos - van en Game.ini
                "PassiveTameIntervalMultiplier": "Game.ini (configuración de servidor)",
                "bAllowTamedDinoRiding": "Game.ini (configuración de servidor)",
                "bDisableDinoRiding": "Game.ini (configuración de servidor)",
                "bDisableDinoTaming": "Game.ini (configuración de servidor)",
                "bUseTameLimitForStructuresOnly": "Game.ini (configuración de servidor)",
                "bForceCanRideFliers": "Game.ini (configuración de servidor)",
                "ForceAllowCaveFlyers": "Game.ini (configuración de servidor)",
                "AllowFlyingStaminaRecovery": "Game.ini (configuración de servidor)",
                "bAllowFlyerCarryPvE": "Game.ini (configuración de servidor)",
                "bFlyerPlatformAllowUnalignedDinoBasing": "Game.ini (configuración de servidor)",
                "TamedDinoCharacterFoodDrainMultiplier": "Game.ini (configuración de servidor)",
                "TamedDinoTorporDrainMultiplier": "Game.ini (configuración de servidor)",
                "WildDinoCharacterFoodDrainMultiplier": "Game.ini (configuración de servidor)",
                "WildDinoTorporDrainMultiplier": "Game.ini (configuración de servidor)",
                "DinoCharacterFoodDrainMultiplier": "Game.ini (configuración de servidor)",
                "DinoCharacterStaminaDrainMultiplier": "Game.ini (configuración de servidor)",
                "DinoCharacterHealthRecoveryMultiplier": "Game.ini (configuración de servidor)",
                "PlayerCharacterWaterDrainMultiplier": "Game.ini (configuración de servidor)",
                "PlayerCharacterFoodDrainMultiplier": "Game.ini (configuración de servidor)",
                "PlayerCharacterStaminaDrainMultiplier": "Game.ini (configuración de servidor)",
                "PlayerCharacterHealthRecoveryMultiplier": "Game.ini (configuración de servidor)",
                "RaidDinoCharacterFoodDrainMultiplier": "Game.ini (configuración de servidor)",
                
                # Campos de recolección - van en Game.ini
                "PlayerHarvestingDamageMultiplier": "Game.ini (configuración de servidor)",
                "DinoHarvestingDamageMultiplier": "Game.ini (configuración de servidor)"
            }
            
            for field in sorted(duplicates):
                if field in recommendations:
                    print(f"   ✅ {field} -> {recommendations[field]}")
                else:
                    print(f"   ❓ {field} -> Revisar documentación oficial")
                    
        else:
            print("✅ No se encontraron campos duplicados.")
            
    except Exception as e:
        print(f"❌ Error al analizar campos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_duplicate_fields()