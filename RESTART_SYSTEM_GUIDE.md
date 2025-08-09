# 🔄 Guía del Sistema de Reinicios Programados

## 📋 Descripción General

El **Sistema de Reinicios Programados** es una herramienta avanzada que permite automatizar el mantenimiento de tu servidor de Ark Survival Ascended. Incluye funcionalidades para:

- ⏰ **Reinicios programados** por días y horas específicas
- 📥 **Actualizaciones automáticas** del servidor
- 💾 **Backups automáticos** antes de reinicios
- 🎮 **Saveworld automático** via RCON
- 👤 **Reinicios manuales** con opciones avanzadas
- 📚 **Historial completo** de todos los reinicios

---

## 🎯 Características Principales

### 🔄 **Reinicios Programados**

- Selecciona **días específicos** de la semana
- Define **múltiples horas** de reinicio por día
- **Backup automático** antes del reinicio (opcional)
- **Saveworld automático** via RCON (opcional)
- **Notificaciones** en el log de la aplicación

### 📥 **Actualizaciones Automáticas**

- Se ejecutan **durante los reinicios programados** (no independientemente)
- **Dos modos**: Actualizar siempre o solo en días específicos
- **Flujo optimizado**: Detención → Actualización → Backup → Saveworld → Inicio
- Mantiene el servidor siempre actualizado sin reinicios adicionales

### ⚙️ **Opciones Avanzadas**

- **Tiempo de aviso**: Configura cuántos minutos antes avisar
- **Backup antes del reinicio**: Crear respaldo automático
- **Saveworld antes del reinicio**: Guardar mundo via RCON
- **Configuración por servidor**: Cada servidor tiene su propia configuración

---

## 📖 Manual de Uso

### 1. **Pestaña "🔄 Reinicios"**

#### **Habilitar Reinicios**

1. Marca ✅ **"Habilitar reinicios programados"**
2. Selecciona los **días de la semana** cuando quieres reinicios
3. Define las **horas de reinicio** en formato `HH:MM`
   - Ejemplo: `00:00, 06:00, 12:00, 18:00`
   - Separa múltiples horas con comas

#### **Estado del Sistema**

- 🔄 **Auto-restart activo**: Los reinicios están programados
- ⏹️ **Inactivo**: No hay reinicios programados
- **Próximo reinicio**: Muestra fecha y hora del siguiente reinicio

### 2. **Pestaña "📥 Actualizaciones"**

#### **Configurar Actualizaciones Automáticas**

Las actualizaciones se ejecutan **automáticamente durante los reinicios programados**. Tienes dos opciones:

**Opción 1: Actualizar Siempre**

- ✅ **"Actualizar servidor en TODOS los reinicios automáticos"**
- El servidor se actualiza en cada reinicio programado

**Opción 2: Días Específicos**

- ✅ **"Actualizar solo en días específicos"**
- Selecciona los días de la semana cuando quieres actualizaciones
- Solo se actualiza en reinicios que ocurran en esos días

#### **Flujo de Actualización**

1. 🛑 Detener servidor
2. 📥 **Actualizar servidor** (SteamCMD)
3. 💾 Backup (si está habilitado)
4. 🎮 Saveworld (si está habilitado)
5. ▶️ Iniciar servidor

### 3. **Pestaña "⚙️ Opciones"**

#### **Configuraciones de Seguridad**

- ✅ **Realizar backup antes del reinicio**: Crea respaldo automático
- ✅ **Ejecutar saveworld (RCON) antes del reinicio**: Guarda el mundo

#### **Avisos por RCON**

- ✅ **Enviar avisos por RCON antes del reinicio**: Notifica a los jugadores
- 📝 **Intervalos de aviso**: Define los minutos antes del reinicio para enviar avisos
  - Ejemplo: `15, 10, 5, 2, 1` (avisos a los 15, 10, 5, 2 y 1 minutos)
- 💬 **Mensaje personalizado**: Configura el mensaje que se enviará
  - Usa `{time}` para mostrar el tiempo restante
  - Ejemplo: `"⚠️ ATENCIÓN: El servidor se reiniciará en {time} minuto(s). Por favor, encuentra un lugar seguro."`

#### **Guardar Configuración**

- Haz clic en **💾 Guardar Configuración** para aplicar cambios
- La configuración se guarda **por servidor**

### 4. **Pestaña "📚 Historial"**

#### **Ver Historial**

- 📋 Lista de todos los reinicios realizados
- 🔄 **Programado** vs 👤 **Manual**
- ✅ **Exitoso** vs ❌ **Fallido**
- 📝 Detalles: Backup, Saveworld, Actualización, Avisos RCON realizados

#### **Gestión del Historial**

- 🔄 **Actualizar**: Refrescar la lista
- 🗑️ **Limpiar Historial**: Eliminar todos los registros

---

## 🚀 Reinicio Manual

### **Proceso del Reinicio Manual**

1. Haz clic en **🔄 Reinicio Manual**
2. El sistema preguntará: _"¿Deseas actualizar el servidor antes del reinicio?"_
3. **Secuencia automática**:
   - 📢 **Avisos RCON** (si están habilitados y se solicitó)
   - 💾 Backup (si está habilitado)
   - 🎮 Saveworld via RCON (si está habilitado)
   - ⏹️ Detener servidor
   - 📥 Actualizar (si se solicitó)
   - ▶️ Iniciar servidor
   - 📚 Guardar en historial

### **Barra de Progreso**

- Muestra el **estado actual** del proceso
- **Porcentaje de completado**
- **Mensajes informativos** de cada paso

---

## ⚙️ Configuración Recomendada

### **Para Servidores de Producción**

```
🔄 Reinicios:
  Días: Lunes, Miércoles, Viernes, Domingo
  Horas: 06:00, 18:00

📥 Actualizaciones:
  Modo: Días específicos (Martes, Sábado)
  Se ejecutan durante reinicios programados

⚙️ Opciones:
  ✅ Backup antes del reinicio
  ✅ Saveworld antes del reinicio
  ✅ Avisos RCON habilitados
  📝 Intervalos: 15, 10, 5, 2, 1 minutos
  💬 Mensaje: "Reinicio en {time} minuto(s)"
```

### **Para Servidores de Desarrollo**

```
🔄 Reinicios:
  Días: Todos los días
  Horas: 00:00, 12:00

📥 Actualizaciones:
  Modo: Actualizar siempre
  Se ejecutan en todos los reinicios

⚙️ Opciones:
  ✅ Backup antes del reinicio
  ✅ Saveworld antes del reinicio
  ✅ Avisos RCON habilitados
  📝 Intervalos: 10, 5, 2, 1 minutos
  💬 Mensaje: "Reinicio en {time} minuto(s)"
```

---

## 🔧 Requisitos Técnicos

### **Dependencias**

- ✅ **Python schedule**: Para programación de tareas
- ✅ **RCON habilitado**: Para saveworld automático
- ✅ **Sistema de Backup**: Para backups automáticos

### **Permisos**

- 🔧 **Escritura en carpeta data/**: Para configuraciones
- 🎮 **Control del servidor**: Para start/stop
- 📡 **Acceso a RCON**: Para saveworld

---

## 📊 Integración con Otros Sistemas

### **🛡️ Sistema de Backup**

- Los backups antes de reinicio usan el **Sistema de Backup Avanzado**
- Respeta la configuración de **compresión** y **ubicación**
- Se registra en el **historial de backups**

### **📡 Sistema RCON**

- Usa la configuración de **IP y puerto** del panel RCON
- Toma la **contraseña** del AdminPassword automáticamente
- Ejecuta `saveworld` antes de cada reinicio

### **📋 Logs del Sistema**

- Todos los eventos se registran en el **log principal**
- Mensajes diferenciados para reinicios **programados** vs **manuales**
- Errores detallados para **debugging**

---

## 🚨 Mensajes y Notificaciones

### **En el Log Principal**

- 🔄 **"Ejecutando reinicio programado"**
- 👤 **"Ejecutando reinicio manual"**
- 📢 **"Enviando avisos RCON: [X] minutos antes del reinicio"**
- 📢 **"Aviso enviado: [mensaje]"**
- 📢 **"Avisos RCON completados, iniciando reinicio"**
- ✅ **"Reinicio completado exitosamente"**
- ❌ **"Error en reinicio: [descripción]"**
- 💾 **"Backup completado antes del reinicio"**
- 🎮 **"Saveworld completado antes del reinicio"**
- 📥 **"Actualización completada"**

### **Estados del Sistema**

- 🔄 **Auto-restart activo**: Sistema funcionando
- ⏹️ **Inactivo**: Sistema detenido
- ❌ **Error en programador**: Problema de configuración

---

## 🛠️ Solución de Problemas

### **❌ "Error en programador"**

**Causa**: Configuración incorrecta de días/horas
**Solución**:

1. Verifica el formato de horas: `HH:MM`
2. Asegúrate de seleccionar al menos un día
3. Guarda la configuración nuevamente

### **❌ "Error al ejecutar saveworld"**

**Causa**: RCON no configurado o servidor no responde
**Solución**:

1. Verifica configuración RCON en pestaña correspondiente
2. Asegúrate de que RCONEnable=True en el servidor
3. Verifica IP y puerto RCON

### **❌ "Error al crear backup"**

**Causa**: Sistema de backup no configurado
**Solución**:

1. Configura el sistema de backup en la pestaña correspondiente
2. Verifica permisos de escritura en carpeta de destino
3. Asegúrate de tener suficiente espacio en disco

### **⚠️ Reinicio no se ejecuta**

**Causa**: Programador detenido o configuración incorrecta
**Solución**:

1. Deshabilita y vuelve a habilitar los reinicios programados
2. Verifica que los días/horas estén correctamente configurados
3. Revisa los logs para mensajes de error

---

## 📈 Mejores Prácticas

### **🕐 Horarios Recomendados**

- **Reinicios**: Durante horas de menor actividad (madrugada/mañana temprano)
- **Actualizaciones**: Diferentes días que los reinicios regulares
- **Backups**: Antes de cada reinicio para seguridad máxima

### **🔄 Frecuencia Recomendada**

- **Servidores pequeños**: 2-3 reinicios por semana
- **Servidores medianos**: 4-5 reinicios por semana
- **Servidores grandes**: Reinicios diarios en horarios fijos

### **💾 Backup y Seguridad**

- ✅ **Siempre** habilitar backup antes del reinicio
- ✅ **Siempre** habilitar saveworld antes del reinicio
- 🔍 **Revisar** el historial regularmente para detectar problemas

---

## 🎉 ¡Listo para Usar!

Con esta configuración, tu servidor de Ark Survival Ascended tendrá:

- ✅ **Mantenimiento automático** sin intervención manual
- ✅ **Backups de seguridad** antes de cada reinicio
- ✅ **Actualizaciones automáticas** para mantener el servidor al día
- ✅ **Historial completo** de todas las operaciones
- ✅ **Control total** con opciones de reinicio manual

**🚀 ¡Tu servidor estará siempre optimizado y actualizado!** 🚀
