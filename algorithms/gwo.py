"""Grey Wolf Optimizer (GWO).

This module implements the Grey Wolf Optimizer, a nature-inspired
metaheuristic algorithm that simulates the leadership hierarchy and
hunting mechanism of grey wolves in nature.

The algorithm models four types of wolves:
1. Alpha: Best solution (leader)
2. Beta: Second best solution (advisor)
3. Delta: Third best solution (scout)
4. Omega: Remaining wolves (followers)

Reference:
    Mirjalili, S., Mirjalili, S. M., & Lewis, A. (2014).
    Grey Wolf Optimizer. Advances in Engineering Software, 69, 46-61.
    DOI: 10.1016/j.advengsoft.2013.12.007

Example:
    >>> from algorithms.gwo import GWO
    >>> from problems.vrp import VRPProblem
    >>>
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>>
    >>> algo = GWO(problem, population_size=30)
    >>> best_solution = algo.run(iterations=100)
"""
import numpy as np
import random
from .base import Individual, MetaheuristicAlgorithm


class Wolf(Individual):
    """Individual in the Grey Wolf Optimizer."""

    def __init__(self, problem, rng=None):
        """
        Initialize a wolf with random position.

        Args:
            problem: Problem instance to solve
            rng: NumPy random generator instance
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.rng = rng if rng is not None else np.random.default_rng()
        self.position = self.rng.uniform(0, 1, self.dimension)
        self._fitness = None
        self.lower_bounds = np.zeros(self.dimension)
        self.upper_bounds = np.ones(self.dimension)

    def fitness(self):
        """Calculate the fitness of this wolf."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self):
        """Check if the solution is feasible."""
        return True  # VRP decoder always produces feasible solutions

    def move(self, population, iteration, max_iterations):
        """Movement logic (handled in GWO.update_population)."""
        pass

    def copy(self, other):
        """
        Copy values from another wolf.

        Args:
            other: Another Wolf individual
        """
        self.position = np.copy(other.position)
        self._fitness = other._fitness


class GWO(MetaheuristicAlgorithm):
    """Grey Wolf Optimizer implementation.

    Models the social hierarchy and hunting behavior of grey wolves.
    Parameter 'a' decreases linearly from 2 to 0 over iterations,
    controlling the transition from exploration to exploitation.
    """

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Initialize GWO.

        Args:
            problem: Problem instance
            population_size: Wolf pack size
            max_iterations: Maximum iterations
            seed: Random seed for reproducibility
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.convergence_curve = []
        self.alpha = None  # Best wolf
        self.beta = None   # Second best
        self.delta = None  # Third best

    def initialize_population(self):
        """Initialize the wolf pack and identify alpha, beta, delta."""
        self.population = [Wolf(self.problem, rng=self.rng) for _ in range(self.population_size)]

        # Sort by fitness to find alpha, beta, delta
        self._update_hierarchy()

        self.convergence_curve = [self.alpha.fitness()]

    def _update_hierarchy(self):
        """Update alpha, beta, delta wolves (3 best solutions)."""
        sorted_pop = sorted(self.population, key=lambda w: w.fitness())

        # Create copies to preserve best solutions (without consuming RNG)
        def _copy_wolf(source):
            w = object.__new__(Wolf)
            w.problem = source.problem
            w.dimension = source.dimension
            w.rng = self.rng
            w.position = np.copy(source.position)
            w._fitness = source._fitness
            w.lower_bounds = source.lower_bounds
            w.upper_bounds = source.upper_bounds
            return w

        self.alpha = _copy_wolf(sorted_pop[0])
        self.beta = _copy_wolf(sorted_pop[1] if len(sorted_pop) > 1 else sorted_pop[0])
        self.delta = _copy_wolf(sorted_pop[2] if len(sorted_pop) > 2 else sorted_pop[0])

        self.best_solution = self.alpha

    def update_population(self):
        """Update the wolf pack positions.

        Parameter a decreases linearly from 2 to 0 (Eq. 3.3).
        Each omega wolf updates position guided by alpha, beta, delta.
        """
        t = len(self.convergence_curve)
        T = self.max_iterations

        # a decreases linearly from 2 to 0 (Eq. 3.3)
        a = 2 - 2 * (t / T)

        for i in range(self.population_size):
            dim = self.population[i].dimension

            # Encircling alpha (Eqs. 3.5-3.6)
            r1 = self.rng.random(dim)
            r2 = self.rng.random(dim)
            A1 = 2 * a * r1 - a
            C1 = 2 * r2
            D_alpha = np.abs(C1 * self.alpha.position - self.population[i].position)
            X1 = self.alpha.position - A1 * D_alpha

            # Encircling beta
            r1 = self.rng.random(dim)
            r2 = self.rng.random(dim)
            A2 = 2 * a * r1 - a
            C2 = 2 * r2
            D_beta = np.abs(C2 * self.beta.position - self.population[i].position)
            X2 = self.beta.position - A2 * D_beta

            # Encircling delta
            r1 = self.rng.random(dim)
            r2 = self.rng.random(dim)
            A3 = 2 * a * r1 - a
            C3 = 2 * r2
            D_delta = np.abs(C3 * self.delta.position - self.population[i].position)
            X3 = self.delta.position - A3 * D_delta

            # New position: average of the three guides (Eq. 3.7)
            new_position = (X1 + X2 + X3) / 3.0

            # Clip to bounds
            self.population[i].position = np.clip(
                new_position,
                self.population[i].lower_bounds,
                self.population[i].upper_bounds,
            )
            self.population[i]._fitness = None

        # Update hierarchy
        self._update_hierarchy()

        self.convergence_curve.append(self.alpha.fitness())
