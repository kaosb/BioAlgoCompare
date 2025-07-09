"""
Schwefel function - Deceptive multimodal problem.
Global minimum: f(x*) = 0 at x* = [420.9687, 420.9687, ..., 420.9687]
"""

import numpy as np
from problems.continuous.base import ContinuousOptimizationProblem


class SchwefelProblem(ContinuousOptimizationProblem):
    """
    Schwefel function.
    
    Properties:
    - Highly multimodal
    - Deceptive (global minimum far from origin)
    - Many local minima
    - Global minimum at x_i = 420.9687
    """
    
    def __init__(self, dimension: int = 30):
        """
        Initialize Schwefel problem.
        
        Args:
            dimension: Number of variables
        """
        self.optimal_value = 420.9687
        super().__init__(
            name=f"Schwefel-{dimension}D",
            dimension=dimension,
            lower_bounds=-500.0 * np.ones(dimension),
            upper_bounds=500.0 * np.ones(dimension),
            optimum_value=0.0,
            optimum_position=self.optimal_value * np.ones(dimension)
        )
    
    def _evaluate_impl(self, solution: np.ndarray) -> float:
        """
        Evaluate the Schwefel function.
        
        Args:
            solution: Input vector
            
        Returns:
            Function value
        """
        n = len(solution)
        
        # Original Schwefel function
        sum_term = np.sum(solution * np.sin(np.sqrt(np.abs(solution))))
        
        # Shifted to have minimum at 0
        return 418.9829 * n - sum_term