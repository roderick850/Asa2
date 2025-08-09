@echo off
echo ========================================
echo    BUILD DEBUG - Ark Server Manager
echo ========================================
echo.

:: Activar entorno virtual
echo [INFO] Activando entorno virtual...
call .venv\Scripts\activate.bat

:: Limpiar builds anteriores
echo [INFO] Limpiando builds anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" echo [INFO] Usando main.spec existente

echo.
echo [INFO] Compilando con modo DEBUG habilitado...
echo [INFO] Esto mostrará mensajes de error detallados si algo falla.
echo.

:: Compilar con PyInstaller en modo debug
pyinstaller ^
    --name "ArkServerManager" ^
    --onefile ^
    --windowed ^
    --icon "ico/ArkManager.ico" ^
    --add-data "config.ini;." ^
    --add-data "data;data" ^
    --add-data "rcon;rcon" ^
    --add-data "ico;ico" ^
    --hidden-import "requests" ^
    --hidden-import "urllib3" ^
    --hidden-import "certifi" ^
    --hidden-import "charset_normalizer" ^
    --hidden-import "idna" ^
    --hidden-import "customtkinter" ^
    --hidden-import "PIL" ^
    --hidden-import "psutil" ^
    --hidden-import "schedule" ^
    --collect-all "requests" ^
    --collect-all "urllib3" ^
    --collect-all "certifi" ^
    --debug all ^
    --log-level DEBUG ^
    main.py

echo.
echo ========================================
echo           BUILD COMPLETADO
echo ========================================
echo.

if exist "dist\ArkServerManager.exe" (
    echo [SUCCESS] ✅ Ejecutable DEBUG creado!
    echo [INFO] Ubicación: dist\ArkServerManager.exe
    echo [INFO] Icono: ico\ArkManager.ico
    echo.
    echo [WARNING] Este ejecutable incluye información de debug.
    echo [WARNING] Para producción, usa build_exe.bat
    echo.
    
    for %%I in ("dist\ArkServerManager.exe") do (
        set size=%%~zI
        echo [INFO] Tamaño: !size! bytes
    )
    echo.
    
    set /p run="¿Quieres ejecutar la aplicación DEBUG ahora? (s/n): "
    if /i "!run!"=="s" (
        echo [INFO] Ejecutando aplicación...
        start "" "dist\ArkServerManager.exe"
    )
) else (
    echo [ERROR] ❌ No se pudo crear el ejecutable
    echo [INFO] Revisa los errores arriba para más detalles
)

echo.
echo Presiona cualquier tecla para salir...
pause >nul
