"""
Optimization problems module.
Contains various optimization problem implementations.
"""

# Legacy imports for backward compatibility
from .vrp import VRPProblem

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

# Adapters
from .adapters import (
    ContinuousAdapter,
    DiscreteAdapter,
    ConstraintHandler,
    MultiObjectiveAdapter
)

__all__ = [
    # Legacy
    'VRPProblem',
    
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