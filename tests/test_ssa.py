"""Tests for Salp Swarm Algorithm (SSA)."""
import pytest
import numpy as np
import os
from algorithms.ssa import SSA, Salp
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


class TestSalp:
    """Tests for the Salp individual class."""

    def test_initialization(self):
        problem = MockProblem(10)
        salp = Salp(problem)
        assert salp.dimension == 10
        assert salp.position.shape == (10,)
        assert np.all(salp.position >= 0)
        assert np.all(salp.position <= 1)

    def test_fitness_evaluation(self):
        problem = MockProblem(5)
        salp = Salp(problem)
        fitness = salp.fitness()
        assert isinstance(fitness, float)
        assert fitness >= 0

    def test_fitness_caching(self):
        problem = MockProblem(5)
        salp = Salp(problem)
        f1 = salp.fitness()
        f2 = salp.fitness()
        assert f1 == f2

    def test_is_feasible(self):
        problem = MockProblem(5)
        salp = Salp(problem)
        assert salp.is_feasible() is True

    def test_copy(self):
        problem = MockProblem(5)
        salp1 = Salp(problem)
        salp2 = Salp(problem)
        salp2.copy(salp1)
        np.testing.assert_array_equal(salp2.position, salp1.position)
        assert salp2._fitness == salp1._fitness


class TestSSA:
    """Tests for the SSA algorithm class."""

    def test_initialization(self):
        problem = MockProblem(10)
        ssa = SSA(problem, population_size=20, max_iterations=50, seed=42)
        assert ssa.population_size == 20
        assert ssa.max_iterations == 50

    def test_initialize_population(self):
        problem = MockProblem(10)
        ssa = SSA(problem, population_size=20, max_iterations=50, seed=42)
        ssa.initialize_population()
        assert len(ssa.population) == 20
        assert ssa.best_solution is not None
        assert len(ssa.convergence_curve) == 1

    def test_convergence(self):
        """SSA should improve fitness over iterations."""
        problem = MockProblem(10)
        ssa = SSA(problem, population_size=30, max_iterations=50, seed=42)
        best = ssa.execute()
        curve = ssa.get_convergence_curve()
        assert curve[-1] <= curve[0]
        assert best.fitness() <= curve[0]

    def test_seed_reproducibility(self):
        """Same seed should produce same results."""
        problem = MockProblem(10)

        ssa1 = SSA(problem, population_size=20, max_iterations=30, seed=123)
        best1 = ssa1.execute()

        ssa2 = SSA(problem, population_size=20, max_iterations=30, seed=123)
        best2 = ssa2.execute()

        assert best1.fitness() == best2.fitness()

    def test_bounds_respected(self):
        """All positions should stay within [0, 1]."""
        problem = MockProblem(10)
        ssa = SSA(problem, population_size=30, max_iterations=50, seed=42)
        ssa.execute()
        for salp in ssa.population:
            assert np.all(salp.position >= 0)
            assert np.all(salp.position <= 1)

    @pytest.mark.skipif(
        not os.path.exists(os.path.join(DATA_DIR, "P-n16-k8.vrp")),
        reason="VRP instance not available",
    )
    def test_vrp_integration(self):
        """Test SSA on a real VRP instance."""
        instance_path = os.path.join(DATA_DIR, "P-n16-k8.vrp")
        problem = VRPProblem(instance_path)

        ssa = SSA(problem, population_size=30, max_iterations=50, seed=42)
        best = ssa.execute()

        assert best.fitness() > 0
        assert best.fitness() < float("inf")

        routes, distance, _ = problem.decode_solution(best.position)
        assert len(routes) > 0
