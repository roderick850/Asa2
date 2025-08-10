# 🎮 Guía de Consola Integrada del Servidor ARK

## 📋 Descripción General

Se ha implementado una **consola del servidor integrada** dentro del panel de logs, que permite monitorear en tiempo real la actividad del servidor ARK directamente desde la interfaz principal.

## 🔧 Características Principales

### ✨ Sistema de Pestañas Integrado

- **📋 Sistema**: Logs generales del sistema
- **🎮 Consola**: Consola en tiempo real del servidor ARK
- **📊 Eventos**: Eventos y actividad del servidor
- **📱 Aplicación**: Registro de la aplicación

### 🎮 Funcionalidades de la Consola

#### 🔌 Conexión al Servidor

- Conexión automática via RCON
- Estado de conexión en tiempo real
- Reconexión automática en caso de desconexión

#### 📊 Monitoreo en Tiempo Real

- Actualización automática cada 5 segundos
- Información del servidor en vivo:
  - Jugadores conectados
  - Estado del mapa
  - Tiempo del juego
  - Auto-saves
  - Estadísticas de dinos y estructuras
  - Ping del servidor

#### 🎛️ Controles de la Consola

- **🧹 Limpiar**: Limpia la consola y reinicia
- **📁 Exportar**: Exporta el contenido a archivo de texto
- **📜 Auto-scroll**: Activa/desactiva el scroll automático
- **📊 Buffer**: Control del tamaño del buffer (1000 líneas por defecto)

#### 💾 Exportación y Gestión

- Exportación con timestamp automático
- Directorio `exports/` para archivos de consola
- Formato legible y organizado
- Confirmación visual de exportación exitosa

## 🚀 Cómo Usar

### 1. Acceder a la Consola

1. Ir a la pestaña **"Logs"** en la interfaz principal
2. Hacer clic en la pestaña **"🎮 Consola"**
3. La consola se inicializará automáticamente

### 2. Conectar al Servidor

```python
# Desde el código, usar:
logs_panel.connect_to_server_console(
    server_ip="192.168.1.100",
    rcon_port=32330,
    rcon_password="tu_password_rcon"
)
```

### 3. Monitorear en Tiempo Real

- La consola se actualiza automáticamente
- Los eventos aparecen con timestamps
- Colores diferenciados por tipo de mensaje:
  - 🟢 Verde: Éxito
  - 🟠 Naranja: Advertencia
  - 🔴 Rojo: Error
  - 🔵 Azul: Información

### 4. Enviar Comandos RCON

```python
# Enviar comando al servidor:
logs_panel.send_rcon_command("listplayers")
logs_panel.send_rcon_command("saveworld")
logs_panel.send_rcon_command("broadcast Mensaje del admin")
```

### 5. Exportar Consola

- Hacer clic en **"📁 Exportar"**
- El archivo se guardará en `exports/consola_servidor_YYYYMMDD_HHMMSS.txt`
- Se mostrará confirmación de exportación exitosa

## 🔗 Integración con Sistema Existente

### RCON Panel

La consola se integra con el sistema RCON existente:

- Reutiliza la configuración de conexión
- Comparte el estado de conexión
- Permite envío de comandos desde ambos paneles

### Server Manager

- Recibe eventos del servidor automáticamente
- Muestra estado en tiempo real
- Integra con el sistema de logs existente

### Event Logger

- Los eventos del servidor aparecen en la consola
- Historial completo de actividad
- Exportación de eventos específicos

## 📁 Estructura de Archivos

```
gui/panels/
├── working_logs_panel.py          # Panel principal con consola integrada
├── server_console_panel.py        # Panel de consola independiente (legacy)
└── rcon_panel.py                  # Panel RCON existente

exports/                           # Directorio de exportaciones
├── consola_servidor_20250109_143022.txt
├── consola_servidor_20250109_143156.txt
└── ...
```

## 🎯 Funcionalidades Avanzadas

### 📊 Estadísticas de la Consola

```python
stats = logs_panel.get_console_statistics()
print(f"Líneas totales: {stats['total_lines']}")
print(f"Tamaño del buffer: {stats['buffer_size']}")
print(f"Auto-scroll: {stats['auto_scroll']}")
print(f"Estado: {stats['console_active']}")
```

### 🔧 Configuración del Buffer

```python
# Cambiar tamaño máximo del buffer
logs_panel.set_max_buffer_lines(2000)

# Limpiar solo el buffer
logs_panel.clear_console_buffer()
```

### 📡 Monitoreo Personalizado

```python
# Agregar eventos personalizados
logs_panel.add_server_event("CUSTOM", "Evento personalizado del servidor")
logs_panel.add_server_output("Salida personalizada del servidor", "info")
```

## 🐛 Solución de Problemas

### Consola No Se Conecta

1. Verificar configuración RCON en `config.ini`
2. Comprobar que el servidor esté ejecutándose
3. Verificar firewall y puertos
4. Revisar logs de error en la consola

### Consola No Se Actualiza

1. Verificar que auto-scroll esté activado
2. Comprobar estado de conexión
3. Reiniciar la consola con botón "Limpiar"
4. Verificar logs de error

### Exportación Fallida

1. Verificar permisos de escritura en directorio `exports/`
2. Comprobar espacio en disco
3. Verificar que la consola tenga contenido
4. Revisar logs de error

## 🔮 Próximas Mejoras

### Funcionalidades Planificadas

- [ ] Filtros de mensajes por tipo
- [ ] Búsqueda en tiempo real
- [ ] Notificaciones push para eventos importantes
- [ ] Integración con Discord/Telegram
- [ ] Historial de comandos enviados
- [ ] Autocompletado de comandos RCON
- [ ] Temas visuales personalizables
- [ ] Exportación en múltiples formatos (JSON, CSV)

### Integración Avanzada

- [ ] API REST para acceso externo
- [ ] WebSocket para actualizaciones en tiempo real
- [ ] Base de datos para historial persistente
- [ ] Sistema de alertas configurable
- [ ] Dashboard web complementario

## 📞 Soporte

Para reportar problemas o solicitar nuevas funcionalidades:

1. Revisar logs de error en la consola
2. Verificar configuración del sistema
3. Consultar documentación existente
4. Crear issue en el repositorio del proyecto

---

**🎮 ¡Disfruta de tu nueva consola integrada del servidor ARK!**
