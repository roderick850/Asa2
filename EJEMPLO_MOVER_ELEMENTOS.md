# 🎯 Cómo Mover Elementos en la Interfaz

## 📍 Sistema de Grid (Cuadrícula)

La interfaz usa un sistema de **grid** con filas y columnas numeradas desde 0.

### 🏗️ Estructura Principal

```python
# En __init__ - Filas principales
self.root.grid_rowconfigure(2, weight=1)  # Fila 2 es flexible

# Filas disponibles:
# row=0: Barra superior (top_bar) - Botones admin + Estado
# row=1: Barra de pestañas (tabs_bar) - Pestañas de navegación
# row=2: Área de contenido (tabview) - Contenido de las pestañas
# row=3: Barra de logs (logs_bar) - Logs siempre visibles
```

### 🔧 Cómo Mover Elementos

#### **1. Mover elementos dentro de la barra superior (top_bar)**

```python
# POSICIÓN ACTUAL:
# row=0, column=0: Botones de administración (izquierda)
# row=0, column=2: Panel de estado (derecha)
# row=1, column=0-2: Ruta raíz (centro)
# row=2, column=0-4: Selección servidor/mapa (centro)

# PARA MOVER:
# Ejemplo: Mover panel de estado a la izquierda
status_frame.grid(row=0, column=0, padx=10, pady=5, sticky="w")  # Cambiar column=2 a column=0

# Ejemplo: Mover botones de administración a la derecha
admin_frame.grid(row=0, column=2, padx=10, pady=5, sticky="e")  # Cambiar column=0 a column=2
```

#### **2. Mover elementos entre filas principales**

```python
# Para mover toda la barra de logs arriba:
self.logs_bar.grid(row=1, column=0, sticky="ew", padx=0, pady=0)  # Cambiar row=3 a row=1

# Para mover las pestañas abajo:
self.tabs_bar.grid(row=2, column=0, sticky="ew", padx=0, pady=0)  # Cambiar row=1 a row=2
```

#### **3. Cambiar el orden de creación**

```python
def __init__(self, root, config_manager, logger):
    # El orden afecta la posición
    self.create_logs_bar()      # Se crea primero (row=0)
    self.create_top_bar()       # Se crea segundo (row=1)
    self.create_tabs_bar()      # Se crea tercero (row=2)
    self.create_tabview()       # Se crea cuarto (row=3)
```

### 📋 Ejemplos Prácticos

#### **Ejemplo 1: Mover panel de estado a la izquierda**

```python
# En create_top_bar()
# Cambiar esta línea:
status_frame.grid(row=0, column=2, padx=10, pady=5, sticky="e")

# Por esta:
status_frame.grid(row=0, column=0, padx=10, pady=5, sticky="w")

# Y mover los botones de administración a la derecha:
admin_frame.grid(row=0, column=2, padx=10, pady=5, sticky="e")
```

#### **Ejemplo 2: Mover ruta raíz arriba de los botones**

```python
# En create_top_bar()
# Cambiar esta línea:
path_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=2, sticky="ew")

# Por esta:
path_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=2, sticky="ew")

# Y mover los botones de administración abajo:
admin_frame.grid(row=1, column=0, padx=10, pady=5, sticky="w")
```

#### **Ejemplo 3: Mover barra de logs arriba de las pestañas**

```python
# En __init__
# Cambiar el orden de creación:
self.create_logs_bar()      # row=0
self.create_tabs_bar()      # row=1
self.create_top_bar()       # row=2
self.create_tabview()       # row=3

# Y actualizar las referencias en create_logs_bar:
self.logs_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
```

### 🎨 Parámetros de Grid

```python
elemento.grid(
    row=0,           # Fila (0, 1, 2, 3...)
    column=0,        # Columna (0, 1, 2, 3...)
    sticky="ew",     # Dirección: "n", "s", "e", "w", "nsew"
    padx=10,         # Padding horizontal
    pady=5,          # Padding vertical
    columnspan=3     # Ocupar múltiples columnas
)
```

### 🔄 Comandos Útiles

```python
# Para ocultar un elemento:
elemento.grid_remove()

# Para mostrar un elemento:
elemento.grid()

# Para cambiar posición dinámicamente:
elemento.grid(row=nueva_fila, column=nueva_columna)
```

### 📝 Notas Importantes

1. **Sticky**: Controla cómo se expande el elemento

   - `"ew"`: Se expande horizontalmente
   - `"ns"`: Se expande verticalmente
   - `"nsew"`: Se expande en todas las direcciones

2. **Columnspan/Rowspan**: Para que un elemento ocupe múltiples columnas/filas

3. **Weight**: Para que una fila/columna sea flexible

   - `weight=1`: Se expande para llenar el espacio disponible

4. **Padx/Pady**: Espaciado alrededor del elemento
