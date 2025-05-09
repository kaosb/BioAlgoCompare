# Guía de Benchmarking

Esta guía proporciona instrucciones detalladas para realizar benchmarks rigurosos y análisis estadísticos de algoritmos metaheurísticos con BioAlgoCompare. Enfocada en metodología científica, reproducibilidad y explicabilidad de los resultados.

## Contenido

1. [Principios de Benchmarking Científico](#principios-de-benchmarking-científico)
2. [Tipos de Benchmarks](#tipos-de-benchmarks)
3. [Configuración de Benchmarks](#configuración-de-benchmarks)
4. [Análisis Estadístico](#análisis-estadístico)
5. [Visualización de Resultados](#visualización-de-resultados)
6. [Ciclo Completo de Benchmarking](#ciclo-completo-de-benchmarking)
7. [Interpretación de Resultados](#interpretación-de-resultados)
8. [Publicación de Resultados](#publicación-de-resultados)

## Principios de Benchmarking Científico

El benchmarking de algoritmos metaheurísticos en BioAlgoCompare sigue estos principios:

### 1. Reproducibilidad

- **Control de semilla**: Todas las ejecuciones usan semillas explícitas para permitir reproducción exacta
- **Documentación completa**: Todos los parámetros son registrados automáticamente
- **Versiones de software**: Se recomienda documentar las versiones exactas de todas las dependencias

### 2. Rigor Estadístico

- **Tamaño de muestra adecuado**: Mínimo 30 ejecuciones para pruebas paramétricas
- **Tests apropiados**: Tests no paramétricos para comparaciones entre algoritmos
- **Corrección para comparaciones múltiples**: Bonferroni, Holm, etc.
- **Intervalos de confianza**: Reportados al 95% por defecto

### 3. Equidad en Comparaciones

- **Recursos computacionales equivalentes**: Mismo número de evaluaciones de función objetivo
- **Inicialización consistente**: Mismos métodos de inicialización para todos los algoritmos
- **Criterios de parada unificados**: Mismo número de iteraciones o tiempo de ejecución

### 4. Transparencia

- **Código abierto**: Todo el código del benchmark es inspeccionable
- **Datos disponibles**: Resultados brutos disponibles para verificación
- **Metodología explícita**: Documentación clara del proceso experimental

## Tipos de Benchmarks

BioAlgoCompare admite varios tipos de benchmarks:

### 1. Benchmark Comparativo Estándar

Compara varios algoritmos en una o más instancias, con múltiples ejecuciones independientes:

```bash
python scripts/analyze.py benchmark --run-benchmark \
    --algorithms egto,foa,hoa,woa \
    --instances E-n22-k4,P-n16-k8 \
    --runs 30 --seed 42 --parallel
```

### 2. Benchmark Masivo

Ejecuta un gran número de repeticiones (1000+) para análisis estadístico detallado:

```bash
python scripts/analyze.py massive \
    --algorithm egto,foa,hoa \
    --instances E-n22-k4 \
    --runs 1000 --parallel --resume
```

### 3. Benchmark de Parámetros

Compara un mismo algoritmo con diferentes configuraciones de parámetros:

```bash
# Usando benchmark con diferentes poblaciones
python scripts/analyze.py benchmark --run-benchmark \
    --algorithms egto \
    --instances E-n22-k4 \
    --population 20,50,100 \
    --runs 30 --seed 42
```

### 4. Benchmark de Iteraciones

Evalúa el impacto del número de iteraciones en la calidad de las soluciones:

```bash
# Ejecución manual con diferentes iteraciones
python scripts/run.py --algorithm egto --instance E-n22-k4 --iterations 100 --runs 10 --seed 42
python scripts/run.py --algorithm egto --instance E-n22-k4 --iterations 500 --runs 10 --seed 42
python scripts/run.py --algorithm egto --instance E-n22-k4 --iterations 1000 --runs 10 --seed 42
```

## Configuración de Benchmarks

### Parámetros Clave

| Parámetro | Uso Científico Recomendado | Efecto en Benchmark |
|-----------|----------------------------|---------------------|
| `--runs`  | ≥30 para significancia estadística | Determina la robustez de los resultados |
| `--seed`  | Valor fijo documentado | Garantiza reproducibilidad |
| `--population` | Consistente entre comparaciones | Afecta recursos computacionales |
| `--iterations` | Suficiente para convergencia | Afecta calidad de resultados |
| `--parallel` | Recomendado para ejecuciones largas | Acelera el benchmark |
| `--optimize` | Opcional, pero debe aplicarse consistentemente | Mejora soluciones con búsqueda local |

### Reproducibilidad Total

Para garantizar reproducibilidad completa del benchmark:

```bash
# 1. Documentar versiones de software
pip freeze > benchmark_environment.txt

# 2. Establecer semilla explícita
python scripts/analyze.py benchmark --run-benchmark \
    --algorithms egto,foa,hoa \
    --instances E-n22-k4 \
    --runs 30 --seed 42 \
    --output-dir results/benchmark_reproducible_1

# 3. Guardar comandos exactos
echo "python scripts/analyze.py benchmark --run-benchmark --algorithms egto,foa,hoa --instances E-n22-k4 --runs 30 --seed 42 --output-dir results/benchmark_reproducible_1" > benchmark_command.txt
```

## Análisis Estadístico

BioAlgoCompare aplica automáticamente análisis estadístico riguroso a los resultados:

### Tests Aplicados

1. **Pruebas de Normalidad**:
   - Shapiro-Wilk para determinar si los datos siguen distribución normal
   - Determina si se usan tests paramétricos o no paramétricos

2. **Comparación de Múltiples Algoritmos**:
   - Test de Friedman (no paramétrico) para detectar diferencias significativas
   - Test de Kruskal-Wallis como alternativa
   - ANOVA para datos normalmente distribuidos

3. **Comparaciones Por Pares**:
   - Test post-hoc de Nemenyi para rankings
   - Test de Wilcoxon con corrección para múltiples comparaciones
   - Corrección de Bonferroni o Holm para controlar la tasa de error

4. **Medidas de Tamaño del Efecto**:
   - A12 de Vargha-Delaney para interpretación práctica
   - Delta de Cliff para estimar la magnitud de las diferencias

### Personalización del Análisis

```bash
# Análisis con nivel de significancia personalizado
python scripts/analyze.py analyze-csv results/benchmark_results.csv \
    --significance-level 0.01 \
    --correction-method holm
```

## Visualización de Resultados

### Tipos de Visualizaciones

1. **Boxplots Comparativos**:
   - Comparación directa de distribución de resultados
   - Outliers claramente identificados
   - Intervalos de confianza mostrados

2. **Curvas de Convergencia**:
   - Media con intervalos de confianza sombreados
   - Permiten analizar velocidad de convergencia
   - Identificación de estancamiento

3. **Diagramas de Diferencia Crítica**:
   - Representación visual de tests post-hoc
   - Grupos de algoritmos sin diferencias significativas
   - Ranking relativo de algoritmos

4. **Soluciones VRP**:
   - Visualización de rutas óptimas encontradas
   - Comparación con soluciones conocidas

### Visualizaciones para Publicación

Para generar visualizaciones de calidad para publicación:

```bash
python scripts/analyze.py analyze-csv results/benchmark_final.csv \
    --publication-ready \
    --format pdf \
    --dpi 600 \
    --output-dir results/publication_figures
```

## Ciclo Completo de Benchmarking

Un ciclo completo de benchmarking científico incluye estos pasos:

### 1. Planificación

- Seleccionar algoritmos e instancias relevantes
- Determinar métricas de rendimiento
- Establecer tamaño de muestra adecuado
- Definir hipótesis a comprobar

### 2. Ejecución Exploratoria

```bash
# Ejecución exploratoria para estimar parámetros
python scripts/run.py --algorithm all --instance P-n16-k8 --runs 5
```

### 3. Configuración de Parámetros

```bash
# Explorar configuraciones de parámetros
python scripts/analyze.py benchmark --run-benchmark \
    --algorithms egto \
    --instances P-n16-k8 \
    --population 20,30,50,100 \
    --runs 10
```

### 4. Benchmark Principal

```bash
# Benchmark definitivo con parámetros optimizados
python scripts/analyze.py benchmark --run-benchmark \
    --algorithms egto,foa,hoa,woa,hho \
    --instances E-n22-k4,P-n16-k8,A-n32-k5 \
    --runs 30 --seed 42 --parallel
```

### 5. Validación Masiva

```bash
# Validación masiva de los mejores algoritmos
python scripts/analyze.py massive \
    --algorithm egto,foa,hoa \
    --instances E-n22-k4 \
    --runs 1000 --parallel
```

### 6. Análisis y Visualización

```bash
# Análisis final con visualizaciones para publicación
python scripts/analyze.py analyze-csv \
    results/benchmark_final.csv \
    --publication-ready
```

## Interpretación de Resultados

### Métricas Principales

1. **Calidad de la Solución**:
   - Mejor fitness encontrado (media, mediana, mejor)
   - Gap respecto al óptimo conocido
   - Desviación estándar y coeficiente de variación

2. **Eficiencia**:
   - Tiempo de ejecución
   - Número de evaluaciones de función objetivo
   - Velocidad de convergencia

3. **Robustez**:
   - Consistencia entre ejecuciones
   - Sensibilidad a la inicialización
   - Comportamiento en diferentes instancias

### Interpretación Estadística

- **p-valor < α**: Indica diferencia estadísticamente significativa
- **Ranking**: Orden relativo de desempeño entre algoritmos
- **Tamaño del efecto**: Magnitud práctica de las diferencias
  - A12 > 0.71: Diferencia grande
  - 0.64 < A12 < 0.71: Diferencia mediana
  - 0.56 < A12 < 0.64: Diferencia pequeña
  - 0.5 < A12 < 0.56: Diferencia insignificante

## Publicación de Resultados

Para preparar resultados de benchmark para publicación científica:

### 1. Tablas de Resultados

```bash
# Generar tablas LaTeX para publicación
python scripts/analyze.py analyze-csv results/benchmark_final.csv \
    --export-tables latex \
    --output-dir results/publication
```

### 2. Figuras

```bash
# Generar figuras vectoriales de alta calidad
python scripts/analyze.py analyze-csv results/benchmark_final.csv \
    --publication-ready \
    --format pdf \
    --output-dir results/publication
```

### 3. Protocolo Experimental

En publicaciones científicas, documente siempre:

1. **Hardware utilizado**: CPU, RAM, sistema operativo
2. **Software**: Versión de Python, bibliotecas, BioAlgoCompare
3. **Parámetros completos**: Población, iteraciones, semilla, etc.
4. **Metodología estadística**: Tests aplicados, nivel de significancia
5. **Código fuente**: Repositorio o enlace para reproducibilidad

### 4. Datos para Reproducibilidad

```bash
# Comprimir todos los resultados y metadatos para compartir
tar -czf benchmark_complete_results.tar.gz \
    results/benchmark_final.csv \
    results/benchmark_final_summary.csv \
    benchmark_environment.txt \
    benchmark_command.txt
```

## Recursos Adicionales

- [Guía de Uso Completa](usage.md)
- [Referencia Técnica de Scripts](../technical/scripts_reference.md)
- [Documentación de Algoritmos](../algorithms/overview.md)
- [Análisis Comparativo](../analysis/comparison.md)