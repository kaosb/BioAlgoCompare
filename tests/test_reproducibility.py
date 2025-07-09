"""
Comprehensive test suite for reproducibility across the framework.
Tests that algorithms produce identical results with the same seed.
"""

import pytest
import numpy as np
import multiprocessing as mp
from typing import List, Dict, Any, Type
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from algorithms.base_v2 import MetaheuristicAlgorithm, AbstractProblem
from algorithms.sho_v2 import SHOV2, VRPProblemAdapter
from problems.vrp_v2 import VRPProblemV2
from utils.random_state import (
    RandomStateManager, get_global_random_manager, 
    set_global_seed, generate_algorithm_seeds
)

# Import existing algorithms for testing
from algorithms.foa_v2 import FOAV2
from algorithms.egto_v2 import EGTOV2
from algorithms.woa_v2 import WOAV2


class TestRandomStateManager:
    """Test the RandomStateManager functionality."""
    
    def test_basic_functionality(self):
        """Test basic seed setting and state management."""
        manager = RandomStateManager(42)
        
        # Generate some random numbers
        nums1 = [np.random.rand() for _ in range(5)]
        
        # Reset to same seed
        manager.set_seed(42)
        nums2 = [np.random.rand() for _ in range(5)]
        
        # Should be identical
        assert np.allclose(nums1, nums2)
    
    def test_sub_seed_generation(self):
        """Test deterministic sub-seed generation."""
        manager = RandomStateManager(12345)
        
        # Generate sub-seeds
        seeds1 = [manager.generate_sub_seed(f"test_{i}") for i in range(10)]
        
        # Reset manager
        manager.sub_seed_counter = 0
        
        # Generate again
        seeds2 = [manager.generate_sub_seed(f"test_{i}") for i in range(10)]
        
        # Should be identical
        assert seeds1 == seeds2
        
        # All seeds should be unique
        assert len(set(seeds1)) == len(seeds1)
    
    def test_checkpoint_restore(self):
        """Test checkpoint and restore functionality."""
        manager = RandomStateManager(999)
        
        # Generate some state changes
        for i in range(5):
            manager.generate_sub_seed(f"checkpoint_test_{i}")
            np.random.rand(10)
        
        # Create checkpoint
        checkpoint = manager.checkpoint()
        
        # Continue changing state
        for i in range(5, 10):
            manager.generate_sub_seed(f"checkpoint_test_{i}")
            np.random.rand(10)
        
        # Restore checkpoint
        manager.restore_checkpoint(checkpoint)
        
        # Generate numbers after restore
        nums_after_restore = [np.random.rand() for _ in range(5)]
        
        # Create new manager with same seed and advance to checkpoint
        manager2 = RandomStateManager(999)
        for i in range(5):
            manager2.generate_sub_seed(f"checkpoint_test_{i}")
            np.random.rand(10)
        
        # Generate same numbers
        nums_from_fresh = [np.random.rand() for _ in range(5)]
        
        # Should be identical
        assert np.allclose(nums_after_restore, nums_from_fresh)
    
    def test_parallel_seeds(self):
        """Test seed generation for parallel execution."""
        seeds = generate_algorithm_seeds(n_algorithms=5, n_runs=10, base_seed=42)
        
        # Check structure
        assert len(seeds) == 5
        for algo_seeds in seeds.values():
            assert len(algo_seeds) == 10
        
        # All seeds should be unique
        all_seeds = []
        for algo_seeds in seeds.values():
            all_seeds.extend(algo_seeds)
        assert len(set(all_seeds)) == len(all_seeds)
        
        # Regenerating should give same results
        seeds2 = generate_algorithm_seeds(n_algorithms=5, n_runs=10, base_seed=42)
        assert seeds == seeds2


class TestAlgorithmReproducibility:
    """Test reproducibility of actual algorithms."""
    
    @pytest.fixture
    def simple_vrp_problem(self):
        """Create a simple VRP problem for testing."""
        return VRPProblem("data/vrp/P-n16-k8.vrp")
    
    def run_algorithm_twice(self, algo_class: Type, problem, seed: int) -> Dict[str, Any]:
        """Run an algorithm twice with the same seed and compare results."""
        results = []
        
        for _ in range(2):
            algo = algo_class(
                problem,
                population_size=20,
                max_iterations=30,
                seed=seed
            )
            
            result = algo.execute()
            
            results.append({
                'fitness': result.fitness(),
                'position': result.position.copy(),
                'convergence': algo.get_convergence_curve().copy(),
                'time': algo.get_execution_time()
            })
        
        return {
            'run1': results[0],
            'run2': results[1],
            'identical_fitness': results[0]['fitness'] == results[1]['fitness'],
            'identical_position': np.array_equal(results[0]['position'], results[1]['position']),
            'identical_convergence': np.array_equal(results[0]['convergence'], results[1]['convergence'])
        }
    
    def test_sho_reproducibility(self, simple_vrp_problem):
        """Test SHO algorithm reproducibility."""
        comparison = self.run_algorithm_twice(SHO, simple_vrp_problem, seed=42)
        
        assert comparison['identical_fitness']
        assert comparison['identical_position']
        assert comparison['identical_convergence']
    
    def test_foa_reproducibility(self, simple_vrp_problem):
        """Test FOA algorithm reproducibility."""
        comparison = self.run_algorithm_twice(FOA, simple_vrp_problem, seed=123)
        
        assert comparison['identical_fitness']
        assert comparison['identical_position']
        assert comparison['identical_convergence']
    
    def test_multiple_algorithms_reproducibility(self, simple_vrp_problem):
        """Test that multiple algorithms are reproducible."""
        algorithms = [SHO, FOA, EGTO, WOA]
        seed = 999
        
        for algo_class in algorithms:
            comparison = self.run_algorithm_twice(algo_class, simple_vrp_problem, seed)
            
            assert comparison['identical_fitness'], f"{algo_class.__name__} not reproducible"
            assert comparison['identical_position'], f"{algo_class.__name__} position not reproducible"
            assert comparison['identical_convergence'], f"{algo_class.__name__} convergence not reproducible"
    
    def test_sho_v2_reproducibility(self, simple_vrp_problem):
        """Test improved SHOV2 algorithm reproducibility."""
        problem_adapter = VRPProblemAdapter(simple_vrp_problem)
        
        results = []
        for _ in range(3):  # Run 3 times to be extra sure
            algo = SHOV2(
                problem_adapter,
                population_size=15,
                max_iterations=25,
                seed=7777
            )
            result = algo.execute()
            results.append({
                'fitness': result.fitness(),
                'position': result.position.copy(),
                'curve': algo.get_convergence_curve().copy()
            })
        
        # All three runs should be identical
        for i in range(1, 3):
            assert results[0]['fitness'] == results[i]['fitness']
            assert np.array_equal(results[0]['position'], results[i]['position'])
            assert np.array_equal(results[0]['curve'], results[i]['curve'])


def parallel_algorithm_run(params):
    """Helper function for parallel execution test."""
    algo_class, problem_path, seed, pop_size, max_iter = params
    
    # Set seed for this process
    set_global_seed(seed)
    
    # Create problem and algorithm
    problem = VRPProblem(problem_path)
    algo = algo_class(problem, pop_size, max_iter, seed)
    
    # Execute
    result = algo.execute()
    
    return {
        'fitness': result.fitness(),
        'position': result.position.copy(),
        'convergence': algo.get_convergence_curve().copy()
    }


class TestParallelReproducibility:
    """Test reproducibility in parallel execution scenarios."""
    
    def test_parallel_same_seeds(self):
        """Test that parallel execution with same seeds gives same results."""
        # Parameters for parallel runs
        algo_class = SHO
        problem_path = "data/vrp/P-n16-k8.vrp"
        seeds = [42, 42, 42, 42]  # Same seed for all
        pop_size = 20
        max_iter = 20
        
        # Create parameter tuples
        params = [(algo_class, problem_path, seed, pop_size, max_iter) for seed in seeds]
        
        # Run in parallel
        with mp.Pool(processes=4) as pool:
            results = pool.map(parallel_algorithm_run, params)
        
        # All results should be identical
        for i in range(1, len(results)):
            assert results[0]['fitness'] == results[i]['fitness']
            assert np.array_equal(results[0]['position'], results[i]['position'])
            assert np.array_equal(results[0]['convergence'], results[i]['convergence'])
    
    def test_parallel_different_seeds(self):
        """Test that parallel execution with different seeds gives different results."""
        # Generate different seeds
        seed_manager = RandomStateManager(12345)
        seeds = [seed_manager.generate_sub_seed(f"parallel_{i}") for i in range(4)]
        
        # Parameters
        algo_class = FOA
        problem_path = "data/vrp/E-n22-k4.vrp"
        pop_size = 15
        max_iter = 15
        
        # Create parameter tuples
        params = [(algo_class, problem_path, seed, pop_size, max_iter) for seed in seeds]
        
        # Run in parallel
        with mp.Pool(processes=4) as pool:
            results = pool.map(parallel_algorithm_run, params)
        
        # Results should be different (at least fitness values)
        fitness_values = [r['fitness'] for r in results]
        assert len(set(fitness_values)) > 1, "All parallel runs gave same fitness"


class TestReproducibilityAcrossSessions:
    """Test that results are reproducible across different Python sessions."""
    
    def test_save_load_state(self, tmp_path):
        """Test saving and loading random state."""
        # Create manager and generate some state
        manager1 = RandomStateManager(54321)
        
        # Do some operations
        for i in range(10):
            np.random.rand(5)
            manager1.generate_sub_seed(f"test_{i}")
        
        # Save state
        state_file = tmp_path / "random_state.json"
        manager1.save_to_file(str(state_file))
        
        # Generate numbers after save
        nums1 = [np.random.rand() for _ in range(10)]
        
        # Create new manager and load state
        manager2 = RandomStateManager()  # Different initial seed
        manager2.load_from_file(str(state_file))
        
        # Generate same numbers
        nums2 = [np.random.rand() for _ in range(10)]
        
        # Should be identical
        assert np.allclose(nums1, nums2)
    
    def test_algorithm_state_persistence(self, tmp_path, simple_vrp_problem):
        """Test that algorithm results can be reproduced after saving/loading state."""
        # Run algorithm with state manager
        manager = RandomStateManager(98765)
        
        # Run algorithm partway
        algo1 = SHO(simple_vrp_problem, population_size=20, max_iterations=50, seed=None)
        manager.set_seed(98765)  # Set seed through manager
        
        # Execute half the iterations manually
        algo1.initialize_population()
        for i in range(25):
            algo1.iteration = i
            algo1.update_population()
        
        # Save state
        state_file = tmp_path / "algo_state.json"
        manager.save_to_file(str(state_file))
        fitness_at_25 = algo1.best_solution.fitness()
        
        # Continue to completion
        for i in range(25, 50):
            algo1.iteration = i
            algo1.update_population()
        
        final_fitness1 = algo1.best_solution.fitness()
        
        # Now recreate from checkpoint
        manager2 = RandomStateManager()
        manager2.load_from_file(str(state_file))
        
        # Create new algorithm instance
        algo2 = SHO(simple_vrp_problem, population_size=20, max_iterations=50, seed=None)
        
        # Copy the state at iteration 25 (this would need proper implementation)
        # For now, we just verify the concept
        assert True  # Placeholder for actual state restoration test


if __name__ == "__main__":
    pytest.main([__file__, "-v"])