#!/usr/bin/env python3
"""
Script de prueba simplificado para identificar problemas de layout
"""

import customtkinter as ctk
import sys
import os

def main():
    """Función principal de prueba simplificada"""
    # Configurar CustomTkinter
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Crear ventana principal
    root = ctk.CTk()
    root.title("Prueba Simple de Layout")
    root.geometry("800x600")
    
    # Configurar grid de la ventana principal
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)
    
    # Crear frame principal
    main_frame = ctk.CTkFrame(root)
    main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure(1, weight=1)
    
    # Título
    title = ctk.CTkLabel(
        main_frame, 
        text="📋 Panel de Logs y Consola del Servidor", 
        font=ctk.CTkFont(size=18, weight="bold")
    )
    title.grid(row=0, column=0, pady=10, sticky="w")
    
    # Crear tabview
    tabview = ctk.CTkTabview(main_frame)
    tabview.grid(row=1, column=0, sticky="nsew", pady=5)
    tabview.grid_columnconfigure(0, weight=1)
    tabview.grid_rowconfigure(0, weight=1)
    
    # Crear pestaña de consola
    tab_console = tabview.add("🎮 Consola")
    tab_console.grid_columnconfigure(0, weight=1)
    tab_console.grid_rowconfigure(1, weight=1)
    
    # Frame de botones
    button_frame = ctk.CTkFrame(tab_console)
    button_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
    button_frame.grid_columnconfigure(0, weight=1)
    
    # Botón de prueba
    test_btn = ctk.CTkButton(
        button_frame,
        text="🧪 Probar",
        command=lambda: add_test_line(),
        width=80
    )
    test_btn.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    
    # Frame de consola
    console_frame = ctk.CTkFrame(tab_console)
    console_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
    
    # Texto de consola
    console_text = ctk.CTkTextbox(
        console_frame,
        font=("Consolas", 10),
        wrap="word"
    )
    console_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    # Scrollbar
    scrollbar = ctk.CTkScrollbar(console_frame, command=console_text.yview)
    scrollbar.pack(side="right", fill="y")
    console_text.configure(yscrollcommand=scrollbar.set)
    
    # Función para agregar línea de prueba
    def add_test_line():
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] 🔧 Línea de prueba agregada\n"
        console_text.insert("end", line)
        console_text.see("end")
        print(f"Línea agregada: {line.strip()}")
    
    # Contenido inicial
    initial_content = f"""🎮 CONSOLA DEL SERVIDOR ARK - {datetime.datetime.now().strftime('%H:%M:%S')}
{'='*60}

✅ Consola inicializada correctamente
⏸️ Estado: Inactiva (esperando conexión)

💡 FUNCIONALIDADES:
• 📜 Auto-scroll automático activado
• 🧹 Botón para limpiar la consola
• 📁 Exportar contenido a archivo
• 📊 Información en tiempo real

🔄 La consola se actualizará automáticamente cuando:
• El servidor esté ejecutándose
• Haya actividad en el servidor
• Se reciban comandos RCON

🚀 ¡Consola lista para monitorear el servidor!
"""
    
    console_text.insert("1.0", initial_content)
    
    # Botón para verificar geometría
    debug_btn = ctk.CTkButton(
        button_frame,
        text="🐛 Debug",
        command=lambda: debug_geometry(),
        width=80,
        fg_color="purple"
    )
    debug_btn.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
    def debug_geometry():
        print(f"Main frame geometry: {main_frame.winfo_geometry()}")
        print(f"Tabview geometry: {tabview.winfo_geometry()}")
        print(f"Tab console geometry: {tab_console.winfo_geometry()}")
        print(f"Console frame geometry: {console_frame.winfo_geometry()}")
        print(f"Console text geometry: {console_text.winfo_geometry()}")
        print(f"Console text width: {console_text.winfo_width()}, height: {console_text.winfo_height()}")
    
    print("✅ Aplicación de prueba simplificada iniciada")
    print("📋 Panel de logs creado")
    print("🎮 Consola del servidor inicializada")
    print("🔍 Usa los botones para probar la funcionalidad")
    
    # Iniciar la aplicación
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error al ejecutar la aplicación de prueba: {e}")
        import traceback
        traceback.print_exc()
