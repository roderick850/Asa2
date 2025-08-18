#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba específico para el problema "Próximo backup: Deshabilitado"

Este script verifica que cuando el auto-backup está habilitado,
NO aparezca "Próximo backup: Deshabilitado" sino la fecha real.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from gui.panels.advanced_backup_panel import AdvancedBackupPanel
import time
import logging

class MockConfigManager:
    """Mock del config manager para pruebas"""
    def __init__(self):
        self.config = {}
        
    def get(self, key, default=None):
        return self.config.get(key, default)
        
    def set(self, key, value):
        self.config[key] = value
        
    def save(self):
        pass

class MockMainWindow:
    """Mock de la ventana principal para pruebas"""
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Test Próximo Backup Fix")
        self.root.geometry("900x700")
        
    def add_log_message(self, message):
        print(f"LOG: {message}")

def test_next_backup_fix():
    """Probar la corrección del próximo backup"""
    print("=== PRUEBA ESPECÍFICA: PRÓXIMO BACKUP DESHABILITADO ===")
    print()
    
    # Crear ventana de prueba
    main_window = MockMainWindow()
    
    # Crear mocks necesarios
    config_manager = MockConfigManager()
    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)
    
    # Crear panel de backup
    backup_panel = AdvancedBackupPanel(main_window.root, config_manager, logger, main_window)
    backup_panel.pack(fill="both", expand=True, padx=10, pady=10)
    
    def check_next_backup_status():
        """Verificar específicamente el estado del próximo backup"""
        try:
            status_text = backup_panel.status_label.cget("text")
            next_backup_text = backup_panel.next_backup_info.cget("text")
            auto_backup_enabled = backup_panel.auto_backup_var.get()
            
            print(f"Estado: {status_text}")
            print(f"Próximo backup: {next_backup_text}")
            print(f"Auto-backup habilitado: {auto_backup_enabled}")
            print()
            
            # Verificación específica del problema
            if auto_backup_enabled and "🟢" in status_text:
                if "Deshabilitado" in next_backup_text:
                    print("❌ PROBLEMA DETECTADO: Muestra 'Deshabilitado' cuando debería mostrar fecha")
                    print("   El auto-backup está activo pero el próximo backup dice 'Deshabilitado'")
                    return False
                elif "20" in next_backup_text and ":" in next_backup_text:  # Verificar formato de fecha
                    print("✅ CORRECTO: Muestra fecha del próximo backup")
                    return True
                else:
                    print("⚠️  ADVERTENCIA: No muestra 'Deshabilitado' pero tampoco una fecha válida")
                    print(f"   Texto actual: '{next_backup_text}'")
                    return False
            elif not auto_backup_enabled:
                if "Deshabilitado" in next_backup_text:
                    print("✅ CORRECTO: Muestra 'Deshabilitado' cuando está inactivo")
                    return True
                else:
                    print("❌ PROBLEMA: No muestra 'Deshabilitado' cuando debería")
                    return False
            else:
                print("⚠️  Estado inconsistente detectado")
                return False
                
        except Exception as e:
            print(f"Error al verificar estado: {e}")
            return False
    
    def test_sequence():
        """Secuencia de pruebas específica"""
        print("1. Estado inicial:")
        result1 = check_next_backup_status()
        
        print("\n2. Habilitando auto-backup (MOMENTO CRÍTICO):")
        backup_panel.auto_backup_var.set(True)
        backup_panel.toggle_auto_backup()
        
        # Esperar un poco más para asegurar que se actualice
        try:
            main_window.root.after(1500, lambda: [
                print("   Verificando después de habilitar..."),
                check_next_backup_status() and print("✅ ÉXITO: El problema está solucionado") or print("❌ FALLO: El problema persiste"),
                print("\n3. Deshabilitando para verificar que funciona correctamente:"),
                backup_panel.auto_backup_var.set(False),
                backup_panel.toggle_auto_backup(),
                main_window.root.after(500, lambda: [
                    check_next_backup_status(),
                    print("\n4. Habilitando nuevamente para doble verificación:"),
                    backup_panel.auto_backup_var.set(True),
                    backup_panel.toggle_auto_backup(),
                    main_window.root.after(1500, lambda: [
                        check_next_backup_status() and print("\n🎉 PRUEBA COMPLETADA: El problema está SOLUCIONADO") or print("\n💥 PRUEBA FALLIDA: El problema AÚN PERSISTE"),
                        print("\nCierre la ventana para terminar.")
                    ])
                ])
            ])
        except Exception as e:
            print(f"Error en programación de pruebas: {e}")
    
    # Iniciar secuencia de pruebas
    try:
        main_window.root.after(500, test_sequence)
    except Exception as e:
        print(f"Error iniciando secuencia de pruebas: {e}")
    
    # Ejecutar la aplicación
    main_window.root.mainloop()

if __name__ == "__main__":
    test_next_backup_fix()