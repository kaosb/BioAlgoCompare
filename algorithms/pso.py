"""
Particle Swarm Optimization (PSO) Algorithm
==========================================

PSO is a population-based optimization algorithm inspired by social behavior of bird flocking
or fish schooling. Each particle represents a potential solution that moves through the search
space influenced by its own best position and the global best position found by the swarm.

Key concepts:
- Velocity: Direction and speed of particle movement
- Personal best (pbest): Best position found by each particle
- Global best (gbest): Best position found by the entire swarm
- Inertia weight: Controls exploration vs exploitation

References:
    Kennedy, J., & Eberhart, R. (1995). Particle swarm optimization.
    Proceedings of ICNN'95 - International Conference on Neural Networks.

This implementation adapts continuous PSO for discrete VRP using velocity clamping
and probabilistic position updates.
"""

import numpy as np
from typing import List, Tuple, Any, Optional
from algorithms.base import MetaheuristicAlgorithm, Individual


class Particle(Individual):
    """Particle in PSO algorithm with velocity and memory of personal best."""

    def __init__(self, dimension: int, problem: Any, rng=None):
        # Initialize basic attributes
        self.dimension = dimension
        self.problem = problem
        self.rng = rng if rng is not None else np.random.default_rng()

        # Initialize position and fitness
        self.position = self.rng.random(dimension)
        self._fitness = None

        # Initialize velocity for each dimension
        self.velocity: np.ndarray = self.rng.uniform(-1, 1, dimension)
        # Personal best position and fitness
        self.pbest_position: np.ndarray = self.position.copy()
        self.pbest_fitness: float = float('inf')
        # PSO parameters
        self.w = 0.9  # Inertia weight (linearly decreasing, Shi & Eberhart 1998)
        self.c1 = 2.0  # Cognitive parameter (Kennedy & Eberhart 1995)
        self.c2 = 2.0  # Social parameter (Kennedy & Eberhart 1995)

    def fitness(self) -> float:
        """Calculate and cache fitness value."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self) -> bool:
        """Check if particle position represents a feasible solution."""
        return bool(self.problem.is_valid(self.position))

    def copy(self, other: 'Particle') -> None:
        """Copy values from another particle."""
        self.position = other.position.copy()
        self.velocity = other.velocity.copy()
        self.pbest_position = other.pbest_position.copy()
        self.pbest_fitness = other.pbest_fitness
        self._fitness = other._fitness

    def update_pbest(self) -> None:
        """Update personal best if current position is better."""
        if self.fitness() < self.pbest_fitness:
            self.pbest_position = self.position.copy()
            self.pbest_fitness = self.fitness()

    def move(self, population: list = None, iteration: int = 0, max_iterations: int = 100) -> None:
        """
        Update particle velocity and position based on PSO equations.

        Args:
            population: The current population of particles
            iteration: Current iteration
            max_iterations: Maximum iterations
        """
        # Note: In PSO, particle movement is handled by the main algorithm
        # This is just to satisfy the abstract method requirement
        pass

    def update_velocity_position(self, gbest_position: np.ndarray) -> None:
        """
        Update particle velocity and position using PSO equations.

        Args:
            gbest_position: Global best position found by the swarm
        """
        # PSO velocity update equation
        # v = w*v + c1*r1*(pbest - x) + c2*r2*(gbest - x)
        r1 = self.rng.random(self.dimension)
        r2 = self.rng.random(self.dimension)

        cognitive = self.c1 * r1 * (self.pbest_position - self.position)
        social = self.c2 * r2 * (gbest_position - self.position)

        self.velocity = self.w * self.velocity + cognitive + social

        # Velocity clamping (Engelbrecht recommends 10-20% of search range)
        v_max = 0.2  # 20% of [0,1] range
        self.velocity = np.clip(self.velocity, -v_max, v_max)

        # Update position
        self.position = self.position + self.velocity

        # Ensure position stays within bounds [0, 1]
        self.position = np.clip(self.position, 0, 1)

        # Evaluate new position
        self._fitness = None  # Reset fitness cache
        self.update_pbest()


class PSO(MetaheuristicAlgorithm):
    """
    Particle Swarm Optimization algorithm for Vehicle Routing Problem.

    PSO simulates social behavior where particles (solutions) move through
    the search space influenced by their own experience and the swarm's
    collective knowledge.
    """

    def __init__(self, problem: Any, population_size: int = 30,
                 max_iterations: int = 100, seed: int = None):
        """
        Initialize PSO algorithm.

        Args:
            problem: VRP problem instance
            population_size: Number of particles in the swarm
            max_iterations: Maximum number of iterations
            seed: Random seed for reproducibility
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.gbest_position: Optional[np.ndarray] = None
        self.gbest_fitness: float = float('inf')

    def initialize_population(self) -> None:
        """Initialize swarm of particles with random positions and velocities."""
        self.population = []
        for i in range(self.population_size):
            particle = Particle(
                dimension=self.problem.get_dimension(),
                problem=self.problem,
                rng=self.rng,
            )
            self.population.append(particle)

            # Update global best if needed
            if particle.fitness() < self.gbest_fitness:
                self.gbest_fitness = particle.fitness()
                self.gbest_position = particle.position.copy()

        self.best_solution = min(self.population, key=lambda p: p.fitness())
        self.convergence_curve = [self.gbest_fitness]

    def update_population(self) -> None:
        """Update swarm positions for one iteration."""
        iteration = len(self.convergence_curve) - 1

        # Adaptive inertia weight (linearly decreasing 0.9 -> 0.4)
        # Update BEFORE moving particles so first iteration uses correct w
        for particle in self.population:
            particle.w = 0.9 - (0.9 - 0.4) * iteration / self.max_iterations

        # Move all particles with updated w
        for particle in self.population:
            particle.update_velocity_position(self.gbest_position)

        # Update global best
        self.update_global_best()

        # Track convergence
        self.convergence_curve.append(self.gbest_fitness)

        # Update best_solution
        best_particle = min(self.population, key=lambda p: p.fitness())
        self.best_solution = best_particle

    def update_global_best(self) -> None:
        """Update global best position based on all particles."""
        for particle in self.population:
            if particle.pbest_fitness < self.gbest_fitness:
                self.gbest_fitness = particle.pbest_fitness
                self.gbest_position = particle.pbest_position.copy()

    def get_parameters(self) -> dict:
        """Get algorithm parameters for reporting."""
        return {
            'algorithm': 'PSO',
            'population_size': self.population_size,
            'max_iterations': self.max_iterations,
            'inertia_weight': '0.9 -> 0.4',
            'c1': 2.0,
            'c2': 2.0,
            'v_max': 0.2,
            'seed': self.seed
        }
