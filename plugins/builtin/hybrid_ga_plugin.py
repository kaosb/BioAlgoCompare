"""
Plugin: name: HybridGA
Plugin: version: 1.0
Plugin: author: BioAlgoCompare Team
Plugin: description: Hybrid Genetic Algorithm with local search
Plugin: problem_types: optimization, vrp
Plugin: dependencies: numpy
"""

import numpy as np
from typing import Optional, List
from algorithms.base_v2 import MetaheuristicAlgorithm, Individual


class HybridGAIndividual(Individual):
    """Individual for Hybrid Genetic Algorithm."""
    
    def __init__(self, problem, position=None):
        super().__init__(problem, position)
        self.local_search_applied = False
    
    def local_search(self, neighborhood_size: int = 5):
        """Apply local search to improve the individual."""
        if self.local_search_applied:
            return
        
        best_position = self.position.copy()
        best_fitness = self.fitness()
        
        # Simple neighborhood search
        for _ in range(neighborhood_size):
            # Create neighbor by small perturbation
            neighbor_position = self.position.copy()
            idx = np.random.randint(0, len(neighbor_position))
            neighbor_position[idx] += np.random.normal(0, 0.1)
            neighbor_position[idx] = np.clip(neighbor_position[idx], 0, 1)
            
            # Evaluate neighbor
            temp_position = self.position
            self.position = neighbor_position
            neighbor_fitness = self.fitness()
            
            # Keep if better
            if neighbor_fitness < best_fitness:
                best_fitness = neighbor_fitness
                best_position = neighbor_position.copy()
            else:
                self.position = temp_position
        
        self.position = best_position
        self._fitness = best_fitness
        self.local_search_applied = True


class HybridGeneticAlgorithm(MetaheuristicAlgorithm):
    """
    Hybrid Genetic Algorithm combining GA with local search.
    
    This algorithm enhances the standard GA by applying local search
    to promising individuals, balancing global exploration with local
    exploitation.
    """
    
    def __init__(self, problem, population_size: int = 30, 
                 max_iterations: int = 100,
                 crossover_rate: float = 0.8,
                 mutation_rate: float = 0.1,
                 elite_size: int = 2,
                 local_search_prob: float = 0.2,
                 local_search_neighborhood: int = 5,
                 seed: Optional[int] = None):
        """
        Initialize Hybrid Genetic Algorithm.
        
        Args:
            problem: Problem instance
            population_size: Size of population
            max_iterations: Maximum iterations
            crossover_rate: Crossover probability
            mutation_rate: Mutation probability
            elite_size: Number of elite individuals
            local_search_prob: Probability of applying local search
            local_search_neighborhood: Size of local search neighborhood
            seed: Random seed
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size
        self.local_search_prob = local_search_prob
        self.local_search_neighborhood = local_search_neighborhood
        
        # Initialize population
        self.initialize_population()
    
    def _create_individual(self) -> Individual:
        """Create a new individual."""
        return HybridGAIndividual(self.problem)
    
    def initialize_population(self) -> None:
        """Initialize the population."""
        self.population = []
        for _ in range(self.population_size):
            individual = self._create_individual()
            self.population.append(individual)
    
    def iterate(self) -> None:
        """Perform one iteration of the hybrid GA."""
        # Sort population by fitness
        self.population.sort(key=lambda x: x.fitness())
        
        # Create new population
        new_population = []
        
        # Keep elite
        for i in range(self.elite_size):
            new_population.append(self.population[i].copy())
        
        # Generate rest of population
        while len(new_population) < self.population_size:
            # Selection
            parent1 = self._tournament_selection()
            parent2 = self._tournament_selection()
            
            # Crossover
            if self.random.random() < self.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1 = parent1.copy()
                child2 = parent2.copy()
            
            # Mutation
            if self.random.random() < self.mutation_rate:
                self._mutate(child1)
            if self.random.random() < self.mutation_rate:
                self._mutate(child2)
            
            # Local search
            if self.random.random() < self.local_search_prob:
                child1.local_search(self.local_search_neighborhood)
            if self.random.random() < self.local_search_prob:
                child2.local_search(self.local_search_neighborhood)
            
            # Add to new population
            new_population.append(child1)
            if len(new_population) < self.population_size:
                new_population.append(child2)
        
        self.population = new_population[:self.population_size]
        
        # Update best solution
        for individual in self.population:
            if self.is_better(individual, self.best_solution):
                self.best_solution = individual.copy()
        
        self.current_iteration += 1
    
    def _tournament_selection(self, tournament_size: int = 3) -> Individual:
        """Tournament selection."""
        tournament = self.random.sample(self.population, tournament_size)
        return min(tournament, key=lambda x: x.fitness())
    
    def _crossover(self, parent1: Individual, parent2: Individual) -> tuple:
        """Uniform crossover."""
        child1 = self._create_individual()
        child2 = self._create_individual()
        
        for i in range(len(parent1.position)):
            if self.random.random() < 0.5:
                child1.position[i] = parent1.position[i]
                child2.position[i] = parent2.position[i]
            else:
                child1.position[i] = parent2.position[i]
                child2.position[i] = parent1.position[i]
        
        return child1, child2
    
    def _mutate(self, individual: Individual) -> None:
        """Gaussian mutation."""
        for i in range(len(individual.position)):
            if self.random.random() < self.mutation_rate:
                individual.position[i] += self.random.normal(0, 0.1)
                individual.position[i] = np.clip(individual.position[i], 0, 1)
        individual._fitness = None  # Reset fitness cache