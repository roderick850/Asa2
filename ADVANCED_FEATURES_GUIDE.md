# 🚀 Guía de Funcionalidades Avanzadas - Ark Server Manager

## ✨ Nuevas Funcionalidades Implementadas

### 📋 **Menú Principal Mejorado**

El botón **"Menu"** ahora despliega un menú completo con acceso rápido a todas las funcionalidades:

#### 🎮 **Acciones Rápidas**:

- **Estado del Servidor**: Va directamente a la pestaña Principal
- **Realizar Backup**: Ejecuta un backup manual inmediato
- **Reiniciar Servidor**: Reinicia el servidor con confirmación
- **Monitoreo**: Accede a la pestaña de Reinicios/Monitoreo
- **Ver Logs**: Va directamente a la pestaña de Logs

#### 🪟 **Opciones de Ventana**:

- **Siempre Visible**: Mantiene la ventana por encima de otras aplicaciones
- **Minimizar a Bandeja**: Minimiza la aplicación a la bandeja del sistema

---

## ⚙️ **Configuraciones Avanzadas**

### 🚀 **Pestaña de Inicio**

#### **🖥️ Iniciar con Windows**

- Configura la aplicación para iniciarse automáticamente con Windows
- Se agrega una entrada en el registro de Windows
- Incluye parámetro `--minimized` para inicio silencioso

#### **🎮 Auto-iniciar Servidor**

- Inicia automáticamente el último servidor usado al abrir la app
- Delay de 3 segundos para permitir que la interfaz se cargue completamente

#### **📦 Iniciar Minimizado**

- Inicia la aplicación minimizada en la bandeja del sistema
- Útil cuando se combina con inicio automático con Windows

#### **💾 Auto-backup al Iniciar**

- Realiza un backup automático cuando se inicia la aplicación
- Delay de 5 segundos para no interferir con otras operaciones

---

### 🎯 **Pestaña de Comportamiento**

#### **📮 Minimizar a Bandeja**

- Al minimizar, la aplicación va a la bandeja del sistema en lugar de la barra de tareas
- Permite mantener la aplicación ejecutándose de forma discreta

#### **🔒 Cerrar a Bandeja**

- Al cerrar la ventana, la aplicación se mantiene ejecutándose en la bandeja
- Ideal para monitoreo continuo del servidor

#### **⚠️ Confirmar Salida**

- Pide confirmación antes de cerrar completamente la aplicación
- Previene cierres accidentales

#### **🔄 Verificar Actualizaciones**

- Verifica automáticamente si hay actualizaciones disponibles
- (Funcionalidad preparada para futuras versiones)

#### **💾 Auto-guardar Configuración**

- Guarda automáticamente los cambios de configuración
- Evita pérdida de configuraciones por cierre inesperado

---

### 🎨 **Pestaña de Interfaz**

#### **📌 Siempre Visible**

- Mantiene la ventana siempre por encima de otras aplicaciones
- Útil para monitoreo continuo mientras usas otras apps

#### **📍 Recordar Posición**

- Recuerda la posición y tamaño de la ventana entre sesiones
- Restaura automáticamente la ventana donde la dejaste

#### **🎨 Tema de la Aplicación**

- **Light**: Tema claro
- **Dark**: Tema oscuro
- **System**: Sigue la configuración del sistema

#### **🔊 Sonidos de Notificación**

- Reproduce sonidos para notificaciones importantes
- Incluye notificaciones de eventos del servidor

---

### 🔧 **Pestaña Avanzado**

#### **🖥️ Ocultar Consola**

- Oculta la ventana de consola en modo debug
- Mejora la experiencia visual

#### **📊 Información del Sistema**

- Muestra información detallada del sistema:
  - Sistema operativo y versión
  - Arquitectura del sistema
  - RAM total disponible
  - Espacio libre en disco
  - Versión de Python

---

## 🔧 **Herramientas del Sistema**

### **Nuevas Herramientas Disponibles**:

#### **🔍 Verificar Archivos del Servidor**

- (En desarrollo) Verificará la integridad de los archivos del servidor

#### **🧹 Limpiar Logs Antiguos**

- Limpia logs antiguos para liberar espacio en disco

#### **📁 Abrir Carpeta del Servidor**

- Abre directamente la carpeta del servidor seleccionado en Windows Explorer

#### **💾 Exportar/Importar Configuración**

- **Exportar**: Guarda todas las configuraciones en un archivo JSON
- **Importar**: Carga configuraciones desde un archivo JSON
- Útil para backup de configuraciones o transferir entre equipos

#### **🔄 Actualizar SteamCMD**

- (En desarrollo) Actualizará SteamCMD a la última versión

#### **📊 Información del Sistema**

- Muestra información detallada del hardware y software

---

## 🌟 **Bandeja del Sistema**

### **Funcionalidades del Icono en la Bandeja**:

#### **🎮 Control del Servidor**:

- **Iniciar Servidor**: Inicia el servidor desde la bandeja
- **Detener Servidor**: Detiene el servidor desde la bandeja
- **Estado del Servidor**: Muestra/actualiza el estado actual

#### **🔧 Acciones Rápidas**:

- **Mostrar Ventana**: Restaura la ventana principal
- **Backup Manual**: Ejecuta un backup inmediato
- **Configuraciones**: Abre las configuraciones avanzadas
- **Acerca de**: Muestra información de la aplicación

#### **🔔 Notificaciones**:

- Notificaciones automáticas de eventos importantes
- Soporte para notificaciones nativas de Windows

---

## 📁 **Gestión de Configuraciones**

### **Archivo de Configuraciones**: `data/app_settings.json`

Las configuraciones se guardan automáticamente y incluyen:

```json
{
  "startup_with_windows": false,
  "auto_start_server": false,
  "minimize_to_tray": false,
  "always_on_top": false,
  "start_minimized": false,
  "close_to_tray": false,
  "auto_check_updates": true,
  "remember_window_position": true,
  "auto_backup_on_start": false,
  "confirm_exit": true,
  "hide_console": true,
  "theme_mode": "system",
  "auto_save_config": true,
  "notification_sound": true,
  "window_x": 100,
  "window_y": 100,
  "window_width": 1200,
  "window_height": 800
}
```

---

## 🎯 **Casos de Uso Recomendados**

### **👨‍💻 Administrador Activo**:

```
✅ Confirmar salida: ON
✅ Siempre visible: ON
✅ Sonidos de notificación: ON
❌ Minimizar a bandeja: OFF
❌ Iniciar con Windows: OFF
```

### **🖥️ Servidor Dedicado 24/7**:

```
✅ Iniciar con Windows: ON
✅ Auto-iniciar servidor: ON
✅ Iniciar minimizado: ON
✅ Cerrar a bandeja: ON
✅ Auto-backup al iniciar: ON
❌ Confirmar salida: OFF
```

### **🏠 Usuario Casual**:

```
✅ Recordar posición: ON
✅ Confirmar salida: ON
✅ Tema: system
❌ Iniciar con Windows: OFF
❌ Auto-iniciar servidor: OFF
```

---

## 🚀 **Cómo Usar las Nuevas Funcionalidades**

### **1. Acceder a Configuraciones Avanzadas**:

- Clic en **"Configuración"** en la barra superior
- O usar el menú **"Menu" → "Configuraciones"**

### **2. Configurar Inicio Automático**:

- Ir a **Configuraciones → Pestaña "Inicio"**
- Activar **"Iniciar con Windows"**
- Opcionalmente activar **"Auto-iniciar servidor"**

### **3. Habilitar Bandeja del Sistema**:

- Ir a **Configuraciones → Pestaña "Comportamiento"**
- Activar **"Minimizar a bandeja"** o **"Cerrar a bandeja"**

### **4. Personalizar Interfaz**:

- Ir a **Configuraciones → Pestaña "Interfaz"**
- Seleccionar tema preferido
- Configurar opciones de ventana

---

## 🔧 **Dependencias Nuevas**

Para usar todas las funcionalidades, asegúrate de tener instalado:

```bash
pip install pystray==0.19.4 win10toast==0.9
```

---

## ⚠️ **Notas Importantes**

### **Permisos de Windows**:

- El inicio automático con Windows requiere permisos para modificar el registro
- La aplicación maneja esto automáticamente, pero puede pedir confirmación

### **Compatibilidad**:

- Funcionalidades de bandeja requieren sistema operativo con soporte
- Notificaciones nativas requieren Windows 10+

### **Rendimiento**:

- Las funcionalidades avanzadas tienen un impacto mínimo en el rendimiento
- La bandeja del sistema usa recursos muy bajos cuando está minimizada

---

## 🎉 **Beneficios de las Nuevas Funcionalidades**

✅ **Mayor Comodidad**: Acceso rápido a todas las funciones  
✅ **Automatización**: Menos intervención manual requerida  
✅ **Profesionalismo**: Comportamiento similar a aplicaciones enterprise  
✅ **Flexibilidad**: Personalizable según necesidades específicas  
✅ **Eficiencia**: Mejor gestión de recursos del sistema  
✅ **Experiencia de Usuario**: Interfaz más pulida y funcional

---

**¡Disfruta de las nuevas funcionalidades avanzadas de Ark Server Manager!** 🎮🚀
