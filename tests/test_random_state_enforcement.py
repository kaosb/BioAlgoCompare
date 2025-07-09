"""
Test that RandomStateManager is properly enforced in algorithms.
"""

import pytest
import numpy as np
from typing import List

from algorithms.base_v2 import Individual, MetaheuristicAlgorithm, MoveContext
from problems.vrp_v2 import VRPProblemV2
from utils.random_state import RandomStateManager


class SimpleIndividual(Individual):
    """Simple test individual for VRP."""
    
    def initialize(self) -> None:
        """Initialize with random position."""
        # For VRP, use continuous position that will be decoded to routes
        self.position = np.random.uniform(0, 1, self.problem.dimension)
        self.invalidate_fitness()
    
    def move(self, context: MoveContext) -> None:
        """Simple random move."""
        self.position += np.random.normal(0, 0.01, self.position.shape)
        # Ensure position stays in bounds
        self.position = np.clip(self.position, 0, 1)
        self.invalidate_fitness()
    
    def fitness(self) -> float:
        """Override fitness to handle VRP decoding."""
        if not self._fitness_calculated:
            # Decode position to routes for VRP
            if hasattr(self.problem, 'decode_continuous'):
                routes = self.problem.decode_continuous(self.position)
                self._fitness = self.problem.evaluate(routes)
            else:
                # For testing, just use sum of position as fitness
                self._fitness = np.sum(self.position)
            self._fitness_calculated = True
        return self._fitness


class SimpleAlgorithm(MetaheuristicAlgorithm[SimpleIndividual]):
    """Simple test algorithm."""
    
    def _create_individual(self) -> SimpleIndividual:
        return SimpleIndividual(self.problem)
    
    def _create_move_context(self) -> MoveContext:
        return MoveContext(
            iteration=self.iteration,
            max_iterations=self.max_iterations,
            population=self.population,
            best_individual=self.best_solution
        )


class TestRandomStateEnforcement:
    """Test suite for random state enforcement."""
    
    @pytest.fixture
    def problem(self):
        """Create a test problem."""
        return VRPProblemV2("data/vrp/A-n32-k5.vrp")
    
    def test_algorithm_has_random_manager(self, problem):
        """Test that algorithms automatically get RandomStateManager."""
        algorithm = SimpleAlgorithm(
            problem=problem,
            population_size=10,
            max_iterations=5,
            seed=42
        )
        
        # Check if algorithm has random_manager attribute
        assert hasattr(algorithm, 'random_manager'), "Algorithm should have random_manager"
        assert isinstance(algorithm.random_manager, RandomStateManager)
        assert algorithm.random_manager.master_seed == 42
    
    def test_reproducibility_with_same_seed(self, problem):
        """Test that same seed produces identical results."""
        # Run algorithm twice with same seed
        alg1 = SimpleAlgorithm(
            problem=problem,
            population_size=10,
            max_iterations=10,
            seed=42
        )
        result1 = alg1.execute()
        fitness1 = result1.fitness()
        
        alg2 = SimpleAlgorithm(
            problem=problem,
            population_size=10,
            max_iterations=10,
            seed=42
        )
        result2 = alg2.execute()
        fitness2 = result2.fitness()
        
        # Results should be identical
        assert fitness1 == fitness2, "Same seed should produce identical results"
        assert np.allclose(result1.position, result2.position), "Positions should be identical"
        
        # Convergence curves should match
        assert alg1.convergence_curve == alg2.convergence_curve, "Convergence curves should match"
    
    def test_different_seeds_produce_different_results(self, problem):
        """Test that different seeds produce different results."""
        # Run algorithm twice with different seeds
        alg1 = SimpleAlgorithm(
            problem=problem,
            population_size=10,
            max_iterations=10,
            seed=42
        )
        result1 = alg1.execute()
        
        alg2 = SimpleAlgorithm(
            problem=problem,
            population_size=10,
            max_iterations=10,
            seed=123
        )
        result2 = alg2.execute()
        
        # Results should be different (with high probability)
        # At least one of these should be true
        assert (result1.fitness() != result2.fitness() or 
                not np.allclose(result1.position, result2.position)), \
               "Different seeds should produce different results"
    
    def test_checkpoint_and_restore(self, problem):
        """Test checkpoint and restore functionality."""
        if not hasattr(MetaheuristicAlgorithm, 'get_random_state'):
            pytest.skip("Checkpointing not available in this version")
        
        algorithm = SimpleAlgorithm(
            problem=problem,
            population_size=10,
            max_iterations=20,
            seed=42
        )
        
        # Run for some iterations
        algorithm.initialize_population()
        for _ in range(5):
            algorithm.update_population()
            algorithm.iteration += 1
        
        # Create checkpoint
        checkpoint = algorithm.get_random_state()
        fitness_at_checkpoint = algorithm.best_solution.fitness()
        
        # Run more iterations
        for _ in range(5):
            algorithm.update_population()
            algorithm.iteration += 1
        
        # Create another algorithm and restore checkpoint
        alg2 = SimpleAlgorithm(
            problem=problem,
            population_size=10,
            max_iterations=20,
            seed=999  # Different seed
        )
        alg2.initialize_population()
        
        # Restore checkpoint
        alg2.set_random_state(checkpoint)
        alg2.iteration = 5  # Reset to checkpoint iteration
        
        # Run same number of iterations from checkpoint
        for _ in range(5):
            alg2.update_population()
            alg2.iteration += 1
        
        # Results should match
        assert np.isclose(
            algorithm.best_solution.fitness(),
            alg2.best_solution.fitness(),
            rtol=1e-10
        ), "Restored algorithm should produce same results"
    
    def test_managed_random_functions(self, problem):
        """Test that managed random functions are available."""
        if not hasattr(MetaheuristicAlgorithm, 'random_uniform'):
            pytest.skip("Managed random functions not available in this version")
        
        algorithm = SimpleAlgorithm(
            problem=problem,
            population_size=5,
            max_iterations=5,
            seed=42
        )
        
        # Test managed random functions
        uniform_values = algorithm.random_uniform(0, 1, 10)
        assert uniform_values.shape == (10,)
        assert np.all((uniform_values >= 0) & (uniform_values <= 1))
        
        normal_values = algorithm.random_normal(0, 1, 10)
        assert normal_values.shape == (10,)
        
        int_values = algorithm.random_randint(0, 10, 5)
        assert int_values.shape == (5,)
        assert np.all((int_values >= 0) & (int_values < 10))
    
    def test_sub_seed_generation(self, problem):
        """Test deterministic sub-seed generation."""
        if not hasattr(MetaheuristicAlgorithm, 'generate_sub_seed'):
            pytest.skip("Sub-seed generation not available in this version")
        
        algorithm = SimpleAlgorithm(
            problem=problem,
            population_size=5,
            max_iterations=5,
            seed=42
        )
        
        # Generate sub-seeds
        seed1 = algorithm.generate_sub_seed("thread_1")
        seed2 = algorithm.generate_sub_seed("thread_2")
        seed3 = algorithm.generate_sub_seed("thread_1")  # Same identifier
        
        # Sub-seeds should be deterministic
        assert seed1 != seed2, "Different identifiers should produce different seeds"
        assert seed1 == seed3, "Same identifier should produce same seed"
        
        # Create another algorithm with same master seed
        alg2 = SimpleAlgorithm(
            problem=problem,
            population_size=5,
            max_iterations=5,
            seed=42
        )
        
        # Should generate same sub-seeds
        assert alg2.generate_sub_seed("thread_1") == seed1
        assert alg2.generate_sub_seed("thread_2") == seed2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])