#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para verificar si los campos se están agregando a GameUserSettings.ini
"""

import configparser
import os
from pathlib import Path

def check_gameusersettings_file():
    """Verificar el contenido del archivo GameUserSettings.ini"""
    
    # Ruta del archivo
    gus_path = r"D:\ASA\Prueba\ShooterGame\Saved\Config\WindowsServer\GameUserSettings.ini"
    
    print(f"🔍 Verificando archivo: {gus_path}")
    
    if not os.path.exists(gus_path):
        print("❌ El archivo GameUserSettings.ini no existe")
        return
    
    print("✅ El archivo existe")
    
    # Leer el archivo
    try:
        config = configparser.ConfigParser()
        config.optionxform = str  # Preservar mayúsculas/minúsculas
        config.read(gus_path, encoding='utf-8')
        
        print(f"\n📋 Secciones encontradas: {list(config.sections())}")
        
        # Contar campos por sección
        total_fields = 0
        for section_name in config.sections():
            section = config[section_name]
            field_count = len(section)
            total_fields += field_count
            print(f"   [{section_name}]: {field_count} campos")
            
            # Mostrar algunos campos de ejemplo
            if field_count > 0:
                fields = list(section.keys())[:5]  # Primeros 5 campos
                print(f"      Ejemplos: {fields}")
        
        print(f"\n📊 Total de campos en el archivo: {total_fields}")
        
        # Verificar campos específicos que deberían estar
        expected_fields = [
            "MaxNumbersofPlayersInTribe",
            "MaxAlliancesPerTribe", 
            "TribeNameChangeCooldown",
            "AllianceNameChangeCooldown",
            "TamingSpeedMultiplier",
            "HarvestAmountMultiplier"
        ]
        
        print("\n🔍 Verificando campos específicos:")
        found_fields = 0
        for field in expected_fields:
            found = False
            for section_name in config.sections():
                if field in config[section_name]:
                    value = config[section_name][field]
                    print(f"   ✅ {field} = {value} (en [{section_name}])")
                    found = True
                    found_fields += 1
                    break
            if not found:
                print(f"   ❌ {field} - NO ENCONTRADO")
        
        print(f"\n📈 Campos verificados encontrados: {found_fields}/{len(expected_fields)}")
        
        # Mostrar tamaño del archivo
        file_size = os.path.getsize(gus_path)
        print(f"📏 Tamaño del archivo: {file_size} bytes")
        
        # Mostrar fecha de modificación
        import datetime
        mod_time = os.path.getmtime(gus_path)
        mod_date = datetime.datetime.fromtimestamp(mod_time)
        print(f"📅 Última modificación: {mod_date}")
        
    except Exception as e:
        print(f"❌ Error al leer el archivo: {e}")

if __name__ == "__main__":
    check_gameusersettings_file()