# Guía de Instalación

## Requisitos del Sistema

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Git (para clonar el repositorio)
- Sistema operativo: Linux, macOS o Windows

## Instalación Rápida

### 1. Clonar el Repositorio

```bash
git clone https://github.com/yourusername/bioalgocompare.git
cd bioalgocompare
```

### 2. Crear Entorno Virtual (Recomendado)

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Linux/macOS:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

### 3. Instalar BioAlgoCompare

#### Opción A: Instalación para Usuarios

```bash
pip install -e .
```

#### Opción B: Instalación para Desarrolladores

```bash
pip install -e ".[dev]"
```

#### Opción C: Instalación con Dashboard

```bash
pip install -e ".[dashboard]"
```

#### Opción D: Instalación Completa

```bash
pip install -e ".[dev,dashboard]"
```

## Verificar la Instalación

```bash
# Verificar que el CLI está instalado
bioalgocompare --version

# Ver comandos disponibles
bioalgocompare --help

# Verificar información del sistema
bioalgocompare info
```

## Dependencias Principales

Las siguientes dependencias se instalan automáticamente:

- **numpy** >= 1.20: Cálculos numéricos
- **pandas** >= 1.3: Manejo de datos
- **matplotlib** >= 3.4: Visualización
- **seaborn** >= 0.11: Gráficos estadísticos
- **scipy** >= 1.7: Funciones científicas
- **tqdm** >= 4.62: Barras de progreso
- **click** >= 8.0: Interfaz de línea de comandos

## Dependencias Opcionales

### Para Desarrollo

- **pytest** >= 6.2: Framework de testing
- **pytest-cov** >= 2.12: Cobertura de código
- **black** >= 21.6: Formateador de código
- **flake8** >= 3.9: Linter
- **mypy** >= 0.910: Type checking

### Para Dashboard

- **dash** >= 2.0: Framework web
- **plotly** >= 5.3: Visualización interactiva

## Configuración de Datasets

### 1. Verificar Datasets Disponibles

```bash
bioalgocompare datasets check
```

### 2. Estructura de Directorios

Asegúrate de que existe la siguiente estructura:

```
bioalgocompare/
├── data/
│   └── vrp/
│       ├── Solomon/
│       ├── Augerat/
│       └── Christofides/
```

### 3. Agregar Datasets

Coloca los archivos `.vrp` en el directorio correspondiente:

```bash
# Ejemplo
cp mis_instancias/*.vrp data/vrp/
```

## Configuración Avanzada

### Variables de Entorno

```bash
# Número de CPUs para paralelización
export BIOALGO_MAX_WORKERS=4

# Directorio de datos personalizado
export BIOALGO_DATA_DIR=/path/to/data

# Nivel de logging
export BIOALGO_LOG_LEVEL=INFO
```

### Archivo de Configuración

Crea `~/.bioalgocompare/config.json`:

```json
{
  "default_population": 50,
  "default_iterations": 200,
  "parallel_enabled": true,
  "max_workers": 4,
  "output_format": "json",
  "plot_enabled": true
}
```

## Solución de Problemas

### Error: "Command not found"

```bash
# Reinstalar en modo editable
pip uninstall bioalgocompare
pip install -e .

# Verificar PATH
which bioalgocompare
```

### Error: "No module named 'algorithms'"

```bash
# Asegurarse de estar en el directorio correcto
cd /path/to/bioalgocompare

# Reinstalar
pip install -e .
```

### Error: "Permission denied"

```bash
# En Linux/macOS, usar --user
pip install --user -e .

# O usar sudo (no recomendado)
sudo pip install -e .
```

### Error en Windows

```powershell
# Usar comillas dobles en PowerShell
pip install -e ".[dev]"

# Verificar política de ejecución
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Actualización

### Actualizar desde Git

```bash
git pull origin main
pip install -e . --upgrade
```

### Actualizar Dependencias

```bash
pip install -e . --upgrade --upgrade-strategy eager
```

## Desinstalación

```bash
# Desinstalar BioAlgoCompare
pip uninstall bioalgocompare

# Desactivar y eliminar entorno virtual
deactivate
rm -rf venv/
```

## Docker (Opcional)

### Construir Imagen

```bash
docker build -t bioalgocompare .
```

### Ejecutar Contenedor

```bash
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  bioalgocompare run woa P-n16-k8.vrp
```

## Verificación Final

Ejecuta el siguiente comando para verificar que todo está correctamente instalado:

```bash
# Test rápido
bioalgocompare run woa P-n16-k8.vrp -r 5 -n 10 -p 10

# Si funciona, deberías ver:
# 🚀 Ejecutando WOA en P-n16-k8.vrp
# ... resultados ...
# ✅ Ejecución completada
```

## Siguiente Paso

Una vez instalado, consulta la [Guía de Inicio Rápido](QUICKSTART.md) para comenzar a usar BioAlgoCompare.