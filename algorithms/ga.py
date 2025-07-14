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

This implementation uses order-based encoding suitable for VRP with specialized
crossover and mutation operators that preserve valid routes.
"""

import numpy as np
from typing import List, Tuple, Any, Optional
from algorithms.base import MetaheuristicAlgorithm, Individual


class Chromosome(Individual):
    """Chromosome (individual) in Genetic Algorithm representing a VRP solution."""
    
    def __init__(self, dimension: int, problem: Any, seed: int = None):
        # Initialize basic attributes
        self.dimension = dimension
        self.problem = problem
        self.rng = np.random.RandomState(seed) if seed is not None else np.random
        
        # Initialize position (genes) and fitness
        self.position = self.rng.random(dimension)
        self._fitness = None
    
    def fitness(self) -> float:
        """Calculate and cache fitness value."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness
    
    def is_feasible(self) -> bool:
        """Check if chromosome represents a feasible solution."""
        return self.problem.is_valid(self.position)
    
    def copy(self, other: 'Chromosome') -> None:
        """Copy values from another chromosome."""
        self.position = other.position.copy()
        self._fitness = other._fitness
        
    def move(self, population: list = None, iteration: int = 0, max_iterations: int = 100) -> None:
        """GA individuals don't move; evolution happens through genetic operators."""
        pass
    
    def crossover(self, other: 'Chromosome') -> Tuple['Chromosome', 'Chromosome']:
        """
        Order Crossover (OX) for permutation representation.
        Preserves relative order of cities from parents.
        
        Args:
            other: Another chromosome to crossover with
            
        Returns:
            Tuple of two offspring chromosomes
        """
        # Create offspring
        offspring1 = Chromosome(self.dimension, self.problem)
        offspring2 = Chromosome(self.dimension, self.problem)
        
        # Select crossover points
        point1 = self.rng.randint(0, self.dimension - 1)
        point2 = self.rng.randint(point1 + 1, self.dimension)
        
        # Copy segment from parents
        offspring1.position[point1:point2] = self.position[point1:point2]
        offspring2.position[point1:point2] = other.position[point1:point2]
        
        # Fill remaining positions preserving order
        self._fill_offspring(offspring1.position, other.position, point1, point2)
        self._fill_offspring(offspring2.position, self.position, point1, point2)
        
        return offspring1, offspring2
    
    def _fill_offspring(self, offspring: np.ndarray, parent: np.ndarray, 
                       start: int, end: int) -> None:
        """Fill remaining positions in offspring preserving order from parent."""
        # Get values not in the copied segment
        segment_values = set(offspring[start:end])
        remaining_values = [v for v in parent if v not in segment_values]
        
        # Fill positions before and after segment
        fill_idx = 0
        for i in range(self.dimension):
            if i < start or i >= end:
                if fill_idx < len(remaining_values):
                    offspring[i] = remaining_values[fill_idx]
                    fill_idx += 1
    
    def mutate(self, mutation_rate: float = 0.01) -> None:
        """
        Apply mutation using swap mutation (exchange two random positions).
        
        Args:
            mutation_rate: Probability of mutation for each gene
        """
        for i in range(self.dimension):
            if self.rng.random() < mutation_rate:
                # Swap with another random position
                j = self.rng.randint(0, self.dimension)
                self.position[i], self.position[j] = self.position[j], self.position[i]
        
        # Reset fitness cache after mutation
        self._fitness = None


class GA(MetaheuristicAlgorithm):
    """
    Genetic Algorithm for Vehicle Routing Problem.
    
    GA evolves a population of solutions using selection, crossover, and mutation
    operators inspired by natural evolution. This implementation uses tournament
    selection and order crossover suitable for permutation-based problems.
    """
    
    def __init__(self, problem: Any, population_size: int = 50, 
                 max_iterations: int = 100, seed: int = None,
                 crossover_rate: float = 0.8, mutation_rate: float = 0.1,
                 tournament_size: int = 3, elitism_size: int = 2):
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
        self.rng = np.random.RandomState(seed) if seed is not None else np.random
    
    def update_population(self) -> None:
        """Update population (required by base class but handled in execute)."""
        pass
        
    def initialize_population(self) -> List[Chromosome]:
        """Initialize population with random chromosomes."""
        self.population = []
        for i in range(self.population_size):
            chromosome = Chromosome(
                dimension=self.problem.get_dimension(),
                problem=self.problem,
                seed=self.seed + i if self.seed else None
            )
            self.population.append(chromosome)
        return self.population
    
    def tournament_selection(self) -> Chromosome:
        """
        Tournament selection: randomly select k individuals and return the best.
        
        Returns:
            Selected chromosome
        """
        tournament = self.rng.choice(self.population, size=self.tournament_size, replace=False)
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
                offspring1 = Chromosome(self.problem.get_dimension(), self.problem)
                offspring2 = Chromosome(self.problem.get_dimension(), self.problem)
                offspring1.position = parent1.position.copy()
                offspring2.position = parent2.position.copy()
            
            # Mutation
            offspring1.mutate(self.mutation_rate)
            offspring2.mutate(self.mutation_rate)
            
            # Add to new population
            new_population.append(offspring1)
            if len(new_population) < self.population_size:
                new_population.append(offspring2)
        
        return new_population[:self.population_size]
    
    def execute(self) -> Tuple[Any, float, List[float]]:
        """
        Execute Genetic Algorithm.
        
        Returns:
            Tuple of (best_solution, best_fitness, convergence_history)
        """
        # Initialize population
        self.population = self.initialize_population()
        self.convergence = []
        self.convergence_curve = []  # Initialize convergence curve for base class compatibility
        
        best_chromosome = min(self.population, key=lambda x: x.fitness())
        best_fitness = best_chromosome.fitness()
        
        # Evolution loop
        for generation in range(self.max_iterations):
            # Evolve population
            self.population = self.evolve_population()
            
            # Track best solution
            current_best = min(self.population, key=lambda x: x.fitness())
            if current_best.fitness() < best_fitness:
                best_chromosome = current_best
                best_fitness = current_best.fitness()
            
            # Track convergence
            self.convergence.append(best_fitness)
            self.convergence_curve.append(best_fitness)  # Add to convergence curve
            
            # Optional: Adaptive mutation rate
            # Increase mutation if population is converging
            fitness_values = [ind.fitness() for ind in self.population]
            if np.std(fitness_values) < 1.0:  # Low diversity
                self.mutation_rate = min(0.2, self.mutation_rate * 1.1)
            else:
                self.mutation_rate = max(0.01, self.mutation_rate * 0.95)
        
        # Store best solution for base class compatibility
        self.best_solution = best_chromosome
        
        # Return best solution found
        best_solution = self.problem.decode_solution(best_chromosome.position)
        return best_solution[0], best_fitness, self.convergence
    
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