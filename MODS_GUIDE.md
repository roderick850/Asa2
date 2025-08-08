# 🎮 Guía del Gestor de Mods - ARK Survival Ascended

## 📋 Descripción General

El panel de Mods integra completamente con CurseForge para permitir:

- 🔍 **Búsqueda de mods** directamente desde CurseForge
- ⭐ **Sistema de favoritos** para mods preferidos
- 📦 **Gestión de mods instalados** con IDs automáticos
- 🚀 **Integración con el servidor** para aplicar mods automáticamente

## 🎯 Características Principales

### 🔍 **Búsqueda de Mods**

- Busca mods por nombre o categoría
- Muestra mods populares con un clic
- Información detallada: descargas, fecha, descripción
- Enlace directo a CurseForge

### ⭐ **Sistema de Favoritos**

- Marca mods como favoritos para acceso rápido
- Gestión completa de favoritos
- Persistencia entre sesiones

### 📦 **Gestión de Instalados**

- Lista de mods "instalados" (seleccionados para el servidor)
- IDs automáticos para configuración del servidor
- Desinstalación con un clic

### 🚀 **Integración con Servidor**

- Los mods se agregan automáticamente al comando del servidor
- Formato: `-mods=956565,854554`
- Si no hay mods, el comando termina en `-log`

## 🚀 Cómo Usar

### 1. **Buscar Mods**

```
1. Ve a la pestaña "Mods"
2. Escribe el nombre del mod en la búsqueda
3. Presiona Enter o haz clic en "Buscar"
4. También puedes hacer clic en "Populares" para ver los más descargados
```

### 2. **Instalar Mods**

```
1. En los resultados de búsqueda, haz clic en "📦 Instalar"
2. El mod se agregará a tu lista de instalados
3. El ID se agregará automáticamente al campo de IDs
4. Haz clic en "Aplicar al Servidor" para guardar
```

### 3. **Manejar Favoritos**

```
1. En cualquier mod, haz clic en "☆ Favorito"
2. El mod aparecerá en la pestaña "⭐ Favoritos"
3. Desde favoritos puedes instalar o remover
```

### 4. **Aplicar al Servidor**

```
1. Los IDs de mods aparecen en la parte inferior
2. Haz clic en "Aplicar al Servidor" para guardar
3. Al iniciar el servidor, los mods se cargarán automáticamente
```

## 🔧 Configuración Técnica

### API de CurseForge

- **API Key**: Integrada y configurada
- **Game ID**: 83374 (ARK: Survival Ascended)
- **Endpoint**: `https://api.curseforge.com/v1`

### Almacenamiento Local

- **Favoritos**: `data/favorite_mods.json`
- **Instalados**: `data/installed_mods.json`
- **Configuración**: `config.ini` (mod_ids)

### Formato de Comando del Servidor

```bash
# Sin mods:
ArkAscendedServer.exe TheIsland_WP?listen?Port=7777 -server -log

# Con mods:
ArkAscendedServer.exe TheIsland_WP?listen?Port=7777 -server -log -mods=956565,854554
```

## 📱 Interfaz del Usuario

### Pestañas Principales

- **🔍 Resultados**: Mods encontrados en búsqueda
- **⭐ Favoritos**: Mods marcados como favoritos
- **📦 Instalados**: Mods seleccionados para el servidor

### Botones de Acción

- **📦 Instalar**: Agregar mod a la lista del servidor
- **⭐ Favorito**: Marcar/desmarcar como favorito
- **🌐 Ver en CF**: Abrir en CurseForge
- **🗑️ Desinstalar**: Remover del servidor
- **🗑️ Remover**: Quitar de favoritos

## 🎮 Ejemplos de Uso

### Buscar "Structures Plus"

```
1. Escribe "structures plus" en búsqueda
2. Aparecerá S+ en los resultados
3. Haz clic en "📦 Instalar"
4. El ID 731604991 se agregará automáticamente
5. Aplica al servidor
```

### Mods Populares

```
1. Haz clic en "Populares"
2. Ve los mods más descargados
3. Instala los que te interesen
4. Marca favoritos para futuro uso
```

## 🛠️ Solución de Problemas

### No aparecen mods

- Verifica conexión a internet
- La API de CurseForge puede tener límites
- Intenta buscar términos más específicos

### Error al aplicar mods

- Verifica que los IDs sean válidos
- Los mods deben ser compatibles con ARK: Survival Ascended
- Algunos mods pueden requerir dependencias

### Mods no cargan en el servidor

- Verifica que el formato sea correcto: `956565,854554`
- Sin espacios entre comas
- IDs deben ser números válidos de CurseForge

## 🔄 Flujo Completo

```
1. 🔍 Buscar mods en CurseForge
2. ⭐ Marcar favoritos (opcional)
3. 📦 Instalar mods deseados
4. 🚀 Aplicar al servidor
5. ⚙️ Iniciar servidor con mods
6. 🎮 ¡Jugar con mods!
```

## 📊 Información de Mods

Cada mod muestra:

- **Nombre** y **descripción**
- **Número de descargas**
- **ID único** de CurseForge
- **Fecha de última actualización**
- **Enlaces** a la página original

¡Disfruta explorando y agregando mods a tu servidor ARK! 🎮🚀
