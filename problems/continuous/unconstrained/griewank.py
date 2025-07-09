"""
Griewank function - Multimodal with product term.
Global minimum: f(x*) = 0 at x* = [0, 0, ..., 0]
"""

import numpy as np
from problems.continuous.base import ContinuousOptimizationProblem


class GriewankProblem(ContinuousOptimizationProblem):
    """
    Griewank function.
    
    Properties:
    - Multimodal
    - Regular distribution of local minima
    - Product term creates interdependence
    - Global minimum at origin
    """
    
    def __init__(self, dimension: int = 30, bounds: float = 600.0):
        """
        Initialize Griewank problem.
        
        Args:
            dimension: Number of variables
            bounds: Search space bounds [-bounds, bounds]
        """
        super().__init__(
            name=f"Griewank-{dimension}D",
            dimension=dimension,
            lower_bounds=-bounds * np.ones(dimension),
            upper_bounds=bounds * np.ones(dimension),
            optimum_value=0.0,
            optimum_position=np.zeros(dimension)
        )
    
    def _evaluate_impl(self, solution: np.ndarray) -> float:
        """
        Evaluate the Griewank function.
        
        Args:
            solution: Input vector
            
        Returns:
            Function value
        """
        n = len(solution)
        
        # Sum term
        sum_term = np.sum(solution**2) / 4000.0
        
        # Product term
        prod_term = 1.0
        for i in range(n):
            prod_term *= np.cos(solution[i] / np.sqrt(i + 1))
        
        return sum_term - prod_term + 1.0