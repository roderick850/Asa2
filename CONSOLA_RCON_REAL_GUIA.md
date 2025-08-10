# 🎮 GUÍA DE CONSOLA RCON REAL - Servidor ARK

## 📋 Descripción

La consola RCON real del servidor ARK permite conectarse directamente al servidor y ejecutar comandos en tiempo real, reemplazando la simulación anterior con datos reales del servidor.

## ✨ Características Principales

### 🔌 **Conexión Real al Servidor**

- **Conexión automática**: Se conecta automáticamente cuando se selecciona un servidor
- **Configuración automática**: Obtiene IP, puerto y password desde la configuración del servidor
- **Verificación de conexión**: Prueba la conexión RCON antes de activar la consola

### 📊 **Monitoreo en Tiem Real**

- **Actualización automática**: Obtiene información del servidor cada 30 segundos
- **Comandos automáticos**: Ejecuta `ListPlayers`, `GetWorldTime`, `GetServerInfo` automáticamente
- **Estado del servidor**: Muestra información en tiempo real de jugadores, tiempo del mundo, etc.

### 🎯 **Comandos Personalizados**

- **Campo de entrada**: Permite escribir comandos RCON personalizados
- **Ejecución inmediata**: Presiona Enter o haz clic en "Ejecutar"
- **Historial de comandos**: Mantiene un registro de todos los comandos ejecutados

### 🛠️ **Controles Avanzados**

- **Botón de conexión**: Conectar/desconectar manualmente
- **Auto-scroll**: Desplazamiento automático a la última línea
- **Exportar consola**: Guardar todo el contenido en un archivo
- **Limpiar consola**: Borrar todo el contenido de la consola

## 🚀 Cómo Usar

### 1. **Acceso a la Consola**

1. Abre la aplicación ARK Server Manager
2. Ve a la pestaña **"Logs"**
3. Dentro de "Logs", selecciona la pestaña **"🎮 Consola"**

### 2. **Conexión Automática**

- La consola se conectará automáticamente cuando:
  - Selecciones un servidor en la pestaña Principal
  - El servidor tenga configurado `AdminPassword`
  - El servidor esté ejecutándose y accesible

### 3. **Conexión Manual**

Si la conexión automática falla:

1. Haz clic en **"🔌 Conectar"**
2. La consola intentará conectarse al servidor
3. Verifica que el servidor esté ejecutándose y RCON esté habilitado

### 4. **Ejecutar Comandos**

1. Escribe un comando RCON en el campo de texto
2. Presiona **Enter** o haz clic en **"▶️ Ejecutar"**
3. La respuesta aparecerá en la consola

### 5. **Comandos RCON Comunes**

```
ListPlayers          - Lista jugadores conectados
GetServerInfo        - Información del servidor
GetWorldTime         - Tiempo del mundo
SaveWorld            - Guardar el mundo
Broadcast <mensaje>  - Enviar mensaje a todos los jugadores
KickPlayer <nombre>  - Expulsar jugador
BanPlayer <nombre>   - Banear jugador
```

## ⚙️ Configuración Requerida

### **En el Servidor ARK**

1. **Habilitar RCON** en los argumentos de inicio:

   ```
   ?RCONEnable=True?RCONPort=27020
   ```

2. **Configurar AdminPassword** en `GameUserSettings.ini`:

   ```ini
   [/Script/Engine.GameSession]
   AdminPassword=tu_password_aqui
   ```

3. **Asegurar que el puerto RCON** esté abierto en el firewall

### **En la Aplicación**

1. **Seleccionar servidor** en la pestaña Principal
2. **Verificar configuración** en la pestaña Configuración
3. **Asegurar que AdminPassword** esté configurado

## 🔍 Solución de Problemas

### **❌ "No se encontró ejecutable RCON"**

- Verifica que `rcon.exe` esté en la carpeta `rcon/`
- Descarga el ejecutable RCON desde la documentación oficial

### **❌ "Error de conexión RCON"**

- Verifica que el servidor esté ejecutándose
- Confirma que RCON esté habilitado en los argumentos
- Verifica que el puerto RCON sea correcto
- Confirma que el AdminPassword sea correcto

### **❌ "Timeout en conexión"**

- El servidor puede estar sobrecargado
- Verifica la conectividad de red
- Intenta aumentar el timeout en la configuración

### **❌ "Sin respuesta del servidor"**

- El servidor puede estar en pausa
- Verifica que el servidor esté respondiendo
- Intenta reiniciar el servidor

## 📊 Información Mostrada

### **Estado de Conexión**

- 🔴 **Desconectado**: No hay conexión al servidor
- 🟢 **Conectado**: Conexión RCON activa
- 🟡 **Conectado pero sin respuesta**: Conexión establecida pero servidor no responde

### **Información en Tiempo Real**

- **👥 Jugadores**: Lista de jugadores conectados
- **⏰ Tiempo**: Tiempo actual del mundo del juego
- **📊 Estadísticas**: Información del servidor (jugadores, mapa, etc.)
- **💾 Estado**: Guardado automático, reinicios, etc.

### **Comandos Ejecutados**

- **📤 Enviando**: Comando que se está ejecutando
- **📥 Respuesta**: Respuesta del servidor
- **❌ Error**: Errores en la ejecución del comando

## 🎯 Casos de Uso

### **Administración del Servidor**

- Monitorear jugadores conectados
- Ejecutar comandos administrativos
- Verificar estado del servidor
- Enviar mensajes a jugadores

### **Debugging y Monitoreo**

- Ver logs del servidor en tiempo real
- Detectar problemas de rendimiento
- Monitorear actividad del servidor
- Verificar comandos RCON

### **Mantenimiento**

- Ejecutar comandos de mantenimiento
- Verificar backups automáticos
- Monitorear reinicios automáticos
- Verificar actualizaciones

## 🔧 Comandos Avanzados

### **Gestión de Jugadores**

```
ListPlayers                    - Listar jugadores
KickPlayer <nombre>           - Expulsar jugador
BanPlayer <nombre>            - Banear jugador
TeleportPlayer <nombre> <x> <y> <z>  - Teletransportar jugador
```

### **Gestión del Mundo**

```
SaveWorld                     - Guardar mundo
GetWorldTime                  - Obtener tiempo del mundo
SetTimeOfDay <hora>          - Establecer hora del día
SetDayNumber <día>           - Establecer día del mundo
```

### **Gestión del Servidor**

```
GetServerInfo                 - Información del servidor
Broadcast <mensaje>           - Mensaje a todos
Shutdown <segundos>           - Apagar servidor
Restart <segundos>            - Reiniciar servidor
```

## 📝 Notas Importantes

1. **Seguridad**: El password RCON debe ser seguro y no compartirse
2. **Rendimiento**: Los comandos RCON pueden afectar el rendimiento del servidor
3. **Limitaciones**: Algunos comandos pueden no estar disponibles según la versión de ARK
4. **Backup**: Siempre haz backup antes de ejecutar comandos críticos
5. **Logs**: Todos los comandos se registran en los logs de la aplicación

## 🚀 Próximas Mejoras

- [ ] **Historial de comandos**: Guardar y reutilizar comandos anteriores
- [ ] **Comandos programados**: Ejecutar comandos en horarios específicos
- [ ] **Alertas automáticas**: Notificaciones cuando ocurran eventos específicos
- [ ] **Integración con Discord**: Enviar notificaciones a Discord
- [ ] **Backup automático**: Backup automático antes de comandos críticos

---

**¡La consola RCON real está lista para usar!** 🎉

Conecta tu servidor ARK y disfruta del monitoreo en tiempo real con comandos reales.


