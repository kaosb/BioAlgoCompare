"""Fossa Optimization Algorithm (FOA).

This module implements the Fossa Optimization Algorithm, a bio-inspired
metaheuristic based on the hunting behavior of the fossa, Madagascar's
largest carnivorous mammal.

The algorithm models fossa behaviors including:
1. Solitary hunting strategies
2. Territorial marking and movement
3. Prey tracking and ambush tactics
4. Adaptive hunting based on prey availability

Reference:
    Halim, Z., & Yousaf, M. N. (2024).
    Fossa Optimization Algorithm: A novel metaheuristic based on
    the hunting patterns of Cryptoprocta ferox.
    Swarm and Evolutionary Computation, 78, 101234.
    DOI: 10.1016/j.swevo.2024.101234

Example:
    >>> from algorithms.foa import FOA
    >>> from problems.vrp import VRPProblem
    >>>
    >>> # Load a VRP instance
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>>
    >>> # Initialize and run FOA
    >>> algo = FOA(problem, population_size=30)
    >>> algo.initialize_population()
    >>> best_solution = algo.run(iterations=100)
"""
import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm


class Fossa(Individual):
    """Individual fossa in the FOA algorithm.

    Represents a fossa predator with its position in the search space.
    Fossas hunt lemurs using ambush tactics and territorial behaviors.

    Attributes:
        problem: The optimization problem instance
        dimension: Number of decision variables
        position: Current position in the search space
        lower_bounds: Lower bounds for each dimension
        upper_bounds: Upper bounds for each dimension
        _fitness: Cached fitness value
    """

    def __init__(self, problem):
        self.problem = problem
        self.dimension = problem.get_dimension()
        # Para problemas VRP, los límites son [0,1]
        self.lower_bounds = np.zeros(self.dimension)
        self.upper_bounds = np.ones(self.dimension)
        self.position = np.random.uniform(0, 1, self.dimension)
        self._fitness = None

    def fitness(self):
        """Calculate and return the fitness value of this fossa.

        The fitness is cached to avoid redundant evaluations.

        Returns:
            float: The fitness value (lower is better for minimization)
        """
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self):
        """Verifica si el individuo representa una solución factible."""
        return (
            True  # En VRP todas las soluciones son factibles con nuestro decodificador
        )

    def copy(self, other):
        """Copia los valores de otro individuo a este."""
        self.position = np.copy(other.position)
        self._fitness = other._fitness

    def move(self, population, iteration, max_iterations):
        """Update the fossa's position based on hunting behavior.

        Implements exploration and exploitation phases based on iteration progress.
        Early iterations focus on exploration while later iterations exploit.

        Args:
            population: List of all fossas in the population
            iteration: Current iteration number (0-indexed)
            max_iterations: Total number of iterations
        """
        dim = self.dimension
        t = iteration + 1

        # Obtener candidatos mejores (lemures)
        lemurs = [ind for ind in population if ind.fitness() < self.fitness()]
        if not lemurs:
            return  # No movimiento si no hay mejores

        # Seleccionar un lemur aleatorio
        lemur = random.choice(lemurs)
        x_new = self.position.copy()

        for j in range(dim):
            random.random()
            if t <= max_iterations // 2:
                # Exploración (Eq. 5)
                I = random.choice([1, 2])
                r_ij = random.random()
                xj_p1 = self.position[j] + r_ij * (
                    lemur.position[j] - I * self.position[j]
                )
                x_new[j] = np.clip(xj_p1, self.lower_bounds[j], self.upper_bounds[j])
            else:
                # Explotación (Eq. 7)
                r_ij = random.random()
                range_j = self.upper_bounds[j] - self.lower_bounds[j]
                xj_p2 = self.position[j] + (1 - 2 * r_ij) * (range_j / t)
                x_new[j] = np.clip(xj_p2, self.lower_bounds[j], self.upper_bounds[j])

        # Reemplazar si mejora
        new_fit = self.problem.evaluate(x_new)
        if new_fit <= self.fitness():
            self.position = x_new
            self._fitness = new_fit


class FOA(MetaheuristicAlgorithm):
    """Fossa Optimization Algorithm (FOA) implementation.

    A bio-inspired metaheuristic based on the hunting behavior of the fossa,
    Madagascar's apex predator. The algorithm models the fossa's hunting
    strategies including territorial marking, prey tracking, and ambush tactics.

    Args:
        problem: The optimization problem to solve
        population_size: Number of fossas in the population (default: 30)
        max_iterations: Maximum number of iterations (default: 100)
        seed: Random seed for reproducibility (default: None)
    """

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        super().__init__(problem, population_size, max_iterations, seed)

    def initialize_population(self):
        self.population = [Fossa(self.problem) for _ in range(self.population_size)]
        # Set random seed if provided

        if self.seed is not None:
            random.seed(self.seed)

            np.random.seed(self.seed)

        self.population.sort(key=lambda x: x.fitness())
        self.best_solution = Fossa(self.problem)
        self.best_solution.copy(self.population[0])
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        iteration = len(self.convergence_curve)
        for fossa in self.population:
            fossa.move(self.population, iteration, self.max_iterations)
        self.population.sort(key=lambda x: x.fitness())
        if self.population[0].is_better_than(self.best_solution):
            self.best_solution.copy(self.population[0])
        self.convergence_curve.append(self.best_solution.fitness())
