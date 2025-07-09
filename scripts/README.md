# Scripts de BioAlgoCompare

Estructura reorganizada de scripts para mayor claridad y mantenibilidad.

## Estructura

```
scripts/
├── core/                  # Scripts principales
│   ├── run.py            # Runner unificado para algoritmos
│   └── analyze.py        # Análisis unificado de resultados
├── utilities/            # Utilidades auxiliares
│   ├── manage_datasets.py    # Gestión de datasets
│   ├── inventory.py          # Análisis del repositorio
│   └── migrate_algorithm.py  # Migración de algoritmos v1 a v2
├── deprecated/           # Scripts obsoletos (referencia histórica)
│   └── README.md
└── benchmark.py          # Script principal de benchmarking
```

## Scripts Principales

### `core/run.py`
Script unificado para ejecutar algoritmos bio-inspirados con tres modos:

- **standard**: Ejecución normal con número específico de runs
- **massive**: Benchmark masivo (1000 runs) con sistema de checkpoints
- **experiment**: Ejecución con semillas específicas

Ejemplos:
```bash
# Modo standard
python scripts/core/run.py --mode standard -a woa -i P-n16-k8.vrp -r 30

# Modo massive con checkpoint
python scripts/core/run.py --mode massive -a sma -i P-n16-k8.vrp --checkpoint-interval 100

# Modo experiment con semillas específicas
python scripts/core/run.py --mode experiment -a opa -i P-n16-k8.vrp --experiment-seeds "42,123,456"
```

### `core/analyze.py`
Análisis unificado que combina múltiples herramientas de análisis:
- Análisis estadístico completo
- Generación de gráficos
- Comparación de algoritmos
- Análisis de significancia estadística

### `benchmark.py`
Script mejorado para ejecutar benchmarks completos:
- Ejecuta múltiples algoritmos en múltiples instancias
- Manejo robusto de errores
- Generación automática de reportes

## Utilidades

### `utilities/manage_datasets.py`
- Verifica disponibilidad de datasets
- Descarga datasets faltantes
- Crea enlaces simbólicos

### `utilities/inventory.py`
- Analiza la estructura del repositorio
- Identifica archivos no utilizados
- Genera reporte de dependencias

### `utilities/migrate_algorithm.py`
- Migración semi-automática de algoritmos v1 a v2
- Genera estructura base y tests

## Migración desde Scripts Antiguos

Si usabas los scripts antiguos, aquí está la equivalencia:

| Script Antiguo | Nuevo Script | Modo/Opción |
|---|---|---|
| `run.py` | `core/run.py` | `--mode standard` |
| `run_massive.py` | `core/run.py` | `--mode massive` |
| `run_opa_experiment.py` | `core/run.py` | `--mode experiment` |
| `ejecutar_benchmark.py` | `benchmark.py` | - |
| `analyze.py` | `core/analyze.py` | - |

## Notas

- Todos los scripts ahora usan por defecto las versiones v2 de los algoritmos
- Los resultados se guardan en directorios organizados: `results/`, `plots/`, `checkpoints/`
- Los scripts deprecated se mantienen solo como referencia histórica