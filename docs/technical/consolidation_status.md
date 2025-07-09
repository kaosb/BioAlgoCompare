# Estado de Consolidación de Scripts

Este documento registra el estado actual de la consolidación de scripts en el proyecto BioAlgoCompare, siguiendo el plan de simplificación y eliminación de redundancias.

## Estructura Actual

| Tipo | Script | Ubicación | Función |
|------|--------|-----------|---------|
| Principal | `run.py` | `scripts/run.py` | Ejecución de algoritmos individuales |
| Principal | `analyze.py` | `scripts/analyze.py` | Script unificado de análisis |
| Principal | `run_massive.py` | `scripts/run_massive.py` | Ejecuciones masivas (1000+) |

## Cambios Realizados

1. ✅ **Eliminación de redundancias del directorio raíz**:
   - Eliminado `run.py` (redundante con `scripts/run.py`)
   - Eliminado `analyze_results.py` (funcionalidad en `scripts/analyze.py`)
   - Eliminado `analyze_1000runs.py` (funcionalidad en `scripts/analyze.py`)
   - Eliminado `run_comparative.py` (redundante)
   - Eliminado `run_massive.py` (redundante con `scripts/run_massive.py`)

2. ✅ **Consolidación en directorio scripts/**:
   - Eliminado `analyze_all.py` (funcionalidad en `analyze.py`)
   - Eliminado `analyze_results.py` (funcionalidad en `analyze.py`)
   - Eliminado directorio `legacy/` completo (no necesario)

3. ✅ **Estructura final simplificada**:
   - Solo 3 scripts esenciales: `run.py`, `analyze.py` y `run_massive.py`
   - Todos ubicados en directorio `scripts/`
   - Documentación actualizada

## Estrategia de Ejecución

Tras la consolidación, los scripts deben ejecutarse de la siguiente manera:

### Ejecución de Algoritmos Individuales

```bash
python scripts/run.py --algorithm ALGORITMO --instance INSTANCIA [opciones]
```

### Benchmarking y Análisis

```bash
python scripts/analyze.py COMANDO [opciones]
```

Comandos disponibles en analyze.py:
- `run`: Ejecución de algoritmos (similar a `run.py`)
- `benchmark`: Benchmarking comparativo
- `massive`: Ejecuciones masivas (1000+)
- `analyze-csv`: Análisis de resultados existentes

### Ejecuciones Masivas (alternativa directa)

```bash
python scripts/run_massive.py [opciones]
```

Esta es una alternativa directa al comando `massive` de analyze.py, cuando se prefiere un script específico para este fin.

## Ventajas de la Consolidación

1. **Simplicidad máxima**: Reducido a solo 3 scripts esenciales
2. **Eliminación de redundancia**: Sin código duplicado ni versiones alternativas
3. **Claridad estructural**: Todos los scripts están en una única ubicación
4. **Facilidad de mantenimiento**: Menos archivos para mantener y actualizar
5. **Menos confusión para usuarios**: Ruta clara de entrada para cada funcionalidad

## Uso de Scripts Principales

### scripts/run.py

Ejecución de algoritmos individuales o comparaciones:

```bash
# Ejecutar un algoritmo
python scripts/run.py --algorithm ewa --instance P-n16-k8 --iterations 100

# Comparar todos los algoritmos
python scripts/run.py --algorithm all --instance E-n22-k4 --runs 5 --parallel
```

### scripts/analyze.py

Análisis completo y benchmarking:

```bash
# Ejecutar benchmark completo
python scripts/analyze.py benchmark --run-benchmark --algorithms egto,foa,hoa --instances E-n22-k4 --runs 30

# Analizar resultados existentes
python scripts/analyze.py analyze-csv results/benchmark_results.csv
```

### scripts/run_massive.py

Ejecuciones masivas con 1000+ repeticiones:

```bash
# Benchmark masivo
python scripts/run_massive.py --algorithm all --runs 1000 --parallel --resume
```

## Metodología Científica

La estructura simplificada facilita la reproducibilidad científica mediante:

1. **Provenance clara**: Todos los parámetros y configuraciones son evidentes
2. **Simplificación del flujo de trabajo**: Menos puntos de entrada, menos confusión
3. **Transparencia mejorada**: Scripts claros y documentados con funcionalidad específica
4. **Estandarización**: Enfoque unificado para todas las operaciones

Para información completa sobre rigor científico, consulte [reproducibility.md](../scientific/reproducibility.md).
