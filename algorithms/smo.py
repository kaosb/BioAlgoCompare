"""
Starling Murmuration Optimizer (SMO) - Version adapted for continuous optimization
Source: Zamani, Nadimi-Shahraki & Gandomi (2022), Computer Methods in Applied Mechanics and Engineering.
DOI: 10.1016/j.cma.2022.114616
"""

import numpy as np
import random
import copy
from algorithms.base import Individual, MetaheuristicAlgorithm


class Starling(Individual):
    """Individual starling in the SMO algorithm.

    Represents a starling with its position and murmuration behaviors.
    Starlings exhibit collective motion patterns and adaptive flocking.

    Attributes:
        problem: The optimization problem instance
        position: Current position in the search space
        personal_best_position: Best position found by this starling
        _fitness: Cached fitness value
        personal_best_fitness: Best fitness value found
    """

    def __init__(self, problem):
        """
        Initialize a starling for the SMO algorithm.

        Args:
            problem: Problem instance to solve
        """
        self.problem = problem
        # Generate random solution - continuous representation
        self.position = self.problem.random_solution()
        self.personal_best_position = copy.deepcopy(self.position)
        self._fitness = None
        self.personal_best_fitness = None

    def fitness(self):
        """Calculate the individual's fitness."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self):
        """Check if the individual represents a feasible solution."""
        return bool(self.problem.is_valid(self.position))

    def copy(self):
        """Create a copy of the current starling."""
        new_starling = Starling(self.problem)
        new_starling.position = copy.deepcopy(self.position)
        new_starling.personal_best_position = copy.deepcopy(self.personal_best_position)
        new_starling._fitness = self._fitness
        new_starling.personal_best_fitness = self.personal_best_fitness
        return new_starling

    def move(
        self, best_position, behavior_type, members=None, coef=0.5, it=0, max_it=100
    ):
        """
        Move the starling - adapted for continuous representation (numpy array).
        - behavior_type: 'separating', 'diving', 'whirling'
        - coef and it/max_it can be used to tune operator intensity
        """
        # Create backup copy of current position
        new_position = copy.deepcopy(self.position)

        # Temporal adaptation (decreases with iterations)
        decay = 1 - (it / max_it) if max_it > 0 else 0.5

        try:
            # Apply different behaviors according to strategy
            if behavior_type == "separating":
                # More random exploration
                r = np.random.random(new_position.shape)
                new_position = new_position + decay * coef * (2 * r - 1)
            elif behavior_type == "diving":
                # Exploitation towards best solution (smaller movement)
                if (
                    hasattr(best_position, "shape")
                    and best_position.shape == new_position.shape
                ):
                    new_position = new_position + decay * coef * (
                        best_position - new_position
                    )
                else:
                    # Small perturbation if no best information available
                    r = np.random.random(new_position.shape)
                    new_position = new_position + decay * coef * 0.1 * (2 * r - 1)
            elif behavior_type == "whirling":
                # Intermediate movement - combination of exploration and exploitation
                if (
                    hasattr(best_position, "shape")
                    and best_position.shape == new_position.shape
                ):
                    r1 = np.random.random(new_position.shape)
                    r2 = np.random.random(new_position.shape)
                    new_position = new_position + decay * coef * (
                        r1 * (best_position - new_position)
                        + r2 * 0.1 * (2 * np.random.random(new_position.shape) - 1)
                    )
                else:
                    # Random movement if no best information available
                    r = np.random.random(new_position.shape)
                    new_position = new_position + decay * coef * 0.5 * (2 * r - 1)

            # Ensure position is within bounds [0,1]
            new_position = np.clip(new_position, 0, 1)
        except Exception:
            # In case of error, apply small perturbation
            new_position = (
                self.position
                + np.random.uniform(-0.05, 0.05, self.position.shape) * decay
            )
            new_position = np.clip(new_position, 0, 1)

        # Evaluate and update if improved
        try:
            new_fit = self.problem.evaluate(new_position)
            curr_fit = self.fitness()

            # Accept if improved or with small probability (Metropolis criterion)
            if new_fit < curr_fit or random.random() < 0.1 * decay:
                self.position = new_position
                self._fitness = new_fit

                # Update personal best if applicable
                if (
                    self.personal_best_fitness is None
                    or new_fit < self.personal_best_fitness
                ):
                    self.personal_best_position = copy.deepcopy(self.position)
                    self.personal_best_fitness = new_fit
        except Exception:
            # If error, keep current position
            pass


class SMO(MetaheuristicAlgorithm):
    """Implementation of the Starling Murmuration Optimizer (SMO) algorithm."""

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Initialize the SMO algorithm.

        Args:
            problem: Problem instance
            population_size: Population size
            max_iterations: Maximum number of iterations
            seed: Seed for reproducibility
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.k = min(10, self.population_size // 3)  # Number of groups (flocks)
        self.mu = 0.3  # Proportion of individuals in separation
        self.seed = seed  # Save seed as attribute
        self.convergence_curve = []  # Initialize convergence curve

    def initialize_population(self):
        """Initialize the starling population."""
        # Initialize seed if available
        if self.seed is not None:
            random.seed(self.seed)
            np.random.seed(self.seed)

        # Reset convergence_curve
        self.convergence_curve = []

        # Initialize starling population
        self.population = []
        for _ in range(self.population_size):
            s = Starling(self.problem)
            s._fitness = s.fitness()
            s.personal_best_fitness = s._fitness
            self.population.append(s)

        # Save best solution found
        self.best_solution = min(self.population, key=lambda s: s.fitness()).copy()
        # Add first convergence point
        self.convergence_curve.append(float(self.best_solution.fitness()))

    def update_population(self):
        """Update the starling population in each iteration."""
        # Current iteration
        current_iter = len(self.convergence_curve)

        # Sort population by fitness
        self.population.sort(key=lambda s: s.fitness())

        # Size of separation subset (exploration)
        sep_size = int(self.mu * self.population_size)

        # Divide into k groups (flocks)
        flocks = []
        group_size = max(1, self.population_size // self.k)

        for i in range(self.k):
            start_idx = i * group_size
            end_idx = (i + 1) * group_size if i < self.k - 1 else self.population_size
            flocks.append(self.population[start_idx:end_idx])

        # Calculate average quality of each group
        flock_qualities = []
        for flock in flocks:
            quality = sum(s.fitness() for s in flock) / len(flock)
            flock_qualities.append(quality)

        avg_quality = sum(flock_qualities) / len(flock_qualities)

        # Update each starling according to its group and position
        for i, s in enumerate(self.population):
            # Determine behavior and group
            if i < sep_size:
                # Exploration group (separation)
                behavior = "separating"
                flock_members = None
            else:
                # Regular group based on quality
                flock_idx = min(i // group_size, self.k - 1)
                flock_members = flocks[flock_idx]
                if flock_qualities[flock_idx] < avg_quality:
                    # Group better than average: diving (exploitation)
                    behavior = "diving"
                else:
                    # Group worse than average: whirling (exploration)
                    behavior = "whirling"

            # Adaptation factor based on position
            coef = 0.5 * (1 - i / self.population_size)

            # Move the starling
            s.move(
                best_position=self.best_solution.position,
                behavior_type=behavior,
                members=flock_members,
                coef=coef,
                it=current_iter,
                max_it=self.max_iterations,
            )

        # Update best solution found globally
        best_individual = min(self.population, key=lambda s: s.fitness())
        if best_individual.is_better_than(self.best_solution):
            self.best_solution = best_individual.copy()

        # Add point to convergence curve
        self.convergence_curve.append(float(self.best_solution.fitness()))

    def get_convergence_curve(self):
        """Retorna la curva de convergencia."""
        if not isinstance(self.convergence_curve, list):
            return []
        return self.convergence_curve
