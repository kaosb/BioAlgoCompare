"""
Rastrigin function - Highly multimodal benchmark problem.
Global minimum: f(x*) = 0 at x* = [0, 0, ..., 0]
"""

import numpy as np
from problems.continuous.base import ContinuousOptimizationProblem


class RastriginProblem(ContinuousOptimizationProblem):
    """
    Rastrigin function: f(x) = 10n + sum(x_i^2 - 10*cos(2*pi*x_i))
    
    Properties:
    - Highly multimodal (many local minima)
    - Regular distribution of local minima
    - Global minimum at origin
    """
    
    def __init__(self, dimension: int = 30, bounds: float = 5.12):
        """
        Initialize Rastrigin problem.
        
        Args:
            dimension: Number of variables
            bounds: Search space bounds [-bounds, bounds]
        """
        super().__init__(
            name=f"Rastrigin-{dimension}D",
            dimension=dimension,
            lower_bounds=-bounds * np.ones(dimension),
            upper_bounds=bounds * np.ones(dimension),
            optimum_value=0.0,
            optimum_position=np.zeros(dimension)
        )
    
    def _evaluate_impl(self, solution: np.ndarray) -> float:
        """
        Evaluate the Rastrigin function.
        
        Args:
            solution: Input vector
            
        Returns:
            Function value
        """
        n = len(solution)
        A = 10.0
        return A * n + np.sum(solution**2 - A * np.cos(2 * np.pi * solution))