"""Tests for algorithm reproducibility with seeds.

This module tests that algorithms produce identical results when run
with the same random seed.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from algorithms import ALGORITHMS  # noqa: E402
from problems.vrp import VRPProblem  # noqa: E402


class TestReproducibility:
    """Test suite for algorithm reproducibility."""

    @pytest.fixture
    def vrp_problem(self):
        """Create a VRP problem for testing."""
        problem = VRPProblem()
        problem.load_instance("P-n16-k8")
        return problem

    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_reproducibility_same_seed(self, algo_name, vrp_problem):
        """Test that same seed produces identical results."""
        # Skip aliases
        if algo_name in ["hyena", "flamingo"]:
            return

        AlgoClass = ALGORITHMS[algo_name]
        seed = 12345
        pop_size = 20
        iterations = 30

        # Run algorithm twice with same seed
        results = []
        for _ in range(2):
            algo = AlgoClass(
                problem=vrp_problem,
                population_size=pop_size,
                max_iterations=iterations,
                seed=seed,
            )

            algo.initialize_population()
            best = algo.run(iterations=iterations)

            results.append(
                {
                    "fitness": best.fitness(),
                    "convergence": algo.get_convergence_curve(),
                    "position": self._get_position_snapshot(best),
                }
            )

        # Check identical results
        assert (
            results[0]["fitness"] == results[1]["fitness"]
        ), f"{algo_name} produced different fitness values with same seed"

        assert (
            results[0]["convergence"] == results[1]["convergence"]
        ), f"{algo_name} produced different convergence curves with same seed"

        # Check position/solution representation
        pos1, pos2 = results[0]["position"], results[1]["position"]
        if isinstance(pos1, np.ndarray):
            assert np.allclose(
                pos1, pos2
            ), f"{algo_name} produced different positions with same seed"
        else:
            assert (
                pos1 == pos2
            ), f"{algo_name} produced different positions with same seed"

    @pytest.mark.parametrize("algo_name", ["ewa", "foa", "opa", "sma", "woa"])
    def test_reproducibility_multiple_runs(self, algo_name, vrp_problem):
        """Test reproducibility across multiple independent runs."""
        AlgoClass = ALGORITHMS[algo_name]
        seed = 999
        n_runs = 5

        # Collect results from multiple runs
        all_fitness = []
        all_final_positions = []

        for run in range(n_runs):
            algo = AlgoClass(
                problem=vrp_problem, population_size=15, max_iterations=20, seed=seed
            )

            algo.initialize_population()
            best = algo.run(iterations=20)

            all_fitness.append(best.fitness())
            all_final_positions.append(self._get_position_snapshot(best))

        # All runs should produce identical fitness
        assert (
            len(set(all_fitness)) == 1
        ), f"{algo_name} produced {len(set(all_fitness))} different fitness values"

        # All runs should produce identical final positions
        first_pos = all_final_positions[0]
        for i, pos in enumerate(all_final_positions[1:], 1):
            if isinstance(first_pos, np.ndarray):
                assert np.allclose(
                    first_pos, pos
                ), f"{algo_name} run {i+1} produced different position"
            else:
                assert (
                    first_pos == pos
                ), f"{algo_name} run {i+1} produced different position"

    @pytest.mark.parametrize("algo_name", list(ALGORITHMS.keys()))
    def test_different_seeds_produce_different_results(self, algo_name, vrp_problem):
        """Test that different seeds produce different results."""
        # Skip aliases
        if algo_name in ["hyena", "flamingo"]:
            return

        AlgoClass = ALGORITHMS[algo_name]
        seeds = [42, 123, 999, 2024]

        # Run with different seeds
        results = []
        for seed in seeds:
            algo = AlgoClass(
                problem=vrp_problem, population_size=10, max_iterations=15, seed=seed
            )

            algo.initialize_population()
            best = algo.run(iterations=15)
            results.append(best.fitness())

        # At least one result should be different
        unique_results = len(set(results))
        assert (
            unique_results > 1
        ), f"{algo_name} produced identical results with {len(seeds)} different seeds"

    def test_seed_none_produces_different_results(self, vrp_problem):
        """Test that seed=None produces non-deterministic results."""
        # Test with a fast algorithm
        AlgoClass = ALGORITHMS["ewa"]

        # Run multiple times without seed
        results = []
        for _ in range(5):
            algo = AlgoClass(
                problem=vrp_problem,
                population_size=10,
                max_iterations=10,
                seed=None,  # Explicitly set to None
            )

            algo.initialize_population()
            best = algo.run(iterations=10)
            results.append(best.fitness())

        # Results should vary (though there's a small chance they're identical)
        unique_results = len(set(results))
        assert (
            unique_results > 1
        ), "Algorithm produced identical results without seed (possible but unlikely)"

    @pytest.mark.parametrize("seed", [0, 1, 42, 12345, 999999, 2**31 - 1])
    def test_various_seed_values(self, seed, vrp_problem):
        """Test reproducibility with various seed values."""
        # Use a representative algorithm
        AlgoClass = ALGORITHMS["sma"]

        # Run twice with the same seed
        results = []
        for _ in range(2):
            algo = AlgoClass(
                problem=vrp_problem, population_size=10, max_iterations=10, seed=seed
            )

            algo.initialize_population()
            best = algo.run(iterations=10)
            results.append(best.fitness())

        assert results[0] == results[1], f"Different results with seed={seed}"

    def test_reproducibility_with_parallel(self, vrp_problem):
        """Test that parallel execution doesn't affect reproducibility."""
        # This is a placeholder - actual parallel execution would be tested
        # in the parallel execution test module
        pass

    def _get_position_snapshot(self, individual):
        """Get a snapshot of individual's position for comparison."""
        if hasattr(individual, "position"):
            pos = individual.position
            if isinstance(pos, np.ndarray):
                return pos.copy()
            elif isinstance(pos, list):
                # For route-based representations (e.g., OPA)
                return [route[:] for route in pos]
            else:
                return pos
        return None

    @pytest.mark.slow
    @pytest.mark.parametrize("algo_name", ["ewa", "opa", "sma"])
    def test_long_run_reproducibility(self, algo_name, vrp_problem):
        """Test reproducibility in longer runs."""
        AlgoClass = ALGORITHMS[algo_name]
        seed = 2024

        # Longer run parameters
        pop_size = 50
        iterations = 200

        # Run twice
        convergence_curves = []
        for _ in range(2):
            algo = AlgoClass(
                problem=vrp_problem,
                population_size=pop_size,
                max_iterations=iterations,
                seed=seed,
            )

            algo.initialize_population()
            algo.run(iterations=iterations)
            convergence_curves.append(algo.get_convergence_curve())

        # Check entire convergence curves match
        assert len(convergence_curves[0]) == len(convergence_curves[1])

        for i, (v1, v2) in enumerate(zip(convergence_curves[0], convergence_curves[1])):
            assert v1 == v2, f"{algo_name} diverged at iteration {i}: {v1} != {v2}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not slow"])
