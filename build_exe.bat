@echo off
echo ========================================
echo  ARK SERVER MANAGER - BUILD SCRIPT
echo ========================================
echo.

:: Verificar si PyInstaller está instalado
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [ERROR] PyInstaller no está instalado.
    echo Instalando PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar PyInstaller.
        echo Por favor, ejecuta: pip install pyinstaller
        pause
        exit /b 1
    )
)

echo [INFO] PyInstaller encontrado.
echo.

:: Limpiar build anterior
if exist "build" (
    echo [INFO] Limpiando directorio build anterior...
    rmdir /s /q "build"
)

if exist "dist" (
    echo [INFO] Limpiando directorio dist anterior...
    rmdir /s /q "dist"
)

echo [INFO] Iniciando compilación...
echo.

:: Compilar con el archivo spec
pyinstaller main.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] Error durante la compilación.
    echo Revisa los mensajes de error anteriores.
    pause
    exit /b 1
)

echo.
echo ========================================
echo            BUILD COMPLETADO
echo ========================================
echo.
echo El ejecutable se encuentra en: dist\ArkServerManager.exe
echo.

:: Verificar si el ejecutable fue creado
if exist "dist\ArkServerManager.exe" (
    echo [SUCCESS] ✅ Ejecutable creado exitosamente con icono personalizado!
    echo [INFO] Icono: ico\ArkManager.ico
    echo.
    echo Tamaño del archivo:
    for %%I in ("dist\ArkServerManager.exe") do echo %%~zI bytes (%%~zI bytes)
    echo.
    set /p run="¿Quieres ejecutar la aplicación ahora? (s/n): "
    if /i "!run!"=="s" (
        echo [INFO] Ejecutando ArkServerManager...
        start "" "dist\ArkServerManager.exe"
    )
) else (
    echo [ERROR] ❌ No se pudo crear el ejecutable.
)

echo.
echo Presiona cualquier tecla para salir...
pause > nul
