"""
Artificial Hummingbird Algorithm (AHA)
Source: Zhao, Wang & Mirjalili (2022), Computer Methods in Applied Mechanics and Engineering.
DOI: 10.1016/j.cma.2021.114194
"""

import numpy as np
import random
from typing import List, Tuple
from copy import deepcopy
from algorithms.base import Individual, MetaheuristicAlgorithm


class Hummingbird(Individual):
    """Individual hummingbird in the AHA algorithm.

    Represents a hummingbird with its position, memory table, and foraging behaviors.
    Hummingbirds exhibit three flight skills and two modes of foraging.

    Attributes:
        position: Current position in the search space
        personal_best_position: Best position found by this hummingbird
        bounds: Search space boundaries
        dimension: Number of dimensions in the problem
        memory_table: Set of visited food sources to avoid revisiting
        _fitness: Cached fitness value
    """

    def __init__(self, position: np.ndarray, bounds: List[Tuple[float, float]]):
        self.position = np.array(position, dtype=float)
        self.personal_best_position = self.position.copy()
        self._fitness = None
        self.bounds = bounds
        self.dimension = len(position)
        self.memory_table = set()

    def fitness(self, objective_function=None):
        """Calculate or return cached fitness value."""
        if objective_function is not None and self._fitness is None:
            self._fitness = objective_function(self.position)
        return self._fitness

    def is_better_than(self, other):
        """Compare if this individual is better than other."""
        return bool(self._fitness < other._fitness)

    def is_feasible(self):
        """Check if the individual represents a feasible solution."""
        return True  # Assuming bound constraints are enforced elsewhere

    def move(self, population=None, iteration=None, max_iterations=None):
        """
        Implements hummingbird movement according to flight type and foraging mode.
        Adapted for the interface required by the Individual base class.

        Args:
            population: Current population of individuals.
            iteration: Current algorithm iteration.
            max_iterations: Maximum number of iterations.
        """
        # This specific AHA implementation will be called from update_population()
        # and not through this interface, so we don't need to implement the logic here
        pass

    def aha_move(
        self, best_individual, population: List["Hummingbird"], memory_table: set
    ):
        """
        Implements hummingbird movement according to flight type and foraging mode.
        """
        # Random selection of flight type: axial, diagonal or omnidirectional
        flight_type = np.random.choice(["axial", "diagonal", "omnidirectional"])

        # Random selection of foraging mode: guided, territorial, migratory
        forage_mode = np.random.choice(["guided", "territorial", "migratory"])

        new_position = self.position.copy()
        dim = self.dimension

        if flight_type == "axial":
            # Movement in a single dimension (axis)
            axis = np.random.randint(0, dim)
            step = np.random.uniform(-1, 1)
            direction = np.zeros(dim)
            direction[axis] = step
        elif flight_type == "diagonal":
            # Movement in a diagonal (subset of dimensions)
            direction = np.random.uniform(-1, 1, size=dim)
            # To simulate diagonal, set some random zeros
            zero_mask = np.random.rand(dim) < 0.5
            direction[zero_mask] = 0
        else:  # omnidirectional
            # Movement in any direction
            direction = np.random.uniform(-1, 1, size=dim)

        # Normalize direction so step is proportional
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction = direction / norm

        # Step parameters (can be adjusted)
        step_size = 0.1  # base step size

        if forage_mode == "guided":
            # Eq. 6: Movement towards best individual with memory
            diff = best_individual.personal_best_position - self.position
            new_position = self.position + step_size * diff + step_size * direction
        elif forage_mode == "territorial":
            # Eq. 7: Local random perturbation
            new_position = self.position + step_size * direction * np.random.uniform(
                -1, 1
            )
        else:  # migratory
            # Eq. 8: Towards a random distant individual
            other = self
            while other is self:
                other = np.random.choice(population)
            diff = other.position - self.position
            new_position = self.position + step_size * diff + step_size * direction

        # Clip to keep within bounds
        for i in range(dim):
            low, high = self.bounds[i]
            new_position[i] = np.clip(new_position[i], low, high)

        # Discretize position for memory table
        discretized_pos = tuple(np.round(new_position, decimals=6))

        # Check if position is already in memory to avoid repetition
        if discretized_pos in memory_table:
            # If already visited, make small random movement to avoid stagnation
            new_position += step_size * np.random.uniform(-1, 1, size=dim)
            for i in range(dim):
                low, high = self.bounds[i]
                new_position[i] = np.clip(new_position[i], low, high)
            discretized_pos = tuple(np.round(new_position, decimals=6))

        # Update position and memory
        self.position = new_position
        self._fitness = None  # Reset fitness
        memory_table.add(discretized_pos)

    def copy(self, other=None):
        """
        Copy values from another individual to this one, or create a copy if no other is provided.

        Args:
            other: Another individual to copy from (optional).

        Returns:
            A copy of the individual if other is None, or None if attributes were copied.
        """
        if other is None:
            # Create and return a new copy
            new_copy = Hummingbird(self.position.copy(), self.bounds)
            new_copy.personal_best_position = self.personal_best_position.copy()
            new_copy._fitness = self._fitness
            return new_copy
        else:
            # Copy attributes from other
            self.position = other.position.copy()
            self.personal_best_position = other.personal_best_position.copy()
            self._fitness = other._fitness
            self.bounds = other.bounds
            self.dimension = other.dimension
            return None


class AHA(MetaheuristicAlgorithm):
    """Artificial Hummingbird Algorithm (AHA) implementation.

    A bio-inspired metaheuristic that simulates the intelligent foraging behavior
    and flight skills of hummingbirds. The algorithm incorporates three flight
    skills (diagonal, omnidirectional, and axial) and two foraging modes
    (guided and territorial).

    Args:
        problem: The optimization problem to solve
        population_size: Number of hummingbirds in the population (default: 30)
        max_iterations: Maximum number of iterations (default: 100)
        seed: Random seed for reproducibility (default: None)

    Attributes:
        population: List of Hummingbird individuals
        memory_table: Global memory of visited food sources
        best_solution: Best solution found so far
        convergence_curve: Fitness values over iterations
    """

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        super().__init__(problem, population_size, max_iterations, seed)
        self.population: List[Hummingbird] = []
        self.memory_table = set()
        self.best_solution = None
        self.convergence_curve = []

    def initialize_population(self):
        # Set random seed if provided
        if self.seed is not None:
            np.random.seed(self.seed)

        self.population = []
        # For VRP problem, we use domain [0,1] for each dimension
        dim = self.problem.get_dimension()
        bounds = [(0, 1) for _ in range(dim)]

        for _ in range(self.population_size):
            position = np.random.uniform(0, 1, size=dim)
            hummingbird = Hummingbird(position, bounds)
            discretized_pos = tuple(np.round(position, decimals=6))
            self.memory_table.add(discretized_pos)
            self.population.append(hummingbird)
        # Initialize fitness
        for ind in self.population:
            ind._fitness = self.problem.evaluate(ind.position)
        # Initialize best solution
        self.best_solution = min(self.population, key=lambda ind: ind.fitness()).copy()
        # Record initial fitness in convergence curve
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        # Sort population by fitness
        for ind in self.population:
            if ind._fitness is None:
                ind._fitness = self.problem.evaluate(ind.position)
        self.population.sort(key=lambda ind: ind.fitness())
        # Update best solution
        current_best = self.population[0]
        if current_best.fitness() < self.best_solution.fitness():
            self.best_solution = current_best.copy()

        # Apply aha_move to all except the best
        for ind in self.population[1:]:
            ind.aha_move(self.best_solution, self.population, self.memory_table)
            # Update personal best if improved
            current_fitness = self.problem.evaluate(ind.position)
            ind._fitness = current_fitness

            # Calculate fitness of personal_best_position
            best_fitness = self.problem.evaluate(ind.personal_best_position)

            if current_fitness < best_fitness:
                ind.personal_best_position = ind.position.copy()

        self.convergence_curve.append(self.best_solution.fitness())

    # No need to implement run or execute - using the base class's execute method
