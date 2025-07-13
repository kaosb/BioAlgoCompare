#!/usr/bin/env python3
"""
Generate Demonstrations for Imitation Learning
=============================================

This script generates expert demonstrations by running optimized algorithms
(PSO, GA) and collecting their parameter choices for training the IL model.

The demonstrations capture:
- Problem state (instance features, iteration, convergence)
- Expert actions (α, β, γ parameters that led to good performance)
- Outcomes (fitness improvement)

Usage:
    python utils/generate_demos.py --algorithm both --instances P-n16-k8,E-n22-k4 --runs 100
"""

import argparse
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms.ho import HO  # noqa: E402
from problems.vrp import VRPProblem  # noqa: E402
from utils.imitation_learning import create_state_from_problem  # noqa: E402


class SimpleGA:
    """Algoritmo Genético simplificado para optimización de parámetros."""

    def __init__(
        self, population_size: int = 20, generations: int = 50, seed: int = None
    ):
        self.population_size = population_size
        self.generations = generations
        self.rng = np.random.RandomState(seed)

    def optimize_ho_params(
        self, problem, state: Dict, ho_iterations: int = 30
    ) -> Tuple[float, float, float, float]:
        """
        Optimiza parámetros de HO para el estado dado.

        Returns:
            Tupla (α, β, γ, fitness) con los mejores parámetros encontrados
        """
        # Límites de parámetros
        bounds = {"alpha": (0.1, 0.9), "beta": (0.2, 0.8), "gamma": (0.3, 1.0)}

        # Inicializar población
        population = []
        for _ in range(self.population_size):
            individual = {
                "alpha": self.rng.uniform(*bounds["alpha"]),
                "beta": self.rng.uniform(*bounds["beta"]),
                "gamma": self.rng.uniform(*bounds["gamma"]),
                "fitness": float("inf"),
            }
            population.append(individual)

        # Evolución
        for gen in range(self.generations):
            # Evaluar fitness
            for ind in population:
                # Ejecutar HO con estos parámetros
                ho = HO(
                    problem, population_size=10, max_iterations=ho_iterations, seed=42
                )

                # Sobrescribir parámetros
                ho.alpha_min = ho.alpha_max = ind["alpha"]
                ho.beta_min = ho.beta_max = ind["beta"]
                ho.gamma_min = ho.gamma_max = ind["gamma"]

                # Ejecutar y obtener fitness
                best_sol = ho.execute()
                ind["fitness"] = best_sol.fitness()

            # Ordenar por fitness
            population.sort(key=lambda x: x["fitness"])

            # Selección y reproducción
            new_population = population[: self.population_size // 2]  # Elitismo

            # Crossover y mutación
            while len(new_population) < self.population_size:
                # Selección de padres
                parent1 = population[self.rng.randint(0, self.population_size // 2)]
                parent2 = population[self.rng.randint(0, self.population_size // 2)]

                # Crossover
                child = {
                    "alpha": parent1["alpha"]
                    if self.rng.random() < 0.5
                    else parent2["alpha"],
                    "beta": parent1["beta"]
                    if self.rng.random() < 0.5
                    else parent2["beta"],
                    "gamma": parent1["gamma"]
                    if self.rng.random() < 0.5
                    else parent2["gamma"],
                    "fitness": float("inf"),
                }

                # Mutación
                if self.rng.random() < 0.1:
                    param = self.rng.choice(["alpha", "beta", "gamma"])
                    child[param] = self.rng.uniform(*bounds[param])

                new_population.append(child)

            population = new_population

        # Retornar el mejor individuo
        best = population[0]
        return best["alpha"], best["beta"], best["gamma"], best["fitness"]


class SimplePSO:
    """Particle Swarm Optimization simplificado para optimización de parámetros."""

    def __init__(self, swarm_size: int = 20, iterations: int = 50, seed: int = None):
        self.swarm_size = swarm_size
        self.iterations = iterations
        self.rng = np.random.RandomState(seed)

    def optimize_ho_params(
        self, problem, state: Dict, ho_iterations: int = 30
    ) -> Tuple[float, float, float, float]:
        """
        Optimiza parámetros de HO usando PSO.

        Returns:
            Tupla (α, β, γ, fitness) con los mejores parámetros encontrados
        """
        # Límites
        bounds = np.array(
            [
                [0.1, 0.9],  # alpha
                [0.2, 0.8],  # beta
                [0.3, 1.0],  # gamma
            ]
        )

        # Inicializar partículas
        positions = self.rng.uniform(bounds[:, 0], bounds[:, 1], (self.swarm_size, 3))
        velocities = self.rng.uniform(-0.1, 0.1, (self.swarm_size, 3))

        # Mejores posiciones
        pbest_positions = positions.copy()
        pbest_fitness = np.full(self.swarm_size, float("inf"))
        gbest_position = None
        gbest_fitness = float("inf")

        # Parámetros PSO
        w = 0.7  # Inercia
        c1 = 1.5  # Componente cognitivo
        c2 = 1.5  # Componente social

        for iteration in range(self.iterations):
            # Evaluar fitness de cada partícula
            for i in range(self.swarm_size):
                # Ejecutar HO con parámetros de la partícula
                ho = HO(
                    problem, population_size=10, max_iterations=ho_iterations, seed=42
                )

                # Establecer parámetros
                ho.alpha_min = ho.alpha_max = positions[i, 0]
                ho.beta_min = ho.beta_max = positions[i, 1]
                ho.gamma_min = ho.gamma_max = positions[i, 2]

                # Ejecutar y obtener fitness
                best_sol = ho.execute()
                fitness = best_sol.fitness()

                # Actualizar pbest
                if fitness < pbest_fitness[i]:
                    pbest_fitness[i] = fitness
                    pbest_positions[i] = positions[i].copy()

                # Actualizar gbest
                if fitness < gbest_fitness:
                    gbest_fitness = fitness
                    gbest_position = positions[i].copy()

            # Actualizar velocidades y posiciones
            for i in range(self.swarm_size):
                r1 = self.rng.random(3)
                r2 = self.rng.random(3)

                velocities[i] = (
                    w * velocities[i]
                    + c1 * r1 * (pbest_positions[i] - positions[i])
                    + c2 * r2 * (gbest_position - positions[i])
                )

                positions[i] = positions[i] + velocities[i]

                # Mantener dentro de límites
                positions[i] = np.clip(positions[i], bounds[:, 0], bounds[:, 1])

        return gbest_position[0], gbest_position[1], gbest_position[2], gbest_fitness


def generate_demonstrations(
    algorithms: List[str], instances: List[str], num_demos: int, seed: int = 42
) -> pd.DataFrame:
    """
    Genera demostraciones de parámetros óptimos.

    Args:
        algorithms: Lista de algoritmos a usar ['ga', 'pso']
        instances: Lista de instancias VRP
        num_demos: Número de demostraciones a generar
        seed: Semilla para reproducibilidad

    Returns:
        DataFrame con demostraciones
    """
    np.random.seed(seed)
    demonstrations = []

    # Para cada instancia
    for instance in instances:
        print(f"\nProcesando instancia: {instance}")

        # Cargar o crear instancia
        if instance.startswith("Solomon"):
            # Crear instancia sintética tipo Solomon
            problem = VRPProblem(seed=seed)
            # Configurar como instancia Solomon RC101
            n_customers = 25
            problem.nodes = [(0, 0)]  # Depot
            for i in range(n_customers):
                x = np.random.uniform(-50, 50)
                y = np.random.uniform(-50, 50)
                problem.nodes.append((x, y))
            problem.demands = [0] + [
                np.random.randint(5, 20) for _ in range(n_customers)
            ]
            problem.capacity = 100
            problem.dimension = n_customers + 1
            problem.compute_distance_matrix()
        else:
            # Cargar instancia VRP real
            instance_path = f"data/vrp/{instance}.vrp"
            if os.path.exists(instance_path):
                problem = VRPProblem(instance_path)
            else:
                print(
                    f"Advertencia: No se encontró {instance_path}, usando instancia sintética"
                )
                problem = VRPProblem(seed=seed)
                problem.dimension = 20

        # Generar diferentes estados de optimización
        demos_per_instance = num_demos // len(instances)

        for demo_idx in range(demos_per_instance):
            # Simular diferentes etapas de optimización
            progress_stages = [0.1, 0.3, 0.5, 0.7, 0.9]
            stage = np.random.choice(progress_stages)

            # Crear un HO temporal para generar estado realista
            ho_temp = HO(
                problem, population_size=20, max_iterations=100, seed=seed + demo_idx
            )
            ho_temp.initialize_population()

            # Ejecutar hasta cierto progreso
            target_iter = int(stage * ho_temp.max_iterations)
            for _ in range(target_iter):
                ho_temp.update_population()

            # Crear estado
            state = create_state_from_problem(
                problem, ho_temp, target_iter, ho_temp.max_iterations
            )

            # Optimizar parámetros con cada algoritmo
            for algo_name in algorithms:
                print(
                    f"  Demo {demo_idx+1}/{demos_per_instance} - Algoritmo: {algo_name}, Progreso: {stage:.1f}"
                )

                if algo_name.lower() == "ga":
                    optimizer = SimpleGA(
                        population_size=10, generations=20, seed=seed + demo_idx
                    )
                elif algo_name.lower() == "pso":
                    optimizer = SimplePSO(
                        swarm_size=10, iterations=20, seed=seed + demo_idx
                    )
                else:
                    print(f"Algoritmo {algo_name} no reconocido")
                    continue

                # Optimizar parámetros
                alpha, beta, gamma, fitness = optimizer.optimize_ho_params(
                    problem, state, ho_iterations=20
                )

                # Guardar demostración
                demo = state.copy()
                demo["instance"] = instance
                demo["algorithm"] = algo_name
                demo["alpha"] = alpha
                demo["beta"] = beta
                demo["gamma"] = gamma
                demo["fitness"] = fitness
                demonstrations.append(demo)

    return pd.DataFrame(demonstrations)


def main():
    parser = argparse.ArgumentParser(description="Generar demostraciones para IL de HO")
    parser.add_argument(
        "--algorithms",
        type=str,
        default="ga,pso",
        help="Algoritmos a usar (separados por coma)",
    )
    parser.add_argument(
        "--instances",
        type=str,
        default="Solomon-RC101",
        help="Instancias VRP (separadas por coma)",
    )
    parser.add_argument(
        "--num", type=int, default=500, help="Número de demostraciones a generar"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Semilla para reproducibilidad"
    )
    parser.add_argument(
        "--output", type=str, default="demos_ho_il.csv", help="Archivo de salida"
    )

    args = parser.parse_args()

    # Parsear algoritmos e instancias
    algorithms = [a.strip() for a in args.algorithms.split(",")]
    instances = [i.strip() for i in args.instances.split(",")]

    print(f"Generando {args.num} demostraciones...")
    print(f"Algoritmos: {algorithms}")
    print(f"Instancias: {instances}")
    print(f"Semilla: {args.seed}")

    # Generar demostraciones
    start_time = datetime.now()
    demos_df = generate_demonstrations(algorithms, instances, args.num, args.seed)
    end_time = datetime.now()

    # Guardar resultados
    output_path = os.path.join("results", args.output)
    os.makedirs("results", exist_ok=True)
    demos_df.to_csv(output_path, index=False)

    print(
        f"\nDemostraciones generadas en {(end_time - start_time).total_seconds():.2f} segundos"
    )
    print(f"Guardadas en: {output_path}")
    print(f"Total de demostraciones: {len(demos_df)}")
    print("\nEstadísticas de parámetros óptimos:")
    print(f"  Alpha: {demos_df['alpha'].mean():.3f} ± {demos_df['alpha'].std():.3f}")
    print(f"  Beta:  {demos_df['beta'].mean():.3f} ± {demos_df['beta'].std():.3f}")
    print(f"  Gamma: {demos_df['gamma'].mean():.3f} ± {demos_df['gamma'].std():.3f}")


if __name__ == "__main__":
    main()
