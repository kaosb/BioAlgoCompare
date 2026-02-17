"""Flamingo Algorithm (FGO).

This module implements the Flamingo Algorithm, a bio-inspired metaheuristic
based on the behavior of flamingos in nature.

The algorithm simulates flamingo behaviors including:
1. Foraging behavior in shallow waters
2. Group migration patterns
3. Social hierarchy within the flock
4. Filter feeding mechanisms

Reference:
    Wang, Z., & Liu, J. (2021).
    Flamingo Search Algorithm: A New Swarm Intelligence Optimization Algorithm.
    IEEE Access, 9, 85975-85993.
    DOI: 10.1109/ACCESS.2021.3086023

Example:
    >>> from algorithms.fgo import FGO
    >>> from problems.vrp import VRPProblem
    >>>
    >>> # Load a VRP instance
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>>
    >>> # Initialize and run FGO
    >>> algo = FGO(problem, population_size=30)
    >>> algo.initialize_population()
    >>> best_solution = algo.run(iterations=100)
"""
import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm


class Flamingo(Individual):
    """Clase para representar un individuo en el algoritmo FGO."""

    def __init__(self, problem, rng=None, py_rng=None):
        """
        Inicializa un flamenco con una posición aleatoria.

        Args:
            problem: Instancia del problema a resolver
            rng: NumPy random generator instance
            py_rng: stdlib Random instance
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.rng = rng if rng is not None else np.random.default_rng()
        self.py_rng = py_rng if py_rng is not None else random.Random()
        self.position = self.rng.uniform(0, 1, self.dimension)
        self._fitness = None
        self.personal_best_position = self.position.copy()
        self.personal_best_fitness = float("inf")

    def fitness(self):
        """Calcula el fitness del individuo."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)

            # Actualizar mejor posición personal si es necesario
            if self._fitness < self.personal_best_fitness:
                self.personal_best_position = self.position.copy()
                self.personal_best_fitness = self._fitness

        return self._fitness

    def is_feasible(self):
        """Verifica si el individuo representa una solución factible."""
        return (
            True  # En VRP todas las soluciones son factibles con nuestro decodificador
        )

    def move(self, best, iteration, max_iterations, mode="forage"):
        """
        Mueve el flamenco según el modelo oficial FSA (IEEE Access 2021).

        Args:
            best: Individuo con mejor fitness (xbj)
            iteration: Iteración actual
            max_iterations: Iteraciones totales
            mode: 'forage' o 'migrate'
        """
        iteration + 1
        n = self.dimension  # para grados de libertad
        x_new = self.position.copy()

        for j in range(self.dimension):
            xij = self.position[j]
            xbj = best.position[j]

            if mode == "forage":
                G1 = self.rng.normal(0, 1)
                G2 = self.rng.normal(0, 1)
                ε1 = self.py_rng.choice([-1, 1])
                ε2 = self.py_rng.choice([-1, 1])
                K = self.rng.chisquare(n)

                # Forrajeo: Eq. (2)
                step = G1 * xbj + ε2 * xij
                scan = G2 * abs(step)
                foot = ε1 * xbj
                delta = scan + foot + K

                x_new[j] = xij + delta

            elif mode == "migrate":
                ω = self.rng.normal(0, n)
                delta = ω * (xbj - xij)

                # Migración: Eq. (3)
                x_new[j] = xij + delta

            # Clip
            x_new[j] = np.clip(x_new[j], 0, 1)

        # Reemplazo si mejora
        new_fit = self.problem.evaluate(x_new)
        if new_fit < self.fitness():
            self.position = x_new
            self._fitness = new_fit

    def copy(self, other):
        """Copia los valores de otro individuo a este."""
        if isinstance(other, Flamingo):
            self.position = other.position.copy()
            self._fitness = other._fitness
            self.personal_best_position = other.personal_best_position.copy()
            self.personal_best_fitness = other.personal_best_fitness


class FGO(MetaheuristicAlgorithm):
    """Implementación del algoritmo Flamingo Optimization Algorithm (FGO)."""

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo FGO.

        Args:
            problem: Instancia del problema a resolver
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)

    def initialize_population(self):
        """Inicializa la población de flamencos."""
        self.population = []

        for _ in range(self.population_size):
            flamingo = Flamingo(self.problem, rng=self.rng, py_rng=self.py_rng)
            self.population.append(flamingo)

        # Ordenar la población por fitness
        self.population.sort(key=lambda x: x.fitness())

        # Guardar la mejor solución
        self.best_solution = object.__new__(Flamingo)
        self.best_solution.problem = self.problem
        self.best_solution.dimension = self.population[0].dimension
        self.best_solution.rng = self.rng
        self.best_solution.py_rng = self.py_rng
        self.best_solution._fitness = None
        self.best_solution.position = None
        self.best_solution.personal_best_position = None
        self.best_solution.personal_best_fitness = float("inf")
        self.best_solution.copy(self.population[0])

        # Inicializar curva de convergencia
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        """Actualiza la población en cada iteración."""
        iteration = len(self.convergence_curve)

        MPb = int(0.1 * self.population_size)
        MPo = MPb
        MPr = int(
            self.py_rng.random() * self.population_size * (1 - MPb / self.population_size)
        )
        MPt = self.population_size - MPo - MPr

        self.population.sort(key=lambda x: x.fitness())

        # Migración inicial: MPo mejores
        for i in range(MPo):
            self.population[i].move(
                self.population[0], iteration, self.max_iterations, mode="migrate"
            )

        # Forrajeo: intermedios
        for i in range(MPo, MPo + MPr):
            self.population[i].move(
                self.population[0], iteration, self.max_iterations, mode="forage"
            )

        # Migración final: MPt peores
        for i in range(MPo + MPr, MPo + MPr + MPt):
            self.population[i].move(
                self.population[0], iteration, self.max_iterations, mode="migrate"
            )

        # Ordenar la población actualizada
        self.population.sort(key=lambda x: x.fitness())

        # Actualizar la mejor solución si es necesario
        if self.population[0].is_better_than(self.best_solution):
            self.best_solution.copy(self.population[0])

        # Actualizar curva de convergencia
        self.convergence_curve.append(self.best_solution.fitness())
