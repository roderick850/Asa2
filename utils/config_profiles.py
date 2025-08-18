import os
import json
import configparser
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class ConfigProfileManager:
    """Gestor de perfiles de configuración para GameUserSettings.ini y Game.ini"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.profiles_dir = Path("data/config_profiles")
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivo de metadatos de perfiles
        self.profiles_metadata_file = self.profiles_dir / "profiles_metadata.json"
        
        # Inicializar metadatos si no existen
        if not self.profiles_metadata_file.exists():
            self._create_empty_metadata()
    
    def _create_empty_metadata(self):
        """Crear archivo de metadatos vacío"""
        metadata = {
            "profiles": {},
            "last_updated": datetime.now().isoformat()
        }
        with open(self.profiles_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def _load_metadata(self) -> Dict:
        """Cargar metadatos de perfiles"""
        try:
            with open(self.profiles_metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al cargar metadatos de perfiles: {e}")
            return {"profiles": {}, "last_updated": datetime.now().isoformat()}
    
    def _save_metadata(self, metadata: Dict):
        """Guardar metadatos de perfiles"""
        try:
            metadata["last_updated"] = datetime.now().isoformat()
            with open(self.profiles_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al guardar metadatos de perfiles: {e}")
    
    def save_profile(self, profile_name: str, gameusersettings_path: str, game_ini_path: str, 
                    description: str = "") -> bool:
        """Guardar un perfil de configuración
        
        Args:
            profile_name: Nombre del perfil
            gameusersettings_path: Ruta al archivo GameUserSettings.ini
            game_ini_path: Ruta al archivo Game.ini
            description: Descripción opcional del perfil
            
        Returns:
            bool: True si se guardó exitosamente, False en caso contrario
        """
        try:
            # Validar nombre del perfil
            if not profile_name or not profile_name.strip():
                raise ValueError("El nombre del perfil no puede estar vacío")
            
            # Limpiar nombre del perfil para usar como nombre de archivo
            safe_name = self._sanitize_filename(profile_name.strip())
            
            # Crear directorio del perfil
            profile_dir = self.profiles_dir / safe_name
            profile_dir.mkdir(exist_ok=True)
            
            # Copiar archivos de configuración
            files_copied = []
            
            # Copiar GameUserSettings.ini si existe
            if gameusersettings_path and os.path.exists(gameusersettings_path):
                dest_gus = profile_dir / "GameUserSettings.ini"
                shutil.copy2(gameusersettings_path, dest_gus)
                files_copied.append("GameUserSettings.ini")
                if self.logger:
                    self.logger.info(f"GameUserSettings.ini copiado a perfil {profile_name}")
            
            # Copiar Game.ini si existe
            if game_ini_path and os.path.exists(game_ini_path):
                dest_game = profile_dir / "Game.ini"
                shutil.copy2(game_ini_path, dest_game)
                files_copied.append("Game.ini")
                if self.logger:
                    self.logger.info(f"Game.ini copiado a perfil {profile_name}")
            
            if not files_copied:
                raise ValueError("No se encontraron archivos de configuración para guardar")
            
            # Actualizar metadatos
            metadata = self._load_metadata()
            metadata["profiles"][safe_name] = {
                "display_name": profile_name,
                "description": description,
                "created_date": datetime.now().isoformat(),
                "files": files_copied,
                "original_paths": {
                    "gameusersettings": gameusersettings_path if os.path.exists(gameusersettings_path or "") else None,
                    "game_ini": game_ini_path if os.path.exists(game_ini_path or "") else None
                }
            }
            self._save_metadata(metadata)
            
            if self.logger:
                self.logger.info(f"Perfil '{profile_name}' guardado exitosamente con archivos: {', '.join(files_copied)}")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al guardar perfil '{profile_name}': {e}")
            return False
    
    def load_profile(self, profile_name: str, gameusersettings_dest: str, game_ini_dest: str) -> bool:
        """Cargar un perfil de configuración
        
        Args:
            profile_name: Nombre del perfil a cargar
            gameusersettings_dest: Ruta destino para GameUserSettings.ini
            game_ini_dest: Ruta destino para Game.ini
            
        Returns:
            bool: True si se cargó exitosamente, False en caso contrario
        """
        try:
            safe_name = self._sanitize_filename(profile_name)
            profile_dir = self.profiles_dir / safe_name
            
            if self.logger:
                self.logger.info(f"Iniciando carga del perfil '{profile_name}'")
                self.logger.info(f"Directorio del perfil: {profile_dir}")
                self.logger.info(f"Destino GameUserSettings: {gameusersettings_dest}")
                self.logger.info(f"Destino Game.ini: {game_ini_dest}")
            
            # Verificar si el perfil existe en metadatos
            metadata = self._load_metadata()
            profile_in_metadata = safe_name in metadata["profiles"]
            
            if not profile_dir.exists() and not profile_in_metadata:
                raise ValueError(f"El perfil '{profile_name}' no existe")
            elif not profile_dir.exists() and profile_in_metadata:
                # Perfil existe en metadatos pero no el directorio - limpiar metadatos
                del metadata["profiles"][safe_name]
                self._save_metadata(metadata)
                raise ValueError(f"El perfil '{profile_name}' estaba corrupto y ha sido eliminado. Por favor, recarga la lista de perfiles.")
            
            # Crear directorios destino si no existen (solo si las rutas no están vacías)
            if gameusersettings_dest and gameusersettings_dest.strip():
                os.makedirs(os.path.dirname(gameusersettings_dest), exist_ok=True)
                if self.logger:
                    self.logger.info(f"Directorio destino GameUserSettings creado: {os.path.dirname(gameusersettings_dest)}")
            if game_ini_dest and game_ini_dest.strip():
                os.makedirs(os.path.dirname(game_ini_dest), exist_ok=True)
                if self.logger:
                    self.logger.info(f"Directorio destino Game.ini creado: {os.path.dirname(game_ini_dest)}")
            
            files_loaded = []
            available_files = []
            
            # Verificar qué archivos están disponibles
            gus_source = profile_dir / "GameUserSettings.ini"
            game_source = profile_dir / "Game.ini"
            
            if self.logger:
                self.logger.info(f"Verificando archivo GameUserSettings en: {gus_source} - Existe: {gus_source.exists()}")
                self.logger.info(f"Verificando archivo Game.ini en: {game_source} - Existe: {game_source.exists()}")
            
            if gus_source.exists():
                available_files.append("GameUserSettings.ini")
            if game_source.exists():
                available_files.append("Game.ini")
            
            if not available_files:
                # Directorio existe pero está vacío - limpiar metadatos y directorio
                if profile_in_metadata:
                    del metadata["profiles"][safe_name]
                    self._save_metadata(metadata)
                try:
                    shutil.rmtree(profile_dir)
                except:
                    pass  # Ignorar errores al limpiar
                raise ValueError(f"El perfil '{profile_name}' no contiene archivos de configuración válidos y ha sido eliminado. Por favor, recarga la lista de perfiles.")
            
            # Cargar GameUserSettings.ini si existe en el perfil
            if gus_source.exists():
                if gameusersettings_dest and gameusersettings_dest.strip():
                    if self.logger:
                        self.logger.info(f"Copiando GameUserSettings.ini desde {gus_source} a {gameusersettings_dest}")
                    shutil.copy2(gus_source, gameusersettings_dest)
                    files_loaded.append("GameUserSettings.ini")
                    if self.logger:
                        self.logger.info(f"GameUserSettings.ini cargado exitosamente desde perfil {profile_name}")
                else:
                    # Intentar construir ruta de destino automáticamente
                    constructed_path = self._construct_gameusersettings_path()
                    if constructed_path:
                        if self.logger:
                            self.logger.info(f"Ruta de destino vacía, construyendo automáticamente: {constructed_path}")
                        # Crear directorio si no existe
                        os.makedirs(os.path.dirname(constructed_path), exist_ok=True)
                        shutil.copy2(gus_source, constructed_path)
                        files_loaded.append("GameUserSettings.ini")
                        if self.logger:
                            self.logger.info(f"GameUserSettings.ini cargado exitosamente desde perfil {profile_name} a ruta construida")
                    else:
                        if self.logger:
                            self.logger.warning(f"GameUserSettings.ini existe en el perfil pero no se pudo construir ruta de destino")
            
            # Cargar Game.ini si existe en el perfil
            if game_source.exists():
                if game_ini_dest and game_ini_dest.strip():
                    if self.logger:
                        self.logger.info(f"Copiando Game.ini desde {game_source} a {game_ini_dest}")
                    shutil.copy2(game_source, game_ini_dest)
                    files_loaded.append("Game.ini")
                    if self.logger:
                        self.logger.info(f"Game.ini cargado exitosamente desde perfil {profile_name}")
                else:
                    # Intentar construir ruta de destino automáticamente
                    constructed_path = self._construct_game_ini_path()
                    if constructed_path:
                        if self.logger:
                            self.logger.info(f"Ruta de destino vacía, construyendo automáticamente: {constructed_path}")
                        # Crear directorio si no existe
                        os.makedirs(os.path.dirname(constructed_path), exist_ok=True)
                        shutil.copy2(game_source, constructed_path)
                        files_loaded.append("Game.ini")
                        if self.logger:
                            self.logger.info(f"Game.ini cargado exitosamente desde perfil {profile_name} a ruta construida")
                    else:
                        if self.logger:
                            self.logger.warning(f"Game.ini existe en el perfil pero no se pudo construir ruta de destino")
            
            if not files_loaded:
                # Esto puede pasar si las rutas de destino están vacías
                if self.logger:
                    self.logger.error(f"No se cargaron archivos. Rutas de destino - GUS: '{gameusersettings_dest}', Game: '{game_ini_dest}'")
                raise ValueError(f"No se pudieron cargar archivos del perfil '{profile_name}'. Verifica que las rutas de destino estén configuradas correctamente.")
            
            if self.logger:
                self.logger.info(f"Perfil '{profile_name}' cargado exitosamente: {', '.join(files_loaded)}")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al cargar perfil '{profile_name}': {e}")
            return False
    
    def get_profiles_list(self) -> List[Dict]:
        """Obtener lista de perfiles disponibles
        
        Returns:
            List[Dict]: Lista de perfiles con sus metadatos
        """
        try:
            metadata = self._load_metadata()
            profiles = []
            corrupted_profiles = []
            
            for safe_name, profile_data in metadata["profiles"].items():
                profile_dir = self.profiles_dir / safe_name
                
                if profile_dir.exists():
                    # Verificar qué archivos existen realmente
                    existing_files = []
                    if (profile_dir / "GameUserSettings.ini").exists():
                        existing_files.append("GameUserSettings.ini")
                    if (profile_dir / "Game.ini").exists():
                        existing_files.append("Game.ini")
                    
                    if existing_files:
                        # Perfil válido con archivos
                        profiles.append({
                            "safe_name": safe_name,
                            "display_name": profile_data.get("display_name", safe_name),
                            "description": profile_data.get("description", ""),
                            "created_date": profile_data.get("created_date", ""),
                            "files": existing_files,
                            "files_count": len(existing_files)
                        })
                    else:
                        # Directorio existe pero está vacío
                        corrupted_profiles.append(safe_name)
                        if self.logger:
                            self.logger.warning(f"Perfil '{safe_name}' tiene directorio vacío, será eliminado")
                else:
                    # Directorio no existe pero está en metadatos
                    corrupted_profiles.append(safe_name)
                    if self.logger:
                        self.logger.warning(f"Perfil '{safe_name}' no tiene directorio, será eliminado de metadatos")
            
            # Limpiar perfiles corruptos
            if corrupted_profiles:
                metadata_changed = False
                for safe_name in corrupted_profiles:
                    if safe_name in metadata["profiles"]:
                        del metadata["profiles"][safe_name]
                        metadata_changed = True
                    
                    # Intentar eliminar directorio vacío si existe
                    profile_dir = self.profiles_dir / safe_name
                    if profile_dir.exists():
                        try:
                            shutil.rmtree(profile_dir)
                        except:
                            pass  # Ignorar errores al limpiar
                
                if metadata_changed:
                    self._save_metadata(metadata)
                    if self.logger:
                        self.logger.info(f"Eliminados {len(corrupted_profiles)} perfiles corruptos: {', '.join(corrupted_profiles)}")
            
            # Ordenar por fecha de creación (más recientes primero)
            profiles.sort(key=lambda x: x.get("created_date", ""), reverse=True)
            return profiles
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al obtener lista de perfiles: {e}")
            return []
    
    def delete_profile(self, profile_name: str) -> bool:
        """Eliminar un perfil de configuración
        
        Args:
            profile_name: Nombre del perfil a eliminar
            
        Returns:
            bool: True si se eliminó exitosamente, False en caso contrario
        """
        try:
            safe_name = self._sanitize_filename(profile_name)
            profile_dir = self.profiles_dir / safe_name
            
            # Actualizar metadatos primero (incluso si el directorio no existe)
            metadata = self._load_metadata()
            profile_existed_in_metadata = safe_name in metadata["profiles"]
            
            if profile_existed_in_metadata:
                del metadata["profiles"][safe_name]
                self._save_metadata(metadata)
            
            # Intentar eliminar directorio si existe
            if profile_dir.exists():
                try:
                    # En Windows, intentar cambiar permisos antes de eliminar
                    import stat
                    for root, dirs, files in os.walk(profile_dir):
                        for d in dirs:
                            os.chmod(os.path.join(root, d), stat.S_IWRITE)
                        for f in files:
                            os.chmod(os.path.join(root, f), stat.S_IWRITE)
                    
                    shutil.rmtree(profile_dir)
                    if self.logger:
                        self.logger.info(f"Directorio del perfil '{profile_name}' eliminado")
                except PermissionError as pe:
                    if self.logger:
                        self.logger.warning(f"No se pudo eliminar el directorio del perfil '{profile_name}': {pe}")
                        self.logger.info(f"Perfil '{profile_name}' eliminado de metadatos (directorio puede requerir eliminación manual)")
            elif not profile_existed_in_metadata:
                raise ValueError(f"El perfil '{profile_name}' no existe")
            
            if self.logger:
                self.logger.info(f"Perfil '{profile_name}' eliminado exitosamente")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al eliminar perfil '{profile_name}': {e}")
            return False
    
    def get_profile_info(self, profile_name: str) -> Optional[Dict]:
        """Obtener información detallada de un perfil
        
        Args:
            profile_name: Nombre del perfil
            
        Returns:
            Dict: Información del perfil o None si no existe
        """
        try:
            safe_name = self._sanitize_filename(profile_name)
            metadata = self._load_metadata()
            
            if safe_name not in metadata["profiles"]:
                return None
            
            profile_data = metadata["profiles"][safe_name]
            profile_dir = self.profiles_dir / safe_name
            
            # Verificar archivos existentes
            files_info = {}
            for filename in ["GameUserSettings.ini", "Game.ini"]:
                file_path = profile_dir / filename
                if file_path.exists():
                    stat = file_path.stat()
                    files_info[filename] = {
                        "exists": True,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                else:
                    files_info[filename] = {"exists": False}
            
            return {
                "safe_name": safe_name,
                "display_name": profile_data.get("display_name", safe_name),
                "description": profile_data.get("description", ""),
                "created_date": profile_data.get("created_date", ""),
                "files_info": files_info,
                "profile_dir": str(profile_dir)
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al obtener información del perfil '{profile_name}': {e}")
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """Limpiar nombre de archivo para uso seguro
        
        Args:
            filename: Nombre original
            
        Returns:
            str: Nombre limpio y seguro para usar como nombre de archivo
        """
        # Caracteres no permitidos en nombres de archivo
        invalid_chars = '<>:"/\\|?*'
        
        # Reemplazar caracteres inválidos con guiones bajos
        clean_name = "".join(c if c not in invalid_chars else "_" for c in filename)
        
        # Limitar longitud
        clean_name = clean_name[:50]
        
        # Eliminar espacios al inicio y final
        clean_name = clean_name.strip()
        
        # Si queda vacío, usar un nombre por defecto
        if not clean_name:
            clean_name = f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return clean_name
    
    def export_profile(self, profile_name: str, export_path: str) -> bool:
        """Exportar un perfil a un archivo ZIP
        
        Args:
            profile_name: Nombre del perfil a exportar
            export_path: Ruta donde guardar el archivo ZIP
            
        Returns:
            bool: True si se exportó exitosamente, False en caso contrario
        """
        try:
            import zipfile
            
            safe_name = self._sanitize_filename(profile_name)
            profile_dir = self.profiles_dir / safe_name
            
            if not profile_dir.exists():
                raise ValueError(f"El perfil '{profile_name}' no existe")
            
            # Crear archivo ZIP
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Agregar archivos INI
                for ini_file in ["GameUserSettings.ini", "Game.ini"]:
                    ini_path = profile_dir / ini_file
                    if ini_path.exists():
                        zipf.write(ini_path, ini_file)
                
                # Agregar metadatos del perfil
                metadata = self._load_metadata()
                if safe_name in metadata["profiles"]:
                    profile_metadata = {
                        "profile_info": metadata["profiles"][safe_name],
                        "export_date": datetime.now().isoformat(),
                        "exported_by": "ASA Server Manager"
                    }
                    zipf.writestr("profile_info.json", 
                                json.dumps(profile_metadata, indent=2, ensure_ascii=False))
            
            if self.logger:
                self.logger.info(f"Perfil '{profile_name}' exportado a: {export_path}")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al exportar perfil '{profile_name}': {e}")
            return False
    
    def import_profile(self, zip_path: str, profile_name: str = None) -> bool:
        """Importar un perfil desde un archivo ZIP
        
        Args:
            zip_path: Ruta al archivo ZIP a importar
            profile_name: Nombre opcional para el perfil (si no se proporciona, se usa el del ZIP)
            
        Returns:
            bool: True si se importó exitosamente, False en caso contrario
        """
        try:
            import zipfile
            
            if not os.path.exists(zip_path):
                raise ValueError(f"El archivo ZIP no existe: {zip_path}")
            
            # Extraer información del ZIP
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                # Leer metadatos si existen
                imported_metadata = None
                if "profile_info.json" in zipf.namelist():
                    metadata_content = zipf.read("profile_info.json").decode('utf-8')
                    imported_metadata = json.loads(metadata_content)
                
                # Determinar nombre del perfil
                if not profile_name:
                    if imported_metadata and "profile_info" in imported_metadata:
                        profile_name = imported_metadata["profile_info"].get("display_name", "Perfil Importado")
                    else:
                        profile_name = f"Perfil Importado {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                
                safe_name = self._sanitize_filename(profile_name)
                profile_dir = self.profiles_dir / safe_name
                profile_dir.mkdir(exist_ok=True)
                
                # Extraer archivos INI
                files_imported = []
                for ini_file in ["GameUserSettings.ini", "Game.ini"]:
                    if ini_file in zipf.namelist():
                        zipf.extract(ini_file, profile_dir)
                        files_imported.append(ini_file)
                
                if not files_imported:
                    raise ValueError("No se encontraron archivos INI válidos en el ZIP")
            
            # Actualizar metadatos
            metadata = self._load_metadata()
            
            # Usar metadatos importados si están disponibles, sino crear nuevos
            if imported_metadata and "profile_info" in imported_metadata:
                profile_data = imported_metadata["profile_info"].copy()
                profile_data["display_name"] = profile_name  # Usar el nombre especificado
                profile_data["imported_date"] = datetime.now().isoformat()
            else:
                profile_data = {
                    "display_name": profile_name,
                    "description": "Perfil importado",
                    "created_date": datetime.now().isoformat(),
                    "imported_date": datetime.now().isoformat(),
                    "files": files_imported
                }
            
            metadata["profiles"][safe_name] = profile_data
            self._save_metadata(metadata)
            
            if self.logger:
                self.logger.info(f"Perfil '{profile_name}' importado exitosamente: {', '.join(files_imported)}")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al importar perfil desde ZIP: {e}")
            return False
    
    def _construct_gameusersettings_path(self) -> str:
        """Construir ruta automática para GameUserSettings.ini basada en configuración del servidor"""
        try:
            # Intentar obtener configuración del servidor desde config_manager si está disponible
            from utils.config_manager import ConfigManager
            config_manager = ConfigManager()
            
            # Obtener la ruta del servidor desde la configuración
            server_path = config_manager.get("server", "server_path", default="")
            root_path = config_manager.get("server", "root_path", default="")
            last_server = config_manager.get("app", "last_server", default="")
            
            # Determinar la ruta del servidor
            if server_path:
                server_dir = Path(server_path)
            elif root_path and last_server:
                server_dir = Path(root_path) / last_server
            else:
                # Último fallback: buscar en rutas comunes
                possible_paths = [
                    Path("D:/ASA/Prueba"),
                    Path("D:/ASA/Prueba2"),
                    Path("D:/ASA/prueba3"),
                    Path("C:/Users/roder/OneDrive/Desktop/Nuevacarpeta/servers"),
                    Path("C:/Users/roder/OneDrive/Desktop/Nuevacarpeta/ARK_Server/ARK_Server")
                ]
                
                for path in possible_paths:
                    if path.exists():
                        server_dir = path
                        break
                else:
                    return None
            
            if server_dir and server_dir.exists():
                gus_path = server_dir / "ShooterGame" / "Saved" / "Config" / "WindowsServer" / "GameUserSettings.ini"
                return str(gus_path)
            
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al construir ruta de GameUserSettings.ini: {e}")
            return None
    
    def _construct_game_ini_path(self) -> str:
        """Construir ruta automática para Game.ini basada en configuración del servidor"""
        try:
            # Intentar obtener configuración del servidor desde config_manager si está disponible
            from utils.config_manager import ConfigManager
            config_manager = ConfigManager()
            
            # Obtener la ruta del servidor desde la configuración
            server_path = config_manager.get("server", "server_path", default="")
            root_path = config_manager.get("server", "root_path", default="")
            last_server = config_manager.get("app", "last_server", default="")
            
            # Determinar la ruta del servidor
            if server_path:
                server_dir = Path(server_path)
            elif root_path and last_server:
                server_dir = Path(root_path) / last_server
            else:
                # Último fallback: buscar en rutas comunes
                possible_paths = [
                    Path("D:/ASA/Prueba"),
                    Path("D:/ASA/Prueba2"),
                    Path("D:/ASA/prueba3"),
                    Path("C:/Users/roder/OneDrive/Desktop/Nuevacarpeta/servers"),
                    Path("C:/Users/roder/OneDrive/Desktop/Nuevacarpeta/ARK_Server/ARK_Server")
                ]
                
                for path in possible_paths:
                    if path.exists():
                        server_dir = path
                        break
                else:
                    return None
            
            if server_dir and server_dir.exists():
                game_ini_path = server_dir / "ShooterGame" / "Saved" / "Config" / "WindowsServer" / "Game.ini"
                return str(game_ini_path)
            
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al construir ruta de Game.ini: {e}")
            return None