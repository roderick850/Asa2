#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis del problema del switch de consola del servidor ARK
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

class ConsoleAnalysisApp:
    def __init__(self):
        # Configurar CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Crear ventana principal
        self.root = ctk.CTk()
        self.root.title("Análisis del Switch de Consola")
        self.root.geometry("900x700")
        
        # Inicializar managers
        self.config_manager = ConfigManager()
        self.server_manager = ServerManager(self.config_manager)
        
        self.create_ui()
        self.analyze_problem()
    
    def create_ui(self):
        """Crear la interfaz de usuario"""
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔍 Análisis del Switch de Consola del Servidor ARK",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Frame de diagnóstico
        self.diagnosis_frame = ctk.CTkFrame(main_frame)
        self.diagnosis_frame.pack(fill="x", pady=10)
        
        diagnosis_title = ctk.CTkLabel(
            self.diagnosis_frame,
            text="📋 Diagnóstico del Problema",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        diagnosis_title.pack(pady=10)
        
        self.diagnosis_text = ctk.CTkTextbox(
            self.diagnosis_frame,
            height=200,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.diagnosis_text.pack(fill="x", padx=10, pady=(0, 10))
        
        # Frame de solución
        solution_frame = ctk.CTkFrame(main_frame)
        solution_frame.pack(fill="x", pady=10)
        
        solution_title = ctk.CTkLabel(
            solution_frame,
            text="💡 Solución Recomendada",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        solution_title.pack(pady=10)
        
        self.solution_text = ctk.CTkTextbox(
            solution_frame,
            height=150,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.solution_text.pack(fill="x", padx=10, pady=(0, 10))
        
        # Frame de prueba
        test_frame = ctk.CTkFrame(main_frame)
        test_frame.pack(fill="x", pady=10)
        
        test_title = ctk.CTkLabel(
            test_frame,
            text="🧪 Prueba del Switch",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        test_title.pack(pady=10)
        
        # Switch de prueba
        self.console_visibility_var = ctk.BooleanVar(
            value=self.config_manager.get("app", "show_server_console", default="true").lower() == "true"
        )
        
        self.show_console_switch = ctk.CTkSwitch(
            test_frame,
            text="Mostrar Consola del Servidor",
            command=self.test_switch,
            variable=self.console_visibility_var
        )
        self.show_console_switch.pack(pady=10)
        
        # Estado del switch
        self.switch_status = ctk.CTkLabel(
            test_frame,
            text=f"Estado: {'Activado' if self.console_visibility_var.get() else 'Desactivado'}",
            font=ctk.CTkFont(size=12)
        )
        self.switch_status.pack(pady=5)
        
        # Botones de acción
        buttons_frame = ctk.CTkFrame(test_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=10)
        
        refresh_btn = ctk.CTkButton(
            buttons_frame,
            text="🔄 Actualizar Análisis",
            command=self.analyze_problem,
            width=150
        )
        refresh_btn.pack(side="left", padx=5)
        
        config_btn = ctk.CTkButton(
            buttons_frame,
            text="⚙️ Ver Configuración",
            command=self.show_config,
            width=150
        )
        config_btn.pack(side="left", padx=5)
        
        close_btn = ctk.CTkButton(
            buttons_frame,
            text="❌ Cerrar",
            command=self.root.quit,
            width=100
        )
        close_btn.pack(side="right", padx=5)
    
    def analyze_problem(self):
        """Analizar el problema del switch de consola"""
        diagnosis = []
        
        # 1. Verificar configuración
        show_console_config = self.config_manager.get("app", "show_server_console", default="true")
        diagnosis.append(f"✅ Configuración 'show_server_console': {show_console_config}")
        
        # 2. Verificar estado del servidor
        is_running = self.server_manager.is_server_running()
        if is_running:
            diagnosis.append("✅ Servidor ARK está ejecutándose")
            server_pid = self.server_manager.get_server_pid()
            diagnosis.append(f"   - PID del servidor: {server_pid}")
        else:
            diagnosis.append("❌ Servidor ARK NO está ejecutándose")
            diagnosis.append("   - Este es el PROBLEMA PRINCIPAL")
        
        # 3. Verificar ventana de consola
        console_hwnd = self.server_manager._find_server_console_window()
        if console_hwnd:
            diagnosis.append(f"✅ Ventana de consola encontrada: HWND={console_hwnd}")
        else:
            diagnosis.append("❌ No se encontró ventana de consola del servidor")
            if not is_running:
                diagnosis.append("   - Normal, ya que el servidor no está ejecutándose")
        
        # 4. Verificar funcionalidad del switch
        diagnosis.append("\n🔧 ANÁLISIS DEL SWITCH:")
        if not is_running:
            diagnosis.append("❌ El switch NO PUEDE funcionar sin un servidor ejecutándose")
            diagnosis.append("   - El switch necesita una ventana de consola activa para mostrar/ocultar")
            diagnosis.append("   - La configuración se guarda correctamente, pero no tiene efecto")
        else:
            diagnosis.append("✅ El switch debería funcionar correctamente")
        
        # Mostrar diagnóstico
        self.diagnosis_text.delete("1.0", "end")
        self.diagnosis_text.insert("1.0", "\n".join(diagnosis))
        
        # Generar solución
        self.generate_solution(is_running)
    
    def generate_solution(self, server_running):
        """Generar solución basada en el análisis"""
        solution = []
        
        if not server_running:
            solution.append("🎯 SOLUCIÓN PRINCIPAL:")
            solution.append("")
            solution.append("1. INICIAR EL SERVIDOR ARK:")
            solution.append("   - Ve al panel principal de ARK Server Manager")
            solution.append("   - Selecciona tu servidor configurado")
            solution.append("   - Haz clic en 'Iniciar Servidor'")
            solution.append("   - Espera a que el servidor se inicie completamente")
            solution.append("")
            solution.append("2. PROBAR EL SWITCH:")
            solution.append("   - Una vez que el servidor esté ejecutándose")
            solution.append("   - Ve al panel de 'Consola'")
            solution.append("   - Prueba el switch 'Mostrar Consola del Servidor'")
            solution.append("   - Deberías ver la ventana de consola aparecer/desaparecer")
            solution.append("")
            solution.append("3. VERIFICACIÓN:")
            solution.append("   - El switch solo funciona cuando hay un servidor activo")
            solution.append("   - La configuración se guarda independientemente del estado del servidor")
            solution.append("   - Al reiniciar el servidor, se aplicará la configuración guardada")
        else:
            solution.append("✅ El servidor está ejecutándose.")
            solution.append("")
            solution.append("Si el switch aún no funciona:")
            solution.append("1. Verifica que la ventana de consola sea visible")
            solution.append("2. Intenta cerrar y reabrir el panel de consola")
            solution.append("3. Reinicia ARK Server Manager")
        
        self.solution_text.delete("1.0", "end")
        self.solution_text.insert("1.0", "\n".join(solution))
    
    def test_switch(self):
        """Probar el switch de consola"""
        show_console = self.show_console_switch.get()
        
        # Actualizar estado visual
        self.switch_status.configure(
            text=f"Estado: {'Activado' if show_console else 'Desactivado'}"
        )
        
        # Guardar configuración
        self.config_manager.set("app", "show_server_console", str(show_console).lower())
        self.config_manager.save()
        
        # Verificar si el servidor está ejecutándose
        is_running = self.server_manager.is_server_running()
        
        if is_running:
            # Intentar aplicar el cambio
            if show_console:
                result = self.server_manager.show_server_console()
            else:
                result = self.server_manager.hide_server_console()
            
            if result:
                messagebox.showinfo(
                    "Switch de Consola",
                    f"✅ Consola del servidor {'mostrada' if show_console else 'ocultada'} correctamente"
                )
            else:
                messagebox.showwarning(
                    "Switch de Consola",
                    "⚠️ No se pudo aplicar el cambio. Verifica que el servidor esté ejecutándose correctamente."
                )
        else:
            messagebox.showinfo(
                "Switch de Consola",
                f"💾 Configuración guardada: {'mostrar' if show_console else 'ocultar'} consola.\n\n"
                f"ℹ️ El cambio se aplicará cuando inicies el servidor ARK."
            )
    
    def show_config(self):
        """Mostrar configuración actual"""
        config_info = [
            "⚙️ CONFIGURACIÓN ACTUAL:",
            "",
            f"show_server_console: {self.config_manager.get('app', 'show_server_console', 'true')}",
            f"Archivo: {self.config_manager.config_file}",
            f"Switch estado: {self.console_visibility_var.get()}",
            "",
            "📁 RUTAS DE SERVIDOR:"
        ]
        
        # Agregar rutas de servidores configurados
        server_paths = [
            ("executable_path_prueba", "Servidor Prueba"),
            ("executable_path_ark_server", "ARK Server"),
            ("executable_path_prueba2", "Servidor Prueba2")
        ]
        
        for key, name in server_paths:
            path = self.config_manager.get("server", key, "")
            if path:
                exists = "✅" if os.path.exists(path) else "❌"
                config_info.append(f"{exists} {name}: {path}")
        
        messagebox.showinfo("Configuración", "\n".join(config_info))
    
    def run(self):
        """Ejecutar la aplicación"""
        self.root.mainloop()

def main():
    """Función principal"""
    print("🔍 Iniciando análisis del switch de consola...")
    
    app = ConsoleAnalysisApp()
    app.run()
    
    print("✅ Análisis completado")

if __name__ == "__main__":
    main()