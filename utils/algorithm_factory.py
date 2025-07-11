"""
Algorithm Factory Module for BioAlgoCompare

This module provides a centralized factory for creating algorithm instances.
It maintains a single registry of all available algorithms and their metadata.
"""

from typing import Dict, Tuple, Type, Any, Optional
from algorithms.base import MetaheuristicAlgorithm

# Import all algorithm implementations
from algorithms.sho import SHO
from algorithms.apo import APO
from algorithms.egto import EGTO
from algorithms.fsa import FSA
from algorithms.foa import FOA
from algorithms.woa import WOA
from algorithms.hho import HHO
from algorithms.mrfo import MRFO
from algorithms.sma import SMA
from algorithms.gto import GTO
from algorithms.ewa import EWA
from algorithms.aha import AHA
from algorithms.opa import OPA
from algorithms.rro import RRO
from algorithms.smo import SMO
from algorithms.gvoa import GVOA


# Algorithm registry: name -> (class, full_name, year)
ALGORITHMS: Dict[str, Tuple[Type[MetaheuristicAlgorithm], str, int]] = {
    # Primary algorithms
    "sho": (SHO, "Spotted Hyena Optimizer", 2017),
    "apo": (APO, "Artificial Protozoa Optimizer", 2024),
    "egto": (EGTO, "Enhanced Gorilla Troops Optimization", 2024),
    "fsa": (FSA, "Flamingo Search Algorithm", 2021),
    "foa": (FOA, "Fossa Optimization Algorithm", 2024),
    "woa": (WOA, "Whale Optimization Algorithm", 2016),
    "hho": (HHO, "Harris Hawks Optimization", 2019),
    "mrfo": (MRFO, "Manta Ray Foraging Optimization", 2020),
    "sma": (SMA, "Slime Mould Algorithm", 2020),
    "gto": (GTO, "Gorilla Troops Optimization", 2021),
    "ewa": (EWA, "Earthworm Optimization Algorithm", 2018),
    "aha": (AHA, "Artificial Hummingbird Algorithm", 2022),
    "opa": (OPA, "Orca Predator Algorithm", 2021),
    "rro": (RRO, "Raven Roosting Optimization", 2016),
    "smo": (SMO, "Starling Murmuration Optimizer", 2022),
    "gvoa": (GVOA, "Griffon Vultures Optimization Algorithm", 2025),
    # Aliases for backward compatibility
    "hoa": (SHO, "Spotted Hyena Optimizer (HOA alias)", 2017),  # HOA = SHO
    "fgo": (FSA, "Flamingo Search Algorithm (FGO alias)", 2021),  # FGO = FSA
}


def create_algorithm(
    name: str,
    problem: Any,
    population_size: int = 30,
    iterations: int = 100,
    seed: Optional[int] = None,
    **kwargs,
) -> MetaheuristicAlgorithm:
    """
    Create an algorithm instance by name.

    Args:
        name: Algorithm name (key in ALGORITHMS registry)
        problem: Problem instance to solve
        population_size: Population size
        iterations: Number of iterations
        seed: Random seed for reproducibility
        **kwargs: Additional algorithm-specific parameters

    Returns:
        Algorithm instance

    Raises:
        ValueError: If algorithm name is not found
    """
    name = name.lower()

    if name not in ALGORITHMS:
        available = ", ".join(sorted(ALGORITHMS.keys()))
        raise ValueError(
            f"Unknown algorithm: '{name}'. " f"Available algorithms: {available}"
        )

    algo_class, _, _ = ALGORITHMS[name]

    # Create algorithm instance with standard parameters
    return algo_class(
        problem=problem,
        population_size=population_size,
        iterations=iterations,
        seed=seed,
        **kwargs,
    )


def get_algorithm_info(name: str) -> Dict[str, Any]:
    """
    Get information about an algorithm.

    Args:
        name: Algorithm name

    Returns:
        Dictionary with algorithm information

    Raises:
        ValueError: If algorithm name is not found
    """
    name = name.lower()

    if name not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm: '{name}'")

    algo_class, full_name, year = ALGORITHMS[name]

    return {
        "name": name,
        "class": algo_class,
        "full_name": full_name,
        "year": year,
        "module": algo_class.__module__,
        "is_alias": name in ["hoa", "fgo"],
    }


def list_algorithms(include_aliases: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    List all available algorithms.

    Args:
        include_aliases: Whether to include algorithm aliases

    Returns:
        Dictionary of algorithm information
    """
    result = {}

    for name, (algo_class, full_name, year) in ALGORITHMS.items():
        if not include_aliases and name in ["hoa", "fgo"]:
            continue

        result[name] = {
            "full_name": full_name,
            "year": year,
            "class_name": algo_class.__name__,
            "is_alias": name in ["hoa", "fgo"],
        }

    return result


def get_algorithm_by_year(
    start_year: int, end_year: Optional[int] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Get algorithms published in a specific year range.

    Args:
        start_year: Start year (inclusive)
        end_year: End year (inclusive), if None uses start_year

    Returns:
        Dictionary of algorithms in the specified year range
    """
    if end_year is None:
        end_year = start_year

    result = {}

    for name, (algo_class, full_name, year) in ALGORITHMS.items():
        if name in ["hoa", "fgo"]:  # Skip aliases
            continue

        if start_year <= year <= end_year:
            result[name] = {
                "full_name": full_name,
                "year": year,
                "class_name": algo_class.__name__,
            }

    return result


# Convenience function for getting algorithm class directly
def get_algorithm_class(name: str) -> Type[MetaheuristicAlgorithm]:
    """
    Get algorithm class by name.

    Args:
        name: Algorithm name

    Returns:
        Algorithm class

    Raises:
        ValueError: If algorithm name is not found
    """
    name = name.lower()

    if name not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm: '{name}'")

    return ALGORITHMS[name][0]
