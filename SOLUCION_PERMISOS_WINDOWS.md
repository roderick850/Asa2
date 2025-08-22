# 🔧 Solución de Problemas de Permisos en Windows

## 📋 Problema SOLUCIONADO ✅

**¡IMPORTANTE!** A partir de la versión actual, la aplicación incluye un **sistema automático de manejo de permisos** que previene el error **"[WinError 5] Acceso denegado: 'data'"**.

### ✅ Lo que hace automáticamente:

- **Detecta problemas de permisos** al intentar crear directorios
- **Usa directorios temporales** como alternativa cuando fallan los permisos
- **Permite que la aplicación abra SIEMPRE**, sin importar la ubicación o permisos
- **Muestra mensajes informativos** cuando usa directorios alternativos

### ⚠️ Cuando verás directorios temporales:

Si la aplicación no puede crear directorios en su ubicación, verás mensajes como:

```
⚠️ Usando directorio temporal: C:\Users\...\Temp\ArkSM_data_...
```

**Esto es normal y la aplicación funcionará correctamente.** Para una experiencia óptima, considera las soluciones a continuación.

## 🚀 Soluciones Rápidas

### ✅ Solución 1: Ejecutar como Administrador

1. **Cierra la aplicación** completamente
2. **Haz clic derecho** en `ArkServerManager.exe`
3. Selecciona **"Ejecutar como administrador"**
4. Acepta el diálogo de UAC cuando aparezca

### ✅ Solución 2: Cambiar Ubicación

Mueve la aplicación a una carpeta con mejores permisos:

**Ubicaciones recomendadas:**

```
C:\ArkServerManager\
C:\Users\[TuUsuario]\Documents\ArkServerManager\
C:\Users\[TuUsuario]\Desktop\ArkServerManager\
```

**Evitar estas ubicaciones:**

```
C:\Program Files\
C:\Program Files (x86)\
C:\Windows\
Carpetas de OneDrive sincronizadas
```

### ✅ Solución 3: Configurar Permisos Manualmente

1. **Haz clic derecho** en la carpeta de la aplicación
2. Selecciona **"Propiedades"**
3. Ve a la pestaña **"Seguridad"**
4. Haz clic en **"Editar"**
5. Selecciona tu usuario
6. Marca **"Control total"**
7. Haz clic en **"Aplicar"** y **"Aceptar"**

### ✅ Solución 4: Configurar Antivirus

Muchos antivirus bloquean la creación de carpetas:

**Windows Defender:**

1. Ve a **Configuración → Actualización y seguridad → Seguridad de Windows**
2. Haz clic en **"Protección contra virus y amenazas"**
3. En **"Configuración de protección contra virus y amenazas"**, haz clic en **"Administrar configuración"**
4. Desplázate hasta **"Exclusiones"** y haz clic en **"Agregar o quitar exclusiones"**
5. Haz clic en **"Agregar una exclusión"** → **"Carpeta"**
6. Selecciona la carpeta donde está la aplicación

**Otros Antivirus:**

- Agrega la carpeta de la aplicación a las **excepciones** o **lista blanca**
- Consulta la documentación específica de tu antivirus

## 🔍 Diagnóstico Avanzado

### Verificar Permisos desde CMD

Abre **Símbolo del sistema** y ejecuta:

```cmd
icacls "C:\ruta\a\tu\aplicacion"
```

Deberías ver algo como:

```
C:\ruta\a\tu\aplicacion NOMBREUSUARIO:(OI)(CI)(F)
```

### Aplicar Permisos desde CMD

Si necesitas aplicar permisos manualmente:

```cmd
icacls "C:\ruta\a\tu\aplicacion" /grant "%USERNAME%":F /T
```

## 🆘 Si Nada Funciona

### Modo de Recuperación

La aplicación intentará usar directorios temporales automáticamente:

- Los datos se guardarán en `%TEMP%\ArkServerManager_data\`
- La aplicación funcionará, pero los datos se perderán al limpiar archivos temporales

### Contactar Soporte

Si el problema persiste:

1. Copia el mensaje de error completo
2. Indica tu versión de Windows
3. Menciona si tienes antivirus activo
4. Describe qué soluciones has intentado

## ⚡ Prevención

Para evitar problemas futuros:

- **No instalar** en carpetas del sistema
- **Usar ubicaciones** con permisos de usuario
- **Mantener excepciones** de antivirus actualizadas
- **Ejecutar como administrador** solo cuando sea necesario

---

## 📝 Notas Técnicas

### Por qué ocurre este problema

- Windows tiene protecciones de seguridad estrictas
- Algunos antivirus son demasiado agresivos
- Ubicaciones del sistema requieren permisos elevados
- Sincronización de OneDrive puede causar conflictos

### Carpetas que necesita la aplicación

```
ArkServerManager/
├── data/          # Configuraciones y datos
├── logs/          # Archivos de registro
├── config/        # Configuración de la app
├── backups/       # Copias de seguridad
└── exports/       # Datos exportados
```

### Información de permisos

La aplicación necesita:

- **Lectura**: Para cargar configuraciones
- **Escritura**: Para guardar datos
- **Creación**: Para generar carpetas
- **Modificación**: Para actualizar archivos
