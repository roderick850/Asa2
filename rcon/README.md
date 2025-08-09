# 🎮 RCON para ARK Server Manager

## 📋 ¿Qué es RCON?

RCON (Remote Console) es un protocolo que permite administrar remotamente servidores de juegos. Con esta pestaña puedes ejecutar comandos administrativos en tu servidor ARK sin necesidad de estar conectado al juego.

## 📥 Descarga del Ejecutable RCON

Para usar la funcionalidad RCON, necesitas descargar un ejecutable RCON. Te recomendamos:

### ✅ Opción Recomendada: RCON CLI

1. Ve a: https://github.com/gorcon/rcon-cli/releases
2. Descarga la última versión para Windows (archivo `.exe`)
3. Coloca el archivo `.exe` en esta carpeta (`rcon/`)
4. Renómbralo a `rcon.exe` para facilitar su uso

### 🔧 Configuración del Servidor ARK

Para que RCON funcione, tu servidor ARK debe tener RCON habilitado:

```ini
# En el archivo GameUserSettings.ini de tu servidor:
[ServerSettings]
RCONEnabled=True
RCONPort=27020
ServerAdminPassword=tu_password_admin
```

## 🚀 Comandos Disponibles

### 👥 Gestión de Jugadores

- `listPlayers` - Lista todos los jugadores conectados
- `KickPlayer "NombreJugador"` - Expulsa un jugador
- `BanPlayer "NombreJugador"` - Banea un jugador

### 🌍 Gestión del Servidor

- `saveworld` - Guarda el mundo actual
- `GetServerInfo` - Información del servidor
- `broadcast "Mensaje"` - Envía mensaje a todos los jugadores
- `DoExit 30` - Apaga el servidor en 30 segundos

### 🔧 Comandos Administrativos

- `cheat GiveItem "Blueprint" 1 1 0` - Dar ítem a jugador
- `cheat SetTimeOfDay 12:00` - Cambiar hora del día
- `cheat DestroyWildDinos` - Eliminar dinosaurios salvajes

## 📝 Configuración en la App

1. **IP**: Dirección del servidor (127.0.0.1 para local)
2. **Puerto**: Puerto RCON (por defecto 27020)
3. **Password**: Password de administrador del servidor

## ⚠️ Importante

- El password RCON es el mismo que `ServerAdminPassword`
- El servidor debe estar ejecutándose para usar RCON
- Algunos comandos requieren permisos de administrador
- Siempre guarda el mundo antes de comandos destructivos

## 🔍 Resolución de Problemas

### ❌ "No se encontró ejecutable RCON"

- Asegúrate de tener un archivo `.exe` en esta carpeta
- Verifica que el archivo no esté corrupto

### ❌ "Error de conexión RCON"

- Verifica que el servidor esté ejecutándose
- Confirma que la IP y puerto sean correctos
- Asegúrate de que RCON esté habilitado en el servidor
- Verifica que el password sea correcto

### ❌ "Timeout"

- El servidor puede estar sobrecargado
- Intenta con comandos más simples primero
- Verifica la conectividad de red

## 📚 Recursos Adicionales

- [Documentación Oficial ARK RCON](https://ark.wiki.gg/wiki/Console_commands)
- [Lista Completa de Comandos](https://ark.wiki.gg/wiki/Console_commands)
- [GitHub RCON CLI](https://github.com/gorcon/rcon-cli)
