import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
from scipy.stats import friedmanchisquare, wilcoxon, kruskal, rankdata, mannwhitneyu
from statsmodels.stats.libqsturng import qsturng
from statsmodels.stats.multitest import multipletests
import os
import math
import warnings
import itertools
from datetime import datetime
import matplotlib.colors as mcolors
from matplotlib.backends.backend_agg import FigureCanvasAgg
from io import BytesIO
import base64

# Suppress specific SciPy warnings
warnings.filterwarnings("ignore", category=stats.ConstantInputWarning)


class StatisticalAnalysis:
    """Clase para realizar análisis estadísticos sobre algoritmos metaheurísticos."""

    @staticmethod
    def prepare_data_for_statistics(benchmark_results, metric="best_fitness"):
        """
        Prepara los datos para pruebas estadísticas.

        Args:
            benchmark_results: Lista de objetos BenchmarkResult
            metric: Métrica a analizar ('best_fitness', 'mean_fitness', 'execution_time', etc.)

        Returns:
            DataFrame con los datos organizados para análisis estadístico
        """
        # Agrupar por instancia
        instances = {}
        for result in benchmark_results:
            if result.instance_name not in instances:
                instances[result.instance_name] = []
            instances[result.instance_name].append(result)

        # Crear DataFrame para cada instancia
        all_data = []

        for instance_name, results in instances.items():
            # Obtener nombres de algoritmos
            algorithm_names = [r.algorithm_name for r in results]

            # Obtener datos según la métrica seleccionada
            if metric == "best_fitness":
                data = [r.fitness_values for r in results]
            elif metric == "mean_fitness":
                data = [[r.mean_fitness] * len(r.fitness_values) for r in results]
            elif metric == "execution_time":
                data = [r.execution_times for r in results]
            elif metric == "gap_to_optimal":
                data = [[r.gap_to_optimal] * len(r.fitness_values) for r in results]
            else:
                # Métrica no reconocida
                continue

            # Asegurar que todos los datos tengan la misma longitud
            min_len = min(len(d) for d in data)
            data = [d[:min_len] for d in data]

            # Crear DataFrame para esta instancia
            for i, algo_name in enumerate(algorithm_names):
                for j, value in enumerate(data[i]):
                    all_data.append(
                        {
                            "Instance": instance_name,
                            "Algorithm": algo_name,
                            "Run": j + 1,
                            "Value": value,
                        }
                    )

        return pd.DataFrame(all_data)

    @staticmethod
    def friedman_test(data_df, alpha=0.05):
        """
        Realiza la prueba de Friedman para comparar múltiples algoritmos.

        Args:
            data_df: DataFrame preparado con prepare_data_for_statistics
            alpha: Nivel de significancia

        Returns:
            Diccionario con resultados de la prueba
        """
        # Verificar que haya suficientes algoritmos y datos
        if len(data_df["Algorithm"].unique()) < 2:
            return {
                "error": "Se requieren al menos 2 algoritmos para la prueba de Friedman"
            }

        # Agrupar por instancia
        instances = data_df["Instance"].unique()
        algorithms = sorted(data_df["Algorithm"].unique())

        # Verificar si hay suficientes datos para Friedman (al menos 2 instancias)
        if len(instances) < 2:
            # Usar Kruskal-Wallis como alternativa para una sola instancia
            return StatisticalAnalysis.kruskal_wallis_test(data_df, alpha)

        # Para cada instancia, calcular el rango promedio de cada algoritmo
        ranks = []
        for instance in instances:
            instance_data = []
            for algo in algorithms:
                # Obtener todos los valores para esta instancia y algoritmo
                values = data_df[
                    (data_df["Instance"] == instance) & (data_df["Algorithm"] == algo)
                ]["Value"].values

                # Si hay varios valores, usar el promedio
                if len(values) > 0:
                    instance_data.append(np.mean(values))
                else:
                    # Si falta algún dato, no se puede aplicar Friedman
                    return {
                        "error": f"Faltan datos para el algoritmo {algo} en la instancia {instance}"
                    }

            # Calcular rangos (menor valor -> mejor rango)
            instance_ranks = rankdata(instance_data)
            ranks.append(instance_ranks)

        # Transponer para tener algoritmos como columnas
        ranks = np.array(ranks)

        # Calcular rangos promedio para cada algoritmo
        avg_ranks = np.mean(ranks, axis=0)
        rank_dict = {algo: rank for algo, rank in zip(algorithms, avg_ranks)}

        # Realizar la prueba de Friedman
        statistic, p_value = friedmanchisquare(
            *[ranks[:, i] for i in range(ranks.shape[1])]
        )

        # Calcular valor crítico para el nivel de significancia
        n_instances = len(instances)
        n_algorithms = len(algorithms)

        # Calcular el valor crítico para el test de Nemenyi
        critical_distance = qsturng(1 - alpha, n_algorithms, np.inf) * np.sqrt(
            (n_algorithms * (n_algorithms + 1)) / (6 * n_instances)
        )

        result = {
            "test": "Friedman",
            "statistic": statistic,
            "p_value": p_value,
            "reject_h0": p_value < alpha,
            "alpha": alpha,
            "algorithms": algorithms,
            "avg_ranks": avg_ranks,
            "rank_dict": rank_dict,
            "critical_distance": critical_distance,
            "n_instances": n_instances,
            "n_algorithms": n_algorithms,
        }

        return result

    @staticmethod
    def kruskal_wallis_test(data_df, alpha=0.05):
        """
        Realiza la prueba de Kruskal-Wallis como alternativa cuando no se cumplen
        los requisitos para la prueba de Friedman.

        Args:
            data_df: DataFrame preparado con prepare_data_for_statistics
            alpha: Nivel de significancia

        Returns:
            Diccionario con resultados de la prueba
        """
        algorithms = sorted(data_df["Algorithm"].unique())
        n_algorithms = len(algorithms)

        # Obtener valores para cada algoritmo
        algo_values = []
        for algo in algorithms:
            values = data_df[data_df["Algorithm"] == algo]["Value"].values
            algo_values.append(values)

        # Realizar la prueba de Kruskal-Wallis
        statistic, p_value = kruskal(*algo_values)

        # Calcular rangos promedio
        all_values = np.concatenate(algo_values)
        all_ranks = rankdata(all_values)

        start = 0
        avg_ranks = []
        for values in algo_values:
            end = start + len(values)
            avg_ranks.append(np.mean(all_ranks[start:end]))
            start = end

        rank_dict = {algo: rank for algo, rank in zip(algorithms, avg_ranks)}

        # Para mantener la compatibilidad con los análisis post-hoc,
        # calculamos un valor comparable al critical_distance de Nemenyi
        # aunque para Kruskal-Wallis el test post-hoc adecuado sería Dunn
        # Esto permite usar el mismo flujo de visualización
        n_instances = 1  # En Kruskal-Wallis, cada muestra es independiente
        n_samples = np.mean(
            [len(vals) for vals in algo_values]
        )  # Promedio de muestras por algoritmo

        # Calculamos una distancia crítica aproximada basada en la fórmula de Nemenyi
        # ajustada para funcionar con una sola instancia pero múltiples muestras
        critical_distance = qsturng(1 - alpha, n_algorithms, np.inf) * np.sqrt(
            (n_algorithms * (n_algorithms + 1)) / (6 * n_samples)
        )

        result = {
            "test": "Kruskal-Wallis",
            "statistic": statistic,
            "p_value": p_value,
            "reject_h0": p_value < alpha,
            "alpha": alpha,
            "algorithms": algorithms,
            "avg_ranks": avg_ranks,
            "rank_dict": rank_dict,
            "critical_distance": critical_distance,  # Añadido para compatibilidad
            "n_instances": n_instances,
            "n_algorithms": n_algorithms,
            "n_samples": n_samples,  # Información adicional para interpretación
        }

        return result

    @staticmethod
    def nemenyi_test(test_result):
        """
        Realiza el test post-hoc de Nemenyi después de Friedman o una prueba equivalente
        para Kruskal-Wallis.

        Args:
            test_result: Resultado de la prueba de Friedman o Kruskal-Wallis

        Returns:
            DataFrame con p-values para comparaciones por pares y distancia crítica
        """
        if "error" in test_result:
            return pd.DataFrame(), 0

        # Verificar que existe critical_distance
        if "critical_distance" not in test_result:
            # Si no existe, generamos un error más informativo
            test_name = test_result.get("test", "Desconocido")
            raise ValueError(
                f"El resultado de la prueba '{test_name}' no contiene la distancia crítica necesaria para realizar el test post-hoc"
            )

        # Si no se rechaza H0, no hay diferencias significativas
        if not test_result["reject_h0"]:
            algorithms = test_result["algorithms"]
            comparison_matrix = pd.DataFrame(1.0, index=algorithms, columns=algorithms)
            return comparison_matrix, test_result["critical_distance"]

        algorithms = test_result["algorithms"]
        avg_ranks = test_result["avg_ranks"]
        n_instances = test_result["n_instances"]
        n_algorithms = test_result["n_algorithms"]

        # Matriz para p-values
        comparison_matrix = pd.DataFrame(index=algorithms, columns=algorithms)

        # Verificar qué tipo de prueba se realizó
        test_type = test_result.get("test", "Friedman")

        # Calcular p-values para cada par de algoritmos
        for i, algo_i in enumerate(algorithms):
            for j, algo_j in enumerate(algorithms):
                if i == j:
                    comparison_matrix.loc[algo_i, algo_j] = 1.0
                else:
                    # Calcular diferencia en rangos
                    rank_diff = abs(avg_ranks[i] - avg_ranks[j])

                    if test_type == "Kruskal-Wallis":
                        # Para Kruskal-Wallis, usar n_samples en lugar de n_instances
                        n_samples = test_result.get("n_samples", n_instances)
                        q = rank_diff / np.sqrt(
                            (n_algorithms * (n_algorithms + 1)) / (6 * n_samples)
                        )
                    else:
                        # Cálculo original para Friedman
                        q = rank_diff / np.sqrt(
                            (n_algorithms * (n_algorithms + 1)) / (6 * n_instances)
                        )

                    # Calcular p-value a partir de q (usando aproximación)
                    p_value = 2 * (1 - stats.norm.cdf(q))

                    comparison_matrix.loc[algo_i, algo_j] = p_value

        # Devolver matriz de p-values y distancia crítica
        return comparison_matrix, test_result["critical_distance"]

    @staticmethod
    def wilcoxon_paired_test(data_df, alpha=0.05, bonferroni_correction=True):
        """
        Realiza pruebas de Wilcoxon por pares con corrección de Bonferroni opcional.

        Args:
            data_df: DataFrame preparado con prepare_data_for_statistics
            alpha: Nivel de significancia
            bonferroni_correction: Si es True, aplica corrección de Bonferroni

        Returns:
            DataFrame con p-values para comparaciones por pares y tabla de efecto tamaño
        """
        algorithms = sorted(data_df["Algorithm"].unique())
        n_algorithms = len(algorithms)

        # Matrices para p-values y efecto tamaño
        wilcoxon_matrix = pd.DataFrame(index=algorithms, columns=algorithms)
        effect_size_matrix = pd.DataFrame(index=algorithms, columns=algorithms)

        # Obtener los datos de cada instancia para cada algoritmo
        algo_data = {}
        instances = data_df["Instance"].unique()

        for algo in algorithms:
            algo_data[algo] = []
            for instance in instances:
                # Tomar el mejor valor para cada instancia y algoritmo
                # (o se podría tomar el promedio, dependiendo del objetivo)
                values = data_df[
                    (data_df["Algorithm"] == algo) & (data_df["Instance"] == instance)
                ]["Value"].values
                if len(values) > 0:
                    # Usar el mejor valor (mínimo)
                    algo_data[algo].append(np.min(values))

        # Lista para almacenar comparaciones para corrección múltiple
        all_p_values = []
        all_comparisons = []

        # Realizar prueba de Wilcoxon para cada par de algoritmos
        for i, algo_i in enumerate(algorithms):
            for j, algo_j in enumerate(algorithms):
                if i == j:
                    wilcoxon_matrix.loc[algo_i, algo_j] = 1.0
                    effect_size_matrix.loc[algo_i, algo_j] = 0.0
                else:
                    # Asegurar que los datos tienen la misma longitud
                    data_i = algo_data[algo_i]
                    data_j = algo_data[algo_j]

                    # Si hay datos suficientes, realizar prueba de Wilcoxon
                    if len(data_i) > 0 and len(data_j) > 0:
                        # Usar prueba de Wilcoxon de dos colas
                        try:
                            statistic, p_value = wilcoxon(data_i, data_j)
                            all_p_values.append(p_value)
                            all_comparisons.append((algo_i, algo_j))

                            # Calcular efecto tamaño (r = Z / sqrt(N))
                            # Wilcoxon no devuelve Z directamente, por lo que aproximamos
                            n = len(data_i)
                            z = stats.norm.ppf(1 - p_value / 2)  # Aproximación
                            effect_size = z / np.sqrt(2 * n)

                            wilcoxon_matrix.loc[algo_i, algo_j] = p_value
                            effect_size_matrix.loc[algo_i, algo_j] = effect_size
                        except:
                            wilcoxon_matrix.loc[algo_i, algo_j] = 1.0
                            effect_size_matrix.loc[algo_i, algo_j] = 0.0
                    else:
                        wilcoxon_matrix.loc[algo_i, algo_j] = 1.0
                        effect_size_matrix.loc[algo_i, algo_j] = 0.0

        # Aplicar corrección de Bonferroni si se solicita
        if bonferroni_correction and len(all_p_values) > 0:
            # Calcular número de comparaciones
            n_algorithms * (n_algorithms - 1) / 2

            # Aplicar corrección de Bonferroni
            reject, adj_p_values, _, _ = multipletests(
                all_p_values, alpha=alpha, method="bonferroni"
            )

            # Actualizar matriz con p-values ajustados
            for (algo_i, algo_j), adj_p in zip(all_comparisons, adj_p_values):
                wilcoxon_matrix.loc[algo_i, algo_j] = adj_p

        return wilcoxon_matrix, effect_size_matrix

    @staticmethod
    def effect_size_cliff_delta(data_df):
        """
        Calcula el efecto tamaño Cliff's Delta para cada par de algoritmos.

        Args:
            data_df: DataFrame preparado con prepare_data_for_statistics

        Returns:
            DataFrame con valores de Cliff's Delta para comparaciones por pares
        """
        algorithms = sorted(data_df["Algorithm"].unique())

        # Matriz para Cliff's Delta
        cliff_delta_matrix = pd.DataFrame(index=algorithms, columns=algorithms)

        # Obtener los datos para cada algoritmo
        algo_data = {}
        for algo in algorithms:
            algo_data[algo] = data_df[data_df["Algorithm"] == algo]["Value"].values

        # Calcular Cliff's Delta para cada par de algoritmos
        for i, algo_i in enumerate(algorithms):
            for j, algo_j in enumerate(algorithms):
                if i == j:
                    cliff_delta_matrix.loc[algo_i, algo_j] = 0.0
                else:
                    x = algo_data[algo_i]
                    y = algo_data[algo_j]

                    # Matriz de comparaciones
                    less = 0
                    greater = 0
                    equal = 0

                    for xi in x:
                        for yi in y:
                            if xi < yi:
                                less += 1
                            elif xi > yi:
                                greater += 1
                            else:
                                equal += 1

                    # Calcular Cliff's Delta
                    total = len(x) * len(y)
                    cliff_delta = (less - greater) / total if total > 0 else 0

                    cliff_delta_matrix.loc[algo_i, algo_j] = cliff_delta

        return cliff_delta_matrix

    @staticmethod
    def effect_size_rank_biserial(data_df):
        """
        Calcula el efecto tamaño rank-biserial para cada par de algoritmos.

        Args:
            data_df: DataFrame preparado con prepare_data_for_statistics

        Returns:
            DataFrame con valores de rank-biserial para comparaciones por pares
        """
        algorithms = sorted(data_df["Algorithm"].unique())

        # Matriz para rank-biserial
        rank_biserial_matrix = pd.DataFrame(index=algorithms, columns=algorithms)

        # Obtener los datos para cada algoritmo
        algo_data = {}
        for algo in algorithms:
            algo_data[algo] = data_df[data_df["Algorithm"] == algo]["Value"].values

        # Calcular rank-biserial para cada par de algoritmos
        for i, algo_i in enumerate(algorithms):
            for j, algo_j in enumerate(algorithms):
                if i == j:
                    rank_biserial_matrix.loc[algo_i, algo_j] = 0.0
                else:
                    x = algo_data[algo_i]
                    y = algo_data[algo_j]

                    # Aplicar Mann-Whitney U
                    try:
                        u, p_value = mannwhitneyu(x, y, alternative="two-sided")
                        n1, n2 = len(x), len(y)

                        # Calcular rank-biserial (r = 1 - 2U/(n1*n2))
                        r = 1 - 2 * u / (n1 * n2)

                        rank_biserial_matrix.loc[algo_i, algo_j] = r
                    except:
                        rank_biserial_matrix.loc[algo_i, algo_j] = 0.0

        return rank_biserial_matrix

    @staticmethod
    def vargha_delaney_a_measure(data_df):
        """
        Calcula la medida A de Vargha-Delaney para cada par de algoritmos.

        Args:
            data_df: DataFrame preparado con prepare_data_for_statistics

        Returns:
            DataFrame con valores de la medida A para comparaciones por pares
        """
        try:
            algorithms = sorted(data_df["Algorithm"].unique())

            # Matriz para la medida A
            a_measure_matrix = pd.DataFrame(index=algorithms, columns=algorithms)

            # Obtener los datos para cada algoritmo, asegurando que son numéricos
            algo_data = {}
            for algo in algorithms:
                try:
                    # Convertir valores a float y eliminar NaN
                    values = data_df[data_df["Algorithm"] == algo]["Value"].values
                    algo_data[algo] = np.array(
                        [float(v) for v in values if not np.isnan(float(v))]
                    )
                except Exception as e:
                    print(f"Debug - Error al obtener datos para {algo}: {str(e)}")
                    algo_data[algo] = np.array([])

            # Calcular la medida A para cada par de algoritmos con manejo de errores
            for i, algo_i in enumerate(algorithms):
                for j, algo_j in enumerate(algorithms):
                    try:
                        if i == j:
                            a_measure_matrix.loc[algo_i, algo_j] = 0.5
                        else:
                            x = algo_data[algo_i]
                            y = algo_data[algo_j]

                            # Verificar que hay datos suficientes
                            if len(x) == 0 or len(y) == 0:
                                print(
                                    f"Debug - Datos insuficientes para comparar {algo_i} y {algo_j}"
                                )
                                a_measure_matrix.loc[algo_i, algo_j] = 0.5
                                continue

                            # Probabilidad de que x sea menor que y
                            p_less = 0
                            for xi in x:
                                for yi in y:
                                    try:
                                        if xi < yi:
                                            p_less += 1
                                        elif xi == yi:
                                            p_less += 0.5
                                    except Exception:
                                        # Si hay error en la comparación, contar como neutro
                                        p_less += 0.5

                            # Calcular A
                            a = (
                                p_less / (len(x) * len(y))
                                if len(x) * len(y) > 0
                                else 0.5
                            )

                            a_measure_matrix.loc[algo_i, algo_j] = a
                    except Exception as e:
                        print(
                            f"Debug - Error al calcular Vargha-Delaney para {algo_i} y {algo_j}: {str(e)}"
                        )
                        a_measure_matrix.loc[algo_i, algo_j] = 0.5

            return a_measure_matrix
        except Exception as e:
            print(f"Debug - Error general en Vargha-Delaney: {str(e)}")
            # Devolver una matriz vacía con un valor de error
            return pd.DataFrame([[0.5]])  # Valor neutro para Vargha-Delaney

    @staticmethod
    def interpret_effect_size(effect_size, method="cliff_delta"):
        """
        Interpreta el tamaño del efecto según el método.

        Args:
            effect_size: Valor del tamaño del efecto
            method: Método utilizado ('cliff_delta', 'rank_biserial', 'vargha_delaney')

        Returns:
            Interpretación como cadena de texto
        """
        if method == "cliff_delta":
            effect_size = abs(effect_size)
            if effect_size < 0.147:
                return "Negligible"
            elif effect_size < 0.33:
                return "Small"
            elif effect_size < 0.474:
                return "Medium"
            else:
                return "Large"

        elif method == "rank_biserial":
            effect_size = abs(effect_size)
            if effect_size < 0.1:
                return "Negligible"
            elif effect_size < 0.3:
                return "Small"
            elif effect_size < 0.5:
                return "Medium"
            else:
                return "Large"

        elif method == "vargha_delaney":
            a = effect_size
            if a < 0.5:
                a = 1 - a  # Asegurar que a >= 0.5

            if a < 0.56:
                return "Negligible"
            elif a < 0.64:
                return "Small"
            elif a < 0.71:
                return "Medium"
            else:
                return "Large"

        return "Unknown"

    @staticmethod
    def plot_critical_difference_diagram(friedman_result, title=None):
        """
        Crea un diagrama de diferencia crítica según los resultados de Friedman.

        Args:
            friedman_result: Resultado de la prueba de Friedman
            title: Título opcional para el gráfico

        Returns:
            Objeto matplotlib.figure.Figure
        """
        # Captura de errores para el diagnóstico
        try:
            if "error" in friedman_result:
                fig, ax = plt.subplots(figsize=(10, 2))
                ax.text(0.5, 0.5, friedman_result["error"], ha="center", va="center")
                ax.axis("off")
                return fig

            # Verificar requisitos mínimos
            if "critical_distance" not in friedman_result:
                fig, ax = plt.subplots(figsize=(10, 2))
                ax.text(
                    0.5,
                    0.5,
                    "No se pudo calcular la distancia crítica para este análisis",
                    ha="center",
                    va="center",
                )
                ax.axis("off")
                return fig

            # Obtener datos necesarios
            algorithms = list(
                friedman_result["algorithms"]
            )  # Convertir a lista para asegurar indexación
            cd = float(
                friedman_result["critical_distance"]
            )  # Convertir a float para cálculos

            # Debugging de tipos de datos
            print(f"Debug - Algoritmos: {algorithms}, Tipo: {type(algorithms)}")
            print(f"Debug - CD: {cd}, Tipo: {type(cd)}")

            # Obtener y convertir avg_ranks de manera segura
            if isinstance(friedman_result["avg_ranks"], np.ndarray):
                avg_ranks = friedman_result["avg_ranks"].astype(float)
            else:
                # Si no es numpy array, convertir a uno
                avg_ranks = np.array([float(r) for r in friedman_result["avg_ranks"]])

            print(f"Debug - Avg Ranks: {avg_ranks}, Tipo: {type(avg_ranks)}")

            # Ordenar algoritmos por rango (usando listas en lugar de indexación numpy)
            pairs = list(zip(avg_ranks, algorithms))
            pairs.sort()  # Ordenar por rango (primer elemento de cada par)
            sorted_ranks = np.array([float(p[0]) for p in pairs])
            sorted_algos = [p[1] for p in pairs]

            print(f"Debug - Sorted Ranks: {sorted_ranks}")
            print(f"Debug - Sorted Algos: {sorted_algos}")

            # Crear figura
            fig, ax = plt.subplots(figsize=(12, 4))

            # Dibujar línea de rangos
            ax.axhline(y=0, color="k", linestyle="-", linewidth=1)

            # Dibujar posición de cada algoritmo
            for i, (algo, rank) in enumerate(zip(sorted_algos, sorted_ranks)):
                ax.plot([rank], [0], "o", color="blue", markersize=8)
                ax.text(rank, 0.1, algo, ha="center", va="bottom", rotation=45)
                ax.text(rank, -0.1, f"{rank:.2f}", ha="center", va="top")

            # Dibujar barras para algoritmos no significativamente diferentes
            for i in range(len(sorted_algos)):
                for j in range(i + 1, len(sorted_algos)):
                    if abs(sorted_ranks[i] - sorted_ranks[j]) <= cd:
                        # Conectar algoritmos no significativamente diferentes
                        y_pos = -0.05 * (
                            1 + (j - i) * 0.5
                        )  # Ajustar altura para evitar solapamiento
                        ax.plot(
                            [sorted_ranks[i], sorted_ranks[j]],
                            [y_pos, y_pos],
                            "k-",
                            linewidth=2,
                        )

            # Ajustar límites y etiquetas
            rank_min, rank_max = min(sorted_ranks), max(sorted_ranks)
            padding = max(0.5, cd * 0.1)
            ax.set_xlim(rank_min - padding, rank_max + padding)
            ax.set_ylim(-0.5, 0.5)

            ax.set_xlabel("Ranking Promedio")

            if title:
                ax.set_title(title)
            else:
                ax.set_title(f"Diagrama de Diferencia Crítica (CD = {cd:.2f})")

            ax.set_yticks([])
            ax.spines["right"].set_visible(False)
            ax.spines["top"].set_visible(False)
            ax.spines["left"].set_visible(False)

            plt.tight_layout()

            return fig

        except Exception as e:
            # En caso de error, generar un diagrama informativo
            print(f"Debug - Error en diagrama CD: {str(e)}")
            fig, ax = plt.subplots(figsize=(10, 2))
            ax.text(
                0.5,
                0.5,
                f"Error al generar diagrama: {str(e)}",
                ha="center",
                va="center",
            )
            ax.axis("off")
            return fig

    @staticmethod
    def plot_posthoc_heatmap(posthoc_matrix, title=None, alpha=0.05):
        """
        Crea un mapa de calor para visualizar los p-values de pruebas post-hoc.

        Args:
            posthoc_matrix: Matriz de p-values
            title: Título opcional para el gráfico
            alpha: Nivel de significancia

        Returns:
            Objeto matplotlib.figure.Figure
        """
        try:
            # Crear copia de la matriz para modificarla
            heatmap_data = posthoc_matrix.copy()

            # Asegurar que los datos son numéricos
            try:
                # Convertir todos los valores a float
                for i in range(len(heatmap_data.index)):
                    for j in range(len(heatmap_data.columns)):
                        try:
                            heatmap_data.iloc[i, j] = float(heatmap_data.iloc[i, j])
                        except (ValueError, TypeError):
                            # Si no se puede convertir a float, usar un valor neutro
                            print(
                                f"Debug - Valor no numérico en posición [{i}, {j}]: {heatmap_data.iloc[i, j]}"
                            )
                            heatmap_data.iloc[
                                i, j
                            ] = 1.0  # Valor neutro para p-values (no significativo)
            except Exception as e:
                print(f"Debug - Error al convertir datos de p-values: {str(e)}")
                # Crear un nuevo DataFrame con los mismos índices y columnas pero con valores float
                indices = heatmap_data.index
                columnas = heatmap_data.columns
                heatmap_data = pd.DataFrame(1.0, index=indices, columns=columnas)

            # Crear figura
            fig, ax = plt.subplots(figsize=(12, 10))

            # Colores para el mapa de calor (verde: significativo, rojo: no significativo)
            cmap = sns.diverging_palette(10, 120, as_cmap=True)

            # Crear máscara para la diagonal con tipo explícito
            mask = np.zeros_like(heatmap_data.values, dtype=bool)
            np.fill_diagonal(mask, True)

            # Crear el mapa de calor con validación de datos
            sns.heatmap(
                heatmap_data.astype(float),
                mask=mask,
                cmap=cmap,
                vmin=0,
                vmax=1,
                square=True,
                linewidths=0.5,
                annot=True,
                fmt=".3f",
                annot_kws={"size": 9},
                ax=ax,
            )

            # Resaltar las celdas con p-value < alpha de manera segura
            for i in range(len(heatmap_data.index)):
                for j in range(len(heatmap_data.columns)):
                    if i != j:
                        try:
                            p_value = float(heatmap_data.iloc[i, j])
                            if p_value < alpha:
                                ax.add_patch(
                                    plt.Rectangle(
                                        (j, i),
                                        1,
                                        1,
                                        fill=False,
                                        edgecolor="black",
                                        lw=2,
                                    )
                                )
                        except Exception as e:
                            print(
                                f"Debug - Error al resaltar celda [{i}, {j}]: {str(e)}"
                            )

            # Ajustar etiquetas y título
            ax.set_xlabel("Algoritmo")
            ax.set_ylabel("Algoritmo")

            if title:
                ax.set_title(title)
            else:
                ax.set_title(f"P-values de Prueba Post-hoc (α = {alpha})")

            plt.tight_layout()

            return fig

        except Exception as e:
            # En caso de error, generar un diagrama informativo
            print(f"Debug - Error al generar mapa de calor post-hoc: {str(e)}")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(
                0.5,
                0.5,
                f"Error al generar el mapa de calor post-hoc:\n{str(e)}",
                ha="center",
                va="center",
                fontsize=12,
                wrap=True,
            )
            ax.axis("off")
            plt.tight_layout()
            return fig

    @staticmethod
    def plot_effect_size_heatmap(effect_size_matrix, method="cliff_delta", title=None):
        """
        Crea un mapa de calor para visualizar el efecto tamaño entre algoritmos.

        Args:
            effect_size_matrix: Matriz de efecto tamaño
            method: Método utilizado para el efecto tamaño
            title: Título opcional para el gráfico

        Returns:
            Objeto matplotlib.figure.Figure
        """
        try:
            # Crear copia de la matriz para modificarla
            heatmap_data = effect_size_matrix.copy()

            # Asegurar que los datos son numéricos
            try:
                # Convertir todos los valores a float
                for i in range(len(heatmap_data.index)):
                    for j in range(len(heatmap_data.columns)):
                        try:
                            heatmap_data.iloc[i, j] = float(heatmap_data.iloc[i, j])
                        except (ValueError, TypeError):
                            # Si no se puede convertir a float, usar un valor neutro
                            print(
                                f"Debug - Valor no numérico en posición [{i}, {j}]: {heatmap_data.iloc[i, j]}"
                            )
                            if method == "vargha_delaney":
                                heatmap_data.iloc[
                                    i, j
                                ] = 0.5  # Valor neutro para Vargha-Delaney
                            else:
                                heatmap_data.iloc[
                                    i, j
                                ] = 0.0  # Valor neutro para otros métodos
            except Exception as e:
                print(f"Debug - Error al convertir datos de efecto tamaño: {str(e)}")
                # Crear un nuevo DataFrame con los mismos índices y columnas pero con valores float
                indices = heatmap_data.index
                columnas = heatmap_data.columns
                heatmap_data = pd.DataFrame(0.0, index=indices, columns=columnas)

            # Crear figura
            fig, ax = plt.subplots(figsize=(12, 10))

            # Definir rango de valores según el método
            if method == "vargha_delaney":
                vmin, vmax = 0, 1
                center = 0.5
            else:
                vmin, vmax = -1, 1
                center = 0

            # Colores para el mapa de calor
            cmap = sns.diverging_palette(240, 10, as_cmap=True)

            # Crear máscara para la diagonal con tipo explícito
            mask = np.zeros_like(heatmap_data.values, dtype=bool)
            np.fill_diagonal(mask, True)

            # Crear el mapa de calor con validación de datos
            sns.heatmap(
                heatmap_data.astype(float),
                mask=mask,
                cmap=cmap,
                vmin=vmin,
                vmax=vmax,
                center=center,
                square=True,
                linewidths=0.5,
                annot=True,
                fmt=".3f",
                annot_kws={"size": 9},
                ax=ax,
            )

            # Añadir anotaciones para la interpretación de manera segura
            for i in range(len(heatmap_data.index)):
                for j in range(len(heatmap_data.columns)):
                    if i != j:
                        try:
                            effect = float(heatmap_data.iloc[i, j])
                            interpretation = StatisticalAnalysis.interpret_effect_size(
                                effect, method
                            )
                            text_color = (
                                "white"
                                if abs(effect - center) > (vmax - vmin) * 0.3
                                else "black"
                            )
                            ax.text(
                                j + 0.5,
                                i + 0.7,
                                interpretation,
                                ha="center",
                                va="center",
                                fontsize=7,
                                color=text_color,
                            )
                        except Exception as e:
                            print(f"Debug - Error al añadir anotación: {str(e)}")

            # Ajustar etiquetas y título
            ax.set_xlabel("Algoritmo")
            ax.set_ylabel("Algoritmo")

            method_names = {
                "cliff_delta": "Cliff's Delta",
                "rank_biserial": "Rank-Biserial",
                "vargha_delaney": "Vargha-Delaney A",
            }

            if title:
                ax.set_title(title)
            else:
                method_name = method_names.get(method, method)
                ax.set_title(f"Efecto Tamaño ({method_name})")

            plt.tight_layout()

            return fig

        except Exception as e:
            # En caso de error, generar un diagrama informativo
            print(f"Debug - Error al generar mapa de efecto tamaño: {str(e)}")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(
                0.5,
                0.5,
                f"Error al generar el mapa de efecto tamaño ({method}):\n{str(e)}",
                ha="center",
                va="center",
                fontsize=12,
                wrap=True,
            )
            ax.axis("off")
            plt.tight_layout()
            return fig

    @staticmethod
    def plot_rank_boxplot(data_df, friedman_result=None, title=None):
        """
        Crea un boxplot de las distribuciones de rangos para cada algoritmo.

        Args:
            data_df: DataFrame preparado con prepare_data_for_statistics
            friedman_result: Resultado opcional de la prueba de Friedman
            title: Título opcional para el gráfico

        Returns:
            Objeto matplotlib.figure.Figure
        """
        # Agrupar datos por instancia y algoritmo
        instances = data_df["Instance"].unique()
        algorithms = sorted(data_df["Algorithm"].unique())

        # Preparar datos de rango
        ranks_data = []

        for instance in instances:
            instance_data = {}
            for algo in algorithms:
                values = data_df[
                    (data_df["Instance"] == instance) & (data_df["Algorithm"] == algo)
                ]["Value"].values

                if len(values) > 0:
                    # Usar el mejor valor para cada combinación instancia-algoritmo
                    instance_data[algo] = np.min(values)

            # Calcular rangos para esta instancia
            if len(instance_data) == len(algorithms):
                algo_values = [instance_data[algo] for algo in algorithms]
                instance_ranks = rankdata(algo_values)

                for algo, rank in zip(algorithms, instance_ranks):
                    ranks_data.append({"Algorithm": algo, "Rank": rank})

        # Convertir a DataFrame
        ranks_df = pd.DataFrame(ranks_data)

        # Crear figura
        fig, ax = plt.subplots(figsize=(12, 6))

        # Crear boxplot
        sns.boxplot(x="Algorithm", y="Rank", data=ranks_df, ax=ax)

        # Añadir puntos individuales
        sns.stripplot(
            x="Algorithm",
            y="Rank",
            data=ranks_df,
            color="black",
            size=4,
            alpha=0.5,
            ax=ax,
        )

        # Si hay resultados de Friedman, añadir rangos promedio
        if friedman_result and "rank_dict" in friedman_result:
            rank_dict = friedman_result["rank_dict"]
            for i, algo in enumerate(algorithms):
                avg_rank = rank_dict[algo]
                ax.plot(i, avg_rank, "r*", markersize=12)

        # Ajustar etiquetas y título
        ax.set_xlabel("Algoritmo")
        ax.set_ylabel("Rango")

        if title:
            ax.set_title(title)
        else:
            ax.set_title("Distribución de Rangos por Algoritmo")

        # Ajustar límites del eje y
        ax.set_ylim(0.5, len(algorithms) + 0.5)
        ax.invert_yaxis()  # Invertir para que menor rango aparezca arriba

        plt.tight_layout()

        return fig

    @staticmethod
    def generate_statistical_comparison_table(
        friedman_result,
        posthoc_matrix,
        effect_size_matrix,
        method="cliff_delta",
        alpha=0.05,
    ):
        """
        Genera una tabla de comparación estadística completa.

        Args:
            friedman_result: Resultado de la prueba de Friedman
            posthoc_matrix: Matriz de p-values de prueba post-hoc
            effect_size_matrix: Matriz de efecto tamaño
            method: Método utilizado para el efecto tamaño
            alpha: Nivel de significancia

        Returns:
            DataFrame con la tabla de comparación
        """
        if "error" in friedman_result:
            return pd.DataFrame({"Error": [friedman_result["error"]]})

        algorithms = friedman_result["algorithms"]
        rank_dict = friedman_result["rank_dict"]

        # Ordenar algoritmos por rango
        sorted_algos = sorted(algorithms, key=lambda x: rank_dict[x])

        # Crear tabla de comparación
        comparison_table = []

        # Añadir fila para cada algoritmo
        for i, algo_i in enumerate(sorted_algos):
            row = {"Algoritmo": algo_i, "Rango": rank_dict[algo_i]}

            # Comparación con otros algoritmos
            for j, algo_j in enumerate(sorted_algos):
                if i != j:
                    p_value = posthoc_matrix.loc[algo_i, algo_j]
                    effect = effect_size_matrix.loc[algo_i, algo_j]
                    interpretation = StatisticalAnalysis.interpret_effect_size(
                        effect, method
                    )

                    # Determinar símbolo para p-value
                    if p_value < alpha:
                        if rank_dict[algo_i] < rank_dict[algo_j]:
                            symbol = "+"  # Mejor
                        else:
                            symbol = "-"  # Peor
                    else:
                        symbol = "="  # No diferencia significativa

                    # Añadir a la fila
                    row[f"{algo_j} (p-value)"] = p_value
                    row[f"{algo_j} (efecto)"] = effect
                    row[f"{algo_j} (interp)"] = interpretation
                    row[f"{algo_j} (comp)"] = symbol

            comparison_table.append(row)

        # Convertir a DataFrame
        df_comparison = pd.DataFrame(comparison_table)

        # Añadir información general
        test_info = {
            "Prueba": friedman_result["test"],
            "Estadístico": friedman_result["statistic"],
            "p-value": friedman_result["p_value"],
            "Diferencia significativa": "Sí" if friedman_result["reject_h0"] else "No",
            "Distancia crítica": friedman_result.get("critical_distance", "N/A"),
        }

        return df_comparison, test_info

    @staticmethod
    def generate_statistical_analysis_report(
        data_df, metric="best_fitness", alpha=0.05, output_file=None
    ):
        """
        Genera un informe completo de análisis estadístico en formato HTML.

        Args:
            data_df: DataFrame preparado con prepare_data_for_statistics
            metric: Métrica analizada
            alpha: Nivel de significancia
            output_file: Ruta para guardar el informe HTML

        Returns:
            Ruta al archivo HTML generado
        """
        # Si no se especifica archivo de salida, generar nombre automático
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"results/statistical_report_{metric}_{timestamp}.html"

        # Crear directorio si no existe
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Validar los datos de entrada
        print(f"Debug - Análisis de datos para {metric}:")
        print(f"- Instancias: {data_df['Instance'].nunique()}")
        print(f"- Algoritmos: {data_df['Algorithm'].nunique()}")
        print(f"- Total de ejecuciones: {len(data_df)}")

        # Verificar si hay suficientes datos para un análisis estadístico
        if data_df["Instance"].nunique() < 2 and data_df["Algorithm"].nunique() < 2:
            error_msg = "Datos insuficientes para análisis estadístico: se requieren múltiples instancias o algoritmos."
            with open(output_file, "w") as f:
                f.write(
                    f"""
                <!DOCTYPE html>
                <html>
                <head><title>Error en Análisis Estadístico</title></head>
                <body>
                <h1>Error en el Análisis Estadístico</h1>
                <p>{error_msg}</p>
                <p>Se requieren al menos 2 algoritmos con múltiples ejecuciones para realizar análisis estadísticos comparativos.</p>
                </body>
                </html>
                """
                )
            return output_file

        # Realizar prueba de Friedman
        friedman_result = StatisticalAnalysis.friedman_test(data_df, alpha=alpha)

        # Información sobre el resultado Friedman
        print("Debug - Resultado de Friedman:")
        for key, value in friedman_result.items():
            if key not in ["avg_ranks", "algorithms"]:
                print(f"- {key}: {value}")

        # Realizar pruebas post-hoc
        try:
            posthoc_matrix, cd = StatisticalAnalysis.nemenyi_test(friedman_result)
            print(f"Debug - Post-hoc completado con éxito. CD = {cd}")
        except Exception as e:
            print(f"Debug - Error en post-hoc: {str(e)}")
            # Crear matrices vacías si falla
            algorithms = friedman_result.get("algorithms", [])
            posthoc_matrix = pd.DataFrame(1.0, index=algorithms, columns=algorithms)
            cd = 0

        # Realizar pruebas por pares con Wilcoxon
        try:
            wilcoxon_matrix, wilcoxon_effect = StatisticalAnalysis.wilcoxon_paired_test(
                data_df, alpha=alpha, bonferroni_correction=True
            )
            print("Debug - Wilcoxon completado con éxito.")
        except Exception as e:
            print(f"Debug - Error en Wilcoxon: {str(e)}")
            # Crear matrices vacías si falla
            algorithms = friedman_result.get("algorithms", [])
            pd.DataFrame(1.0, index=algorithms, columns=algorithms)
            pd.DataFrame(0.0, index=algorithms, columns=algorithms)

        # Calcular diferentes medidas de efecto tamaño
        try:
            cliff_delta = StatisticalAnalysis.effect_size_cliff_delta(data_df)
            vargha_delaney = StatisticalAnalysis.vargha_delaney_a_measure(data_df)
            print("Debug - Cálculo de efecto tamaño completado con éxito.")
        except Exception as e:
            print(f"Debug - Error en cálculo de efecto tamaño: {str(e)}")
            # Crear matrices vacías si falla
            algorithms = friedman_result.get("algorithms", [])
            cliff_delta = pd.DataFrame(0.0, index=algorithms, columns=algorithms)
            vargha_delaney = pd.DataFrame(0.5, index=algorithms, columns=algorithms)

        # Generar tabla de comparación
        (
            comparison_table,
            test_info,
        ) = StatisticalAnalysis.generate_statistical_comparison_table(
            friedman_result,
            posthoc_matrix,
            cliff_delta,
            method="cliff_delta",
            alpha=alpha,
        )

        # Generar visualizaciones
        figures_dir = os.path.join(os.path.dirname(output_file), "figures")
        os.makedirs(figures_dir, exist_ok=True)

        # Función para convertir figura a string base64 de forma segura
        def fig_to_base64(fig):
            try:
                buf = BytesIO()
                fig.savefig(buf, format="png")
                buf.seek(0)
                img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
                plt.close(fig)
                return img_str
            except Exception as e:
                print(f"Debug - Error al convertir figura a base64: {str(e)}")
                # Generar una imagen de error alternativa
                error_fig, ax = plt.subplots(figsize=(8, 2))
                ax.text(
                    0.5,
                    0.5,
                    f"Error al generar gráfico: {str(e)}",
                    ha="center",
                    va="center",
                    fontsize=12,
                    color="red",
                )
                ax.axis("off")

                buf = BytesIO()
                error_fig.savefig(buf, format="png")
                buf.seek(0)
                img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
                plt.close(error_fig)
                return img_str

        # Generar visualizaciones dentro de bloques try/except para manejar errores
        try:
            cd_diagram = StatisticalAnalysis.plot_critical_difference_diagram(
                friedman_result,
                title=f"Diagrama de Diferencia Crítica - {metric.capitalize()}",
            )
            cd_img = fig_to_base64(cd_diagram)
        except Exception as e:
            print(f"Debug - Error al generar diagrama CD: {str(e)}")
            cd_img = fig_to_base64(plt.figure(figsize=(8, 2)))

        try:
            posthoc_heatmap = StatisticalAnalysis.plot_posthoc_heatmap(
                posthoc_matrix,
                title=f"P-values Post-hoc - {metric.capitalize()}",
                alpha=alpha,
            )
            posthoc_img = fig_to_base64(posthoc_heatmap)
        except Exception as e:
            print(f"Debug - Error al generar mapa de calor post-hoc: {str(e)}")
            posthoc_img = fig_to_base64(plt.figure(figsize=(8, 2)))

        try:
            effect_heatmap = StatisticalAnalysis.plot_effect_size_heatmap(
                cliff_delta,
                method="cliff_delta",
                title=f"Cliff's Delta - {metric.capitalize()}",
            )
            effect_img = fig_to_base64(effect_heatmap)
        except Exception as e:
            print(f"Debug - Error al generar mapa de efecto tamaño: {str(e)}")
            effect_img = fig_to_base64(plt.figure(figsize=(8, 2)))

        try:
            vd_heatmap = StatisticalAnalysis.plot_effect_size_heatmap(
                vargha_delaney,
                method="vargha_delaney",
                title=f"Vargha-Delaney A - {metric.capitalize()}",
            )
            vd_img = fig_to_base64(vd_heatmap)
        except Exception as e:
            print(f"Debug - Error al generar mapa Vargha-Delaney: {str(e)}")
            vd_img = fig_to_base64(plt.figure(figsize=(8, 2)))

        try:
            rank_boxplot = StatisticalAnalysis.plot_rank_boxplot(
                data_df,
                friedman_result,
                title=f"Distribución de Rangos - {metric.capitalize()}",
            )
            rank_img = fig_to_base64(rank_boxplot)
        except Exception as e:
            print(f"Debug - Error al generar boxplot de rangos: {str(e)}")
            rank_img = fig_to_base64(plt.figure(figsize=(8, 2)))

        # Crear contenido HTML
        # Convertir la métrica a string seguro para prevenir errores de formato
        metric_str = str(metric).capitalize() if metric else "Desconocida"

        # Crear contenido HTML evitando problemas con indentación y newlines
        css_style = """body {
    font-family: "Arial", sans-serif;
    margin: 20px;
    line-height: 1.6;
}
h1, h2, h3 {
    color: #2c3e50;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 20px;
}
th, td {
    text-align: left;
    padding: 8px;
    border: 1px solid #ddd;
}
th {
    background-color: #f2f2f2;
}
tr:nth-child(even) {
    background-color: #f9f9f9;
}
.section {
    margin-bottom: 30px;
}
.figure {
    margin: 20px 0;
    text-align: center;
}
.figure img {
    max-width: 100%;
    height: auto;
}
.caption {
    margin-top: 10px;
    font-style: italic;
    color: #666;
}
.highlight {
    font-weight: bold;
    color: #e74c3c;
}
.mejor {
    color: green;
    font-weight: bold;
}
.peor {
    color: red;
    font-weight: bold;
}
.equal {
    color: gray;
}"""

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Análisis Estadístico - {metric_str}</title>
    <style>
{css_style}
    </style>
</head>
<body>
    <h1>Análisis Estadístico - {metric_str}</h1>
    <p>Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

    <div class="section">
        <h2>Resultados de la Prueba {test_info['Prueba']}</h2>
        <table>
            <tr>
                <th>Estadístico</th>
                <th>p-value</th>
                <th>Diferencia Significativa</th>
                <th>Distancia Crítica</th>
            </tr>
            <tr>
                <td>{test_info['Estadístico']:.4f}</td>
                <td>{test_info['p-value']:.4f}</td>
                <td>{test_info['Diferencia significativa']}</td>
                <td>{test_info['Distancia crítica']}</td>
            </tr>
        </table>

        <p>
            <strong>Interpretación:</strong>
            {
            "La prueba " + test_info['Prueba'] + " indica que hay diferencias estadísticamente significativas entre los algoritmos comparados (p-value < " + str(alpha) + ")."
            if test_info['Diferencia significativa'] == 'Sí' else
            "La prueba " + test_info['Prueba'] + " NO indica diferencias estadísticamente significativas entre los algoritmos comparados (p-value >= " + str(alpha) + ")."
            }
        </p>
    </div>

    <div class="section">
        <h2>Ranking de Algoritmos</h2>
        <table>
            <tr>
                <th>Posición</th>
                <th>Algoritmo</th>
                <th>Rango Promedio</th>
            </tr>"""

        # Añadir filas para cada algoritmo (ordenados por rango)
        if "error" not in friedman_result:
            algo_ranks = [
                (algo, friedman_result["rank_dict"][algo])
                for algo in friedman_result["algorithms"]
            ]
            algo_ranks.sort(key=lambda x: x[1])

            for i, (algo, rank) in enumerate(algo_ranks):
                html_content += f"""
            <tr>
                <td>{i+1}</td>
                <td>{algo}</td>
                <td>{rank:.2f}</td>
            </tr>"""

        html_content += """
        </table>
    </div>

    <div class="section">
        <h2>Comparaciones entre Algoritmos</h2>
        <p>Simbología: + (mejor), - (peor), = (no hay diferencia significativa)</p>
        <table>
            <tr>
                <th>Algoritmo</th>
                <th>Rango</th>"""

        # Añadir columnas para cada algoritmo
        if "error" not in friedman_result:
            for algo in algo_ranks:
                html_content += f"<th>{algo[0]}</th>"

        html_content += """
            </tr>"""

        # Añadir filas para cada algoritmo
        if "error" not in friedman_result:
            for i, (algo_i, rank_i) in enumerate(algo_ranks):
                html_content += f"""
            <tr>
                <td>{algo_i}</td>
                <td>{rank_i:.2f}</td>"""

                for j, (algo_j, _) in enumerate(algo_ranks):
                    if i == j:
                        html_content += "<td>-</td>"
                    else:
                        p_value = posthoc_matrix.loc[algo_i, algo_j]
                        effect = cliff_delta.loc[algo_i, algo_j]

                        if p_value < alpha:
                            if rank_i < friedman_result["rank_dict"][algo_j]:
                                symbol = '<span class="mejor">+</span>'  # Mejor
                            else:
                                symbol = '<span class="peor">-</span>'  # Peor
                        else:
                            symbol = '<span class="equal">=</span>'  # No diferencia significativa

                        html_content += f"""
                <td>{symbol} (p={p_value:.3f}, d={effect:.3f})</td>"""

                html_content += """
            </tr>"""

        html_content += """
        </table>
    </div>

    <div class="section">
        <h2>Visualizaciones</h2>

        <div class="figure">
            <img src="data:image/png;base64,{cd_img}" alt="Critical Difference Diagram">
            <div class="caption">Figura 1: Diagrama de diferencia crítica</div>
        </div>

        <div class="figure">
            <img src="data:image/png;base64,{rank_img}" alt="Rank Distribution">
            <div class="caption">Figura 2: Distribución de rangos por algoritmo</div>
        </div>

        <div class="figure">
            <img src="data:image/png;base64,{posthoc_img}" alt="Post-hoc Test p-values">
            <div class="caption">Figura 3: Matriz de p-values de prueba post-hoc</div>
        </div>

        <div class="figure">
            <img src="data:image/png;base64,{effect_img}" alt="Effect Size - Cliff's Delta">
            <div class="caption">Figura 4: Tamaño del efecto (Cliff's Delta)</div>
        </div>

        <div class="figure">
            <img src="data:image/png;base64,{vd_img}" alt="Effect Size - Vargha-Delaney A">
            <div class="caption">Figura 5: Tamaño del efecto (Vargha-Delaney A)</div>
        </div>
    </div>

    <div class="section">
        <h2>Interpretación de los Resultados</h2>
        <p>
            Este análisis estadístico para la métrica <strong>{metric_str}</strong>
            {
            "muestra diferencias significativas entre los algoritmos. "
            if test_info['Diferencia significativa'] == 'Sí' else
            "no muestra diferencias significativas entre los algoritmos. "
            }
        </p>

        <p>
            <strong>Principales conclusiones:</strong>
        </p>
        <ul>"""

        # Preparar diccionario para el formato

        # Añadir conclusiones basadas en los resultados
        if (
            "error" not in friedman_result
            and test_info["Diferencia significativa"] == "Sí"
        ):
            best_algo = algo_ranks[0][0]
            worst_algo = algo_ranks[-1][0]

            html_content += f"""
            <li>El algoritmo <strong>{best_algo}</strong> obtuvo el mejor ranking promedio ({algo_ranks[0][1]:.2f}).</li>
            <li>El algoritmo <strong>{worst_algo}</strong> obtuvo el peor ranking promedio ({algo_ranks[-1][1]:.2f}).</li>"""

            # Buscar algoritmos que no sean significativamente diferentes del mejor
            not_diff_from_best = []
            for algo_j, _ in algo_ranks[1:]:
                if posthoc_matrix.loc[best_algo, algo_j] >= alpha:
                    not_diff_from_best.append(algo_j)

            if not_diff_from_best:
                html_content += f"""
            <li>Los algoritmos {', '.join(not_diff_from_best)} no son significativamente diferentes del mejor algoritmo ({best_algo}).</li>"""
        else:
            html_content += """
            <li>No se encontraron diferencias estadísticamente significativas entre los algoritmos comparados.</li>"""

        html_content += """
        </ul>
    </div>
</body>
</html>"""

        # Guardar el informe directamente sin usar format() que puede causar problemas con f-strings
        with open(output_file, "w") as f:
            f.write(
                html_content.replace("{cd_img}", cd_img)
                .replace("{rank_img}", rank_img)
                .replace("{posthoc_img}", posthoc_img)
                .replace("{effect_img}", effect_img)
                .replace("{vd_img}", vd_img)
            )

        return output_file

    @staticmethod
    def run_comprehensive_statistical_analysis(
        benchmark_results, metrics=None, alpha=0.05, output_dir=None
    ):
        """
        Ejecuta un análisis estadístico completo para múltiples métricas.

        Args:
            benchmark_results: Lista de objetos BenchmarkResult
            metrics: Lista de métricas a analizar
            alpha: Nivel de significancia
            output_dir: Directorio para guardar los resultados

        Returns:
            Lista de rutas a los informes generados
        """
        if metrics is None:
            metrics = ["best_fitness", "mean_fitness", "execution_time"]

        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"results/statistical_analysis_{timestamp}"

        # Crear directorio si no existe
        os.makedirs(output_dir, exist_ok=True)

        # Preparar datos para cada métrica y generar informes
        report_paths = []
        successful_metrics = []

        for metric in metrics:
            try:
                print(f"Procesando métrica: {metric}")
                data_df = StatisticalAnalysis.prepare_data_for_statistics(
                    benchmark_results, metric=metric
                )

                # Verificar que hay datos suficientes
                if len(data_df) > 0:
                    # Verificar la calidad de los datos
                    has_nan = data_df["Value"].isna().any()
                    if has_nan:
                        print(
                            f"⚠️ Advertencia: La métrica {metric} contiene valores NaN. Se eliminarán antes del análisis."
                        )
                        data_df = data_df.dropna(subset=["Value"])

                    # Intentar convertir Value a float (en caso de que haya strings o tipos no numéricos)
                    try:
                        data_df["Value"] = data_df["Value"].astype(float)
                    except Exception as e:
                        print(
                            f"⚠️ Error al convertir datos para {metric} a float: {str(e)}"
                        )
                        # Intentar limpiar datos problemáticos
                        data_df = data_df[
                            pd.to_numeric(data_df["Value"], errors="coerce").notna()
                        ]
                        if len(data_df) == 0:
                            print(
                                f"⚠️ No quedan datos válidos para la métrica {metric} después de la limpieza"
                            )
                            continue
                        data_df["Value"] = data_df["Value"].astype(float)

                    # Verificar si hay suficientes datos después de la limpieza
                    if (
                        len(data_df) < 10
                    ):  # Umbral arbitrario para tener datos significativos
                        print(
                            f"⚠️ Pocos datos ({len(data_df)}) para la métrica {metric} después de la limpieza"
                        )

                    # Generar informe
                    output_file = os.path.join(output_dir, f"report_{metric}.html")
                    try:
                        report_path = (
                            StatisticalAnalysis.generate_statistical_analysis_report(
                                data_df,
                                metric=metric,
                                alpha=alpha,
                                output_file=output_file,
                            )
                        )

                        report_paths.append(report_path)
                        successful_metrics.append(metric)
                        print(f"✅ Informe generado para {metric}")
                    except Exception as report_error:
                        print(
                            f"⚠️ Error al generar informe para {metric}: {str(report_error)}"
                        )
                else:
                    print(f"⚠️ No hay datos suficientes para la métrica {metric}")
            except Exception as e:
                print(f"⚠️ Error al procesar la métrica {metric}: {str(e)}")

        # Verificar si se generó algún informe
        if not report_paths:
            error_path = os.path.join(output_dir, "error_report.html")
            with open(error_path, "w") as f:
                f.write(
                    f"""
                <!DOCTYPE html>
                <html>
                <head><title>Error en Análisis Estadístico</title></head>
                <body>
                <h1>Error en el Análisis Estadístico</h1>
                <p>No se pudo generar ningún informe estadístico para las métricas proporcionadas.</p>
                <p>Métricas intentadas: {', '.join(metrics)}</p>
                <p>Es posible que los datos no sean suficientes o tengan problemas de formato.</p>
                </body>
                </html>
                """
                )
            return [error_path]

        # Generar índice HTML
        index_path = os.path.join(output_dir, "index.html")

        # Contenido del índice - manteniendo el CSS en formato inline
        index_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Análisis Estadístico Completo</title>
    <style>
body {{
    font-family: "Arial", sans-serif;
    margin: 20px;
    line-height: 1.6;
}}
h1, h2, h3 {{
    color: #2c3e50;
}}
ul {{
    list-style-type: none;
    padding: 0;
}}
li {{
    margin-bottom: 10px;
}}
a {{
    text-decoration: none;
    color: #3498db;
    padding: 5px 10px;
    border: 1px solid #3498db;
    border-radius: 5px;
}}
a:hover {{
    background-color: #3498db;
    color: white;
}}
.warning {{
    color: #e67e22;
    background-color: #fff3e0;
    padding: 10px;
    border-left: 5px solid #e67e22;
    margin-bottom: 20px;
}}
    </style>
</head>
<body>
    <h1>Análisis Estadístico Completo</h1>
    <p>Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

    {f'<div class="warning"><p>⚠️ Algunas métricas no pudieron ser analizadas: {", ".join(set(metrics) - set(successful_metrics))}</p></div>' if len(successful_metrics) < len(metrics) else ''}

    <h2>Informes por Métrica</h2>
    <ul>"""

        # Añadir enlaces a los informes generados
        for metric in successful_metrics:
            rel_path = f"report_{metric}.html"
            index_content += f"""
                <li><a href="{rel_path}">{metric.capitalize()}</a></li>
            """

        index_content += """
            </ul>
        </body>
        </html>
        """

        # Guardar el índice
        with open(index_path, "w") as f:
            f.write(index_content)

        report_paths.append(index_path)

        return report_paths
