"""
Vectorized operations for high-performance algorithm implementations.

This module provides NumPy-optimized operations that replace loops with
vectorized computations for significant performance improvements.
"""

import numpy as np
from typing import Optional, Tuple, Union, List, Callable
from numba import jit, prange, config
import warnings
import logging

# Try to import CuPy for GPU acceleration
try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    cp = None

logger = logging.getLogger(__name__)

# Configure Numba
config.THREADING_LAYER = 'threadsafe'


class VectorizedOperations:
    """
    Collection of vectorized operations for algorithm optimization.
    
    Provides high-performance implementations of common algorithm operations
    using NumPy vectorization, Numba JIT compilation, and optional GPU acceleration.
    """
    
    def __init__(self, use_gpu: bool = False, gpu_device: int = 0):
        """
        Initialize vectorized operations.
        
        Args:
            use_gpu: Whether to use GPU acceleration (requires CuPy)
            gpu_device: GPU device ID
        """
        self.use_gpu = use_gpu and CUPY_AVAILABLE
        
        if self.use_gpu:
            cp.cuda.Device(gpu_device).use()
            self.array_module = cp
            logger.info(f"GPU acceleration enabled on device {gpu_device}")
        else:
            self.array_module = np
            if use_gpu and not CUPY_AVAILABLE:
                warnings.warn("GPU requested but CuPy not available, using CPU")
    
    def to_device(self, array: np.ndarray) -> Union[np.ndarray, 'cp.ndarray']:
        """Transfer array to appropriate device (CPU/GPU)."""
        if self.use_gpu:
            return cp.asarray(array)
        return array
    
    def to_host(self, array: Union[np.ndarray, 'cp.ndarray']) -> np.ndarray:
        """Transfer array back to host (CPU)."""
        if self.use_gpu and hasattr(array, 'get'):
            return array.get()
        return array
    
    # Distance calculations
    
    def euclidean_distances_matrix(self, points: np.ndarray) -> np.ndarray:
        """
        Compute pairwise Euclidean distances between all points.
        
        Args:
            points: Array of shape (n_points, n_dimensions)
        
        Returns:
            Distance matrix of shape (n_points, n_points)
        """
        xp = self.array_module
        points = self.to_device(points)
        
        # Using broadcasting for efficient computation
        # ||a - b||^2 = ||a||^2 + ||b||^2 - 2<a, b>
        sq_norms = xp.sum(points**2, axis=1)
        dot_products = xp.dot(points, points.T)
        distances_sq = sq_norms[:, None] + sq_norms[None, :] - 2 * dot_products
        
        # Numerical stability: ensure non-negative
        distances_sq = xp.maximum(distances_sq, 0)
        distances = xp.sqrt(distances_sq)
        
        return self.to_host(distances)
    
    @staticmethod
    @jit(nopython=True, parallel=True, cache=True)
    def euclidean_distances_to_point_numba(
        points: np.ndarray,
        target: np.ndarray
    ) -> np.ndarray:
        """
        Compute distances from multiple points to a single target (Numba optimized).
        
        Args:
            points: Array of shape (n_points, n_dimensions)
            target: Array of shape (n_dimensions,)
        
        Returns:
            Distances array of shape (n_points,)
        """
        n_points = points.shape[0]
        distances = np.empty(n_points)
        
        for i in prange(n_points):
            dist = 0.0
            for j in range(points.shape[1]):
                diff = points[i, j] - target[j]
                dist += diff * diff
            distances[i] = np.sqrt(dist)
        
        return distances
    
    def manhattan_distances_matrix(self, points: np.ndarray) -> np.ndarray:
        """
        Compute pairwise Manhattan distances between all points.
        
        Args:
            points: Array of shape (n_points, n_dimensions)
        
        Returns:
            Distance matrix of shape (n_points, n_points)
        """
        xp = self.array_module
        points = self.to_device(points)
        
        # Use broadcasting to compute all pairwise differences
        diffs = xp.abs(points[:, None, :] - points[None, :, :])
        distances = xp.sum(diffs, axis=2)
        
        return self.to_host(distances)
    
    # Population operations
    
    def initialize_population_uniform(
        self,
        pop_size: int,
        dimensions: int,
        bounds: Tuple[float, float] = (0, 1),
        seed: Optional[int] = None
    ) -> np.ndarray:
        """
        Initialize population with uniform random distribution.
        
        Args:
            pop_size: Population size
            dimensions: Number of dimensions
            bounds: Min and max bounds for each dimension
            seed: Random seed
        
        Returns:
            Population array of shape (pop_size, dimensions)
        """
        xp = self.array_module
        
        if seed is not None:
            if self.use_gpu:
                xp.random.seed(seed)
            else:
                np.random.seed(seed)
        
        population = xp.random.uniform(
            bounds[0], bounds[1],
            size=(pop_size, dimensions)
        )
        
        return self.to_host(population)
    
    def initialize_population_normal(
        self,
        pop_size: int,
        dimensions: int,
        center: Optional[np.ndarray] = None,
        std: float = 0.1,
        bounds: Optional[Tuple[float, float]] = None,
        seed: Optional[int] = None
    ) -> np.ndarray:
        """
        Initialize population with normal distribution.
        
        Args:
            pop_size: Population size
            dimensions: Number of dimensions
            center: Center point for distribution
            std: Standard deviation
            bounds: Optional bounds to clip values
            seed: Random seed
        
        Returns:
            Population array of shape (pop_size, dimensions)
        """
        xp = self.array_module
        
        if seed is not None:
            if self.use_gpu:
                xp.random.seed(seed)
            else:
                np.random.seed(seed)
        
        if center is None:
            center = xp.ones(dimensions) * 0.5
        else:
            center = self.to_device(center)
        
        population = xp.random.normal(
            center, std,
            size=(pop_size, dimensions)
        )
        
        if bounds:
            population = xp.clip(population, bounds[0], bounds[1])
        
        return self.to_host(population)
    
    def evaluate_population_vectorized(
        self,
        population: np.ndarray,
        fitness_func: Callable[[np.ndarray], np.ndarray]
    ) -> np.ndarray:
        """
        Evaluate entire population using vectorized fitness function.
        
        Args:
            population: Population array of shape (pop_size, dimensions)
            fitness_func: Vectorized fitness function
        
        Returns:
            Fitness values array of shape (pop_size,)
        """
        population = self.to_device(population)
        fitness_values = fitness_func(population)
        return self.to_host(fitness_values)
    
    @staticmethod
    @jit(nopython=True, parallel=True, cache=True)
    def crossover_uniform_numba(
        parent1: np.ndarray,
        parent2: np.ndarray,
        mask: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Uniform crossover between two parents (Numba optimized).
        
        Args:
            parent1: First parent
            parent2: Second parent
            mask: Boolean mask for crossover
        
        Returns:
            Two offspring
        """
        offspring1 = np.empty_like(parent1)
        offspring2 = np.empty_like(parent2)
        
        for i in prange(len(parent1)):
            if mask[i]:
                offspring1[i] = parent1[i]
                offspring2[i] = parent2[i]
            else:
                offspring1[i] = parent2[i]
                offspring2[i] = parent1[i]
        
        return offspring1, offspring2
    
    def crossover_arithmetic(
        self,
        parent1: np.ndarray,
        parent2: np.ndarray,
        alpha: Union[float, np.ndarray] = 0.5
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Arithmetic crossover between parents.
        
        Args:
            parent1: First parent array
            parent2: Second parent array
            alpha: Blending factor (scalar or array)
        
        Returns:
            Two offspring arrays
        """
        xp = self.array_module
        parent1 = self.to_device(parent1)
        parent2 = self.to_device(parent2)
        
        if isinstance(alpha, (int, float)):
            alpha = xp.full(parent1.shape, alpha)
        else:
            alpha = self.to_device(alpha)
        
        offspring1 = alpha * parent1 + (1 - alpha) * parent2
        offspring2 = (1 - alpha) * parent1 + alpha * parent2
        
        return self.to_host(offspring1), self.to_host(offspring2)
    
    def mutation_gaussian(
        self,
        population: np.ndarray,
        mutation_rate: float = 0.1,
        sigma: float = 0.1,
        bounds: Optional[Tuple[float, float]] = None
    ) -> np.ndarray:
        """
        Apply Gaussian mutation to population.
        
        Args:
            population: Population array
            mutation_rate: Probability of mutation per gene
            sigma: Standard deviation of Gaussian noise
            bounds: Optional bounds to clip values
        
        Returns:
            Mutated population
        """
        xp = self.array_module
        population = self.to_device(population)
        
        # Create mutation mask
        mask = xp.random.random(population.shape) < mutation_rate
        
        # Apply Gaussian noise
        noise = xp.random.normal(0, sigma, population.shape)
        mutated = population + mask * noise
        
        if bounds:
            mutated = xp.clip(mutated, bounds[0], bounds[1])
        
        return self.to_host(mutated)
    
    def mutation_polynomial(
        self,
        population: np.ndarray,
        mutation_rate: float = 0.1,
        eta: float = 20.0,
        bounds: Tuple[float, float] = (0, 1)
    ) -> np.ndarray:
        """
        Apply polynomial mutation (used in genetic algorithms).
        
        Args:
            population: Population array
            mutation_rate: Probability of mutation per gene
            eta: Distribution index (higher = less disruptive)
            bounds: Variable bounds
        
        Returns:
            Mutated population
        """
        xp = self.array_module
        population = self.to_device(population)
        
        # Create mutation mask
        mask = xp.random.random(population.shape) < mutation_rate
        
        # Polynomial mutation
        u = xp.random.random(population.shape)
        
        delta1 = (population - bounds[0]) / (bounds[1] - bounds[0])
        delta2 = (bounds[1] - population) / (bounds[1] - bounds[0])
        
        mut_pow = 1.0 / (eta + 1.0)
        
        deltaq = xp.where(
            u <= 0.5,
            xp.power(2.0 * u + (1.0 - 2.0 * u) * xp.power(1.0 - delta1, eta + 1.0), mut_pow) - 1.0,
            1.0 - xp.power(2.0 * (1.0 - u) + 2.0 * (u - 0.5) * xp.power(1.0 - delta2, eta + 1.0), mut_pow)
        )
        
        mutated = population + mask * deltaq * (bounds[1] - bounds[0])
        mutated = xp.clip(mutated, bounds[0], bounds[1])
        
        return self.to_host(mutated)
    
    # Selection operations
    
    def tournament_selection(
        self,
        population: np.ndarray,
        fitness: np.ndarray,
        n_select: int,
        tournament_size: int = 3
    ) -> np.ndarray:
        """
        Tournament selection of individuals.
        
        Args:
            population: Population array
            fitness: Fitness values (lower is better)
            n_select: Number of individuals to select
            tournament_size: Size of each tournament
        
        Returns:
            Indices of selected individuals
        """
        xp = self.array_module
        fitness = self.to_device(fitness)
        
        selected_indices = xp.empty(n_select, dtype=int)
        
        for i in range(n_select):
            # Random tournament participants
            tournament = xp.random.choice(
                len(fitness), tournament_size, replace=False
            )
            
            # Select best (minimum fitness)
            winner = tournament[xp.argmin(fitness[tournament])]
            selected_indices[i] = winner
        
        return self.to_host(selected_indices)
    
    def roulette_wheel_selection(
        self,
        fitness: np.ndarray,
        n_select: int,
        minimize: bool = True
    ) -> np.ndarray:
        """
        Roulette wheel selection based on fitness.
        
        Args:
            fitness: Fitness values
            n_select: Number of individuals to select
            minimize: Whether minimizing fitness
        
        Returns:
            Indices of selected individuals
        """
        xp = self.array_module
        fitness = self.to_device(fitness)
        
        # Convert to selection probabilities
        if minimize:
            # For minimization, invert fitness
            weights = 1.0 / (fitness - xp.min(fitness) + 1e-10)
        else:
            weights = fitness - xp.min(fitness) + 1e-10
        
        # Normalize
        probabilities = weights / xp.sum(weights)
        
        # Cumulative sum for roulette wheel
        cum_probs = xp.cumsum(probabilities)
        
        selected_indices = xp.empty(n_select, dtype=int)
        
        for i in range(n_select):
            r = xp.random.random()
            selected_indices[i] = xp.searchsorted(cum_probs, r)
        
        return self.to_host(selected_indices)
    
    # Movement operations
    
    def levy_flight(
        self,
        size: Union[int, Tuple[int, ...]],
        beta: float = 1.5,
        scale: float = 0.01
    ) -> np.ndarray:
        """
        Generate Lévy flight random walk.
        
        Args:
            size: Output shape
            beta: Lévy index (typically 1.5)
            scale: Scaling factor
        
        Returns:
            Lévy flight steps
        """
        xp = self.array_module
        
        # Mantegna's algorithm
        sigma_u = (
            xp.exp(xp.log(xp.abs(
                xp.exp(xp.log(xp.abs(1 + beta)) + xp.log(xp.sin(xp.pi * beta / 2))) /
                (beta * xp.exp(xp.log(xp.abs(2)) * ((beta - 1) / 2)))
            )) / beta)
        )
        
        u = xp.random.normal(0, sigma_u, size)
        v = xp.random.normal(0, 1, size)
        
        step = u / xp.power(xp.abs(v), 1 / beta)
        levy = scale * step
        
        return self.to_host(levy)
    
    def spiral_movement(
        self,
        current_pos: np.ndarray,
        target_pos: np.ndarray,
        a: float = 1.0,
        b: float = 1.0,
        l: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Spiral movement towards target (used in WOA, SMA).
        
        Args:
            current_pos: Current positions
            target_pos: Target positions
            a: Spiral constant
            b: Spiral shape constant
            l: Random parameter array
        
        Returns:
            New positions after spiral movement
        """
        xp = self.array_module
        current_pos = self.to_device(current_pos)
        target_pos = self.to_device(target_pos)
        
        if l is None:
            l = xp.random.uniform(-1, 1, current_pos.shape)
        else:
            l = self.to_device(l)
        
        distance = xp.abs(target_pos - current_pos)
        new_pos = distance * xp.exp(b * l) * xp.cos(2 * xp.pi * l) + target_pos
        
        return self.to_host(new_pos)
    
    # Boundary handling
    
    def apply_bounds(
        self,
        positions: np.ndarray,
        bounds: Union[Tuple[float, float], np.ndarray],
        method: str = 'clip'
    ) -> np.ndarray:
        """
        Apply boundary constraints to positions.
        
        Args:
            positions: Position array
            bounds: Bounds (scalar tuple or array of bounds per dimension)
            method: Boundary handling method ('clip', 'reflect', 'wrap')
        
        Returns:
            Bounded positions
        """
        xp = self.array_module
        positions = self.to_device(positions)
        
        if isinstance(bounds, tuple):
            lower, upper = bounds
        else:
            bounds = self.to_device(bounds)
            lower = bounds[:, 0]
            upper = bounds[:, 1]
        
        if method == 'clip':
            bounded = xp.clip(positions, lower, upper)
        
        elif method == 'reflect':
            # Reflect at boundaries
            range_size = upper - lower
            
            # Normalize to [0, 1]
            normalized = (positions - lower) / range_size
            
            # Reflect
            reflected = xp.abs((normalized + 1) % 2 - 1)
            
            # Scale back
            bounded = reflected * range_size + lower
        
        elif method == 'wrap':
            # Wrap around boundaries
            range_size = upper - lower
            bounded = ((positions - lower) % range_size) + lower
        
        else:
            raise ValueError(f"Unknown boundary method: {method}")
        
        return self.to_host(bounded)
    
    # Utility operations
    
    def calculate_diversity(self, population: np.ndarray) -> float:
        """
        Calculate population diversity as average distance from centroid.
        
        Args:
            population: Population array
        
        Returns:
            Diversity measure
        """
        xp = self.array_module
        population = self.to_device(population)
        
        centroid = xp.mean(population, axis=0)
        distances = xp.sqrt(xp.sum((population - centroid)**2, axis=1))
        diversity = xp.mean(distances)
        
        return float(self.to_host(diversity))
    
    def find_nearest_neighbors(
        self,
        points: np.ndarray,
        k: int = 5,
        exclude_self: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Find k-nearest neighbors for each point.
        
        Args:
            points: Array of points
            k: Number of neighbors
            exclude_self: Whether to exclude self from neighbors
        
        Returns:
            Indices and distances of nearest neighbors
        """
        distances = self.euclidean_distances_matrix(points)
        
        xp = self.array_module
        distances = self.to_device(distances)
        
        if exclude_self:
            # Set diagonal to infinity
            xp.fill_diagonal(distances, xp.inf)
        
        # Find k nearest
        k = min(k, len(points) - (1 if exclude_self else 0))
        
        # Use partition for efficiency
        indices = xp.argpartition(distances, k, axis=1)[:, :k]
        
        # Get actual sorted indices
        row_indices = xp.arange(len(points))[:, None]
        neighbor_distances = distances[row_indices, indices]
        sorted_idx = xp.argsort(neighbor_distances, axis=1)
        
        indices = indices[row_indices, sorted_idx]
        neighbor_distances = neighbor_distances[row_indices, sorted_idx]
        
        return self.to_host(indices), self.to_host(neighbor_distances)
    
    def parallel_sort(
        self,
        values: np.ndarray,
        indices: Optional[np.ndarray] = None,
        descending: bool = False
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Parallel sorting of values with indices.
        
        Args:
            values: Values to sort
            indices: Optional indices to sort along
            descending: Whether to sort in descending order
        
        Returns:
            Sorted values and indices
        """
        xp = self.array_module
        values = self.to_device(values)
        
        if indices is None:
            indices = xp.arange(len(values))
        else:
            indices = self.to_device(indices)
        
        # Sort
        sorted_idx = xp.argsort(values)
        
        if descending:
            sorted_idx = sorted_idx[::-1]
        
        sorted_values = values[sorted_idx]
        sorted_indices = indices[sorted_idx]
        
        return self.to_host(sorted_values), self.to_host(sorted_indices)


# Standalone optimized functions using Numba

@jit(nopython=True, parallel=True, cache=True)
def fast_matrix_vector_multiply(matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
    """
    Fast matrix-vector multiplication using Numba.
    
    Args:
        matrix: Matrix of shape (m, n)
        vector: Vector of shape (n,)
    
    Returns:
        Result vector of shape (m,)
    """
    m, n = matrix.shape
    result = np.zeros(m)
    
    for i in prange(m):
        for j in range(n):
            result[i] += matrix[i, j] * vector[j]
    
    return result


@jit(nopython=True, parallel=True, cache=True)
def fast_elementwise_operation(
    arr1: np.ndarray,
    arr2: np.ndarray,
    operation: str = 'add'
) -> np.ndarray:
    """
    Fast element-wise operations using Numba.
    
    Args:
        arr1: First array
        arr2: Second array
        operation: Operation type ('add', 'multiply', 'subtract', 'divide')
    
    Returns:
        Result array
    """
    result = np.empty_like(arr1)
    
    for i in prange(arr1.size):
        if operation == 'add':
            result.flat[i] = arr1.flat[i] + arr2.flat[i]
        elif operation == 'multiply':
            result.flat[i] = arr1.flat[i] * arr2.flat[i]
        elif operation == 'subtract':
            result.flat[i] = arr1.flat[i] - arr2.flat[i]
        elif operation == 'divide':
            result.flat[i] = arr1.flat[i] / (arr2.flat[i] + 1e-10)
    
    return result


@jit(nopython=True, cache=True)
def fast_cumulative_sum(arr: np.ndarray) -> np.ndarray:
    """
    Fast cumulative sum using Numba.
    
    Args:
        arr: Input array
    
    Returns:
        Cumulative sum array
    """
    result = np.empty_like(arr)
    result[0] = arr[0]
    
    for i in range(1, len(arr)):
        result[i] = result[i-1] + arr[i]
    
    return result


# Batch operations for VRP-specific calculations

class VRPVectorizedOps:
    """Vectorized operations specific to Vehicle Routing Problems."""
    
    @staticmethod
    def calculate_route_distances_batch(
        routes: List[List[int]],
        distance_matrix: np.ndarray
    ) -> np.ndarray:
        """
        Calculate distances for multiple routes in batch.
        
        Args:
            routes: List of routes (each route is a list of node indices)
            distance_matrix: Pairwise distance matrix
        
        Returns:
            Array of route distances
        """
        distances = np.zeros(len(routes))
        
        for i, route in enumerate(routes):
            if len(route) > 1:
                # Add depot at start and end if not present
                if route[0] != 0:
                    route = [0] + route
                if route[-1] != 0:
                    route = route + [0]
                
                # Sum distances
                for j in range(len(route) - 1):
                    distances[i] += distance_matrix[route[j], route[j+1]]
        
        return distances
    
    @staticmethod
    @jit(nopython=True, parallel=True)
    def check_capacity_constraints_batch(
        routes: np.ndarray,
        demands: np.ndarray,
        capacity: float
    ) -> np.ndarray:
        """
        Check capacity constraints for multiple routes.
        
        Args:
            routes: Routes array (padded with -1)
            demands: Node demands
            capacity: Vehicle capacity
        
        Returns:
            Boolean array indicating valid routes
        """
        n_routes = routes.shape[0]
        valid = np.ones(n_routes, dtype=np.bool_)
        
        for i in prange(n_routes):
            total_demand = 0.0
            for j in range(routes.shape[1]):
                node = routes[i, j]
                if node == -1:  # Padding
                    break
                if node > 0:  # Not depot
                    total_demand += demands[node]
            
            valid[i] = total_demand <= capacity
        
        return valid