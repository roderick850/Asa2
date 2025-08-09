#!/bin/bash

echo "========================================"
echo "  ARK SERVER MANAGER - BUILD SCRIPT"
echo "========================================"
echo

# Verificar si PyInstaller está instalado
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "[ERROR] PyInstaller no está instalado."
    echo "Instalando PyInstaller..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "[ERROR] No se pudo instalar PyInstaller."
        echo "Por favor, ejecuta: pip3 install pyinstaller"
        exit 1
    fi
fi

echo "[INFO] PyInstaller encontrado."
echo

# Limpiar build anterior
if [ -d "build" ]; then
    echo "[INFO] Limpiando directorio build anterior..."
    rm -rf "build"
fi

if [ -d "dist" ]; then
    echo "[INFO] Limpiando directorio dist anterior..."
    rm -rf "dist"
fi

echo "[INFO] Iniciando compilación..."
echo

# Compilar con el archivo spec
pyinstaller main.spec --clean --noconfirm

if [ $? -ne 0 ]; then
    echo
    echo "[ERROR] Error durante la compilación."
    echo "Revisa los mensajes de error anteriores."
    exit 1
fi

echo
echo "========================================"
echo "            BUILD COMPLETADO"
echo "========================================"
echo

# Verificar si el ejecutable fue creado
if [ -f "dist/ArkServerManager" ]; then
    echo "[SUCCESS] ✅ Ejecutable creado exitosamente con icono personalizado!"
    echo "[INFO] Icono: ico/ArkManager.ico"
    echo
    echo "El ejecutable se encuentra en: dist/ArkServerManager"
    echo
    echo "Tamaño del archivo:"
    ls -lh "dist/ArkServerManager" | awk '{print $5}'
    echo
    
    # Hacer el archivo ejecutable
    chmod +x "dist/ArkServerManager"
    
    read -p "¿Quieres ejecutar la aplicación ahora? (s/n): " run
    if [[ $run == "s" || $run == "S" ]]; then
        echo "[INFO] Ejecutando ArkServerManager..."
        ./dist/ArkServerManager &
    fi
else
    echo "[ERROR] ❌ No se pudo crear el ejecutable."
fi

echo
echo "Script completado."
