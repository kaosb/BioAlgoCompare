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
    """Class to represent an individual in the EGTO algorithm."""

    def __init__(self, problem):
        """
        Initialize a gorilla with a random position.

        Args:
            problem: Problem instance to solve
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        # For VRP problems, bounds are [0,1]
        self.lower_bounds = np.zeros(self.dimension)
        self.upper_bounds = np.ones(self.dimension)
        self.position = np.random.uniform(0, 1, self.dimension)
        self._fitness = None

    def fitness(self):
        """Calculate the individual's fitness."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self):
        """Check if the individual represents a feasible solution."""
        return (
            True  # In VRP all solutions are feasible with our decoder
        )

    def move(self, best, iteration, max_iterations):
        """
        Gorilla movement according to the EGTO+MPA algorithm.
        """
        dim = self.dimension
        P = 0.5
        CF = 0.5
        FADs = 0.2
        random.random()

        if iteration < max_iterations / 3:
            # High speed (exploratory phase with Brownian motion)
            RB = np.random.normal(0, 1, dim)
            S = np.random.rand(dim) * self.position
            delta = P * RB * S
            self.position += delta

        elif iteration < 2 * max_iterations / 3:
            # Medium speed (random mixing)
            R = np.random.rand(dim)
            S = R * (best.position - R * self.position)
            delta = P * CF * S
            self.position += delta

        else:
            # Low speed (predator behavior, random perturbation)
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

        # Apply bounds and reset fitness
        self.position = np.clip(self.position, self.lower_bounds, self.upper_bounds)
        self._fitness = None

    def copy(self, other):
        """Copy values from another individual to this one."""
        if isinstance(other, EnhancedGorilla):
            self.position = other.position.copy()
            self._fitness = other._fitness


class EGTO(MetaheuristicAlgorithm):
    """Implementation of the Enhanced Gorilla Troops Optimization (EGTO) algorithm."""

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Initialize the EGTO algorithm.

        Args:
            problem: Problem instance to solve
            population_size: Population size
            max_iterations: Maximum number of iterations
            seed: Seed for reproducibility
        """
        super().__init__(problem, population_size, max_iterations, seed)

    def initialize_population(self):
        """Initialize the gorilla population."""
        # Set random seed if provided

        if self.seed is not None:
            random.seed(self.seed)

            np.random.seed(self.seed)

        self.population = []

        for _ in range(self.population_size):
            gorilla = EnhancedGorilla(self.problem)
            self.population.append(gorilla)

        # Sort population by fitness
        self.population.sort(key=lambda x: x.fitness())

        # Save the best solution
        self.best_solution = EnhancedGorilla(self.problem)
        self.best_solution.copy(self.population[0])

        # Initialize convergence curve
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        """Update the population in each iteration."""
        iteration = len(self.convergence_curve)

        # Sort population by fitness
        self.population.sort(key=lambda x: x.fitness())

        best_gorilla = self.population[0]

        for i in range(self.population_size):
            # Move each gorilla
            self.population[i].move(best_gorilla, iteration, self.max_iterations)

        # Sort the updated population
        self.population.sort(key=lambda x: x.fitness())

        # Update best solution if necessary
        if self.population[0].is_better_than(self.best_solution):
            self.best_solution.copy(self.population[0])

        # Update convergence curve
        self.convergence_curve.append(self.best_solution.fitness())
