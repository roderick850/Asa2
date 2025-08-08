# Ark Survival Ascended - Administrador de Servidores

Una aplicación moderna y completa para administrar servidores de Ark Survival Ascended, desarrollada con CustomTkinter.

## 🚀 Características

### Control del Servidor

- Iniciar, detener y reiniciar el servidor
- Monitoreo en tiempo real del estado del servidor
- Configuración rápida de puerto y máximo de jugadores
- Control de procesos del servidor

### Configuración Avanzada

- Gestión completa de configuraciones del servidor
- Configuración de multiplicadores de juego (XP, cosecha, taming)
- Parámetros avanzados del servidor
- Rutas personalizables para datos y logs

### Monitoreo del Sistema

- Estadísticas en tiempo real de CPU, memoria y disco
- Monitoreo del rendimiento del servidor
- Gráficos de rendimiento (placeholder)
- Alertas de sistema

### Gestión de Jugadores

- Lista de jugadores conectados
- Acciones rápidas (expulsar todos, guardar mundo)
- Gestión individual de jugadores (kick, ban, teleport)
- Estadísticas de jugadores

### Sistema de Backups

- Creación manual y automática de backups
- Configuración de frecuencia y retención
- Restauración de backups
- Gestión de espacio en disco

### Gestión de Logs

- Visualización de logs en tiempo real
- Filtrado y búsqueda de logs
- Rotación automática de archivos de log
- Estadísticas de logs

## 📋 Requisitos

- Python 3.8 o superior
- Windows 10/11 (optimizado para Windows)
- Servidor de Ark Survival Ascended instalado

## 🛠️ Instalación

1. **Clonar o descargar el repositorio**

   ```bash
   git clone <url-del-repositorio>
   cd Asa2
   ```

2. **Activar el entorno virtual**

   ```bash
   # Windows
   .venv\Scripts\activate

   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Instalar dependencias**

   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**
   ```bash
   python main.py
   ```

## 🎮 Uso

### Primera Configuración

1. **Configurar ruta del servidor**

   - Ve a la pestaña "Configuración"
   - Haz clic en "Buscar" junto a "Ruta del servidor"
   - Selecciona el ejecutable de tu servidor Ark

2. **Configurar rutas de datos**

   - Establece la ruta donde se guardan los datos del servidor
   - Configura la ruta de logs del servidor

3. **Ajustar configuración de juego**
   - Modifica los multiplicadores según tus preferencias
   - Configura el puerto y máximo de jugadores

### Control del Servidor

1. **Iniciar servidor**

   - Ve a la pestaña "Servidor"
   - Haz clic en "Iniciar Servidor"
   - El estado cambiará a "Ejecutándose"

2. **Monitorear rendimiento**

   - Ve a la pestaña "Monitoreo"
   - Activa el monitoreo para ver estadísticas en tiempo real

3. **Gestionar jugadores**
   - Ve a la pestaña "Jugadores"
   - Verás la lista de jugadores conectados
   - Usa las acciones rápidas para gestionar el servidor

### Backups Automáticos

1. **Configurar backups**

   - Ve a la pestaña "Backups"
   - Establece la ruta de origen (datos del servidor)
   - Configura la ruta de destino para los backups
   - Ajusta la frecuencia y retención

2. **Activar backup automático**
   - Haz clic en "Iniciar Backup Automático"
   - Los backups se crearán automáticamente según la frecuencia configurada

### Gestión de Logs

1. **Configurar logs**

   - Ve a la pestaña "Logs"
   - Establece la ruta donde se encuentran los logs del servidor

2. **Monitorear logs**
   - Activa el monitoreo para ver logs en tiempo real
   - Usa filtros para buscar información específica

## 📁 Estructura del Proyecto

```
Asa2/
├── main.py                 # Archivo principal
├── requirements.txt        # Dependencias
├── README.md              # Este archivo
├── config.ini             # Configuración (se crea automáticamente)
├── gui/                   # Interfaz gráfica
│   ├── __init__.py
│   ├── main_window.py     # Ventana principal
│   └── panels/            # Paneles de la interfaz
│       ├── __init__.py
│       ├── server_panel.py
│       ├── config_panel.py
│       ├── monitoring_panel.py
│       ├── players_panel.py
│       ├── backup_panel.py
│       └── logs_panel.py
├── utils/                 # Utilidades
│   ├── __init__.py
│   ├── config_manager.py  # Gestor de configuración
│   └── logger.py          # Sistema de logging
└── logs/                  # Logs de la aplicación (se crea automáticamente)
    └── app.log
```

## ⚙️ Configuración

### Archivo config.ini

La aplicación crea automáticamente un archivo `config.ini` con la siguiente estructura:

```ini
[server]
path = C:\Path\To\ArkServer.exe
port = 7777
max_players = 70
name = Mi Servidor Ark

[game]
xp_multiplier = 1.0
harvest_multiplier = 1.0
taming_multiplier = 1.0
day_night_speed = 1.0

[advanced]
data_path = C:\Path\To\ServerData
logs_path = C:\Path\To\Logs
additional_params =

[backup]
source_path = C:\Path\To\ServerData
destination_path = C:\Path\To\Backups
frequency_hours = 24
retain_backups = 7

[logs]
logs_path = C:\Path\To\Logs
max_log_size_mb = 100
retain_logs_days = 30

[app]
theme = dark
language = es
auto_start_monitoring = false
auto_start_backup = false
```

## 🔧 Personalización

### Temas

La aplicación soporta tres temas:

- **Dark**: Tema oscuro (por defecto)
- **Light**: Tema claro
- **System**: Seguir configuración del sistema

### Idiomas

Actualmente soporta:

- Español (por defecto)
- Inglés (a implementar)

## 🐛 Solución de Problemas

### El servidor no inicia

1. Verifica que la ruta del ejecutable sea correcta
2. Asegúrate de que el puerto no esté en uso
3. Revisa los logs de la aplicación

### Error de permisos

1. Ejecuta la aplicación como administrador
2. Verifica permisos en las carpetas de datos y logs

### Problemas de rendimiento

1. Reduce la frecuencia de monitoreo
2. Cierra otras aplicaciones que consuman recursos
3. Verifica el espacio en disco

## 📝 Logs

La aplicación genera logs detallados en `logs/app.log`:

- Eventos del servidor
- Acciones de jugadores
- Errores y advertencias
- Cambios de configuración

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para contribuir:

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

Si encuentras problemas o tienes preguntas:

1. Revisa la sección de solución de problemas
2. Consulta los logs de la aplicación
3. Abre un issue en el repositorio

## 🔄 Actualizaciones

Para actualizar la aplicación:

1. Descarga la nueva versión
2. Haz backup de tu `config.ini`
3. Reemplaza los archivos
4. Restaura tu configuración

---

**Desarrollado con ❤️ para la comunidad de Ark Survival Ascended**
