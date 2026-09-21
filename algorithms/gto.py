"""Gorilla Troops Optimizer (GTO).

This module implements the Gorilla Troops Optimizer, a nature-inspired
metaheuristic algorithm that simulates the social behavior of gorilla troops.

The algorithm models five main behaviors:
1. Migration to unknown places (exploration)
2. Migration to known locations (exploration)
3. Moving towards other gorillas (exploration)
4. Following the silverback (exploitation)
5. Competition for adult females (exploitation)

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
    """Individual in the Gorilla Troops Optimizer."""

    def __init__(self, problem, rng=None, py_rng=None):
        """
        Initialize a gorilla with a random position.

        Args:
            problem: Problem instance to solve
            rng: NumPy random generator instance
            py_rng: stdlib Random instance
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.rng = rng if rng is not None else np.random.default_rng()
        self.py_rng = py_rng if py_rng is not None else random.Random()
        self.position = self.rng.uniform(0, 1, self.dimension)
        self._fitness = None
        self.lower_bounds = np.zeros(self.dimension)
        self.upper_bounds = np.ones(self.dimension)

    def fitness(self):
        """Calculate the fitness of this gorilla."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self):
        """Check if the solution is feasible."""
        return True

    def move(self, population, iteration, max_iterations):
        """Movement logic (handled in GTO.update_population)."""
        pass

    def copy(self, other):
        """Copy values from another gorilla."""
        self.position = np.copy(other.position)
        self._fitness = other._fitness


class GTO(MetaheuristicAlgorithm):
    """Gorilla Troops Optimizer (Abdollahzadeh et al., 2021).

    Implements the five behaviors of gorilla troops for optimization:
    exploration via migration and group movement, exploitation via
    silverback following and female competition.
    """

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Initialize GTO.

        Args:
            problem: Problem instance
            population_size: Population size
            max_iterations: Maximum iterations
            seed: Random seed for reproducibility
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.convergence_curve = []
        # Parameters from original paper
        self.beta = 3
        self.p = 0.03
        self.W = 0.8

    def initialize_population(self):
        """Initialize the gorilla population."""
        self.population = []
        for _ in range(self.population_size):
            gorilla = Gorilla(self.problem, rng=self.rng, py_rng=self.py_rng)
            self.population.append(gorilla)

        # Find the initial silverback (best solution)
        self.best_solution = self.population[0]
        for i in range(1, self.population_size):
            if self.population[i].is_better_than(self.best_solution):
                self.best_solution = self.population[i]

        # Store a copy of the silverback
        self._update_silverback(self.best_solution)
        self.convergence_curve = [self.best_solution.fitness()]

    def _update_silverback(self, source):
        """Create a copy of the silverback from a source gorilla."""
        sb = object.__new__(Gorilla)
        sb.problem = self.problem
        sb.dimension = source.dimension
        sb.rng = self.rng
        sb.py_rng = self.py_rng
        sb.position = np.copy(source.position)
        sb._fitness = source._fitness
        sb.lower_bounds = source.lower_bounds
        sb.upper_bounds = source.upper_bounds
        self.best_solution = sb

    def update_population(self):
        """Update gorilla positions per MATLAB reference (Abdollahzadeh 2021).

        Parameters:
            F = cos(2*rand) + 1  (NOT cos(2*pi*rand))
            a = F * (1 - t/T)
            C = a * (2*rand - 1)
        """
        t = len(self.convergence_curve)
        lb = np.zeros(self.population[0].dimension)
        ub = np.ones(self.population[0].dimension)
        dim = self.population[0].dimension

        # Eq. 3: F = cos(2*rand) + 1 (MATLAB: cos(2*rand)+1)
        F = math.cos(2 * self.py_rng.random()) + 1
        # Eq. 2: a = F * (1 - t/T)
        a = F * (1 - t / self.max_iterations)
        # Eq. 4: C = a * (2*rand - 1), i.e. l in [-1,1]
        C = a * (2 * self.py_rng.random() - 1)

        silverback = self.best_solution

        for i in range(self.population_size):
            new_position = self.population[i].position.copy()
            old_fitness = self.population[i].fitness()

            # --- Exploration phase (a >= W) ---
            if abs(a) >= self.W:
                if self.py_rng.random() < self.p:
                    # Eq. 1: Migration to unknown place
                    r1 = self.rng.random(dim)
                    new_position = lb + (ub - lb) * r1

                elif self.py_rng.random() >= 0.5:
                    # Eq. 6: Moving towards another gorilla
                    Xr = self.py_rng.choice(self.population).position
                    Z = self.rng.uniform(-a, a, dim)
                    H = Z * self.population[i].position  # Eq. 5
                    new_position = (
                        self.population[i].position
                        - C * (C * (self.population[i].position - Xr)
                               + self.rng.random(dim) * (self.population[i].position - Xr))
                    )
                else:
                    # Migration to known location
                    Z = self.rng.uniform(-a, a, dim)
                    H = Z * self.population[i].position  # Eq. 5
                    new_position = (
                        (ub - lb) * self.rng.random(dim) + lb
                    ) + C * H

            # --- Exploitation phase (a < W) ---
            else:
                if self.py_rng.random() >= 0.5:
                    # Eq. 7: Following the silverback
                    g = 2 ** C
                    M = np.mean([gor.position for gor in self.population], axis=0)
                    delta = (np.abs(M) ** g) ** (1.0 / g) if g != 0 else np.abs(M)
                    new_position = (
                        C * delta * (self.population[i].position - silverback.position)
                        + self.population[i].position
                    )
                else:
                    # Eqs. 10-13: Competition for adult females
                    Q = 2 * self.py_rng.random() - 1
                    if self.py_rng.random() >= 0.5:
                        E = self.rng.random(dim)
                    else:
                        E = self.rng.standard_normal(dim)
                    A = self.beta * E
                    new_position = (
                        silverback.position
                        - (silverback.position * Q - self.population[i].position * Q) * A
                    )

            # Clip to bounds
            new_position = np.clip(new_position, lb, ub)

            # Greedy selection
            new_fitness = self.problem.evaluate(new_position)
            if new_fitness < old_fitness:
                self.population[i].position = new_position
                self.population[i]._fitness = new_fitness
            # else: keep current position (already set)

            # Update silverback if improved
            if self.population[i].fitness() < silverback.fitness():
                self._update_silverback(self.population[i])
                silverback = self.best_solution

        self.convergence_curve.append(self.best_solution.fitness())
