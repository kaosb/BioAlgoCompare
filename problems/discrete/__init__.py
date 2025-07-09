"""
Discrete optimization problems.
"""

from .base import DiscreteOptimizationProblem, PermutationProblem
from .routing.tsp import TSPProblem

__all__ = ['DiscreteOptimizationProblem', 'PermutationProblem', 'TSPProblem']