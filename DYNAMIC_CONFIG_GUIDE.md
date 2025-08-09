# 🎮 Guía de Configuración Dinámica de ARK

## 📋 **Descripción General**

El nuevo sistema de configuración dinámica permite editar automáticamente los archivos de configuración de ARK Survival Ascended sin necesidad de programar campos específicos. El sistema:

- 🔍 **Detecta automáticamente** archivos de configuración de ARK
- 📝 **Parsea dinámicamente** todas las secciones y parámetros
- 🎛️ **Genera UI automáticamente** basada en tipos de datos
- 💾 **Guarda cambios** directamente en los archivos INI
- 🔄 **Crea backups** automáticos antes de guardar

## 🚀 **Características Principales**

### **✅ Detección Automática de Archivos**

```
Busca automáticamente:
- GameUserSettings.ini
- Game.ini
- Engine.ini
- ServerSettings.ini
```

### **🎯 Detección Inteligente de Tipos**

| Tipo          | Ejemplos                         | Widget UI          |
| ------------- | -------------------------------- | ------------------ |
| **Boolean**   | `True`, `False`, `1`, `0`        | Switch ON/OFF      |
| **Integer**   | `70`, `1000`, `5000`             | Entry numérico     |
| **Float**     | `1.5`, `2.0`, `0.8`              | Entry decimal      |
| **String**    | `"Mi Servidor"`, `"password123"` | Entry de texto     |
| **Long Text** | Mensajes largos                  | TextBox multilinea |

### **🔧 Reconocimiento de Patrones**

```python
# El sistema reconoce patrones comunes:
Multiplier → Float (ej: XPMultiplier=2.0)
Max/Min/Limit → Integer (ej: MaxPlayers=70)
Enable/Disable → Boolean (ej: EnablePvP=True)
Password/Name → String (ej: ServerPassword="...")
```

## 📁 **Estructura de Archivos Detectados**

### **🎮 GameUserSettings.ini**

```ini
[ServerSettings]
SessionName=Mi Servidor ARK
MaxPlayers=70
ServerPVE=True

[/script/shootergame.shootergamemode]
XPMultiplier=2.0
TamingSpeedMultiplier=3.0
```

### **⚙️ Game.ini**

```ini
[/script/engine.gamesession]
MaxPlayers=70

[/script/shootergame.shootergamemode]
bUseCorpseLocator=True
bDisablePvEGamma=False
```

## 🎛️ **Interfaz de Usuario**

### **📊 Vista Principal**

```
🎮 Configuración Dinámica de ARK
┌─────────────────────────────────────┐
│ 🔍 Buscar Configs  ✅ 2 archivos    │
│ 💾 Guardar Todo    🔄 Recargar      │
└─────────────────────────────────────┘

📄 GameUserSettings.ini
├── [ServerSettings]
│   ├── SessionName: [Mi Servidor]
│   ├── MaxPlayers: [70]
│   └── ServerPVE: [✓ ON/OFF]
└── [/script/shootergame.shootergamemode]
    ├── XPMultiplier: [2.0]
    └── TamingSpeedMultiplier: [3.0]
```

### **🎨 Widgets por Tipo**

- **🔘 Boolean**: Switch visual ON/OFF
- **🔢 Numbers**: Entry con validación numérica
- **📝 Text**: Entry simple o TextBox para textos largos
- **📂 Paths**: Entry con botón "Buscar" (futuro)

## 🔧 **Uso del Sistema**

### **1️⃣ Búsqueda Automática**

```
1. El sistema busca en la ruta raíz configurada
2. Detecta archivos *.ini en subdirectorios
3. Muestra cantidad de archivos encontrados
```

### **2️⃣ Selección Manual**

```
Si no encuentra archivos automáticamente:
1. Clic en "Seleccionar Archivos de Configuración"
2. Buscar manualmente archivos .ini
3. Seleccionar múltiples archivos
```

### **3️⃣ Edición de Parámetros**

```
1. Expandir secciones de archivos
2. Modificar valores en widgets apropiados
3. Los cambios se reflejan en tiempo real
```

### **4️⃣ Guardado Seguro**

```
1. Clic en "💾 Guardar Todo"
2. Se crean backups automáticos (.backup)
3. Se escriben los nuevos valores
4. Confirmación de éxito
```

## 🛡️ **Seguridad y Backups**

### **🔒 Protección de Datos**

- ✅ Backup automático antes de cada guardado
- ✅ Validación de tipos de datos
- ✅ Preservación del formato original
- ✅ Manejo de errores robusto

### **💾 Archivos de Backup**

```
GameUserSettings.ini → GameUserSettings.ini.backup
Game.ini → Game.ini.backup
```

## 🎯 **Ventajas del Sistema Dinámico**

### **✅ Para Desarrolladores**

- Sin necesidad de hardcodear campos
- Mantenimiento mínimo del código
- Adaptable a nuevas versiones de ARK
- Escalable a cualquier archivo INI

### **✅ Para Usuarios**

- Interfaz intuitiva y organizada
- Detección automática de configuraciones
- Edición visual de todos los parámetros
- Seguridad con backups automáticos

### **✅ Para Servidores**

- Configuración completa sin limitaciones
- Soporte para parámetros experimentales
- Compatibilidad con mods que agreguen configs
- Organización por archivos y secciones

## 🔧 **Ejemplos de Uso**

### **Scenario 1: Servidor PvE Casual**

```ini
[ServerSettings]
ServerPVE=True
DifficultyOffset=0.5
MaxPlayers=20

[/script/shootergame.shootergamemode]
XPMultiplier=3.0
TamingSpeedMultiplier=5.0
HarvestAmountMultiplier=2.0
```

### **Scenario 2: Servidor PvP Competitivo**

```ini
[ServerSettings]
ServerPVE=False
DifficultyOffset=1.0
MaxPlayers=100

[/script/shootergame.shootergamemode]
XPMultiplier=1.0
TamingSpeedMultiplier=1.0
PlayerDamageMultiplier=1.5
```

### **Scenario 3: Servidor Experimental**

```ini
[ServerSettings]
AllowFlyerCarryPVE=True
AllowCaveBuildingPvE=True
MaxTamedDinos=10000

[/script/shootergame.shootergamemode]
BabyMatureSpeedMultiplier=20.0
MatingIntervalMultiplier=0.1
```

## 🚀 **Futuras Mejoras**

### **🔮 Características Planificadas**

- [ ] **Templates de configuración** (PvE, PvP, Roleplay)
- [ ] **Validación avanzada** de valores
- [ ] **Búsqueda y filtrado** de parámetros
- [ ] **Documentación inline** de parámetros
- [ ] **Comparación** entre configuraciones
- [ ] **Import/Export** de configuraciones
- [ ] **Presets** para diferentes tipos de servidor

### **🎛️ Mejoras de UI**

- [ ] **Categorización** por funcionalidad
- [ ] **Favoritos** para parámetros comunes
- [ ] **Historial** de cambios
- [ ] **Preview** antes de guardar
- [ ] **Tooltips** informativos
- [ ] **Drag & Drop** para archivos

## 📞 **Soporte**

### **🐛 Reporte de Problemas**

Si encuentras algún problema:

1. Revisa los logs de la aplicación
2. Verifica que la ruta raíz esté configurada
3. Confirma que los archivos INI no estén bloqueados
4. Revisa los archivos .backup si algo sale mal

### **📝 Archivos de Log**

```
logs/app.log - Logs generales de la aplicación
```

---

**¡El sistema de configuración dinámica hace que gestionar tu servidor ARK sea más fácil que nunca!** 🎮✨
