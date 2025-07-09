"""
Common mathematical operators for metaheuristic algorithms.

This module consolidates frequently used mathematical functions
to avoid code duplication across different algorithms.
"""

import numpy as np
from typing import Union, Optional, Tuple
import math


def levy_flight(dimension: int, 
                beta: float = 1.5, 
                scale: float = 1.0,
                epsilon: float = 1e-8) -> np.ndarray:
    """
    Generate a Lévy flight step.
    
    Lévy flights are random walks where the step-lengths follow a Lévy distribution.
    They are commonly used in metaheuristic algorithms for exploration.
    
    Args:
        dimension: The dimension of the step vector
        beta: The power law index (typically between 1 and 3)
        scale: Scaling factor for the step size
        epsilon: Small value to avoid division by zero
        
    Returns:
        A numpy array of shape (dimension,) representing the Lévy flight step
        
    References:
        - Mantegna, R. N. (1994). Fast, accurate algorithm for numerical simulation 
          of Lévy stable stochastic processes.
    """
    # Mantegna's algorithm for Lévy flight
    sigma_u = (
        math.gamma(1 + beta) * np.sin(np.pi * beta / 2) /
        (math.gamma((1 + beta) / 2) * beta * 2**((beta - 1) / 2))
    ) ** (1 / beta)
    
    # Generate random samples
    u = np.random.normal(0, sigma_u, dimension)
    v = np.random.normal(0, 1, dimension)
    
    # Calculate step
    step = u / (np.abs(v) ** (1 / beta) + epsilon)
    
    # Apply scaling
    return scale * step


def cauchy_mutation(dimension: int, 
                   scale: float = 1.0,
                   location: float = 0.0) -> np.ndarray:
    """
    Generate a Cauchy distribution sample for mutation.
    
    The Cauchy distribution has heavier tails than the normal distribution,
    making it suitable for global exploration in optimization.
    
    Args:
        dimension: The dimension of the sample
        scale: Scale parameter (gamma) of the Cauchy distribution
        location: Location parameter of the Cauchy distribution
        
    Returns:
        A numpy array of shape (dimension,) with Cauchy-distributed values
    """
    # Use numpy's standard Cauchy and scale/shift
    return location + scale * np.random.standard_cauchy(dimension)


def gaussian_mutation(dimension: int,
                     mean: float = 0.0,
                     std: float = 1.0) -> np.ndarray:
    """
    Generate a Gaussian (normal) distribution sample for mutation.
    
    Args:
        dimension: The dimension of the sample
        mean: Mean of the distribution
        std: Standard deviation
        
    Returns:
        A numpy array of shape (dimension,) with normally distributed values
    """
    return np.random.normal(mean, std, dimension)


def brownian_motion(dimension: int,
                   time_step: float = 1.0,
                   diffusion_coefficient: float = 1.0) -> np.ndarray:
    """
    Generate a Brownian motion step.
    
    Brownian motion is used in some algorithms to model random walk behavior.
    
    Args:
        dimension: The dimension of the step
        time_step: Time step size (dt)
        diffusion_coefficient: Diffusion coefficient (D)
        
    Returns:
        A numpy array representing the Brownian motion step
    """
    # Brownian motion: dX = sqrt(2 * D * dt) * N(0, 1)
    scale = np.sqrt(2 * diffusion_coefficient * time_step)
    return scale * np.random.normal(0, 1, dimension)


def random_walk(dimension: int,
                step_size: float = 1.0,
                walk_type: str = 'uniform') -> np.ndarray:
    """
    Generate a random walk step.
    
    Args:
        dimension: The dimension of the step
        step_size: Maximum step size
        walk_type: Type of random walk ('uniform', 'gaussian', 'levy')
        
    Returns:
        A numpy array representing the random walk step
    """
    if walk_type == 'uniform':
        # Uniform random walk in [-step_size, step_size]
        return np.random.uniform(-step_size, step_size, dimension)
    elif walk_type == 'gaussian':
        # Gaussian random walk
        return step_size * np.random.normal(0, 1, dimension)
    elif walk_type == 'levy':
        # Lévy flight random walk
        return levy_flight(dimension, scale=step_size)
    else:
        raise ValueError(f"Unknown walk type: {walk_type}")


def sigmoid(x: Union[float, np.ndarray], 
           steepness: float = 1.0) -> Union[float, np.ndarray]:
    """
    Sigmoid function for smooth transitions.
    
    Args:
        x: Input value(s)
        steepness: Controls the steepness of the sigmoid
        
    Returns:
        Sigmoid of x
    """
    return 1 / (1 + np.exp(-steepness * x))


def adaptive_parameter(iteration: int,
                      max_iterations: int,
                      initial_value: float,
                      final_value: float,
                      schedule: str = 'linear') -> float:
    """
    Calculate an adaptive parameter value based on iteration progress.
    
    Args:
        iteration: Current iteration
        max_iterations: Maximum iterations
        initial_value: Starting value
        final_value: Ending value
        schedule: Type of schedule ('linear', 'exponential', 'sigmoid', 'cosine')
        
    Returns:
        The adapted parameter value
    """
    if max_iterations == 0:
        return initial_value
    
    progress = iteration / max_iterations
    
    if schedule == 'linear':
        return initial_value + (final_value - initial_value) * progress
    
    elif schedule == 'exponential':
        if final_value == 0:
            # Avoid log(0)
            return initial_value * (1 - progress)
        else:
            # Exponential interpolation
            return initial_value * (final_value / initial_value) ** progress
    
    elif schedule == 'sigmoid':
        # Sigmoid transition (smooth S-curve)
        x = 10 * (progress - 0.5)  # Map [0,1] to [-5,5]
        sigmoid_value = sigmoid(x)
        return initial_value + (final_value - initial_value) * sigmoid_value
    
    elif schedule == 'cosine':
        # Cosine annealing
        cos_value = 0.5 * (1 + np.cos(np.pi * progress))
        return final_value + (initial_value - final_value) * cos_value
    
    else:
        raise ValueError(f"Unknown schedule type: {schedule}")


def chaotic_map(x: Union[float, np.ndarray],
                map_type: str = 'logistic',
                parameter: float = 4.0) -> Union[float, np.ndarray]:
    """
    Generate chaotic sequence using various chaotic maps.
    
    Args:
        x: Current value(s) in [0, 1]
        map_type: Type of chaotic map ('logistic', 'tent', 'sine', 'circle')
        parameter: Control parameter for the map
        
    Returns:
        Next value(s) in the chaotic sequence
    """
    if map_type == 'logistic':
        # Logistic map: x_{n+1} = r * x_n * (1 - x_n)
        return parameter * x * (1 - x)
    
    elif map_type == 'tent':
        # Tent map
        return np.where(x < 0.5, parameter * x, parameter * (1 - x))
    
    elif map_type == 'sine':
        # Sine map: x_{n+1} = (a/4) * sin(π * x_n)
        return (parameter / 4) * np.sin(np.pi * x)
    
    elif map_type == 'circle':
        # Circle map (simplified version)
        K = parameter
        return (x + K / (2 * np.pi) * np.sin(2 * np.pi * x)) % 1
    
    else:
        raise ValueError(f"Unknown chaotic map type: {map_type}")


def spiral_movement(current_pos: np.ndarray,
                   target_pos: np.ndarray,
                   iteration: int,
                   spiral_param: float = 0.1) -> np.ndarray:
    """
    Calculate spiral movement towards a target position.
    
    Used in algorithms like WOA (Whale Optimization Algorithm).
    
    Args:
        current_pos: Current position
        target_pos: Target position
        iteration: Current iteration (affects spiral radius)
        spiral_param: Parameter controlling spiral shape
        
    Returns:
        New position after spiral movement
    """
    distance = np.linalg.norm(target_pos - current_pos)
    
    # Spiral equation parameters
    b = spiral_param
    l = np.random.uniform(-1, 1)
    
    # Calculate spiral movement
    return (
        distance * np.exp(b * l) * np.cos(2 * np.pi * l) * (target_pos - current_pos) +
        target_pos
    )


def tournament_selection(population: list,
                        fitness_values: list,
                        tournament_size: int = 3,
                        minimize: bool = True) -> int:
    """
    Tournament selection for choosing individuals.
    
    Args:
        population: List of individuals (not used, but kept for consistency)
        fitness_values: Fitness values of the population
        tournament_size: Number of individuals in each tournament
        minimize: Whether we're minimizing (True) or maximizing (False)
        
    Returns:
        Index of the selected individual
    """
    pop_size = len(fitness_values)
    
    # Select random individuals for tournament
    tournament_indices = np.random.choice(pop_size, tournament_size, replace=False)
    tournament_fitness = [fitness_values[i] for i in tournament_indices]
    
    # Select best from tournament
    if minimize:
        best_idx = np.argmin(tournament_fitness)
    else:
        best_idx = np.argmax(tournament_fitness)
    
    return tournament_indices[best_idx]


def roulette_wheel_selection(fitness_values: list,
                            minimize: bool = True,
                            pressure: float = 1.0) -> int:
    """
    Roulette wheel selection based on fitness values.
    
    Args:
        fitness_values: List of fitness values
        minimize: Whether we're minimizing (True) or maximizing (False)
        pressure: Selection pressure (higher = more selective)
        
    Returns:
        Index of the selected individual
    """
    fitness_array = np.array(fitness_values)
    
    if minimize:
        # For minimization, invert fitness values
        if np.any(fitness_array <= 0):
            # Handle negative or zero fitness
            fitness_array = fitness_array - np.min(fitness_array) + 1
        selection_probs = 1.0 / fitness_array
    else:
        # For maximization, use fitness directly
        if np.any(fitness_array < 0):
            # Shift to make all positive
            fitness_array = fitness_array - np.min(fitness_array)
        selection_probs = fitness_array
    
    # Apply selection pressure
    selection_probs = selection_probs ** pressure
    
    # Normalize to probabilities
    selection_probs = selection_probs / np.sum(selection_probs)
    
    # Select individual
    return np.random.choice(len(fitness_values), p=selection_probs)


def boundary_handling(position: np.ndarray,
                     lower_bounds: np.ndarray,
                     upper_bounds: np.ndarray,
                     method: str = 'clip') -> np.ndarray:
    """
    Handle boundary constraints for continuous optimization.
    
    Args:
        position: Current position
        lower_bounds: Lower bounds for each dimension
        upper_bounds: Upper bounds for each dimension
        method: Boundary handling method ('clip', 'reflect', 'wrap', 'random')
        
    Returns:
        Position after boundary handling
    """
    if method == 'clip':
        # Simple clipping to bounds
        return np.clip(position, lower_bounds, upper_bounds)
    
    elif method == 'reflect':
        # Reflection at boundaries
        pos = position.copy()
        
        # Handle lower bounds
        below_lower = pos < lower_bounds
        pos[below_lower] = 2 * lower_bounds[below_lower] - pos[below_lower]
        
        # Handle upper bounds
        above_upper = pos > upper_bounds
        pos[above_upper] = 2 * upper_bounds[above_upper] - pos[above_upper]
        
        # Ensure still within bounds after reflection
        return np.clip(pos, lower_bounds, upper_bounds)
    
    elif method == 'wrap':
        # Periodic boundary conditions
        pos = position.copy()
        range_size = upper_bounds - lower_bounds
        
        # Wrap around
        while np.any(pos < lower_bounds) or np.any(pos > upper_bounds):
            pos[pos < lower_bounds] += range_size[pos < lower_bounds]
            pos[pos > upper_bounds] -= range_size[pos > upper_bounds]
        
        return pos
    
    elif method == 'random':
        # Random reinitialization for out-of-bounds dimensions
        pos = position.copy()
        out_of_bounds = (pos < lower_bounds) | (pos > upper_bounds)
        pos[out_of_bounds] = np.random.uniform(
            lower_bounds[out_of_bounds],
            upper_bounds[out_of_bounds]
        )
        return pos
    
    else:
        raise ValueError(f"Unknown boundary handling method: {method}")


def diversity_measure(population: np.ndarray,
                     metric: str = 'average_distance') -> float:
    """
    Calculate population diversity.
    
    Args:
        population: Array of shape (pop_size, dimension)
        metric: Type of diversity metric
        
    Returns:
        Diversity value
    """
    if len(population) < 2:
        return 0.0
    
    if metric == 'average_distance':
        # Average pairwise distance
        total_distance = 0
        count = 0
        
        for i in range(len(population)):
            for j in range(i + 1, len(population)):
                total_distance += np.linalg.norm(population[i] - population[j])
                count += 1
        
        return total_distance / count if count > 0 else 0.0
    
    elif metric == 'std_deviation':
        # Standard deviation along each dimension
        return np.mean(np.std(population, axis=0))
    
    elif metric == 'entropy':
        # Shannon entropy based on grid discretization
        # This is a simplified version
        n_bins = 10
        hist, _ = np.histogramdd(population, bins=n_bins)
        hist = hist.flatten()
        hist = hist[hist > 0]  # Remove zero entries
        hist = hist / hist.sum()  # Normalize
        
        # Calculate entropy
        return -np.sum(hist * np.log(hist))
    
    else:
        raise ValueError(f"Unknown diversity metric: {metric}")