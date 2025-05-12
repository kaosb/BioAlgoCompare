#!/usr/bin/env python3
"""
Módulo mejorado para benchmarking de algoritmos metaheurísticos.
Implementa paralelización avanzada, sistema de checkpoint y recuperación,
y almacenamiento eficiente para ejecuciones masivas.
"""

import os
import time
import json
import numpy as np
import pandas as pd
from datetime import datetime
import multiprocessing as mp
from multiprocessing import Pool, cpu_count
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
import pickle
import gzip
import logging
import hashlib
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("benchmark.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("enhanced_benchmarking")

# Importar constantes y utilidades desde el módulo original
from utils.benchmarking import OPTIMAL_VALUES, BenchmarkResult


class EnhancedBenchmarkResult(BenchmarkResult):
    """Versión mejorada de BenchmarkResult con características adicionales."""

    def __init__(self, algorithm_name, instance_name, runs=0):
        super().__init__(algorithm_name, instance_name, runs)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.checkpoints = []
        self.metadata = {
            "system_info": self._get_system_info(),
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "completion_status": "initialized",
        }

    def _get_system_info(self):
        """Recopila información del sistema para reproducibilidad"""
        import platform

        return {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cores": cpu_count(),
        }

    def mark_checkpoint(self, current_run):
        """Registra un checkpoint con la ejecución actual"""
        self.checkpoints.append(
            {
                "run": current_run,
                "timestamp": datetime.now().isoformat(),
                "completed_runs": len(self.fitness_values),
            }
        )

    def mark_completed(self):
        """Marca el benchmark como completado"""
        self.metadata["end_time"] = datetime.now().isoformat()
        self.metadata["completion_status"] = "completed"
        self.metadata["total_runs"] = len(self.fitness_values)
        self.metadata["elapsed_time"] = (
            datetime.fromisoformat(self.metadata["end_time"])
            - datetime.fromisoformat(self.metadata["start_time"])
        ).total_seconds()

    def to_dict(self):
        """Convierte el resultado a un diccionario para serialización"""
        result = super().to_dict()
        result.update(
            {
                "timestamp": self.timestamp,
                "checkpoints": self.checkpoints,
                "metadata": self.metadata,
            }
        )
        return result

    @classmethod
    def from_dict(cls, data):
        """Crea una instancia a partir de un diccionario"""
        result = cls(data["algorithm_name"], data["instance_name"])
        result.fitness_values = data["fitness_values"]
        result.execution_times = data["execution_times"]
        result.convergence_curves = data["convergence_curves"]
        result.best_fitness = data.get("best_fitness")
        result.mean_fitness = data.get("mean_fitness")
        result.std_fitness = data.get("std_fitness")
        result.mean_time = data.get("mean_time")
        result.std_time = data.get("std_time")
        result.success_rate = data.get("success_rate")
        result.gap_to_optimal = data.get("gap_to_optimal")
        result.timestamp = data.get(
            "timestamp", datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        result.checkpoints = data.get("checkpoints", [])
        result.metadata = data.get("metadata", {})
        return result


def generate_benchmark_id(algorithm_classes, instances, seed, iterations, population):
    """Genera un ID único para el benchmark basado en sus parámetros"""
    algo_names = sorted([a.__name__ for a in algorithm_classes.values()])
    inst_names = sorted(instances)

    # Crear una cadena que represente los parámetros
    param_str = f"{'-'.join(algo_names)}_{'-'.join(inst_names)}_{seed}_{iterations}_{population}"

    # Generar hash abreviado para ID único
    benchmark_id = hashlib.md5(param_str.encode()).hexdigest()[:12]

    return benchmark_id


def _run_algorithm_task(args):
    """Función para ejecutar un algoritmo como parte de un benchmark paralelo"""
    (
        algo_class,
        instance_name,
        instance_path,
        run_id,
        iterations,
        population,
        seed,
        checkpoint_dir,
    ) = args

    try:
        from problems.vrp import VRPProblem

        # Cargar el problema
        problem = VRPProblem(instance_path)

        # Crear semilla específica para esta ejecución
        run_seed = seed + run_id if seed is not None else None

        # Inicializar algoritmo
        algorithm = algo_class(
            problem,
            population_size=population,
            max_iterations=iterations,
            seed=run_seed,
        )

        # Ejecutar algoritmo
        start_time = time.time()
        best_solution = algorithm.execute()
        execution_time = time.time() - start_time

        # Preparar resultado
        result = {
            "algorithm": algo_class.__name__,
            "instance": instance_name,
            "run_id": run_id,
            "fitness": best_solution.fitness(),
            "time": execution_time,
            "convergence": algorithm.get_convergence_curve(),
            "seed": run_seed,
        }

        # Guardar checkpoint individual si se especifica directorio
        if checkpoint_dir:
            # Guardar resultado en formato pickle para checkpoint
            checkpoint_file = os.path.join(
                checkpoint_dir, f"{algo_class.__name__}_{instance_name}_run{run_id}.pkl"
            )
            with open(checkpoint_file, "wb") as f:
                pickle.dump(result, f)

            # Guardar resultado individual en CSV
            csv_dir = os.path.join(os.path.dirname(checkpoint_dir), "results")
            algo_dir = os.path.join(csv_dir, algo_class.__name__)
            os.makedirs(algo_dir, exist_ok=True)

            # Crear CSV con los datos de esta corrida
            csv_file = os.path.join(algo_dir, f"{instance_name}_seed{run_seed}.csv")

            # Crear DataFrame con la curva de convergencia
            convergence_df = pd.DataFrame(
                {
                    "iteration": range(len(result["convergence"])),
                    "fitness": result["convergence"],
                    "algorithm": result["algorithm"],
                    "instance": result["instance"],
                    "run_id": result["run_id"],
                    "seed": result["seed"],
                }
            )

            # Guardar a CSV
            convergence_df.to_csv(csv_file, index=False)

        return result

    except Exception as e:
        logger.error(
            f"Error en ejecución {run_id} de {algo_class.__name__} para {instance_name}: {str(e)}"
        )
        return {
            "algorithm": algo_class.__name__ if algo_class else "Unknown",
            "instance": instance_name,
            "run_id": run_id,
            "error": str(e),
        }


def run_massive_benchmark(
    algorithm_classes,
    instances,
    runs=1000,
    iterations=100,
    population=30,
    seed=42,
    parallel=True,
    checkpoint_interval=50,
    output_dir=None,
    resume=False,
):
    """
    Ejecuta un benchmark masivo con soporte para checkpoint y recuperación.

    Args:
        algorithm_classes: Diccionario con los algoritmos a evaluar
        instances: Lista de nombres de instancias
        runs: Número de ejecuciones por combinación algoritmo/instancia
        iterations: Número de iteraciones por ejecución
        population: Tamaño de población
        seed: Semilla base para reproducibilidad
        parallel: Si se ejecuta en paralelo
        checkpoint_interval: Cada cuántas ejecuciones guardar un checkpoint
        output_dir: Directorio para guardar resultados
        resume: Si se debe intentar reanudar un benchmark anterior

    Returns:
        Lista de objetos EnhancedBenchmarkResult
    """
    # Configurar directorio de salida
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    benchmark_id = generate_benchmark_id(
        algorithm_classes, instances, seed, iterations, population
    )

    if output_dir is None:
        output_dir = f"results/massive_benchmark_{benchmark_id}_{timestamp}"

    # Crear directorios
    os.makedirs(output_dir, exist_ok=True)
    checkpoint_dir = os.path.join(output_dir, "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)

    # Archivo para checkpoint global
    checkpoint_file = os.path.join(output_dir, "benchmark_state.json.gz")

    # Verificar si reanudar benchmark
    benchmark_results = []
    completed_tasks = set()

    if resume and os.path.exists(checkpoint_file):
        try:
            logger.info(f"Intentando reanudar benchmark desde {checkpoint_file}")
            with gzip.open(checkpoint_file, "rt") as f:
                checkpoint_data = json.load(f)

            # Recuperar resultados guardados
            for result_data in checkpoint_data.get("results", []):
                benchmark_results.append(EnhancedBenchmarkResult.from_dict(result_data))

            # Recuperar tareas completadas
            completed_tasks = set(checkpoint_data.get("completed_tasks", []))

            logger.info(
                f"Reanudado con éxito: {len(benchmark_results)} resultados, {len(completed_tasks)} tareas completadas"
            )
        except Exception as e:
            logger.error(f"Error al reanudar benchmark: {str(e)}")
            logger.info("Iniciando benchmark desde cero")
            benchmark_results = []
            completed_tasks = set()

    # Verificar instancias
    valid_instances = []
    for instance_name in instances:
        instance_path = f"data/vrp/{instance_name}.vrp"
        if os.path.exists(instance_path):
            valid_instances.append((instance_name, instance_path))
        else:
            logger.warning(f"Instancia no encontrada: {instance_name}")

    if not valid_instances:
        logger.error("No se encontraron instancias válidas")
        return []

    # Crear todas las tareas necesarias
    all_tasks = []
    for algo_name, algo_class in algorithm_classes.items():
        for instance_name, instance_path in valid_instances:
            # Verificar si ya existe un resultado para esta combinación
            existing_result = None
            for result in benchmark_results:
                if (
                    result.algorithm_name == algo_class.__name__
                    and result.instance_name == instance_name
                ):
                    existing_result = result
                    break

            # Si no existe o no está completo, planificar ejecuciones
            if existing_result is None:
                # Crear nuevo resultado
                new_result = EnhancedBenchmarkResult(algo_class.__name__, instance_name)
                benchmark_results.append(new_result)

                # Añadir todas las ejecuciones como tareas
                for run_id in range(1, runs + 1):
                    task_id = f"{algo_class.__name__}_{instance_name}_{run_id}"
                    if task_id not in completed_tasks:
                        all_tasks.append(
                            (
                                algo_class,
                                instance_name,
                                instance_path,
                                run_id,
                                iterations,
                                population,
                                seed,
                                checkpoint_dir,
                            )
                        )

            elif len(existing_result.fitness_values) < runs:
                # Continuar ejecuciones para resultado existente pero incompleto
                completed_runs = len(existing_result.fitness_values)
                logger.info(
                    f"Continuando {algo_class.__name__} en {instance_name} desde ejecución {completed_runs+1}"
                )

                for run_id in range(completed_runs + 1, runs + 1):
                    task_id = f"{algo_class.__name__}_{instance_name}_{run_id}"
                    if task_id not in completed_tasks:
                        all_tasks.append(
                            (
                                algo_class,
                                instance_name,
                                instance_path,
                                run_id,
                                iterations,
                                population,
                                seed,
                                checkpoint_dir,
                            )
                        )

    # Salir si no hay tareas pendientes
    if not all_tasks:
        logger.info("No hay tareas pendientes, el benchmark está completo")
        return benchmark_results

    # Configurar multiprocessing
    if parallel:
        num_processes = min(cpu_count(), len(all_tasks))
        logger.info(f"Modo paralelo activado. Usando {num_processes} procesos.")
    else:
        num_processes = 1

    # Función para guardar el estado actual del benchmark
    def save_checkpoint():
        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "results": [result.to_dict() for result in benchmark_results],
            "completed_tasks": list(completed_tasks),
            "pending_tasks": len(all_tasks),
            "config": {
                "runs": runs,
                "iterations": iterations,
                "population": population,
                "seed": seed,
                "benchmark_id": benchmark_id,
            },
        }

        with gzip.open(checkpoint_file, "wt") as f:
            json.dump(checkpoint_data, f)

        logger.info(f"Checkpoint guardado: {checkpoint_file}")

    # Guardar checkpoint inicial
    save_checkpoint()

    # Ejecutar tareas
    task_count = len(all_tasks)
    completed_count = 0
    checkpoint_counter = 0

    logger.info(f"Iniciando benchmark con {task_count} tareas")
    start_time = time.time()

    try:
        # Usar ProcessPoolExecutor para mejor manejo de memoria y control
        if parallel and num_processes > 1:
            with ProcessPoolExecutor(max_workers=num_processes) as executor:
                results_iter = list(
                    tqdm(
                        executor.map(_run_algorithm_task, all_tasks),
                        total=len(all_tasks),
                        desc="Ejecutando benchmark",
                    )
                )
        else:
            # Ejecución secuencial
            results_iter = []
            for i, task in enumerate(all_tasks):
                logger.info(
                    f"Tarea {i+1}/{len(all_tasks)}: {task[0].__name__} en {task[1]}, run {task[3]}"
                )
                result = _run_algorithm_task(task)
                results_iter.append(result)

                # Mostrar progreso
                if (i + 1) % 10 == 0 or i + 1 == len(all_tasks):
                    logger.info(
                        f"Progreso: {i+1}/{len(all_tasks)} ({(i+1)/len(all_tasks)*100:.1f}%)"
                    )

        # Procesar resultados
        for result in results_iter:
            if "error" in result:
                logger.error(f"Error en tarea: {result}")
                continue

            # Buscar el objeto de resultado correspondiente
            target_result = None
            for res in benchmark_results:
                if (
                    res.algorithm_name == result["algorithm"]
                    and res.instance_name == result["instance"]
                ):
                    target_result = res
                    break

            # Si no existe, crear uno nuevo (no debería ocurrir)
            if target_result is None:
                logger.warning(
                    f"Creando resultado nuevo para {result['algorithm']} - {result['instance']}"
                )
                target_result = EnhancedBenchmarkResult(
                    result["algorithm"], result["instance"]
                )
                benchmark_results.append(target_result)

            # Añadir datos
            target_result.add_run(
                result["fitness"], result["time"], result["convergence"]
            )

            # Marcar tarea como completada
            task_id = f"{result['algorithm']}_{result['instance']}_{result['run_id']}"
            completed_tasks.add(task_id)
            completed_count += 1
            checkpoint_counter += 1

            # Guardar checkpoint periódicamente
            if checkpoint_counter >= checkpoint_interval:
                for res in benchmark_results:
                    res.compute_metrics()
                save_checkpoint()
                checkpoint_counter = 0

    except KeyboardInterrupt:
        logger.warning("Benchmark interrumpido por el usuario")
    except Exception as e:
        logger.error(f"Error en benchmark: {str(e)}")
    finally:
        # Calcular métricas y guardar checkpoint final
        for result in benchmark_results:
            result.compute_metrics()
            result.mark_completed()

        save_checkpoint()

        # Guardar resultados
        duration = time.time() - start_time
        logger.info(f"Benchmark completado en {duration/60:.2f} minutos")
        logger.info(f"Completadas {completed_count}/{task_count} tareas")

        # Generar archivo CSV resumen
        summary_df = create_summary_dataframe(benchmark_results)
        summary_file = os.path.join(output_dir, "massive_benchmark_summary.csv")
        summary_df.to_csv(summary_file, index=False)
        logger.info(f"Resumen guardado en {summary_file}")

        return benchmark_results


def create_summary_dataframe(benchmark_results):
    """Crea un DataFrame con el resumen de los resultados del benchmark"""
    summary_data = []

    for result in benchmark_results:
        if not result.fitness_values:  # Omitir resultados vacíos
            continue

        row = {
            "Algorithm": result.algorithm_name,
            "Instance": result.instance_name,
            "Runs": len(result.fitness_values),
            "Best": result.best_fitness,
            "Mean": result.mean_fitness,
            "Std": result.std_fitness,
            "Time": result.mean_time,
            "Time_Std": result.std_time,
        }

        # Añadir gap al óptimo si está disponible
        if result.gap_to_optimal is not None:
            row["Gap (%)"] = result.gap_to_optimal

        # Añadir tasa de éxito si está disponible
        if result.success_rate is not None:
            row["Success (%)"] = result.success_rate

        summary_data.append(row)

    # Crear DataFrame
    summary_df = pd.DataFrame(summary_data)

    return summary_df


def load_results(output_dir, algorithms=None, instances=None):
    """
    Carga resultados específicos de un directorio de benchmark.

    Args:
        output_dir: Directorio de resultados del benchmark
        algorithms: Lista de algoritmos a filtrar (None = todos)
        instances: Lista de instancias a filtrar (None = todas)

    Returns:
        Lista de objetos EnhancedBenchmarkResult
    """
    checkpoint_file = os.path.join(output_dir, "benchmark_state.json.gz")

    if not os.path.exists(checkpoint_file):
        logger.error(f"No se encontró archivo de checkpoint en {checkpoint_file}")
        return []

    try:
        with gzip.open(checkpoint_file, "rt") as f:
            checkpoint_data = json.load(f)

        # Convertir datos a objetos EnhancedBenchmarkResult
        all_results = []
        for result_data in checkpoint_data.get("results", []):
            # Filtrar por algoritmo si se especifica
            if algorithms and result_data["algorithm_name"] not in algorithms:
                continue

            # Filtrar por instancia si se especifica
            if instances and result_data["instance_name"] not in instances:
                continue

            all_results.append(EnhancedBenchmarkResult.from_dict(result_data))

        logger.info(f"Cargados {len(all_results)} resultados desde {checkpoint_file}")
        return all_results

    except Exception as e:
        logger.error(f"Error al cargar resultados: {str(e)}")
        return []


def extract_convergence_data(benchmark_results):
    """
    Extrae datos de convergencia de los resultados para análisis avanzado.

    Args:
        benchmark_results: Lista de objetos EnhancedBenchmarkResult

    Returns:
        DataFrame con datos de convergencia
    """
    convergence_data = []

    for result in benchmark_results:
        algo_name = result.algorithm_name
        instance_name = result.instance_name

        for run_id, curve in enumerate(result.convergence_curves, 1):
            if not curve:  # Saltar curvas vacías
                continue

            # Convertir a array numpy para manipulación
            curve_np = np.array(curve)

            # Añadir puntos clave de la curva
            for iteration, fitness in enumerate(curve_np):
                convergence_data.append(
                    {
                        "Algorithm": algo_name,
                        "Instance": instance_name,
                        "Run": run_id,
                        "Iteration": iteration,
                        "Fitness": fitness,
                    }
                )

    return pd.DataFrame(convergence_data)


def create_enhanced_report(
    benchmark_results, output_file=None, include_convergence=True
):
    """
    Crea un informe HTML enriquecido con los resultados del benchmark.

    Args:
        benchmark_results: Lista de objetos EnhancedBenchmarkResult
        output_file: Ruta al archivo HTML de salida
        include_convergence: Si se incluyen gráficos de convergencia

    Returns:
        Ruta al archivo HTML generado
    """
    import matplotlib.pyplot as plt
    import base64
    from io import BytesIO

    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"results/enhanced_report_{timestamp}.html"

    # Directorio para guardar figuras
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Crear DataFrame con resumen
    summary_df = create_summary_dataframe(benchmark_results)

    # Agrupar resultados por instancia
    instance_results = {}
    for result in benchmark_results:
        if result.instance_name not in instance_results:
            instance_results[result.instance_name] = []
        instance_results[result.instance_name].append(result)

    # Crear reporte HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Informe Avanzado de Benchmark</title>
        <style>
            body {{
                font-family: "Arial", sans-serif;
                margin: 20px;
                line-height: 1.6;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 20px;
            }}
            th, td {{
                text-align: left;
                padding: 8px;
                border: 1px solid #ddd;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            .section {{
                margin-bottom: 30px;
            }}
            .figure {{
                margin: 20px 0;
                text-align: center;
            }}
            .figure img {{
                max-width: 100%;
                height: auto;
            }}
            .caption {{
                margin-top: 10px;
                font-style: italic;
                color: #666;
            }}
            .highlight {{
                font-weight: bold;
                color: #e74c3c;
            }}
            .success {{
                color: #27ae60;
            }}
            .navbar {{
                position: fixed;
                top: 0;
                width: 100%;
                background-color: #2c3e50;
                padding: 10px 0;
                z-index: 1000;
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
            .boxplot {{
                margin: 20px 0;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="navbar">
            <a href="#summary">Resumen</a>
            <a href="#instances">Instancias</a>
            <a href="#convergence">Convergencia</a>
            <a href="#statistics">Estadísticas</a>
        </div>
        
        <div class="content">
            <h1>Informe Avanzado de Benchmark</h1>
            <p>Generado el: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <div class="section" id="summary">
                <h2>Resumen de Resultados</h2>
                {summary_df.to_html(index=False, classes="table")}
            </div>
    """

    # Añadir sección por instancia
    html_content += """
            <div class="section" id="instances">
                <h2>Resultados por Instancia</h2>
    """

    for instance_name, results in instance_results.items():
        html_content += f"""
                <h3>Instancia: {instance_name}</h3>
        """

        # Añadir boxplot de fitness por algoritmo
        plt.figure(figsize=(10, 6))
        data = []
        labels = []

        for result in results:
            if result.fitness_values:
                data.append(result.fitness_values)
                labels.append(result.algorithm_name)

        if data:
            plt.boxplot(data, labels=labels)
            plt.title(f"Distribución de fitness - {instance_name}")
            plt.ylabel("Fitness")
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Convertir figura a base64 para incrustar en HTML
            buffer = BytesIO()
            plt.savefig(buffer, format="png")
            plt.close()

            img_str = base64.b64encode(buffer.getvalue()).decode()

            html_content += f"""
                <div class="boxplot">
                    <img src="data:image/png;base64,{img_str}" alt="Boxplot - {instance_name}">
                    <p class="caption">Distribución de fitness por algoritmo</p>
                </div>
            """

        # Tabla de resumen para esta instancia
        instance_summary = summary_df[summary_df["Instance"] == instance_name]
        html_content += """
                <table>
                    <tr>
                        <th>Algoritmo</th>
                        <th>Mejor</th>
                        <th>Promedio</th>
                        <th>Desv. Est.</th>
                        <th>Tiempo</th>
                    </tr>
        """

        for _, row in instance_summary.iterrows():
            html_content += f"""
                    <tr>
                        <td>{row['Algorithm']}</td>
                        <td>{row['Best']:.2f}</td>
                        <td>{row['Mean']:.2f}</td>
                        <td>{row['Std']:.2f}</td>
                        <td>{row['Time']:.2f}s</td>
                    </tr>
            """

        html_content += """
                </table>
        """

    html_content += """
            </div>
    """

    # Añadir gráficos de convergencia si se solicita
    if include_convergence:
        html_content += """
            <div class="section" id="convergence">
                <h2>Análisis de Convergencia</h2>
        """

        for instance_name, results in instance_results.items():
            html_content += f"""
                <h3>Convergencia - {instance_name}</h3>
            """

            # Crear gráfico de convergencia promedio
            plt.figure(figsize=(10, 6))

            for result in results:
                if not result.convergence_curves:
                    continue

                # Encontrar la longitud mínima de las curvas
                min_length = min(
                    len(curve) for curve in result.convergence_curves if curve
                )

                if min_length > 0:
                    # Recortar curvas a la misma longitud
                    curves = [
                        curve[:min_length]
                        for curve in result.convergence_curves
                        if curve
                    ]

                    # Calcular promedio
                    avg_curve = np.mean(curves, axis=0)

                    # Calcular intervalo de confianza (95%)
                    std_curve = np.std(curves, axis=0)
                    n = len(curves)
                    ci = 1.96 * std_curve / np.sqrt(n)

                    # Graficar
                    x = np.arange(min_length)
                    plt.plot(x, avg_curve, label=result.algorithm_name)
                    plt.fill_between(x, avg_curve - ci, avg_curve + ci, alpha=0.2)

            plt.title(f"Convergencia Promedio - {instance_name}")
            plt.xlabel("Iteración")
            plt.ylabel("Fitness")
            plt.legend()
            plt.grid(True, linestyle="--", alpha=0.7)
            plt.tight_layout()

            # Convertir figura a base64
            buffer = BytesIO()
            plt.savefig(buffer, format="png")
            plt.close()

            img_str = base64.b64encode(buffer.getvalue()).decode()

            html_content += f"""
                <div class="figure">
                    <img src="data:image/png;base64,{img_str}" alt="Convergencia - {instance_name}">
                    <p class="caption">Curvas de convergencia promedio con intervalos de confianza del 95%</p>
                </div>
            """

        html_content += """
            </div>
        """

    # Estadísticas avanzadas (solo placeholder)
    html_content += """
            <div class="section" id="statistics">
                <h2>Estadísticas Avanzadas</h2>
                <p>Este informe incluye datos de múltiples ejecuciones por algoritmo, lo que permite un análisis estadístico robusto.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Guardar HTML
    with open(output_file, "w") as f:
        f.write(html_content)

    logger.info(f"Informe HTML generado: {output_file}")

    return output_file


# Función de alto nivel para ejecutar todo el proceso
def run_complete_analysis(
    algorithm_classes,
    instances,
    runs=1000,
    iterations=100,
    population=30,
    seed=42,
    parallel=True,
    output_dir=None,
    resume=True,
):
    """
    Ejecuta un análisis completo incluyendo benchmark masivo y generación de reportes.

    Args:
        algorithm_classes: Diccionario de clases de algoritmos
        instances: Lista de nombres de instancias
        runs: Número de ejecuciones por combinación algoritmo/instancia
        iterations: Número de iteraciones por ejecución
        population: Tamaño de población
        seed: Semilla base para reproducibilidad
        parallel: Si se ejecuta en paralelo
        output_dir: Directorio para guardar resultados
        resume: Si se intenta reanudar benchmark previo

    Returns:
        Ruta al reporte HTML generado
    """
    # Ejecutar benchmark
    benchmark_results = run_massive_benchmark(
        algorithm_classes,
        instances,
        runs=runs,
        iterations=iterations,
        population=population,
        seed=seed,
        parallel=parallel,
        checkpoint_interval=max(1, runs // 20),  # Checkpoint cada 5% de progreso
        output_dir=output_dir,
        resume=resume,
    )

    if not benchmark_results:
        logger.error("No se obtuvieron resultados del benchmark")
        return None

    # Generar reporte
    report_file = (
        os.path.join(output_dir, "massive_benchmark_report.html")
        if output_dir
        else None
    )
    report_path = create_enhanced_report(
        benchmark_results, output_file=report_file, include_convergence=True
    )

    logger.info(f"Análisis completo generado: {report_path}")

    return report_path
