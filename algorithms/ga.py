"""
Genetic Algorithm (GA)
=====================

GA is an evolutionary algorithm inspired by natural selection and genetics.
It evolves a population of solutions through selection, crossover, and mutation
operators to find optimal or near-optimal solutions.

Key concepts:
- Chromosome: Encoded solution (individual)
- Fitness: Quality measure of a solution
- Selection: Choosing parents for reproduction
- Crossover: Combining parents to create offspring
- Mutation: Random changes to maintain diversity

References:
    Holland, J. H. (1975). Adaptation in natural and artificial systems.
    Goldberg, D. E. (1989). Genetic algorithms in search, optimization, and machine learning.
    Bean, J. C. (1994). Genetic algorithms and random keys for sequencing and optimization.
        ORSA Journal on Computing, 6(2), 154-160.

This implementation uses random-key encoding [0,1] for VRP with uniform crossover
(Bean 1994) and swap mutation, suitable for permutation-decoded problems.
"""

import numpy as np
from typing import List, Tuple, Any, Optional
from algorithms.base import MetaheuristicAlgorithm, Individual


class Chromosome(Individual):
    """Chromosome (individual) in Genetic Algorithm representing a VRP solution."""

    def __init__(self, dimension: int, problem: Any, rng=None,
                 lower_bounds=None, upper_bounds=None):
        # Initialize basic attributes
        self.dimension = dimension
        self.problem = problem
        self.rng = rng if rng is not None else np.random.default_rng()

        # Bounds: default to [0, 1] (e.g. random-key VRP) when not provided.
        if lower_bounds is None:
            lower_bounds = np.zeros(dimension)
        if upper_bounds is None:
            upper_bounds = np.ones(dimension)
        self.lower_bounds = np.asarray(lower_bounds, dtype=float)
        self.upper_bounds = np.asarray(upper_bounds, dtype=float)

        # Initialize position (genes) and fitness
        self.position = self.rng.uniform(self.lower_bounds, self.upper_bounds, dimension)
        self._fitness = None

    def fitness(self) -> float:
        """Calculate and cache fitness value."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self) -> bool:
        """Check if chromosome represents a feasible solution."""
        return bool(self.problem.is_valid(self.position))

    def copy(self, other: 'Chromosome') -> None:
        """Copy values from another chromosome."""
        self.position = other.position.copy()
        self._fitness = other._fitness

    def move(self, population: list = None, iteration: int = 0, max_iterations: int = 100) -> None:
        """GA individuals don't move; evolution happens through genetic operators."""
        pass

    def crossover(self, other: 'Chromosome') -> Tuple['Chromosome', 'Chromosome']:
        """
        Uniform Crossover for random-key representation (Bean, 1994).

        Each gene is independently inherited from one parent with equal
        probability. This is the standard crossover for RKGA.

        Args:
            other: Another chromosome to crossover with

        Returns:
            Tuple of two offspring chromosomes
        """
        # Create offspring
        offspring1 = Chromosome(self.dimension, self.problem, rng=self.rng)
        offspring2 = Chromosome(self.dimension, self.problem, rng=self.rng)

        # Uniform crossover: for each gene, inherit from parent A or B
        mask = self.rng.random(self.dimension) < 0.5
        offspring1.position = np.where(mask, self.position, other.position)
        offspring2.position = np.where(mask, other.position, self.position)

        # Reset fitness cache
        offspring1._fitness = None
        offspring2._fitness = None

        return offspring1, offspring2

    def mutate(self, mutation_rate: float = 0.01) -> None:
        """
        Apply mutation using swap mutation (exchange two random positions).

        Args:
            mutation_rate: Probability of mutation for each gene
        """
        for i in range(self.dimension):
            if self.rng.random() < mutation_rate:
                # Swap with another random position
                j = int(self.rng.integers(0, self.dimension))
                self.position[i], self.position[j] = self.position[j], self.position[i]

        # Reset fitness cache after mutation
        self._fitness = None


class GA(MetaheuristicAlgorithm):
    """
    Genetic Algorithm for Vehicle Routing Problem.

    GA evolves a population of solutions using selection, crossover, and mutation
    operators inspired by natural evolution. This implementation uses tournament
    selection and uniform crossover suitable for random-key encoded problems.
    """

    def __init__(self, problem: Any, population_size: int = 50,
                 max_iterations: int = 100, seed: int = None,
                 crossover_rate: float = 0.8, mutation_rate: float = 0.1,
                 tournament_size: int = 3, elitism_size: int = 2,
                 use_il: bool = False, il_model: Any = None):
        """
        Initialize Genetic Algorithm.

        Args:
            problem: VRP problem instance
            population_size: Number of individuals in population
            max_iterations: Maximum number of generations
            seed: Random seed for reproducibility
            crossover_rate: Probability of crossover
            mutation_rate: Probability of mutation per gene
            tournament_size: Number of individuals in tournament selection
            elitism_size: Number of best individuals to preserve
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.elitism_size = elitism_size
        # IL hooks: multiplicative modulation of (crossover_rate, mutation_rate).
        self.use_il = use_il
        self.il_model = il_model
        self.base_crossover_rate = float(crossover_rate)
        self.base_mutation_rate = float(mutation_rate)

    def _get_il_params(self, iteration: int) -> tuple:
        """Return (cx_factor, mut_factor) multipliers; neutral (1.0, 1.0)."""
        if not self.use_il or self.il_model is None:
            return 1.0, 1.0
        try:
            cxf, mutf = self.il_model.predict(self, iteration)
            return float(cxf), float(mutf)
        except Exception:
            return 1.0, 1.0

    def initialize_population(self) -> None:
        """Initialize population with random chromosomes."""
        self.population = []
        dim = self.problem.get_dimension()
        lo = getattr(self.problem, "get_lower_bounds", lambda: np.zeros(dim))()
        hi = getattr(self.problem, "get_upper_bounds", lambda: np.ones(dim))()
        for i in range(self.population_size):
            chromosome = Chromosome(
                dimension=dim,
                problem=self.problem,
                rng=self.rng,
                lower_bounds=lo,
                upper_bounds=hi,
            )
            self.population.append(chromosome)

        self.best_solution = min(self.population, key=lambda x: x.fitness())
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self) -> None:
        """Evolve population for one generation."""
        # IL modulation of control parameters (neutral by default). Rates are
        # probabilities, so clip to [0, 1] after applying the factors.
        iteration = len(self.convergence_curve) - 1
        cxf, mutf = self._get_il_params(iteration)
        self.crossover_rate = float(np.clip(self.base_crossover_rate * cxf, 0.0, 1.0))
        self.mutation_rate = float(np.clip(self.base_mutation_rate * mutf, 0.0, 1.0))

        self.population = self.evolve_population()

        # Track best solution
        current_best = min(self.population, key=lambda x: x.fitness())
        if current_best.fitness() < self.best_solution.fitness():
            self.best_solution = current_best

        self.convergence_curve.append(self.best_solution.fitness())

    def tournament_selection(self) -> Chromosome:
        """
        Tournament selection: randomly select k individuals and return the best.

        Returns:
            Selected chromosome
        """
        indices = self.rng.choice(len(self.population), size=self.tournament_size, replace=False)
        tournament = [self.population[i] for i in indices]
        return min(tournament, key=lambda x: x.fitness())

    def evolve_population(self) -> List[Chromosome]:
        """
        Create new population through selection, crossover, and mutation.

        Returns:
            New population
        """
        new_population = []

        # Elitism: preserve best individuals
        sorted_pop = sorted(self.population, key=lambda x: x.fitness())
        new_population.extend(sorted_pop[:self.elitism_size])

        # Generate rest of population
        while len(new_population) < self.population_size:
            # Selection
            parent1 = self.tournament_selection()
            parent2 = self.tournament_selection()

            # Crossover
            if self.rng.random() < self.crossover_rate:
                offspring1, offspring2 = parent1.crossover(parent2)
            else:
                # No crossover, copy parents
                offspring1 = object.__new__(Chromosome)
                offspring1.dimension = parent1.dimension
                offspring1.problem = parent1.problem
                offspring1.rng = self.rng
                offspring1.position = parent1.position.copy()
                offspring1._fitness = None

                offspring2 = object.__new__(Chromosome)
                offspring2.dimension = parent2.dimension
                offspring2.problem = parent2.problem
                offspring2.rng = self.rng
                offspring2.position = parent2.position.copy()
                offspring2._fitness = None

            # Mutation
            offspring1.mutate(self.mutation_rate)
            offspring2.mutate(self.mutation_rate)

            # Add to new population
            new_population.append(offspring1)
            if len(new_population) < self.population_size:
                new_population.append(offspring2)

        return new_population[:self.population_size]

    def get_parameters(self) -> dict:
        """Get algorithm parameters for reporting."""
        return {
            'algorithm': 'GA',
            'population_size': self.population_size,
            'max_iterations': self.max_iterations,
            'crossover_rate': self.crossover_rate,
            'mutation_rate': self.mutation_rate,
            'tournament_size': self.tournament_size,
            'elitism_size': self.elitism_size,
            'seed': self.seed
        }
