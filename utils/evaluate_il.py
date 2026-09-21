#!/usr/bin/env python3
"""
Script para evaluar la mejora de HO con Imitation Learning.

Compara el rendimiento de HO estándar vs HO+IL en términos de:
- Convergencia
- Calidad de soluciones
- Hipervolumen (para problemas multiobjetivo)

Uso:
    python utils/evaluate_il.py --instances P-n16-k8,E-n22-k4 --runs 30 --model models/ho_il_model.pth
"""

import argparse
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms.ho import HO  # noqa: E402
from problems.vrp import VRPProblem  # noqa: E402


def calculate_hypervolume(
    solutions: List[Tuple[float, float, float]],
    reference_point: Tuple[float, float, float] = None,
) -> float:
    """
    Calcula el hipervolumen para un conjunto de soluciones multiobjetivo.

    Args:
        solutions: Lista de tuplas (obj1, obj2, obj3)
        reference_point: Punto de referencia (peor caso)

    Returns:
        Hipervolumen del conjunto de soluciones
    """
    if not solutions:
        return 0.0

    # Si no hay punto de referencia, usar el peor de cada objetivo + 10%
    if reference_point is None:
        max_obj1 = max(s[0] for s in solutions) * 1.1
        max_obj2 = max(s[1] for s in solutions) * 1.1
        max_obj3 = max(s[2] for s in solutions) * 1.1
        reference_point = (max_obj1, max_obj2, max_obj3)

    # Simplificación: usar producto de las diferencias (aproximación)
    # Para cálculo exacto, usar pymoo o similar
    hypervolume = 0.0
    for sol in solutions:
        volume = 1.0
        for i in range(3):
            diff = reference_point[i] - sol[i]
            if diff > 0:
                volume *= diff
            else:
                volume = 0
                break
        hypervolume += volume

    return hypervolume


def evaluate_algorithms(
    instance_name: str, runs: int, il_model_path: str = None
) -> Dict:
    """
    Evalúa HO estándar vs HO+IL en una instancia.

    Returns:
        Diccionario con métricas comparativas
    """
    # Cargar instancia
    instance_path = f"data/vrp/{instance_name}.vrp"
    if os.path.exists(instance_path):
        problem = VRPProblem(instance_path, seed=42)
    else:
        # Instancia sintética
        print(f"Creando instancia sintética para {instance_name}")
        problem = VRPProblem(seed=42)
        n_customers = 20
        problem.nodes = [(0, 0)]
        for _ in range(n_customers):
            x = np.random.uniform(-50, 50)
            y = np.random.uniform(-50, 50)
            problem.nodes.append((x, y))
        problem.demands = [0] + [np.random.randint(5, 20) for _ in range(n_customers)]
        problem.capacity = 100
        problem.dimension = n_customers + 1
        problem.compute_distance_matrix()

    results = {
        "standard": {
            "fitness": [],
            "convergence_curves": [],
            "execution_times": [],
            "final_params": [],
        },
        "il": {
            "fitness": [],
            "convergence_curves": [],
            "execution_times": [],
            "final_params": [],
        },
    }

    # Configuración común
    population_size = 30
    max_iterations = 100

    print(f"\nEvaluando en {instance_name} con {runs} ejecuciones...")

    for run in range(runs):
        seed = 42 + run

        # HO Estándar
        ho_standard = HO(
            problem, population_size, max_iterations, seed=seed, use_il=False
        )
        start_time = datetime.now()
        best_standard = ho_standard.execute()
        time_standard = (datetime.now() - start_time).total_seconds()

        results["standard"]["fitness"].append(best_standard.fitness())
        results["standard"]["convergence_curves"].append(
            ho_standard.get_convergence_curve()
        )
        results["standard"]["execution_times"].append(time_standard)

        # Parámetros finales (promedio de la última iteración)
        final_alpha = (
            ho_standard.alpha_min
            + (ho_standard.alpha_max - ho_standard.alpha_min) * 0.5
        )
        final_beta = (
            ho_standard.beta_min + (ho_standard.beta_max - ho_standard.beta_min) * 0.5
        )
        final_gamma = (
            ho_standard.gamma_min
            + (ho_standard.gamma_max - ho_standard.gamma_min) * 0.5
        )
        results["standard"]["final_params"].append(
            (final_alpha, final_beta, final_gamma)
        )

        # HO con IL
        ho_il = HO(
            problem,
            population_size,
            max_iterations,
            seed=seed,
            use_il=True,
            il_model_path=il_model_path,
        )
        start_time = datetime.now()
        best_il = ho_il.execute()
        time_il = (datetime.now() - start_time).total_seconds()

        results["il"]["fitness"].append(best_il.fitness())
        results["il"]["convergence_curves"].append(ho_il.get_convergence_curve())
        results["il"]["execution_times"].append(time_il)

        # Los parámetros de IL son dinámicos, tomar el último usado
        if ho_il.use_il:
            # Aproximación: usar valores medios
            results["il"]["final_params"].append((0.5, 0.5, 0.65))
        else:
            results["il"]["final_params"].append((final_alpha, final_beta, final_gamma))

        if (run + 1) % 5 == 0:
            print(f"  Progreso: {run + 1}/{runs}")

    return results


def analyze_results(results: Dict, instance_name: str) -> Dict:
    """Analiza y compara resultados."""
    analysis = {}

    # Fitness
    fitness_standard = results["standard"]["fitness"]
    fitness_il = results["il"]["fitness"]

    analysis["fitness"] = {
        "standard_mean": np.mean(fitness_standard),
        "standard_std": np.std(fitness_standard),
        "standard_best": np.min(fitness_standard),
        "il_mean": np.mean(fitness_il),
        "il_std": np.std(fitness_il),
        "il_best": np.min(fitness_il),
        "improvement_mean": (np.mean(fitness_standard) - np.mean(fitness_il))
        / np.mean(fitness_standard)
        * 100,
        "improvement_best": (np.min(fitness_standard) - np.min(fitness_il))
        / np.min(fitness_standard)
        * 100,
    }

    # Tiempo de ejecución
    time_standard = results["standard"]["execution_times"]
    time_il = results["il"]["execution_times"]

    analysis["time"] = {
        "standard_mean": np.mean(time_standard),
        "il_mean": np.mean(time_il),
        "overhead": (np.mean(time_il) - np.mean(time_standard))
        / np.mean(time_standard)
        * 100,
    }

    # Calcular área bajo la curva de convergencia (menor es mejor)
    auc_standard = [
        np.trapezoid(curve) for curve in results["standard"]["convergence_curves"]
    ]
    auc_il = [np.trapezoid(curve) for curve in results["il"]["convergence_curves"]]

    mean_auc_standard = np.mean(auc_standard)
    mean_auc_il = np.mean(auc_il)
    
    # Evitar división por cero
    auc_improvement = 0.0
    if mean_auc_standard > 0:
        auc_improvement = (mean_auc_standard - mean_auc_il) / mean_auc_standard * 100
    
    analysis["convergence"] = {
        "auc_standard": mean_auc_standard,
        "auc_il": mean_auc_il,
        "auc_improvement": auc_improvement,
    }

    # Test estadístico (Mann-Whitney U)
    from scipy.stats import mannwhitneyu

    statistic, p_value = mannwhitneyu(fitness_il, fitness_standard, alternative="less")

    analysis["statistical"] = {
        "mann_whitney_statistic": statistic,
        "p_value": p_value,
        "significant": p_value < 0.05,
    }

    return analysis


def plot_comparison(results: Dict, analysis: Dict, instance_name: str, output_dir: str):
    """Genera gráficos comparativos."""
    os.makedirs(output_dir, exist_ok=True)

    # 1. Box plot de fitness
    plt.figure(figsize=(10, 6))
    data = [results["standard"]["fitness"], results["il"]["fitness"]]
    plt.boxplot(data, labels=["HO Estándar", "HO + IL"])
    plt.ylabel("Fitness (Distancia)")
    plt.title(f"Comparación de Fitness - {instance_name}")
    plt.grid(True, alpha=0.3)

    # Agregar estadísticas
    plt.text(
        0.02,
        0.98,
        f"Mejora promedio: {analysis['fitness']['improvement_mean']:.2f}%",
        transform=plt.gca().transAxes,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"fitness_comparison_{instance_name}.png"))
    plt.close()

    # 2. Curvas de convergencia promedio
    plt.figure(figsize=(12, 6))

    # Calcular curvas promedio
    max_len = max(len(curve) for curve in results["standard"]["convergence_curves"])

    standard_curves = np.zeros(
        (len(results["standard"]["convergence_curves"]), max_len)
    )
    il_curves = np.zeros((len(results["il"]["convergence_curves"]), max_len))

    for i, curve in enumerate(results["standard"]["convergence_curves"]):
        standard_curves[i, : len(curve)] = curve
        standard_curves[i, len(curve) :] = curve[-1]

    for i, curve in enumerate(results["il"]["convergence_curves"]):
        il_curves[i, : len(curve)] = curve
        il_curves[i, len(curve) :] = curve[-1]

    mean_standard = np.mean(standard_curves, axis=0)
    mean_il = np.mean(il_curves, axis=0)
    std_standard = np.std(standard_curves, axis=0)
    std_il = np.std(il_curves, axis=0)

    iterations = range(max_len)

    plt.plot(iterations, mean_standard, "b-", label="HO Estándar", linewidth=2)
    plt.fill_between(
        iterations,
        mean_standard - std_standard,
        mean_standard + std_standard,
        alpha=0.3,
        color="blue",
    )

    plt.plot(iterations, mean_il, "r-", label="HO + IL", linewidth=2)
    plt.fill_between(
        iterations, mean_il - std_il, mean_il + std_il, alpha=0.3, color="red"
    )

    plt.xlabel("Iteración")
    plt.ylabel("Fitness")
    plt.title(f"Curvas de Convergencia - {instance_name}")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"convergence_comparison_{instance_name}.png"))
    plt.close()

    # 3. Distribución de parámetros finales
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    params_standard = np.array(results["standard"]["final_params"])
    params_il = np.array(results["il"]["final_params"])

    param_names = ["Alpha (α)", "Beta (β)", "Gamma (γ)"]

    for i, (ax, name) in enumerate(zip(axes, param_names)):
        ax.hist(
            params_standard[:, i], bins=15, alpha=0.5, label="HO Estándar", color="blue"
        )
        ax.hist(params_il[:, i], bins=15, alpha=0.5, label="HO + IL", color="red")
        ax.set_xlabel(name)
        ax.set_ylabel("Frecuencia")
        ax.set_title(f"Distribución de {name}")
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.suptitle(f"Parámetros Finales - {instance_name}")
    plt.tight_layout()
    plt.savefig(
        os.path.join(output_dir, f"parameters_distribution_{instance_name}.png")
    )
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Evaluar mejora de HO con IL")
    parser.add_argument(
        "--instances",
        type=str,
        default="P-n16-k8,E-n22-k4",
        help="Instancias VRP (separadas por coma)",
    )
    parser.add_argument(
        "--runs", type=int, default=30, help="Número de ejecuciones por instancia"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="models/ho_il_model.pth",
        help="Ruta al modelo IL entrenado",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/il_evaluation",
        help="Directorio para resultados",
    )

    args = parser.parse_args()

    instances = [i.strip() for i in args.instances.split(",")]

    print("Evaluación de HO con Imitation Learning")
    print(f"Instancias: {instances}")
    print(f"Ejecuciones por instancia: {args.runs}")
    print(f"Modelo IL: {args.model}")

    # Verificar si existe el modelo
    if not os.path.exists(args.model):
        print(f"\nAdvertencia: No se encontró el modelo {args.model}")
        print("La evaluación usará HO sin IL entrenado (modo fallback)")

    # Resultados globales
    global_results = {}

    for instance in instances:
        # Evaluar
        results = evaluate_algorithms(instance, args.runs, args.model)

        # Analizar
        analysis = analyze_results(results, instance)

        # Guardar
        global_results[instance] = {"results": results, "analysis": analysis}

        # Generar gráficos
        plot_comparison(results, analysis, instance, args.output_dir)

        # Imprimir resumen
        print(f"\n=== Resultados para {instance} ===")
        print("Fitness promedio:")
        print(
            f"  HO Estándar: {analysis['fitness']['standard_mean']:.2f} ± {analysis['fitness']['standard_std']:.2f}"
        )
        print(
            f"  HO + IL:     {analysis['fitness']['il_mean']:.2f} ± {analysis['fitness']['il_std']:.2f}"
        )
        print(f"  Mejora:      {analysis['fitness']['improvement_mean']:.2f}%")
        print("\nMejor fitness:")
        print(f"  HO Estándar: {analysis['fitness']['standard_best']:.2f}")
        print(f"  HO + IL:     {analysis['fitness']['il_best']:.2f}")
        print(f"  Mejora:      {analysis['fitness']['improvement_best']:.2f}%")
        print("\nSignificancia estadística:")
        print(f"  p-valor: {analysis['statistical']['p_value']:.4f}")
        print(
            f"  Significativo: {'Sí' if analysis['statistical']['significant'] else 'No'}"
        )
        print("\nTiempo de ejecución:")
        print(f"  Overhead IL: {analysis['time']['overhead']:.2f}%")

    # Guardar resumen
    summary_path = os.path.join(args.output_dir, "evaluation_summary.csv")
    summary_data = []

    for instance, data in global_results.items():
        analysis = data["analysis"]
        summary_data.append(
            {
                "instance": instance,
                "fitness_mean_standard": analysis["fitness"]["standard_mean"],
                "fitness_mean_il": analysis["fitness"]["il_mean"],
                "improvement_mean": analysis["fitness"]["improvement_mean"],
                "fitness_best_standard": analysis["fitness"]["standard_best"],
                "fitness_best_il": analysis["fitness"]["il_best"],
                "improvement_best": analysis["fitness"]["improvement_best"],
                "p_value": analysis["statistical"]["p_value"],
                "significant": analysis["statistical"]["significant"],
                "time_overhead": analysis["time"]["overhead"],
                "auc_improvement": analysis["convergence"]["auc_improvement"],
            }
        )

    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(summary_path, index=False)

    print("\n✓ Evaluación completada")
    print(f"Resultados guardados en: {args.output_dir}")

    # Resumen global
    if len(instances) > 1:
        print("\n=== Resumen Global ===")
        print(
            f"Mejora promedio en fitness: {summary_df['improvement_mean'].mean():.2f}%"
        )
        print(
            f"Mejora promedio en mejor solución: {summary_df['improvement_best'].mean():.2f}%"
        )
        print(
            f"Instancias con mejora significativa: {summary_df['significant'].sum()}/{len(instances)}"
        )


if __name__ == "__main__":
    main()
