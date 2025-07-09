"""Unit tests for algorithm interface compliance.

This module tests that all Individual and Algorithm classes properly
implement the required base class interfaces.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from algorithms import ALGORITHMS  # noqa: E402
from algorithms.base import Individual, MetaheuristicAlgorithm  # noqa: E402
from problems.vrp import VRPProblem  # noqa: E402


class TestIndividualInterface:
    """Test suite for Individual class interface compliance."""
    
    @pytest.fixture
    def vrp_problem(self):
        """Create a simple VRP problem for testing."""
        problem = VRPProblem()
        problem.load_instance('P-n16-k8')
        return problem
    
    def get_individual_classes(self):
        """Get all Individual classes from algorithms."""
        individual_classes = {
            'aha': 'Hummingbird',
            'apo': 'Protozoa',
            'egto': 'EnhancedGorilla',
            'ewa': 'Earthworm',
            'fgo': 'Flamingo',
            'foa': 'Fossa',
            'fsa': 'Flamingo',
            'gto': 'Gorilla',
            'gvoa': 'Vulture',
            'hho': 'Hawk',
            'hoa': 'Hyena',
            'mrfo': 'MantaRay',
            'opa': 'Orca',
            'rro': 'Raven',
            'sho': 'Hyena',
            'sma': 'SlimeMould',
            'smo': 'Starling',
            'woa': 'Whale'
        }
        return individual_classes
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_individual_inheritance(self, algo_name):
        """Test that Individual classes inherit from base Individual."""
        # Skip aliases
        if algo_name in ['hyena', 'flamingo']:
            return
            
        individual_classes = self.get_individual_classes()
        if algo_name not in individual_classes:
            pytest.skip(f"No Individual class mapping for {algo_name}")
        
        # Import the algorithm module
        module = __import__(f'algorithms.{algo_name}', fromlist=[individual_classes[algo_name]])
        IndividualClass = getattr(module, individual_classes[algo_name])
        
        # Check inheritance
        assert issubclass(IndividualClass, Individual), \
            f"{individual_classes[algo_name]} does not inherit from Individual"
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_individual_has_required_methods(self, algo_name, vrp_problem):
        """Test that Individual classes implement required methods."""
        # Skip aliases
        if algo_name in ['hyena', 'flamingo']:
            return
            
        # Initialize algorithm to get an individual
        AlgoClass = ALGORITHMS[algo_name]
        algo = AlgoClass(vrp_problem)
        algo.initialize_population()
        
        if not algo.population:
            pytest.skip(f"No population created for {algo_name}")
        
        individual = algo.population[0]
        
        # Check required methods exist
        assert hasattr(individual, 'fitness'), f"{algo_name} Individual missing fitness method"
        assert hasattr(individual, 'is_better_than'), f"{algo_name} Individual missing is_better_than method"
        assert hasattr(individual, 'is_feasible'), f"{algo_name} Individual missing is_feasible method"
        assert hasattr(individual, 'move'), f"{algo_name} Individual missing move method"
        assert hasattr(individual, 'copy'), f"{algo_name} Individual missing copy method"
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_fitness_method(self, algo_name, vrp_problem):
        """Test Individual fitness() method returns numeric value."""
        # Skip aliases
        if algo_name in ['hyena', 'flamingo']:
            return
            
        AlgoClass = ALGORITHMS[algo_name]
        algo = AlgoClass(vrp_problem)
        algo.initialize_population()
        
        individual = algo.population[0]
        
        # Test fitness method
        fitness_value = individual.fitness()
        assert isinstance(fitness_value, (int, float)), \
            f"{algo_name} fitness() should return numeric value"
        assert fitness_value >= 0, \
            f"{algo_name} fitness() should return non-negative value for VRP"
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_is_better_than_method(self, algo_name, vrp_problem):
        """Test Individual is_better_than() method."""
        # Skip aliases
        if algo_name in ['hyena', 'flamingo']:
            return
            
        AlgoClass = ALGORITHMS[algo_name]
        algo = AlgoClass(vrp_problem)
        algo.initialize_population()
        
        if len(algo.population) < 2:
            pytest.skip(f"Need at least 2 individuals for {algo_name}")
        
        ind1 = algo.population[0]
        ind2 = algo.population[1]
        
        # Test is_better_than method
        result = ind1.is_better_than(ind2)
        assert isinstance(result, bool), \
            f"{algo_name} is_better_than() should return boolean"
        
        # Test consistency: if A is better than B, then B is not better than A
        if result:
            assert not ind2.is_better_than(ind1), \
                f"{algo_name} is_better_than() is not consistent"
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_is_feasible_method(self, algo_name, vrp_problem):
        """Test Individual is_feasible() method."""
        # Skip aliases
        if algo_name in ['hyena', 'flamingo']:
            return
            
        AlgoClass = ALGORITHMS[algo_name]
        algo = AlgoClass(vrp_problem)
        algo.initialize_population()
        
        individual = algo.population[0]
        
        # Test is_feasible method
        result = individual.is_feasible()
        assert isinstance(result, bool), \
            f"{algo_name} is_feasible() should return boolean"
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_copy_method(self, algo_name, vrp_problem):
        """Test Individual copy() method."""
        # Skip aliases
        if algo_name in ['hyena', 'flamingo']:
            return
            
        AlgoClass = ALGORITHMS[algo_name]
        algo = AlgoClass(vrp_problem)
        algo.initialize_population()
        
        if len(algo.population) < 2:
            pytest.skip(f"Need at least 2 individuals for {algo_name}")
        
        ind1 = algo.population[0]
        ind2 = algo.population[1]
        
        # Test copy method - some algorithms return new instance, others modify in place
        # First, test if it accepts other parameter (base interface)
        try:
            result = ind1.copy(ind2)
            # If it returns None, it modified ind1 in place
            if result is None:
                # Check that ind1 now has same fitness as ind2
                assert ind1.fitness() == ind2.fitness(), \
                    f"{algo_name} copy() did not properly copy fitness"
            else:
                # If it returns a new instance
                assert result.fitness() == ind1.fitness(), \
                    f"{algo_name} copy() returned instance with different fitness"
        except TypeError:
            # Some algorithms might have different signature, try without parameter
            result = ind1.copy()
            assert result is not None, f"{algo_name} copy() should return new instance"
            assert result.fitness() == ind1.fitness(), \
                f"{algo_name} copy() returned instance with different fitness"


class TestAlgorithmInterface:
    """Test suite for Algorithm class interface compliance."""
    
    @pytest.fixture
    def vrp_problem(self):
        """Create a simple VRP problem for testing."""
        problem = VRPProblem()
        problem.load_instance('P-n16-k8')
        return problem
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_algorithm_inheritance(self, algo_name):
        """Test that Algorithm classes inherit from MetaheuristicAlgorithm."""
        AlgoClass = ALGORITHMS[algo_name]
        assert issubclass(AlgoClass, MetaheuristicAlgorithm), \
            f"{algo_name} does not inherit from MetaheuristicAlgorithm"
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_algorithm_required_methods(self, algo_name, vrp_problem):
        """Test that Algorithm classes have required methods."""
        AlgoClass = ALGORITHMS[algo_name]
        algo = AlgoClass(vrp_problem)
        
        # Check required methods
        assert hasattr(algo, 'initialize_population'), \
            f"{algo_name} missing initialize_population method"
        assert hasattr(algo, 'update_population'), \
            f"{algo_name} missing update_population method"
        assert hasattr(algo, 'run'), \
            f"{algo_name} missing run method"
        assert hasattr(algo, 'get_best_solution'), \
            f"{algo_name} missing get_best_solution method"
        assert hasattr(algo, 'get_convergence_curve'), \
            f"{algo_name} missing get_convergence_curve method"
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_initialize_population(self, algo_name, vrp_problem):
        """Test initialize_population creates correct population."""
        AlgoClass = ALGORITHMS[algo_name]
        algo = AlgoClass(vrp_problem, population_size=10)
        
        # Initialize population
        algo.initialize_population()
        
        # Check population was created
        assert hasattr(algo, 'population'), \
            f"{algo_name} should have population attribute"
        assert len(algo.population) == 10, \
            f"{algo_name} population size mismatch"
        
        # Check best solution is tracked
        assert hasattr(algo, 'best_solution'), \
            f"{algo_name} should track best_solution"
        assert algo.best_solution is not None, \
            f"{algo_name} best_solution should be initialized"
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_update_population(self, algo_name, vrp_problem):
        """Test update_population method execution."""
        AlgoClass = ALGORITHMS[algo_name]
        algo = AlgoClass(vrp_problem, population_size=5, max_iterations=10)
        
        # Initialize population
        algo.initialize_population()
        initial_best = algo.best_solution.fitness()
        
        # Update population once
        algo.update_population()
        
        # Check convergence curve is updated
        assert hasattr(algo, 'convergence_curve'), \
            f"{algo_name} should have convergence_curve"
        assert len(algo.convergence_curve) >= 2, \
            f"{algo_name} convergence_curve should be updated"
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_run_method(self, algo_name, vrp_problem):
        """Test run method executes correctly."""
        AlgoClass = ALGORITHMS[algo_name]
        algo = AlgoClass(vrp_problem, population_size=5, max_iterations=5)
        
        # Run algorithm
        algo.initialize_population()
        best_solution = algo.run(iterations=5)
        
        # Check return value
        assert best_solution is not None, \
            f"{algo_name} run() should return best solution"
        assert hasattr(best_solution, 'fitness'), \
            f"{algo_name} run() should return Individual with fitness method"
        
        # Check convergence curve length
        assert len(algo.convergence_curve) == 6, \
            f"{algo_name} convergence curve length mismatch (expected 6, got {len(algo.convergence_curve)})"
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_get_best_solution(self, algo_name, vrp_problem):
        """Test get_best_solution method."""
        AlgoClass = ALGORITHMS[algo_name]
        algo = AlgoClass(vrp_problem, population_size=5)
        
        # Initialize and run briefly
        algo.initialize_population()
        algo.run(iterations=2)
        
        # Get best solution
        best = algo.get_best_solution()
        
        assert best is not None, \
            f"{algo_name} get_best_solution() should return solution"
        assert hasattr(best, 'fitness'), \
            f"{algo_name} get_best_solution() should return Individual"
        assert callable(best.fitness), \
            f"{algo_name} best solution should have callable fitness method"
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_get_convergence_curve(self, algo_name, vrp_problem):
        """Test get_convergence_curve method."""
        AlgoClass = ALGORITHMS[algo_name]
        algo = AlgoClass(vrp_problem, population_size=5)
        
        # Initialize and run
        algo.initialize_population()
        algo.run(iterations=3)
        
        # Get convergence curve
        curve = algo.get_convergence_curve()
        
        assert isinstance(curve, list), \
            f"{algo_name} get_convergence_curve() should return list"
        assert len(curve) == 4, \
            f"{algo_name} convergence curve length mismatch"
        assert all(isinstance(v, (int, float)) for v in curve), \
            f"{algo_name} convergence curve should contain numeric values"
        
        # Check convergence (best fitness should not increase)
        for i in range(1, len(curve)):
            assert curve[i] <= curve[i-1] + 1e-6, \
                f"{algo_name} fitness increased during optimization"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])