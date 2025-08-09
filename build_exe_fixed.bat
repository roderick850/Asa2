@echo off
setlocal enabledelayedexpansion

echo ========================================
echo  ARK SERVER MANAGER - BUILD SCRIPT V2
echo ========================================
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no está instalado o no está en el PATH.
    echo Por favor, instala Python primero.
    pause
    exit /b 1
)

echo [INFO] ✅ Python encontrado.
echo.

:: Instalar/actualizar dependencias
echo [INFO] 📦 Instalando/actualizando dependencias...
echo.

pip install --upgrade pip
if errorlevel 1 (
    echo [WARNING] No se pudo actualizar pip, continuando...
)

:: Instalar desde requirements.txt
if exist "requirements.txt" (
    echo [INFO] Instalando desde requirements.txt...
    pip install -r requirements.txt --upgrade
    if errorlevel 1 (
        echo [ERROR] Error al instalar dependencias desde requirements.txt
        pause
        exit /b 1
    )
) else (
    echo [INFO] requirements.txt no encontrado, instalando dependencias manualmente...
    pip install customtkinter>=5.2.0 Pillow>=10.0.0 psutil>=5.9.0 requests>=2.31.0 schedule>=1.2.0 pystray>=0.19.0 win10toast>=0.9 PyInstaller>=6.0.0
)

echo.
echo [INFO] 🧪 Verificando dependencias críticas...

:: Verificar cada dependencia crítica
set "deps=customtkinter PIL psutil requests schedule pystray win10toast PyInstaller"
for %%d in (%deps%) do (
    python -c "import %%d; print('[✅] %%d OK')" 2>nul || (
        echo [❌] Error con %%d
        echo [INFO] Intentando reinstalar %%d...
        pip install --force-reinstall %%d
        python -c "import %%d; print('[✅] %%d OK después de reinstalar')" || (
            echo [ERROR] No se pudo instalar %%d correctamente
            pause
            exit /b 1
        )
    )
)

echo.
echo [INFO] ✅ Todas las dependencias verificadas.
echo.

:: Limpiar build anterior
if exist "build" (
    echo [INFO] 🧹 Limpiando directorio build anterior...
    rmdir /s /q "build" 2>nul
)

if exist "dist" (
    echo [INFO] 🧹 Limpiando directorio dist anterior...
    rmdir /s /q "dist" 2>nul
)

:: Verificar archivos necesarios
if not exist "main.py" (
    echo [ERROR] main.py no encontrado
    pause
    exit /b 1
)

if not exist "main.spec" (
    echo [ERROR] main.spec no encontrado
    pause
    exit /b 1
)

if not exist "ico\ArkManager.ico" (
    echo [WARNING] Icono no encontrado en ico\ArkManager.ico
)

echo [INFO] 🔨 Iniciando compilación con PyInstaller...
echo.

:: Compilar con verbose para debugging
pyinstaller main.spec --clean --noconfirm --log-level=INFO

if errorlevel 1 (
    echo.
    echo [ERROR] ❌ Error durante la compilación.
    echo.
    echo [INFO] Intentando compilación con modo debug...
    pyinstaller main.spec --clean --noconfirm --log-level=DEBUG --debug=all
    
    if errorlevel 1 (
        echo.
        echo [ERROR] ❌ Error crítico durante la compilación.
        echo Revisa los mensajes de error anteriores.
        echo.
        echo [TIP] Asegúrate de que:
        echo   - Todas las dependencias estén instaladas
        echo   - No hay archivos bloqueados
        echo   - Tienes permisos de escritura
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo         BUILD COMPLETADO ✅
echo ========================================
echo.

:: Verificar si el ejecutable fue creado
if exist "dist\ArkServerManager.exe" (
    echo [SUCCESS] ✅ Ejecutable creado exitosamente!
    echo [INFO] 📍 Ubicación: dist\ArkServerManager.exe
    echo [INFO] 🎨 Icono: ico\ArkManager.ico
    echo.
    
    :: Mostrar tamaño del archivo
    for %%I in ("dist\ArkServerManager.exe") do (
        set /a "size_mb=%%~zI/1024/1024"
        echo [INFO] 📏 Tamaño: %%~zI bytes (~!size_mb! MB)
    )
    
    echo.
    echo [INFO] 🧪 Verificando que el ejecutable funcione...
    
    :: Test básico del ejecutable
    timeout /t 2 >nul
    "dist\ArkServerManager.exe" --version 2>nul && (
        echo [SUCCESS] ✅ Ejecutable verificado correctamente!
    ) || (
        echo [WARNING] ⚠️ No se pudo verificar automáticamente
    )
    
    echo.
    set /p run="🚀 ¿Quieres ejecutar la aplicación ahora? (s/n): "
    if /i "!run!"=="s" (
        echo [INFO] 🚀 Ejecutando ArkServerManager...
        start "" "dist\ArkServerManager.exe"
    )
    
    echo.
    echo [INFO] 📋 Archivos en dist:
    dir /b "dist\"
    
) else (
    echo [ERROR] ❌ No se pudo crear el ejecutable.
    echo.
    echo [DEBUG] Contenido del directorio dist:
    if exist "dist" (
        dir "dist"
    ) else (
        echo Directorio dist no existe
    )
    echo.
    echo [DEBUG] Verifica los logs de PyInstaller arriba para más detalles.
)

echo.
echo Presiona cualquier tecla para salir...
pause > nul
