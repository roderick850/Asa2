@echo off
echo ============================================
echo   🛡️ BUILD CLEAN ARK SERVER MANAGER
echo ============================================
echo.
echo [INFO] Este script crea un ejecutable más limpio
echo [INFO] que reduce las alertas de antivirus
echo.

echo [INFO] Activando entorno virtual...
call .venv\Scripts\activate.bat

echo [INFO] Limpiando archivos anteriores...
if exist "dist\ArkServerManager.exe" (
    taskkill /f /im ArkServerManager.exe 2>nul
    del /f "dist\ArkServerManager.exe" 2>nul
)
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo [INFO] Creando directorios limpios...
mkdir build 2>nul
mkdir dist 2>nul

echo [INFO] Compilando con configuración antivirus-friendly...
.venv\Scripts\python.exe -m PyInstaller main.spec --clean --noconfirm

if exist "dist\ArkServerManager.exe" (
    echo.
    echo [SUCCESS] ✅ Ejecutable creado exitosamente!
    echo.
    echo [INFO] 🛡️ Configuración antivirus-friendly aplicada:
    echo [INFO] - UPX desactivado
    echo [INFO] - Módulos problemáticos excluidos
    echo [INFO] - Optimización básica
    echo.
    for %%I in ("dist\ArkServerManager.exe") do (
        set size=%%~zI
        set /a sizeMB=!size!/1024/1024
        echo [INFO] Tamaño: !sizeMB! MB
    )
    echo.
    echo [ANTIVIRUS] ⚠️ Si aún aparece alerta:
    echo [ANTIVIRUS] 1. Agregar excepción para: %cd%\dist\ArkServerManager.exe
    echo [ANTIVIRUS] 2. Agregar excepción para carpeta: %cd%\dist\
    echo [ANTIVIRUS] 3. Escanear archivo en VirusTotal.com para confirmar
    echo.
    set /p run="¿Quieres ejecutar la aplicación ahora? (s/n): "
    if /i "!run!"=="s" (
        echo [INFO] Ejecutando aplicación...
        start "" "dist\ArkServerManager.exe"
    )
) else (
    echo [ERROR] ❌ Error al crear el ejecutable
    echo [INFO] Revisa los logs arriba para más detalles
    pause
)

echo.
echo [INFO] Proceso completado.
pause
