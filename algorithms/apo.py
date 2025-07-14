"""Artificial Protozoa Optimizer (APO).

This module implements the Artificial Protozoa Optimizer algorithm,
a bio-inspired metaheuristic based on the behavior of protozoa organisms.

The algorithm simulates three main behaviors of protozoa:
1. Dormancy: When conditions are unfavorable, protozoa enter a dormant state
2. Reproduction: Protozoa reproduce through various mechanisms
3. Foraging: Active movement and food searching behavior

Reference:
    Wang, X., Snášel, V., Mirjalili, S., et al. (2024).
    Artificial Protozoa Optimizer (APO): A novel bio-inspired metaheuristic algorithm
    for engineering optimization.
    Knowledge-Based Systems, 295, 111737.
    DOI: 10.1016/j.knosys.2024.111737

Example:
    >>> from algorithms.apo import APO
    >>> from problems.vrp import VRPProblem
    >>>
    >>> # Load a VRP instance
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>>
    >>> # Initialize and run APO
    >>> apo = APO(problem, population_size=30)
    >>> apo.initialize_population()
    >>> best_solution = apo.run(iterations=100)
"""
import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm


class Protozoa(Individual):
    """Individual protozoa organism in the APO algorithm.

    Each protozoa represents a potential solution to the optimization problem.
    Protozoa can exhibit dormancy, reproduction, and foraging behaviors.

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
        """Calculate and return the fitness value of this protozoa.

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

    def move(self, population, iteration, max_iterations, pf_max=0.1, npairs=1):
        """Update the position of this protozoa based on APO behaviors.

        Implements three main behaviors:
        1. Dormancy: Random repositioning when conditions are unfavorable
        2. Reproduction: Creating variations through genetic-like operations
        3. Foraging: Movement towards better solutions

        Args:
            population: List of all protozoa in the population
            iteration: Current iteration number
            max_iterations: Maximum number of iterations
            pf_max: Maximum foraging probability (default: 0.1)
            npairs: Number of pairs for reproduction (default: 1)
        """
        dim = self.dimension
        ps = len(population)
        i = population.index(self)

        # Probabilidades dinámicas
        pf = pf_max * random.random()
        pah = 0.5 * (1 + math.cos((iteration / max_iterations) * math.pi))
        pdr = 0.5 * (1 + math.cos(((ps - i) / ps) * math.pi))

        # Dormancia o reproducción
        if random.random() < pf:
            if random.random() < pdr:
                # Dormancia - Eq. 11
                self.position = self.lower_bounds + np.random.rand(dim) * (
                    self.upper_bounds - self.lower_bounds
                )
            else:
                # Reproducción - Eq. 13
                Mr = np.zeros(dim)
                idxs = np.random.permutation(dim)[: math.ceil(dim * random.random())]
                Mr[idxs] = 1
                delta = np.random.rand(dim) * (
                    self.lower_bounds
                    + np.random.rand(dim) * (self.upper_bounds - self.lower_bounds)
                )
                self.position = self.position + random.choice([-1, 1]) * delta * Mr
        else:
            Mf = np.zeros(dim)
            idxs = np.random.permutation(dim)[: math.ceil(dim * i / ps)]
            Mf[idxs] = 1
            if random.random() < pah:
                # Autotrofia - Eq. 1
                j = random.randint(0, ps - 1)
                neighbor_plus = population[min(i + 1, ps - 1)].position
                neighbor_minus = population[max(i - 1, 0)].position
                wa = math.exp(
                    -abs(population[max(i - 1, 0)].fitness())
                    / (population[min(i + 1, ps - 1)].fitness() + 1e-16)
                )
                delta = (
                    population[j].position
                    - self.position
                    + (wa * (neighbor_minus - neighbor_plus))
                ) / npairs
                f = random.random() * (
                    1 + math.cos((iteration / max_iterations) * math.pi)
                )
                self.position = self.position + f * delta * Mf
            else:
                # Heterotrofia - Eq. 7
                neighbor_minus = population[max(i - 1, 0)].position
                neighbor_plus = population[min(i + 1, ps - 1)].position
                wh = math.exp(
                    -abs(population[max(i - 1, 0)].fitness())
                    / (population[min(i + 1, ps - 1)].fitness() + 1e-16)
                )
                Xnear = (
                    1
                    + random.choice([-1, 1])
                    * random.random()
                    * (1 - iteration / max_iterations)
                ) * self.position
                delta = (
                    Xnear - self.position + (wh * (neighbor_minus - neighbor_plus))
                ) / npairs
                f = random.random() * (
                    1 + math.cos((iteration / max_iterations) * math.pi)
                )
                self.position = self.position + f * delta * Mf

        # Clip y reset
        self.position = np.clip(self.position, self.lower_bounds, self.upper_bounds)
        self._fitness = None

    def copy(self, other):
        """Copy the attributes from another protozoa.

        Args:
            other: Another Protozoa instance to copy from
        """
        if isinstance(other, Protozoa):
            self.position = other.position.copy()
            self._fitness = other._fitness


class APO(MetaheuristicAlgorithm):
    """Artificial Protozoa Optimizer (APO) algorithm implementation.

    A bio-inspired optimization algorithm that simulates the behavior of
    protozoa organisms, including dormancy, reproduction, and foraging.

    The algorithm maintains a population of protozoa that evolve through
    iterations using biological-inspired operators.

    Args:
        problem: The optimization problem to solve
        population_size: Number of protozoa in the population (default: 30)
        pf_max: Maximum foraging probability (default: 0.1)
        npairs: Number of pairs for reproduction (default: 1)
    """

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        super().__init__(problem, population_size, max_iterations, seed)

    def initialize_population(self):
        """Inicializa la población de protozoos."""
        # Set random seed if provided

        if self.seed is not None:
            random.seed(self.seed)

            np.random.seed(self.seed)

        self.population = []
        for _ in range(self.population_size):
            protozoa = Protozoa(self.problem)
            self.population.append(protozoa)
        self.population.sort(key=lambda x: x.fitness())
        self.best_solution = Protozoa(self.problem)
        self.best_solution.copy(self.population[0])
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        """Actualiza la población en cada iteración."""
        iteration = len(self.convergence_curve)
        self.population.sort(key=lambda x: x.fitness())
        self.population[0]
        self.population[-1]
        for i in range(self.population_size):
            self.population[i].move(self.population, iteration, self.max_iterations)
        self.population.sort(key=lambda x: x.fitness())
        if self.population[0].fitness() < self.best_solution.fitness():
            self.best_solution.copy(self.population[0])
        self.convergence_curve.append(self.best_solution.fitness())
