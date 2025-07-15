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

### Test de Friedman Alineado (No Paramétrico)

Usado cuando los datos no siguen distribución normal, especialmente efectivo para comparaciones de algoritmos:

```python
from scipy import stats
import numpy as np
import pandas as pd

def aligned_friedman_test(benchmark_data):
    # Crear dataframe con resultados
    df = pd.DataFrame(benchmark_data)

    # Calcular el rendimiento promedio global
    global_mean = df.values.mean()

    # Alinear los datos restando la media global
    aligned_data = df.values - global_mean

    # Convertir a rangos (ranks)
    ranks = pd.DataFrame(
        stats.rankdata(aligned_data, axis=0),
        columns=df.columns
    )

    # Calcular rangos medios por algoritmo
    mean_ranks = ranks.mean(axis=0)

    # Aplicar prueba de Friedman sobre los rangos
    n, k = df.shape  # n: número de instancias, k: número de algoritmos
    chi2 = (12 * n) / (k * (k + 1)) * ((mean_ranks**2).sum() - k * ((k + 1)**2) / 4)
    df_chi = k - 1
    p_value = 1 - stats.chi2.cdf(chi2, df_chi)

    return {
        'statistic': chi2,
        'p_value': p_value,
        'reject_h0': p_value <= 0.05,
        'mean_ranks': mean_ranks.to_dict()
    }
```

Esta implementación avanzada usa el test de Friedman alineado, que es más potente que el test de Friedman clásico para detectar diferencias entre algoritmos en múltiples instancias de problemas.

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

### Test de Nemenyi Post-hoc

Aplicado después del test de Friedman para identificar diferencias específicas entre pares de algoritmos:

```python
import numpy as np
import pandas as pd
import scikit_posthocs as sp

def nemenyi_posthoc_test(ranks_df, algorithm_names=None):
    """
    Realiza el test post-hoc de Nemenyi para comparaciones múltiples.

    Parameters:
    -----------
    ranks_df : pandas.DataFrame
        DataFrame con los rangos (ranks) de los algoritmos
    algorithm_names : list, optional
        Nombres de los algoritmos a analizar

    Returns:
    --------
    dict
        Resultados del test de Nemenyi incluyendo:
        - 'p_values': matriz de p-valores para cada par de algoritmos
        - 'cd': valor de diferencia crítica
        - 'rankings': ranking promedio de cada algoritmo
    """
    if algorithm_names is None:
        algorithm_names = ranks_df.columns.tolist()

    # Asegurar que solo utilizamos las columnas de los algoritmos especificados
    ranks = ranks_df[algorithm_names]

    # Calcular matriz de p-valores con el test de Nemenyi
    p_values = sp.posthoc_nemenyi_friedman(ranks.values)

    # Convertir a DataFrame con nombres de algoritmos
    p_values_df = pd.DataFrame(
        p_values,
        index=algorithm_names,
        columns=algorithm_names
    )

    # Calcular diferencia crítica (CD)
    n, k = ranks.shape  # n: número de instancias, k: número de algoritmos
    q_alpha = 2.0  # Valor crítico para alfa=0.05 y k algoritmos (aproximado)
    cd = q_alpha * np.sqrt((k * (k + 1)) / (6 * n))

    # Calcular ranking promedio para cada algoritmo
    mean_ranks = ranks.mean(axis=0)

    return {
        'p_values': p_values_df.to_dict(),
        'cd': cd,
        'rankings': mean_ranks.to_dict()
    }
```

### Diagrama de Diferencia Crítica (CD)

Los diagramas CD son una representación visual de los resultados del test de Nemenyi, mostrando agrupaciones de algoritmos sin diferencias significativas:

```python
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx

def create_cd_diagram(rankings, cd_value, algorithm_names=None, title="Diagrama de Diferencia Crítica"):
    """
    Crea un diagrama de diferencia crítica a partir de los rankings de algoritmos.

    Parameters:
    -----------
    rankings : dict
        Diccionario con los rankings medios de cada algoritmo
    cd_value : float
        Valor de diferencia crítica
    algorithm_names : list, optional
        Nombres de los algoritmos (si no se proporcionan, se toman de rankings)
    title : str
        Título del diagrama

    Returns:
    --------
    matplotlib.figure.Figure
        Figura con el diagrama CD
    """
    if algorithm_names is None:
        algorithm_names = list(rankings.keys())

    # Ordenar algoritmos por ranking (menor es mejor)
    sorted_algos = sorted(algorithm_names, key=lambda x: rankings[x])

    # Crear gráfico
    fig, ax = plt.subplots(figsize=(12, 5))

    # Dibujar línea horizontal principal
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)

    # Posición de cada algoritmo en la línea
    positions = {algo: i for i, algo in enumerate(sorted_algos)}

    # Dibujar posiciones de algoritmos
    for algo, pos in positions.items():
        ax.plot(pos, 0, 'o', color='blue', markersize=8)
        ax.text(pos, -0.1, algo, ha='center', va='top', rotation=45, fontsize=9)

    # Crear grafo para conexiones
    G = nx.Graph()

    # Añadir algoritmos como nodos
    for algo in sorted_algos:
        G.add_node(algo)

    # Conexiones entre algoritmos que no son significativamente diferentes
    for i, algo1 in enumerate(sorted_algos):
        for algo2 in sorted_algos[i+1:]:
            if abs(rankings[algo1] - rankings[algo2]) <= cd_value:
                G.add_edge(algo1, algo2)

    # Identificar grupos conectados (cliques)
    cliques = list(nx.find_cliques(G))

    # Dibujar líneas que conectan algoritmos sin diferencias significativas
    max_y = 0.3
    y_positions = {}

    # Para cada clique, dibujar una línea que conecte todos sus miembros
    for i, clique in enumerate(sorted(cliques, key=len, reverse=True)):
        if len(clique) < 2:
            continue

        # Ordenar clique por posición en línea horizontal
        clique = sorted(clique, key=lambda x: positions[x])

        # Asignar altura para esta línea
        y_pos = (i + 1) * max_y / (len(cliques) + 1)

        # Guardar posición y para cada algoritmo
        for algo in clique:
            y_positions[algo] = max(y_positions.get(algo, 0), y_pos)

        # Dibujar línea para el clique
        x_values = [positions[algo] for algo in clique]
        y_values = [y_pos] * len(clique)
        ax.plot(x_values, y_values, '-', color='black', alpha=0.7, linewidth=1.5)

    # Conectar algoritmos a sus líneas
    for algo, pos in positions.items():
        if algo in y_positions:
            ax.plot([pos, pos], [0, y_positions[algo]], '--', color='black', alpha=0.3)

    # Añadir CD value al gráfico
    ax.text(len(positions) - 1, max_y * 1.1, f"CD = {cd_value:.2f}",
            ha='right', va='bottom', fontsize=10, fontstyle='italic')

    # Ajustar límites del eje y
    ax.set_ylim(-0.5, max_y * 1.3)
    ax.set_xlim(-0.5, len(positions) - 0.5)

    # Ocultar ejes
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    # Título
    ax.set_title(title)

    # Añadir leyenda
    ax.text(0, -0.3, "menor es mejor →", ha='left', va='top',
            fontstyle='italic', fontsize=9, alpha=0.7)

    plt.tight_layout()
    return fig
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

El estadístico A12 de Vargha-Delaney es una medida de tamaño del efecto no paramétrica que cuantifica la probabilidad de que un algoritmo supere a otro:

```python
import numpy as np
from scipy import stats

def vargha_delaney_a12(data1, data2):
    """
    Calcula el estadístico A12 de Vargha-Delaney para cada par de algoritmos.

    Parameters:
    -----------
    data1, data2 : array-like
        Vectores de resultados para dos algoritmos

    Returns:
    --------
    float
        Estadístico A12:
        - A12 = 0.5: No hay dominancia
        - A12 > 0.5: data1 tiende a superar a data2
        - A12 < 0.5: data2 tiende a superar a data1
    """
    m, n = len(data1), len(data2)

    # En optimización, frecuentemente "menor es mejor"
    # Para problemas de minimización (como VRP) usar estos dos vectores directamente
    # Para problemas de maximización, invertir el signo: -data1, -data2

    # Concatenar y calcular rangos
    ranks = stats.rankdata(np.concatenate([data1, data2]))

    # Suma de rangos de data1
    r1 = sum(ranks[:m])

    # Calcular A12 según la fórmula de Vargha-Delaney
    a12 = (r1/m - (m+1)/2) / n + 0.5

    return a12

def interpret_a12(a12):
    """
    Interpreta el tamaño del efecto A12 según las guías de Vargha-Delaney.

    Parameters:
    -----------
    a12 : float
        Valor del estadístico A12

    Returns:
    --------
    str
        Interpretación del tamaño del efecto
    """
    if a12 == 0.5:
        return "No hay efecto"

    # Para a12 > 0.5 (algoritmo 1 supera a algoritmo 2)
    if a12 > 0.5:
        if a12 < 0.56:
            return "Efecto despreciable"
        elif a12 < 0.64:
            return "Efecto pequeño"
        elif a12 < 0.71:
            return "Efecto mediano"
        else:
            return "Efecto grande"

    # Para a12 < 0.5 (algoritmo 2 supera a algoritmo 1)
    else:
        a12_complemento = 1 - a12  # transformar para usar las mismas reglas
        if a12_complemento < 0.56:
            return "Efecto despreciable (inverso)"
        elif a12_complemento < 0.64:
            return "Efecto pequeño (inverso)"
        elif a12_complemento < 0.71:
            return "Efecto mediano (inverso)"
        else:
            return "Efecto grande (inverso)"
```

### Matriz de Tamaños de Efecto

Para facilitar la comparación entre todos los pares de algoritmos, se implementa la generación de una matriz completa de tamaños de efecto:

```python
import pandas as pd
import numpy as np

def generate_effect_size_matrix(data_dict):
    """
    Genera una matriz con los tamaños de efecto A12 para todos los pares de algoritmos.

    Parameters:
    -----------
    data_dict : dict
        Diccionario donde las claves son nombres de algoritmos y los valores son arrays con resultados

    Returns:
    --------
    pandas.DataFrame
        Matriz de tamaños de efecto
    """
    alg_names = list(data_dict.keys())
    n_algs = len(alg_names)

    # Inicializar matriz de tamaños de efecto
    a12_matrix = np.zeros((n_algs, n_algs))

    # Calcular A12 para cada par de algoritmos
    for i in range(n_algs):
        for j in range(n_algs):
            if i != j:
                a12_matrix[i, j] = vargha_delaney_a12(
                    data_dict[alg_names[i]],
                    data_dict[alg_names[j]]
                )
            else:
                a12_matrix[i, j] = 0.5  # Mismo algoritmo (sin efecto)

    # Convertir a DataFrame
    a12_df = pd.DataFrame(
        a12_matrix,
        index=alg_names,
        columns=alg_names
    )

    return a12_df
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

### Función Integrada de Análisis Estadístico

Para facilitar el uso de todas estas técnicas estadísticas avanzadas, BioAlgoCompare implementa una función integrada que realiza el análisis completo y genera informes:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
from pathlib import Path
import os

def run_all(df, output_dir=None):
    """
    Ejecuta análisis estadístico completo sobre un DataFrame de resultados de benchmark.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame con resultados de benchmark. Debe contener columnas 'Algorithm' e 'Instance'
        así como una columna de desempeño ('Best' o 'Best Fitness')
    output_dir : str o Path, optional
        Directorio donde guardar los resultados. Si no se especifica, usa el mismo directorio
        del archivo CSV

    Returns:
    --------
    dict
        Diccionario con los resultados de todos los análisis estadísticos
    """
    logger = logging.getLogger(__name__)

    # Verificar estructura del DataFrame
    required_cols = ['Algorithm', 'Instance']
    if not all(col in df.columns for col in required_cols):
        logger.error(f"El DataFrame debe contener las columnas: {required_cols}")
        return {"error": f"El DataFrame debe contener las columnas: {required_cols}"}

    # Detectar columna de desempeño
    score_col = next(
        (c for c in df.columns if c.lower() in {"best", "best fitness"}),
        None,
    )
    if score_col is None:
        logger.error("No se encontró columna de desempeño ('Best' o 'Best Fitness')")
        return {
            "error": "No se encontró columna de desempeño ('Best' o 'Best Fitness')"
        }

    # Verificar suficientes algoritmos
    algorithms = df['Algorithm'].unique()
    if len(algorithms) < 2:
        logger.error("Se necesitan al menos 2 algoritmos para el análisis")
        return {"error": "Se necesitan al menos 2 algoritmos para el análisis"}

    # Organizar datos para análisis
    pivot_df = df.pivot_table(
        index='Instance',
        columns='Algorithm',
        values=score_col,
        aggfunc='mean'
    )

    # Verificar suficientes instancias
    if len(pivot_df) < 3:
        logger.error("Se necesitan al menos 3 instancias para test de Friedman")
        return {"error": "Se necesitan al menos 3 instancias para test de Friedman"}

    # Ejecutar test de Friedman alineado
    friedman_result = aligned_friedman_test(pivot_df)

    # Si hay diferencias significativas, ejecutar post-hoc
    if friedman_result['reject_h0']:
        # Calcular ranks para el test de Nemenyi
        pivot_ranks = pivot_df.rank(axis=1)  # Ranking por fila (instancia)
        nemenyi_result = nemenyi_posthoc_test(pivot_ranks)

        # Generar matriz de tamaños de efecto A12
        data_by_alg = {}
        for alg in algorithms:
            data_by_alg[alg] = df[df['Algorithm'] == alg][score_col].values

        a12_matrix = generate_effect_size_matrix(data_by_alg)
    else:
        nemenyi_result = {"info": "No se realizó test post-hoc (No se rechazó H0)"}
        a12_matrix = pd.DataFrame()

    # Generar visualizaciones
    results = {
        "friedman_test": friedman_result,
        "post_hoc": nemenyi_result,
        "effect_size": a12_matrix.to_dict() if not a12_matrix.empty else {},
    }

    # Guardar resultados si se especificó directorio
    if output_dir:
        output_dir = Path(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        # Generar diagrama CD
        if friedman_result['reject_h0']:
            fig = create_cd_diagram(
                nemenyi_result['rankings'],
                nemenyi_result['cd'],
                title="Diagrama de Diferencia Crítica (menor es mejor)"
            )
            fig.savefig(output_dir / "cd_diagram.png", dpi=300, bbox_inches='tight')
            plt.close(fig)

            # Generar informe en markdown
            generate_markdown_report(
                results,
                score_col,
                output_path=output_dir / "stats_report.md"
            )

    return results

def generate_markdown_report(results, score_column, output_path):
    """
    Genera un informe en formato Markdown con los resultados del análisis estadístico.

    Parameters:
    -----------
    results : dict
        Resultados del análisis estadístico
    score_column : str
        Nombre de la columna de desempeño
    output_path : Path
        Ruta donde guardar el informe Markdown
    """
    with open(output_path, 'w') as f:
        f.write(f"# Informe de Análisis Estadístico\n\n")

        # Prueba de Friedman
        friedman = results['friedman_test']
        f.write(f"## Prueba de Friedman Alineado\n\n")
        f.write(f"- **Estadístico chi²**: {friedman['statistic']:.4f}\n")
        f.write(f"- **p-valor**: {friedman['p_value']:.6f}\n")
        f.write(f"- **Conclusión**: ")

        if friedman['reject_h0']:
            f.write("Existen diferencias estadísticamente significativas entre los algoritmos (p < 0.05)\n\n")

            # Rankings promedio
            f.write(f"### Rankings Promedio\n\n")
            f.write("| Algoritmo | Ranking Promedio |\n")
            f.write("|-----------|------------------|\n")

            # Ordenar algoritmos por ranking (menor es mejor)
            sorted_ranks = sorted(
                friedman['mean_ranks'].items(),
                key=lambda x: x[1]
            )

            for alg, rank in sorted_ranks:
                f.write(f"| {alg} | {rank:.2f} |\n")

            f.write("\n")

            # Prueba post-hoc de Nemenyi
            f.write(f"## Prueba Post-hoc de Nemenyi\n\n")
            f.write(f"- **Diferencia Crítica (CD)**: {results['post_hoc']['cd']:.4f}\n\n")

            f.write("### Matriz de p-valores\n\n")
            f.write("Los p-valores indican la probabilidad de que dos algoritmos tengan un rendimiento similar. ")
            f.write("Valores p < 0.05 indican diferencias estadísticamente significativas.\n\n")

            # Convertir matriz de p-valores a DataFrame para mejor formato
            p_values = results['post_hoc']['p_values']
            p_df = pd.DataFrame(p_values)

            f.write("```\n")
            f.write(f"{p_df.to_string()}\n")
            f.write("```\n\n")

            # Matriz de tamaños de efecto A12
            f.write(f"## Tamaños de Efecto (A12 de Vargha-Delaney)\n\n")

            f.write("La matriz siguiente muestra el estadístico A12 para cada par de algoritmos. ")
            f.write("Un valor A12 = 0.5 indica que no hay diferencia. ")
            f.write("A12 > 0.5 indica que el algoritmo de la fila tiende a superar al de la columna. ")
            f.write("A12 < 0.5 indica que el algoritmo de la columna tiende a superar al de la fila.\n\n")

            f.write("Interpretación de A12:\n")
            f.write("- A12 > 0.71 o < 0.29: Efecto grande\n")
            f.write("- A12 entre 0.64 y 0.71 o entre 0.29 y 0.36: Efecto mediano\n")
            f.write("- A12 entre 0.56 y 0.64 o entre 0.36 y 0.44: Efecto pequeño\n")
            f.write("- A12 entre 0.44 y 0.56: Efecto despreciable\n\n")

            a12_df = pd.DataFrame(results['effect_size'])

            f.write("```\n")
            f.write(f"{a12_df.to_string()}\n")
            f.write("```\n\n")

            # Diagrama CD
            f.write(f"## Diagrama de Diferencia Crítica\n\n")
            f.write(f"![Diagrama CD](cd_diagram.png)\n\n")
            f.write("Los algoritmos conectados por una línea no presentan diferencias estadísticamente significativas entre sí.\n\n")

            # Conclusiones generales
            f.write(f"## Conclusiones\n\n")

            # Identificar el mejor algoritmo
            best_alg = sorted_ranks[0][0]
            f.write(f"- El algoritmo **{best_alg}** obtuvo el mejor ranking promedio ({sorted_ranks[0][1]:.2f}).\n")

            # Crear grupos de algoritmos estadísticamente equivalentes
            # (esto es una simplificación; idealmente deberías usar cliques del grafo como en el CD-diagram)
            groups = []
            current_group = [sorted_ranks[0][0]]

            for i in range(1, len(sorted_ranks)):
                prev_alg = sorted_ranks[i-1][0]
                curr_alg = sorted_ranks[i][0]

                # Verificar si hay diferencia significativa
                p_val = p_df.loc[prev_alg, curr_alg] if prev_alg in p_df.index and curr_alg in p_df.columns else 1.0

                if p_val >= 0.05:  # No hay diferencia significativa
                    current_group.append(curr_alg)
                else:
                    groups.append(current_group)
                    current_group = [curr_alg]

            if current_group:
                groups.append(current_group)

            # Reportar grupos
            if len(groups) > 1:
                f.write("- Se identificaron los siguientes grupos de algoritmos estadísticamente equivalentes:\n")
                for i, group in enumerate(groups, 1):
                    f.write(f"  - Grupo {i}: {', '.join(group)}\n")
            else:
                f.write("- No se encontraron diferencias estadísticamente significativas entre los algoritmos evaluados.\n")

        else:
            f.write("No hay evidencia de diferencias estadísticamente significativas entre los algoritmos (p >= 0.05)\n\n")
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
