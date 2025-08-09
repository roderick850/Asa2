# 🚀 Instrucciones para Compilar Ark Server Manager

Este documento explica cómo generar un ejecutable de la aplicación Ark Server Manager.

## 📋 Requisitos Previos

### 1. Instalar PyInstaller

```bash
pip install pyinstaller
```

### 2. Verificar Dependencias

Asegúrate de que todas las dependencias estén instaladas:

```bash
pip install -r requirements.txt
```

## 🔧 Métodos de Compilación

### Método 1: Script Automático (Recomendado)

#### En Windows:

```cmd
build_exe.bat
```

#### En Linux/macOS:

```bash
chmod +x build_exe.sh
./build_exe.sh
```

### Método 2: Comando Manual

#### Compilación Básica:

```bash
pyinstaller main.spec --clean --noconfirm
```

#### Compilación con Opciones Adicionales:

```bash
pyinstaller main.spec --clean --noconfirm --onefile --windowed
```

## 📁 Estructura del Resultado

Después de la compilación, encontrarás:

```
dist/
├── ArkServerManager.exe        # El ejecutable principal (Windows)
├── ArkServerManager           # El ejecutable principal (Linux/macOS)
└── [archivos de dependencias] # Archivos necesarios para la ejecución
```

## ⚙️ Personalización del main.spec

El archivo `main.spec` contiene la configuración de compilación. Puedes modificar:

### Cambiar el Nombre del Ejecutable:

```python
name='TuNombreApp'
```

### Icono Personalizado:

✅ **Ya configurado**: `icon='ico/ArkManager.ico'`

### Cambiar Icono (opcional):

```python
icon='ruta/a/tu/nuevo_icono.ico'  # Windows
icon='ruta/a/tu/nuevo_icono.icns' # macOS
```

### Habilitar Consola para Debug:

```python
console=True  # Cambiar a True para ver mensajes de debug
```

### Optimización de Tamaño:

```python
optimize=2,  # Nivel máximo de optimización
upx=True,    # Compresión UPX (si está instalado)
```

## 🐛 Solución de Problemas Comunes

### Error: "Module not found"

- Agregar el módulo faltante a `hiddenimports` en `main.spec`:

```python
hiddenimports = [
    'tu_modulo_faltante',
    # ... otros módulos
]
```

### Ejecutable muy Grande

- Verificar y agregar módulos innecesarios a `excludes`:

```python
excludes = [
    'modulo_innecesario',
    # ... otros módulos
]
```

### Error de Importación de CustomTkinter

- Asegúrate de que CustomTkinter esté en `hiddenimports`:

```python
hiddenimports = [
    'customtkinter',
    'PIL',
    'PIL._tkinter_finder',
    'tkinter',
    'tkinter.ttk',
]
```

### Problema con Archivos de Datos

- Verificar que todos los archivos necesarios estén en `datas`:

```python
datas = [
    ('config.ini', '.'),
    ('data', 'data'),
    ('rcon', 'rcon'),
]
```

## 📊 Optimizaciones Avanzadas

### Reducir Tamaño del Ejecutable:

1. **Usar --onefile**: Crea un solo archivo ejecutable
2. **Instalar UPX**: Para compresión adicional

   ```bash
   # Windows (con Chocolatey)
   choco install upx

   # Linux (Ubuntu/Debian)
   sudo apt-get install upx-ucl

   # macOS (con Homebrew)
   brew install upx
   ```

### Compilación Multi-Plataforma:

- Compila en cada plataforma objetivo
- Windows: `.exe`
- Linux: Sin extensión
- macOS: `.app` o sin extensión

## 🔐 Firma Digital (Opcional)

### Windows:

```bash
signtool sign /f tu_certificado.pfx /p contraseña dist/ArkServerManager.exe
```

### macOS:

```bash
codesign --force --verify --verbose --sign "Developer ID" dist/ArkServerManager
```

## 📝 Notas Importantes

1. **Tamaño del Ejecutable**: El primer build puede ser grande (~100-200MB) debido a las dependencias de CustomTkinter y PIL.

2. **Tiempo de Compilación**: El proceso puede tomar varios minutos dependiendo de tu sistema.

3. **Antivirus**: Algunos antivirus pueden marcar falsas alarmas con ejecutables de PyInstaller. Es normal.

4. **Pruebas**: Siempre prueba el ejecutable en diferentes máquinas antes de distribuir.

5. **Distribución**: El ejecutable incluye todo lo necesario y no requiere Python instalado en la máquina objetivo.

## 🚀 Comandos Rápidos

```bash
# Compilación rápida para desarrollo
pyinstaller --onefile --windowed main.py

# Compilación con spec personalizado (recomendado)
pyinstaller main.spec --clean

# Compilación optimizada para distribución
pyinstaller main.spec --clean --noconfirm --optimize=2
```

## 💡 Tips Adicionales

- Usa `--clean` para limpiar builds anteriores
- Usa `--noconfirm` para sobrescribir sin preguntar
- Prueba primero con `console=True` para debug
- Mantén el archivo `main.spec` bajo control de versiones
- Considera crear diferentes specs para desarrollo y producción

¡Tu aplicación Ark Server Manager estará lista para distribuir! 🎉
