# Guía de Uso Completa

Esta guía proporciona instrucciones detalladas sobre cómo utilizar BioAlgoCompare para realizar comparaciones rigurosas de algoritmos metaheurísticos bioinspirados aplicados a problemas de ruteo de vehículos (VRP).

## Contenido

1. [Flujos de Trabajo Comunes](#flujos-de-trabajo-comunes)
2. [Ejecución de Algoritmos Individuales](#ejecución-de-algoritmos-individuales)
3. [Benchmarking Comparativo](#benchmarking-comparativo)
4. [Ejecuciones Masivas y Análisis Estadístico](#ejecuciones-masivas-y-análisis-estadístico)
5. [Visualización y Exportación de Resultados](#visualización-y-exportación-de-resultados)
6. [Análisis de Archivos CSV](#análisis-de-archivos-csv)
7. [Consideraciones para Investigación Científica](#consideraciones-para-investigación-científica)
8. [Solución de Problemas Comunes](#solución-de-problemas-comunes)

## Flujos de Trabajo Comunes

Según sus objetivos, puede elegir entre varios flujos de trabajo:

### 1. Exploración Rápida

Para explorar rápidamente el comportamiento de un algoritmo en una instancia específica:

```bash
python scripts/run.py --algorithm egto --instance P-n16-k8 --iterations 100
```

### 2. Análisis Comparativo

Para comparar varios algoritmos en una instancia:

```bash
python scripts/run.py --algorithm all --instance E-n22-k4 --runs 5 --parallel
```

### 3. Estudio de Rendimiento Profundo

Para realizar un análisis estadístico riguroso:

```bash
python scripts/analyze.py benchmark --run-benchmark --parallel \
    --instances E-n22-k4,P-n16-k8 --algorithms egto,foa,hoa --runs 30
```

### 4. Análisis Científico Masivo

Para estudios que requieren alta confianza estadística:

```bash
python scripts/analyze.py massive --runs 1000 --algorithm egto,foa --parallel
```

## Ejecución de Algoritmos Individuales

El script principal para ejecutar algoritmos individuales es `scripts/run.py`.

### Sintaxis Básica

```bash
python scripts/run.py --algorithm ALGORITMO --instance INSTANCIA [opciones]
```

### Parámetros Principales

| Parámetro | Descripción | Valor Predeterminado |
|-----------|-------------|----------------------|
| `--algorithm`, `-a` | Algoritmo a ejecutar | (Requerido) |
| `--instance`, `-i` | Nombre de la instancia VRP | (Requerido) |
| `--iterations`, `-n` | Número de iteraciones | 100 |
| `--population`, `-p` | Tamaño de la población | 30 |
| `--runs`, `-r` | Número de ejecuciones | 1 |
| `--seed`, `-s` | Semilla para reproducibilidad | (Aleatorio) |
| `--visualize/--no-visualize` | Activar/desactivar visualización | True |
| `--save/--no-save` | Guardar resultados | True |
| `--parallel/--no-parallel` | Ejecución paralela | False |

### Algoritmos Disponibles

| Código | Nombre Completo | Inspiración |
|--------|-----------------|-------------|
| `hoa` o `sho` | Spotted Hyena Optimizer | Estrategias de caza de hienas |
| `apo` | Artificial Protozoa Optimizer | Comportamiento de protozoarios |
| `egto` | Enhanced Gorilla Troops Optimization | Comportamiento social de gorilas mejorado |
| `fgo` o `fsa` | Flamingo Search Algorithm | Comportamiento de flamencos |
| `foa` | Fossa Optimization Algorithm | Comportamiento de cazadores fosasa |
| `woa` | Whale Optimization Algorithm | Estrategia alimentaria de ballenas |
| `hho` | Harris Hawks Optimization | Caza cooperativa de halcones |
| `mrfo` | Manta Ray Foraging Optimization | Alimentación de mantarrayas |
| `sma` | Slime Mould Algorithm | Comportamiento de moho viscoso |
| `gto` | Gorilla Troops Optimizer | Jerarquía social de gorilas |
| `ewa` | Earthworm Algorithm | Movimiento de lombrices |
| `all` | Todos los algoritmos | - |

### Ejemplos de Uso

#### Ejecución Básica
```bash
python scripts/run.py --algorithm ewa --instance P-n16-k8
```

#### Control de Reproducibilidad
```bash
python scripts/run.py --algorithm egto --instance E-n22-k4 --seed 42
```

#### Múltiples Ejecuciones
```bash
python scripts/run.py --algorithm foa --instance A-n32-k5 --runs 10 --parallel
```

#### Estudio de Parámetros
```bash
# Probar diferentes tamaños de población
python scripts/run.py --algorithm gto --instance E-n22-k4 --population 20 --seed 123
python scripts/run.py --algorithm gto --instance E-n22-k4 --population 50 --seed 123
python scripts/run.py --algorithm gto --instance E-n22-k4 --population 100 --seed 123

# Probar diferentes números de iteraciones
python scripts/run.py --algorithm gto --instance E-n22-k4 --iterations 50 --seed 123
python scripts/run.py --algorithm gto --instance E-n22-k4 --iterations 200 --seed 123
python scripts/run.py --algorithm gto --instance E-n22-k4 --iterations 500 --seed 123
```

## Benchmarking Comparativo

Para realizar comparaciones sistemáticas entre algoritmos, use `scripts/analyze.py benchmark`.

### Sintaxis Básica

```bash
python scripts/analyze.py benchmark [opciones]
```

### Parámetros Principales

| Parámetro | Descripción | Valor Predeterminado |
|-----------|-------------|----------------------|
| `--input`, `-i` | Archivo de resultados existente | None |
| `--run-benchmark/--no-run-benchmark` | Ejecutar nuevo benchmark | False |
| `--instances`, `-inst` | Instancias para benchmark (separadas por coma) | ['P-n16-k8', 'E-n22-k4'] |
| `--algorithms`, `-a` | Algoritmos para benchmark (separados por coma) | [todos] |
| `--runs`, `-r` | Ejecuciones por algoritmo | 5 |
| `--iterations`, `-n` | Iteraciones por ejecución | 100 |
| `--population`, `-p` | Tamaño de población | 30 |
| `--seed`, `-s` | Semilla base | 42 |
| `--parallel/--no-parallel` | Ejecución paralela | False |
| `--optimize/--no-optimize` | Aplicar optimización local | False |
| `--output-dir`, `-o` | Directorio de salida | auto |

### Ejemplos de Uso

#### Benchmark Básico
```bash
python scripts/analyze.py benchmark --run-benchmark
```

#### Benchmark Personalizado
```bash
python scripts/analyze.py benchmark --run-benchmark \
    --instances P-n16-k8,E-n22-k4 \
    --algorithms egto,foa,hoa \
    --runs 10 --parallel
```

#### Benchmark con Optimización Local
```bash
python scripts/analyze.py benchmark --run-benchmark --optimize \
    --instances A-n32-k5 \
    --algorithms egto,gto \
    --runs 5
```

#### Analizar Benchmark Existente
```bash
python scripts/analyze.py benchmark --input results/benchmark_20250508_123456.json
```

## Ejecuciones Masivas y Análisis Estadístico

Para análisis estadístico riguroso con muchas ejecuciones (1000+):

### Sintaxis Básica

```bash
python scripts/analyze.py massive [opciones]
```

### Parámetros Principales

| Parámetro | Descripción | Valor Predeterminado |
|-----------|-------------|----------------------|
| `--runs`, `-r` | Ejecuciones por algoritmo | 1000 |
| `--iterations`, `-n` | Iteraciones por ejecución | 100 |
| `--population`, `-p` | Tamaño de población | 40 |
| `--seed`, `-s` | Semilla base | 42 |
| `--algorithm`, `-a` | Algoritmos (separados por coma) | ['all'] |
| `--instances`, `-i` | Instancias (separadas por coma) | ['E-n22-k4', 'P-n16-k8', 'A-n32-k5'] |
| `--parallel/--no-parallel` | Ejecución paralela | True |
| `--resume/--no-resume` | Reanudar si hay interrupción | True |

### Ejemplos de Uso

#### Benchmark Masivo para un Algoritmo
```bash
python scripts/analyze.py massive --algorithm egto --runs 1000
```

#### Benchmark Masivo Múltiple
```bash
python scripts/analyze.py massive --algorithm egto,foa,hoa --runs 1000 \
    --instances E-n22-k4 --parallel
```

#### Reanudar Benchmark Interrumpido
```bash
python scripts/analyze.py massive --resume
```

## Visualización y Exportación de Resultados

Los resultados se guardan automáticamente en el directorio `results/`:

### Estructura de Resultados

```
results/
├── {instancia}_{timestamp}.csv           # Resultados detallados
├── {instancia}_{timestamp}_summary.csv   # Resumen estadístico
├── {algoritmo}_{instancia}_solution.png  # Visualización de ruta
├── {algoritmo}_{instancia}_convergence.png # Curva de convergencia
├── comparison_{instancia}.png            # Comparación de algoritmos
├── benchmarks/                           # Resultados de benchmarks
└── massive_{timestamp}/                  # Resultados de ejecuciones masivas
    ├── benchmark_state.json.gz           # Estado completo (checkpoint)
    ├── massive_benchmark_summary.csv     # Resumen estadístico
    └── massive_benchmark_report.html     # Informe interactivo
```

### Volver a Generar Visualizaciones

Puede regenerar visualizaciones a partir de resultados guardados:

```bash
python scripts/analyze.py analyze-csv results/{instancia}_{timestamp}.csv
```

### Exportar para Publicación Científica

```bash
python scripts/analyze.py analyze-csv \
    --input results/benchmark_final.csv \
    --publication-ready \
    --output-dir results/publication_figures
```

## Análisis de Archivos CSV

Para analizar resultados existentes en formato CSV:

### Sintaxis Básica

```bash
python scripts/analyze.py analyze-csv CSV_FILE [opciones]
```

### Parámetros Principales

| Parámetro | Descripción | Valor Predeterminado |
|-----------|-------------|----------------------|
| `--output-dir`, `-o` | Directorio de salida | None |
| `--format`, `-f` | Formato de figuras (png, pdf, svg) | png |
| `--dpi` | Resolución de figuras | 300 |
| `--publication-ready/--no-publication-ready` | Figuras para publicación | False |

### Ejemplos de Uso

```bash
python scripts/analyze.py analyze-csv results/benchmark_20250508_123456.csv \
    --publication-ready --format pdf
```

## Consideraciones para Investigación Científica

### Reproducibilidad

Para garantizar resultados reproducibles:

1. **Siempre especifique una semilla**:
   ```bash
   python scripts/run.py --algorithm egto --instance E-n22-k4 --seed 42
   ```

2. **Documente los parámetros completos**:
   Los archivos de resultados incluyen metadatos con parámetros, pero también es buena práctica documentarlos manualmente.

3. **Guarde versiones de software**:
   ```bash
   pip freeze > requirements_frozen.txt
   ```

### Rigor Estadístico

1. **Múltiples ejecuciones**:
   Para conclusiones estadísticamente significativas, use al menos 30 ejecuciones:
   ```bash
   python scripts/run.py --algorithm egto --instance E-n22-k4 --runs 30
   ```

2. **Tests estadísticos**:
   El análisis automático incluye tests estadísticos (Friedman, Wilcoxon, etc.) y corrección para comparaciones múltiples.

3. **Tamaño del efecto**:
   Los informes incluyen medidas de tamaño del efecto (Cliff's Delta, Vargha-Delaney).

## Solución de Problemas Comunes

### Error: Memoria Insuficiente

Si encuentra errores de memoria durante ejecuciones paralelas:

```bash
# Reducir el paralelismo
python scripts/run.py --algorithm all --instance E-n22-k4 --runs 10 --parallel \
    --max-workers 4  # Limitar número de procesos
```

### Error: Instancia No Encontrada

Si aparece "La instancia X no existe":

```bash
# Listar instancias disponibles
ls data/vrp/
```

### Interrupción de Ejecuciones Largas

Para ejecuciones masivas, siempre use la opción `--resume`:

```bash
python scripts/analyze.py massive --resume
```

### Problemas de Visualización

Si las visualizaciones no se muestran correctamente:

```bash
# Cambiar el backend de matplotlib
echo "backend: TkAgg" > ~/.matplotlib/matplotlibrc
```

## Recursos Adicionales

- [Referencia Detallada de Scripts](../technical/scripts_reference.md)
- [Guía de Benchmarking](benchmarking.md)
- [Documentación de Algoritmos](../algorithms/overview.md)
- [Análisis Comparativo](../analysis/comparison.md)