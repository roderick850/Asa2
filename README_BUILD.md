# 🔧 Guía de Compilación - Ark Server Manager

## 🚀 Compilación Rápida (Método Automático)

### Para usuarios que quieren un ejecutable inmediatamente:

```cmd
install_and_build.bat
```

Este script:

1. ✅ Instala PyInstaller automáticamente
2. ✅ Verifica dependencias
3. ✅ Compila la aplicación
4. ✅ Te muestra el resultado

## 📋 Requisitos

- **Python 3.8+** instalado
- **pip** funcionando correctamente
- **Conexión a internet** (para descargar PyInstaller)

## 🎯 Métodos Disponibles

### 1. **Script Todo-en-Uno** (Recomendado para principiantes)

```cmd
install_and_build.bat
```

### 2. **Script de Compilación** (Si ya tienes PyInstaller)

```cmd
build_exe.bat
```

### 3. **Manual** (Para usuarios avanzados)

```cmd
pip install pyinstaller
pyinstaller main.spec --clean --noconfirm
```

## 📁 Resultado

Después de la compilación exitosa:

```
dist/
└── ArkServerManager.exe    # 🎉 Tu aplicación ejecutable
```

**Tamaño esperado**: ~150-250 MB (incluye todas las dependencias)

## ⚡ Ejecutar la Aplicación

### Desde el ejecutable:

```cmd
dist\ArkServerManager.exe
```

### Desde código fuente:

```cmd
python main.py
```

## 🐛 Solución de Problemas

### ❌ Error: "PyInstaller no está instalado"

```cmd
pip install pyinstaller
```

### ❌ Error: "Module not found" durante compilación

- Edita `main.spec` y agrega el módulo faltante a `hiddenimports`

### ❌ Ejecutable muy lento al iniciar

- Es normal la primera vez (puede tardar 10-30 segundos)
- Las siguientes ejecuciones serán más rápidas

### ❌ Antivirus bloquea el ejecutable

- Es una falsa alarma común con PyInstaller
- Agrega una excepción en tu antivirus

### ❌ Error: "No module named 'customtkinter'"

- Verifica que todas las dependencias estén instaladas:

```cmd
pip install -r requirements.txt
```

## 🔧 Personalización

### Cambiar nombre del ejecutable:

Edita `main.spec`, línea:

```python
name='TuNombreApp'
```

### Agregar icono:

1. Consigue un archivo `.ico`
2. Edita `main.spec`:

```python
icon='ruta/a/tu/icono.ico'
```

### Habilitar consola para debug:

Edita `main.spec`:

```python
console=True
```

## 📊 Información del Build

### Archivos incluidos automáticamente:

- ✅ `config.ini`
- ✅ Carpeta `data/` (configuraciones JSON)
- ✅ Carpeta `rcon/` (herramientas RCON)
- ✅ Documentación (`.md`)
- ✅ Todas las dependencias Python

### Archivos excluidos para reducir tamaño:

- ❌ Módulos de testing
- ❌ Jupyter/IPython
- ❌ Matplotlib, NumPy, SciPy
- ❌ Documentación de desarrollo

## 🎉 ¡Listo!

Una vez compilado, puedes:

1. **Distribuir** el archivo `ArkServerManager.exe`
2. **Ejecutar** en cualquier Windows sin Python instalado
3. **Copiar** a cualquier ubicación que desees

## 💡 Tips Adicionales

- **Primera ejecución**: Puede tardar en cargar (normal)
- **Tamaño**: El ejecutable es grande pero incluye todo lo necesario
- **Portabilidad**: Funciona sin instalar nada adicional
- **Updates**: Para nuevas versiones, recompila con estos mismos pasos

---

**¿Problemas?** Revisa `BUILD_INSTRUCTIONS.md` para soluciones detalladas.

**¿Todo funcionó?** ¡Perfecto! Tu Ark Server Manager está listo para usar. 🎮
