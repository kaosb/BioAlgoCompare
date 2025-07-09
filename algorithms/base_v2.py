"""
Migration wrapper for algorithms/base_v2.py

⚠️  DEPRECATED: This module is deprecated and will be removed in version 3.0.
Please import from algorithms.core instead:

    from algorithms.core import MetaheuristicAlgorithm, Individual

This wrapper provides backward compatibility while issuing deprecation warnings.
"""

from algorithms.legacy_compatibility import (
    LegacyMetaheuristicAlgorithm as MetaheuristicAlgorithm,
    LegacyIndividual as Individual,
    LegacyProblem as AbstractProblem,
    CoreMoveContext as MoveContext,
    deprecation_warning
)

# Issue deprecation warning
deprecation_warning(
    "algorithms/base_v2.py",
    "algorithms.core",
    version="3.0"
)

# Export expected classes
__all__ = [
    'MetaheuristicAlgorithm',
    'Individual', 
    'AbstractProblem',
    'MoveContext'
]
