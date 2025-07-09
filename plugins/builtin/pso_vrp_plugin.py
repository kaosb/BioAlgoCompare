"""
Plugin: name: PSO-VRP
Plugin: version: 1.0
Plugin: author: BioAlgoCompare Team
Plugin: description: Particle Swarm Optimization adapted for VRP
Plugin: problem_types: vrp, optimization
Plugin: dependencies: numpy
"""

import numpy as np
from typing import Optional, List, Dict, Any
from algorithms.base_v2 import MetaheuristicAlgorithm, Individual


class VRPParticle(Individual):
    """Particle for PSO adapted to VRP."""
    
    def __init__(self, problem, position=None):
        super().__init__(problem, position)
        # PSO-specific attributes
        self.velocity = np.zeros_like(self.position)
        self.best_position = self.position.copy()
        self.best_fitness = self.fitness()
        # VRP-specific attributes
        self.route_improvement_rate = 0.0
        self.feasibility_violations = 0
    
    def update_velocity(self, global_best_position: np.ndarray,
                       w: float, c1: float, c2: float, r1: float, r2: float) -> None:
        """Update particle velocity with VRP constraints."""
        # Standard PSO velocity update
        cognitive = c1 * r1 * (self.best_position - self.position)
        social = c2 * r2 * (global_best_position - self.position)
        self.velocity = w * self.velocity + cognitive + social
        
        # Apply velocity clamping for VRP
        max_velocity = 0.3  # Limit velocity for stability
        self.velocity = np.clip(self.velocity, -max_velocity, max_velocity)
    
    def update_position(self) -> None:
        """Update particle position."""
        self.position = self.position + self.velocity
        self.position = np.clip(self.position, 0, 1)
        self._fitness = None  # Reset fitness cache
    
    def repair_solution(self) -> None:
        """Repair infeasible VRP solutions."""
        # Ensure all values are in [0, 1]
        self.position = np.clip(self.position, 0, 1)
        
        # Additional VRP-specific repairs could be added here
        # For example, route balancing or customer reassignment


class ParticleSwarmVRP(MetaheuristicAlgorithm):
    """
    Particle Swarm Optimization adapted for Vehicle Routing Problem.
    
    This implementation includes VRP-specific operators and constraint handling
    to improve solution quality for routing problems.
    """
    
    def __init__(self, problem, population_size: int = 30,
                 max_iterations: int = 100,
                 w: float = 0.9, w_min: float = 0.4,
                 c1: float = 2.0, c2: float = 2.0,
                 local_search_freq: int = 10,
                 repair_prob: float = 0.3,
                 seed: Optional[int] = None):
        """
        Initialize PSO for VRP.
        
        Args:
            problem: VRP problem instance
            population_size: Number of particles
            max_iterations: Maximum iterations
            w: Initial inertia weight
            w_min: Minimum inertia weight
            c1: Cognitive component weight
            c2: Social component weight
            local_search_freq: Frequency of local search (every N iterations)
            repair_prob: Probability of applying solution repair
            seed: Random seed
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        self.w = w
        self.w_min = w_min
        self.c1 = c1
        self.c2 = c2
        self.local_search_freq = local_search_freq
        self.repair_prob = repair_prob
        
        # VRP-specific tracking
        self.feasible_solutions_count = 0
        self.improvement_history = []
        
        # Initialize swarm
        self.initialize_population()
        self._initialize_global_best()
    
    def _create_individual(self) -> Individual:
        """Create a VRP particle."""
        return VRPParticle(self.problem)
    
    def initialize_population(self) -> None:
        """Initialize the particle swarm."""
        self.population = []
        for _ in range(self.population_size):
            particle = self._create_individual()
            self.population.append(particle)
    
    def _initialize_global_best(self) -> None:
        """Initialize global best position."""
        # Find best particle
        best_particle = min(self.population, key=lambda p: p.fitness())
        self.global_best_position = best_particle.position.copy()
        self.global_best_fitness = best_particle.fitness()
        self.best_solution = best_particle.copy()
    
    def iterate(self) -> None:
        """Perform one iteration of PSO-VRP."""
        # Update inertia weight (linear decrease)
        progress = self.current_iteration / self.max_iterations
        self.w = self.w - (self.w - self.w_min) * progress
        
        # Update particles
        for particle in self.population:
            # Generate random values
            r1 = self.random.random()
            r2 = self.random.random()
            
            # Update velocity and position
            particle.update_velocity(
                self.global_best_position,
                self.w, self.c1, self.c2, r1, r2
            )
            particle.update_position()
            
            # Apply repair with probability
            if self.random.random() < self.repair_prob:
                particle.repair_solution()
            
            # Update personal best
            current_fitness = particle.fitness()
            if current_fitness < particle.best_fitness:
                particle.best_position = particle.position.copy()
                particle.best_fitness = current_fitness
                
                # Update global best
                if current_fitness < self.global_best_fitness:
                    self.global_best_position = particle.position.copy()
                    self.global_best_fitness = current_fitness
                    self.best_solution = particle.copy()
        
        # Apply local search periodically
        if (self.current_iteration + 1) % self.local_search_freq == 0:
            self._apply_local_search()
        
        # Track improvement
        self.improvement_history.append(self.global_best_fitness)
        
        # Count feasible solutions
        self.feasible_solutions_count = sum(
            1 for p in self.population 
            if not hasattr(p, '_is_infeasible') or not p._is_infeasible
        )
        
        self.current_iteration += 1
    
    def _apply_local_search(self) -> None:
        """Apply local search to best particles."""
        # Select top particles for local search
        sorted_particles = sorted(self.population, key=lambda p: p.fitness())
        n_elite = max(1, int(0.1 * self.population_size))
        
        for particle in sorted_particles[:n_elite]:
            improved_position = self._vrp_local_search(particle.position)
            
            # Create temporary particle to evaluate
            temp_particle = self._create_individual()
            temp_particle.position = improved_position
            
            if temp_particle.fitness() < particle.fitness():
                particle.position = improved_position
                particle._fitness = None  # Reset fitness cache
                
                # Update personal best if improved
                if particle.fitness() < particle.best_fitness:
                    particle.best_position = particle.position.copy()
                    particle.best_fitness = particle.fitness()
                    
                    # Update global best if improved
                    if particle.fitness() < self.global_best_fitness:
                        self.global_best_position = particle.position.copy()
                        self.global_best_fitness = particle.fitness()
                        self.best_solution = particle.copy()
    
    def _vrp_local_search(self, position: np.ndarray) -> np.ndarray:
        """
        VRP-specific local search operators.
        
        Args:
            position: Current position
            
        Returns:
            Improved position
        """
        improved = position.copy()
        
        # Try different local search operators
        operators = [
            self._swap_operator,
            self._insert_operator,
            self._reverse_operator
        ]
        
        for operator in operators:
            candidate = operator(improved)
            
            # Create temporary particle to evaluate
            temp_particle = self._create_individual()
            temp_particle.position = candidate
            
            current_particle = self._create_individual()
            current_particle.position = improved
            
            if temp_particle.fitness() < current_particle.fitness():
                improved = candidate
        
        return improved
    
    def _swap_operator(self, position: np.ndarray) -> np.ndarray:
        """Swap two random positions."""
        result = position.copy()
        i, j = self.random.sample(range(len(position)), 2)
        result[i], result[j] = result[j], result[i]
        return result
    
    def _insert_operator(self, position: np.ndarray) -> np.ndarray:
        """Remove and insert at different position."""
        result = position.copy()
        n = len(position)
        i = self.random.randint(0, n - 1)
        j = self.random.randint(0, n - 1)
        
        if i != j:
            value = result[i]
            result = np.delete(result, i)
            result = np.insert(result, j, value)
        
        return result
    
    def _reverse_operator(self, position: np.ndarray) -> np.ndarray:
        """Reverse a subsequence."""
        result = position.copy()
        n = len(position)
        i = self.random.randint(0, n - 2)
        j = self.random.randint(i + 1, n - 1)
        result[i:j+1] = result[i:j+1][::-1]
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get algorithm statistics."""
        stats = {
            'current_iteration': self.current_iteration,
            'global_best_fitness': self.global_best_fitness,
            'inertia_weight': self.w,
            'feasible_solutions': self.feasible_solutions_count,
            'population_size': self.population_size
        }
        
        if self.improvement_history:
            stats['improvement_rate'] = (
                self.improvement_history[0] - self.improvement_history[-1]
            ) / self.improvement_history[0]
        
        return stats