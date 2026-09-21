"""
Comprehensive tests for all metaheuristic algorithms.

This module provides systematic testing for all algorithms to ensure:
1. Proper initialization
2. Convergence behavior
3. Basic functionality
4. Reproducibility with seeds
"""
import pytest
import numpy as np
from algorithms import ALGORITHMS
from problems.vrp import VRPProblem


class TestAllAlgorithms:
    """Test suite that covers all algorithms systematically."""
    
    @pytest.fixture
    def small_vrp_problem(self):
        """Create a small VRP instance for quick testing."""
        problem = VRPProblem()
        problem.load_instance("E-n22-k4")
        return problem
    
    @pytest.fixture
    def tiny_vrp_problem(self):
        """Create a tiny VRP instance for convergence testing."""
        # Manually create a 5-node problem
        problem = VRPProblem()
        problem.dimension = 5
        problem.capacity = 50
        problem.depot_index = 0
        problem.nodes = [(0, 0), (10, 0), (0, 10), (-10, 0), (0, -10)]
        problem.demands = [0, 10, 15, 20, 15]  # Total demand = 60
        problem.compute_distance_matrix()
        problem.name = "tiny-5-node"
        return problem
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_algorithm_initialization(self, algo_name, small_vrp_problem):
        """Test that each algorithm initializes correctly."""
        AlgoClass = ALGORITHMS[algo_name]
        
        # Test with default parameters
        algo = AlgoClass(problem=small_vrp_problem)
        assert algo.problem == small_vrp_problem
        assert algo.population_size > 0
        assert algo.max_iterations > 0
        
        # Test with custom parameters
        algo = AlgoClass(
            problem=small_vrp_problem,
            population_size=20,
            max_iterations=50,
            seed=42
        )
        assert algo.population_size == 20
        assert algo.max_iterations == 50
        assert algo.seed == 42
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_algorithm_population_creation(self, algo_name, small_vrp_problem):
        """Test that each algorithm creates valid initial populations."""
        AlgoClass = ALGORITHMS[algo_name]
        algo = AlgoClass(problem=small_vrp_problem, population_size=10, seed=42)
        
        # Initialize population
        algo.initialize_population()
        
        # Check population was created
        assert hasattr(algo, 'population')
        assert len(algo.population) == 10
        
        # Check individuals have required attributes
        for individual in algo.population:
            assert hasattr(individual, 'fitness')
            if hasattr(individual, 'position'):
                position = individual.position
                # OPA uses route representation
                if algo_name in ['opa']:
                    # Position is a list of routes
                    assert isinstance(position, list)
                    assert all(isinstance(route, list) for route in position)
                else:
                    # Check position is valid for VRP encoding
                    assert len(position) == small_vrp_problem.get_dimension()
                    assert np.all(position >= 0) and np.all(position <= 1)
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_algorithm_single_iteration(self, algo_name, tiny_vrp_problem):
        """Test that each algorithm can perform a single iteration."""
        AlgoClass = ALGORITHMS[algo_name]
        algo = AlgoClass(
            problem=tiny_vrp_problem, 
            population_size=10, 
            max_iterations=1,
            seed=42
        )
        
        # Run one iteration
        algo.run()
        
        # Check convergence curve
        assert hasattr(algo, 'convergence_curve')
        assert len(algo.convergence_curve) >= 1
        
        # Check best solution
        best_solution = algo.get_best_solution()
        assert best_solution is not None
        
        # For VRP, check solution validity
        if hasattr(best_solution, 'position'):
            assert tiny_vrp_problem.is_valid(best_solution.position)
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_algorithm_convergence(self, algo_name, tiny_vrp_problem):
        """Test that algorithms show convergence behavior."""
        AlgoClass = ALGORITHMS[algo_name]
        algo = AlgoClass(
            problem=tiny_vrp_problem,
            population_size=10,
            max_iterations=20,
            seed=42
        )
        
        # Run algorithm
        algo.run()
        
        # Get convergence curve
        convergence = algo.get_convergence_curve()
        assert len(convergence) >= 20
        
        # Check that fitness doesn't get worse
        # Allow small tolerance for stochastic algorithms
        for i in range(1, len(convergence)):
            assert convergence[i] <= convergence[i-1] * 1.01
        
        # Check some improvement occurred (at least 1% or stayed same)
        initial_fitness = convergence[0]
        final_fitness = convergence[-1]
        assert final_fitness <= initial_fitness
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_algorithm_reproducibility(self, algo_name, tiny_vrp_problem):
        """Test that algorithms with same seed produce same results."""
        AlgoClass = ALGORITHMS[algo_name]
        seed = 12345
        
        # Run algorithm twice with same seed
        algo1 = AlgoClass(
            problem=tiny_vrp_problem,
            population_size=5,
            max_iterations=5,
            seed=seed
        )
        algo1.run()
        convergence1 = algo1.get_convergence_curve()
        
        algo2 = AlgoClass(
            problem=tiny_vrp_problem,
            population_size=5,
            max_iterations=5,
            seed=seed
        )
        algo2.run()
        convergence2 = algo2.get_convergence_curve()
        
        # Check convergence curves are identical
        assert len(convergence1) == len(convergence2)
        assert np.allclose(convergence1, convergence2)
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_algorithm_best_solution_tracking(self, algo_name, tiny_vrp_problem):
        """Test that algorithms properly track best solution."""
        AlgoClass = ALGORITHMS[algo_name]
        algo = AlgoClass(
            problem=tiny_vrp_problem,
            population_size=10,
            max_iterations=10,
            seed=42
        )
        
        algo.run()
        
        # Get best solution
        best_solution = algo.get_best_solution()
        assert best_solution is not None
        
        # Check best solution matches final convergence value
        final_fitness = algo.get_convergence_curve()[-1]
        
        # For algorithms that return Individual objects
        if hasattr(best_solution, 'fitness'):
            if callable(best_solution.fitness):
                assert best_solution.fitness() == final_fitness
            else:
                assert best_solution.fitness == final_fitness
        # For algorithms that return position directly
        elif isinstance(best_solution, np.ndarray):
            evaluated_fitness = tiny_vrp_problem.evaluate(best_solution)
            assert abs(evaluated_fitness - final_fitness) < 1e-6
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_algorithm_attributes(self, algo_name, tiny_vrp_problem):
        """Test that algorithms have expected attributes after initialization."""
        AlgoClass = ALGORITHMS[algo_name]
        algo = AlgoClass(problem=tiny_vrp_problem, seed=42)
        
        # Check required attributes
        assert hasattr(algo, 'problem')
        assert hasattr(algo, 'population_size')
        assert hasattr(algo, 'max_iterations')
        assert hasattr(algo, 'seed')
        assert hasattr(algo, 'convergence_curve')
        
        # Check required methods
        assert hasattr(algo, 'initialize_population')
        assert hasattr(algo, 'update_population')
        assert hasattr(algo, 'run')
        assert hasattr(algo, 'get_best_solution')
        assert hasattr(algo, 'get_convergence_curve')
        
        # All methods should be callable
        assert callable(algo.initialize_population)
        assert callable(algo.update_population)
        assert callable(algo.run)
        assert callable(algo.get_best_solution)
        assert callable(algo.get_convergence_curve)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])