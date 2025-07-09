"""
Adapters for using different problem types with metaheuristic algorithms.
These adapters provide seamless integration between continuous algorithms
and discrete/constrained problems.
"""

import numpy as np
from typing import Optional, Callable, Any
from problems.base import AbstractProblem, ContinuousProblem, LegacyAbstractProblem
from problems.discrete.base import DiscreteOptimizationProblem


class ContinuousAdapter(LegacyAbstractProblem):
    """
    Adapter to use new problem types with existing algorithms.
    
    This adapter wraps any AbstractProblem to provide the legacy
    interface expected by existing v2 algorithms.
    """
    
    def __init__(self, problem: AbstractProblem):
        """
        Initialize adapter with a problem instance.
        
        Args:
            problem: Problem to adapt
        """
        super().__init__(problem.name)
        self.wrapped_problem = problem
        
        # Set dimension
        self._dimension = problem.dimension
        
        # Set bounds based on problem type
        if isinstance(problem, ContinuousProblem):
            self._lower_bounds = problem.lower_bounds
            self._upper_bounds = problem.upper_bounds
        else:
            # For discrete problems, use [0, 1] bounds
            self._lower_bounds = np.zeros(self._dimension)
            self._upper_bounds = np.ones(self._dimension)
    
    @property
    def dimension(self) -> int:
        """Get problem dimension."""
        return self._dimension
    
    @property
    def lower_bounds(self) -> np.ndarray:
        """Get lower bounds."""
        return self._lower_bounds
    
    @property
    def upper_bounds(self) -> np.ndarray:
        """Get upper bounds."""
        return self._upper_bounds
    
    def evaluate(self, solution: np.ndarray) -> float:
        """
        Evaluate a solution.
        
        Args:
            solution: Solution vector
            
        Returns:
            Fitness value
        """
        if isinstance(self.wrapped_problem, ContinuousProblem):
            return self.wrapped_problem.evaluate(solution)
        elif isinstance(self.wrapped_problem, DiscreteOptimizationProblem):
            return self.wrapped_problem.evaluate_continuous(solution)
        else:
            # Generic case - assume continuous
            return self.wrapped_problem.evaluate(solution)
    
    def _evaluate_impl(self, solution: np.ndarray) -> float:
        """Internal evaluation (for ContinuousProblem compatibility)."""
        return self.evaluate(solution)
    
    def is_feasible(self, solution: np.ndarray) -> bool:
        """Check solution feasibility."""
        if isinstance(self.wrapped_problem, ContinuousProblem):
            return self.wrapped_problem.is_feasible(solution)
        elif isinstance(self.wrapped_problem, DiscreteOptimizationProblem):
            return self.wrapped_problem.is_feasible_continuous(solution)
        else:
            # Default bounds check
            return super().is_feasible(solution)
    
    # Additional methods for full compatibility
    def get_dimension(self) -> int:
        """Legacy method for getting dimension."""
        return self.dimension
    
    def get_lower_bounds(self) -> np.ndarray:
        """Legacy method for getting lower bounds."""
        return self.lower_bounds
    
    def get_upper_bounds(self) -> np.ndarray:
        """Legacy method for getting upper bounds."""
        return self.upper_bounds


class DiscreteAdapter(DiscreteOptimizationProblem):
    """
    Adapter to use continuous algorithms with discrete problems.
    
    This adapter handles the conversion between continuous
    representations (used by algorithms) and discrete
    representations (natural for the problem).
    """
    
    def __init__(
        self,
        problem: DiscreteOptimizationProblem,
        encoding: str = 'random_keys'
    ):
        """
        Initialize discrete adapter.
        
        Args:
            problem: Discrete problem to adapt
            encoding: Encoding method ('random_keys', 'binary', etc.)
        """
        super().__init__(problem.name, problem.dimension)
        self.wrapped_problem = problem
        self.encoding = encoding
        
        # Copy best known value if available
        self._best_known = problem.best_known_value
    
    def encode_continuous(self, continuous: np.ndarray) -> Any:
        """Delegate to wrapped problem."""
        return self.wrapped_problem.encode_continuous(continuous)
    
    def decode_to_continuous(self, discrete: Any) -> np.ndarray:
        """Delegate to wrapped problem."""
        return self.wrapped_problem.decode_to_continuous(discrete)
    
    @property
    def search_space_size(self) -> int:
        """Delegate to wrapped problem."""
        return self.wrapped_problem.search_space_size
    
    def evaluate(self, solution: Any) -> float:
        """Delegate to wrapped problem."""
        return self.wrapped_problem.evaluate(solution)
    
    def is_feasible(self, solution: Any) -> bool:
        """Delegate to wrapped problem."""
        return self.wrapped_problem.is_feasible(solution)
    
    def random_solution(self) -> Any:
        """Delegate to wrapped problem."""
        return self.wrapped_problem.random_solution()


class ConstraintHandler:
    """
    Handles constraints for optimization problems.
    
    Provides different constraint handling methods like
    penalty functions, repair operators, etc.
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        method: str = 'penalty',
        penalty_factor: float = 1e6
    ):
        """
        Initialize constraint handler.
        
        Args:
            problem: Problem with constraints
            method: Constraint handling method
            penalty_factor: Penalty multiplier
        """
        self.problem = problem
        self.method = method
        self.penalty_factor = penalty_factor
    
    def handle(self, solution: np.ndarray, fitness: float) -> float:
        """
        Apply constraint handling to fitness value.
        
        Args:
            solution: Solution to check
            fitness: Original fitness
            
        Returns:
            Modified fitness with constraints
        """
        if self.method == 'penalty':
            return self._penalty_method(solution, fitness)
        elif self.method == 'repair':
            return self._repair_method(solution, fitness)
        else:
            return fitness
    
    def _penalty_method(self, solution: np.ndarray, fitness: float) -> float:
        """Apply penalty for constraint violations."""
        if self.problem.is_feasible(solution):
            return fitness
        
        # Calculate violation magnitude
        violation = self._calculate_violation(solution)
        return fitness + self.penalty_factor * violation
    
    def _repair_method(self, solution: np.ndarray, fitness: float) -> float:
        """Repair infeasible solutions."""
        if hasattr(self.problem, 'repair'):
            repaired = self.problem.repair(solution)
            return self.problem.evaluate(repaired)
        return fitness
    
    def _calculate_violation(self, solution: np.ndarray) -> float:
        """Calculate constraint violation magnitude."""
        # Simple bounds violation
        if isinstance(self.problem, ContinuousProblem):
            lower_violation = np.sum(np.maximum(0, self.problem.lower_bounds - solution))
            upper_violation = np.sum(np.maximum(0, solution - self.problem.upper_bounds))
            return lower_violation + upper_violation
        return 1.0  # Binary violation for other cases


class MultiObjectiveAdapter:
    """
    Adapter for multi-objective problems.
    
    Converts multi-objective problems to single-objective
    using various scalarization methods.
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        method: str = 'weighted_sum',
        weights: Optional[np.ndarray] = None
    ):
        """
        Initialize multi-objective adapter.
        
        Args:
            problem: Multi-objective problem
            method: Scalarization method
            weights: Objective weights
        """
        self.problem = problem
        self.method = method
        self.weights = weights
    
    def scalarize(self, objectives: np.ndarray) -> float:
        """
        Convert multiple objectives to single value.
        
        Args:
            objectives: Array of objective values
            
        Returns:
            Scalarized fitness
        """
        if self.method == 'weighted_sum':
            if self.weights is None:
                # Equal weights
                return np.mean(objectives)
            return np.dot(objectives, self.weights)
        elif self.method == 'tchebycheff':
            if self.weights is None:
                self.weights = np.ones(len(objectives)) / len(objectives)
            # Tchebycheff scalarization
            ideal = np.zeros_like(objectives)  # Assuming minimization
            return np.max(self.weights * np.abs(objectives - ideal))
        else:
            return objectives[0]  # Default to first objective