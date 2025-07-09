"""Unit tests for algorithm initialization.

This module tests that all algorithms can be properly initialized with
various parameter configurations.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from algorithms import ALGORITHMS, get_algorithm  # noqa: E402
from problems.vrp import VRPProblem  # noqa: E402


class TestAlgorithmInitialization:
    """Test suite for algorithm initialization."""
    
    @pytest.fixture
    def vrp_problem(self):
        """Create a simple VRP problem for testing."""
        problem = VRPProblem()
        # Use a small instance for quick tests
        problem.load_instance('P-n16-k8')
        return problem
    
    def test_all_algorithms_in_registry(self):
        """Test that all expected algorithms are in the registry."""
        expected_algorithms = [
            'aha', 'apo', 'egto', 'ewa', 'fgo', 'foa', 'fsa', 'gto', 
            'gvoa', 'hho', 'hoa', 'mrfo', 'opa', 'rro', 'sho', 'sma', 
            'smo', 'woa'
        ]
        
        for algo_name in expected_algorithms:
            assert algo_name in ALGORITHMS, f"Algorithm {algo_name} not found in registry"
    
    def test_algorithm_aliases(self):
        """Test that algorithm aliases work correctly."""
        assert ALGORITHMS['hyena'] == ALGORITHMS['sho']
        assert ALGORITHMS['flamingo'] == ALGORITHMS['fsa']
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_algorithm_initialization_default_params(self, algo_name, vrp_problem):
        """Test each algorithm can be initialized with default parameters."""
        AlgoClass = ALGORITHMS[algo_name]
        
        # Initialize algorithm
        algo = AlgoClass(vrp_problem)
        
        # Check basic attributes
        assert algo.problem == vrp_problem
        # Most algorithms use 30, but some may have different defaults
        assert algo.population_size > 0
        assert algo.max_iterations > 0
        assert algo.seed is None  # default
        
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_algorithm_initialization_custom_params(self, algo_name, vrp_problem):
        """Test each algorithm can be initialized with custom parameters."""
        AlgoClass = ALGORITHMS[algo_name]
        
        # Custom parameters
        pop_size = 50
        max_iter = 200
        seed = 12345
        
        # Initialize algorithm
        algo = AlgoClass(
            problem=vrp_problem,
            population_size=pop_size,
            max_iterations=max_iter,
            seed=seed
        )
        
        # Check custom attributes
        assert algo.problem == vrp_problem
        assert algo.population_size == pop_size
        assert algo.max_iterations == max_iter
        assert algo.seed == seed
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    @pytest.mark.parametrize("pop_size", [1, 10, 30, 100])
    def test_algorithm_initialization_population_sizes(self, algo_name, pop_size, vrp_problem):
        """Test algorithms with different population sizes."""
        AlgoClass = ALGORITHMS[algo_name]
        
        # Initialize with different population size
        algo = AlgoClass(problem=vrp_problem, population_size=pop_size)
        assert algo.population_size == pop_size
        
        # Initialize population
        algo.initialize_population()
        
        # Check population was created with correct size
        assert len(algo.population) == pop_size
        
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_algorithm_initialization_reproducibility(self, algo_name, vrp_problem):
        """Test that algorithms with same seed produce same initial population."""
        AlgoClass = ALGORITHMS[algo_name]
        seed = 42
        
        # Initialize two algorithms with same seed
        algo1 = AlgoClass(problem=vrp_problem, seed=seed)
        algo2 = AlgoClass(problem=vrp_problem, seed=seed)
        
        # Initialize populations
        algo1.initialize_population()
        algo2.initialize_population()
        
        # Check first individual's position is the same
        # Note: Some algorithms might use problem-specific initialization
        if hasattr(algo1.population[0], 'position'):
            pos1 = algo1.population[0].position
            pos2 = algo2.population[0].position
            
            # For numpy arrays
            if hasattr(pos1, 'shape'):
                assert (pos1 == pos2).all(), f"Positions differ for {algo_name} with same seed"
            # For route-based representations (OPA)
            else:
                assert pos1 == pos2, f"Positions differ for {algo_name} with same seed"
    
    def test_get_algorithm_function(self):
        """Test the get_algorithm utility function."""
        # Test valid algorithm names
        for name in ['EWA', 'ewa', 'Ewa']:
            AlgoClass = get_algorithm(name)
            assert AlgoClass == ALGORITHMS['ewa']
        
        # Test invalid algorithm name
        with pytest.raises(ValueError) as excinfo:
            get_algorithm('invalid_algo')
        
        assert "Algorithm 'invalid_algo' not found" in str(excinfo.value)
        assert "Available:" in str(excinfo.value)
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_algorithm_has_required_methods(self, algo_name):
        """Test that algorithm classes have required methods."""
        AlgoClass = ALGORITHMS[algo_name]
        
        # Check for required methods
        assert hasattr(AlgoClass, 'initialize_population')
        assert hasattr(AlgoClass, 'update_population')
        assert hasattr(AlgoClass, 'run')
        assert hasattr(AlgoClass, 'get_best_solution')
        assert hasattr(AlgoClass, 'get_convergence_curve')
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_algorithm_initialization_invalid_params(self, algo_name, vrp_problem):
        """Test algorithm behavior with invalid parameters."""
        AlgoClass = ALGORITHMS[algo_name]
        
        # Test with negative population size (should handle gracefully)
        with pytest.raises((ValueError, AssertionError)):
            algo = AlgoClass(problem=vrp_problem, population_size=-10)
        
        # Test with zero iterations (should handle gracefully)
        with pytest.raises((ValueError, AssertionError)):
            algo = AlgoClass(problem=vrp_problem, max_iterations=0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])