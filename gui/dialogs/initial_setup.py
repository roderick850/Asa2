import customtkinter as ctk
import os
import subprocess
import threading
import zipfile
import urllib.request
from pathlib import Path


class InitialSetupDialog:
    def __init__(self, parent, config_manager, logger):
        self.parent = parent
        self.config_manager = config_manager
        self.logger = logger
        self.result = False
        
        # Crear ventana modal
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Configuración Inicial")
        self.dialog.geometry("600x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrar la ventana
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"600x400+{x}+{y}")
        
        self.create_widgets()
        
        # Esperar hasta que se cierre la ventana
        self.dialog.wait_window()
    
    def create_widgets(self):
        # Frame principal
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Configuración Inicial", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(20, 30))
        
        # Descripción
        desc_label = ctk.CTkLabel(
            main_frame,
            text="Bienvenido al Administrador de Servidores de Ark Survival Ascended.\nConfigure la ruta raíz donde se instalarán los servidores:",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        desc_label.pack(pady=(0, 20))
        
        # Frame para la ruta
        path_frame = ctk.CTkFrame(main_frame)
        path_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(path_frame, text="Ruta raíz de servidores:").pack(anchor="w", padx=10, pady=(10, 5))
        
        # Frame para entrada y botón
        input_frame = ctk.CTkFrame(path_frame)
        input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.path_entry = ctk.CTkEntry(input_frame, placeholder_text="C:\\ArkServers")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_button = ctk.CTkButton(
            input_frame,
            text="Examinar",
            command=self.browse_path,
            width=100
        )
        browse_button.pack(side="right")
        
        # Verificar SteamCMD
        steam_frame = ctk.CTkFrame(main_frame)
        steam_frame.pack(fill="x", padx=20, pady=10)
        
        self.steam_status_label = ctk.CTkLabel(
            steam_frame,
            text="Verificando SteamCMD...",
            font=ctk.CTkFont(size=12)
        )
        self.steam_status_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.install_steam_button = ctk.CTkButton(
            steam_frame,
            text="Instalar SteamCMD",
            command=self.install_steamcmd,
            fg_color="blue",
            hover_color="darkblue"
        )
        self.install_steam_button.pack(anchor="w", padx=10, pady=(0, 10))
        self.install_steam_button.pack_forget()  # Oculto por defecto
        
        # Botones de acción
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", padx=20, pady=20)
        
        self.continue_button = ctk.CTkButton(
            buttons_frame,
            text="Continuar",
            command=self.continue_setup,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.continue_button.pack(side="right", padx=(10, 0))
        
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancelar",
            command=self.cancel_setup,
            fg_color="red",
            hover_color="darkred"
        )
        cancel_button.pack(side="right")
        
        # Verificar SteamCMD al inicio
        self.check_steamcmd()
    
    def browse_path(self):
        """Abrir diálogo para seleccionar ruta"""
        from tkinter import filedialog
        
        path = filedialog.askdirectory(
            title="Seleccionar ruta raíz para servidores",
            initialdir=os.path.expanduser("~")
        )
        
        if path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)
    
    def check_steamcmd(self):
        """Verificar si SteamCMD está instalado"""
        def check():
            try:
                # Verificar si steamcmd está en el PATH
                result = subprocess.run(
                    ["steamcmd", "+quit"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                
                if result.returncode == 0:
                    self.dialog.after(0, lambda: self.steam_status_label.configure(
                        text="✅ SteamCMD encontrado en el sistema",
                        text_color="green"
                    ))
                    self.steamcmd_installed = True
                else:
                    raise Exception("SteamCMD no encontrado")
                    
            except Exception as e:
                # Verificar si existe en la ruta raíz
                root_path = self.path_entry.get().strip()
                if root_path:
                    steamcmd_path = os.path.join(root_path, "steamcmd", "steamcmd.exe")
                    if os.path.exists(steamcmd_path):
                        self.dialog.after(0, lambda: self.steam_status_label.configure(
                            text="✅ SteamCMD encontrado en la ruta raíz",
                            text_color="green"
                        ))
                        self.steamcmd_installed = True
                    else:
                        self.dialog.after(0, lambda: self.steam_status_label.configure(
                            text="❌ SteamCMD no encontrado",
                            text_color="red"
                        ))
                        self.dialog.after(0, lambda: self.install_steam_button.pack(anchor="w", padx=10, pady=(0, 10)))
                        self.steamcmd_installed = False
                else:
                    self.dialog.after(0, lambda: self.steam_status_label.configure(
                        text="⚠️ Configure la ruta raíz para verificar SteamCMD",
                        text_color="orange"
                    ))
                    self.steamcmd_installed = False
        
        threading.Thread(target=check, daemon=True).start()
    
    def install_steamcmd(self):
        """Instalar SteamCMD"""
        def install():
            try:
                root_path = self.path_entry.get().strip()
                if not root_path:
                                    self.dialog.after(0, lambda: self.steam_status_label.configure(
                    text="❌ Configure la ruta raíz primero",
                    text_color="red"
                ))
                return
                
                self.dialog.after(0, lambda: self.steam_status_label.configure(
                    text="⏳ Descargando SteamCMD...",
                    text_color="orange"
                ))
                self.dialog.after(0, lambda: self.install_steam_button.configure(state="disabled"))
                
                # Crear directorio para SteamCMD
                steamcmd_dir = os.path.join(root_path, "steamcmd")
                os.makedirs(steamcmd_dir, exist_ok=True)
                
                # URL de descarga de SteamCMD
                steamcmd_url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
                zip_path = os.path.join(steamcmd_dir, "steamcmd.zip")
                
                # Descargar SteamCMD
                urllib.request.urlretrieve(steamcmd_url, zip_path)
                
                self.dialog.after(0, lambda: self.steam_status_label.configure(
                    text="⏳ Extrayendo SteamCMD...",
                    text_color="orange"
                ))
                
                # Extraer archivo ZIP
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(steamcmd_dir)
                
                # Eliminar archivo ZIP
                os.remove(zip_path)
                
                # Verificar instalación
                steamcmd_exe = os.path.join(steamcmd_dir, "steamcmd.exe")
                if os.path.exists(steamcmd_exe):
                    self.dialog.after(0, lambda: self.steam_status_label.configure(
                        text="✅ SteamCMD instalado correctamente",
                        text_color="green"
                    ))
                    self.steamcmd_installed = True
                    self.dialog.after(0, lambda: self.install_steam_button.pack_forget())
                    
                    # Actualizar configuración
                    self.config_manager.set("server", "steamcmd_path", steamcmd_exe)
                    self.config_manager.save()
                    
                    self.logger.info(f"SteamCMD instalado en: {steamcmd_exe}")
                else:
                    raise Exception("Error al extraer SteamCMD")
                    
            except Exception as e:
                self.dialog.after(0, lambda: self.steam_status_label.configure(
                    text=f"❌ Error al instalar SteamCMD: {str(e)}",
                    text_color="red"
                ))
                self.logger.error(f"Error al instalar SteamCMD: {e}")
            finally:
                self.dialog.after(0, lambda: self.install_steam_button.configure(state="normal"))
        
        threading.Thread(target=install, daemon=True).start()
    
    def continue_setup(self):
        """Continuar con la configuración"""
        root_path = self.path_entry.get().strip()
        
        if not root_path:
            # Mostrar error
            error_label = ctk.CTkLabel(
                self.dialog,
                text="❌ Debe especificar una ruta raíz",
                text_color="red"
            )
            error_label.pack(pady=10)
            return
        
        if not os.path.exists(root_path):
            try:
                os.makedirs(root_path, exist_ok=True)
            except Exception as e:
                error_label = ctk.CTkLabel(
                    self.dialog,
                    text=f"❌ Error al crear directorio: {str(e)}",
                    text_color="red"
                )
                error_label.pack(pady=10)
                return
        
        # Guardar configuración
        self.config_manager.set("server", "root_path", root_path)
        self.config_manager.set("server", "install_path", os.path.join(root_path, "servers"))
        self.config_manager.save()
        
        self.logger.info(f"Ruta raíz configurada: {root_path}")
        
        self.result = True
        self.dialog.destroy()
    
    def cancel_setup(self):
        """Cancelar configuración"""
        self.result = False
        self.dialog.destroy()
