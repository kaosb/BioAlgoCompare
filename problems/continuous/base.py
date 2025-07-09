"""
Base class for continuous optimization problems.
Extends the generic ContinuousProblem with additional features.
"""

import numpy as np
from typing import Optional, Callable
from problems.base import ContinuousProblem


class ContinuousOptimizationProblem(ContinuousProblem):
    """
    Enhanced base class for continuous optimization problems.
    
    Provides additional features like constraint handling,
    gradient computation, and problem-specific metadata.
    """
    
    def __init__(
        self,
        name: str,
        dimension: int,
        lower_bounds: Optional[np.ndarray] = None,
        upper_bounds: Optional[np.ndarray] = None,
        optimum_value: Optional[float] = None,
        optimum_position: Optional[np.ndarray] = None
    ):
        """
        Initialize a continuous optimization problem.
        
        Args:
            name: Name of the problem
            dimension: Number of decision variables
            lower_bounds: Lower bounds (default: -100 for all)
            upper_bounds: Upper bounds (default: 100 for all)
            optimum_value: Known global optimum value
            optimum_position: Known global optimum position
        """
        super().__init__(name, dimension)
        
        # Set bounds
        if lower_bounds is None:
            self._lower_bounds = np.full(dimension, -100.0)
        else:
            self._lower_bounds = np.asarray(lower_bounds)
            
        if upper_bounds is None:
            self._upper_bounds = np.full(dimension, 100.0)
        else:
            self._upper_bounds = np.asarray(upper_bounds)
        
        # Set known optimum
        self._best_known = optimum_value
        self._optimum_position = optimum_position
        
        # Optional gradient function
        self._gradient_fn: Optional[Callable] = None
    
    @property
    def lower_bounds(self) -> np.ndarray:
        """Get the lower bounds."""
        return self._lower_bounds
    
    @property
    def upper_bounds(self) -> np.ndarray:
        """Get the upper bounds."""
        return self._upper_bounds
    
    @property
    def optimum_position(self) -> Optional[np.ndarray]:
        """Get the known optimum position if available."""
        return self._optimum_position
    
    def has_gradient(self) -> bool:
        """Check if gradient information is available."""
        return self._gradient_fn is not None
    
    def gradient(self, solution: np.ndarray) -> Optional[np.ndarray]:
        """
        Compute the gradient at a given point.
        
        Args:
            solution: Point at which to compute gradient
            
        Returns:
            Gradient vector or None if not available
        """
        if self._gradient_fn is not None:
            return self._gradient_fn(solution)
        return None
    
    def distance_to_optimum(self, solution: np.ndarray) -> Optional[float]:
        """
        Compute distance to known optimum position.
        
        Args:
            solution: Current solution
            
        Returns:
            Euclidean distance or None if optimum unknown
        """
        if self._optimum_position is not None:
            return np.linalg.norm(solution - self._optimum_position)
        return None
    
    def gap_to_optimum(self, fitness: float) -> Optional[float]:
        """
        Compute gap to known optimum value.
        
        Args:
            fitness: Current fitness value
            
        Returns:
            Gap or None if optimum unknown
        """
        if self._best_known is not None:
            return abs(fitness - self._best_known)
        return None