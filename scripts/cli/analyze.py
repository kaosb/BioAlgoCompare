#!/usr/bin/env python3
"""
Script unificado para análisis de algoritmos metaheurísticos.
Combina las funcionalidades de:
- analyze_results.py: Análisis básico y benchmarking
- analyze_csv.py: Análisis de archivos CSV de resultados
- analyze_1000runs.py: Análisis estadístico riguroso con 1000 ejecuciones
- analyze_massive.py: Análisis masivo con checkpointing
"""

import click
import os
import json
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import logging
from pathlib import Path
import multiprocessing as mp
from math import sqrt
from scipy import stats
import sys

# Añadir el directorio raíz del proyecto al path para poder importar los módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("analyze.log"), logging.StreamHandler()],
)
logger = logging.getLogger("analyze")

# Importar utilidades
from utils.benchmarking import (
    BenchmarkResult, 
    BenchmarkRunner,
    BenchmarkVisualizer,
    OPTIMAL_VALUES, 
    create_benchmark_report,
    run_benchmark as benchmark_function,
    save_benchmark_results,
    load_benchmark_results
)
from utils.statistics import UnifiedStatisticalAnalysis
from utils.vrp_operators import VRPOperators
from utils.improved.advanced_visualization import (
    create_full_visualization_set,
    create_visual_report,
)

# Importar problema
from problems.vrp import VRPProblem
from problems.vrp_v2 import VRPProblemV2

# Importar algoritmos
from algorithms.sho import SHO  # Previously HOA
from algorithms.apo import APO
from algorithms.egto import EGTO
from algorithms.fsa import FSA  # Previously FGO
from algorithms.foa import FOA
from algorithms.woa import WOA
from algorithms.hho import HHO
from algorithms.mrfo import MRFO
from algorithms.sma import SMA
from algorithms.gto import GTO
from algorithms.ewa import EWA
from algorithms.aha import AHA
from algorithms.rro import RRO
from algorithms.gvoa import GVOA
from algorithms.smo import SMO
from algorithms.opa import OPA

# Todos los algoritmos disponibles
ALGORITHMS = {
    "hoa": SHO,  # Previously HOA
    "sho": SHO,
    "apo": APO,
    "egto": EGTO,
    "fgo": FSA,  # Previously FGO
    "fsa": FSA,
    "foa": FOA,
    "woa": WOA,
    "hho": HHO,
    "mrfo": MRFO,
    "sma": SMA,
    "gto": GTO,
    "ewa": EWA,
    "aha": AHA,
    "rro": RRO,
    "gvoa": GVOA,
    "smo": SMO,
    "opa": OPA,
}


# Comando principal
@click.group()
def cli():
    """Herramienta unificada para análisis de algoritmos metaheurísticos."""
    pass


# Comando para ejecución estándar
@cli.command()
@click.option(
    "--algorithm",
    "-a",
    type=click.Choice(list(ALGORITHMS.keys()) + ["all"]),
    required=True,
    help="Algoritmo a ejecutar",
)
@click.option("--instance", "-i", required=True, help="Nombre de la instancia VRP")
@click.option("--iterations", "-n", default=100, help="Número de iteraciones")
@click.option("--population", "-pop", default=30, help="Tamaño de la población")
@click.option("--runs", "-r", default=1, help="Número de ejecuciones independientes")
@click.option(
    "--seed", "-s", default=None, type=int, help="Semilla para reproducibilidad"
)
@click.option("--visualize/--no-visualize", default=True, help="Visualizar resultados")
@click.option("--save/--no-save", default=True, help="Guardar resultados")
@click.option(
    "--parallel/--no-parallel", "-p", default=False, help="Ejecutar en paralelo"
)
def run(
    algorithm, instance, iterations, population, runs, seed, visualize, save, parallel
):
    """Ejecuta algoritmos de optimización para resolver problemas VRP."""
    # Importar el módulo para ejecución
    from scripts.run import main as run_main

    # Ejecutar con los parámetros proporcionados
    run_main(
        algorithm,
        instance,
        iterations,
        population,
        runs,
        seed,
        visualize,
        save,
        parallel,
    )


# Comando para análisis de resultados
@cli.command()
@click.option("--input", "-i", help="Ruta al archivo CSV o JSON de resultados")
@click.option(
    "--run-benchmark/--no-run-benchmark",
    default=False,
    help="Ejecutar nuevo benchmark en lugar de cargar resultados existentes",
)
@click.option(
    "--instances",
    "-inst",
    help='Instancias para el benchmark (lista separada por comas, ej: "P-n16-k8,E-n22-k4")',
)
@click.option(
    "--algorithms",
    "-a",
    help='Algoritmos para el benchmark (lista separada por comas, ej: "ewa,foa,egto")',
)
@click.option(
    "--runs", "-r", default=5, help="Número de ejecuciones por algoritmo/instancia"
)
@click.option(
    "--iterations", "-n", default=100, help="Número de iteraciones por ejecución"
)
@click.option("--population", "-p", default=30, help="Tamaño de población")
@click.option("--seed", "-s", default=42, help="Semilla para reproducibilidad")
@click.option("--parallel/--no-parallel", default=False, help="Usar ejecución paralela")
@click.option(
    "--optimize/--no-optimize",
    default=False,
    help="Aplicar optimización local a las soluciones",
)
@click.option(
    "--output-dir",
    "-o",
    default=None,
    help="Directorio de salida (por defecto se genera automáticamente)",
)
def benchmark(
    input,
    run_benchmark,
    instances,
    algorithms,
    runs,
    iterations,
    population,
    seed,
    parallel,
    optimize,
    output_dir,
):
    """
    Analiza resultados de algoritmos metaheurísticos y genera informes.
    """
    # Configurar directorio de salida
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"results/analysis_{timestamp}"

    os.makedirs(output_dir, exist_ok=True)

    # Determinar origen de los datos
    benchmark_results = []

    if run_benchmark:
        if not instances:
            instance_list = [
                "P-n16-k8",
                "E-n22-k4",
            ]  # Por defecto, usar instancias pequeñas
        else:
            instance_list = instances.split(",")

        if not algorithms:
            algo_list = [
                "hoa",
                "apo",
                "egto",
                "fgo",
                "foa",
            ]  # Por defecto, usar algoritmos principales
        else:
            algo_list = algorithms.split(",")

        # Preparar diccionario de algoritmos
        algo_dict = {algo: ALGORITHMS[algo] for algo in algo_list if algo in ALGORITHMS}

        # Ejecutar benchmark
        logger.info(
            f"Ejecutando benchmark con {len(algo_dict)} algoritmos en {len(instance_list)} instancias..."
        )
        benchmark_results = benchmark_function(
            algo_dict,
            instance_list,
            runs=runs,
            iterations=iterations,
            population=population,
            seed=seed,
            parallel=parallel,
        )

        # Guardar resultados del benchmark
        benchmark_path = os.path.join(output_dir, "benchmark_results.json")
        from utils.benchmarking import save_benchmark_results

        save_benchmark_results(benchmark_results, benchmark_path)
        logger.info(f"Resultados del benchmark guardados en {benchmark_path}")

    elif input:
        # Cargar resultados existentes
        if input.endswith(".json"):
            # Archivo JSON de benchmark
            from utils.benchmarking import load_benchmark_results

            benchmark_results = load_benchmark_results(input)
            logger.info(f"Cargados {len(benchmark_results)} resultados desde {input}")

        elif input.endswith(".csv"):
            # Archivo CSV de resultados
            try:
                df = pd.read_csv(input)

                # Renombrar columnas si es necesario para compatibilidad
                rename_map = {
                    "Best": "Best Fitness",
                    "Mean": "Mean Fitness",
                    "Time": "Execution Time (s)",
                    "Time_Std": "Time Std"
                }
                df.rename(columns=rename_map, inplace=True)

                # Agrupar por algoritmo e instancia
                grouped = df.groupby(["Algorithm", "Instance"])

                # Convertir a objetos BenchmarkResult
                for (algo, instance), group in grouped:
                    result = BenchmarkResult(algo, instance)

                    # Añadir datos de cada ejecución
                    for _, row in group.iterrows():
                        result.add_run(
                            row["Best Fitness"],
                            row["Execution Time (s)"],
                            [],  # No hay datos de convergencia disponibles
                        )

                    # Calcular métricas
                    result.compute_metrics()
                    benchmark_results.append(result)

                logger.info(
                    f"Cargados {len(benchmark_results)} resultados desde {input}"
                )

            except Exception as e:
                logger.error(f"Error al cargar resultados desde CSV: {str(e)}")
                return
        else:
            logger.error(f"Formato de archivo no soportado: {input}")
            return
    else:
        logger.error(
            "Debe especificar una fuente de datos (--input) o ejecutar un nuevo benchmark (--run-benchmark)"
        )
        return

    # Aplicar optimización local si se solicita
    if optimize and benchmark_results:
        logger.info("Aplicando optimización local a las soluciones...")

        # Para cada instancia, aplicar optimización local
        instances_set = set(result.instance_name for result in benchmark_results)

        for instance_name in instances_set:
            # Cargar problema
            instance_path = f"data/vrp/{instance_name}.vrp"
            if not os.path.exists(instance_path):
                logger.warning(
                    f"Advertencia: No se encontró la instancia {instance_name}, omitiendo optimización"
                )
                continue

            # Para cada algoritmo con resultados en esta instancia
            instance_results = [
                r for r in benchmark_results if r.instance_name == instance_name
            ]

            for result in instance_results:
                logger.info(
                    f"  Optimizando soluciones de {result.algorithm_name} para {instance_name}..."
                )

                # Crear un objeto BenchmarkResult para almacenar resultados optimizados
                optimized_result = BenchmarkResult(
                    result.algorithm_name + "_OPT",
                    result.instance_name,
                    runs=len(result.fitness_values),
                )

                # Para cada solución (con mejor fitness de cada run)
                for i, original_solution_data in enumerate(result.solutions):
                    # Determinar el tipo de problema y la solución
                    if isinstance(original_solution_data, list) and all(isinstance(r, list) for r in original_solution_data):
                        # Es una solución v2 (lista de rutas)
                        problem = VRPProblemV2(instance_path)
                        original_routes = original_solution_data
                    else:
                        # Es una solución v1 (array continuo)
                        problem = VRPProblem(instance_path)
                        original_routes, _, _ = problem.decode_solution(np.array(original_solution_data))

                    # Aplicar optimización local
                    optimized_routes = VRPOperators.optimize_all_routes(
                        original_routes,
                        problem.distance_matrix,
                        problem.demands,
                        problem.capacity,
                    )

                    # Aplicar optimización entre rutas
                    final_routes = VRPOperators.optimize_between_routes(
                        optimized_routes,
                        problem.distance_matrix,
                        problem.demands,
                        problem.capacity,
                    )

                    # Evaluar solución optimizada
                    optimized_distance, _ = VRPOperators.evaluate_solution(
                        final_routes,
                        problem.distance_matrix,
                        problem.demands,
                        problem.capacity,
                    )

                    # Calcular tiempo de optimización (simulado)
                    optimization_time = (
                        0.1 * len(original_routes) * len(original_routes[0]) if original_routes else 0.1
                    )

                    # Añadir al resultado optimizado
                    optimized_result.add_run(
                        optimized_distance,
                        result.execution_times[i] + optimization_time,
                        [],  # No hay curva de convergencia para la solución optimizada
                        final_routes # Almacenar la solución optimizada
                    )

                    # Visualizar comparación (solo para la primera solución)
                    if i == 0:
                        fig = VRPOperators.plot_routes_comparison(
                            original_routes,
                            final_routes,
                            problem,
                            title=f"Comparación: {result.algorithm_name} - {instance_name}",
                        )

                        # Guardar visualización
                        fig_path = os.path.join(
                            output_dir,
                            f"{result.algorithm_name}_{instance_name}_optimization.png",
                        )
                        fig.savefig(fig_path)
                        plt.close(fig)

                # Calcular métricas y añadir a resultados
                optimized_result.compute_metrics()
                benchmark_results.append(optimized_result)

                # Mostrar mejora
                improvement = (
                    (result.mean_fitness - optimized_result.mean_fitness)
                    / result.mean_fitness
                    * 100
                )
                logger.info(f"  Mejora promedio: {improvement:.2f}%")

    # Generar informe de benchmark
    logger.info("Generando informe de benchmark...")
    benchmark_report_path = os.path.join(output_dir, "benchmark_report.html")
    create_benchmark_report(benchmark_results, benchmark_report_path)
    logger.info(f"Informe de benchmark guardado en {benchmark_report_path}")

    # Realizar análisis estadístico
    logger.info("Ejecutando análisis estadístico...")

    metrics = ["best_fitness", "mean_fitness", "execution_time"]
    if any(r.gap_to_optimal is not None for r in benchmark_results):
        metrics.append("gap_to_optimal")

    # Verificar si hay suficientes datos para un análisis estadístico robusto
    if len(benchmark_results) < 2:
        logger.warning(
            "⚠️ Advertencia: Se requieren al menos 2 algoritmos para realizar análisis estadísticos comparativos."
        )
        logger.info("Se generará un informe descriptivo en su lugar.")

        # Generar solo el informe descriptivo
        try:
            report_path = create_benchmark_report(
                benchmark_results, os.path.join(output_dir, "benchmark_report.html")
            )
            logger.info(f"Informe descriptivo guardado en {report_path}")
        except Exception as e:
            logger.error(f"Error al generar el informe descriptivo: {str(e)}")
    else:
        # Generar informes estadísticos completos
        try:
            if len(benchmark_results) >= 2 and all(
                len(result.fitness_values) >= 5 for result in benchmark_results
            ):
                try:
                    # Llamar al análisis estadístico con manejo de errores para cada métrica
                    valid_metrics = []
                    for metric in metrics:
                        try:
                            # Verificar que hay datos para esta métrica
                            data_df = StatisticalAnalysis.prepare_data_for_statistics(
                                benchmark_results, metric=metric
                            )
                            if len(data_df) > 0:
                                valid_metrics.append(metric)
                            else:
                                logger.warning(
                                    f"⚠️ No hay datos suficientes para la métrica {metric}"
                                )
                        except Exception as metric_error:
                            logger.error(
                                f"⚠️ Error al preparar datos para la métrica {metric}: {str(metric_error)}"
                            )

                    if valid_metrics:
                        (
                            StatisticalAnalysis.run_comprehensive_statistical_analysis(
                                benchmark_results,
                                metrics=valid_metrics,
                                output_dir=output_dir,
                            )
                        )
                        logger.info(
                            f"Análisis estadístico completo. Informes guardados en {output_dir}"
                        )
                    else:
                        raise ValueError(
                            "No se pudieron procesar las métricas disponibles"
                        )
                except Exception as analysis_error:
                    logger.error(
                        f"⚠️ Error durante el análisis estadístico: {str(analysis_error)}"
                    )
                    # Continuar con el informe básico en caso de error
                    raise analysis_error
            else:
                logger.warning(
                    "⚠️ Datos insuficientes para un análisis estadístico completo."
                )
                logger.info(
                    "Para análisis rigurosos se recomiendan al menos 2 algoritmos con 5+ ejecuciones cada uno."
                )
                logger.info("Generando informe básico con las métricas disponibles...")

                # Generar informe básico con los datos disponibles
                report_path = create_benchmark_report(
                    benchmark_results,
                    os.path.join(output_dir, "benchmark_simple_report.html"),
                )
                logger.info(f"Informe básico guardado en {report_path}")
        except Exception as e:
            logger.error(f"⚠️ Error durante el análisis estadístico: {str(e)}")
            logger.info("Se intentará generar un informe básico en su lugar.")

            try:
                report_path = create_benchmark_report(
                    benchmark_results,
                    os.path.join(output_dir, "benchmark_fallback_report.html"),
                )
                logger.info(f"Informe básico guardado en {report_path}")
            except Exception as e2:
                logger.error(f"Error al generar el informe básico: {str(e2)}")
                logger.error(
                    "Por favor, verifique los datos de entrada e intente nuevamente con más ejecuciones o algoritmos."
                )


# Comando para benchmarking masivo
@cli.command()
@click.option(
    "--runs", "-r", default=1000, help="Número de ejecuciones por algoritmo/instancia"
)
@click.option(
    "--iterations", "-n", default=100, help="Número de iteraciones por ejecución"
)
@click.option("--population", "-p", default=40, help="Tamaño de población")
@click.option("--seed", "-s", default=42, help="Semilla para reproducibilidad")
@click.option(
    "--algorithm",
    "-a",
    multiple=True,
    type=click.Choice(list(ALGORITHMS.keys()) + ["all"]),
    default=["all"],
    help="Algoritmos a ejecutar",
)
@click.option(
    "--instances", "-i", multiple=True, help="Instancias a evaluar (sin extensión)"
)
@click.option("--parallel/--no-parallel", default=True, help="Ejecutar en paralelo")
@click.option(
    "--resume/--no-resume",
    default=True,
    help="Intentar reanudar benchmark interrumpido",
)
@click.option(
    "--output-dir",
    "-o",
    default=None,
    help="Directorio de salida (automático si no se especifica)",
)
def massive(
    runs,
    iterations,
    population,
    seed,
    algorithm,
    instances,
    parallel,
    resume,
    output_dir,
):
    """
    Ejecuta benchmarks masivos con 1000+ ejecuciones y análisis estadístico riguroso.
    """
    # Procesar algoritmos seleccionados
    if "all" in algorithm:
        selected_algorithms = ALGORITHMS.copy()
    else:
        selected_algorithms = {name: ALGORITHMS[name] for name in algorithm if name in ALGORITHMS}
    
    # Si no se especifican instancias, usar algunas por defecto
    if not instances:
        instances = ["E-n22-k4", "P-n16-k8", "A-n32-k5"]
    
    # Crear runner con configuración para ejecuciones masivas
    runner = BenchmarkRunner(
        output_dir=output_dir,
        parallel=parallel,
        checkpoint_interval=50,  # Checkpoint más frecuente para runs masivos
        verbose=True
    )
    
    # Ejecutar benchmark
    logger.info(f"Starting massive benchmark: {runs} runs per algorithm/instance")
    results = runner.run_benchmark(
        algorithms=selected_algorithms,
        instances=list(instances),
        runs=runs,
        iterations=iterations,
        population=population,
        seed=seed,
        resume=resume
    )
    
    # Generar reporte completo
    logger.info("Generating comprehensive report...")
    report_path = BenchmarkVisualizer.create_comprehensive_report(
        results,
        Path(runner.output_dir),
        include_stats=True
    )
    
    logger.info(f"Massive benchmark completed. Report: {report_path}")


# Comando para análisis de archivos CSV existentes
@cli.command()
@click.argument("csv_file", type=click.Path(exists=True))
@click.option(
    "--output-dir",
    "-o",
    default=None,
    help="Directorio de salida (por defecto: results/analysis_csv)",
)
def analyze_csv(csv_file, output_dir):
    """
    Analiza resultados de CSV y genera visualizaciones estadísticas.
    """
    # Determinar directorio de salida
    if output_dir is None:
        output_dir = "results/analysis_csv"

    # Crear directorio de salida
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Directorio de análisis: {output_dir}")

    # Cargar datos
    logger.info(f"Cargando datos desde {csv_file}")
    df = pd.read_csv(csv_file)

    # Renombrar columnas si es necesario para compatibilidad
    rename_map = {
        "Best": "Best Fitness",
        "Mean": "Mean Fitness",
        "Time": "Execution Time (s)",
        "Time_Std": "Time Std"
    }
    df.rename(columns=rename_map, inplace=True)

    # Mostrar resumen
    logger.info("\nResumen de datos:")
    logger.info(df.to_string())

    # Análisis estadístico básico
    logger.info("\nAnálisis estadístico:")
    algorithms = df["Algorithm"].unique()

    for algo in algorithms:
        algo_data = df[df["Algorithm"] == algo]
        logger.info(f"\n{algo}:")
        logger.info(f"  Ejecuciones: {algo_data['Run'].nunique()}")
        logger.info(f"  Mejor fitness: {algo_data['Best Fitness'].min():.4f}")
        logger.info(f"  Fitness promedio: {algo_data['Best Fitness'].mean():.4f}")
        logger.info(f"  Desviación estándar: {algo_data['Best Fitness'].std():.4f}")
        logger.info(f"  Tiempo promedio: {algo_data['Execution Time (s)'].mean():.4f}s")

    # Crear visualizaciones
    logger.info("\nGenerando visualizaciones...")

    # Procesar datos para visualizaciones
    summary_df = (
        df.groupby("Algorithm")
        .agg(
            {
                "Best Fitness": ["min", "mean", "std"],
                "Execution Time (s)": ["mean", "std"],
            }
        )
        .reset_index()
    )

    # Configurar multiíndice
    summary_df.columns = ["_".join(col).strip() for col in summary_df.columns.values]
    summary_df.rename(columns={"Algorithm_": "Algorithm"}, inplace=True)

    # Gráfico de barras para fitness promedio
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(x="Algorithm", y="Best Fitness_mean", data=summary_df)

    # Añadir barras de error
    ax.errorbar(
        range(len(summary_df)),
        summary_df["Best Fitness_mean"],
        yerr=summary_df["Best Fitness_std"],
        fmt="none",
        c="red",
        capsize=5,
    )

    plt.title("Fitness promedio por algoritmo")
    plt.ylabel("Fitness")
    plt.tight_layout()

    # Guardar gráfico
    bar_plot = os.path.join(output_dir, "fitness_bar_plot.png")
    plt.savefig(bar_plot, dpi=300)
    plt.close()

    # Comparación de tiempo de ejecución
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(x="Algorithm", y="Execution Time (s)_mean", data=summary_df)

    # Añadir barras de error para tiempo
    ax.errorbar(
        range(len(summary_df)),
        summary_df["Execution Time (s)_mean"],
        yerr=summary_df["Execution Time (s)_std"],
        fmt="none",
        c="red",
        capsize=5,
    )

    plt.title("Tiempo de ejecución promedio por algoritmo")
    plt.ylabel("Tiempo (s)")
    plt.tight_layout()

    time_plot = os.path.join(output_dir, "time_bar_plot.png")
    plt.savefig(time_plot, dpi=300)
    plt.close()

    # Boxplot para distribución de fitness
    plt.figure(figsize=(12, 6))
    ax = sns.boxplot(x="Algorithm", y="Best Fitness", data=df)
    plt.title("Distribución de Fitness por Algoritmo")
    plt.ylabel("Fitness")
    plt.tight_layout()

    box_plot = os.path.join(output_dir, "fitness_boxplot.png")
    plt.savefig(box_plot, dpi=300)
    plt.close()

    # Generar informe HTML
    html_report = os.path.join(output_dir, "analysis_report.html")

    # Generar el HTML
    with open(html_report, "w") as f:
        f.write(
            f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Análisis de Algoritmos Metaheurísticos</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #333366; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                img {{ max-width: 100%; height: auto; margin: 20px 0; }}
                .summary {{ margin-bottom: 30px; }}
            </style>
        </head>
        <body>
            <h1>Análisis de Algoritmos Metaheurísticos</h1>
            <div class="summary">
                <h2>Resumen del Análisis</h2>
                <p><strong>Archivo:</strong> {csv_file}</p>
                <p><strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Algoritmos analizados:</strong> {', '.join(algorithms)}</p>
            </div>
            
            <h2>Resultados Estadísticos</h2>
            <table>
                <tr>
                    <th>Algoritmo</th>
                    <th>Mejor Fitness</th>
                    <th>Fitness Promedio</th>
                    <th>Desviación Estándar</th>
                    <th>Tiempo Promedio (s)</th>
                </tr>
        """
        )

        for _, row in summary_df.iterrows():
            f.write(
                f"""
                <tr>
                    <td>{row['Algorithm']}</td>
                    <td>{row['Best Fitness_min']:.4f}</td>
                    <td>{row['Best Fitness_mean']:.4f}</td>
                    <td>{row['Best Fitness_std']:.4f}</td>
                    <td>{row['Execution Time (s)_mean']:.4f}</td>
                </tr>
            """
            )

        f.write(
            f"""
            </table>
            
            <h2>Visualizaciones</h2>
            
            <h3>Fitness Promedio por Algoritmo</h3>
            <img src="{os.path.basename(bar_plot)}" alt="Fitness promedio">
            
            <h3>Tiempo de Ejecución por Algoritmo</h3>
            <img src="{os.path.basename(time_plot)}" alt="Tiempo de ejecución">
            
            <h3>Distribución de Fitness</h3>
            <img src="{os.path.basename(box_plot)}" alt="Distribución de fitness">
            
        </body>
        </html>
        """
        )

    logger.info(f"\nInforme de análisis generado: {html_report}")
    logger.info(f"Visualizaciones guardadas en {output_dir}")

    return html_report


# Stats command for advanced statistical analysis
@cli.command()
@click.option("--csv", required=True, help="Path to the CSV file with benchmark results")
@click.option("--out", default=None, help="Output directory for results (default: same as CSV directory)")
def stats(csv, out):
    """
    Perform advanced statistical analysis (Friedman, Nemenyi, A12) and generate visualizations.
    """
    # Check if the CSV file exists
    if not os.path.exists(csv):
        logger.error(f"CSV file not found: {csv}")
        return

    # Determine output directory (default is the same directory as the CSV file)
    if out is None:
        out = os.path.dirname(csv)

    # Create output directory if it doesn't exist
    os.makedirs(out, exist_ok=True)

    logger.info(f"Performing advanced statistical analysis on {csv}")
    logger.info(f"Results will be saved to {out}")

    # Run the analysis using the unified statistics module
    from utils.statistics import run_all
    results = run_all(csv, out)

    if "error" in results:
        logger.error(f"Error in statistical analysis: {results['error']}")
        return

    # Print summary to console
    print("\n----- Statistical Analysis Summary -----")
    print(f"Global p-value: {results['friedman_p']:.6f}")

    if results['friedman_p'] < 0.05:
        print("Result: Statistically significant differences between algorithms detected.")

        # Get top 3 algorithms
        algorithm_ranks = results['mean_ranks']
        sorted_algos = sorted(algorithm_ranks.items(), key=lambda x: x[1])

        print("\nTop 3 algorithms:")
        for i, (algo, rank) in enumerate(sorted_algos[:3]):
            print(f"{i+1}. {algo} (rank: {rank:.2f})")

        # Get statistically equivalent algorithms
        cd = results['critical_distance']
        best_algo = sorted_algos[0][0]
        best_rank = sorted_algos[0][1]

        equivalent = [best_algo]
        for algo, rank in sorted_algos[1:]:
            if abs(rank - best_rank) <= cd:
                equivalent.append(algo)

        if len(equivalent) > 1:
            print(f"\nAlgorithms statistically equivalent to the best ({best_algo}):")
            for algo in equivalent[1:]:
                print(f"- {algo}")
        else:
            print(f"\nThe best algorithm ({best_algo}) is significantly better than all others.")
    else:
        print("Result: No statistically significant differences between algorithms.")

    print(f"\nFull report: {results['report']}")
    print(f"CD diagram: {results['cd_diagram']}")
    print("-----------------------------------------")

    return results

if __name__ == "__main__":
    cli()
