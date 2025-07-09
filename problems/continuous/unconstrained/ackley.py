"""
Ackley function - Multimodal benchmark with exponential terms.
Global minimum: f(x*) = 0 at x* = [0, 0, ..., 0]
"""

import numpy as np
from problems.continuous.base import ContinuousOptimizationProblem


class AckleyProblem(ContinuousOptimizationProblem):
    """
    Ackley function - Multimodal with a nearly flat outer region.
    
    Properties:
    - Multimodal with many local minima
    - Nearly flat outer region
    - Global minimum at origin
    """
    
    def __init__(self, dimension: int = 30, bounds: float = 32.768):
        """
        Initialize Ackley problem.
        
        Args:
            dimension: Number of variables
            bounds: Search space bounds [-bounds, bounds]
        """
        super().__init__(
            name=f"Ackley-{dimension}D",
            dimension=dimension,
            lower_bounds=-bounds * np.ones(dimension),
            upper_bounds=bounds * np.ones(dimension),
            optimum_value=0.0,
            optimum_position=np.zeros(dimension)
        )
        
        # Ackley parameters
        self.a = 20.0
        self.b = 0.2
        self.c = 2 * np.pi
    
    def _evaluate_impl(self, solution: np.ndarray) -> float:
        """
        Evaluate the Ackley function.
        
        Args:
            solution: Input vector
            
        Returns:
            Function value
        """
        n = len(solution)
        sum1 = np.sum(solution**2)
        sum2 = np.sum(np.cos(self.c * solution))
        
        term1 = -self.a * np.exp(-self.b * np.sqrt(sum1 / n))
        term2 = -np.exp(sum2 / n)
        
        return term1 + term2 + self.a + np.e