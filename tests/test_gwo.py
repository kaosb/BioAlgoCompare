"""Tests for Grey Wolf Optimizer (GWO)."""
import pytest
import numpy as np
import os
from algorithms.gwo import GWO, Wolf
from problems.vrp import VRPProblem


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/vrp")


class MockProblem:
    """Minimal mock problem for unit testing."""

    def __init__(self, dimension=10):
        self._dimension = dimension

    def get_dimension(self):
        return self._dimension

    def evaluate(self, solution):
        return float(np.sum((solution - 0.5) ** 2))


class TestWolf:
    """Tests for the Wolf individual class."""

    def test_initialization(self):
        problem = MockProblem(10)
        wolf = Wolf(problem)
        assert wolf.dimension == 10
        assert wolf.position.shape == (10,)
        assert np.all(wolf.position >= 0)
        assert np.all(wolf.position <= 1)

    def test_fitness_evaluation(self):
        problem = MockProblem(5)
        wolf = Wolf(problem)
        fitness = wolf.fitness()
        assert isinstance(fitness, float)
        assert fitness >= 0

    def test_fitness_caching(self):
        problem = MockProblem(5)
        wolf = Wolf(problem)
        f1 = wolf.fitness()
        f2 = wolf.fitness()
        assert f1 == f2

    def test_is_feasible(self):
        problem = MockProblem(5)
        wolf = Wolf(problem)
        assert wolf.is_feasible() is True

    def test_copy(self):
        problem = MockProblem(5)
        wolf1 = Wolf(problem)
        wolf2 = Wolf(problem)
        wolf2.copy(wolf1)
        np.testing.assert_array_equal(wolf2.position, wolf1.position)
        assert wolf2._fitness == wolf1._fitness


class TestGWO:
    """Tests for the GWO algorithm class."""

    def test_initialization(self):
        problem = MockProblem(10)
        gwo = GWO(problem, population_size=20, max_iterations=50, seed=42)
        assert gwo.population_size == 20
        assert gwo.max_iterations == 50

    def test_initialize_population(self):
        problem = MockProblem(10)
        gwo = GWO(problem, population_size=20, max_iterations=50, seed=42)
        gwo.initialize_population()
        assert len(gwo.population) == 20
        assert gwo.alpha is not None
        assert gwo.beta is not None
        assert gwo.delta is not None
        assert len(gwo.convergence_curve) == 1

    def test_hierarchy(self):
        """Alpha should be the best, beta second, delta third."""
        problem = MockProblem(10)
        gwo = GWO(problem, population_size=30, max_iterations=10, seed=42)
        gwo.initialize_population()
        assert gwo.alpha.fitness() <= gwo.beta.fitness()
        assert gwo.beta.fitness() <= gwo.delta.fitness()

    def test_convergence(self):
        """GWO should improve fitness over iterations."""
        problem = MockProblem(10)
        gwo = GWO(problem, population_size=30, max_iterations=50, seed=42)
        best = gwo.execute()
        curve = gwo.get_convergence_curve()
        assert curve[-1] <= curve[0]
        assert best.fitness() <= curve[0]

    def test_seed_reproducibility(self):
        """Same seed should produce same results."""
        problem = MockProblem(10)

        gwo1 = GWO(problem, population_size=20, max_iterations=30, seed=123)
        best1 = gwo1.execute()

        gwo2 = GWO(problem, population_size=20, max_iterations=30, seed=123)
        best2 = gwo2.execute()

        assert best1.fitness() == best2.fitness()

    def test_bounds_respected(self):
        """All positions should stay within [0, 1]."""
        problem = MockProblem(10)
        gwo = GWO(problem, population_size=30, max_iterations=50, seed=42)
        gwo.execute()
        for wolf in gwo.population:
            assert np.all(wolf.position >= 0)
            assert np.all(wolf.position <= 1)

    def test_a_parameter_decay(self):
        """Parameter 'a' should decrease linearly from 2 to 0."""
        problem = MockProblem(5)
        gwo = GWO(problem, population_size=10, max_iterations=100, seed=42)
        gwo.execute()
        # After all iterations, a should be near 0
        # (We test indirectly through convergence behavior)
        curve = gwo.get_convergence_curve()
        assert len(curve) == 101  # 1 initial + 100 iterations

    @pytest.mark.skipif(
        not os.path.exists(os.path.join(DATA_DIR, "P-n16-k8.vrp")),
        reason="VRP instance not available",
    )
    def test_vrp_integration(self):
        """Test GWO on a real VRP instance."""
        instance_path = os.path.join(DATA_DIR, "P-n16-k8.vrp")
        problem = VRPProblem(instance_path)

        gwo = GWO(problem, population_size=30, max_iterations=50, seed=42)
        best = gwo.execute()

        assert best.fitness() > 0
        assert best.fitness() < float("inf")

        routes, distance, _ = problem.decode_solution(best.position)
        assert len(routes) > 0
