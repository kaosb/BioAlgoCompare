"""
Rosenbrock function - Classic benchmark with a narrow valley.
Global minimum: f(x*) = 0 at x* = [1, 1, ..., 1]
"""

import numpy as np
from problems.continuous.base import ContinuousOptimizationProblem


class RosenbrockProblem(ContinuousOptimizationProblem):
    """
    Rosenbrock function (Banana function).
    
    Properties:
    - Unimodal
    - Non-convex
    - Narrow, parabolic valley
    - Global minimum at [1, 1, ..., 1]
    """
    
    def __init__(self, dimension: int = 30, bounds: float = 30.0):
        """
        Initialize Rosenbrock problem.
        
        Args:
            dimension: Number of variables
            bounds: Search space bounds [-bounds, bounds]
        """
        super().__init__(
            name=f"Rosenbrock-{dimension}D",
            dimension=dimension,
            lower_bounds=-bounds * np.ones(dimension),
            upper_bounds=bounds * np.ones(dimension),
            optimum_value=0.0,
            optimum_position=np.ones(dimension)
        )
    
    def _evaluate_impl(self, solution: np.ndarray) -> float:
        """
        Evaluate the Rosenbrock function.
        
        Args:
            solution: Input vector
            
        Returns:
            Function value
        """
        n = len(solution)
        total = 0.0
        
        for i in range(n - 1):
            term1 = 100 * (solution[i+1] - solution[i]**2)**2
            term2 = (1 - solution[i])**2
            total += term1 + term2
            
        return total