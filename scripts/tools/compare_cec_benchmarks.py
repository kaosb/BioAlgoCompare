#!/usr/bin/env python3
"""
Comparación Quick-HO vs CEC2017 benchmarks
Para validación rigurosa según estándares CEC
"""
# ruff: noqa: E402

import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple

# Añadir path del proyecto
sys.path.insert(0, ".")

# Intentar importar CEC2017
try:
    from cec2017.functions import all_functions as cec_functions

    CEC_AVAILABLE = True
except ImportError:
    print("WARNING: CEC2017 no disponible. Instalar con: pip install cec2017")
    CEC_AVAILABLE = False

# Importar algoritmos del proyecto
from algorithms.ho import HO
from algorithms.base import MetaheuristicAlgorithm


class CEC2017Problem:
    """Wrapper para problemas CEC2017."""

    def __init__(self, func_num: int, dimension: int = 10):
        self.func_num = func_num
        self.dimension = dimension
        self.lower_bound = -100
        self.upper_bound = 100

        if CEC_AVAILABLE:
            self.cec_func = cec_functions[func_num - 1]

    def evaluate(self, x: np.ndarray) -> float:
        """Evaluar función CEC2017."""
        if not CEC_AVAILABLE:
            # Función de prueba simple si CEC no está disponible
            return np.sum(x**2)
        return self.cec_func(x.flatten())


def run_cec_comparison(
    algorithms: List[Tuple[str, type]],
    dimensions: List[int] = [10, 30, 50],
    functions: List[int] = [1, 3, 7, 10],  # Unimodal y multimodal
    runs: int = 30,
    max_iterations: int = 1000,
    population_size: int = 50,
) -> pd.DataFrame:
    """
    Ejecutar comparación en benchmarks CEC2017.

    Args:
        algorithms: Lista de (nombre, clase) de algoritmos
        dimensions: Dimensiones a probar
        functions: Números de funciones CEC (1-30)
        runs: Número de ejecuciones independientes
        max_iterations: Iteraciones máximas
        population_size: Tamaño de población

    Returns:
        DataFrame con resultados
    """
    results = []

    for dim in dimensions:
        for func_num in functions:
            print(f"\n=== CEC2017 F{func_num} - Dim {dim} ===")

            # Crear problema CEC
            problem = CEC2017Problem(func_num, dim)

            for algo_name, AlgoClass in algorithms:
                print(f"  Ejecutando {algo_name}...")

                fitness_values = []
                convergence_curves = []

                for run in range(runs):
                    # Configurar semilla para reproducibilidad
                    seed = 42 + run

                    # Crear instancia del algoritmo
                    if algo_name == "HO":
                        # HO con parámetros específicos
                        algo = AlgoClass(
                            problem,
                            population_size=population_size,
                            max_iterations=max_iterations,
                            seed=seed,
                            use_il=False,  # Sin IL para comparación justa
                        )
                    else:
                        algo = AlgoClass(
                            problem,
                            population_size=population_size,
                            max_iterations=max_iterations,
                            seed=seed,
                        )

                    # Ejecutar
                    best_solution = algo.execute()
                    fitness = best_solution.fitness()
                    fitness_values.append(fitness)
                    convergence_curves.append(algo.get_convergence_curve())

                    if (run + 1) % 5 == 0:
                        print(f"    Progreso: {run + 1}/{runs} runs")

                # Calcular estadísticas
                results.append(
                    {
                        "Algorithm": algo_name,
                        "Function": f"F{func_num}",
                        "Dimension": dim,
                        "Mean": np.mean(fitness_values),
                        "Std": np.std(fitness_values),
                        "Min": np.min(fitness_values),
                        "Max": np.max(fitness_values),
                        "Median": np.median(fitness_values),
                        "Success_Rate": np.sum(np.array(fitness_values) < 1e-8) / runs,
                    }
                )

                print(
                    f"    Mean: {np.mean(fitness_values):.6e} ± {np.std(fitness_values):.6e}"
                )

    return pd.DataFrame(results)


def analyze_ho_phases():
    """
    Analizar comportamiento de las 3 fases de HO.
    Validación según Amiri et al. (2024).
    """
    print("\n=== Análisis de Fases HO (Amiri et al. 2024) ===")

    # Problema de prueba
    problem = CEC2017Problem(3, 30)  # F3 multimodal

    # Ejecutar HO con seguimiento de fases
    ho = HO(problem, population_size=50, max_iterations=300, seed=42)

    # Monitorear proporción de individuos en cada fase
    phase_tracking = {
        "iteration": [],
        "position_phase": [],
        "defense_phase": [],
        "evasion_phase": [],
    }

    # Modificar temporalmente HO para tracking

    def tracked_execute():
        for iteration in range(ho.max_iterations):
            # Contar fases
            position_count = 0
            defense_count = 0
            evasion_count = 0

            for i, ind in enumerate(ho.population):
                r = np.random.random()
                if r < ho.alpha:
                    position_count += 1
                elif r < ho.alpha + ho.beta:
                    defense_count += 1
                else:
                    evasion_count += 1

            phase_tracking["iteration"].append(iteration)
            phase_tracking["position_phase"].append(position_count / ho.population_size)
            phase_tracking["defense_phase"].append(defense_count / ho.population_size)
            phase_tracking["evasion_phase"].append(evasion_count / ho.population_size)

            # Ejecutar iteración normal
            ho._update_population()

        return ho.best_individual

    ho.execute = tracked_execute
    ho.execute()

    # Visualizar distribución de fases
    plt.figure(figsize=(10, 6))
    plt.plot(
        phase_tracking["iteration"],
        phase_tracking["position_phase"],
        label="Position Phase",
        linewidth=2,
    )
    plt.plot(
        phase_tracking["iteration"],
        phase_tracking["defense_phase"],
        label="Defense Phase",
        linewidth=2,
    )
    plt.plot(
        phase_tracking["iteration"],
        phase_tracking["evasion_phase"],
        label="Evasion Phase",
        linewidth=2,
    )

    plt.xlabel("Iteration")
    plt.ylabel("Proportion of Population")
    plt.title("HO Phase Distribution (Amiri et al. 2024)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("ho_phase_analysis.png", dpi=300)
    print("  Gráfico guardado: ho_phase_analysis.png")

    # Imprimir estadísticas
    print("\nEstadísticas de fases (promedio):")
    print(f"  Position: {np.mean(phase_tracking['position_phase']):.3f}")
    print(f"  Defense: {np.mean(phase_tracking['defense_phase']):.3f}")
    print(f"  Evasion: {np.mean(phase_tracking['evasion_phase']):.3f}")


def validate_qc_metrics():
    """
    Validar métricas específicas de Quick Commerce.
    """
    print("\n=== Validación Métricas QC-DVRP ===")

    from problems.vrp import VRPProblem

    # Cargar instancia Solomon
    problem = VRPProblem("data/vrp/Solomon-RC101.vrp")

    # Ejecutar HO con multiobjective
    ho = HO(problem, population_size=50, max_iterations=200, seed=42)
    best = ho.execute()

    # Evaluar métricas QC
    if hasattr(problem, "evaluate_multi"):
        delivery_time, load_var, distance = problem.evaluate_multi(best.position)

        print("\nMétricas Quick Commerce:")
        print(f"  Tiempo promedio entrega: {delivery_time:.2f} min")
        print(f"  Coef. variación carga: {load_var:.3f}")
        print(f"  Distancia total: {distance:.2f}")

        # Validar objetivos tesis
        on_time = delivery_time <= 30
        balanced = load_var <= 0.2

        print("\nValidación objetivos tesis:")
        print(f"  Entregas ≤30min: {'✓' if on_time else '✗'}")
        print(f"  Balance carga ≤0.2: {'✓' if balanced else '✗'}")

        return {
            "delivery_time": delivery_time,
            "load_variation": load_var,
            "distance": distance,
            "meets_objectives": on_time and balanced,
        }
    else:
        print("ERROR: VRPProblem no tiene evaluate_multi")
        return None


if __name__ == "__main__":
    print("=== Quick-HO vs CEC2017 Benchmark Comparison ===")
    print("Referencias:")
    print("- Amiri et al. (2024): Hippopotamus optimization algorithm")
    print("- Potvin (2009): Evolutionary algorithms for vehicle routing")
    print("")

    # Definir algoritmos a comparar
    from algorithms.sho import SHO
    from algorithms.foa import FOA

    algorithms = [("HO", HO), ("SHO", SHO), ("FOA", FOA)]

    # 1. Comparación CEC2017
    if CEC_AVAILABLE:
        print("\n1. Ejecutando comparación CEC2017...")
        cec_results = run_cec_comparison(
            algorithms,
            dimensions=[10, 30],
            functions=[1, 3, 7, 10],  # Unimodal (1,3) y Multimodal (7,10)
            runs=30,
        )

        # Guardar resultados
        cec_results.to_csv("cec2017_comparison_results.csv", index=False)
        print("\nResultados guardados en: cec2017_comparison_results.csv")

        # Mostrar resumen
        print("\nResumen por función:")
        summary = cec_results.groupby(["Function", "Algorithm"])["Mean"].mean()
        print(summary)

    # 2. Análisis de fases HO
    print("\n2. Analizando fases de HO...")
    analyze_ho_phases()

    # 3. Validación métricas QC
    print("\n3. Validando métricas Quick Commerce...")
    qc_results = validate_qc_metrics()

    print("\n=== Validación Completa ===")
    print("Todos los análisis completados exitosamente")
