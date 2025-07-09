# BioAlgoCompare CLI

Interfaz de línea de comandos unificada para el framework BioAlgoCompare.

## Instalación

### Método 1: Instalación directa (recomendado)

```bash
# Desde el directorio del proyecto
pip install -e .
```

Esto instalará el comando `bioalgocompare` globalmente en tu entorno Python.

### Método 2: Uso directo

```bash
# Desde el directorio del proyecto
python bioalgocompare.py [COMANDO]
```

## Comandos Disponibles

### 📊 `run` - Ejecutar Algoritmos

Ejecuta un algoritmo bio-inspirado en una instancia VRP.

```bash
# Ejecución básica
bioalgocompare run woa P-n16-k8.vrp

# Con parámetros personalizados
bioalgocompare run sma P-n19-k2.vrp -p 50 -n 200 -r 50

# Modo massive (1000 runs con checkpoints)
bioalgocompare run gto P-n16-k8.vrp --mode massive --checkpoint-interval 100

# Modo experiment con semillas específicas
bioalgocompare run opa P-n16-k8.vrp --mode experiment --experiment-seeds "42,123,456"

# Con gráficos
bioalgocompare run woa P-n16-k8.vrp --plot
```

**Opciones principales:**
- `-p, --population`: Tamaño de población (default: 30)
- `-n, --iterations`: Número de iteraciones (default: 100)
- `-r, --runs`: Número de ejecuciones (default: 30)
- `-s, --seed`: Semilla aleatoria
- `--mode`: Modo de ejecución (standard/massive/experiment)
- `--plot/--no-plot`: Generar gráficos
- `--parallel/--no-parallel`: Ejecución paralela
- `-w, --workers`: Número de workers paralelos

### 🔬 `benchmark` - Ejecutar Benchmarks

Ejecuta múltiples algoritmos en múltiples instancias.

```bash
# Benchmark básico
bioalgocompare benchmark -a woa,sma,gto -i P-n16-k8,P-n19-k2

# Con parámetros personalizados
bioalgocompare benchmark \
    -a woa,sma,gto,mrfo,aha,ewa \
    -i P-n16-k8,P-n19-k2,P-n20-k2 \
    -p 50 -n 200 -r 50
```

**Opciones:**
- `-a, --algorithms`: Algoritmos a ejecutar (separados por coma)
- `-i, --instances`: Instancias VRP (separadas por coma)
- `-p, --population`: Tamaño de población
- `-n, --iterations`: Número de iteraciones
- `-r, --runs`: Número de ejecuciones por algoritmo

### 📈 `analyze` - Analizar Resultados

Analiza resultados de experimentos previos.

```bash
# Análisis básico
bioalgocompare analyze results/experiment_20240101.json

# Análisis detallado con comparación
bioalgocompare analyze results/benchmark_20240101.json --format detailed --compare

# Análisis estadístico
bioalgocompare analyze results/massive_run.json --format statistical

# Guardar reporte
bioalgocompare analyze results/data.json -o report.md
```

**Opciones:**
- `--format`: Formato de análisis (summary/detailed/statistical)
- `--compare/--no-compare`: Comparar múltiples algoritmos
- `--plot/--no-plot`: Generar gráficos
- `-o, --output`: Archivo de salida para el reporte

### 📁 `datasets` - Gestión de Datasets

Comandos para gestionar datasets VRP.

```bash
# Verificar datasets disponibles
bioalgocompare datasets check

# Descargar datasets faltantes (en desarrollo)
bioalgocompare datasets download
```

### 🔄 `migrate` - Migración de Algoritmos

Herramientas para migrar algoritmos de v1 a v2.

```bash
# Migrar un algoritmo
bioalgocompare migrate algorithm my_algo --output algorithms/my_algo_v2.py

# Forzar sobrescritura
bioalgocompare migrate algorithm my_algo --force
```

### ℹ️ `info` - Información del Sistema

Muestra información sobre el proyecto y algoritmos disponibles.

```bash
bioalgocompare info
```

### 📋 `inventory` - Inventario del Repositorio

Genera un inventario del repositorio.

```bash
# Inventario básico
bioalgocompare inventory

# Inventario detallado
bioalgocompare inventory --detailed
```

### 🎯 `dashboard` - Dashboard de Visualización

Lanza el dashboard interactivo (en desarrollo).

```bash
# Lanzar dashboard
bioalgocompare dashboard

# En puerto específico
bioalgocompare dashboard --port 8080

# Modo debug
bioalgocompare dashboard --debug
```

## Algoritmos Disponibles

Los siguientes algoritmos están disponibles en versión v2:

| Código | Nombre Completo |
|--------|----------------|
| `sho` | Spotted Hyena Optimizer |
| `apo` | African Penguin Optimization |
| `egto` | Enhanced Gorilla Troops Optimizer |
| `fsa` | Fish School Algorithm |
| `foa` | Fruit Fly Optimization Algorithm |
| `woa` | Whale Optimization Algorithm |
| `hho` | Harris Hawks Optimization |
| `mrfo` | Manta Ray Foraging Optimization |
| `sma` | Slime Mould Algorithm |
| `gto` | Gorilla Troops Optimizer |
| `ewa` | Earthworm Algorithm |
| `aha` | Artificial Hummingbird Algorithm |
| `rro` | Raven Roosting Optimization |
| `gvoa` | Growth Variation Optimization Algorithm |
| `smo` | Starling Murmuration Optimizer |
| `opa` | Orca Predation Algorithm |
| `hoa` | Hyena Optimization Algorithm |
| `fgo` | Flamingo Optimization Algorithm |

## Ejemplos de Uso

### Experimento Completo

```bash
# 1. Verificar datasets
bioalgocompare datasets check

# 2. Ejecutar benchmark
bioalgocompare benchmark \
    -a woa,sma,gto,mrfo \
    -i P-n16-k8,P-n19-k2,P-n20-k2 \
    -r 50

# 3. Analizar resultados
bioalgocompare analyze results/benchmark_*.json --format detailed

# 4. Ejecutar algoritmo específico con más detalle
bioalgocompare run woa P-n16-k8.vrp --mode massive --plot
```

### Comparación Rápida

```bash
# Ejecutar 3 algoritmos en una instancia
for algo in woa sma gto; do
    bioalgocompare run $algo P-n16-k8.vrp -r 30 --plot
done

# Analizar todos los resultados
bioalgocompare analyze results/*.json --compare
```

## Estructura de Archivos de Salida

Los resultados se guardan en los siguientes directorios:

```
results/          # Resultados de experimentos (JSON, CSV)
plots/            # Gráficos generados
checkpoints/      # Checkpoints para modo massive
```

### Formato de Resultados JSON

```json
{
  "stats": {
    "algorithm": "woa",
    "instance": "P-n16-k8",
    "total_runs": 30,
    "best_fitness": 450.123,
    "mean_fitness": 465.789,
    "std_fitness": 12.345,
    ...
  },
  "results": [
    {
      "run_id": 0,
      "seed": 42,
      "fitness": 450.123,
      "solution": [...],
      "convergence": [...],
      "execution_time": 2.345
    },
    ...
  ]
}
```

## Tips y Mejores Prácticas

1. **Para benchmarks largos**: Usa el modo `massive` con checkpoints
2. **Para reproducibilidad**: Siempre especifica una semilla con `-s`
3. **Para análisis rápido**: Usa `--plot` para visualización inmediata
4. **Para comparaciones**: Ejecuta múltiples algoritmos con los mismos parámetros
5. **Para desarrollo**: Instala con `pip install -e .[dev]` para herramientas adicionales

## Solución de Problemas

### El comando no se encuentra

```bash
# Reinstalar en modo editable
pip install -e .

# O usar directamente
python bioalgocompare.py [comando]
```

### Error de importación

```bash
# Asegurarse de estar en el directorio correcto
cd /path/to/bioalgocompare

# Verificar instalación
pip list | grep bioalgocompare
```

### Memoria insuficiente en ejecuciones paralelas

```bash
# Reducir número de workers
bioalgocompare run woa instance.vrp --workers 2

# O desactivar paralelismo
bioalgocompare run woa instance.vrp --no-parallel
```