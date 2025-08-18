# Diseño de Arquitectura para Sistema de Cluster ARK

## Análisis de la Arquitectura Actual

### Estructura Actual (Servidor Individual)
- **ConfigManager**: Maneja configuración centralizada en `config.ini`
- **Datos por Servidor**: Almacenados en archivos JSON en carpeta `data/`
- **Paneles**: Cada panel maneja un servidor a la vez
- **ServerManager**: Gestiona operaciones de un servidor individual
- **Selección de Servidor**: Dropdown que permite cambiar entre servidores

### Limitaciones Actuales
1. Solo un servidor activo a la vez
2. No hay vista consolidada de múltiples servidores
3. Operaciones secuenciales (no paralelas)
4. Monitoreo individual por servidor
5. Backup individual por servidor

## Diseño de Arquitectura de Cluster

### 1. Componentes Principales

#### A. ClusterManager (Nuevo)
```python
class ClusterManager:
    def __init__(self, config_manager):
        self.servers = {}  # {server_name: ServerInstance}
        self.cluster_config = {}  # Configuración del cluster
        self.active_servers = set()  # Servidores actualmente ejecutándose
```

#### B. ServerInstance (Nuevo)
```python
class ServerInstance:
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.server_manager = ServerManager(config)
        self.status = "stopped"
        self.last_update = None
```

#### C. ClusterConfigManager (Extensión)
```python
class ClusterConfigManager(ConfigManager):
    def __init__(self):
        super().__init__()
        self.cluster_configs = {}  # Configuraciones por cluster
        self.server_relationships = {}  # Relaciones entre servidores
```

### 2. Estructura de Datos del Cluster

#### A. Configuración del Cluster (`data/cluster_config.json`)
```json
{
  "cluster_id": "my_ark_cluster",
  "cluster_name": "Mi Cluster ARK",
  "servers": {
    "island": {
      "name": "The Island",
      "map": "TheIsland_WP",
      "port": 7777,
      "query_port": 27015,
      "rcon_port": 32330,
      "priority": 1,
      "auto_start": true,
      "transfer_allowed": true
    },
    "center": {
      "name": "The Center",
      "map": "TheCenter_WP",
      "port": 7778,
      "query_port": 27016,
      "rcon_port": 32331,
      "priority": 2,
      "auto_start": true,
      "transfer_allowed": true
    },
    "scorched": {
      "name": "Scorched Earth",
      "map": "ScorchedEarth_WP",
      "port": 7779,
      "query_port": 27017,
      "rcon_port": 32332,
      "priority": 3,
      "auto_start": false,
      "transfer_allowed": true
    }
  },
  "shared_settings": {
    "cluster_directory_override": "MyClusterSaves",
    "prevent_download_survivors": false,
    "prevent_download_items": false,
    "prevent_download_dinos": false,
    "prevent_upload_survivors": false,
    "prevent_upload_items": false,
    "prevent_upload_dinos": false,
    "max_tribute_characters": 5,
    "max_tribute_dinos": 10,
    "max_tribute_items": 50
  },
  "backup_settings": {
    "coordinated_backup": true,
    "backup_schedule": "0 2 * * *",  # Cron format
    "retention_days": 7,
    "compress_backups": true
  },
  "monitoring": {
    "check_interval": 30,  # segundos
    "restart_on_crash": true,
    "max_restart_attempts": 3,
    "notification_webhook": ""
  }
}
```

#### B. Estado del Cluster (`data/cluster_status.json`)
```json
{
  "cluster_id": "my_ark_cluster",
  "last_update": "2025-01-17T10:30:00Z",
  "servers": {
    "island": {
      "status": "running",
      "pid": 12345,
      "uptime": 3600,
      "players_online": 5,
      "last_backup": "2025-01-17T02:00:00Z",
      "memory_usage": 2048,
      "cpu_usage": 45.2
    },
    "center": {
      "status": "running",
      "pid": 12346,
      "uptime": 3500,
      "players_online": 3,
      "last_backup": "2025-01-17T02:00:00Z",
      "memory_usage": 1800,
      "cpu_usage": 38.7
    },
    "scorched": {
      "status": "stopped",
      "pid": null,
      "uptime": 0,
      "players_online": 0,
      "last_backup": "2025-01-16T02:00:00Z",
      "memory_usage": 0,
      "cpu_usage": 0
    }
  },
  "cluster_stats": {
    "total_players": 8,
    "total_memory": 3848,
    "average_cpu": 41.95,
    "active_servers": 2
  }
}
```

### 3. Interfaz de Usuario del Cluster

#### A. Panel Principal del Cluster
- **Vista de Resumen**: Estado de todos los servidores
- **Controles Globales**: Iniciar/Detener todo el cluster
- **Estadísticas Consolidadas**: Jugadores totales, uso de recursos
- **Alertas del Cluster**: Notificaciones importantes

#### B. Vista de Servidores Múltiples
- **Grid de Servidores**: Tarjetas con estado de cada servidor
- **Acciones Rápidas**: Iniciar/Detener/Reiniciar por servidor
- **Indicadores Visuales**: Estado, jugadores, recursos
- **Filtros**: Por estado, mapa, prioridad

#### C. Panel de Monitoreo del Cluster
- **Gráficos en Tiempo Real**: CPU, RAM, jugadores
- **Logs Consolidados**: Vista unificada de todos los servidores
- **Historial de Eventos**: Timeline de eventos del cluster
- **Alertas Configurables**: Umbrales personalizables

### 4. Funcionalidades del Cluster

#### A. Gestión de Servidores
- **Inicio Secuencial**: Servidores por prioridad
- **Inicio Paralelo**: Todos los servidores simultáneamente
- **Reinicio Coordinado**: Reinicio escalonado para mantener disponibilidad
- **Detención Graceful**: Guardar y cerrar ordenadamente

#### B. Transferencia de Personajes/Items
- **Configuración de Transferencias**: Entre qué servidores permitir
- **Monitoreo de Transferencias**: Log de movimientos
- **Restricciones**: Límites por tipo de contenido
- **Validación**: Verificar integridad de transferencias

#### C. Backup Coordinado
- **Backup Simultáneo**: Todos los servidores al mismo tiempo
- **Backup Escalonado**: Uno por uno para reducir carga
- **Verificación de Integridad**: Validar backups automáticamente
- **Restauración del Cluster**: Restaurar todo el cluster a un punto

#### D. Monitoreo Avanzado
- **Health Checks**: Verificación automática de estado
- **Auto-Restart**: Reinicio automático en caso de crash
- **Notificaciones**: Discord/Webhook/Email
- **Métricas**: Recolección y almacenamiento de estadísticas

### 5. Configuración de Red del Cluster

#### A. Puertos Automáticos
```python
def assign_cluster_ports(base_port=7777):
    ports = {}
    for i, server in enumerate(cluster_servers):
        ports[server] = {
            'game_port': base_port + i,
            'query_port': base_port + 100 + i,
            'rcon_port': base_port + 200 + i
        }
    return ports
```

#### B. Validación de Puertos
- **Detección de Conflictos**: Verificar puertos disponibles
- **Asignación Automática**: Encontrar puertos libres
- **Configuración de Firewall**: Sugerencias de reglas

### 6. Implementación por Fases

#### Fase 1: Infraestructura Base
1. ClusterManager y ServerInstance
2. Configuración básica del cluster
3. Vista de múltiples servidores
4. Operaciones básicas (start/stop)

#### Fase 2: Monitoreo y Control
1. Monitoreo en tiempo real
2. Logs consolidados
3. Alertas básicas
4. Panel de control avanzado

#### Fase 3: Funcionalidades Avanzadas
1. Backup coordinado
2. Auto-restart y health checks
3. Transferencias entre servidores
4. Métricas y reportes

#### Fase 4: Optimización y Extras
1. Notificaciones externas
2. API REST para integración
3. Plantillas de cluster
4. Importación/Exportación de configuraciones

### 7. Beneficios del Sistema de Cluster

#### A. Para Administradores
- **Vista Unificada**: Todo el cluster en una sola interfaz
- **Operaciones Masivas**: Controlar múltiples servidores a la vez
- **Monitoreo Centralizado**: Estado de todo el cluster
- **Backup Coordinado**: Respaldos consistentes

#### B. Para Jugadores
- **Transferencias Fluidas**: Mover personajes/items entre mapas
- **Experiencia Continua**: Progreso compartido entre servidores
- **Mayor Disponibilidad**: Si un servidor falla, otros siguen
- **Variedad de Mapas**: Acceso a múltiples mundos

#### C. Para el Sistema
- **Escalabilidad**: Fácil agregar/quitar servidores
- **Eficiencia**: Uso optimizado de recursos
- **Confiabilidad**: Redundancia y recuperación automática
- **Mantenimiento**: Operaciones coordinadas

### 8. Consideraciones Técnicas

#### A. Recursos del Sistema
- **RAM**: ~2-4GB por servidor ARK
- **CPU**: Cores dedicados recomendados
- **Almacenamiento**: SSD recomendado para mejor rendimiento
- **Red**: Ancho de banda suficiente para múltiples conexiones

#### B. Limitaciones
- **Máximo Recomendado**: 5-8 servidores por cluster
- **Puertos**: Verificar disponibilidad de rangos
- **Firewall**: Configuración más compleja
- **Mantenimiento**: Mayor complejidad operativa

### 9. Migración desde Sistema Actual

#### A. Compatibilidad
- **Configuraciones Existentes**: Importar automáticamente
- **Datos de Servidores**: Migrar sin pérdida
- **Modo Híbrido**: Permitir uso individual y cluster

#### B. Proceso de Migración
1. **Backup Completo**: Respaldar configuración actual
2. **Crear Cluster**: Configurar nuevo sistema
3. **Importar Servidores**: Migrar servidores existentes
4. **Validar**: Verificar funcionamiento
5. **Activar**: Cambiar al modo cluster

Este diseño proporciona una base sólida para implementar un sistema de cluster robusto y escalable que mejore significativamente la capacidad de gestión de múltiples servidores ARK.