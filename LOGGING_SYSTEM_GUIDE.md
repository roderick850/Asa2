# 📋 Guía del Sistema de Logging Mejorado

## 🎯 **Descripción General**

Hemos implementado un sistema de logging robusto y completo que registra todos los eventos importantes del servidor ARK en archivos separados y los muestra en la interfaz de usuario de manera clara y organizada.

---

## 🔧 **Componentes del Sistema**

### **1. `utils/server_logger.py` - Logger Especializado**

**Características principales:**

- ✅ **Archivo por día**: Crea un archivo nuevo cada día (`server_events_YYYY-MM-DD.log`)
- ✅ **Ubicación organizada**: Guarda logs en `logs/server_events/`
- ✅ **Formato consistente**: `FECHA HORA | NIVEL | EVENTO | Detalles`
- ✅ **Emojis identificativos**: Cada tipo de evento tiene un emoji único
- ✅ **Persistencia**: Los eventos se guardan en disco para consulta histórica

**Métodos disponibles:**

```python
# Eventos del servidor
log_server_start(server_path, map_name, additional_info)     # 🚀
log_server_stop(reason, additional_info)                     # ⏹️
log_server_restart(reason, additional_info)                  # 🔄
log_server_crash(error_details)                             # 💥

# Actualizaciones
log_server_update_start(method)                             # 📥
log_server_update_complete(success, details)                # 📥

# Reinicios automáticos
log_automatic_restart_start(restart_info)                   # 🕐
log_automatic_restart_complete(restart_info)                # 🕐

# Backup
log_backup_event(event_type, success, details)              # 💾

# RCON
log_rcon_command(command, success, result)                  # 🎮

# Mods
log_mod_operation(operation, mod_name, mod_id, success)     # 🔧

# Configuración
log_config_change(config_type, setting_name, old, new)      # ⚙️

# Eventos personalizados
log_custom_event(event_name, details, level)                # 📋
```

### **2. `gui/main_window.py` - Integración Central**

**Funcionalidades agregadas:**

- ✅ **Instancia central**: Crea `ServerEventLogger` al inicializar
- ✅ **Método universal**: `log_server_event()` para fácil acceso desde cualquier panel
- ✅ **Actualización automática**: Cambia el nombre del servidor en el logger automáticamente
- ✅ **Recuperación de eventos**: `get_server_events()` para consultas

**Ejemplo de uso:**

```python
# Desde cualquier panel que tenga acceso a main_window
self.main_window.log_server_event("server_start",
    server_path="/path/to/server",
    map_name="TheIsland_WP")
```

### **3. Integración en Paneles**

#### **🖥️ Server Panel (`server_panel.py`)**

- ✅ **Inicio manual**: Registra cuando el usuario inicia el servidor
- ✅ **Detención manual**: Registra cuando el usuario detiene el servidor
- ✅ **Reinicio manual**: Registra cuando el usuario reinicia el servidor
- ✅ **Actualizaciones**: Registra inicio y finalización de actualizaciones

#### **🔄 Advanced Restart Panel (`advanced_restart_panel.py`)**

- ✅ **Reinicios programados**: Registra inicio y finalización de reinicios automáticos
- ✅ **Detalles completos**: Incluye si se actualizó, hizo backup, saveworld, etc.

#### **💾 Advanced Backup Panel (`advanced_backup_panel.py`)**

- ✅ **Backups manuales**: Registra cuando el usuario hace backup manual
- ✅ **Backups automáticos**: Registra backups programados
- ✅ **Estado**: Registra éxito o fallo con detalles del error

#### **🎮 RCON Panel (`rcon_panel.py`)**

- ✅ **Comandos RCON**: Registra todos los comandos ejecutados
- ✅ **Resultados**: Incluye resultado del comando (limitado a 100 caracteres)
- ✅ **Estado**: Registra éxito o fallo de cada comando

---

## 📊 **Panel de Logs Mejorado**

### **Funcionalidades de la UI:**

#### **🎮 Botón "Eventos Servidor"**

- **Función**: Muestra los eventos específicos del servidor (inicio, parada, actualizaciones, etc.)
- **Formato**: Chronological, más recientes primero
- **Límite**: Últimos 50 eventos de las últimas 24 horas
- **Ubicación**: `logs/server_events/server_events_YYYY-MM-DD.log`

#### **📋 Botón "Log App"**

- **Función**: Muestra el log general de la aplicación
- **Contenido**: Logs del sistema, errores, información general
- **Límite**: Últimas 100 líneas
- **Ubicación**: `logs/app.log`

#### **💬 Botón "Log de Chat"**

- **Función**: Logs de chat del servidor ARK (si están disponibles)

#### **❌ Botón "Log de Errores"**

- **Función**: Logs de errores del servidor ARK (si están disponibles)

#### **🖥️ Botón "Log del Servidor"**

- **Función**: Logs generales del servidor ARK (si están disponibles)

---

## 🚀 **Ejemplos de Eventos Registrados**

### **📋 Eventos del Sistema**

```
2025-08-09 00:14:47 | INFO | 📋 APLICACIÓN INICIADA | Servidor: Prueba2 | Ark Server Manager se ha iniciado correctamente
```

### **🚀 Eventos del Servidor**

```
2025-08-09 00:15:30 | INFO | 🚀 SERVIDOR INICIADO | Servidor: Prueba2 | Mapa: TheIsland_WP | PID: 12345
2025-08-09 00:16:45 | INFO | ⏹️ SERVIDOR DETENIDO | Servidor: Prueba2 | Motivo: Manual - Botón Detener | Usuario detuvo servidor desde interfaz
2025-08-09 00:17:12 | INFO | 🔄 SERVIDOR REINICIADO | Servidor: Prueba2 | Motivo: Manual - Botón Reiniciar | Usuario reinició servidor desde interfaz | Mapa: TheIsland_WP
```

### **📥 Eventos de Actualización**

```
2025-08-09 00:18:00 | INFO | 📥 ACTUALIZACIÓN INICIADA | Servidor: Prueba2 | Método: SteamCMD
2025-08-09 00:20:15 | INFO | 📥 ACTUALIZACIÓN ✅ EXITOSA | Servidor: Prueba2 | Actualización completada vía botón Actualizar
```

### **🕐 Eventos de Reinicio Automático**

```
2025-08-09 06:00:00 | INFO | 🕐 REINICIO AUTOMÁTICO INICIADO | Servidor: Prueba2 | Con actualización | Con backup | Con saveworld | Con avisos RCON
2025-08-09 06:05:30 | INFO | 🕐 REINICIO AUTOMÁTICO ✅ EXITOSO | Servidor: Prueba2 | Acciones: Actualización, Backup, Saveworld, Avisos RCON
```

### **💾 Eventos de Backup**

```
2025-08-09 00:22:45 | INFO | 💾 BACKUP ✅ EXITOSO | Servidor: Prueba2 | Tipo: manual | Backup 'Prueba2_20250809_002245.zip' creado exitosamente
2025-08-09 00:37:15 | INFO | 💾 BACKUP ✅ EXITOSO | Servidor: Prueba2 | Tipo: automático | Backup 'Prueba2_20250809_003715.zip' creado exitosamente
```

### **🎮 Eventos RCON**

```
2025-08-09 00:25:10 | INFO | 🎮 RCON ✅ EXITOSO | Servidor: Prueba2 | Comando: listplayers | Resultado: Current player count: 5
2025-08-09 00:25:30 | INFO | 🎮 RCON ✅ EXITOSO | Servidor: Prueba2 | Comando: saveworld | Resultado: World saved
```

---

## 🔍 **Cómo Usar el Sistema**

### **1. Ver Eventos en la Interfaz**

1. Abrir la pestaña **"Logs"**
2. Hacer clic en **"🎮 Eventos Servidor"** para ver eventos específicos
3. Hacer clic en **"📋 Log App"** para ver logs generales de la aplicación
4. Hacer clic en **"🔄 Actualizar"** para refrescar el contenido

### **2. Acceder a Archivos de Log**

- **Eventos del servidor**: `logs/server_events/server_events_YYYY-MM-DD.log`
- **Log de aplicación**: `logs/app.log`

### **3. Agregar Eventos Personalizados (Para Desarrolladores)**

```python
# Desde cualquier panel con acceso a main_window
self.main_window.log_server_event("custom_event",
    event_name="Mantenimiento programado",
    details="Realizando mantenimiento de rutina del servidor",
    level="info"
)
```

---

## 📈 **Beneficios del Sistema**

### **🎯 Para Usuarios Finales**

- ✅ **Historial completo**: Ve todo lo que ha pasado con el servidor
- ✅ **Interfaz clara**: Eventos organizados cronológicamente con emojis
- ✅ **Resolución de problemas**: Identifica cuándo y por qué ocurrieron errores
- ✅ **Auditoría**: Rastrea acciones realizadas en el servidor

### **🔧 Para Administradores**

- ✅ **Respaldo**: Archivos persistentes para análisis posterior
- ✅ **Debugging**: Información detallada para resolver problemas
- ✅ **Monitoreo**: Seguimiento de actividad del servidor 24/7
- ✅ **Reportes**: Base de datos para generar reportes de actividad

### **👨‍💻 Para Desarrolladores**

- ✅ **Extensible**: Fácil agregar nuevos tipos de eventos
- ✅ **Consistente**: Formato uniforme para todos los eventos
- ✅ **Centralizado**: Un solo punto de acceso para logging
- ✅ **Configurable**: Personalizable por servidor

---

## 🚀 **Estado de Implementación**

### **✅ Completado**

- [x] Sistema de logging especializado (`ServerEventLogger`)
- [x] Integración en ventana principal (`MainWindow`)
- [x] Logging en panel de servidor (inicio, parada, reinicio, actualización)
- [x] Logging en sistema de reinicios automáticos
- [x] Logging en sistema de backup
- [x] Logging en panel RCON
- [x] Panel de logs mejorado con múltiples vistas
- [x] Archivos de log persistentes por día
- [x] Eventos con emojis identificativos

### **🎯 Sistema Completamente Funcional**

El sistema de logging está **100% implementado y operativo**. Todos los eventos principales del servidor se registran automáticamente y se pueden consultar tanto en la interfaz como en los archivos de log.

**🎉 ¡El sistema está listo para uso en producción!**
