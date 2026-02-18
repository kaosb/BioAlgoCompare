"""Unit tests for HO (Hippopotamus Optimization) algorithm coverage.

Tests the faithful implementation of Amiri et al. (2024):
- Three sequential phases (position, defense, evasion)
- Parameter-free design
- Greedy selection after each phase
- Legacy parameter acceptance (backward compatibility)
"""
import os
import sys

import numpy as np
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from algorithms.ho import HO, Hippopotamus
from problems.vrp import VRPProblem


@pytest.fixture
def vrp_problem():
    """Create a VRP problem instance for testing."""
    problem = VRPProblem()
    problem.load_instance("P-n16-k8")
    return problem


@pytest.fixture
def small_vrp():
    """Create a small VRP problem for fast tests."""
    problem = VRPProblem()
    problem.load_instance("E-n22-k4")
    return problem


class TestIsFeasibleNoIsValid:
    """Hippopotamus.is_feasible when problem lacks is_valid method."""

    def test_is_feasible_no_is_valid(self):
        """When problem has no is_valid method, is_feasible should return True."""
        mock_problem = MagicMock(spec=["evaluate", "get_dimension"])
        mock_problem.get_dimension.return_value = 5
        mock_problem.evaluate.return_value = 100.0

        rng = np.random.default_rng(42)
        hippo = Hippopotamus(mock_problem, rng=rng)

        assert not hasattr(mock_problem, "is_valid")
        result = hippo.is_feasible()
        assert result is True

    def test_is_feasible_with_is_valid(self, vrp_problem):
        """When problem has is_valid method, it should be called."""
        rng = np.random.default_rng(42)
        hippo = Hippopotamus(vrp_problem, rng=rng)

        assert hasattr(vrp_problem, "is_valid")
        result = hippo.is_feasible()
        assert isinstance(result, bool)


class TestHOWithVRP:
    """HO execution with real VRP problem instances."""

    def test_execute_small_vrp(self, small_vrp):
        """Execute HO with a real VRP and verify it completes."""
        algo = HO(
            small_vrp,
            population_size=10,
            max_iterations=10,
            seed=42,
        )
        result = algo.execute()
        assert result is not None
        assert result.fitness() < float("inf")
        assert len(algo.convergence_curve) == 11

    def test_execute_vrp_p16(self, vrp_problem):
        """Execute HO on P-n16-k8 instance."""
        algo = HO(
            vrp_problem,
            population_size=10,
            max_iterations=5,
            seed=42,
        )
        result = algo.execute()
        assert result is not None
        assert result.fitness() > 0


class TestLegacyParamsIgnored:
    """Legacy parameters (alpha, beta, gamma, IL) are accepted but ignored."""

    def test_legacy_params_no_error(self, vrp_problem):
        """Creating HO with legacy params should not raise."""
        algo = HO(
            vrp_problem,
            population_size=5,
            max_iterations=3,
            seed=42,
            alpha_fixed=0.5,
            beta_fixed=0.2,
            gamma_fixed=0.7,
            use_il=True,
            il_model_path="/fake/path",
        )
        algo.execute()
        assert algo.best_solution is not None

    def test_legacy_params_not_stored(self):
        """Legacy params should not be stored as algorithm attributes."""
        mock_problem = MagicMock(spec=["evaluate", "get_dimension"])
        mock_problem.get_dimension.return_value = 5
        mock_problem.evaluate.return_value = 100.0

        algo = HO(
            mock_problem,
            population_size=5,
            max_iterations=3,
            seed=42,
            alpha_fixed=0.5,
            use_il=True,
        )
        # These should NOT be stored as attributes in the new implementation
        assert not hasattr(algo, "alpha_fixed")
        assert not hasattr(algo, "use_il")
        assert not hasattr(algo, "il_model")


class TestDominantTracking:
    """Test that dominant hippo (best solution) is tracked correctly."""

    def test_dominant_improves(self):
        """Dominant should improve or stay the same over iterations."""
        mock_problem = MagicMock(spec=["evaluate", "get_dimension"])
        mock_problem.get_dimension.return_value = 10
        mock_problem.evaluate.side_effect = lambda x: float(np.sum(x ** 2))

        algo = HO(
            mock_problem,
            population_size=20,
            max_iterations=20,
            seed=42,
        )
        algo.execute()

        curve = algo.convergence_curve
        # Convergence curve should be monotonically non-increasing
        for i in range(1, len(curve)):
            assert curve[i] <= curve[i - 1]
