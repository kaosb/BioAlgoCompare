"""Spotted Hyena Optimizer (SHO).

This module implements the Spotted Hyena Optimizer, inspired by the
social hierarchy and collaborative hunting behavior of spotted hyenas.

The algorithm models four main phases:
1. Searching and tracking prey
2. Encircling prey
3. Hunting with pack coordination
4. Attacking prey

SHO emphasizes the social hierarchy where the best solutions guide the search.

Reference:
    Dhiman, G., & Kumar, V. (2017).
    Spotted hyena optimizer: A novel bio-inspired based metaheuristic
    technique for engineering applications.
    Advances in Engineering Software, 114, 48-70.
    DOI: 10.1016/j.advengsoft.2017.05.014

Example:
    >>> from algorithms.sho import SHO
    >>> from problems.vrp import VRPProblem
    >>>
    >>> # Load a VRP instance
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>>
    >>> # Initialize and run SHO
    >>> algo = SHO(problem, population_size=30)
    >>> algo.initialize_population()
    >>> best_solution = algo.run(iterations=100)
"""
import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm


class Hyena(Individual):
    """Class to represent an individual in the SHO (Spotted Hyena Optimizer) algorithm."""

    def __init__(self, problem):
        """
        Initialize a hyena with a random position.

        Args:
            problem: Problem instance to solve
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
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

    def move(self, alpha, beta, delta, iteration, max_iterations):
        """
        Move the hyena according to SHO algorithm rules.

        Args:
            alpha: Best hyena (leader)
            beta: Second best hyena
            delta: Third best hyena
            iteration: Current iteration
            max_iterations: Maximum number of iterations
        """
        a = 2 - iteration * (2 / max_iterations)  # Linearly decreases from 2 to 0

        for i in range(self.dimension):
            r1 = random.random()
            r2 = random.random()

            A = 2 * a * r1 - a  # Coefficient vector
            C = 2 * r2  # Emphasis vector

            # Exploration/exploitation phase
            if abs(A) >= 1:  # Exploration
                rand_index = random.randint(0, 2)
                if rand_index == 0:
                    D = abs(C * alpha.position[i] - self.position[i])
                    self.position[i] = alpha.position[i] - A * D
                elif rand_index == 1:
                    D = abs(C * beta.position[i] - self.position[i])
                    self.position[i] = beta.position[i] - A * D
                else:
                    D = abs(C * delta.position[i] - self.position[i])
                    self.position[i] = delta.position[i] - A * D
            else:  # Exploitation - Circular attack
                D_alpha = abs(C * alpha.position[i] - self.position[i])
                D_beta = abs(C * beta.position[i] - self.position[i])
                D_delta = abs(C * delta.position[i] - self.position[i])

                X1 = alpha.position[i] - A * D_alpha
                X2 = beta.position[i] - A * D_beta
                X3 = delta.position[i] - A * D_delta

                self.position[i] = (X1 + X2 + X3) / 3

            # Keep position within bounds [0, 1]
            self.position[i] = max(0, min(1, self.position[i]))

        # Invalidate fitness since position has changed
        self._fitness = None

    def copy(self, other):
        """Copy values from another individual to this one."""
        if isinstance(other, Hyena):
            self.position = other.position.copy()
            self._fitness = other._fitness


class SHO(MetaheuristicAlgorithm):
    """Implementation of the Spotted Hyena Optimizer (SHO) algorithm."""

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Initialize the SHO algorithm.

        Args:
            problem: Problem instance to solve
            population_size: Population size
            max_iterations: Maximum number of iterations
            seed: Seed for reproducibility
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.alpha = None  # Best hyena
        self.beta = None  # Second best hyena
        self.delta = None  # Third best hyena

    def initialize_population(self):
        """Initialize the hyena population."""
        # Set random seed if provided

        if self.seed is not None:
            random.seed(self.seed)

            np.random.seed(self.seed)

        self.population = []

        for _ in range(self.population_size):
            hyena = Hyena(self.problem)
            self.population.append(hyena)

        # Sort population by fitness
        self.population.sort(key=lambda x: x.fitness())

        # Assign leaders (handle small population case)
        self.alpha = self.population[0]
        self.beta = (
            self.population[1] if len(self.population) > 1 else self.population[0]
        )
        self.delta = (
            self.population[2] if len(self.population) > 2 else self.population[0]
        )

        # Save the best solution
        self.best_solution = Hyena(self.problem)
        self.best_solution.copy(self.alpha)

        # Initialize convergence curve
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        """Update the population in each iteration."""
        iteration = len(self.convergence_curve)

        for i in range(self.population_size):
            # Move each hyena
            self.population[i].move(
                self.alpha, self.beta, self.delta, iteration, self.max_iterations
            )

        # Sort population by fitness
        self.population.sort(key=lambda x: x.fitness())

        # Update leaders (handle small population case)
        self.alpha = self.population[0]
        self.beta = (
            self.population[1] if len(self.population) > 1 else self.population[0]
        )
        self.delta = (
            self.population[2] if len(self.population) > 2 else self.population[0]
        )

        # Update best solution if necessary
        if self.alpha.is_better_than(self.best_solution):
            self.best_solution.copy(self.alpha)

        # Update convergence curve
        self.convergence_curve.append(self.best_solution.fitness())


# Alias to maintain compatibility with existing code
HOA = SHO
