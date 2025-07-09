"""
Sphere function - Simple unimodal benchmark problem.
Global minimum: f(x*) = 0 at x* = [0, 0, ..., 0]
"""

import numpy as np
from problems.continuous.base import ContinuousOptimizationProblem


class SphereProblem(ContinuousOptimizationProblem):
    """
    Sphere function: f(x) = sum(x_i^2)
    
    Properties:
    - Unimodal
    - Convex
    - Separable
    - Global minimum at origin
    """
    
    def __init__(self, dimension: int = 30, bounds: float = 100.0):
        """
        Initialize Sphere problem.
        
        Args:
            dimension: Number of variables
            bounds: Search space bounds [-bounds, bounds]
        """
        super().__init__(
            name=f"Sphere-{dimension}D",
            dimension=dimension,
            lower_bounds=-bounds * np.ones(dimension),
            upper_bounds=bounds * np.ones(dimension),
            optimum_value=0.0,
            optimum_position=np.zeros(dimension)
        )
        
        # Set gradient function
        self._gradient_fn = lambda x: 2 * x
    
    def _evaluate_impl(self, solution: np.ndarray) -> float:
        """
        Evaluate the Sphere function.
        
        Args:
            solution: Input vector
            
        Returns:
            Function value
        """
        return np.sum(solution ** 2)