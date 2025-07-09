"""Extended convergence tests for all algorithms.

This module tests that all 18 algorithms show proper convergence behavior
on various VRP instances.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from algorithms import ALGORITHMS  # noqa: E402
from problems.vrp import VRPProblem  # noqa: E402


class TestAlgorithmConvergence:
    """Test suite for algorithm convergence behavior."""
    
    # Test instances of different sizes
    TEST_INSTANCES = {
        'small': 'P-n16-k8',    # 16 nodes
        'medium': 'E-n22-k4',   # 22 nodes
        'large': 'A-n32-k5'     # 32 nodes
    }
    
    # Convergence criteria
    MIN_IMPROVEMENT_RATIO = 0.01  # Minimum 1% improvement expected
    MAX_STAGNATION_RATIO = 0.9   # Maximum 90% of iterations without improvement
    
    @pytest.fixture(scope="class")
    def vrp_problems(self):
        """Load VRP problems for testing."""
        problems = {}
        for size, instance in self.TEST_INSTANCES.items():
            problem = VRPProblem()
            problem.load_instance(instance)
            problems[size] = problem
        return problems
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    @pytest.mark.parametrize("instance_size", ['small', 'medium'])
    def test_algorithm_convergence(self, algo_name, instance_size, vrp_problems):
        """Test that each algorithm shows convergence on different instances."""
        # Skip aliases
        if algo_name in ['hyena', 'flamingo']:
            return
        
        problem = vrp_problems[instance_size]
        AlgoClass = ALGORITHMS[algo_name]
        
        # Configure for convergence test
        pop_size = 20 if instance_size == 'small' else 30
        iterations = 50 if instance_size == 'small' else 100
        
        # Initialize algorithm
        algo = AlgoClass(
            problem=problem,
            population_size=pop_size,
            max_iterations=iterations,
            seed=42  # Fixed seed for reproducibility
        )
        
        # Run algorithm
        algo.initialize_population()
        best_solution = algo.run(iterations=iterations)
        
        # Get convergence curve
        curve = algo.get_convergence_curve()
        
        # Test 1: Convergence curve has correct length
        assert len(curve) == iterations + 1, \
            f"{algo_name} convergence curve length mismatch"
        
        # Test 2: All values are valid (finite and positive)
        assert all(np.isfinite(v) and v > 0 for v in curve), \
            f"{algo_name} has invalid values in convergence curve"
        
        # Test 3: Initial and final fitness
        initial_fitness = curve[0]
        final_fitness = curve[-1]
        
        assert final_fitness <= initial_fitness, \
            f"{algo_name} final fitness worse than initial"
        
        # Test 4: Improvement ratio
        improvement = (initial_fitness - final_fitness) / initial_fitness
        assert improvement >= self.MIN_IMPROVEMENT_RATIO, \
            f"{algo_name} improvement {improvement:.2%} below minimum {self.MIN_IMPROVEMENT_RATIO:.0%}"
        
        # Test 5: Check for stagnation
        stagnation_count = 0
        best_so_far = curve[0]
        
        for fitness in curve[1:]:
            if fitness >= best_so_far - 1e-6:  # No improvement
                stagnation_count += 1
            else:
                best_so_far = fitness
                stagnation_count = 0  # Reset on improvement
        
        stagnation_ratio = stagnation_count / iterations
        assert stagnation_ratio <= self.MAX_STAGNATION_RATIO, \
            f"{algo_name} stagnated for {stagnation_ratio:.0%} of iterations"
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_algorithm_monotonic_improvement(self, algo_name, vrp_problems):
        """Test that best fitness never increases (monotonic improvement)."""
        # Skip aliases
        if algo_name in ['hyena', 'flamingo']:
            return
        
        problem = vrp_problems['small']
        AlgoClass = ALGORITHMS[algo_name]
        
        # Quick test with small population
        algo = AlgoClass(
            problem=problem,
            population_size=10,
            max_iterations=20,
            seed=123
        )
        
        # Run algorithm
        algo.initialize_population()
        algo.run(iterations=20)
        
        # Check monotonic improvement
        curve = algo.get_convergence_curve()
        
        for i in range(1, len(curve)):
            assert curve[i] <= curve[i-1] + 1e-6, \
                f"{algo_name} fitness increased at iteration {i}: {curve[i-1]} -> {curve[i]}"
    
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_algorithm_different_seeds(self, algo_name, vrp_problems):
        """Test that algorithms with different seeds produce different trajectories."""
        # Skip aliases
        if algo_name in ['hyena', 'flamingo']:
            return
        
        problem = vrp_problems['small']
        AlgoClass = ALGORITHMS[algo_name]
        
        curves = []
        seeds = [42, 123, 999]
        
        for seed in seeds:
            algo = AlgoClass(
                problem=problem,
                population_size=10,
                max_iterations=20,
                seed=seed
            )
            
            algo.initialize_population()
            algo.run(iterations=20)
            curves.append(algo.get_convergence_curve())
        
        # Check that at least one pair of curves differs
        all_identical = True
        for i in range(len(curves)):
            for j in range(i+1, len(curves)):
                if curves[i] != curves[j]:
                    all_identical = False
                    break
            if not all_identical:
                break
        
        assert not all_identical, \
            f"{algo_name} produces identical results with different seeds"
    
    @pytest.mark.parametrize("algo_name", ['ewa', 'opa', 'sma', 'woa', 'hho'])
    def test_top_algorithms_performance(self, algo_name, vrp_problems):
        """Test that top algorithms achieve good performance."""
        problem = vrp_problems['medium']
        AlgoClass = ALGORITHMS[algo_name]
        
        # Run with good parameters
        algo = AlgoClass(
            problem=problem,
            population_size=50,
            max_iterations=200,
            seed=42
        )
        
        algo.initialize_population()
        best_solution = algo.run(iterations=200)
        
        # These algorithms should achieve significant improvement
        curve = algo.get_convergence_curve()
        initial = curve[0]
        final = curve[-1]
        improvement = (initial - final) / initial
        
        # Top algorithms should achieve at least 10% improvement
        assert improvement >= 0.10, \
            f"Top algorithm {algo_name} only achieved {improvement:.1%} improvement"
    
    @pytest.mark.slow
    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys())[:5])  # Test subset
    def test_algorithm_long_run_convergence(self, algo_name, vrp_problems):
        """Test algorithm behavior in longer runs (marked as slow)."""
        # Skip aliases
        if algo_name in ['hyena', 'flamingo']:
            return
        
        problem = vrp_problems['large']
        AlgoClass = ALGORITHMS[algo_name]
        
        # Longer run
        algo = AlgoClass(
            problem=problem,
            population_size=50,
            max_iterations=500,
            seed=42
        )
        
        algo.initialize_population()
        algo.run(iterations=500)
        
        curve = algo.get_convergence_curve()
        
        # Check improvement in different phases
        early_improvement = (curve[0] - curve[100]) / curve[0]
        mid_improvement = (curve[100] - curve[300]) / curve[100]
        late_improvement = (curve[300] - curve[500]) / curve[300]
        
        # Early phase should show most improvement
        assert early_improvement > mid_improvement, \
            f"{algo_name} did not show expected convergence pattern"
        
        # Should still improve in later phases
        assert mid_improvement >= 0, \
            f"{algo_name} got worse in mid phase"
        assert late_improvement >= -0.01, \
            f"{algo_name} got significantly worse in late phase"


if __name__ == "__main__":
    # Run without slow tests by default
    pytest.main([__file__, "-v", "-m", "not slow"])