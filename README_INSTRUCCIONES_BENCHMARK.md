# Instrucciones para Ejecución de Benchmark VRP

Este documento proporciona instrucciones detalladas para ejecutar pruebas de benchmark completas para el Problema de Ruteo de Vehículos (VRP) utilizando los algoritmos metaheurísticos implementados.

## Objetivo

Realizar un análisis comparativo exhaustivo de 11 algoritmos metaheurísticos en 3 instancias VRP de diferente tamaño, con 30 ejecuciones independientes para garantizar significancia estadística.

## Configuración Recomendada

- **Instancias a evaluar**: 
  - P-n16-k8 (pequeña: 16 nodos, 8 vehículos)
  - E-n22-k4 (mediana: 22 nodos, 4 vehículos)
  - M-n151-k12 (grande: 151 nodos, 12 vehículos)

- **Algoritmos a evaluar**:
  - HHO (Harris Hawks Optimization)
  - WOA (Whale Optimization Algorithm)
  - EWA (Earthworm Algorithm)
  - SMA (Slime Mould Algorithm)
  - MRFO (Manta Ray Foraging Optimization)
  - GTO (Gorilla Troops Optimization)
  - EGTO (Enhanced Gorilla Troops Optimization)
  - FOA (Forest Optimization Algorithm)
  - FGO (Flamingo Optimization)
  - HOA (Hyena Optimization Algorithm)
  - APO (Artificial Protozoa Optimizer)

- **Parámetros**:
  - Iteraciones: 500
  - Tamaño de población: 30
  - Ejecuciones por algoritmo/instancia: 30
  - Semilla: 42 (para reproducibilidad)
  - Paralelización: 8 núcleos

## Instrucciones Paso a Paso

### 1. Ejecución de Benchmark Completo

El siguiente comando ejecutará el benchmark para todas las instancias y algoritmos con 30 ejecuciones cada uno, aprovechando la paralelización de 8 núcleos:

```bash
OUTPUT_DIR="results/vrp_full_$(date +%Y%m%d_%H%M)"
mkdir -p $OUTPUT_DIR

PYTHONPATH=. python scripts/analyze_results.py \
  --run-benchmark \
  --instances P-n16-k8 E-n22-k4 M-n151-k12 \
  --algorithms hho --algorithms woa --algorithms ewa --algorithms sma \
  --algorithms mrfo --algorithms gto --algorithms egto --algorithms foa \
  --algorithms fgo --algorithms hoa --algorithms apo \
  --runs 30 \
  --iterations 500 \
  --population 30 \
  --parallel \
  --seed 42 \
  --output-dir $OUTPUT_DIR
```

### 2. Ejecución por Grupos

Si hay limitaciones de tiempo o recursos, se recomienda ejecutar el benchmark por grupos:

#### Grupo 1: Instancia pequeña (P-n16-k8)

```bash
OUTPUT_DIR="results/vrp_p16_$(date +%Y%m%d_%H%M)"
mkdir -p $OUTPUT_DIR

PYTHONPATH=. python scripts/analyze_results.py \
  --run-benchmark \
  --instances P-n16-k8 \
  --algorithms hho --algorithms woa --algorithms ewa --algorithms sma \
  --algorithms mrfo --algorithms gto --algorithms egto --algorithms foa \
  --algorithms fgo --algorithms hoa --algorithms apo \
  --runs 30 \
  --iterations 500 \
  --population 30 \
  --parallel \
  --seed 42 \
  --output-dir $OUTPUT_DIR
```

#### Grupo 2: Instancia mediana (E-n22-k4)

```bash
OUTPUT_DIR="results/vrp_e22_$(date +%Y%m%d_%H%M)"
mkdir -p $OUTPUT_DIR

PYTHONPATH=. python scripts/analyze_results.py \
  --run-benchmark \
  --instances E-n22-k4 \
  --algorithms hho --algorithms woa --algorithms ewa --algorithms sma \
  --algorithms mrfo --algorithms gto --algorithms egto --algorithms foa \
  --algorithms fgo --algorithms hoa --algorithms apo \
  --runs 30 \
  --iterations 500 \
  --population 30 \
  --parallel \
  --seed 42 \
  --output-dir $OUTPUT_DIR
```

#### Grupo 3: Instancia grande (M-n151-k12)

```bash
OUTPUT_DIR="results/vrp_m151_$(date +%Y%m%d_%H%M)"
mkdir -p $OUTPUT_DIR

PYTHONPATH=. python scripts/analyze_results.py \
  --run-benchmark \
  --instances M-n151-k12 \
  --algorithms hho --algorithms woa --algorithms ewa --algorithms sma \
  --algorithms mrfo --algorithms gto --algorithms egto --algorithms foa \
  --algorithms fgo --algorithms hoa --algorithms apo \
  --runs 30 \
  --iterations 500 \
  --population 30 \
  --parallel \
  --seed 42 \
  --output-dir $OUTPUT_DIR
```

### 3. Ejecución por Algoritmos

Para mayor modularidad, se pueden ejecutar grupos de algoritmos por separado:

#### Ejemplo: HHO, WOA, EWA (Grupo 1)

```bash
OUTPUT_DIR="results/vrp_grupo1_$(date +%Y%m%d_%H%M)"
mkdir -p $OUTPUT_DIR

PYTHONPATH=. python scripts/analyze_results.py \
  --run-benchmark \
  --instances P-n16-k8 E-n22-k4 M-n151-k12 \
  --algorithms hho --algorithms woa --algorithms ewa \
  --runs 30 \
  --iterations 500 \
  --population 30 \
  --parallel \
  --seed 42 \
  --output-dir $OUTPUT_DIR
```

#### Ejemplo: MRFO, GTO, EGTO, FOA (Grupo 2)

```bash
OUTPUT_DIR="results/vrp_grupo2_$(date +%Y%m%d_%H%M)"
mkdir -p $OUTPUT_DIR

PYTHONPATH=. python scripts/analyze_results.py \
  --run-benchmark \
  --instances P-n16-k8 E-n22-k4 M-n151-k12 \
  --algorithms mrfo --algorithms gto --algorithms egto --algorithms foa \
  --runs 30 \
  --iterations 500 \
  --population 30 \
  --parallel \
  --seed 42 \
  --output-dir $OUTPUT_DIR
```

#### Ejemplo: FGO, HOA, APO, SMA (Grupo 3)

```bash
OUTPUT_DIR="results/vrp_grupo3_$(date +%Y%m%d_%H%M)"
mkdir -p $OUTPUT_DIR

PYTHONPATH=. python scripts/analyze_results.py \
  --run-benchmark \
  --instances P-n16-k8 E-n22-k4 M-n151-k12 \
  --algorithms fgo --algorithms hoa --algorithms apo --algorithms sma \
  --runs 30 \
  --iterations 500 \
  --population 30 \
  --parallel \
  --seed 42 \
  --output-dir $OUTPUT_DIR
```

### 4. Ejecuciones con Diversidad de Parámetros

Para analizar el impacto de diferentes configuraciones de parámetros:

#### Variación de Población

```bash
# Población pequeña (20)
PYTHONPATH=. python scripts/analyze_results.py \
  --run-benchmark \
  --instances P-n16-k8 E-n22-k4 \
  --algorithms hho --algorithms woa --algorithms gto \
  --runs 10 \
  --iterations 500 \
  --population 20 \
  --parallel \
  --seed 42 \
  --output-dir results/vrp_pop20

# Población grande (50)
PYTHONPATH=. python scripts/analyze_results.py \
  --run-benchmark \
  --instances P-n16-k8 E-n22-k4 \
  --algorithms hho --algorithms woa --algorithms gto \
  --runs 10 \
  --iterations 500 \
  --population 50 \
  --parallel \
  --seed 42 \
  --output-dir results/vrp_pop50
```

#### Variación de Iteraciones

```bash
# Iteraciones reducidas (100)
PYTHONPATH=. python scripts/analyze_results.py \
  --run-benchmark \
  --instances P-n16-k8 E-n22-k4 \
  --algorithms hho --algorithms woa --algorithms gto \
  --runs 10 \
  --iterations 100 \
  --population 30 \
  --parallel \
  --seed 42 \
  --output-dir results/vrp_iter100

# Iteraciones extendidas (1000)
PYTHONPATH=. python scripts/analyze_results.py \
  --run-benchmark \
  --instances P-n16-k8 E-n22-k4 \
  --algorithms hho --algorithms woa --algorithms gto \
  --runs 10 \
  --iterations 1000 \
  --population 30 \
  --parallel \
  --seed 42 \
  --output-dir results/vrp_iter1000
```

## Análisis de Resultados

Después de ejecutar los benchmarks, se recomienda realizar un análisis consolidado de los resultados:

1. **Consolidación de datos**: Recopilar todos los archivos `benchmark_results.json` de los diferentes directorios de resultados.

2. **Generación de gráficas comparativas**: Utilizar los scripts disponibles para generar visualizaciones:
   - Gráficas de caja para comparar distribuciones
   - Gráficas de convergencia
   - Mapas de calor para relaciones estadísticas

3. **Análisis estadístico**: Aplicar pruebas no paramétricas (Friedman, Wilcoxon) para determinar diferencias significativas entre algoritmos.

4. **Documentación de hallazgos**: Crear un informe detallado que incluya:
   - Tablas comparativas de rendimiento
   - Gráficas generadas
   - Conclusiones sobre fortalezas y debilidades de cada algoritmo
   - Recomendaciones para diferentes escenarios de aplicación

## Consideraciones Importantes

1. **Tiempo de ejecución**: El benchmark completo con todos los algoritmos, instancias y 30 ejecuciones puede tomar varias horas. Planifique en consecuencia.

2. **Recursos computacionales**: La paralelización ayuda a reducir el tiempo total, pero aumenta el uso de CPU y memoria. Monitorice los recursos durante la ejecución.

3. **Almacenamiento**: Los resultados generados pueden ocupar espacio considerable, especialmente las gráficas y archivos JSON. Asegúrese de tener suficiente espacio disponible.

4. **Reproducibilidad**: El uso de una semilla fija (42) garantiza la reproducibilidad de los resultados. Para análisis de robustez, considere ejecutar con diferentes semillas.

5. **Escalabilidad**: La instancia M-n151-k12 es significativamente más grande y puede requerir tiempos de ejecución mucho mayores. Considere ejecutarla por separado si es necesario.

---

Al seguir estas instrucciones, podrá obtener un conjunto diverso y estadísticamente significativo de datos para un análisis riguroso del rendimiento de los algoritmos metaheurísticos en problemas VRP.

*Última actualización: 8 de mayo de 2025*