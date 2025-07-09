"""
Optimization problems module.
Contains various optimization problem implementations.
"""

from .vrp_v2 import VRPProblemV2

# New problem hierarchy
from .base import (
    AbstractProblem,
    ContinuousProblem,
    LegacyAbstractProblem
)

# Continuous problems
from .continuous.base import ContinuousOptimizationProblem
from .continuous.unconstrained import (
    SphereProblem,
    RastriginProblem,
    AckleyProblem,
    RosenbrockProblem,
    GriewankProblem,
    SchwefelProblem
)

# Discrete problems
from .discrete.base import (
    DiscreteOptimizationProblem,
    PermutationProblem
)
from .discrete.routing.tsp import TSPProblem

from .main_adapters import ContinuousAdapter, DiscreteAdapter, ConstraintHandler, MultiObjectiveAdapter
from .adapters.discrete_problem_adapter import DiscreteProblemAdapter

__all__ = [
    'VRPProblemV2',
    
    # Base classes
    'AbstractProblem',
    'ContinuousProblem',
    'LegacyAbstractProblem',
    
    # Continuous
    'ContinuousOptimizationProblem',
    'SphereProblem',
    'RastriginProblem',
    'AckleyProblem',
    'RosenbrockProblem',
    'GriewankProblem',
    'SchwefelProblem',
    
    # Discrete
    'DiscreteOptimizationProblem',
    'PermutationProblem',
    'TSPProblem',
    
    # Adapters
    'ContinuousAdapter',
    'DiscreteAdapter',
    'ConstraintHandler',
    'MultiObjectiveAdapter'
]