"""Gorilla Troops Optimizer (GTO).

This module implements the Gorilla Troops Optimizer, a nature-inspired
metaheuristic algorithm that simulates the social behavior of gorilla troops.

The algorithm models five main behaviors:
1. Migration to unknown places (exploration)
2. Moving towards other gorillas (exploitation)
3. Following the silverback (leader)
4. Competition for adult females
5. Migration to known locations

Reference:
    Abdollahzadeh, B., Gharehchopogh, F. S., & Mirjalili, S. (2021).
    Artificial gorilla troops optimizer: A new nature-inspired metaheuristic
    algorithm for global optimization problems.
    International Journal of Intelligent Systems, 36(10), 5887-5958.
    DOI: 10.1002/int.22535

Example:
    >>> from algorithms.gto import GTO
    >>> from problems.vrp import VRPProblem
    >>>
    >>> # Load a VRP instance
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>>
    >>> # Initialize and run GTO
    >>> algo = GTO(problem, population_size=30)
    >>> algo.initialize_population()
    >>> best_solution = algo.run(iterations=100)
"""
import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm


class Gorilla(Individual):
    """Clase para representar un individuo en el algoritmo GTO (Gorilla Troops Optimization)."""

    def __init__(self, problem):
        """
        Inicializa un gorila con una posición aleatoria.

        Args:
            problem: Instancia del problema a resolver
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.position = np.random.uniform(0, 1, self.dimension)
        self._fitness = None
        # Para problemas VRP, los límites son [0,1]
        self.lower_bounds = np.zeros(self.dimension)
        self.upper_bounds = np.ones(self.dimension)

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

    def move(
        self, best_gorilla, C, L, W, beta, p, iteration, max_iter, population=None
    ):
        """Update the gorilla's position based on GTO behaviors.

        Implements five main behaviors: migration to unknown places, moving
        towards other gorillas, following the silverback, competition for
        females, and migration to known locations.

        Args:
            best_gorilla: Position of the silverback (best solution)
            C: Parameter C for exploration/exploitation balance
            L: Parameter L for step size control
            W: Threshold W for transition between exploration and exploitation
            beta: Parameter beta for competition behavior
            p: Probability parameter for exploration
            iteration: Current iteration number
            max_iter: Maximum number of iterations
            population: List of all gorillas (optional)
        """
        dim = self.dimension
        # --- Operadores de exploración (Ecuación 1) ---
        if random.random() < p:
            # Exploración: migración a lugar desconocido
            r1 = np.random.rand(dim)
            self.position = (
                self.lower_bounds + (self.upper_bounds - self.lower_bounds) * r1
            )
        elif random.random() >= 0.5 and population is not None:
            # Exploración: moverse hacia otro gorila
            Xr = random.choice(population).position
            self.position = self.position + C * (Xr - self.position)
        else:
            # Exploración: migración hacia un lugar conocido
            H = (np.random.uniform(-C, C, dim)) * self.position
            self.position = (self.upper_bounds - self.lower_bounds) * np.random.rand(
                dim
            ) + self.lower_bounds
            self.position = self.position + L * H

        # --- Transición a explotación si corresponde ---
        if C < W:
            if random.random() < 0.5 and population is not None:
                # Seguir al silverback (Eq. 7)
                M = np.mean([g.position for g in population], axis=0)
                self.position = L * (M - self.position) + best_gorilla.position
            else:
                # Competencia por hembras (Eq. 10)
                Q = 2 * random.random() - 1
                E = (
                    np.random.rand(dim)
                    if random.random() >= 0.5
                    else np.random.randn(dim)
                )
                A = beta * E
                self.position = (
                    best_gorilla.position
                    - Q * (best_gorilla.position - self.position) * A
                )

        # Clipping
        self.position = np.clip(self.position, self.lower_bounds, self.upper_bounds)
        self._fitness = None

    def copy(self, other):
        """
        Copia los valores de otro individuo a este.

        Args:
            other: Otro individuo (Gorilla)
        """
        self.position = np.copy(other.position)
        self._fitness = other._fitness


class GTO(MetaheuristicAlgorithm):
    """Implementación del algoritmo de optimización de tropas de gorilas (Gorilla Troops Optimization)."""

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo GTO.

        Args:
            problem: Instancia del problema
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.convergence_curve = []
        self.exploitation_factor = (
            0.5  # Factor para balancear exploración y explotación
        )
        self.social_factor = 0.2  # Factor para aprendizaje social
        self.beta = 3
        self.p = 0.03
        self.W = 0.8

    def initialize_population(self):
        """Inicializa la población de gorilas."""
        # Set random seed if provided

        if self.seed is not None:
            random.seed(self.seed)

            np.random.seed(self.seed)

        self.population = []
        for _ in range(self.population_size):
            gorilla = Gorilla(self.problem)
            self.population.append(gorilla)

        # Encontrar el mejor gorila inicial
        self.best_solution = self.population[0]
        for i in range(1, self.population_size):
            if self.population[i].is_better_than(self.best_solution):
                self.best_solution = self.population[i]

        # Initialize convergence curve with initial best fitness
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        """Actualiza la población en cada iteración."""
        t = len(self.convergence_curve)
        F = math.cos(2 * math.pi * random.random()) + 1
        C = F * (1 - t / self.max_iterations)
        l = random.uniform(-1, 1)
        L = C * l

        # Ajustar el factor de explotación basado en la iteración actual
        self.exploitation_factor = 0.5 - 0.3 * (
            len(self.convergence_curve) / self.max_iterations
        )

        # Actualizar cada gorila
        for i in range(self.population_size):
            # No mover el mejor gorila
            if self.population[i] is not self.best_solution:
                # Movimiento principal siguiendo al líder
                self.population[i].move(
                    self.best_solution,
                    C,
                    L,
                    self.W,
                    self.beta,
                    self.p,
                    t,
                    self.max_iterations,
                    self.population,
                )

                # Comportamiento social: interacción entre gorilas
                if random.random() < self.social_factor:
                    # Seleccionar otro gorila aleatoriamente
                    other_idx = random.randint(0, self.population_size - 1)
                    while other_idx == i:
                        other_idx = random.randint(0, self.population_size - 1)

                    # Aprendizaje social
                    for j in range(self.population[i].dimension):
                        if random.random() < 0.3:  # Probabilidad de aprendizaje
                            self.population[i].position[j] = self.population[
                                i
                            ].position[j] + random.random() * (
                                self.population[other_idx].position[j]
                                - self.population[i].position[j]
                            )

                    # Asegurar valores en rango [0, 1]
                    self.population[i].position = np.clip(
                        self.population[i].position, 0, 1
                    )
                    self.population[i]._fitness = None

                # Actualizar mejor solución si es necesario
                if self.population[i].is_better_than(self.best_solution):
                    gorilla_copy = Gorilla(self.problem)
                    gorilla_copy.copy(self.population[i])
                    self.best_solution = gorilla_copy

        # Registrar el mejor fitness en la curva de convergencia
        self.convergence_curve.append(self.best_solution.fitness())
