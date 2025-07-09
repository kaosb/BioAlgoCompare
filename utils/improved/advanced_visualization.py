#!/usr/bin/env python3
"""
Módulo para visualizaciones estadísticas avanzadas para el análisis de algoritmos
metaheurísticos. Proporciona gráficos de ranking, CD diagrams, violín plots
y otras visualizaciones para el análisis riguroso.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from scipy import stats
import os
from datetime import datetime
import logging
import warnings

# Ignorar advertencias de matplotlib
warnings.filterwarnings("ignore", category=UserWarning)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("advanced_visualization")

# Colores para algoritmos
ALGORITHM_COLORS = {
    "HOA": "#1f77b4",
    "APO": "#ff7f0e",
    "EGTO": "#2ca02c",
    "FGO": "#d62728",
    "FOA": "#9467bd",
    "HOA_OPT": "#1f77b4",
    "APO_OPT": "#ff7f0e",
    "EGTO_OPT": "#2ca02c",
    "FGO_OPT": "#d62728",
    "FOA_OPT": "#9467bd",
}


def set_publication_style():
    """Configura el estilo de matplotlib para publicaciones científicas"""
    plt.style.use("seaborn-whitegrid")
    plt.rcParams["figure.figsize"] = (10, 6)
    plt.rcParams["font.size"] = 12
    plt.rcParams["axes.labelsize"] = 14
    plt.rcParams["axes.titlesize"] = 16
    plt.rcParams["xtick.labelsize"] = 12
    plt.rcParams["ytick.labelsize"] = 12
    plt.rcParams["legend.fontsize"] = 12
    plt.rcParams["figure.titlesize"] = 18


def create_result_distribution_plot(
    data, metric="fitness", by="algorithm", output_dir=None
):
    """
    Crea gráficos de violín o boxplot para visualizar la distribución de los resultados.

    Args:
        data: DataFrame con los resultados (debe tener columnas algorithm, instance, run, fitness)
        metric: Métrica a visualizar (fitness, time, etc.)
        by: Agrupar por 'algorithm' o 'instance'
        output_dir: Directorio para guardar las figuras

    Returns:
        Rutas a las figuras generadas
    """
    set_publication_style()
    figures = []

    if by == "algorithm":
        # Agrupar por algoritmo (una figura por instancia)
        instances = data["instance"].unique()

        for instance in instances:
            instance_data = data[data["instance"] == instance]

            # Crear figura
            plt.figure(figsize=(12, 7))

            # Crear violin plot
            sns.violinplot(
                x="algorithm",
                y=metric,
                data=instance_data,
                palette=ALGORITHM_COLORS,
                inner="box",
                cut=0,
            )

            # Añadir swarm plot para ver distribución de puntos
            sns.swarmplot(
                x="algorithm",
                y=metric,
                data=instance_data,
                color="black",
                alpha=0.5,
                size=3,
            )

            # Personalizar gráfico
            plt.title(f"Distribución de {metric} para instancia {instance}")
            plt.ylabel(f"{metric.capitalize()}")
            plt.xlabel("Algoritmo")
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Guardar figura
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                fig_path = os.path.join(
                    output_dir, f"distribution_{instance}_{metric}.png"
                )
                plt.savefig(fig_path, dpi=300, bbox_inches="tight")
                figures.append(fig_path)

            plt.close()

    elif by == "instance":
        # Agrupar por instancia (una figura por algoritmo)
        algorithms = data["algorithm"].unique()

        for algorithm in algorithms:
            algo_data = data[data["algorithm"] == algorithm]

            # Crear figura
            plt.figure(figsize=(12, 7))

            # Crear violin plot
            sns.violinplot(
                x="instance", y=metric, data=algo_data, inner="box", cut=0
            )

            # Añadir swarm plot
            sns.swarmplot(
                x="instance", y=metric, data=algo_data, color="black", alpha=0.5, size=3
            )

            # Personalizar gráfico
            plt.title(f"Distribución de {metric} para algoritmo {algorithm}")
            plt.ylabel(f"{metric.capitalize()}")
            plt.xlabel("Instancia")
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Guardar figura
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                fig_path = os.path.join(
                    output_dir, f"distribution_{algorithm}_{metric}.png"
                )
                plt.savefig(fig_path, dpi=300, bbox_inches="tight")
                figures.append(fig_path)

            plt.close()

    return figures


def create_convergence_plot(
    results, instances=None, algorithms=None, confidence_interval=0.95, output_dir=None
):
    """
    Crea gráficos de convergencia con intervalos de confianza.

    Args:
        results: Lista de objetos BenchmarkResult o EnhancedBenchmarkResult
        instances: Lista de instancias a incluir (None = todas)
        algorithms: Lista de algoritmos a incluir (None = todos)
        confidence_interval: Nivel de confianza para intervalos (0-1)
        output_dir: Directorio para guardar las figuras

    Returns:
        Rutas a las figuras generadas
    """
    set_publication_style()
    figures = []

    # Filtrar resultados
    filtered_results = results
    if instances:
        filtered_results = [r for r in filtered_results if r.instance_name in instances]
    if algorithms:
        filtered_results = [
            r for r in filtered_results if r.algorithm_name in algorithms
        ]

    # Agrupar por instancia
    instance_results = {}
    for result in filtered_results:
        if result.instance_name not in instance_results:
            instance_results[result.instance_name] = []
        instance_results[result.instance_name].append(result)

    # Z-score para el intervalo de confianza
    z = stats.norm.ppf((1 + confidence_interval) / 2)

    for instance, inst_results in instance_results.items():
        plt.figure(figsize=(12, 7))

        for result in inst_results:
            if not result.convergence_curves:
                continue

            # Encontrar longitud mínima común para todas las curvas
            curves = [curve for curve in result.convergence_curves if curve]
            if not curves:
                continue

            min_length = min(len(curve) for curve in curves)

            # Truncar curvas a la misma longitud
            truncated_curves = [curve[:min_length] for curve in curves]

            # Convertir a array numpy
            curves_array = np.array(truncated_curves)

            # Calcular media y desviación estándar
            mean_curve = np.mean(curves_array, axis=0)
            std_curve = np.std(curves_array, axis=0)

            # Calcular intervalo de confianza
            n = len(curves)
            ci = z * std_curve / np.sqrt(n)

            # Graficar
            x = np.arange(min_length)
            color = ALGORITHM_COLORS.get(result.algorithm_name, None)

            plt.plot(x, mean_curve, label=result.algorithm_name, color=color)
            plt.fill_between(
                x, mean_curve - ci, mean_curve + ci, alpha=0.2, color=color
            )

        # Personalizar gráfico
        plt.title(f"Curvas de convergencia - {instance}")
        plt.xlabel("Iteración")
        plt.ylabel("Fitness")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()

        # Guardar figura
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            fig_path = os.path.join(output_dir, f"convergence_{instance}.png")
            plt.savefig(fig_path, dpi=300, bbox_inches="tight")
            figures.append(fig_path)

        plt.close()

    return figures


def create_cd_diagram(ranks, names, cd=None, output_file=None):
    """
    Crea un diagrama de diferencia crítica (CD) para visualizar los rankings de algoritmos.

    Args:
        ranks: Array con los rankings promedio
        names: Lista con los nombres de los algoritmos
        cd: Valor de diferencia crítica (None = no mostrar)
        output_file: Ruta para guardar la figura

    Returns:
        Ruta a la figura generada
    """
    set_publication_style()

    # Ordenar algoritmos por ranking
    sorted_indices = np.argsort(ranks)
    sorted_ranks = ranks[sorted_indices]
    sorted_names = [names[i] for i in sorted_indices]

    # Crear figura
    fig, ax = plt.subplots(figsize=(10, 6))

    # Dibujar línea horizontal
    ax.plot([0, max(ranks) + 1], [0, 0], "k-", linewidth=2)

    # Dibujar posiciones
    ax.scatter(
        sorted_ranks, np.zeros_like(sorted_ranks), marker="o", s=100, color="black"
    )

    # Añadir nombres de algoritmos
    for i, (rank, name) in enumerate(zip(sorted_ranks, sorted_names)):
        ax.annotate(
            name,
            xy=(rank, 0),
            xytext=(rank, -0.3 if i % 2 == 0 else 0.3),
            ha="center",
            va="center",
            fontsize=12,
        )

    # Añadir diferencia crítica si se proporciona
    if cd is not None:
        # Dibujar CD en la parte superior
        ax.plot([1, 1 + cd], [0.2, 0.2], "k-")
        ax.plot([1, 1], [0.15, 0.25], "k-")
        ax.plot([1 + cd, 1 + cd], [0.15, 0.25], "k-")
        ax.text(1 + cd / 2, 0.3, f"CD = {cd:.2f}", ha="center")

        # Conectar algoritmos no significativamente diferentes
        for i in range(len(sorted_ranks)):
            for j in range(i + 1, len(sorted_ranks)):
                if sorted_ranks[j] - sorted_ranks[i] <= cd:
                    # Dibujar línea conectando algoritmos
                    y_pos = -0.1 - 0.05 * (j - i)
                    ax.plot(
                        [sorted_ranks[i], sorted_ranks[j]],
                        [y_pos, y_pos],
                        "k-",
                        linewidth=1.5,
                    )

    # Personalizar gráfico
    ax.set_xlim(0, max(ranks) + 1)
    ax.set_ylim(-0.5, 0.5)
    ax.set_yticks([])
    ax.set_xlabel("Ranking Promedio")
    ax.set_title("Diagrama de Diferencia Crítica")

    # Eliminar bordes
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Guardar figura
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, dpi=300, bbox_inches="tight")

    plt.close()
    return output_file


def create_heatmap(data, row_var, col_var, value_var, title=None, output_file=None):
    """
    Crea un mapa de calor para visualizar la relación entre dos variables.

    Args:
        data: DataFrame con los datos
        row_var: Variable para las filas
        col_var: Variable para las columnas
        value_var: Variable para los valores (colores)
        title: Título del gráfico
        output_file: Ruta para guardar la figura

    Returns:
        Ruta a la figura generada
    """
    set_publication_style()

    # Crear pivot table
    pivot = data.pivot_table(
        index=row_var, columns=col_var, values=value_var, aggfunc="mean"
    )

    # Crear figura
    plt.figure(figsize=(12, 8))

    # Crear mapa de calor
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".2f",
        cmap="viridis",
        linewidths=0.5,
        cbar_kws={"label": value_var},
    )

    # Personalizar gráfico
    if title:
        plt.title(title)
    else:
        plt.title(f"{value_var} por {row_var} y {col_var}")

    plt.tight_layout()

    # Guardar figura
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, dpi=300, bbox_inches="tight")

    plt.close()
    return output_file


def create_radar_chart(data, categories, group_var, value_var, output_file=None):
    """
    Crea un gráfico de radar para comparar algoritmos en múltiples dimensiones.

    Args:
        data: DataFrame con los datos
        categories: Lista de categorías para el radar (instancias o métricas)
        group_var: Variable para agrupar (normalmente 'algorithm')
        value_var: Variable para los valores
        output_file: Ruta para guardar la figura

    Returns:
        Ruta a la figura generada
    """
    set_publication_style()

    # Agrupar datos
    grouped = data.pivot_table(
        index=group_var, columns=categories, values=value_var, aggfunc="mean"
    )

    # Normalizar los datos (min-max scaling para cada categoría)
    normalized = grouped.copy()
    for col in normalized.columns:
        normalized[col] = (normalized[col] - normalized[col].min()) / (
            normalized[col].max() - normalized[col].min()
        )

    # Preparar gráfico
    len(grouped.index)
    n_cats = len(categories)

    # Calcular ángulos para cada categoría
    angles = np.linspace(0, 2 * np.pi, n_cats, endpoint=False).tolist()
    angles += angles[:1]  # Cerrar el círculo

    # Crear figura
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    # Dibujar un eje por categoría y añadir etiquetas
    plt.xticks(angles[:-1], categories, size=12)

    # Dibujar líneas de referencia (polígonos en el fondo)
    ax.set_rlabel_position(0)
    plt.yticks([0.25, 0.5, 0.75], ["0.25", "0.50", "0.75"], color="grey", size=10)
    plt.ylim(0, 1)

    # Graficar cada grupo
    for i, group in enumerate(grouped.index):
        values = normalized.loc[group].values.flatten().tolist()
        values += values[:1]  # Cerrar el círculo

        color = ALGORITHM_COLORS.get(group, None)
        ax.plot(
            angles, values, linewidth=2, linestyle="solid", label=group, color=color
        )
        ax.fill(angles, values, alpha=0.1, color=color)

    # Añadir leyenda
    plt.legend(loc="upper right", bbox_to_anchor=(0.1, 0.1))

    # Personalizar gráfico
    plt.title(f"Comparación de {group_var} por {value_var}", size=18, y=1.1)

    # Guardar figura
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, dpi=300, bbox_inches="tight")

    plt.close()
    return output_file


def create_full_visualization_set(results, data_df, output_dir=None):
    """
    Crea un conjunto completo de visualizaciones para el análisis de algoritmos.

    Args:
        results: Lista de objetos BenchmarkResult o EnhancedBenchmarkResult
        data_df: DataFrame con todos los datos a nivel de ejecución individual
        output_dir: Directorio para guardar las figuras

    Returns:
        Diccionario con rutas a las figuras generadas
    """
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"results/visualizations_{timestamp}"

    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Generando visualizaciones en {output_dir}")

    # Crear subdirectorios
    dirs = {
        "distribution": os.path.join(output_dir, "distribution"),
        "convergence": os.path.join(output_dir, "convergence"),
        "ranking": os.path.join(output_dir, "ranking"),
        "heatmap": os.path.join(output_dir, "heatmap"),
        "radar": os.path.join(output_dir, "radar"),
    }

    for d in dirs.values():
        os.makedirs(d, exist_ok=True)

    # Generar visualizaciones
    figures = {}

    # 1. Distribución de resultados
    logger.info("Generando gráficos de distribución...")
    figures["distribution_by_algorithm"] = create_result_distribution_plot(
        data_df, metric="fitness", by="algorithm", output_dir=dirs["distribution"]
    )

    figures["distribution_by_instance"] = create_result_distribution_plot(
        data_df, metric="fitness", by="instance", output_dir=dirs["distribution"]
    )

    # 2. Curvas de convergencia
    logger.info("Generando gráficos de convergencia...")
    figures["convergence"] = create_convergence_plot(
        results, output_dir=dirs["convergence"]
    )

    # 3. Diagramas CD (Critical Difference)
    logger.info("Generando diagramas de ranking...")

    # Preparar datos de ranking
    instances = list(set(r.instance_name for r in results))
    algorithms = list(set(r.algorithm_name for r in results))

    ranks_matrix = np.zeros((len(instances), len(algorithms)))

    for i, instance in enumerate(instances):
        instance_results = [r for r in results if r.instance_name == instance]

        # Calcular rankings
        fitness_values = [r.mean_fitness for r in instance_results]
        ranks = np.argsort(np.argsort(fitness_values))

        # Asignar a la matriz
        for j, r in enumerate(instance_results):
            algo_idx = algorithms.index(r.algorithm_name)
            ranks_matrix[i, algo_idx] = ranks[j] + 1

    # Calcular ranking promedio
    avg_ranks = np.mean(ranks_matrix, axis=0)

    # CD diagram global
    cd_value = 1.96 * np.sqrt(
        (len(algorithms) * (len(algorithms) + 1)) / (6 * len(instances))
    )
    figures["cd_diagram"] = create_cd_diagram(
        avg_ranks,
        algorithms,
        cd=cd_value,
        output_file=os.path.join(dirs["ranking"], "cd_diagram.png"),
    )

    # 4. Heatmaps
    logger.info("Generando mapas de calor...")

    # Heatmap de fitness por algoritmo e instancia
    summary_df = pd.DataFrame(
        [
            {
                "Algorithm": r.algorithm_name,
                "Instance": r.instance_name,
                "Best": r.best_fitness,
                "Mean": r.mean_fitness,
                "Std": r.std_fitness,
                "Time": r.mean_time,
            }
            for r in results
        ]
    )

    figures["heatmap_mean"] = create_heatmap(
        summary_df,
        "Algorithm",
        "Instance",
        "Mean",
        title="Fitness Promedio por Algoritmo e Instancia",
        output_file=os.path.join(dirs["heatmap"], "heatmap_mean_fitness.png"),
    )

    figures["heatmap_best"] = create_heatmap(
        summary_df,
        "Algorithm",
        "Instance",
        "Best",
        title="Mejor Fitness por Algoritmo e Instancia",
        output_file=os.path.join(dirs["heatmap"], "heatmap_best_fitness.png"),
    )

    figures["heatmap_time"] = create_heatmap(
        summary_df,
        "Algorithm",
        "Instance",
        "Time",
        title="Tiempo de Ejecución por Algoritmo e Instancia",
        output_file=os.path.join(dirs["heatmap"], "heatmap_time.png"),
    )

    # 5. Radar Charts
    logger.info("Generando gráficos de radar...")

    # Normalizar datos para radar chart (se requiere que valores más bajos sean mejores)
    radar_df = summary_df.copy()
    radar_df["Mean"] = (
        1 / radar_df["Mean"]
    )  # Invertir para que valores más altos sean mejores

    figures["radar"] = create_radar_chart(
        radar_df,
        instances,
        "Algorithm",
        "Mean",
        output_file=os.path.join(dirs["radar"], "radar_chart.png"),
    )

    logger.info(
        f"Visualizaciones generadas: {sum(len(f) for f in figures.values())} figuras"
    )

    return figures


# Función auxiliar para crear informe HTML con todas las visualizaciones
def create_visual_report(figures, output_file=None):
    """
    Crea un informe HTML con todas las visualizaciones generadas.

    Args:
        figures: Diccionario con rutas a las figuras
        output_file: Ruta para el archivo HTML

    Returns:
        Ruta al archivo HTML generado
    """
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"results/visual_report_{timestamp}.html"

    # Preparar contenido HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Informe Visual de Análisis</title>
        <style>
            body {{
                font-family: "Arial", sans-serif;
                margin: 20px;
                line-height: 1.6;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            .figure {{
                margin: 20px 0;
                text-align: center;
            }}
            .figure img {{
                max-width: 100%;
                height: auto;
                border: 1px solid #ddd;
            }}
            .caption {{
                margin-top: 10px;
                font-style: italic;
                color: #666;
            }}
            .section {{
                margin-bottom: 30px;
            }}
            .navbar {{
                position: fixed;
                top: 0;
                width: 100%;
                background-color: #2c3e50;
                padding: 10px 0;
                z-index: 1000;
                left: 0;
            }}
            .navbar a {{
                color: white;
                padding: 10px 15px;
                text-decoration: none;
                display: inline-block;
            }}
            .navbar a:hover {{
                background-color: #1a252f;
            }}
            .content {{
                margin-top: 60px;
            }}
        </style>
    </head>
    <body>
        <div class="navbar">
            <a href="#distribution">Distribución</a>
            <a href="#convergence">Convergencia</a>
            <a href="#ranking">Ranking</a>
            <a href="#heatmap">Heatmaps</a>
            <a href="#radar">Radar</a>
        </div>

        <div class="content">
            <h1>Informe Visual de Análisis</h1>
            <p>Generado el: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    """

    # Sección de distribución
    if "distribution_by_algorithm" in figures:
        html_content += """
            <div class="section" id="distribution">
                <h2>Distribución de Resultados</h2>
                <p>Estos gráficos muestran la distribución de los valores de fitness para cada algoritmo y cada instancia.</p>
        """

        for fig_path in figures["distribution_by_algorithm"]:
            fig_name = os.path.basename(fig_path)
            instance = fig_name.split("_")[1]
            html_content += f"""
                <div class="figure">
                    <h3>Instancia: {instance}</h3>
                    <img src="{fig_path}" alt="Distribución - {instance}">
                    <p class="caption">Distribución de fitness por algoritmo para la instancia {instance}</p>
                </div>
            """

        html_content += """
            </div>
        """

    # Sección de convergencia
    if "convergence" in figures:
        html_content += """
            <div class="section" id="convergence">
                <h2>Curvas de Convergencia</h2>
                <p>Estos gráficos muestran la evolución del fitness a lo largo de las iteraciones, con intervalos de confianza.</p>
        """

        for fig_path in figures["convergence"]:
            fig_name = os.path.basename(fig_path)
            instance = fig_name.split("_")[1].split(".")[0]
            html_content += f"""
                <div class="figure">
                    <h3>Convergencia - {instance}</h3>
                    <img src="{fig_path}" alt="Convergencia - {instance}">
                    <p class="caption">Curvas de convergencia para la instancia {instance}</p>
                </div>
            """

        html_content += """
            </div>
        """

    # Sección de ranking
    if "cd_diagram" in figures:
        html_content += """
            <div class="section" id="ranking">
                <h2>Análisis de Ranking</h2>
                <p>Este diagrama muestra el ranking promedio de los algoritmos y su diferencia crítica.</p>
        """

        html_content += f"""
            <div class="figure">
                <h3>Diagrama de Diferencia Crítica</h3>
                <img src="{figures['cd_diagram']}" alt="CD Diagram">
                <p class="caption">
                    Diagrama de diferencia crítica (CD). Algoritmos conectados por una línea no son significativamente diferentes.
                    Los algoritmos están ordenados de mejor (izquierda) a peor (derecha) según su ranking promedio.
                </p>
            </div>
        """

        html_content += """
            </div>
        """

    # Sección de heatmaps
    if "heatmap_mean" in figures:
        html_content += """
            <div class="section" id="heatmap">
                <h2>Mapas de Calor</h2>
                <p>Estos mapas muestran la relación entre algoritmos e instancias para diferentes métricas.</p>
        """

        for key in ["heatmap_mean", "heatmap_best", "heatmap_time"]:
            if key in figures:
                title = {
                    "heatmap_mean": "Fitness Promedio",
                    "heatmap_best": "Mejor Fitness",
                    "heatmap_time": "Tiempo de Ejecución",
                }[key]

                html_content += f"""
                    <div class="figure">
                        <h3>{title}</h3>
                        <img src="{figures[key]}" alt="{title}">
                        <p class="caption">Mapa de calor de {title.lower()} por algoritmo e instancia</p>
                    </div>
                """

        html_content += """
            </div>
        """

    # Sección de radar
    if "radar" in figures:
        html_content += """
            <div class="section" id="radar">
                <h2>Gráfico de Radar</h2>
                <p>Este gráfico muestra el rendimiento relativo de cada algoritmo en diferentes instancias.</p>
        """

        html_content += f"""
            <div class="figure">
                <h3>Comparación de Algoritmos</h3>
                <img src="{figures['radar']}" alt="Radar Chart">
                <p class="caption">
                    Gráfico de radar que muestra el rendimiento normalizado de cada algoritmo en las diferentes instancias.
                    Valores más alejados del centro indican mejor rendimiento relativo.
                </p>
            </div>
        """

        html_content += """
            </div>
        """

    # Cerrar HTML
    html_content += """
        </div>
    </body>
    </html>
    """

    # Guardar archivo
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        f.write(html_content)

    logger.info(f"Informe visual generado: {output_file}")

    return output_file
