@echo off
echo ========================================
echo   ARK SERVER MANAGER - SETUP Y BUILD
echo ========================================
echo.

echo [INFO] Verificando entorno virtual...
if not exist ".venv" (
    echo [WARNING] No se encontró entorno virtual.
    echo [INFO] Continuando con el entorno actual...
)

echo.
echo [INFO] Instalando PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo [ERROR] No se pudo instalar PyInstaller.
    echo [ERROR] Verifica tu instalación de Python y pip.
    pause
    exit /b 1
)

echo.
echo [INFO] Verificando otras dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo [WARNING] Algunos paquetes pueden no haberse instalado correctamente.
    echo [INFO] Continuando con la compilación...
)

echo.
echo ========================================
echo        INICIANDO COMPILACIÓN
echo ========================================
echo.

:: Limpiar builds anteriores
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo [INFO] Compilando aplicación...
pyinstaller main.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] Error durante la compilación.
    echo [INFO] Revisa el archivo main.spec y las dependencias.
    pause
    exit /b 1
)

echo.
echo ========================================
echo           BUILD COMPLETADO
echo ========================================
echo.

if exist "dist\ArkServerManager.exe" (
    echo [SUCCESS] ✅ Ejecutable creado exitosamente con icono personalizado!
    echo [INFO] Ubicación: dist\ArkServerManager.exe
    echo [INFO] Icono: ico\ArkManager.ico
    echo.
    
    for %%I in ("dist\ArkServerManager.exe") do (
        set size=%%~zI
        call :FormatSize !size! formatted_size
        echo [INFO] Tamaño: !formatted_size!
    )
    
    echo.
    echo [INFO] Para ejecutar la aplicación, usa:
    echo [INFO] dist\ArkServerManager.exe
    echo.
    
    set /p open="¿Quieres abrir la carpeta dist? (s/n): "
    if /i "!open!"=="s" (
        explorer dist
    )
    
    set /p run="¿Quieres ejecutar la aplicación ahora? (s/n): "
    if /i "!run!"=="s" (
        start "" "dist\ArkServerManager.exe"
    )
) else (
    echo [ERROR] ❌ No se pudo crear el ejecutable.
    echo [INFO] Revisa los errores anteriores.
)

echo.
pause
exit /b 0

:FormatSize
setlocal enabledelayedexpansion
set size=%1
if %size% lss 1024 (
    set "%~2=%size% bytes"
    goto :eof
)
set /a size=%size%/1024
if %size% lss 1024 (
    set "%~2=%size% KB"
    goto :eof
)
set /a size=%size%/1024
if %size% lss 1024 (
    set "%~2=%size% MB"
    goto :eof
)
set /a size=%size%/1024
set "%~2=%size% GB"
goto :eof
