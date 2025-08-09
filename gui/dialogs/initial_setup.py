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
        self.dialog = None
        
        try:
            self.create_dialog()
        except Exception as e:
            self.logger.error(f"Error crítico al crear diálogo inicial: {e}")
            # Si no se puede crear el diálogo, forzar a mostrar la ventana principal
            # pero NO marcar como exitoso
            self.result = False
            self._try_simple_dialog()
    
    def create_dialog(self):
        """Crear la ventana de diálogo de forma segura"""
        # Crear ventana modal
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("🚀 Configuración Inicial - Ark Server Manager")
        self.dialog.geometry("650x450")
        self.dialog.resizable(False, False)
        
        # Configurar comportamiento de ventana
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel_setup)
        
        # Configurar icono de forma segura
        self._set_icon()
        
        # Centrar la ventana
        self._center_window()
        
        # Crear contenido
        self.create_widgets()
        
        # Configurar como modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.focus_set()
        
        # Esperar hasta que se cierre la ventana
        self.dialog.wait_window()
    

    def _set_icon(self):
        """Configurar icono de forma segura"""
        try:
            icon_path = Path(__file__).parent.parent.parent / "ico" / "ArkManager.ico"
            if icon_path.exists() and self.dialog and self.dialog.winfo_exists():
                self.dialog.wm_iconbitmap(str(icon_path))
        except Exception:
            pass  # Ignorar errores de icono
    
    def _center_window(self):
        """Centrar la ventana en la pantalla"""
        try:
            if self.dialog and self.dialog.winfo_exists():
                self.dialog.update_idletasks()
                width = 650
                height = 450
                screen_width = self.dialog.winfo_screenwidth()
                screen_height = self.dialog.winfo_screenheight()
                x = (screen_width // 2) - (width // 2)
                y = (screen_height // 2) - (height // 2)
                self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        except Exception as e:
            self.logger.warning(f"No se pudo centrar ventana: {e}")
    
    def _try_simple_dialog(self):
        """Intentar crear un diálogo más simple como fallback"""
        try:
            import tkinter as tk
            import tkinter.filedialog as filedialog
            import tkinter.messagebox as msgbox
            
            self.logger.info("Intentando diálogo simple para configuración inicial...")
            
            # Mostrar mensaje explicativo
            response = msgbox.askquestion(
                "Configuración Inicial",
                "Bienvenido a Ark Server Manager\n\n"
                "Es necesario configurar la ruta raíz del servidor ARK.\n"
                "¿Deseas seleccionar la carpeta ahora?"
            )
            
            if response == 'yes':
                # Mostrar selector de carpeta
                folder_path = filedialog.askdirectory(
                    title="Seleccionar carpeta raíz del servidor ARK",
                    mustexist=True
                )
                
                if folder_path:
                    try:
                        # Guardar la configuración
                        self.config_manager.set("server", "root_path", folder_path)
                        self.config_manager.save_config()
                        
                        msgbox.showinfo(
                            "Configuración Completada",
                            f"✅ Ruta configurada correctamente:\n{folder_path}"
                        )
                        
                        self.result = True
                        self.logger.info(f"Configuración simple completada: {folder_path}")
                        
                    except Exception as e:
                        self.logger.error(f"Error al guardar configuración simple: {e}")
                        msgbox.showerror(
                            "Error",
                            f"Error al guardar la configuración:\n{e}"
                        )
                        self.result = False
                else:
                    # Usuario canceló
                    self.result = False
            else:
                # Usuario no quiere configurar ahora
                self.result = False
                
        except Exception as e:
            self.logger.error(f"Error en diálogo simple: {e}")
            self.result = False
    
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
        try:
            # Limpiar errores anteriores
            for widget in self.dialog.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text_color") == "red":
                    widget.destroy()
            
            root_path = self.path_entry.get().strip()
            
            if not root_path:
                self._show_error("❌ Debe especificar una ruta raíz")
                return
            
            # Validar que la ruta sea válida
            try:
                # Expandir variables de entorno si las hay
                root_path = os.path.expandvars(root_path)
                root_path = os.path.expanduser(root_path)
                root_path = os.path.abspath(root_path)
            except Exception as e:
                self._show_error(f"❌ Ruta inválida: {str(e)}")
                return
            
            # Verificar permisos de escritura
            test_dir = os.path.dirname(root_path)
            if not os.access(test_dir, os.W_OK):
                self._show_error("❌ Sin permisos de escritura en la ubicación seleccionada")
                return
            
            if not os.path.exists(root_path):
                try:
                    os.makedirs(root_path, exist_ok=True)
                    self.logger.info(f"Directorio creado: {root_path}")
                except Exception as e:
                    self._show_error(f"❌ Error al crear directorio: {str(e)}")
                    return
            
            # Verificar que se puede escribir en el directorio
            try:
                test_file = os.path.join(root_path, "test_write.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except Exception as e:
                self._show_error(f"❌ No se puede escribir en el directorio: {str(e)}")
                return
            
            # Guardar configuración
            try:
                self.config_manager.set("server", "root_path", root_path)
                self.config_manager.set("server", "install_path", os.path.join(root_path, "servers"))
                self.config_manager.save()
                
                self.logger.info(f"Ruta raíz configurada exitosamente: {root_path}")
                
                # Mostrar mensaje de éxito
                success_label = ctk.CTkLabel(
                    self.dialog,
                    text="✅ Configuración guardada correctamente",
                    text_color="green"
                )
                success_label.pack(pady=10)
                
                # Esperar un momento antes de cerrar
                self.dialog.after(1000, self._close_with_success)
                
            except Exception as e:
                self.logger.error(f"Error al guardar configuración: {e}")
                self._show_error(f"❌ Error al guardar configuración: {str(e)}")
                return
        
        except Exception as e:
            self.logger.error(f"Error inesperado en continue_setup: {e}")
            self._show_error(f"❌ Error inesperado: {str(e)}")
    
    def _show_error(self, message):
        """Mostrar mensaje de error"""
        error_label = ctk.CTkLabel(
            self.dialog,
            text=message,
            text_color="red"
        )
        error_label.pack(pady=10)
        
        # Auto-eliminar el error después de 5 segundos
        self.dialog.after(5000, lambda: error_label.destroy())
    
    def _close_with_success(self):
        """Cerrar diálogo con éxito"""
        try:
            self.result = True
            if self.dialog and self.dialog.winfo_exists():
                self.dialog.grab_release()  # Liberar el grab antes de cerrar
                self.dialog.destroy()
        except Exception as e:
            self.logger.error(f"Error al cerrar diálogo: {e}")
            self.result = True  # Asegurar que result sea True
    
    def cancel_setup(self):
        """Cancelar configuración"""
        try:
            self.result = False
            if self.dialog and self.dialog.winfo_exists():
                self.dialog.grab_release()
                self.dialog.destroy()
        except Exception as e:
            self.logger.error(f"Error al cancelar diálogo: {e}")
            self.result = False
