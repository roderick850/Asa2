# 🛠️ Solución para Error de Compilación - "No module named 'requests'"

## 📋 Problema

Al compilar con `pyinstaller main.spec` aparece el error:

```
Failed to execute script 'main' due to unhandled exception: No module named 'requests'
```

## ✅ Solución (Método Recomendado)

### **Opción 1: Usar el Script Automático (Recomendado)**

1. **Ejecuta el script de solución automática:**
   ```batch
   python fix_requests_issue.py
   ```
2. **Si no hay errores, compila con el script mejorado:**
   ```batch
   build_exe_fixed.bat
   ```

### **Opción 2: Solución Manual**

1. **Instala/reinstala todas las dependencias:**

   ```batch
   pip install --force-reinstall -r requirements.txt
   ```

2. **Instala específicamente las dependencias problemáticas:**

   ```batch
   pip install --force-reinstall requests urllib3 certifi charset-normalizer idna
   ```

3. **Verifica que requests funcione:**

   ```batch
   python -c "import requests; print('✅ requests OK')"
   ```

4. **Compila con el script mejorado:**
   ```batch
   build_exe_fixed.bat
   ```

### **Opción 3: Compilación Direct con PyInstaller**

Si prefieres usar PyInstaller directamente:

```batch
pyinstaller main.spec --clean --noconfirm --log-level=INFO
```

## 🔧 Cambios Realizados

### **Archivo `main.spec` mejorado:**

- ✅ Agregados todos los submódulos de `requests`
- ✅ Incluidos certificados SSL (`certifi`)
- ✅ Agregados módulos de `urllib3`
- ✅ Mejoradas las dependencias de CustomTkinter

### **Script `build_exe_fixed.bat`:**

- ✅ Verificación automática de dependencias
- ✅ Instalación automática de módulos faltantes
- ✅ Logs detallados para debugging
- ✅ Verificación del ejecutable final

### **Script `fix_requests_issue.py`:**

- ✅ Diagnóstico automático de problemas
- ✅ Instalación automática de módulos faltantes
- ✅ Verificación de imports

## 🚨 Solución de Problemas

### **Si sigue dando error de requests:**

1. **Reinstala requests desde cero:**

   ```batch
   pip uninstall requests urllib3 certifi
   pip install requests urllib3 certifi
   ```

2. **Verifica la instalación:**

   ```batch
   python -c "import requests; import requests.adapters; import urllib3; import certifi; print('Todo OK')"
   ```

3. **Usa el modo debug de PyInstaller:**
   ```batch
   pyinstaller main.spec --clean --noconfirm --debug=all
   ```

### **Si el ejecutable no inicia:**

1. **Ejecuta desde consola para ver errores:**

   ```batch
   cd dist
   ArkServerManager.exe
   ```

2. **Verifica que todos los archivos estén incluidos:**
   - `dist/ArkServerManager.exe`
   - Carpetas: `data/`, `examples/`, `rcon/`, `ico/`

## 📁 Archivos Importantes

- `build_exe_fixed.bat` - Script de compilación mejorado
- `fix_requests_issue.py` - Diagnóstico y solución automática
- `main.spec` - Configuración mejorada de PyInstaller
- `requirements.txt` - Lista de dependencias

## 🎯 Recomendación Final

**Usa siempre `build_exe_fixed.bat`** en lugar de compilar directamente con PyInstaller. Este script:

1. 🔍 Verifica todas las dependencias
2. 📦 Instala automáticamente lo que falta
3. 🧹 Limpia builds anteriores
4. 🔨 Compila con configuración optimizada
5. ✅ Verifica el resultado final

¡El ejecutable debería funcionar perfectamente ahora! 🚀
