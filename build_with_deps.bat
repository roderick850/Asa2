@echo off
echo ============================================
echo   🚀 BUILD ARK SERVER MANAGER CON DEPS
echo ============================================
echo.

echo [INFO] Activando entorno virtual...
call .venv\Scripts\activate.bat

echo [INFO] Instalando/actualizando dependencias...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo [INFO] Verificando dependencias críticas...
python -c "import requests; print('✅ requests OK')" || (echo "❌ Error con requests" && exit /b 1)
python -c "import pystray; print('✅ pystray OK')" || (echo "❌ Error con pystray" && exit /b 1)
python -c "import customtkinter; print('✅ customtkinter OK')" || (echo "❌ Error con customtkinter" && exit /b 1)

echo [INFO] Limpiando archivos anteriores...
if exist "dist\ArkServerManager.exe" (
    taskkill /f /im ArkServerManager.exe 2>nul
    del /f "dist\ArkServerManager.exe" 2>nul
)
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo [INFO] Compilando ejecutable...
python -m PyInstaller main.spec

if exist "dist\ArkServerManager.exe" (
    echo.
    echo [SUCCESS] ✅ Ejecutable creado exitosamente!
    echo [INFO] Ubicación: dist\ArkServerManager.exe
    echo [INFO] Icono: ico\ArkManager.ico
    echo.
    for %%I in ("dist\ArkServerManager.exe") do (
        set size=%%~zI
        set /a sizeMB=!size!/1024/1024
        echo [INFO] Tamaño: !sizeMB! MB
    )
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
