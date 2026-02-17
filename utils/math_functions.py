"""Mathematical functions shared across multiple algorithms.

This module contains common mathematical operations used by various
bio-inspired algorithms to avoid code duplication.
"""

import numpy as np
import math
from typing import Union, Optional


def levy_flight(dim: int, beta: float = 1.5, rng=None) -> np.ndarray:
    """Generate Lévy flight step vector.

    Lévy flights are random walks with step-lengths having a probability
    distribution that is heavy-tailed. They are used in various optimization
    algorithms for exploration.

    Args:
        dim: Dimension of the step vector
        beta: Power law index (default: 1.5)
        rng: NumPy random generator instance (uses global if None)

    Returns:
        np.ndarray: Lévy flight step vector of size dim

    References:
        Mantegna, R. N. (1994). Fast, accurate algorithm for numerical
        simulation of Lévy stable stochastic processes.
    """
    if rng is None:
        rng = np.random.default_rng()
    # Calculate sigma using Mantegna's method
    sigma = (
        math.gamma(1 + beta)
        * math.sin(math.pi * beta / 2)
        / (math.gamma((1 + beta) / 2) * beta * 2 ** ((beta - 1) / 2))
    ) ** (1 / beta)

    # Generate random samples
    u = rng.normal(0, sigma, dim)
    v = rng.normal(0, 1, dim)

    # Calculate Lévy flight step
    return u / (np.abs(v) ** (1 / beta))


def cauchy_distribution(size: Union[int, tuple]) -> np.ndarray:
    """Generate random numbers from Cauchy distribution.
    
    The Cauchy distribution is used in some algorithms for generating
    large occasional jumps in the search space.
    
    Args:
        size: Output shape (integer or tuple of integers)
        
    Returns:
        np.ndarray: Random samples from standard Cauchy distribution
    """
    if isinstance(size, int):
        size = (size,)
    return np.tan(np.pi * (np.random.rand(*size) - 0.5))


def sigmoid(x: np.ndarray) -> np.ndarray:
    """Sigmoid activation function.
    
    Maps any real value to the range (0, 1).
    
    Args:
        x: Input array
        
    Returns:
        np.ndarray: Sigmoid of input values
    """
    return 1 / (1 + np.exp(-x))


def tanh(x: np.ndarray) -> np.ndarray:
    """Hyperbolic tangent activation function.
    
    Maps any real value to the range (-1, 1).
    
    Args:
        x: Input array
        
    Returns:
        np.ndarray: Hyperbolic tangent of input values
    """
    return np.tanh(x)


def gaussian_mutation(position: np.ndarray, sigma: float = 0.1) -> np.ndarray:
    """Apply Gaussian mutation to a position vector.
    
    Args:
        position: Current position vector
        sigma: Standard deviation of the Gaussian noise
        
    Returns:
        np.ndarray: Mutated position vector
    """
    noise = np.random.normal(0, sigma, position.shape)
    return position + noise


def polynomial_mutation(position: np.ndarray, eta: float = 20.0) -> np.ndarray:
    """Apply polynomial mutation to a position vector.
    
    This mutation operator is commonly used in genetic algorithms and
    provides a controlled mutation with tunable distribution.
    
    Args:
        position: Current position vector (assumed to be in [0, 1])
        eta: Distribution index (higher values = smaller mutations)
        
    Returns:
        np.ndarray: Mutated position vector
    """
    u = np.random.rand(*position.shape)
    delta = np.zeros_like(position)
    
    mask1 = u <= 0.5
    mask2 = u > 0.5
    
    delta[mask1] = (2 * u[mask1]) ** (1 / (eta + 1)) - 1
    delta[mask2] = 1 - (2 * (1 - u[mask2])) ** (1 / (eta + 1))
    
    mutated = position + delta
    return np.clip(mutated, 0, 1)


def spiral_movement(current: np.ndarray, target: np.ndarray, 
                   b: float = 1.0, l: float = None) -> np.ndarray:
    """Calculate spiral movement towards a target.
    
    Used in algorithms like WOA (Whale Optimization Algorithm) for
    exploitation phase.
    
    Args:
        current: Current position
        target: Target position
        b: Spiral shape constant
        l: Random number in [-1, 1] (generated if None)
        
    Returns:
        np.ndarray: New position after spiral movement
    """
    if l is None:
        l = 2 * np.random.rand() - 1
    
    distance = np.abs(target - current)
    return distance * np.exp(b * l) * np.cos(2 * np.pi * l) + target


def s_shaped_transfer(x: np.ndarray, version: int = 1) -> np.ndarray:
    """S-shaped transfer functions for binary optimization.
    
    Args:
        x: Input values
        version: Version of S-shaped function (1-4)
        
    Returns:
        np.ndarray: Probability values in [0, 1]
    """
    if version == 1:
        return sigmoid(x)
    elif version == 2:
        return sigmoid(2 * x)
    elif version == 3:
        return sigmoid(4 * x)
    elif version == 4:
        return sigmoid(x / 2)
    else:
        raise ValueError(f"Invalid S-shaped version: {version}")


def v_shaped_transfer(x: np.ndarray, version: int = 1) -> np.ndarray:
    """V-shaped transfer functions for binary optimization.
    
    Args:
        x: Input values
        version: Version of V-shaped function (1-4)
        
    Returns:
        np.ndarray: Probability values in [0, 1]
    """
    if version == 1:
        return np.abs(tanh(x))
    elif version == 2:
        return np.abs(tanh(2 * x))
    elif version == 3:
        return np.abs(tanh(4 * x))
    elif version == 4:
        return np.abs(tanh(x / 2))
    else:
        raise ValueError(f"Invalid V-shaped version: {version}")


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate Euclidean distance between two points.
    
    Args:
        a: First point
        b: Second point
        
    Returns:
        float: Euclidean distance
    """
    return np.linalg.norm(a - b)


def manhattan_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate Manhattan distance between two points.
    
    Args:
        a: First point
        b: Second point
        
    Returns:
        float: Manhattan distance
    """
    return np.sum(np.abs(a - b))


def minkowski_distance(a: np.ndarray, b: np.ndarray, p: float = 2) -> float:
    """Calculate Minkowski distance between two points.
    
    Args:
        a: First point
        b: Second point
        p: Order of the Minkowski distance
        
    Returns:
        float: Minkowski distance
    """
    return np.sum(np.abs(a - b) ** p) ** (1 / p)