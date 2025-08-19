import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from datetime import datetime
from typing import Optional, Dict, List
import os

class SaveProfileDialog:
    """Diálogo para guardar un perfil de configuración"""
    
    def __init__(self, parent, profile_manager, gameusersettings_path: str = "", game_ini_path: str = ""):
        self.parent = parent
        self.profile_manager = profile_manager
        self.gameusersettings_path = gameusersettings_path
        self.game_ini_path = game_ini_path
        self.result = None
        
        # Configurar tema de CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.dialog = None
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Frame principal
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título ya está en el título de la ventana, no necesitamos otro
        
        # Frame para información de archivos
        files_frame = ctk.CTkFrame(main_frame)
        files_frame.pack(fill="x", pady=(0, 20), padx=10)
        
        files_title = ctk.CTkLabel(files_frame, text="📁 Archivos a incluir", font=("Arial", 14, "bold"))
        files_title.pack(pady=(10, 5))
        
        # Verificar qué archivos existen
        gus_exists = os.path.exists(self.gameusersettings_path or "")
        game_exists = os.path.exists(self.game_ini_path or "")
        
        # GameUserSettings.ini
        gus_icon = "✅" if gus_exists else "❌"
        gus_label = ctk.CTkLabel(files_frame, text=f"{gus_icon} GameUserSettings.ini")
        gus_label.pack(pady=2)
        
        if gus_exists:
            gus_path_label = ctk.CTkLabel(files_frame, text=f"({self.gameusersettings_path})", 
                                         text_color="gray")
            gus_path_label.pack(pady=2)
        else:
            gus_missing_label = ctk.CTkLabel(files_frame, text="(No encontrado)", 
                                            text_color="red")
            gus_missing_label.pack(pady=2)
        
        # Game.ini
        game_icon = "✅" if game_exists else "❌"
        game_label = ctk.CTkLabel(files_frame, text=f"{game_icon} Game.ini")
        game_label.pack(pady=2)
        
        if game_exists:
            game_path_label = ctk.CTkLabel(files_frame, text=f"({self.game_ini_path})", 
                                          text_color="gray")
            game_path_label.pack(pady=2)
        else:
            game_missing_label = ctk.CTkLabel(files_frame, text="(No encontrado)", 
                                             text_color="red")
            game_missing_label.pack(pady=2)
        
        # Advertencia si no hay archivos
        if not gus_exists and not game_exists:
            warning_label = ctk.CTkLabel(files_frame, 
                                        text="⚠️ No se encontraron archivos de configuración para guardar",
                                        text_color="orange")
            warning_label.pack(pady=(10, 0))
        
        # Frame para datos del perfil
        profile_frame = ctk.CTkFrame(main_frame)
        profile_frame.pack(fill="both", expand=True, pady=(0, 20), padx=10)
        
        profile_title = ctk.CTkLabel(profile_frame, text="📝 Información del perfil", font=("Arial", 14, "bold"))
        profile_title.pack(pady=(10, 5))
        
        # Nombre del perfil
        name_label = ctk.CTkLabel(profile_frame, text="Nombre del perfil:*")
        name_label.pack(anchor="w", pady=(10, 5), padx=10)
        
        self.name_entry = ctk.CTkEntry(profile_frame, font=("Arial", 12))
        self.name_entry.pack(fill="x", pady=(0, 15), padx=10)
        self.name_entry.bind('<Return>', lambda e: self.save_profile())
        
        # Descripción
        desc_label = ctk.CTkLabel(profile_frame, text="Descripción (opcional):")
        desc_label.pack(anchor="w", pady=(0, 5), padx=10)
        
        self.desc_text = ctk.CTkTextbox(profile_frame, height=120, font=("Arial", 12))
        self.desc_text.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        
        # Placeholder para descripción
        placeholder_text = "Ej: Configuración PvP con experiencia x10, taming rápido, recursos abundantes..."
        self.desc_text.insert("0.0", placeholder_text)
        
        def on_desc_focus_in(event):
            if self.desc_text.get("0.0", "end").strip() == placeholder_text:
                self.desc_text.delete("0.0", "end")
        
        def on_desc_focus_out(event):
            if not self.desc_text.get("0.0", "end").strip():
                self.desc_text.insert("0.0", placeholder_text)
        
        self.desc_text.bind('<FocusIn>', on_desc_focus_in)
        self.desc_text.bind('<FocusOut>', on_desc_focus_out)
        
        # Botones
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", pady=(10, 0), padx=10)
        
        cancel_button = ctk.CTkButton(buttons_frame, text="❌ Cancelar", command=self.cancel)
        cancel_button.pack(side="right", padx=(10, 0))
        
        save_button = ctk.CTkButton(buttons_frame, text="💾 Guardar Perfil", command=self.save_profile)
        save_button.pack(side="right")
        
        # Hacer que el botón Guardar sea el predeterminado
        self.dialog.bind('<Return>', lambda e: self.save_profile())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
    
    def save_profile(self):
        """Guardar el perfil"""
        name = self.name_entry.get().strip()
        
        if not name:
            messagebox.showerror("Error", "El nombre del perfil es obligatorio", parent=self.dialog)
            self.name_entry.focus_set()
            return
        
        # Obtener descripción
        desc = self.desc_text.get("0.0", "end").strip()
        placeholder_text = "Ej: Configuración PvP con experiencia x10, taming rápido, recursos abundantes..."
        if desc == placeholder_text:
            desc = ""
        
        # Verificar si hay archivos para guardar
        gus_exists = os.path.exists(self.gameusersettings_path or "")
        game_exists = os.path.exists(self.game_ini_path or "")
        
        if not gus_exists and not game_exists:
            messagebox.showerror("Error", 
                               "No se encontraron archivos de configuración para guardar.\n\n"
                               "Asegúrate de que los archivos GameUserSettings.ini y/o Game.ini existan.",
                               parent=self.dialog)
            return
        
        # Verificar si el perfil ya existe
        existing_profiles = self.profile_manager.get_profiles_list()
        safe_name = self.profile_manager._sanitize_filename(name)
        
        profile_exists = any(p['safe_name'] == safe_name for p in existing_profiles)
        
        if profile_exists:
            response = messagebox.askyesno("Perfil existente",
                                         f"Ya existe un perfil con el nombre '{name}'.\n\n"
                                         "¿Deseas sobrescribirlo?",
                                         parent=self.dialog)
            if not response:
                return
        
        # Guardar perfil
        try:
            success = self.profile_manager.save_profile(
                profile_name=name,
                gameusersettings_path=self.gameusersettings_path,
                game_ini_path=self.game_ini_path,
                description=desc
            )
            
            if success:
                self.result = {
                    'name': name,
                    'description': desc,
                    'saved': True
                }
                messagebox.showinfo("Éxito", 
                                  f"El perfil '{name}' se ha guardado exitosamente.",
                                  parent=self.dialog)
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", 
                                   "No se pudo guardar el perfil. Revisa los logs para más detalles.",
                                   parent=self.dialog)
        
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Error al guardar el perfil:\n{str(e)}",
                               parent=self.dialog)
    
    def cancel(self):
        """Cancelar y cerrar diálogo"""
        self.result = None
        self.dialog.destroy()
    
    def show(self) -> Optional[Dict]:
        """Mostrar el diálogo y retornar el resultado"""
        # Crear ventana del diálogo
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("💾 Guardar Perfil de Configuración")
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)
        
        # Centrar ventana
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Configurar interfaz
        self.setup_ui()
        
        # Enfocar en el campo de nombre
        self.name_entry.focus()
        
        # Esperar hasta que se cierre el diálogo
        self.dialog.wait_window()
        return self.result


class LoadProfileDialog:
    """Diálogo para cargar un perfil de configuración"""
    
    def __init__(self, parent, profile_manager, gameusersettings_dest: str = "", game_ini_dest: str = ""):
        self.parent = parent
        self.profile_manager = profile_manager
        self.gameusersettings_dest = gameusersettings_dest
        self.game_ini_dest = game_ini_dest
        self.result = None
        
        # Configurar tema de CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.dialog = None
        self.profiles_listbox = None
        self.selected_profile = None
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Frame principal
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # El título ya está en la ventana, no necesitamos otro
        
        # Frame para lista de perfiles
        profiles_frame = ctk.CTkFrame(main_frame)
        profiles_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Título del frame de perfiles
        profiles_title = ctk.CTkLabel(profiles_frame, text="📋 Perfiles disponibles", 
                                     font=ctk.CTkFont(size=14, weight="bold"))
        profiles_title.pack(pady=(10, 5))
        
        # Treeview para mostrar perfiles
        tree_frame = ctk.CTkFrame(profiles_frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Configurar Treeview
        columns = ('name', 'description', 'files', 'date')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=10)
        
        # Configurar columnas
        self.tree.heading('name', text='Nombre')
        self.tree.heading('description', text='Descripción')
        self.tree.heading('files', text='Archivos')
        self.tree.heading('date', text='Fecha de creación')
        
        self.tree.column('name', width=150, minwidth=100)
        self.tree.column('description', width=250, minwidth=150)
        self.tree.column('files', width=120, minwidth=80)
        self.tree.column('date', width=150, minwidth=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview y scrollbars
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind eventos
        self.tree.bind('<<TreeviewSelect>>', self.on_profile_select)
        self.tree.bind('<Double-1>', lambda e: self.load_profile())
        
        # Frame para información del perfil seleccionado
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", pady=(0, 20))
        
        # Título del frame de información
        info_title = ctk.CTkLabel(info_frame, text="ℹ️ Información del perfil", 
                                 font=ctk.CTkFont(size=14, weight="bold"))
        info_title.pack(pady=(10, 5))
        
        self.info_text = ctk.CTkTextbox(info_frame, height=100, wrap="word")
        self.info_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.info_text.configure(state="disabled")
        
        # Frame para botones de acción
        action_frame = ctk.CTkFrame(main_frame)
        action_frame.pack(fill="x", pady=(0, 10))
        
        # Botones de gestión
        refresh_button = ctk.CTkButton(action_frame, text="🔄 Actualizar Lista", command=self.load_profiles)
        refresh_button.pack(side="left", padx=10, pady=10)
        
        self.update_profile_button = ctk.CTkButton(action_frame, text="⬆️ Actualizar Perfil", 
                                                  command=self.update_selected_profile, state="disabled")
        self.update_profile_button.pack(side="left", padx=(0, 10), pady=10)
        
        delete_button = ctk.CTkButton(action_frame, text="🗑️ Eliminar", command=self.delete_profile)
        delete_button.pack(side="left", padx=(0, 10), pady=10)
        
        export_button = ctk.CTkButton(action_frame, text="📤 Exportar", command=self.export_profile)
        export_button.pack(side="left", padx=(0, 10), pady=10)
        
        import_button = ctk.CTkButton(action_frame, text="📥 Importar", command=self.import_profile)
        import_button.pack(side="left", padx=(0, 10), pady=10)
        
        # Botones principales
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x")
        
        cancel_button = ctk.CTkButton(buttons_frame, text="❌ Cancelar", command=self.cancel)
        cancel_button.pack(side="right", padx=10, pady=10)
        
        self.load_button = ctk.CTkButton(buttons_frame, text="📂 Cargar Perfil", 
                                        command=self.load_profile, state="disabled")
        self.load_button.pack(side="right", padx=(0, 10), pady=10)
        
        # Binds de teclado
        self.dialog.bind('<Return>', lambda e: self.load_profile() if self.load_button.cget('state') == 'normal' else None)
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        self.dialog.bind('<Delete>', lambda e: self.delete_profile())
        self.dialog.bind('<F5>', lambda e: self.load_profiles())
    
    def load_profiles(self):
        """Cargar lista de perfiles"""
        # Limpiar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Obtener perfiles
        self.profiles = self.profile_manager.get_profiles_list()
        
        if not self.profiles:
            # Mostrar mensaje si no hay perfiles
            self.tree.insert('', tk.END, values=('No hay perfiles guardados', '', '', ''))
            self.update_info_text("No se encontraron perfiles de configuración guardados.")
            return
        
        # Agregar perfiles al treeview
        for profile in self.profiles:
            # Formatear fecha
            date_str = ""
            if profile.get('created_date'):
                try:
                    date_obj = datetime.fromisoformat(profile['created_date'].replace('Z', '+00:00'))
                    date_str = date_obj.strftime('%Y-%m-%d %H:%M')
                except:
                    date_str = profile['created_date'][:16]  # Fallback
            
            # Formatear archivos
            files_str = f"{profile['files_count']} archivo(s)"
            if profile['files']:
                files_str = ', '.join(profile['files'])
            
            # Truncar descripción si es muy larga
            description = profile.get('description', '')
            if len(description) > 50:
                description = description[:47] + "..."
            
            self.tree.insert('', tk.END, values=(
                profile['display_name'],
                description,
                files_str,
                date_str
            ))
        
        self.update_info_text("Selecciona un perfil para ver más información.")
    
    def on_profile_select(self, event):
        """Manejar selección de perfil"""
        selection = self.tree.selection()
        if not selection or not self.profiles:
            self.load_button.configure(state=tk.DISABLED)
            self.update_profile_button.configure(state=tk.DISABLED)
            self.update_info_text("")
            return
        
        # Obtener índice del perfil seleccionado
        item = selection[0]
        index = self.tree.index(item)
        
        if index >= len(self.profiles):
            return
        
        profile = self.profiles[index]
        
        # Habilitar botones
        self.load_button.configure(state="normal")
        self.update_profile_button.configure(state="normal")
        
        # Mostrar información detallada
        info_text = f"Nombre: {profile['display_name']}\n"
        
        if profile.get('description'):
            info_text += f"Descripción: {profile['description']}\n"
        
        if profile.get('created_date'):
            try:
                date_obj = datetime.fromisoformat(profile['created_date'].replace('Z', '+00:00'))
                date_str = date_obj.strftime('%d/%m/%Y a las %H:%M')
                info_text += f"Creado: {date_str}\n"
            except:
                info_text += f"Creado: {profile['created_date']}\n"
        
        # Mostrar información de última actualización si está disponible
        profile_info = self.profile_manager.get_profile_info(profile['display_name'])
        if profile_info and profile_info.get('last_updated'):
            try:
                update_date_obj = datetime.fromisoformat(profile_info['last_updated'].replace('Z', '+00:00'))
                update_date_str = update_date_obj.strftime('%d/%m/%Y a las %H:%M')
                info_text += f"Última actualización: {update_date_str}\n"
            except:
                info_text += f"Última actualización: {profile_info['last_updated']}\n"
        
        if profile.get('files'):
            info_text += f"Archivos incluidos: {', '.join(profile['files'])}"
        
        self.update_info_text(info_text)
    
    def update_info_text(self, text: str):
        """Actualizar texto de información"""
        self.info_text.configure(state="normal")
        self.info_text.delete("0.0", "end")
        self.info_text.insert("0.0", text)
        self.info_text.configure(state="disabled")
    
    def load_profile(self):
        """Cargar el perfil seleccionado"""
        selection = self.tree.selection()
        if not selection or not self.profiles:
            return
        
        index = self.tree.index(selection[0])
        if index >= len(self.profiles):
            return
        
        profile = self.profiles[index]
        
        # Confirmar carga
        response = messagebox.askyesno("Confirmar carga",
                                     f"¿Estás seguro de que deseas cargar el perfil '{profile['display_name']}'?\n\n"
                                     "Esto sobrescribirá los archivos de configuración actuales.",
                                     parent=self.dialog)
        if not response:
            return
        
        # Cargar perfil
        try:
            success = self.profile_manager.load_profile(
                profile_name=profile['display_name'],
                gameusersettings_dest=self.gameusersettings_dest,
                game_ini_dest=self.game_ini_dest
            )
            
            if success:
                self.result = {
                    'profile': profile,
                    'loaded': True
                }
                messagebox.showinfo("Éxito", 
                                  f"El perfil '{profile['display_name']}' se ha cargado exitosamente.",
                                  parent=self.dialog)
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", 
                                   "No se pudo cargar el perfil. Revisa los logs para más detalles.",
                                   parent=self.dialog)
        
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Error al cargar el perfil:\n{str(e)}",
                               parent=self.dialog)
    
    def delete_profile(self):
        """Eliminar el perfil seleccionado"""
        selection = self.tree.selection()
        if not selection or not self.profiles:
            return
        
        index = self.tree.index(selection[0])
        if index >= len(self.profiles):
            return
        
        profile = self.profiles[index]
        
        # Confirmar eliminación
        response = messagebox.askyesno("Confirmar eliminación",
                                     f"¿Estás seguro de que deseas eliminar el perfil '{profile['display_name']}'?\n\n"
                                     "Esta acción no se puede deshacer.",
                                     parent=self.dialog)
        if not response:
            return
        
        # Eliminar perfil
        try:
            success = self.profile_manager.delete_profile(profile['display_name'])
            
            if success:
                messagebox.showinfo("Éxito", 
                                  f"El perfil '{profile['display_name']}' se ha eliminado exitosamente.",
                                  parent=self.dialog)
                self.load_profiles()  # Recargar lista
            else:
                messagebox.showerror("Error", 
                                   "No se pudo eliminar el perfil. Revisa los logs para más detalles.",
                                   parent=self.dialog)
        
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Error al eliminar el perfil:\n{str(e)}",
                               parent=self.dialog)
    
    def export_profile(self):
        """Exportar el perfil seleccionado"""
        selection = self.tree.selection()
        if not selection or not self.profiles:
            messagebox.showwarning("Advertencia", "Selecciona un perfil para exportar.", parent=self.dialog)
            return
        
        index = self.tree.index(selection[0])
        if index >= len(self.profiles):
            return
        
        profile = self.profiles[index]
        
        # Seleccionar ubicación de exportación
        filename = f"perfil_{profile['safe_name']}.zip"
        export_path = filedialog.asksaveasfilename(
            parent=self.dialog,
            title="Exportar perfil",
            defaultextension=".zip",
            filetypes=[("Archivos ZIP", "*.zip"), ("Todos los archivos", "*.*")],
            initialvalue=filename
        )
        
        if not export_path:
            return
        
        # Exportar perfil
        try:
            success = self.profile_manager.export_profile(profile['display_name'], export_path)
            
            if success:
                messagebox.showinfo("Éxito", 
                                  f"El perfil '{profile['display_name']}' se ha exportado exitosamente a:\n{export_path}",
                                  parent=self.dialog)
            else:
                messagebox.showerror("Error", 
                                   "No se pudo exportar el perfil. Revisa los logs para más detalles.",
                                   parent=self.dialog)
        
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Error al exportar el perfil:\n{str(e)}",
                               parent=self.dialog)
    
    def import_profile(self):
        """Importar un perfil desde archivo ZIP"""
        # Seleccionar archivo ZIP
        zip_path = filedialog.askopenfilename(
            parent=self.dialog,
            title="Importar perfil",
            filetypes=[("Archivos ZIP", "*.zip"), ("Todos los archivos", "*.*")]
        )
        
        if not zip_path:
            return
        
        # Pedir nombre para el perfil importado
        import_dialog = ImportProfileNameDialog(self.dialog)
        result = import_dialog.show()
        
        if not result:
            return
        
        profile_name = result['name']
        
        # Importar perfil
        try:
            success = self.profile_manager.import_profile(zip_path, profile_name)
            
            if success:
                messagebox.showinfo("Éxito", 
                                  f"El perfil '{profile_name}' se ha importado exitosamente.",
                                  parent=self.dialog)
                self.load_profiles()  # Recargar lista
            else:
                messagebox.showerror("Error", 
                                   "No se pudo importar el perfil. Revisa los logs para más detalles.",
                                   parent=self.dialog)
        
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Error al importar el perfil:\n{str(e)}",
                               parent=self.dialog)
    
    def update_selected_profile(self):
        """Actualizar el perfil seleccionado con los archivos de configuración actuales"""
        selection = self.tree.selection()
        if not selection or not self.profiles:
            return
        
        index = self.tree.index(selection[0])
        if index >= len(self.profiles):
            return
        
        profile = self.profiles[index]
        
        # Confirmar actualización
        response = messagebox.askyesno("Confirmar actualización",
                                     f"¿Estás seguro de que deseas actualizar el perfil '{profile['display_name']}'?\n\n"
                                     "Esto sobrescribirá los archivos guardados en el perfil con los archivos de configuración actuales.",
                                     parent=self.dialog)
        if not response:
            return
        
        # Actualizar perfil
        try:
            success = self.profile_manager.update_profile(
                profile_name=profile['display_name'],
                gameusersettings_path=self.gameusersettings_dest,
                game_ini_path=self.game_ini_dest
            )
            
            if success:
                messagebox.showinfo("Éxito", 
                                  f"El perfil '{profile['display_name']}' se ha actualizado exitosamente con los archivos actuales.",
                                  parent=self.dialog)
                self.load_profiles()  # Recargar lista para mostrar cambios
            else:
                messagebox.showerror("Error", 
                                   "No se pudo actualizar el perfil. Revisa los logs para más detalles.",
                                   parent=self.dialog)
        
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Error al actualizar el perfil:\n{str(e)}",
                               parent=self.dialog)
    
    def cancel(self):
        """Cancelar y cerrar diálogo"""
        self.result = None
        self.dialog.destroy()
    
    def show(self) -> Optional[Dict]:
        """Mostrar el diálogo y retornar el resultado"""
        # Crear ventana del diálogo
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("📂 Cargar Perfil de Configuración")
        self.dialog.geometry("800x600")
        self.dialog.resizable(True, True)
        
        # Centrar ventana
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Configurar interfaz
        self.setup_ui()
        
        # Cargar perfiles
        self.load_profiles()
        
        # Esperar hasta que se cierre el diálogo
        self.dialog.wait_window()
        return self.result


class ImportProfileNameDialog:
    """Diálogo para ingresar el nombre al importar un perfil"""
    
    def __init__(self, parent, suggested_name: str = ""):
        self.parent = parent
        self.suggested_name = suggested_name
        self.result = None
        
        # Configurar tema de CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.dialog = None
        self.name_entry = None
    
    def show(self) -> Optional[Dict]:
        """Mostrar el diálogo y retornar el resultado"""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("📥 Importar Perfil")
        self.dialog.geometry("450x250")
        self.dialog.resizable(False, False)
        
        # Centrar ventana
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        
        # Enfocar en el campo de nombre
        self.name_entry.focus()
        if self.suggested_name:
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, self.suggested_name)
            self.name_entry.select_range(0, "end")
        else:
            # Sugerir nombre por defecto
            default_name = f"Perfil Importado {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            self.name_entry.insert(0, default_name)
            self.name_entry.select_range(0, "end")
        
        # Esperar hasta que se cierre el diálogo
        self.dialog.wait_window()
        
        return self.result
    
    def _create_widgets(self):
        """Crear los widgets del diálogo"""
        # Frame principal
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame, 
            text="📥 Importar Perfil de Configuración",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(15, 25))
        
        # Frame de entrada
        input_frame = ctk.CTkFrame(main_frame)
        input_frame.pack(fill="x", padx=15, pady=(0, 25))
        
        # Instrucción
        instruction_label = ctk.CTkLabel(
            input_frame,
            text="Ingresa un nombre para el perfil importado:",
            font=ctk.CTkFont(size=12)
        )
        instruction_label.pack(pady=(20, 8))
        
        # Campo de nombre
        self.name_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Nombre del perfil...",
            font=ctk.CTkFont(size=12),
            height=35
        )
        self.name_entry.pack(fill="x", padx=15, pady=(0, 20))
        
        # Frame de botones
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=15)
        
        # Botón cancelar
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="❌ Cancelar",
            command=self._cancel,
            fg_color="gray",
            hover_color="darkgray",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=35
        )
        cancel_btn.pack(side="right", padx=(10, 15), pady=15)
        
        # Botón importar
        import_btn = ctk.CTkButton(
            button_frame,
            text="📥 Importar",
            command=self._import_profile,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=35
        )
        import_btn.pack(side="right", pady=15)
        
        # Binds
        self.dialog.bind('<Return>', lambda e: self._import_profile())
        self.dialog.bind('<Escape>', lambda e: self._cancel())
    
    def _import_profile(self):
        """Importar el perfil con el nombre especificado"""
        name = self.name_entry.get().strip()
        
        if not name:
            messagebox.showerror("Error", "El nombre del perfil es obligatorio", parent=self.dialog)
            self.name_entry.focus()
            return
        
        self.result = {'name': name}
        self.dialog.destroy()
    
    def _cancel(self):
        """Cancelar el diálogo"""
        self.result = None
        self.dialog.destroy()