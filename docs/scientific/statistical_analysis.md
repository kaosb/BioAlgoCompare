# Guía de Análisis Estadístico

Este documento proporciona una explicación detallada de las metodologías estadísticas implementadas en BioAlgoCompare para el análisis riguroso de algoritmos metaheurísticos. Está dirigido a investigadores y académicos que buscan comprender e interpretar correctamente los resultados estadísticos generados por la plataforma.

## Contenido

1. [Fundamentos Estadísticos](#fundamentos-estadísticos)
2. [Pruebas de Normalidad](#pruebas-de-normalidad)
3. [Comparación de Múltiples Algoritmos](#comparación-de-múltiples-algoritmos)
4. [Pruebas Post-hoc](#pruebas-post-hoc)
5. [Tamaño del Efecto](#tamaño-del-efecto)
6. [Intervalos de Confianza](#intervalos-de-confianza)
7. [Visualización Estadística](#visualización-estadística)
8. [Interpretación de Resultados](#interpretación-de-resultados)

## Fundamentos Estadísticos

Los algoritmos metaheurísticos son inherentemente estocásticos, lo que hace necesario un análisis estadístico riguroso para obtener conclusiones válidas sobre su rendimiento.

### Principios Clave

1. **Muestreo adecuado**: Se requieren múltiples ejecuciones independientes para capturar la variabilidad
2. **Selección de pruebas**: Las características de los datos determinan las pruebas apropiadas
3. **Control de errores**: Ajustes para comparaciones múltiples evitan falsas conclusiones
4. **Magnitud práctica**: El tamaño del efecto complementa la significancia estadística

### Implementación en BioAlgoCompare

El sistema `utils/statistical_analysis.py` implementa automáticamente:

```python
# Ejemplo (pseudocódigo)
def analyze_results(benchmark_data):
    # 1. Prueba de normalidad
    is_normal = test_normality(benchmark_data)
    
    # 2. Selección de prueba apropiada
    if is_normal:
        p_value = parametric_test(benchmark_data)
    else:
        p_value = non_parametric_test(benchmark_data)
    
    # 3. Corrección para comparaciones múltiples
    adjusted_p = correction_method(p_value)
    
    # 4. Cálculo de tamaño del efecto
    effect_size = calculate_effect_size(benchmark_data)
    
    return StatisticalResults(p_value, adjusted_p, effect_size)
```

## Pruebas de Normalidad

Estas pruebas determinan si los datos siguen una distribución normal, lo que influye en la selección de pruebas paramétricas o no paramétricas.

### Prueba de Shapiro-Wilk

Implementada automáticamente en BioAlgoCompare para cada conjunto de resultados:

```python
from scipy import stats

def test_normality(data):
    shapiro_test = stats.shapiro(data)
    return shapiro_test.pvalue > 0.05  # Ho: datos siguen distribución normal
```

### Interpretación

- **p > 0.05**: No se puede rechazar la hipótesis de normalidad
- **p ≤ 0.05**: Se rechaza la normalidad, use pruebas no paramétricas

### Visualización QQ-Plot

Complemento visual a las pruebas numéricas:

```python
import statsmodels.api as sm
import matplotlib.pyplot as plt

def create_qq_plot(data, algorithm_name):
    fig = sm.qqplot(data, line='45')
    plt.title(f'QQ-Plot for {algorithm_name}')
    return fig
```

## Comparación de Múltiples Algoritmos

Cuando se comparan múltiples algoritmos simultáneamente, BioAlgoCompare aplica pruebas de comparación global.

### Test de Friedman (No Paramétrico)

Usado cuando los datos no siguen distribución normal:

```python
from scipy import stats

def friedman_test(benchmark_data):
    # Reorganizar datos por algoritmo e instancia
    data_matrix = reshape_for_friedman(benchmark_data)
    
    # Aplicar prueba de Friedman
    friedman_result = stats.friedmanchisquare(*data_matrix)
    
    return {
        'statistic': friedman_result.statistic,
        'p_value': friedman_result.pvalue,
        'reject_h0': friedman_result.pvalue <= 0.05
    }
```

### ANOVA (Paramétrico)

Utilizado cuando los datos siguen distribución normal:

```python
from scipy import stats

def anova_test(benchmark_data):
    # Agrupar datos por algoritmo
    groups = [data for alg, data in benchmark_data.items()]
    
    # Aplicar ANOVA
    anova_result = stats.f_oneway(*groups)
    
    return {
        'statistic': anova_result.statistic,
        'p_value': anova_result.pvalue,
        'reject_h0': anova_result.pvalue <= 0.05
    }
```

### Interpretación

- **Hipótesis nula (H₀)**: No hay diferencias significativas entre los algoritmos
- **Hipótesis alternativa (H₁)**: Al menos un algoritmo es significativamente diferente
- **Decisión**: 
  - Si p ≤ 0.05: Rechazar H₀, existen diferencias significativas
  - Si p > 0.05: No rechazar H₀, no hay evidencia de diferencias significativas

## Pruebas Post-hoc

Cuando la prueba global indica diferencias significativas, las pruebas post-hoc identifican específicamente qué algoritmos difieren.

### Test de Nemenyi

Aplicado después del test de Friedman:

```python
from scikit_posthocs import posthoc_nemenyi

def nemenyi_test(benchmark_data):
    # Reorganizar datos
    data_matrix = reshape_for_posthoc(benchmark_data)
    
    # Aplicar prueba de Nemenyi
    nemenyi_result = posthoc_nemenyi(data_matrix)
    
    return nemenyi_result  # Matriz de p-valores para pares de algoritmos
```

### Test de Wilcoxon con Corrección de Bonferroni

Para comparaciones por pares controlando la tasa de error:

```python
from scipy import stats
import numpy as np

def wilcoxon_tests_with_bonferroni(benchmark_data):
    algorithms = list(benchmark_data.keys())
    n_comparisons = len(algorithms) * (len(algorithms) - 1) // 2
    
    results = {}
    
    for i in range(len(algorithms)):
        for j in range(i+1, len(algorithms)):
            alg1, alg2 = algorithms[i], algorithms[j]
            
            # Test de Wilcoxon
            w_stat, p_value = stats.wilcoxon(
                benchmark_data[alg1],
                benchmark_data[alg2]
            )
            
            # Corrección de Bonferroni
            adjusted_p = min(p_value * n_comparisons, 1.0)
            
            results[(alg1, alg2)] = {
                'w_statistic': w_stat,
                'p_value': p_value,
                'adjusted_p': adjusted_p,
                'significant': adjusted_p <= 0.05
            }
    
    return results
```

### Interpretación

- **Matriz de p-valores**: Cada celda (i,j) representa la probabilidad de que los algoritmos i y j tengan distribuciones idénticas
- **Significancia**: Si p-valor ajustado ≤ 0.05, existe diferencia significativa
- **Ranking**: Permite ordenar algoritmos por desempeño relativo

## Tamaño del Efecto

Las medidas de tamaño del efecto cuantifican la magnitud práctica de las diferencias, complementando la significancia estadística.

### A12 de Vargha-Delaney

Mide la probabilidad de que un algoritmo supere a otro:

```python
def a12_effect_size(data1, data2):
    """
    Calcula el estadístico A12 de Vargha-Delaney.
    A12 = P(X > Y) + 0.5 * P(X = Y)
    """
    m, n = len(data1), len(data2)
    r = stats.rankdata(np.concatenate([data1, data2]))
    r1 = sum(r[:m])
    
    # A12 = (r1/m - (m+1)/2) / n
    a12 = (r1/m - (m+1)/2) / n + 0.5
    
    return a12
```

### Delta de Cliff

Otra medida no paramétrica del tamaño del efecto:

```python
def cliffs_delta(data1, data2):
    """
    Calcula el Delta de Cliff.
    d = (#{X > Y} - #{X < Y}) / (m*n)
    """
    m, n = len(data1), len(data2)
    
    larger = sum(x > y for x in data1 for y in data2)
    smaller = sum(x < y for x in data1 for y in data2)
    
    return (larger - smaller) / (m * n)
```

### Interpretación de A12

- **A12 = 0.5**: Distribuciones idénticas
- **A12 > 0.71**: Diferencia grande (algoritmo 1 es superior)
- **0.64 < A12 < 0.71**: Diferencia mediana
- **0.56 < A12 < 0.64**: Diferencia pequeña
- **Análogamente para A12 < 0.5**: Algoritmo 2 es superior

## Intervalos de Confianza

Los intervalos de confianza proporcionan información sobre la precisión de las estimaciones.

### Cálculo Básico

```python
def confidence_interval(data, confidence=0.95):
    """
    Calcula intervalo de confianza para la media.
    """
    n = len(data)
    mean = np.mean(data)
    sem = stats.sem(data)  # Error estándar de la media
    h = sem * stats.t.ppf((1 + confidence) / 2, n - 1)
    
    return mean - h, mean + h
```

### Bootstrap para Distribuciones No Normales

```python
def bootstrap_confidence_interval(data, confidence=0.95, n_resamples=10000):
    """
    Calcula intervalo de confianza usando bootstrap.
    """
    n = len(data)
    resamples = np.random.choice(data, (n_resamples, n), replace=True)
    means = np.mean(resamples, axis=1)
    
    lower = np.percentile(means, (1 - confidence) * 100 / 2)
    upper = np.percentile(means, 100 - (1 - confidence) * 100 / 2)
    
    return lower, upper
```

### Interpretación

- **Intervalo del 95%**: 95% de probabilidad de que el verdadero valor esté en este rango
- **Anchura del intervalo**: Indica precisión de la estimación
- **Solapamiento de intervalos**: Sugiere ausencia de diferencia estadística

## Visualización Estadística

BioAlgoCompare implementa visualizaciones estadísticas avanzadas para interpretar resultados.

### Boxplots con Notches

```python
def create_boxplot_with_notches(benchmark_data):
    fig, ax = plt.subplots(figsize=(12, 6))
    
    data = [values for alg, values in benchmark_data.items()]
    labels = list(benchmark_data.keys())
    
    box = ax.boxplot(
        data, labels=labels, notch=True, patch_artist=True,
        showmeans=True, meanprops={'marker':'o', 'markerfacecolor':'white'}
    )
    
    ax.set_ylabel('Fitness (menor es mejor)')
    ax.set_title('Comparación de algoritmos con intervalos de confianza (notches)')
    
    return fig
```

### Diagramas de Diferencia Crítica

```python
def create_critical_difference_diagram(ranks, p_values, names):
    # Implementación usando Orange3 o código personalizado
    # para visualizar resultados del test de Nemenyi
    ...
```

### Curvas de Convergencia con Intervalos

```python
def plot_convergence_with_intervals(convergence_data):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for algorithm, curves in convergence_data.items():
        # Calcular media y desviación estándar por iteración
        mean_curve = np.mean(curves, axis=0)
        std_curve = np.std(curves, axis=0)
        
        # Plotear media
        line = ax.plot(mean_curve, label=algorithm)
        color = line[0].get_color()
        
        # Añadir intervalo de confianza
        ax.fill_between(
            range(len(mean_curve)),
            mean_curve - 1.96 * std_curve / np.sqrt(len(curves)),
            mean_curve + 1.96 * std_curve / np.sqrt(len(curves)),
            alpha=0.2, color=color
        )
    
    ax.set_xlabel('Iteraciones')
    ax.set_ylabel('Fitness (menor es mejor)')
    ax.legend()
    
    return fig
```

## Interpretación de Resultados

### Guía para Conclusiones Científicas

1. **Verificar normalidad**:
   - Shapiro-Wilk o QQ-plots
   - Determina qué pruebas son válidas

2. **Comprobar significancia global**:
   - Test de Friedman o ANOVA
   - ¿Hay diferencias entre algoritmos?

3. **Identificar diferencias específicas**:
   - Pruebas post-hoc con corrección
   - ¿Qué algoritmos difieren entre sí?

4. **Evaluar magnitud práctica**:
   - Tamaño del efecto (A12, Delta de Cliff)
   - ¿Las diferencias son relevantes en la práctica?

5. **Considerar rangos de incertidumbre**:
   - Intervalos de confianza
   - ¿Cuán precisas son las estimaciones?

### Ejemplo de Interpretación Completa

```
Resultado: El test de Friedman indica diferencias significativas entre los algoritmos (p < 0.001). 
Las pruebas post-hoc muestran que EGTO supera significativamente a FOA y WOA (p_adj < 0.01), 
con un tamaño de efecto grande (A12 = 0.78 y 0.82, respectivamente). El algoritmo HOA no 
presenta diferencias significativas con EGTO (p_adj = 0.14), pero sí supera a WOA 
(p_adj < 0.05, A12 = 0.67).

Conclusión: EGTO y HOA constituyen el grupo de algoritmos con mejor desempeño, con EGTO 
mostrando una ligera ventaja no estadísticamente significativa. Ambos superan claramente 
a FOA y WOA con diferencias tanto estadísticamente significativas como de magnitud 
práctica relevante.
```

## Recursos Adicionales

- [Guía de Reproducibilidad](reproducibility.md)
- [Guía de Benchmarking](../guides/benchmarking.md)
- [Visualización Científica](scientific_visualization.md)