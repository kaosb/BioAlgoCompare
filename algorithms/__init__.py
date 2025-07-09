"""Bio-inspired optimization algorithms package.

This package contains implementations of various bio-inspired metaheuristic
algorithms for solving optimization problems, particularly the Vehicle Routing
Problem (VRP).

Available algorithms:
    - AHA: Artificial Hummingbird Algorithm
    - APO: Artificial Protozoa Optimizer
    - EGTO: Enhanced Gorilla Troops Optimizer
    - EWA: Earthworm Algorithm
    - FGO/FSA: Flamingo Algorithm / Flamingo Search Algorithm
    - FOA: Fossa Optimization Algorithm
    - GTO: Gorilla Troops Optimizer
    - HHO: Harris Hawks Optimization
    - HOA/SHO: Hyena Optimization Algorithm / Spotted Hyena Optimizer
    - MRFO: Manta Ray Foraging Optimization
    - OPA: Orca Predator Algorithm
    - RRO: Raven Roosting Optimization
    - SMA: Slime Mould Algorithm
    - SMO: Starling Murmuration Optimizer
    - WOA: Whale Optimization Algorithm
    - GVOA: Griffon Vultures Optimization Algorithm

Example usage:
    >>> from algorithms import EWA
    >>> from problems.vrp import VRPProblem
    >>> 
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>> 
    >>> algorithm = EWA(problem, population_size=30)
    >>> algorithm.initialize_population()
    >>> best_solution = algorithm.run(iterations=100)
"""

# Import base classes
from .base import Individual, MetaheuristicAlgorithm

# Import all algorithm implementations
from .aha import AHA, Hummingbird
from .apo import APO, Protozoa
from .egto import EGTO, EnhancedGorilla
from .ewa import EWA, Earthworm
from .fgo import FGO, Flamingo as FlamingoFGO
from .foa import FOA, Fossa
from .fsa import FSA, Flamingo as FlamingoFSA
from .gto import GTO, Gorilla
from .gvoa import GVOA, Vulture
from .hho import HHO, Hawk
from .hoa import HOA, Hyena as HyenaHOA
from .mrfo import MRFO, MantaRay
from .opa import OPA, Orca
from .rro import RRO, Raven
from .sho import SHO, Hyena as HyenaSHO
from .sma import SMA, SlimeMould
from .smo import SMO, Starling
from .woa import WOA, Whale

# Create algorithm registry for easy access
ALGORITHMS = {
    'aha': AHA,
    'apo': APO,
    'egto': EGTO,
    'ewa': EWA,
    'fgo': FGO,
    'foa': FOA,
    'fsa': FSA,
    'gto': GTO,
    'gvoa': GVOA,
    'hho': HHO,
    'hoa': HOA,
    'mrfo': MRFO,
    'opa': OPA,
    'rro': RRO,
    'sho': SHO,
    'sma': SMA,
    'smo': SMO,
    'woa': WOA,
}

# Aliases for convenience
ALGORITHMS['hyena'] = SHO  # Spotted Hyena Optimizer
ALGORITHMS['flamingo'] = FSA  # Default to FSA for flamingo

def get_algorithm(name):
    """Get an algorithm class by name.
    
    Args:
        name: Algorithm name (case-insensitive)
        
    Returns:
        Algorithm class
        
    Raises:
        ValueError: If algorithm name is not found
    """
    name_lower = name.lower()
    if name_lower not in ALGORITHMS:
        available = ', '.join(sorted(ALGORITHMS.keys()))
        raise ValueError(f"Algorithm '{name}' not found. Available: {available}")
    return ALGORITHMS[name_lower]

# Export all classes and utilities
__all__ = [
    # Base classes
    'Individual',
    'MetaheuristicAlgorithm',
    # Algorithms
    'AHA', 'APO', 'EGTO', 'EWA', 'FGO', 'FOA', 'FSA', 'GTO', 'GVOA',
    'HHO', 'HOA', 'MRFO', 'OPA', 'RRO', 'SHO', 'SMA', 'SMO', 'WOA',
    # Individual classes
    'Hummingbird', 'Protozoa', 'EnhancedGorilla', 'Earthworm', 'FlamingoFGO',
    'Fossa', 'FlamingoFSA', 'Gorilla', 'Vulture', 'Hawk', 'HyenaHOA',
    'MantaRay', 'Orca', 'Raven', 'HyenaSHO', 'SlimeMould', 'Starling', 'Whale',
    # Utilities
    'ALGORITHMS', 'get_algorithm',
]