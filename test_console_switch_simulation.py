#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de simulación para probar el switch de consola sin servidor ejecutándose
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager
from utils.server_manager import ServerManager
from gui.panels.console_panel import ConsolePanel

class TestConsoleApp:
    def __init__(self):
        # Configurar CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Crear ventana principal
        self.root = ctk.CTk()
        self.root.title("Test Console Switch")
        self.root.geometry("800x600")
        
        # Inicializar managers
        self.config_manager = ConfigManager()
        self.server_manager = ServerManager(self.config_manager)
        
        # Crear frame principal
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text="🧪 Test del Switch de Consola",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Frame de información
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        info_text = (
            "Este test simula el comportamiento del switch de consola.\n"
            "Puedes probar la funcionalidad sin necesidad de tener un servidor ejecutándose."
        )
        
        info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=12),
            wraplength=700
        )
        info_label.pack(pady=10)
        
        # Frame de controles
        controls_frame = ctk.CTkFrame(main_frame)
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        # Switch de consola
        self.console_visibility_var = ctk.BooleanVar(
            value=self.config_manager.get("app", "show_server_console", default="true").lower() == "true"
        )
        
        self.show_console_switch = ctk.CTkSwitch(
            controls_frame,
            text="Mostrar Consola del Servidor",
            command=self.toggle_console_visibility,
            variable=self.console_visibility_var
        )
        self.show_console_switch.pack(pady=10)
        
        # Estado actual
        self.status_label = ctk.CTkLabel(
            controls_frame,
            text=f"Estado actual: {'Visible' if self.console_visibility_var.get() else 'Oculta'}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.status_label.pack(pady=5)
        
        # Frame de botones de prueba
        test_frame = ctk.CTkFrame(main_frame)
        test_frame.pack(fill="x", padx=10, pady=5)
        
        test_label = ctk.CTkLabel(
            test_frame,
            text="🔧 Pruebas Adicionales",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        test_label.pack(pady=(10, 5))
        
        # Botones de prueba
        buttons_frame = ctk.CTkFrame(test_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=5)
        
        test_config_btn = ctk.CTkButton(
            buttons_frame,
            text="🔍 Ver Configuración",
            command=self.show_config,
            width=150
        )
        test_config_btn.pack(side="left", padx=5)
        
        test_search_btn = ctk.CTkButton(
            buttons_frame,
            text="🔎 Buscar Procesos ARK",
            command=self.search_ark_processes,
            width=150
        )
        test_search_btn.pack(side="left", padx=5)
        
        test_windows_btn = ctk.CTkButton(
            buttons_frame,
            text="🪟 Listar Ventanas",
            command=self.list_windows,
            width=150
        )
        test_windows_btn.pack(side="left", padx=5)
        
        # Área de log
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        log_title = ctk.CTkLabel(
            log_frame,
            text="📋 Log de Eventos",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        log_title.pack(pady=(10, 5))
        
        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Consolas", size=10)
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Log inicial
        self.add_log("🚀 Test del switch de consola iniciado")
        self.add_log(f"📁 Archivo de configuración: {self.config_manager.config_file}")
        self.add_log(f"⚙️ Estado inicial: {'Visible' if self.console_visibility_var.get() else 'Oculta'}")
    
    def add_log(self, message):
        """Agregar mensaje al log"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert("end", log_message)
        self.log_text.see("end")
    
    def toggle_console_visibility(self):
        """Simular el toggle del switch de consola"""
        try:
            show_console = self.show_console_switch.get()
            action = "mostrar" if show_console else "ocultar"
            
            self.add_log(f"🔄 Usuario solicitó {action} la consola del servidor")
            
            # Guardar configuración
            self.config_manager.set("app", "show_server_console", str(show_console).lower())
            self.config_manager.save()
            
            self.add_log(f"💾 Configuración guardada: show_server_console = {show_console}")
            
            # Actualizar estado
            self.status_label.configure(
                text=f"Estado actual: {'Visible' if show_console else 'Oculta'}"
            )
            
            # Simular búsqueda de servidor
            self.add_log("🔍 Buscando servidor ejecutándose...")
            
            # Buscar procesos ARK
            ark_processes = self.find_ark_processes()
            
            if ark_processes:
                self.add_log(f"✅ Encontrados {len(ark_processes)} procesos ARK")
                for proc in ark_processes:
                    self.add_log(f"   - PID: {proc['pid']}, Nombre: {proc['name']}")
                
                # Simular búsqueda de ventana
                self.add_log("🪟 Buscando ventana de consola...")
                
                # Aquí simularíamos la búsqueda real
                self.add_log(f"🎯 Simulando {action} consola del servidor...")
                
                if show_console:
                    self.add_log("✅ Consola del servidor: VISIBLE (simulado)")
                else:
                    self.add_log("✅ Consola del servidor: OCULTA (simulado)")
            else:
                self.add_log("ℹ️ No hay servidor ejecutándose. El cambio se aplicará al iniciar el servidor")
            
        except Exception as e:
            self.add_log(f"❌ Error: {str(e)}")
            import traceback
            self.add_log(f"📋 Traceback: {traceback.format_exc()}")
    
    def find_ark_processes(self):
        """Buscar procesos de ARK"""
        import psutil
        ark_processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'ArkAscendedServer.exe' in proc.info['name']:
                        ark_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.add_log(f"❌ Error buscando procesos: {e}")
        
        return ark_processes
    
    def show_config(self):
        """Mostrar configuración actual"""
        try:
            show_console = self.config_manager.get("app", "show_server_console", default="true")
            
            config_info = (
                f"Configuración actual:\n\n"
                f"show_server_console: {show_console}\n"
                f"Archivo: {self.config_manager.config_file}\n"
                f"Switch estado: {self.console_visibility_var.get()}"
            )
            
            messagebox.showinfo("Configuración", config_info)
            self.add_log("📋 Configuración mostrada al usuario")
            
        except Exception as e:
            self.add_log(f"❌ Error mostrando configuración: {e}")
    
    def search_ark_processes(self):
        """Buscar y mostrar procesos ARK"""
        self.add_log("🔍 Buscando procesos ARK...")
        
        ark_processes = self.find_ark_processes()
        
        if ark_processes:
            self.add_log(f"✅ Encontrados {len(ark_processes)} procesos ARK:")
            for proc in ark_processes:
                self.add_log(f"   - PID: {proc['pid']}, Nombre: {proc['name']}")
        else:
            self.add_log("❌ No se encontraron procesos ARK ejecutándose")
    
    def list_windows(self):
        """Listar ventanas del sistema (solo las visibles)"""
        import ctypes
        from ctypes import wintypes
        
        self.add_log("🪟 Listando ventanas visibles...")
        
        try:
            user32 = ctypes.windll.user32
            windows = []
            
            def enum_windows_callback(hwnd, lparam):
                try:
                    if user32.IsWindowVisible(hwnd):
                        window_text = ctypes.create_unicode_buffer(256)
                        user32.GetWindowTextW(hwnd, window_text, 256)
                        
                        if window_text.value.strip():  # Solo ventanas con título
                            windows.append({
                                'hwnd': hwnd,
                                'title': window_text.value
                            })
                except:
                    pass
                return True
            
            user32.EnumWindows(
                ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(enum_windows_callback),
                0
            )
            
            self.add_log(f"✅ Encontradas {len(windows)} ventanas visibles")
            
            # Mostrar solo las primeras 10 para no saturar el log
            for i, window in enumerate(windows[:10]):
                self.add_log(f"   {i+1}. {window['title']}")
            
            if len(windows) > 10:
                self.add_log(f"   ... y {len(windows) - 10} más")
                
        except Exception as e:
            self.add_log(f"❌ Error listando ventanas: {e}")
    
    def run(self):
        """Ejecutar la aplicación"""
        self.root.mainloop()

def main():
    """Función principal"""
    print("🧪 Iniciando test del switch de consola...")
    
    app = TestConsoleApp()
    app.run()
    
    print("✅ Test completado")

if __name__ == "__main__":
    main()