"""Shared test fixtures and utilities for BioAlgoCompare tests.

This module contains common test utilities, mock classes, and fixtures
used across multiple test files to avoid code duplication.
"""

import numpy as np
from typing import Optional, List, Tuple, Union
from problems.vrp import VRPProblem


class MockProblem:
    """Mock problem class for algorithm testing.
    
    Provides a simple optimization problem interface for testing
    metaheuristic algorithms without requiring actual problem instances.
    """
    
    def __init__(self, dimension: int = 5, optimal_value: Optional[float] = None):
        """Initialize mock problem.
        
        Args:
            dimension: Problem dimension
            optimal_value: Known optimal value (for gap calculations)
        """
        self.dimension = dimension
        self.optimal_value = optimal_value
        self.eval_count = 0
        self.best_solution_seen = None
        self.best_fitness_seen = float('inf')
        
    def get_dimension(self) -> int:
        """Get problem dimension."""
        return self.dimension
    
    def evaluate(self, solution: np.ndarray) -> float:
        """Evaluate a solution.
        
        Simple test function: sum of squared differences from [0.5, 0.5, ...]
        Optimal solution is [0.5, 0.5, ...] with fitness 0.0
        
        Args:
            solution: Solution vector
            
        Returns:
            Fitness value (lower is better)
        """
        self.eval_count += 1
        
        # Simple quadratic function with optimum at center
        fitness = np.sum((solution - 0.5) ** 2)
        
        # Track best solution seen
        if fitness < self.best_fitness_seen:
            self.best_fitness_seen = fitness
            self.best_solution_seen = solution.copy()
            
        return fitness
    
    def is_feasible(self, solution: np.ndarray) -> bool:
        """Check if solution is feasible.
        
        Args:
            solution: Solution vector
            
        Returns:
            True if feasible (always True for mock problem)
        """
        return np.all((solution >= 0) & (solution <= 1))
    
    def reset_eval_count(self):
        """Reset evaluation counter."""
        self.eval_count = 0
        self.best_solution_seen = None
        self.best_fitness_seen = float('inf')


class MockVRPProblem(VRPProblem):
    """Mock VRP problem for testing VRP-specific algorithms.
    
    Provides a simple VRP instance without loading from file.
    """
    
    def __init__(self, n_customers: int = 5, capacity: int = 100, seed: int = 42):
        """Initialize mock VRP problem.
        
        Args:
            n_customers: Number of customers (excluding depot)
            capacity: Vehicle capacity
            seed: Random seed for reproducibility
        """
        super().__init__(instance_path=None, seed=seed)
        
        # Set problem parameters
        self.dimension = n_customers + 1  # +1 for depot
        self.capacity = capacity
        self.depot_index = 0
        
        # Generate random nodes
        np.random.seed(seed)
        self.nodes = [(0, 0)]  # Depot at origin
        for _ in range(n_customers):
            x = np.random.uniform(-50, 50)
            y = np.random.uniform(-50, 50)
            self.nodes.append((x, y))
        
        # Generate random demands
        self.demands = [0]  # No demand at depot
        for _ in range(n_customers):
            demand = np.random.randint(10, 30)
            self.demands.append(demand)
        
        # Compute distance matrix
        self.compute_distance_matrix()
        
        # Set optimal value (unknown for random instance)
        self.optimal_value = None


class AlgorithmTestHelper:
    """Helper class for testing metaheuristic algorithms."""
    
    @staticmethod
    def verify_convergence(convergence_curve: List[float], 
                         tolerance: float = 0.01) -> bool:
        """Verify that algorithm shows convergence behavior.
        
        Args:
            convergence_curve: List of fitness values over iterations
            tolerance: Minimum improvement to consider convergence
            
        Returns:
            True if algorithm shows convergence
        """
        if len(convergence_curve) < 2:
            return False
        
        # Check overall improvement
        initial_fitness = convergence_curve[0]
        final_fitness = convergence_curve[-1]
        improvement = initial_fitness - final_fitness
        
        # Should show some improvement
        if improvement < tolerance:
            return False
        
        # Check monotonic non-increasing (allowing plateaus)
        for i in range(1, len(convergence_curve)):
            if convergence_curve[i] > convergence_curve[i-1] + tolerance:
                return False
        
        return True
    
    @staticmethod
    def verify_population_diversity(population: List, 
                                  min_diversity: float = 0.01) -> bool:
        """Verify that population maintains diversity.
        
        Args:
            population: List of individuals
            min_diversity: Minimum average pairwise distance
            
        Returns:
            True if population is diverse enough
        """
        if len(population) < 2:
            return True
        
        positions = [ind.position for ind in population]
        n = len(positions)
        
        # Calculate average pairwise distance
        total_distance = 0
        count = 0
        
        for i in range(n):
            for j in range(i + 1, n):
                distance = np.linalg.norm(positions[i] - positions[j])
                total_distance += distance
                count += 1
        
        avg_distance = total_distance / count if count > 0 else 0
        return avg_distance >= min_diversity
    
    @staticmethod
    def generate_test_cases(problem_dims: List[int] = [5, 10, 20],
                          pop_sizes: List[int] = [10, 30],
                          max_iters: List[int] = [50, 100]) -> List[dict]:
        """Generate test case configurations.
        
        Args:
            problem_dims: List of problem dimensions to test
            pop_sizes: List of population sizes to test
            max_iters: List of iteration counts to test
            
        Returns:
            List of test configurations
        """
        test_cases = []
        
        for dim in problem_dims:
            for pop_size in pop_sizes:
                for max_iter in max_iters:
                    test_cases.append({
                        'dimension': dim,
                        'population_size': pop_size,
                        'max_iterations': max_iter,
                        'seed': 42  # Fixed seed for reproducibility
                    })
        
        return test_cases


def assert_solution_quality(solution: np.ndarray, problem: MockProblem,
                          max_fitness: float = 1.0):
    """Assert that solution meets quality standards.
    
    Args:
        solution: Solution vector
        problem: Problem instance
        max_fitness: Maximum acceptable fitness
    """
    assert solution is not None, "Solution should not be None"
    assert len(solution) == problem.dimension, "Solution dimension mismatch"
    assert problem.is_feasible(solution), "Solution should be feasible"
    
    fitness = problem.evaluate(solution)
    assert fitness <= max_fitness, f"Fitness {fitness} exceeds threshold {max_fitness}"


def create_benchmark_problems(n_problems: int = 3, 
                            dimension_range: Tuple[int, int] = (5, 20),
                            seed: int = 42) -> List[MockProblem]:
    """Create a set of benchmark problems for testing.
    
    Args:
        n_problems: Number of problems to create
        dimension_range: Range of dimensions (min, max)
        seed: Random seed
        
    Returns:
        List of mock problems
    """
    np.random.seed(seed)
    problems = []
    
    for i in range(n_problems):
        dim = np.random.randint(dimension_range[0], dimension_range[1] + 1)
        # Optimal value is 0 for our quadratic function
        problem = MockProblem(dimension=dim, optimal_value=0.0)
        problems.append(problem)
    
    return problems