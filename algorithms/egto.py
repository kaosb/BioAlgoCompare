"""Enhanced Gorilla Troops Optimizer (EGTO).

This module implements the Enhanced Gorilla Troops Optimizer algorithm,
an improved version of the original GTO algorithm that simulates the social
intelligence and behaviors of gorilla troops in nature.

The algorithm models several gorilla behaviors:
1. Migration to different areas (exploration)
2. Moving towards the silverback (exploitation)
3. Following other gorillas in the troop
4. Competing for adult females

The enhanced version includes improvements like adaptive parameters and
better balance between exploration and exploitation.

Reference:
    Abdollahzadeh, B., Soleimanian Gharehchopogh, F., & Mirjalili, S. (2021).
    Artificial gorilla troops optimizer: A new nature-inspired metaheuristic 
    algorithm for global optimization problems.
    International Journal of Intelligent Systems, 36(10), 5887-5958.
    DOI: 10.1002/int.22535

Example:
    >>> from algorithms.egto import EGTO
    >>> from problems.vrp import VRPProblem
    >>> 
    >>> # Load a VRP instance
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>> 
    >>> # Initialize and run EGTO
    >>> egto = EGTO(problem, population_size=30)
    >>> egto.initialize_population()
    >>> best_solution = egto.run(iterations=100)
"""
import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm


class EnhancedGorilla(Individual):
    """Clase para representar un individuo en el algoritmo EGTO."""

    def __init__(self, problem):
        """
        Inicializa un gorila con una posición aleatoria.

        Args:
            problem: Instancia del problema a resolver
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        # Para problemas VRP, los límites son [0,1]
        self.lower_bounds = np.zeros(self.dimension)
        self.upper_bounds = np.ones(self.dimension)
        self.position = np.random.uniform(0, 1, self.dimension)
        self._fitness = None

    def fitness(self):
        """Calcula el fitness del individuo."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self):
        """Verifica si el individuo representa una solución factible."""
        return (
            True  # En VRP todas las soluciones son factibles con nuestro decodificador
        )

    def move(self, best, iteration, max_iterations):
        """
        Movimiento del gorila según el algoritmo EGTO+MPA.
        """
        dim = self.dimension
        P = 0.5
        CF = 0.5
        FADs = 0.2
        random.random()

        if iteration < max_iterations / 3:
            # Alta velocidad (fase exploratoria con movimiento browniano)
            RB = np.random.normal(0, 1, dim)
            S = np.random.rand(dim) * self.position
            delta = P * RB * S
            self.position += delta

        elif iteration < 2 * max_iterations / 3:
            # Media velocidad (mezcla aleatoria)
            R = np.random.rand(dim)
            S = R * (best.position - R * self.position)
            delta = P * CF * S
            self.position += delta

        else:
            # Baja velocidad (comportamiento de depredador, perturbación aleatoria)
            r1 = random.random()
            if r1 < FADs:
                epsilon = 1e-8
                U = np.random.normal(0, 1, dim)
                V = np.random.normal(0, 1, dim)
                beta = 1.5
                sigma = (
                    math.gamma(1 + beta)
                    * math.sin(math.pi * beta / 2)
                    / (math.gamma((1 + beta) / 2) * beta * 2 ** ((beta - 1) / 2))
                ) ** (1 / beta)
                LF = 0.01 * (U * sigma) / (np.abs(V) + epsilon)
                self.position += LF * self.position
            else:
                step = best.position - self.position
                self.position += P * step

        # Aplicar límites y resetear fitness
        self.position = np.clip(self.position, self.lower_bounds, self.upper_bounds)
        self._fitness = None

    def copy(self, other):
        """Copia los valores de otro individuo a este."""
        if isinstance(other, EnhancedGorilla):
            self.position = other.position.copy()
            self._fitness = other._fitness


class EGTO(MetaheuristicAlgorithm):
    """Implementación del algoritmo Enhanced Gorilla Troops Optimization (EGTO)."""

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo EGTO.

        Args:
            problem: Instancia del problema a resolver
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)

    def initialize_population(self):
        """Inicializa la población de gorilas."""
        # Set random seed if provided

        if self.seed is not None:

            random.seed(self.seed)

            np.random.seed(self.seed)

        self.population = []

        for _ in range(self.population_size):
            gorilla = EnhancedGorilla(self.problem)
            self.population.append(gorilla)

        # Ordenar la población por fitness
        self.population.sort(key=lambda x: x.fitness())

        # Guardar la mejor solución
        self.best_solution = EnhancedGorilla(self.problem)
        self.best_solution.copy(self.population[0])

        # Inicializar curva de convergencia
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        """Actualiza la población en cada iteración."""
        iteration = len(self.convergence_curve)

        # Ordenar la población por fitness
        self.population.sort(key=lambda x: x.fitness())

        best_gorilla = self.population[0]

        for i in range(self.population_size):
            # Mover cada gorila
            self.population[i].move(best_gorilla, iteration, self.max_iterations)

        # Ordenar la población actualizada
        self.population.sort(key=lambda x: x.fitness())

        # Actualizar la mejor solución si es necesario
        if self.population[0].is_better_than(self.best_solution):
            self.best_solution.copy(self.population[0])

        # Actualizar curva de convergencia
        self.convergence_curve.append(self.best_solution.fitness())
