#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar las correcciones del estado de backup

Este script verifica:
1. Que el estado muestre puntos de color correctos (🟢 para activo, 🔴 para inactivo)
2. Que el próximo backup se calcule correctamente cuando está habilitado
3. Que muestre "Deshabilitado" solo cuando realmente esté deshabilitado
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
        self.root.title("Test Backup Status Fix")
        self.root.geometry("800x600")
        
    def add_log_message(self, message):
        print(f"LOG: {message}")

def test_backup_status():
    """Probar las correcciones del estado de backup"""
    print("=== PRUEBA DE CORRECCIONES DEL ESTADO DE BACKUP ===")
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
    
    def check_status():
        """Verificar el estado actual"""
        try:
            status_text = backup_panel.status_label.cget("text")
            next_backup_text = backup_panel.next_backup_info.cget("text")
            auto_backup_enabled = backup_panel.auto_backup_var.get()
            
            print(f"Estado actual: {status_text}")
            print(f"Próximo backup: {next_backup_text}")
            print(f"Auto-backup habilitado: {auto_backup_enabled}")
            print()
            
            # Verificar puntos de color
            if auto_backup_enabled:
                if "🟢" in status_text:
                    print("✅ Punto verde correcto para estado activo")
                else:
                    print("❌ Falta punto verde para estado activo")
                    
                if "Deshabilitado" not in next_backup_text:
                    print("✅ Próximo backup no muestra 'Deshabilitado' cuando está activo")
                else:
                    print("❌ Próximo backup muestra 'Deshabilitado' cuando debería estar activo")
            else:
                if "🔴" in status_text:
                    print("✅ Punto rojo correcto para estado inactivo")
                else:
                    print("❌ Falta punto rojo para estado inactivo")
                    
                if "Deshabilitado" in next_backup_text:
                    print("✅ Próximo backup muestra 'Deshabilitado' correctamente")
                else:
                    print("❌ Próximo backup no muestra 'Deshabilitado' cuando debería")
            
        except Exception as e:
            print(f"Error al verificar estado: {e}")
    
    def test_sequence():
        """Secuencia de pruebas"""
        print("1. Estado inicial (debería estar inactivo con punto rojo):")
        main_window.root.after(1000, lambda: [
            check_status(),
            print("\n2. Habilitando auto-backup (debería mostrar punto verde y calcular próximo backup):"),
            backup_panel.auto_backup_var.set(True),
            backup_panel.toggle_auto_backup(),
            main_window.root.after(2000, lambda: [
                check_status(),
                print("\n3. Deshabilitando auto-backup (debería mostrar punto rojo y 'Deshabilitado'):"),
                backup_panel.auto_backup_var.set(False),
                backup_panel.toggle_auto_backup(),
                main_window.root.after(1000, lambda: [
                    check_status(),
                    print("\n4. Habilitando nuevamente para verificar consistencia:"),
                    backup_panel.auto_backup_var.set(True),
                    backup_panel.toggle_auto_backup(),
                    main_window.root.after(2000, lambda: [
                        check_status(),
                        print("\n=== PRUEBA COMPLETADA ==="),
                        print("Cierre la ventana para terminar.")
                    ])
                ])
            ])
        ])
    
    # Iniciar secuencia de pruebas
    main_window.root.after(500, test_sequence)
    
    # Ejecutar la aplicación
    main_window.root.mainloop()

if __name__ == "__main__":
    test_backup_status()