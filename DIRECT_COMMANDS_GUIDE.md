# ⌨️ Guía del Panel de Comandos Directos - ARK Survival Ascended

## 📋 Descripción General

El panel de **Comandos Directos** reemplaza la funcionalidad de RCON con una comunicación directa y confiable con el servidor de Ark Survival Ascended. En lugar de depender de una API externa o RCON que puede fallar, este panel se comunica directamente con el proceso del servidor usando `stdin` y `stdout`.

## 🎯 Ventajas sobre RCON

- ✅ **Comunicación directa**: No hay intermediarios que puedan fallar
- ✅ **Respuesta inmediata**: Los comandos se ejecutan instantáneamente
- ✅ **Sin configuración compleja**: Funciona automáticamente con el servidor
- ✅ **Monitoreo en tiempo real**: Estado continuo del servidor
- ✅ **Comandos nativos**: Todos los comandos del servidor de Ark están disponibles

## 🚀 Cómo Usar

### 1. **Conectar al Servidor**

```
1. Asegúrate de que el servidor esté ejecutándose
2. Selecciona el servidor en la pestaña "Principal"
3. Ve a la pestaña "Comandos Directos"
4. Haz clic en "🔌 Conectar al Servidor"
5. El estado cambiará a "✅ Conectado"
```

### 2. **Comandos Rápidos**

El panel incluye botones para comandos comunes:

- **📢 Broadcast**: Enviar mensaje a todos los jugadores
- **⏰ Tiempo**: Ver la hora del juego
- **🌤️ Clima**: Información del clima actual
- **📋 Lista Jugadores**: Ver jugadores conectados
- **💾 Guardar Mundo**: Guardar el progreso del mundo
- **🔄 Reiniciar**: Reiniciar el servidor
- **📊 Estadísticas**: Ver estadísticas del servidor
- **🌍 Información Mapa**: Detalles del mapa actual

### 3. **Comandos Personalizados**

```
1. Escribe cualquier comando en el campo "Comando"
2. Haz clic en "📤 Ejecutar"
3. El comando se enviará al servidor
4. La respuesta aparecerá en el área de resultados
```

### 4. **Monitoreo en Tiempo Real**

```
1. Una vez conectado, el monitoreo se inicia automáticamente
2. El servidor se actualiza cada 30 segundos
3. Puedes detener/reiniciar el monitoreo manualmente
4. Usa "🔄 Actualizar Ahora" para información inmediata
```

## 🔧 Comandos Disponibles

### **Comandos Básicos**
- `time` - Hora del juego
- `weather` - Estado del clima
- `listplayers` - Lista de jugadores
- `saveworld` - Guardar mundo
- `doexit` - Reiniciar servidor

### **Comandos de Administración**
- `broadcast <mensaje>` - Enviar mensaje a todos
- `kick <jugador>` - Expulsar jugador
- `ban <jugador>` - Banear jugador
- `teleport <jugador> <x> <y> <z>` - Teleportar jugador
- `giveitem <jugador> <item> <cantidad>` - Dar item

### **Comandos de Información**
- `showworldinfo` - Información del mundo
- `showmyadminmanager` - Estadísticas del servidor
- `showserverinfo` - Información del servidor
- `showplayercount` - Contador de jugadores

### **Comandos de Mods**
- `reloadmods` - Recargar mods
- `listmods` - Listar mods activos
- `modinfo <mod_id>` - Información de un mod

## 📡 Funcionalidades del Panel

### **Estado de Conexión**
- Indicador visual del estado (Conectado/Desconectado)
- Botones para conectar/desconectar
- Verificación automática del servidor

### **Comandos Rápidos**
- Botones organizados por categorías
- Comandos más utilizados con un clic
- Personalización fácil de comandos

### **Monitoreo Continuo**
- Actualización automática cada 30 segundos
- Estado del servidor en tiempo real
- Detección de desconexiones

### **Historial y Resultados**
- Registro de todos los comandos enviados
- Respuestas del servidor organizadas
- Exportación de resultados a archivo
- Copia al portapapeles

## 🛠️ Solución de Problemas

### **No puedo conectar**
- Verifica que el servidor esté ejecutándose
- Asegúrate de haber seleccionado un servidor
- El servidor debe estar en modo consola

### **Los comandos no funcionan**
- Verifica que estés conectado (estado verde)
- Algunos comandos requieren permisos de administrador
- Comprueba la sintaxis del comando

### **Monitoreo no funciona**
- El monitoreo se inicia automáticamente al conectar
- Verifica que el servidor esté respondiendo
- Puedes reiniciar el monitoreo manualmente

### **Comandos específicos no funcionan**
- Algunos comandos pueden variar según la versión de Ark
- Los mods pueden agregar o modificar comandos
- Consulta la documentación oficial de Ark para comandos específicos

## 🔄 Flujo de Trabajo Típico

```
1. 🚀 Iniciar servidor desde la pestaña "Principal"
2. 🔌 Conectar usando "Comandos Directos"
3. 📊 Monitorear estado del servidor
4. ⌨️ Ejecutar comandos según sea necesario
5. 📢 Comunicarse con jugadores
6. 💾 Guardar mundo regularmente
7. 🔌 Desconectar al terminar
```

## 💡 Consejos de Uso

### **Para Administradores**
- Mantén el monitoreo activo para supervisión continua
- Usa comandos de broadcast para comunicaciones importantes
- Guarda el mundo regularmente antes de cambios importantes
- Ten una lista de comandos útiles guardada

### **Para Monitoreo**
- El panel se actualiza automáticamente cada 30 segundos
- Puedes ajustar la frecuencia modificando el código
- Los resultados se guardan localmente para revisión posterior
- Usa la función de exportar para reportes

### **Para Comunicación**
- Los comandos de broadcast son inmediatos
- Puedes crear macros de comandos personalizados
- El historial te permite repetir comandos anteriores
- Los resultados se muestran con timestamps

## 🎮 Integración con el Servidor

Este panel se integra perfectamente con:

- **Panel Principal**: Para iniciar/detener el servidor
- **Panel de Consola**: Para ver la salida del servidor
- **Panel de Logs**: Para revisar el historial completo
- **Panel de Mods**: Para gestionar mods del servidor

¡Disfruta de un control directo y confiable de tu servidor de Ark Survival Ascended! 🎮🚀
