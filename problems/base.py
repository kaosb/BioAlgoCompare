"""
Base classes for all optimization problems.
Provides a generic interface that supports both continuous and discrete problems.
"""

from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic, Optional, Union
import numpy as np

# Type variable for solution representation
T = TypeVar('T')


class AbstractProblem(ABC, Generic[T]):
    """
    Generic base class for all optimization problems.
    
    This class is generic over the solution type T, which allows
    different problem types to use their natural representations
    (e.g., np.ndarray for continuous, List[int] for discrete).
    """
    
    def __init__(self, name: str):
        """
        Initialize the problem.
        
        Args:
            name: Name of the problem instance
        """
        self.name = name
        self._best_known: Optional[float] = None
        self._evaluations: int = 0
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        Get the dimension of the problem.
        
        Returns:
            The problem dimension
        """
        pass
    
    @abstractmethod
    def evaluate(self, solution: T) -> float:
        """
        Evaluate a solution and return its fitness value.
        
        Args:
            solution: The solution to evaluate
            
        Returns:
            The fitness value (lower is better)
        """
        pass
    
    @abstractmethod
    def is_feasible(self, solution: T) -> bool:
        """
        Check if a solution is feasible.
        
        Args:
            solution: The solution to check
            
        Returns:
            True if the solution is feasible
        """
        pass
    
    @abstractmethod
    def random_solution(self) -> T:
        """
        Generate a random feasible solution.
        
        Returns:
            A random solution of type T
        """
        pass
    
    @property
    def best_known_value(self) -> Optional[float]:
        """
        Get the best known value for this problem (if available).
        
        Returns:
            Best known value or None if not available
        """
        return self._best_known
    
    @property
    def evaluations(self) -> int:
        """
        Get the number of evaluations performed.
        
        Returns:
            Number of evaluations
        """
        return self._evaluations
    
    def reset_evaluations(self) -> None:
        """Reset the evaluation counter."""
        self._evaluations = 0
    
    def __str__(self) -> str:
        """String representation of the problem."""
        return f"{self.__class__.__name__}(name='{self.name}', dimension={self.dimension})"


class ContinuousProblem(AbstractProblem[np.ndarray]):
    """
    Base class for continuous optimization problems.
    
    This class provides the interface for problems with continuous
    variables, where solutions are represented as numpy arrays.
    """
    
    def __init__(self, name: str, dimension: int):
        """
        Initialize a continuous problem.
        
        Args:
            name: Name of the problem instance
            dimension: Number of decision variables
        """
        super().__init__(name)
        self._dimension = dimension
    
    @property
    def dimension(self) -> int:
        """Get the dimension of the problem."""
        return self._dimension
    
    def get_dimension(self) -> int:
        """Legacy method for getting dimension."""
        return self.dimension
    
    @property
    @abstractmethod
    def lower_bounds(self) -> np.ndarray:
        """
        Get the lower bounds for each dimension.
        
        Returns:
            Array of lower bounds
        """
        pass
    
    @property
    @abstractmethod
    def upper_bounds(self) -> np.ndarray:
        """
        Get the upper bounds for each dimension.
        
        Returns:
            Array of upper bounds
        """
        pass
    
    def get_lower_bounds(self) -> np.ndarray:
        """Legacy method for getting lower bounds."""
        return self.lower_bounds
    
    def get_upper_bounds(self) -> np.ndarray:
        """Legacy method for getting upper bounds."""
        return self.upper_bounds
    
    def is_feasible(self, solution: np.ndarray) -> bool:
        """
        Check if a solution is feasible (within bounds).
        
        Args:
            solution: The solution to check
            
        Returns:
            True if the solution is feasible
        """
        if len(solution) != self.dimension:
            return False
        
        return np.all(solution >= self.lower_bounds) and \
               np.all(solution <= self.upper_bounds)
    
    def repair(self, solution: np.ndarray) -> np.ndarray:
        """
        Repair an infeasible solution by clipping to bounds.
        
        Args:
            solution: The solution to repair
            
        Returns:
            The repaired solution
        """
        return np.clip(solution, self.lower_bounds, self.upper_bounds)
    
    def random_solution(self) -> np.ndarray:
        """
        Generate a random solution within bounds.
        
        Returns:
            Random solution array
        """
        return np.random.uniform(
            self.lower_bounds,
            self.upper_bounds,
            size=self.dimension
        )
    
    def evaluate(self, solution: np.ndarray) -> float:
        """
        Evaluate a solution (to be implemented by subclasses).
        
        Args:
            solution: The solution to evaluate
            
        Returns:
            The fitness value
        """
        self._evaluations += 1
        return self._evaluate_impl(solution)
    
    @abstractmethod
    def _evaluate_impl(self, solution: np.ndarray) -> float:
        """
        Internal evaluation method to be implemented by subclasses.
        
        Args:
            solution: The solution to evaluate
            
        Returns:
            The fitness value
        """
        pass


# Legacy compatibility
class LegacyAbstractProblem(ContinuousProblem):
    """
    Legacy AbstractProblem for backward compatibility.
    
    This class maintains the old interface while using the new
    problem hierarchy internally.
    """
    
    def __init__(self, name: str):
        """Initialize with just a name (dimension set later)."""
        # Don't call super().__init__ yet, wait for dimension
        self.name = name
        self._best_known = None
        self._evaluations = 0
        self._dimension = None
        self._lower_bounds = None
        self._upper_bounds = None
    
    def get_dimension(self) -> int:
        """Legacy method for getting dimension."""
        return self.dimension
    
    def get_lower_bounds(self) -> np.ndarray:
        """Legacy method for getting lower bounds."""
        return self.lower_bounds
    
    def get_upper_bounds(self) -> np.ndarray:
        """Legacy method for getting upper bounds."""
        return self.upper_bounds