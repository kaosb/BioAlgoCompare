"""Manta Ray Foraging Optimization (MRFO).

This module implements the Manta Ray Foraging Optimization algorithm,
inspired by the foraging behaviors of manta rays.

The algorithm simulates three foraging behaviors:
1. Chain foraging: Manta rays line up head-to-tail
2. Cyclone foraging: Manta rays create a spiral pattern
3. Somersault foraging: Manta rays perform backward somersaults

Reference:
    Zhao, W., Zhang, Z., & Wang, L. (2020).
    Manta ray foraging optimization: An effective bio-inspired optimizer.
    Engineering Applications of Artificial Intelligence, 87, 103300.
    DOI: 10.1016/j.engappai.2019.103300

Example:
    >>> from algorithms.mrfo import MRFO
    >>> from problems.vrp import VRPProblem
    >>>
    >>> # Load a VRP instance
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>>
    >>> # Initialize and run MRFO
    >>> algo = MRFO(problem, population_size=30)
    >>> algo.initialize_population()
    >>> best_solution = algo.run(iterations=100)
"""
import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm


class MantaRay(Individual):
    """Class to represent an individual in the MRFO (Manta Ray Foraging Optimization) algorithm."""

    def __init__(self, problem):
        """
        Initialize a manta ray with a random position.

        Args:
            problem: Problem instance to solve
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.position = np.random.uniform(0, 1, self.dimension)
        # For VRP problems, bounds are [0,1]
        self.lower_bounds = np.zeros(self.dimension)
        self.upper_bounds = np.ones(self.dimension)
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

    def move(self, best_ray, t, T, alpha=2.0):
        """
        Move the manta ray according to MRFO algorithm rules.

        Args:
            best_ray: Best manta ray (leader)
            t: Current iteration
            T: Maximum number of iterations
            alpha: Spiral factor
        """
        r = random.random()  # Random factor to select behavior
        beta = (
            2 * math.exp(1 - (t / T)) * math.sin(2 * math.pi * r)
        )  # Controls the spiral

        if t / T < 0.5:  # First half: chain foraging
            for i in range(self.dimension):
                r1 = random.random()
                # Follow the best manta ray with spiral factor
                self.position[i] = (
                    best_ray.position[i]
                    + beta * (best_ray.position[i] - self.position[i])
                    + alpha * r1
                )
        else:  # Second half: cyclone foraging
            for i in range(self.dimension):
                r2 = random.random()
                if random.random() < 0.5:  # External spiral (moving away)
                    # Cyclone behavior
                    self.position[i] = best_ray.position[i] + alpha * math.exp(
                        beta * r2
                    ) * math.cos(2 * math.pi * r2) * abs(
                        best_ray.position[i] - self.position[i]
                    )
                else:  # Internal spiral (approaching)
                    # Depth exploration
                    self.position[i] = (
                        best_ray.position[i]
                        + random.random() * (best_ray.position[i] - self.position[i])
                        + beta * r2
                    )

        LB = self.lower_bounds
        UB = self.upper_bounds
        self.position = np.clip(self.position, LB, UB)

        # Optional phase: somersault foraging (at the end of each iteration or periodically)
        somersault_prob = 0.3  # probability of applying this step
        if random.random() < somersault_prob:
            for i in range(self.dimension):
                self.position[i] += random.uniform(-1, 1) * abs(
                    best_ray.position[i] - self.position[i]
                )

        # Reset fitness to recalculate
        self._fitness = None

    def copy(self, other):
        """
        Copy values from another individual to this one.

        Args:
            other: Another individual (MantaRay)
        """
        self.position = np.copy(other.position)
        self._fitness = other._fitness


class MRFO(MetaheuristicAlgorithm):
    """Implementation of the Manta Ray Foraging Optimization (MRFO) algorithm."""

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Initialize the MRFO algorithm.

        Args:
            problem: Problem instance
            population_size: Population size
            max_iterations: Maximum number of iterations
            seed: Seed for reproducibility
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.convergence_curve = []
        self.spiral_factor = 2.0  # Factor for spiral behavior

    def initialize_population(self):
        """Initialize the manta ray population."""
        # Set random seed if provided

        if self.seed is not None:
            random.seed(self.seed)

            np.random.seed(self.seed)

        self.population = []
        for _ in range(self.population_size):
            ray = MantaRay(self.problem)
            self.population.append(ray)

        # Find the best initial manta ray
        self.best_solution = self.population[0]
        for i in range(1, self.population_size):
            if self.population[i].is_better_than(self.best_solution):
                self.best_solution = self.population[i]

        # Initialize convergence curve with initial best fitness
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        """Update the population in each iteration."""
        # Current iteration is the size of convergence curve
        current_iter = len(self.convergence_curve)

        # Update each manta ray
        for i in range(self.population_size):
            # Don't move the best manta ray
            if self.population[i] is not self.best_solution:
                # Move according to MRFO algorithm
                self.population[i].move(
                    self.best_solution,
                    current_iter,
                    self.max_iterations,
                    self.spiral_factor,
                )

                # Update best solution if necessary
                if self.population[i].is_better_than(self.best_solution):
                    ray_copy = MantaRay(self.problem)
                    ray_copy.copy(self.population[i])
                    self.best_solution = ray_copy

        # Record best fitness in convergence curve
        self.convergence_curve.append(self.best_solution.fitness())
