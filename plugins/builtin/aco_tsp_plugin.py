"""
Plugin: name: ACO-TSP
Plugin: version: 1.0
Plugin: author: BioAlgoCompare Team
Plugin: description: Ant Colony Optimization for TSP/VRP problems
Plugin: problem_types: tsp, vrp, optimization
Plugin: dependencies: numpy
"""

import numpy as np
from typing import Optional, List, Tuple, Dict, Any
from algorithms.base_v2 import MetaheuristicAlgorithm, Individual


class AntIndividual(Individual):
    """Ant for ACO algorithm."""
    
    def __init__(self, problem, position=None):
        super().__init__(problem, position)
        self.tour = []
        self.tour_length = float('inf')
        self.visited = set()
    
    def construct_tour(self, pheromones: np.ndarray, alpha: float, 
                      beta: float, random_func) -> None:
        """Construct a tour using pheromone trails."""
        n_customers = len(self.position)
        
        # Start from depot (if VRP) or random city (if TSP)
        current = 0
        self.tour = [current]
        self.visited = {current}
        
        # Build tour
        while len(self.tour) < n_customers:
            next_city = self._select_next_city(
                current, pheromones, alpha, beta, random_func
            )
            self.tour.append(next_city)
            self.visited.add(next_city)
            current = next_city
        
        # Convert tour to position encoding
        self._tour_to_position()
    
    def _select_next_city(self, current: int, pheromones: np.ndarray,
                         alpha: float, beta: float, random_func) -> int:
        """Select next city based on pheromone and heuristic information."""
        unvisited = [i for i in range(len(self.position)) if i not in self.visited]
        
        if not unvisited:
            return 0  # Return to start
        
        # Calculate probabilities
        probabilities = []
        for city in unvisited:
            # Pheromone level
            tau = pheromones[current, city] ** alpha
            
            # Heuristic information (inverse of distance)
            if hasattr(self.problem, 'distance_matrix'):
                distance = self.problem.distance_matrix[current, city]
                eta = (1.0 / distance) ** beta if distance > 0 else 1.0
            else:
                eta = 1.0
            
            probabilities.append(tau * eta)
        
        # Normalize probabilities
        total = sum(probabilities)
        if total > 0:
            probabilities = [p / total for p in probabilities]
        else:
            probabilities = [1.0 / len(unvisited)] * len(unvisited)
        
        # Select next city
        return random_func.choices(unvisited, weights=probabilities)[0]
    
    def _tour_to_position(self) -> None:
        """Convert tour representation to position encoding."""
        # Create a mapping from tour order to continuous values
        n = len(self.tour)
        for i, city in enumerate(self.tour):
            if city < len(self.position):
                self.position[city] = i / (n - 1) if n > 1 else 0.5
    
    def calculate_tour_length(self) -> float:
        """Calculate total tour length."""
        if not hasattr(self.problem, 'distance_matrix'):
            return self.fitness()
        
        total_distance = 0
        for i in range(len(self.tour)):
            from_city = self.tour[i]
            to_city = self.tour[(i + 1) % len(self.tour)]
            total_distance += self.problem.distance_matrix[from_city, to_city]
        
        self.tour_length = total_distance
        return total_distance


class AntColonyOptimization(MetaheuristicAlgorithm):
    """
    Ant Colony Optimization for routing problems.
    
    This implementation is optimized for TSP and VRP problems with
    pheromone-based path construction and various pheromone update strategies.
    """
    
    def __init__(self, problem, population_size: int = 30,
                 max_iterations: int = 100,
                 alpha: float = 1.0, beta: float = 2.0,
                 rho: float = 0.1, tau0: float = 0.1,
                 elite_ants: int = 5,
                 q0: float = 0.9,
                 local_search: bool = True,
                 seed: Optional[int] = None):
        """
        Initialize ACO algorithm.
        
        Args:
            problem: Problem instance (TSP or VRP)
            population_size: Number of ants
            max_iterations: Maximum iterations
            alpha: Pheromone importance
            beta: Heuristic importance
            rho: Pheromone evaporation rate
            tau0: Initial pheromone level
            elite_ants: Number of elite ants for pheromone update
            q0: Exploitation vs exploration parameter
            local_search: Whether to apply local search
            seed: Random seed
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.tau0 = tau0
        self.elite_ants = elite_ants
        self.q0 = q0
        self.local_search = local_search
        
        # Initialize pheromone matrix
        self._init_pheromones()
        
        # Best tour tracking
        self.best_tour = None
        self.best_tour_length = float('inf')
        
        # Statistics
        self.convergence_count = 0
        self.diversity_history = []
        
        # Initialize colony
        self.initialize_population()
    
    def _init_pheromones(self) -> None:
        """Initialize pheromone matrix."""
        # Determine problem size
        if hasattr(self.problem, 'dimension'):
            n = self.problem.dimension
        elif hasattr(self.problem, 'distance_matrix'):
            n = len(self.problem.distance_matrix)
        else:
            n = 10  # Default size
        
        self.pheromones = np.full((n, n), self.tau0)
    
    def _create_individual(self) -> Individual:
        """Create an ant."""
        return AntIndividual(self.problem)
    
    def initialize_population(self) -> None:
        """Initialize ant colony."""
        self.population = []
        for _ in range(self.population_size):
            ant = self._create_individual()
            self.population.append(ant)
    
    def iterate(self) -> None:
        """Perform one iteration of ACO."""
        # Construct tours for all ants
        for ant in self.population:
            ant.construct_tour(self.pheromones, self.alpha, self.beta, self.random)
            ant.calculate_tour_length()
            
            # Apply local search if enabled
            if self.local_search:
                self._apply_2opt(ant)
        
        # Sort ants by tour length
        self.population.sort(key=lambda a: a.tour_length)
        
        # Update best solution
        if self.population[0].tour_length < self.best_tour_length:
            self.best_tour_length = self.population[0].tour_length
            self.best_tour = self.population[0].tour.copy()
            self.best_solution = self.population[0].copy()
            self.convergence_count = 0
        else:
            self.convergence_count += 1
        
        # Update pheromones
        self._update_pheromones()
        
        # Track diversity
        self._track_diversity()
        
        self.current_iteration += 1
    
    def _update_pheromones(self) -> None:
        """Update pheromone trails."""
        # Evaporation
        self.pheromones *= (1 - self.rho)
        
        # Add pheromone from elite ants
        n_elite = min(self.elite_ants, len(self.population))
        for ant in self.population[:n_elite]:
            delta = 1.0 / ant.tour_length
            
            for i in range(len(ant.tour)):
                from_city = ant.tour[i]
                to_city = ant.tour[(i + 1) % len(ant.tour)]
                self.pheromones[from_city, to_city] += delta
                self.pheromones[to_city, from_city] += delta
        
        # Ensure minimum pheromone level
        self.pheromones = np.maximum(self.pheromones, self.tau0 / 100)
    
    def _apply_2opt(self, ant: AntIndividual) -> None:
        """Apply 2-opt local search to improve tour."""
        if not hasattr(self.problem, 'distance_matrix'):
            return
        
        improved = True
        tour = ant.tour.copy()
        
        while improved:
            improved = False
            
            for i in range(1, len(tour) - 2):
                for j in range(i + 1, len(tour)):
                    if j - i == 1:
                        continue
                    
                    # Current edges
                    current_dist = (
                        self.problem.distance_matrix[tour[i-1], tour[i]] +
                        self.problem.distance_matrix[tour[j-1], tour[j]]
                    )
                    
                    # New edges after 2-opt
                    new_dist = (
                        self.problem.distance_matrix[tour[i-1], tour[j-1]] +
                        self.problem.distance_matrix[tour[i], tour[j]]
                    )
                    
                    # If improvement found
                    if new_dist < current_dist:
                        # Reverse tour segment
                        tour[i:j] = tour[i:j][::-1]
                        improved = True
                        break
                
                if improved:
                    break
        
        # Update ant with improved tour
        ant.tour = tour
        ant.calculate_tour_length()
        ant._tour_to_position()
    
    def _track_diversity(self) -> None:
        """Track population diversity."""
        # Calculate average pairwise distance between tours
        total_distance = 0
        count = 0
        
        for i in range(len(self.population)):
            for j in range(i + 1, len(self.population)):
                distance = self._tour_distance(
                    self.population[i].tour,
                    self.population[j].tour
                )
                total_distance += distance
                count += 1
        
        avg_diversity = total_distance / count if count > 0 else 0
        self.diversity_history.append(avg_diversity)
    
    def _tour_distance(self, tour1: List[int], tour2: List[int]) -> float:
        """Calculate distance between two tours."""
        # Simple Hamming distance
        distance = 0
        for i in range(min(len(tour1), len(tour2))):
            if tour1[i] != tour2[i]:
                distance += 1
        return distance / len(tour1)
    
    def get_best_tour(self) -> Optional[List[int]]:
        """Get the best tour found."""
        return self.best_tour
    
    def get_stats(self) -> Dict[str, Any]:
        """Get algorithm statistics."""
        stats = {
            'current_iteration': self.current_iteration,
            'best_tour_length': self.best_tour_length,
            'convergence_count': self.convergence_count,
            'pheromone_mean': np.mean(self.pheromones),
            'pheromone_std': np.std(self.pheromones)
        }
        
        if self.diversity_history:
            stats['current_diversity'] = self.diversity_history[-1]
            stats['diversity_trend'] = (
                self.diversity_history[-1] - self.diversity_history[0]
            ) if len(self.diversity_history) > 1 else 0
        
        return stats