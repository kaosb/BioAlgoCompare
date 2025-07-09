"""
Reproducibility module for BioAlgoCompare.

Provides comprehensive reproducibility management for all experiments.
"""

from .reproducibility_manager import (
    ReproducibilityManager,
    RandomStateManager,
    EnvironmentManager,
    ExperimentContext,
    ReproducibilityError,
    get_global_manager,
    set_global_seed,
    create_reproducible_experiment
)

__all__ = [
    'ReproducibilityManager',
    'RandomStateManager',
    'EnvironmentManager',
    'ExperimentContext',
    'ReproducibilityError',
    'get_global_manager',
    'set_global_seed',
    'create_reproducible_experiment'
]

# Version info
__version__ = '1.0.0'