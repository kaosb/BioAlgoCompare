"""Salp Swarm Algorithm (SSA).

This module implements the Salp Swarm Algorithm, a nature-inspired
metaheuristic algorithm that simulates the swarming behavior of salps
navigating and foraging in oceans.

The algorithm models:
1. Leader salp movement towards food source
2. Follower salps chaining behavior
3. Exponential decay of exploration parameter c1

Reference:
    Mirjalili, S., Gandomi, A. H., Mirjalili, S. Z., Saremi, S.,
    Faris, H., & Mirjalili, S. M. (2017).
    Salp Swarm Algorithm: A bio-inspired optimizer for engineering
    design problems. Advances in Engineering Software, 114, 163-191.
    DOI: 10.1016/j.advengsoft.2017.07.002

Example:
    >>> from algorithms.ssa import SSA
    >>> from problems.vrp import VRPProblem
    >>>
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>>
    >>> algo = SSA(problem, population_size=30)
    >>> best_solution = algo.run(iterations=100)
"""
import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm


class Salp(Individual):
    """Individual in the Salp Swarm Algorithm."""

    def __init__(self, problem, rng=None):
        """
        Initialize a salp with random position.

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
        """Calculate the fitness of this salp."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self):
        """Check if the solution is feasible."""
        return True  # VRP decoder always produces feasible solutions

    def move(self, population, iteration, max_iterations):
        """Movement logic (handled in SSA.update_population)."""
        pass

    def copy(self, other):
        """
        Copy values from another salp.

        Args:
            other: Another Salp individual
        """
        self.position = np.copy(other.position)
        self._fitness = other._fitness


class SSA(MetaheuristicAlgorithm):
    """Salp Swarm Algorithm implementation.

    Models the chain-like swarming behavior of salps in the ocean.
    The leader salp follows the food source while followers form
    a chain behind it. The c1 parameter decays exponentially to
    balance exploration and exploitation.
    """

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Initialize SSA.

        Args:
            problem: Problem instance
            population_size: Number of salps
            max_iterations: Maximum iterations
            seed: Random seed for reproducibility
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.convergence_curve = []

    def initialize_population(self):
        """Initialize the salp swarm."""
        self.population = [Salp(self.problem, rng=self.rng) for _ in range(self.population_size)]

        # Identify food source (best salp)
        self.best_solution = self.population[0]
        for i in range(1, self.population_size):
            if self.population[i].is_better_than(self.best_solution):
                self.best_solution = self.population[i]

        # Store a copy of the best solution as food position
        self.food_position = object.__new__(Salp)
        self.food_position.problem = self.problem
        self.food_position.dimension = self.best_solution.dimension
        self.food_position.rng = self.rng
        self.food_position.lower_bounds = self.best_solution.lower_bounds
        self.food_position.upper_bounds = self.best_solution.upper_bounds
        self.food_position._fitness = None
        self.food_position.position = None
        self.food_position.copy(self.best_solution)

        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        """Update the salp swarm positions.

        Leader salp (index 0) moves towards food source.
        Follower salps (indices 1..N-1) follow their predecessor.
        c1 decays exponentially: c1 = 2 * exp(-(4t/T)^2)
        """
        t = len(self.convergence_curve)
        T = self.max_iterations

        # c1 decreases exponentially (Eq. 3.2)
        c1 = 2 * math.exp(-((4 * t / T) ** 2))

        lb = self.food_position.lower_bounds
        ub = self.food_position.upper_bounds
        food_pos = self.food_position.position

        for i in range(self.population_size):
            if i == 0:
                # Leader salp update (Eq. 3.1)
                c2 = self.rng.random(self.population[i].dimension)
                c3 = self.rng.random(self.population[i].dimension)

                # Where c3 >= 0.5: move towards food; else: move away
                new_position = np.where(
                    c3 >= 0.5,
                    food_pos + c1 * ((ub - lb) * c2 + lb),
                    food_pos - c1 * ((ub - lb) * c2 + lb),
                )

                self.population[i].position = np.clip(new_position, lb, ub)
                self.population[i]._fitness = None
            else:
                # Follower salps (Eq. 3.4): average of current and previous
                new_position = (
                    self.population[i].position + self.population[i - 1].position
                ) / 2.0

                self.population[i].position = np.clip(new_position, lb, ub)
                self.population[i]._fitness = None

            # Update food source if better solution found
            if self.population[i].is_better_than(self.food_position):
                self.food_position.copy(self.population[i])

        # Update best solution
        self.best_solution = self.food_position
        self.convergence_curve.append(self.best_solution.fitness())
