"""
Tests for the improved base architecture (base_v2).
Verifies that the new design maintains functionality and improves reproducibility.
"""

import pytest
import numpy as np
from typing import List
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from algorithms.base_v2 import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem
from algorithms.sho_v2 import SHOV2, SpottedHyena, VRPProblemAdapter
from problems.vrp_v2 import VRPProblemV2


class SimpleTestProblem(AbstractProblem):
    """Simple test problem for unit testing."""
    
    def __init__(self, dimension: int = 10):
        super().__init__(f"TestProblem{dimension}D")
        self._dimension = dimension
        self._lower_bounds = np.full(dimension, -10.0)
        self._upper_bounds = np.full(dimension, 10.0)
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    @property
    def lower_bounds(self) -> np.ndarray:
        return self._lower_bounds
    
    @property
    def upper_bounds(self) -> np.ndarray:
        return self._upper_bounds
    
    def evaluate(self, solution: np.ndarray) -> float:
        """Simple sphere function for testing."""
        return np.sum(solution ** 2)


class SimpleIndividual(Individual):
    """Simple individual for testing."""
    
    def initialize(self) -> None:
        self.position = self.problem.random_solution()
    
    def move(self, context: MoveContext) -> None:
        """Simple random walk movement."""
        step = np.random.uniform(-1, 1, self.problem.dimension)
        self.position += step
        self.position = self.problem.repair(self.position)


class SimpleAlgorithm(MetaheuristicAlgorithm[SimpleIndividual]):
    """Simple algorithm for testing base functionality."""
    
    def _create_individual(self) -> SimpleIndividual:
        return SimpleIndividual(self.problem)
    
    def _create_move_context(self) -> MoveContext:
        return super()._create_move_context()


class TestMoveContext:
    """Test the MoveContext class."""
    
    def test_parameter_management(self):
        """Test getting and setting parameters."""
        context = MoveContext(iteration=5, max_iterations=100)
        
        # Test default values
        assert context.get_param('missing') is None
        assert context.get_param('missing', 'default') == 'default'
        
        # Test setting and getting
        context.set_param('alpha', 0.5)
        assert context.get_param('alpha') == 0.5
        
        # Test multiple parameters
        context.set_param('beta', [1, 2, 3])
        context.set_param('gamma', {'key': 'value'})
        assert len(context.algorithm_params) == 3


class TestIndividual:
    """Test the improved Individual base class."""
    
    def test_fitness_caching(self):
        """Test that fitness is properly cached."""
        problem = SimpleTestProblem(5)
        ind = SimpleIndividual(problem)
        ind.initialize()
        
        # First call should calculate
        fitness1 = ind.fitness()
        assert ind._fitness_calculated
        
        # Modify position without invalidating
        original_pos = ind.position.copy()
        ind.position += 1.0
        
        # Should return cached value
        fitness2 = ind.fitness()
        assert fitness1 == fitness2
        
        # Invalidate and recalculate
        ind.invalidate_fitness()
        assert not ind._fitness_calculated
        fitness3 = ind.fitness()
        assert fitness3 != fitness1
    
    def test_clone(self):
        """Test individual cloning."""
        problem = SimpleTestProblem(5)
        ind1 = SimpleIndividual(problem)
        ind1.initialize()
        _ = ind1.fitness()  # Calculate fitness
        
        # Clone
        ind2 = ind1.clone()
        
        # Check independence
        assert np.array_equal(ind1.position, ind2.position)
        assert ind1.fitness() == ind2.fitness()
        assert ind1._fitness_calculated == ind2._fitness_calculated
        
        # Modify clone shouldn't affect original
        ind2.position += 1.0
        assert not np.array_equal(ind1.position, ind2.position)


class TestMetaheuristicAlgorithm:
    """Test the improved MetaheuristicAlgorithm base class."""
    
    def test_initialization(self):
        """Test proper initialization."""
        problem = SimpleTestProblem(10)
        algo = SimpleAlgorithm(problem, population_size=20, max_iterations=50, seed=42)
        
        assert algo.population_size == 20
        assert algo.max_iterations == 50
        assert algo.seed == 42
        assert len(algo.population) == 0
        
    def test_population_initialization(self):
        """Test population initialization."""
        problem = SimpleTestProblem(5)
        algo = SimpleAlgorithm(problem, population_size=10, seed=123)
        
        algo.initialize_population()
        
        assert len(algo.population) == 10
        assert algo.best_solution is not None
        assert len(algo.convergence_curve) == 1
        assert algo.convergence_curve[0] == algo.best_solution.fitness()
        
        # Check population is sorted
        fitnesses = [ind.fitness() for ind in algo.population]
        assert fitnesses == sorted(fitnesses)
    
    def test_reproducibility(self):
        """Test that same seed produces same results."""
        problem = SimpleTestProblem(10)
        
        # Run 1
        algo1 = SimpleAlgorithm(problem, population_size=20, max_iterations=10, seed=999)
        result1 = algo1.execute()
        fitness1 = result1.fitness()
        curve1 = algo1.get_convergence_curve().copy()
        
        # Run 2 with same seed
        algo2 = SimpleAlgorithm(problem, population_size=20, max_iterations=10, seed=999)
        result2 = algo2.execute()
        fitness2 = result2.fitness()
        curve2 = algo2.get_convergence_curve().copy()
        
        # Should be identical
        assert fitness1 == fitness2
        assert np.array_equal(curve1, curve2)
        assert np.array_equal(result1.position, result2.position)
    
    def test_summary(self):
        """Test summary generation."""
        problem = SimpleTestProblem(5)
        algo = SimpleAlgorithm(problem, population_size=10, max_iterations=5, seed=42)
        algo.execute()
        
        summary = algo.summary()
        
        assert summary['algorithm'] == 'SimpleAlgorithm'
        assert summary['problem'] == 'SimpleTestProblem'
        assert summary['population_size'] == 10
        assert summary['iterations'] == 5
        assert summary['seed'] == 42
        assert 'best_fitness' in summary
        assert 'execution_time' in summary
        assert len(summary['convergence_curve']) == 6  # initial + 5 iterations


class TestSHOV2:
    """Test the migrated SHO algorithm."""
    
    def test_with_vrp_adapter(self):
        """Test SHOV2 with VRP problem adapter."""
        # Load VRP problem
        vrp = VRPProblem("data/vrp/P-n16-k8.vrp")
        problem = VRPProblemAdapter(vrp)
        
        # Run algorithm
        algo = SHOV2(problem, population_size=10, max_iterations=10, seed=42)
        result = algo.execute()
        
        assert result is not None
        assert result.fitness() > 0
        assert len(algo.convergence_curve) == 11
        
    def test_leaders_update(self):
        """Test that alpha, beta, delta are properly updated."""
        problem = SimpleTestProblem(5)
        algo = SHOV2(problem, population_size=10, max_iterations=5, seed=42)
        
        algo.initialize_population()
        
        # Check initial leaders
        assert algo.alpha is not None
        assert algo.beta is not None
        assert algo.delta is not None
        assert algo.alpha.fitness() <= algo.beta.fitness()
        assert algo.beta.fitness() <= algo.delta.fitness()
        
        # Run one iteration
        algo.iteration = 0
        algo.update_population()
        
        # Leaders should still be ordered
        assert algo.alpha.fitness() <= algo.beta.fitness()
        assert algo.beta.fitness() <= algo.delta.fitness()
    
    def test_reproducibility_sho(self):
        """Test SHOV2 reproducibility."""
        problem = SimpleTestProblem(10)
        
        # Run twice with same seed
        results = []
        for _ in range(2):
            algo = SHOV2(problem, population_size=15, max_iterations=20, seed=12345)
            result = algo.execute()
            results.append({
                'fitness': result.fitness(),
                'position': result.position.copy(),
                'curve': algo.get_convergence_curve().copy()
            })
        
        # Check identical results
        assert results[0]['fitness'] == results[1]['fitness']
        assert np.array_equal(results[0]['position'], results[1]['position'])
        assert np.array_equal(results[0]['curve'], results[1]['curve'])


class TestAbstractProblem:
    """Test the AbstractProblem base class."""
    
    def test_feasibility_check(self):
        """Test solution feasibility checking."""
        problem = SimpleTestProblem(5)
        
        # Valid solution
        valid = np.zeros(5)
        assert problem.is_feasible(valid)
        
        # Out of bounds
        invalid1 = np.full(5, 20.0)  # Above upper bound
        assert not problem.is_feasible(invalid1)
        
        invalid2 = np.full(5, -20.0)  # Below lower bound
        assert not problem.is_feasible(invalid2)
        
        # Wrong dimension
        invalid3 = np.zeros(3)
        assert not problem.is_feasible(invalid3)
    
    def test_repair(self):
        """Test solution repair."""
        problem = SimpleTestProblem(5)
        
        # Solution with violations
        solution = np.array([15.0, -15.0, 0.0, 5.0, -5.0])
        repaired = problem.repair(solution)
        
        assert np.all(repaired >= problem.lower_bounds)
        assert np.all(repaired <= problem.upper_bounds)
        assert repaired[0] == 10.0  # Clipped to upper bound
        assert repaired[1] == -10.0  # Clipped to lower bound
        assert repaired[2] == 0.0  # No change
    
    def test_random_solution(self):
        """Test random solution generation."""
        problem = SimpleTestProblem(10)
        
        # Generate multiple random solutions
        for _ in range(100):
            solution = problem.random_solution()
            assert problem.is_feasible(solution)
            assert len(solution) == problem.dimension


if __name__ == "__main__":
    pytest.main([__file__, "-v"])