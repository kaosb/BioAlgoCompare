"""
Adapter for discrete optimization problems to expose a continuous interface.
"""

import numpy as np
from typing import Any, List, Tuple

from problems.base import AbstractProblem, ContinuousProblem
from problems.vrp_v2 import VRPProblemV2


class DiscreteProblemAdapter(ContinuousProblem):
    """
    Adapts a discrete problem (like VRPProblemV2) to a continuous interface.
    
    This allows algorithms designed for continuous optimization to work with
    discrete problems by handling the encoding and decoding of solutions.
    """
    
    def __init__(self, discrete_problem: VRPProblemV2):
        """
        Initializes the adapter.
        
        Args:
            discrete_problem: The discrete problem instance to adapt.
        """
        if not isinstance(discrete_problem, VRPProblemV2):
            raise TypeError("DiscreteProblemAdapter currently only supports VRPProblemV2.")
            
        super().__init__(
            name=f"Adapted-{discrete_problem.name}",
            dimension=discrete_problem.dimension # This is the number of customers
        )
        self.discrete_problem = discrete_problem
        
        # Store bounds for continuous encoding [0,1]
        self._lower_bounds = np.zeros(discrete_problem.dimension)
        self._upper_bounds = np.ones(discrete_problem.dimension)
    
    @property
    def lower_bounds(self) -> np.ndarray:
        """Get the lower bounds for continuous encoding."""
        return self._lower_bounds
    
    @property  
    def upper_bounds(self) -> np.ndarray:
        """Get the upper bounds for continuous encoding."""
        return self._upper_bounds
        
    def _evaluate_impl(self, solution: np.ndarray) -> float:
        """
        Evaluates a continuous solution by converting it to the discrete
        representation and then evaluating it with the wrapped discrete problem.
        """
        discrete_solution = self.discrete_problem.encode_continuous(solution)
        return self.discrete_problem.evaluate(discrete_solution)

    def is_feasible(self, solution: np.ndarray) -> bool:
        """
        Checks feasibility of a continuous solution.
        """
        # For random-keys encoding, any continuous solution in [0,1] is feasible
        # in terms of permutation, but the resulting routes might not be capacity-feasible.
        # We rely on the discrete problem's evaluate method to handle penalties.
        return np.all(solution >= self.lower_bounds) and np.all(solution <= self.upper_bounds)

    def random_solution(self) -> np.ndarray:
        """
        Generates a random continuous solution.
        """
        return np.random.uniform(self.lower_bounds, self.upper_bounds, self.dimension)

    def repair(self, solution: np.ndarray) -> np.ndarray:
        """
        Repairs a continuous solution by clipping to bounds.
        """
        return np.clip(solution, self.lower_bounds, self.upper_bounds)
