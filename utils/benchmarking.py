import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
import os
import json
import time
from datetime import datetime
import matplotlib.colors as mcolors
from matplotlib.patches import Polygon
from matplotlib.table import Table
import matplotlib.gridspec as gridspec
from scipy.stats import friedmanchisquare, wilcoxon
import multiprocessing as mp


# Función auxiliar para la ejecución de algoritmos en paralelo
# Definida a nivel de módulo para evitar problemas de pickle
def _run_algo_task(params):
    AlgoClass, problem, population, iterations, run_seed, _ = params
    algo = AlgoClass(
        problem, population_size=population, max_iterations=iterations, seed=run_seed
    )

    start_time = time.time()
    best_solution = algo.execute()
    execution_time = time.time() - start_time

    return best_solution.fitness(), execution_time, algo.get_convergence_curve()


class BenchmarkResult:
    """Clase para almacenar y analizar resultados de benchmarking."""

    def __init__(self, algorithm_name, instance_name, runs=None):
        """
        Inicializa un resultado de benchmark.

        Args:
            algorithm_name: Nombre del algoritmo
            instance_name: Nombre de la instancia
            runs: Número de ejecuciones independientes (si es None, se determina por los datos)
        """
        self.algorithm_name = algorithm_name
        self.instance_name = instance_name
        self.optimal_value = OPTIMAL_VALUES.get(instance_name, None)

        # Resultados por ejecución
        self.fitness_values = []
        self.execution_times = []
        self.convergence_curves = []

        # Métricas derivadas
        self.best_fitness = None
        self.worst_fitness = None
        self.mean_fitness = None
        self.std_fitness = None
        self.mean_time = None
        self.std_time = None
        self.gap_to_optimal = None
        self.success_rate = None
        self.avg_convergence = None

        # Si no se especifica el número de ejecuciones, se determina por los datos
        self.runs = runs

    def add_run(self, fitness, execution_time, convergence_curve):
        """Añade los resultados de una ejecución."""
        self.fitness_values.append(fitness)
        self.execution_times.append(execution_time)
        self.convergence_curves.append(convergence_curve)

    def compute_metrics(self):
        """Calcula las métricas derivadas de los resultados."""
        if not self.fitness_values:
            return

        # Métricas básicas
        self.best_fitness = min(self.fitness_values)
        self.worst_fitness = max(self.fitness_values)
        self.mean_fitness = np.mean(self.fitness_values)
        self.std_fitness = np.std(self.fitness_values)
        self.mean_time = np.mean(self.execution_times)
        self.std_time = np.std(self.execution_times)

        # Gap respecto al óptimo conocido
        if self.optimal_value:
            self.gap_to_optimal = (
                (self.best_fitness - self.optimal_value) / self.optimal_value * 100
            )

            # Tasa de éxito (soluciones dentro del 1% del óptimo)
            threshold = self.optimal_value * 1.01
            successful_runs = sum(
                1 for fitness in self.fitness_values if fitness <= threshold
            )
            self.success_rate = successful_runs / len(self.fitness_values) * 100

        # Calcular curva de convergencia promedio
        # Primero aseguramos que todas las curvas tengan la misma longitud
        if self.convergence_curves:
            min_length = min(len(curve) for curve in self.convergence_curves)
            standardized_curves = [
                curve[:min_length] for curve in self.convergence_curves
            ]
            self.avg_convergence = np.mean(standardized_curves, axis=0)

    def to_dict(self):
        """Convierte los resultados a un diccionario para almacenamiento/serialización."""
        self.compute_metrics()

        result = {
            "algorithm": self.algorithm_name,
            "instance": self.instance_name,
            "optimal_value": self.optimal_value,
            "runs": len(self.fitness_values),
            "metrics": {
                "best_fitness": self.best_fitness,
                "worst_fitness": self.worst_fitness,
                "mean_fitness": self.mean_fitness,
                "std_fitness": self.std_fitness,
                "mean_time": self.mean_time,
                "std_time": self.std_time,
                "gap_to_optimal": self.gap_to_optimal,
                "success_rate": self.success_rate,
            },
            "detailed_results": {
                "fitness_values": self.fitness_values,
                "execution_times": self.execution_times,
            },
        }

        # No incluimos las curvas de convergencia en el diccionario para evitar objetos muy grandes
        return result

    @classmethod
    def from_dict(cls, data):
        """Crea un objeto BenchmarkResult a partir de un diccionario."""
        result = cls(data["algorithm"], data["instance"])

        for i in range(data["runs"]):
            result.add_run(
                data["detailed_results"]["fitness_values"][i],
                data["detailed_results"]["execution_times"][i],
                [],  # No se almacenan las curvas de convergencia en el diccionario
            )

        # Calculamos las métricas
        result.compute_metrics()
        return result


# Valores óptimos conocidos para instancias estándar de VRP
OPTIMAL_VALUES = {
    "A-n32-k5": 784,
    "P-n16-k8": 450,
    "E-n22-k4": 375,
    "B-n31-k5": 672,
    "E-n51-k5": 521,
}


def save_benchmark_results(results, filename=None):
    """
    Guarda los resultados de benchmarking en un archivo JSON.

    Args:
        results: Lista de objetos BenchmarkResult
        filename: Nombre del archivo (si es None, se genera automáticamente)
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/benchmark_{timestamp}.json"

    # Crear directorio si no existe
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Convertir resultados a diccionarios
    data = [result.to_dict() for result in results]

    # Guardar en formato JSON
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

    return filename


def load_benchmark_results(filename):
    """
    Carga resultados de benchmarking desde un archivo JSON.

    Args:
        filename: Ruta al archivo JSON

    Returns:
        Lista de objetos BenchmarkResult
    """
    with open(filename, "r") as f:
        data = json.load(f)

    # Convertir diccionarios a objetos BenchmarkResult
    results = [BenchmarkResult.from_dict(item) for item in data]
    return results


def run_benchmark(
    algorithms,
    problem_instances,
    runs=10,
    iterations=100,
    population=30,
    seed=None,
    parallel=False,
):
    """
    Ejecuta un benchmark comparativo de algoritmos sobre instancias de problemas.

    Args:
        algorithms: Diccionario de algoritmos {nombre: clase}
        problem_instances: Lista de instancias VRP
        runs: Número de ejecuciones independientes por combinación
        iterations: Número de iteraciones por ejecución
        population: Tamaño de población para los algoritmos
        seed: Semilla inicial para reproducibilidad
        parallel: Si es True, se ejecutan en paralelo

    Returns:
        Lista de objetos BenchmarkResult
    """
    from problems.vrp import VRPProblem

    results = []

    # Configurar procesamiento paralelo si está habilitado
    if parallel:
        pool = mp.Pool(
            processes=min(mp.cpu_count(), len(algorithms) * len(problem_instances))
        )
        tasks = []

    for instance_name in problem_instances:
        instance_path = f"data/vrp/{instance_name}.vrp"
        if not os.path.exists(instance_path):
            print(f"Error: La instancia {instance_name} no existe en data/vrp")
            continue

        problem = VRPProblem(instance_path)
        print(f"Benchmark para instancia: {instance_name}")

        for algo_name, AlgoClass in algorithms.items():
            print(f"  Ejecutando {algo_name}...")
            benchmark_result = BenchmarkResult(algo_name, instance_name, runs)

            if parallel:
                # Agregar tarea a la lista para ejecución paralela
                for run in range(runs):
                    run_seed = seed + run if seed is not None else None
                    tasks.append(
                        (
                            AlgoClass,
                            problem,
                            population,
                            iterations,
                            run_seed,
                            benchmark_result,
                        )
                    )
            else:
                # Ejecución secuencial
                for run in range(runs):
                    run_seed = seed + run if seed is not None else None
                    algo = AlgoClass(
                        problem,
                        population_size=population,
                        max_iterations=iterations,
                        seed=run_seed,
                    )

                    start_time = time.time()
                    best_solution = algo.execute()
                    execution_time = time.time() - start_time

                    benchmark_result.add_run(
                        best_solution.fitness(),
                        execution_time,
                        algo.get_convergence_curve(),
                    )

                    print(
                        f"    Ejecución {run+1}/{runs}: Fitness = {best_solution.fitness():.2f}, Tiempo = {execution_time:.2f}s"
                    )

                benchmark_result.compute_metrics()
                results.append(benchmark_result)

                print(
                    f"  Mejor: {benchmark_result.best_fitness:.2f}, Promedio: {benchmark_result.mean_fitness:.2f}, "
                    + f"Tiempo: {benchmark_result.mean_time:.2f}s"
                )
                if benchmark_result.optimal_value:
                    print(
                        f"  Gap al óptimo: {benchmark_result.gap_to_optimal:.2f}%, "
                        + f"Tasa de éxito: {benchmark_result.success_rate:.2f}%"
                    )
                print()

    # Ejecutar tareas en paralelo si está habilitado
    if parallel and tasks:
        # Ejecutar las tareas en paralelo utilizando la función _run_algo_task definida a nivel de módulo
        parallel_results = pool.map(_run_algo_task, tasks)
        pool.close()
        pool.join()

        # Agrupar los resultados por algoritmo e instancia
        task_index = 0
        for instance_name in problem_instances:
            for algo_name in algorithms:
                benchmark_result = BenchmarkResult(algo_name, instance_name, runs)

                for _ in range(runs):
                    fitness, time, convergence = parallel_results[task_index]
                    benchmark_result.add_run(fitness, time, convergence)
                    task_index += 1

                benchmark_result.compute_metrics()
                results.append(benchmark_result)

    return results


def plot_solution_quality(benchmark_results, title=None, show_optimal=True):
    """
    Visualiza la calidad de las soluciones obtenidas por diferentes algoritmos.

    Args:
        benchmark_results: Lista de objetos BenchmarkResult
        title: Título para el gráfico
        show_optimal: Si es True, muestra el valor óptimo como línea de referencia
    """
    # Agrupar por instancia
    instances = {}
    for result in benchmark_results:
        if result.instance_name not in instances:
            instances[result.instance_name] = []
        instances[result.instance_name].append(result)

    # Crear gráficos para cada instancia
    n_instances = len(instances)
    fig, axes = plt.subplots(n_instances, 1, figsize=(12, 5 * n_instances))

    if n_instances == 1:
        axes = [axes]

    for i, (instance_name, results) in enumerate(instances.items()):
        ax = axes[i]

        # Datos para el boxplot
        data = []
        labels = []

        for result in results:
            data.append(result.fitness_values)
            labels.append(result.algorithm_name)

        # Crear boxplot
        bp = ax.boxplot(data, patch_artist=True, labels=labels)

        # Colorear cajas
        colors = list(mcolors.TABLEAU_COLORS.values())
        for j, box in enumerate(bp["boxes"]):
            box.set(facecolor=colors[j % len(colors)])

        # Mostrar valor óptimo si está disponible
        optimal = OPTIMAL_VALUES.get(instance_name)
        if show_optimal and optimal is not None:
            ax.axhline(y=optimal, color="r", linestyle="--", label=f"Óptimo: {optimal}")
            ax.legend()

        ax.set_title(f"Calidad de solución - {instance_name}")
        ax.set_ylabel("Fitness (Distancia)")
        ax.grid(True, linestyle="--", alpha=0.7)

    plt.tight_layout()

    if title:
        fig.suptitle(title, fontsize=16)
        plt.subplots_adjust(top=0.95)

    return plt


def plot_execution_time(benchmark_results, title=None):
    """
    Visualiza el tiempo de ejecución de diferentes algoritmos.

    Args:
        benchmark_results: Lista de objetos BenchmarkResult
        title: Título para el gráfico
    """
    # Agrupar por instancia
    instances = {}
    for result in benchmark_results:
        if result.instance_name not in instances:
            instances[result.instance_name] = []
        instances[result.instance_name].append(result)

    # Crear gráficos para cada instancia
    n_instances = len(instances)
    fig, axes = plt.subplots(n_instances, 1, figsize=(12, 4 * n_instances))

    if n_instances == 1:
        axes = [axes]

    for i, (instance_name, results) in enumerate(instances.items()):
        ax = axes[i]

        # Datos para el gráfico de barras
        algorithms = []
        mean_times = []
        std_times = []

        for result in results:
            algorithms.append(result.algorithm_name)
            mean_times.append(result.mean_time)
            std_times.append(result.std_time)

        # Crear gráfico de barras
        x = np.arange(len(algorithms))
        bars = ax.bar(x, mean_times, yerr=std_times, alpha=0.7, capsize=5)

        # Colorear barras
        colors = list(mcolors.TABLEAU_COLORS.values())
        for j, bar in enumerate(bars):
            bar.set_color(colors[j % len(colors)])

        ax.set_title(f"Tiempo de ejecución - {instance_name}")
        ax.set_ylabel("Tiempo (segundos)")
        ax.set_xticks(x)
        ax.set_xticklabels(algorithms)
        ax.grid(True, linestyle="--", alpha=0.7, axis="y")

    plt.tight_layout()

    if title:
        fig.suptitle(title, fontsize=16)
        plt.subplots_adjust(top=0.95)

    return plt


def plot_convergence_comparison(benchmark_results, title=None):
    """
    Compara las curvas de convergencia de diferentes algoritmos.

    Args:
        benchmark_results: Lista de objetos BenchmarkResult
        title: Título para el gráfico
    """
    # Agrupar por instancia
    instances = {}
    for result in benchmark_results:
        if result.instance_name not in instances:
            instances[result.instance_name] = []
        instances[result.instance_name].append(result)

    # Crear gráficos para cada instancia
    n_instances = len(instances)
    fig, axes = plt.subplots(n_instances, 1, figsize=(12, 5 * n_instances))

    if n_instances == 1:
        axes = [axes]

    for i, (instance_name, results) in enumerate(instances.items()):
        ax = axes[i]

        # Dibujar curvas de convergencia
        for result in results:
            if result.avg_convergence is not None:
                iterations = list(range(1, len(result.avg_convergence) + 1))
                ax.plot(
                    iterations,
                    result.avg_convergence,
                    linewidth=2,
                    label=result.algorithm_name,
                )

        # Mostrar valor óptimo si está disponible
        optimal = OPTIMAL_VALUES.get(instance_name)
        if optimal is not None:
            ax.axhline(y=optimal, color="r", linestyle="--", label=f"Óptimo: {optimal}")

        ax.set_title(f"Curvas de convergencia - {instance_name}")
        ax.set_xlabel("Iteración")
        ax.set_ylabel("Fitness (Distancia)")
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend()

    plt.tight_layout()

    if title:
        fig.suptitle(title, fontsize=16)
        plt.subplots_adjust(top=0.95)

    return plt


def plot_performance_radar(benchmark_results, instance_name, metrics=None, title=None):
    """
    Crea un gráfico radar que compara el rendimiento de los algoritmos en varias métricas.

    Args:
        benchmark_results: Lista de objetos BenchmarkResult
        instance_name: Nombre de la instancia a comparar
        metrics: Lista de métricas a comparar (por defecto: calidad, tiempo, estabilidad)
        title: Título para el gráfico
    """
    # Filtrar resultados por instancia
    results = [r for r in benchmark_results if r.instance_name == instance_name]
    if not results:
        return None

    if metrics is None:
        metrics = ["quality", "time", "stability", "success"]

    # Obtener datos normalizados para cada métrica
    algorithms = [r.algorithm_name for r in results]
    n_metrics = len(metrics)

    # Ángulos para el gráfico radar
    angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
    angles += angles[:1]  # Cerrar el polígono

    # Crear figura
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    # Preparar datos para cada algoritmo
    for i, result in enumerate(results):
        values = []

        for metric in metrics:
            if metric == "quality":
                # Mejor fitness normalizado (menor es mejor, invertir la normalización)
                if result.optimal_value:
                    # Normalizar respecto al óptimo
                    value = result.optimal_value / result.best_fitness
                else:
                    # Normalizar respecto al mejor entre los algoritmos
                    best_fitness = min(r.best_fitness for r in results)
                    value = best_fitness / result.best_fitness
            elif metric == "time":
                # Tiempo normalizado (menor es mejor, invertir la normalización)
                min_time = min(r.mean_time for r in results)
                value = min_time / result.mean_time
            elif metric == "stability":
                # Estabilidad normalizada (menor desviación es mejor, invertir la normalización)
                if result.std_fitness == 0:
                    value = 1.0  # Perfecta estabilidad
                else:
                    min_std = min(max(0.001, r.std_fitness) for r in results)
                    value = min_std / max(0.001, result.std_fitness)
            elif metric == "success":
                # Tasa de éxito normalizada (mayor es mejor)
                if result.success_rate is not None:
                    value = result.success_rate / 100.0
                else:
                    value = 0.0
            else:
                value = 0.5  # Valor por defecto

            values.append(max(0, min(1, value)))  # Limitar entre 0 y 1

        # Cerrar el polígono
        values += values[:1]

        # Dibujar el polígono
        ax.plot(angles, values, linewidth=2, label=result.algorithm_name)
        ax.fill(angles, values, alpha=0.1)

    # Configurar el gráfico
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([m.capitalize() for m in metrics])
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"])
    ax.set_ylim(0, 1)

    if title:
        ax.set_title(title)
    else:
        ax.set_title(f"Comparación de rendimiento - {instance_name}")

    ax.legend(loc="upper right", bbox_to_anchor=(0.1, 0.1))

    return plt



class BenchmarkReportBuilder:
    """Build benchmark reports with proper separation of concerns."""
    
    def __init__(self, benchmark_results):
        """Initialize with benchmark results."""
        self.results = benchmark_results
        self.instances = self._group_by_instance()
        
    def create_report(self, filename=None):
        """Create the benchmark report."""
        filename = self._prepare_filename(filename)
        
        # Create summary
        summary_df = self._create_summary_dataframe()
        
        # Generate visualizations
        figures_dir = self._prepare_figures_directory(filename)
        visualizations = self._generate_all_visualizations(figures_dir)
        
        # Build HTML
        html_content = self._build_html_report(summary_df, visualizations)
        
        # Save report
        self._save_report(filename, html_content)
        
        return filename
        
    def _prepare_filename(self, filename):
        """Prepare output filename."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"results/benchmark_report_{timestamp}.html"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        return filename
        
    def _group_by_instance(self):
        """Group results by instance name."""
        instances = {}
        for result in self.results:
            if result.instance_name not in instances:
                instances[result.instance_name] = []
            instances[result.instance_name].append(result)
        return instances
        
    def _create_summary_dataframe(self):
        """Create summary DataFrame from results."""
        summary_data = []
        
        for instance_name, results in self.instances.items():
            for result in results:
                summary_data.append({
                    "Instance": result.instance_name,
                    "Algorithm": result.algorithm_name,
                    "Best": f"{result.best_fitness:.2f}",
                    "Mean": f"{result.mean_fitness:.2f} ± {result.std_fitness:.2f}",
                    "Time (s)": f"{result.mean_time:.2f} ± {result.std_time:.2f}",
                    "Gap (%)": f"{result.gap_to_optimal:.2f}"
                    if result.gap_to_optimal is not None
                    else "N/A",
                    "Success (%)": f"{result.success_rate:.2f}"
                    if result.success_rate is not None
                    else "N/A",
                })
        
        return pd.DataFrame(summary_data)
        
    def _prepare_figures_directory(self, filename):
        """Prepare directory for figures."""
        figures_dir = os.path.join(os.path.dirname(filename), "figures")
        os.makedirs(figures_dir, exist_ok=True)
        return figures_dir
        
    def _generate_all_visualizations(self, figures_dir):
        """Generate all visualizations for the report."""
        visualizations = {}
        
        for instance_name, results in self.instances.items():
            instance_results = [
                r for r in self.results if r.instance_name == instance_name
            ]
            
            visualizations[instance_name] = self._generate_instance_visualizations(
                instance_name, instance_results, figures_dir
            )
            
        return visualizations
        
    def _generate_instance_visualizations(self, instance_name, results, figures_dir):
        """Generate visualizations for a single instance."""
        viz = {}
        
        # Solution quality
        viz['quality'] = self._save_plot(
            plot_solution_quality(results),
            figures_dir,
            f"{instance_name}_quality.png"
        )
        
        # Execution time
        viz['time'] = self._save_plot(
            plot_execution_time(results),
            figures_dir,
            f"{instance_name}_time.png"
        )
        
        # Convergence
        viz['convergence'] = self._save_plot(
            plot_convergence_comparison(results),
            figures_dir,
            f"{instance_name}_convergence.png"
        )
        
        # Performance radar
        plt_radar = plot_performance_radar(results, instance_name)
        if plt_radar:
            viz['radar'] = self._save_plot(
                plt_radar,
                figures_dir,
                f"{instance_name}_radar.png"
            )
        
        return viz
        
    def _save_plot(self, plt_obj, figures_dir, filename):
        """Save a plot and return the filename."""
        path = os.path.join(figures_dir, filename)
        plt_obj.savefig(path)
        plt_obj.close()
        return filename
        
    def _build_html_report(self, summary_df, visualizations):
        """Build the HTML report content."""
        html = self._get_html_header()
        html += self._get_summary_section(summary_df)
        
        # Add instance sections
        for instance_name in self.instances:
            html += self._get_instance_section(instance_name, visualizations.get(instance_name, {}))
        
        # Add statistical analysis
        html += self._get_statistical_analysis_section()
        
        html += "</body>\n</html>"
        return html
        
    def _get_html_header(self):
        """Get HTML header with CSS."""
        css = self._get_css_styles()
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Benchmark Report</title>
    <style>
{css}
    </style>
</head>
<body>
    <h1>Benchmark Report</h1>
    <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
"""
        
    def _get_css_styles(self):
        """Get CSS styles for the report."""
        return """body {
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
}"""
        
    def _get_summary_section(self, summary_df):
        """Get HTML for summary section."""
        return f"""
    <div class="section">
        <h2>Summary</h2>
        {summary_df.to_html(index=False)}
    </div>
"""
        
    def _get_instance_section(self, instance_name, visualizations):
        """Get HTML for instance section."""
        html = f"""
    <div class="section">
        <h2>Instance: {instance_name}</h2>
        <p>Optimal value: {OPTIMAL_VALUES.get(instance_name, 'Unknown')}</p>
"""
        
        # Add visualizations
        if 'quality' in visualizations:
            html += f"""
        <div class="figure">
            <img src="figures/{visualizations['quality']}" alt="Solution Quality">
            <div class="caption">Figure: Solution quality comparison for {instance_name}</div>
        </div>
"""
        
        if 'time' in visualizations:
            html += f"""
        <div class="figure">
            <img src="figures/{visualizations['time']}" alt="Execution Time">
            <div class="caption">Figure: Execution time comparison for {instance_name}</div>
        </div>
"""
        
        if 'convergence' in visualizations:
            html += f"""
        <div class="figure">
            <img src="figures/{visualizations['convergence']}" alt="Convergence Curves">
            <div class="caption">Figure: Convergence curve comparison for {instance_name}</div>
        </div>
"""
        
        if 'radar' in visualizations:
            html += f"""
        <div class="figure">
            <img src="figures/{visualizations['radar']}" alt="Performance Radar">
            <div class="caption">Figure: Performance radar chart for {instance_name}</div>
        </div>
"""
        
        html += "    </div>"
        return html
        
    def _get_statistical_analysis_section(self):
        """Get HTML for statistical analysis section."""
        if len(self.results) == 0:
            return ""
            
        html = """
    <div class="section">
        <h2>Statistical Analysis</h2>
"""
        
        # Perform statistical tests for each instance
        for instance_name, results in self.instances.items():
            if len(results) >= 2:
                html += self._perform_statistical_tests(instance_name, results)
        
        html += "    </div>"
        return html
        
    def _perform_statistical_tests(self, instance_name, results):
        """Perform statistical tests for an instance."""
        html = f"<h3>Statistical tests for {instance_name}</h3>"
        
        # Prepare data
        algorithm_names = [r.algorithm_name for r in results]
        samples = [r.fitness_values for r in results]
        
        # Ensure equal sample sizes
        min_samples = min(len(s) for s in samples)
        samples = [s[:min_samples] for s in samples]
        
        if min_samples >= 5 and len(samples) >= 2:
            # Friedman test
            friedman_html = self._perform_friedman_test(samples, algorithm_names)
            if friedman_html:
                html += friedman_html
        
        return html
        
    def _perform_friedman_test(self, samples, algorithm_names):
        """Perform Friedman test and return HTML."""
        try:
            friedman_samples = [list(s) for s in samples]
            statistic, p_value = friedmanchisquare(*friedman_samples)
            
            html = f"""<p>Friedman Test</p>
<table>
    <tr><th>Statistic</th><th>p-value</th><th>Interpretation</th></tr>
    <tr>
        <td>{statistic:.4f}</td>
        <td>{p_value:.4f}</td>
        <td>{"Significant differences exist" if p_value < 0.05 else "No significant differences"}</td>
    </tr>
</table>
"""
            
            # Post-hoc tests if significant
            if p_value < 0.05 and len(samples) > 2:
                html += self._perform_posthoc_tests(samples, algorithm_names)
            
            return html
            
        except Exception as e:
            return f"<p>Error performing Friedman test: {str(e)}</p>"
        
    def _perform_posthoc_tests(self, samples, algorithm_names):
        """Perform post-hoc tests."""
        html = "<p>Post-hoc Wilcoxon Signed-Rank Tests</p>"
        html += """<table>
    <tr><th>Algorithm A</th><th>Algorithm B</th><th>p-value</th><th>Interpretation</th></tr>
"""
        
        for i in range(len(samples)):
            for j in range(i + 1, len(samples)):
                try:
                    stat, p = wilcoxon(samples[i], samples[j])
                    html += f"""    <tr>
        <td>{algorithm_names[i]}</td>
        <td>{algorithm_names[j]}</td>
        <td>{p:.4f}</td>
        <td>{"Significant difference" if p < 0.05 else "No significant difference"}</td>
    </tr>
"""
                except Exception:
                    pass
        
        html += "</table>"
        return html
        
    def _save_report(self, filename, html_content):
        """Save the HTML report."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)




def create_benchmark_report(benchmark_results, filename=None):
    """
    Crea un informe detallado de los resultados del benchmark.
    
    Versión refactorizada que utiliza BenchmarkReportBuilder para reducir
    la complejidad ciclomática de 17 a menos de 10.

    Args:
        benchmark_results: Lista de objetos BenchmarkResult
        filename: Ruta donde guardar el informe (si es None, se genera automáticamente)
    """
    builder = BenchmarkReportBuilder(benchmark_results)
    return builder.create_report(filename)

