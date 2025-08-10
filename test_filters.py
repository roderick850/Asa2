#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar los filtros de consola
"""

import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_filter_patterns():
    """Probar los patrones de filtrado"""
    
    # Simular la función _should_skip_line
    def _should_skip_line(line, show_app=True, show_status=True, show_game_only=False):
        """Versión simplificada de la función de filtrado para pruebas"""
        line_lower = line.lower()
        
        # Patrones de mensajes internos de la aplicación
        app_patterns = [
            "estado del servidor actualizado",
            "ark server manager",
            "info -",
            "warning -", 
            "error -",
            "logger",
            "configurando",
            "iniciando",
            "detenido",
            "listo para conectar",
            "en funcionamiento",
            "error crítico",
            "advertencia",
            "servidor detenido exitosamente",
            "servidor detenido",
            "buscando procesos",
            "verificando procesos",
            "enviando señal",
            "esperando que el servidor termine",
            "servidor detenido correctamente",
            "verificando que el proceso se cerró",
            "no se encontraron procesos",
            "servidor completamente detenido",
            "configuración guardada correctamente"
        ]
        
        # Patrones de mensajes de estado del servidor
        status_patterns = [
            "estado del servidor actualizado",
            "configurando",
            "iniciando",
            "detenido",
            "listo para conectar",
            "en funcionamiento",
            "error crítico",
            "advertencia"
        ]
        
        # Patrones de mensajes del juego ARK
        game_patterns = [
            "player connected", "jugador conectado", "player joined", "jugador se unió",
            "player disconnected", "jugador desconectado", "world saved", "mundo guardado",
            "player spawned", "jugador apareció", "player died", "jugador murió",
            "tribe log", "log de tribu", "chat", "mensaje", "server has completed startup",
            "startup complete", "ready for connections", "listening", "escuchando",
            "advertising for join", "server is ready", "world loaded", "mundo cargado",
            "map loaded", "mapa cargado", "mod loaded", "plugin loaded", "world save",
            "backup", "shutting down", "stopping", "server stopped", "exit", "shutdown"
        ]
        
        # Aplicar filtros según configuración
        if not show_app:
            if any(pattern in line_lower for pattern in app_patterns):
                return True
                
        if not show_status:
            if any(pattern in line_lower for pattern in status_patterns):
                return True
                
        if show_game_only:
            # Si solo mostrar mensajes del juego, verificar que sea un mensaje del juego
            if not any(pattern in line_lower for pattern in game_patterns):
                return True
        
        return False
    
    # Mensajes de prueba
    test_messages = [
        # Mensajes internos de la app (deben ser filtrados por defecto)
        "Estado del servidor actualizado: 🚀 Iniciando",
        "ArkServerManager - INFO - Estado del servidor actualizado: 🔴 Detenido",
        "Logger - INFO - Configuración guardada correctamente",
        "Servidor detenido exitosamente",
        
        # Mensajes de estado del servidor (deben ser filtrados por defecto)
        "Estado del servidor actualizado: 🔧 Configurando",
        "Estado del servidor actualizado: ✅ Listo para conectar",
        "Estado del servidor actualizado: 🟢 En funcionamiento",
        
        # Mensajes del juego ARK (deben pasar por defecto)
        "Player connected: TestPlayer",
        "World saved successfully",
        "Mod loaded: StackMeMore",
        "Server has completed startup",
        "Player joined: NewPlayer",
        "Tribe log: Player built a structure",
        
        # Mensajes mixtos
        "Some random message that should pass through",
        "Error in game: Player died",
        "Warning: Low memory usage"
    ]
    
    print("🧪 PRUEBA DE FILTROS DE CONSOLA")
    print("=" * 50)
    
    # Probar configuración por defecto (solo mensajes del juego)
    print("\n📋 CONFIGURACIÓN POR DEFECTO (Solo mensajes del juego ARK):")
    print("-" * 50)
    
    for msg in test_messages:
        should_skip = _should_skip_line(msg, show_app=False, show_status=False, show_game_only=True)
        status = "❌ FILTRADO" if should_skip else "✅ MOSTRAR"
        print(f"{status}: {msg}")
    
    # Probar configuración con todos los filtros desactivados
    print("\n📋 TODOS LOS FILTROS DESACTIVADOS:")
    print("-" * 50)
    
    for msg in test_messages:
        should_skip = _should_skip_line(msg, show_app=True, show_status=True, show_game_only=False)
        status = "❌ FILTRADO" if should_skip else "✅ MOSTRAR"
        print(f"{status}: {msg}")
    
    # Probar configuración personalizada
    print("\n📋 CONFIGURACIÓN PERSONALIZADA (App: No, Estado: Sí, Solo ARK: No):")
    print("-" * 50)
    
    for msg in test_messages:
        should_skip = _should_skip_line(msg, show_app=False, show_status=True, show_game_only=False)
        status = "❌ FILTRADO" if should_skip else "✅ MOSTRAR"
        print(f"{status}: {msg}")
    
    print("\n✅ Prueba de filtros completada")

if __name__ == "__main__":
    test_filter_patterns()
