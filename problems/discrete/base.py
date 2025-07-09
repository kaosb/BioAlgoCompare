"""
Base class for discrete optimization problems.
Provides encoding/decoding between continuous and discrete representations.
"""

import numpy as np
from abc import abstractmethod
from typing import List, Tuple, Any, Optional
from problems.base import AbstractProblem


class DiscreteOptimizationProblem(AbstractProblem[List[int]]):
    """
    Base class for discrete optimization problems.
    
    Provides methods to convert between continuous representations
    (used by metaheuristics) and discrete representations (natural
    for the problem).
    """
    
    def __init__(self, name: str, dimension: int):
        """
        Initialize a discrete problem.
        
        Args:
            name: Problem name
            dimension: Problem dimension (for continuous encoding)
        """
        super().__init__(name)
        self._dimension = dimension
    
    @property
    def dimension(self) -> int:
        """Get the dimension for continuous encoding."""
        return self._dimension
    
    @abstractmethod
    def encode_continuous(self, continuous: np.ndarray) -> List[int]:
        """
        Convert continuous representation to discrete.
        
        Args:
            continuous: Continuous solution vector
            
        Returns:
            Discrete solution
        """
        pass
    
    @abstractmethod
    def decode_to_continuous(self, discrete: List[int]) -> np.ndarray:
        """
        Convert discrete representation to continuous.
        
        Args:
            discrete: Discrete solution
            
        Returns:
            Continuous solution vector
        """
        pass
    
    @property
    @abstractmethod
    def search_space_size(self) -> int:
        """
        Get the size of the discrete search space.
        
        Returns:
            Number of possible discrete solutions
        """
        pass
    
    def evaluate_continuous(self, continuous: np.ndarray) -> float:
        """
        Evaluate a continuous solution by converting to discrete.
        
        Args:
            continuous: Continuous solution
            
        Returns:
            Fitness value
        """
        discrete = self.encode_continuous(continuous)
        return self.evaluate(discrete)
    
    def is_feasible_continuous(self, continuous: np.ndarray) -> bool:
        """
        Check feasibility of continuous solution.
        
        Args:
            continuous: Continuous solution
            
        Returns:
            True if feasible
        """
        if len(continuous) != self.dimension:
            return False
        
        # Check bounds [0, 1]
        if not np.all((continuous >= 0) & (continuous <= 1)):
            return False
            
        # Check discrete feasibility
        discrete = self.encode_continuous(continuous)
        return self.is_feasible(discrete)
    
    def random_continuous(self) -> np.ndarray:
        """
        Generate random continuous solution.
        
        Returns:
            Random continuous vector
        """
        discrete = self.random_solution()
        return self.decode_to_continuous(discrete)


class PermutationProblem(DiscreteOptimizationProblem):
    """
    Base class for permutation-based problems (TSP, scheduling, etc.).
    
    Solutions are permutations of integers [0, 1, ..., n-1].
    """
    
    def __init__(self, name: str, n_elements: int):
        """
        Initialize a permutation problem.
        
        Args:
            name: Problem name
            n_elements: Number of elements to permute
        """
        super().__init__(name, n_elements)
        self.n_elements = n_elements
    
    @property
    def search_space_size(self) -> int:
        """Get factorial search space size."""
        import math
        return math.factorial(self.n_elements)
    
    def encode_continuous(self, continuous: np.ndarray) -> List[int]:
        """
        Convert continuous to permutation using random keys.
        
        Args:
            continuous: Continuous vector in [0, 1]^n
            
        Returns:
            Permutation as list of integers
        """
        # Random keys encoding: sort indices by continuous values
        indices = np.argsort(continuous)
        return indices.tolist()
    
    def decode_to_continuous(self, permutation: List[int]) -> np.ndarray:
        """
        Convert permutation to continuous representation.
        
        Args:
            permutation: Permutation as list
            
        Returns:
            Continuous vector
        """
        n = len(permutation)
        continuous = np.zeros(n)
        
        # Assign values based on position in permutation
        for i, elem in enumerate(permutation):
            continuous[elem] = (i + 0.5) / n
            
        return continuous
    
    def is_feasible(self, solution: List[int]) -> bool:
        """
        Check if solution is a valid permutation.
        
        Args:
            solution: Solution to check
            
        Returns:
            True if valid permutation
        """
        if len(solution) != self.n_elements:
            return False
            
        # Check if all elements are present exactly once
        return set(solution) == set(range(self.n_elements))
    
    def random_solution(self) -> List[int]:
        """
        Generate random permutation.
        
        Returns:
            Random permutation
        """
        return np.random.permutation(self.n_elements).tolist()
    
    def swap_mutation(self, permutation: List[int]) -> List[int]:
        """
        Apply swap mutation to permutation.
        
        Args:
            permutation: Original permutation
            
        Returns:
            Mutated permutation
        """
        perm_copy = permutation.copy()
        i, j = np.random.choice(self.n_elements, 2, replace=False)
        perm_copy[i], perm_copy[j] = perm_copy[j], perm_copy[i]
        return perm_copy
    
    def insert_mutation(self, permutation: List[int]) -> List[int]:
        """
        Apply insert mutation to permutation.
        
        Args:
            permutation: Original permutation
            
        Returns:
            Mutated permutation
        """
        perm_copy = permutation.copy()
        i = np.random.randint(self.n_elements)
        j = np.random.randint(self.n_elements)
        
        if i != j:
            elem = perm_copy.pop(i)
            perm_copy.insert(j, elem)
            
        return perm_copy