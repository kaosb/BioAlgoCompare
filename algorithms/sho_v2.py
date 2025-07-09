"""
Spotted Hyena Optimizer (SHO) - Version 2
Migrated to use the improved base architecture.
"""

import numpy as np
from typing import List
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem


class SpottedHyena(Individual):
    """Individual representing a spotted hyena in the SHO algorithm."""
    
    def initialize(self) -> None:
        """Initialize the hyena's position randomly within problem bounds."""
        self.position = self.problem.random_solution()
        self.velocity = np.zeros(self.problem.dimension)
    
    def move(self, context: MoveContext) -> None:
        """
        Move the hyena according to SHO rules.
        
        Args:
            context: MoveContext containing iteration info and algorithm parameters
        """
        # Get algorithm-specific parameters from context
        alpha = context.get_param('alpha')
        beta = context.get_param('beta') 
        delta = context.get_param('delta')
        h = context.get_param('h')
        
        iteration = context.iteration
        max_iterations = context.max_iterations
        
        # Calculate movement vectors
        r1, r2, r3 = np.random.random(3)
        
        # Position updates based on alpha, beta, and delta
        D_alpha = abs(alpha.position - self.position)
        D_beta = abs(beta.position - self.position)
        D_delta = abs(delta.position - self.position)
        
        X1 = alpha.position - r1 * D_alpha
        X2 = beta.position - r2 * D_beta
        X3 = delta.position - r3 * D_delta
        
        # Update position
        self.position = (X1 + X2 + X3) / 3.0
        
        # Apply h factor for encircling behavior
        self.position = self.position * h
        
        # Ensure position stays within bounds
        self.position = self.problem.repair(self.position)


class SHOV2(MetaheuristicAlgorithm[SpottedHyena]):
    """
    Spotted Hyena Optimizer (SHO) - Improved Version
    
    This implementation uses the new architecture with MoveContext
    for better consistency and maintainability.
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        seed: int = None
    ):
        super().__init__(problem, population_size, max_iterations, seed)
        
        # SHO-specific attributes
        self.alpha: SpottedHyena = None  # Best solution
        self.beta: SpottedHyena = None   # Second best
        self.delta: SpottedHyena = None  # Third best
    
    def _create_individual(self) -> SpottedHyena:
        """Create a new spotted hyena individual."""
        return SpottedHyena(self.problem)
    
    def _should_sort_population(self) -> bool:
        """SHO needs sorted population to identify alpha, beta, delta."""
        return True
    
    def initialize_population(self) -> None:
        """Initialize population and identify leaders."""
        super().initialize_population()
        
        # Identify alpha, beta, delta (best three solutions)
        self.alpha = self.population[0].clone()
        self.beta = self.population[1].clone() if self.population_size > 1 else self.alpha.clone()
        self.delta = self.population[2].clone() if self.population_size > 2 else self.beta.clone()
    
    def _create_move_context(self) -> MoveContext:
        """Create context with SHO-specific parameters."""
        # Calculate h factor for encircling behavior
        h = 5 - self.iteration * (5 / self.max_iterations)
        
        context = super()._create_move_context()
        context.set_param('alpha', self.alpha)
        context.set_param('beta', self.beta)
        context.set_param('delta', self.delta)
        context.set_param('h', h)
        
        return context
    
    def update_population(self) -> None:
        """Update population and leaders."""
        super().update_population()
        
        # Update alpha, beta, delta after population update
        if self.population_size >= 1 and self.population[0].is_better_than(self.alpha):
            self.alpha = self.population[0].clone()
        
        if self.population_size >= 2 and self.population[1].is_better_than(self.beta):
            self.beta = self.population[1].clone()
            
        if self.population_size >= 3 and self.population[2].is_better_than(self.delta):
            self.delta = self.population[2].clone()


# Example of how to adapt VRPProblem to new architecture
class VRPProblemAdapter(AbstractProblem):
    """Adapter to make existing VRPProblem compatible with new architecture."""
    
    def __init__(self, vrp_problem):
        """
        Initialize adapter with existing VRPProblem instance.
        
        Args:
            vrp_problem: Instance of the original VRPProblem class
        """
        super().__init__(vrp_problem.name or "VRP")
        self.vrp_problem = vrp_problem
        self._dimension = vrp_problem.dimension - 1  # Exclude depot
        self._lower_bounds = np.zeros(self._dimension)
        self._upper_bounds = np.ones(self._dimension)
    
    @property
    def dimension(self) -> int:
        """Get problem dimension."""
        return self._dimension
    
    @property 
    def lower_bounds(self) -> np.ndarray:
        """Get lower bounds (0 for VRP encoding)."""
        return self._lower_bounds
    
    @property
    def upper_bounds(self) -> np.ndarray:
        """Get upper bounds (1 for VRP encoding)."""
        return self._upper_bounds
    
    def evaluate(self, solution: np.ndarray) -> float:
        """Evaluate VRP solution using original problem."""
        return self.vrp_problem.evaluate(solution)