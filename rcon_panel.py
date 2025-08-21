def refresh_server_info(self):
    """Actualiza la información del servidor usando comandos RCON válidos"""
    try:
        # Usar solo comandos RCON válidos para ARK
        players_result = self.execute_rcon_command_sync("ListPlayers")
        
        if players_result and "error" not in players_result.lower():
            # Procesar lista de jugadores
            lines = players_result.strip().split('\n')
            player_count = len([line for line in lines if line.strip() and 'No Players Connected' not in line])
            
            # Actualizar interfaz con información válida
            self.game_time_label.config(text="Información disponible via ListPlayers")
            self.world_info_label.config(text=f"Jugadores conectados: {player_count}")
            self.dino_count_label.config(text="Conteo de dinos no disponible via RCON")
        else:
            # Mostrar error de conexión
            self.game_time_label.config(text="Error: No se pudo conectar al servidor")
            self.world_info_label.config(text="Verificar configuración RCON")
            self.dino_count_label.config(text="Conexión RCON requerida")
            
    except Exception as e:
        self.game_time_label.config(text=f"Error: {str(e)}")
        self.world_info_label.config(text="Error de conexión RCON")
        self.dino_count_label.config(text="Verificar configuración")