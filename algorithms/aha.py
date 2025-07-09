"""
Artificial Hummingbird Algorithm (AHA)
Fuente: Zhao, Wang & Mirjalili (2022), Computer Methods in Applied Mechanics and Engineering.
DOI: 10.1016/j.cma.2021.114194
"""

import numpy as np
import random
from typing import List, Tuple
from copy import deepcopy
from algorithms.base import Individual, MetaheuristicAlgorithm


class Hummingbird(Individual):
    """Individual hummingbird in the AHA algorithm.

    Represents a hummingbird with its position, memory table, and foraging behaviors.
    Hummingbirds exhibit three flight skills and two modes of foraging.

    Attributes:
        position: Current position in the search space
        personal_best_position: Best position found by this hummingbird
        bounds: Search space boundaries
        dimension: Number of dimensions in the problem
        memory_table: Set of visited food sources to avoid revisiting
        _fitness: Cached fitness value
    """

    def __init__(self, position: np.ndarray, bounds: List[Tuple[float, float]]):
        self.position = np.array(position, dtype=float)
        self.personal_best_position = self.position.copy()
        self._fitness = None
        self.bounds = bounds
        self.dimension = len(position)
        self.memory_table = set()

    def fitness(self, objective_function=None):
        """Calculate or return cached fitness value."""
        if objective_function is not None and self._fitness is None:
            self._fitness = objective_function(self.position)
        return self._fitness

    def is_better_than(self, other):
        """Compare if this individual is better than other."""
        return bool(self._fitness < other._fitness)

    def is_feasible(self):
        """Check if the individual represents a feasible solution."""
        return True  # Assuming bound constraints are enforced elsewhere

    def move(self, population=None, iteration=None, max_iterations=None):
        """
        Implementa el movimiento del colibrí según el tipo de vuelo y modo de forrajeo.
        Adaptado para la interfaz requerida por la clase base Individual.

        Args:
            population: La población actual de individuos.
            iteration: La iteración actual del algoritmo.
            max_iterations: El número máximo de iteraciones.
        """
        # Esta implementación específica de AHA será llamada desde update_population()
        # y no a través de esta interfaz, por lo que no necesitamos implementar la lógica aquí
        pass

    def aha_move(
        self, best_individual, population: List["Hummingbird"], memory_table: set
    ):
        """
        Implementa el movimiento del colibrí según el tipo de vuelo y modo de forrajeo.
        """
        # Selección aleatoria del tipo de vuelo: axial, diagonal u omnidireccional
        flight_type = np.random.choice(["axial", "diagonal", "omnidirectional"])

        # Selección aleatoria del modo de forrajeo: guiado, territorial, migratorio
        forage_mode = np.random.choice(["guided", "territorial", "migratory"])

        new_position = self.position.copy()
        dim = self.dimension

        if flight_type == "axial":
            # Movimiento en una sola dimensión (eje)
            axis = np.random.randint(0, dim)
            step = np.random.uniform(-1, 1)
            direction = np.zeros(dim)
            direction[axis] = step
        elif flight_type == "diagonal":
            # Movimiento en una diagonal (subconjunto de dimensiones)
            direction = np.random.uniform(-1, 1, size=dim)
            # Para simular diagonal, poner algunos ceros aleatorios
            zero_mask = np.random.rand(dim) < 0.5
            direction[zero_mask] = 0
        else:  # omnidireccional
            # Movimiento en cualquier dirección
            direction = np.random.uniform(-1, 1, size=dim)

        # Normalizar dirección para que el paso sea proporcional
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction = direction / norm

        # Parámetros del paso (pueden ajustarse)
        step_size = 0.1  # tamaño base del paso

        if forage_mode == "guided":
            # Eq. 6: Movimiento hacia el mejor individuo con memoria
            diff = best_individual.personal_best_position - self.position
            new_position = self.position + step_size * diff + step_size * direction
        elif forage_mode == "territorial":
            # Eq. 7: Perturbación aleatoria local
            new_position = self.position + step_size * direction * np.random.uniform(
                -1, 1
            )
        else:  # migratory
            # Eq. 8: Hacia un individuo aleatorio lejos
            other = self
            while other is self:
                other = np.random.choice(population)
            diff = other.position - self.position
            new_position = self.position + step_size * diff + step_size * direction

        # Clip para mantener dentro de los límites
        for i in range(dim):
            low, high = self.bounds[i]
            new_position[i] = np.clip(new_position[i], low, high)

        # Discretizar posición para la tabla de memoria
        discretized_pos = tuple(np.round(new_position, decimals=6))

        # Verificar si la posición ya está en la memoria para evitar repetir
        if discretized_pos in memory_table:
            # Si ya visitado, hacer un pequeño movimiento aleatorio para evitar estancamiento
            new_position += step_size * np.random.uniform(-1, 1, size=dim)
            for i in range(dim):
                low, high = self.bounds[i]
                new_position[i] = np.clip(new_position[i], low, high)
            discretized_pos = tuple(np.round(new_position, decimals=6))

        # Actualizar posición y memoria
        self.position = new_position
        self._fitness = None  # reset fitness
        memory_table.add(discretized_pos)

    def copy(self, other=None):
        """
        Copia los valores de otro individuo a este, o crea una copia si no se proporciona otro.

        Args:
            other: Otro individuo del que copiar (opcional).

        Returns:
            Una copia del individuo si other es None, o None si se copiaron atributos.
        """
        if other is None:
            # Crear y devolver una nueva copia
            new_copy = Hummingbird(self.position.copy(), self.bounds)
            new_copy.personal_best_position = self.personal_best_position.copy()
            new_copy._fitness = self._fitness
            return new_copy
        else:
            # Copiar atributos desde other
            self.position = other.position.copy()
            self.personal_best_position = other.personal_best_position.copy()
            self._fitness = other._fitness
            self.bounds = other.bounds
            self.dimension = other.dimension
            return None


class AHA(MetaheuristicAlgorithm):
    """Artificial Hummingbird Algorithm (AHA) implementation.

    A bio-inspired metaheuristic that simulates the intelligent foraging behavior
    and flight skills of hummingbirds. The algorithm incorporates three flight
    skills (diagonal, omnidirectional, and axial) and two foraging modes
    (guided and territorial).

    Args:
        problem: The optimization problem to solve
        population_size: Number of hummingbirds in the population (default: 30)
        max_iterations: Maximum number of iterations (default: 100)
        seed: Random seed for reproducibility (default: None)

    Attributes:
        population: List of Hummingbird individuals
        memory_table: Global memory of visited food sources
        best_solution: Best solution found so far
        convergence_curve: Fitness values over iterations
    """

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        super().__init__(problem, population_size, max_iterations, seed)
        self.population: List[Hummingbird] = []
        self.memory_table = set()
        self.best_solution = None
        self.convergence_curve = []

    def initialize_population(self):
        # Set random seed if provided
        if self.seed is not None:
            np.random.seed(self.seed)

        self.population = []
        # Para el problema VRP, usamos el dominio [0,1] por cada dimensión
        dim = self.problem.get_dimension()
        bounds = [(0, 1) for _ in range(dim)]

        for _ in range(self.population_size):
            position = np.random.uniform(0, 1, size=dim)
            hummingbird = Hummingbird(position, bounds)
            discretized_pos = tuple(np.round(position, decimals=6))
            self.memory_table.add(discretized_pos)
            self.population.append(hummingbird)
        # Inicializar fitness
        for ind in self.population:
            ind._fitness = self.problem.evaluate(ind.position)
        # Inicializar mejor solución
        self.best_solution = min(self.population, key=lambda ind: ind.fitness()).copy()
        # Registrar el fitness inicial en la curva de convergencia
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        # Ordenar población por fitness
        for ind in self.population:
            if ind._fitness is None:
                ind._fitness = self.problem.evaluate(ind.position)
        self.population.sort(key=lambda ind: ind.fitness())
        # Actualizar mejor solución
        current_best = self.population[0]
        if current_best.fitness() < self.best_solution.fitness():
            self.best_solution = current_best.copy()

        # Aplicar aha_move a todos menos el mejor
        for ind in self.population[1:]:
            ind.aha_move(self.best_solution, self.population, self.memory_table)
            # Actualizar personal best si mejora
            current_fitness = self.problem.evaluate(ind.position)
            ind._fitness = current_fitness

            # Calcular el fitness de personal_best_position
            best_fitness = self.problem.evaluate(ind.personal_best_position)

            if current_fitness < best_fitness:
                ind.personal_best_position = ind.position.copy()

        self.convergence_curve.append(self.best_solution.fitness())

    # No need to implement run or execute - using the base class's execute method
