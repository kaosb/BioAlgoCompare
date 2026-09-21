"""Unit tests for SMO (Starling Murmuration Optimizer) exception handlers and coverage gaps.

Targets uncovered lines in algorithms/smo.py:
- Lines 98-99: Diving behavior with invalid best_position (except block)
- Lines 114-115: Whirling behavior with invalid best_position (except block)
- Lines 119-125: Outer exception handler in move() method
- Line 144: Exception handler in evaluate block of move()
"""
import os
import sys

import copy
import numpy as np
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from algorithms.smo import SMO, Starling
from problems.vrp import VRPProblem


@pytest.fixture
def vrp_problem():
    """Create a VRP problem instance for testing."""
    problem = VRPProblem()
    problem.load_instance("P-n16-k8")
    return problem


@pytest.fixture
def starling(vrp_problem):
    """Create a Starling individual for testing."""
    rng = np.random.default_rng(42)
    import random
    py_rng = random.Random(42)
    s = Starling(vrp_problem, rng=rng, py_rng=py_rng)
    s._fitness = s.fitness()
    s.personal_best_fitness = s._fitness
    return s


class TestStarlingDivingInvalidBest:
    """Tests for diving behavior with invalid best_position."""

    def test_dive_invalid_best_position(self, starling):
        """Lines 98-99: Call move with invalid best_position for diving behavior.

        When best_position is a string (no 'shape' attribute matching),
        the else branch at lines 98-99 should execute (small perturbation).
        """
        original_position = copy.deepcopy(starling.position)

        starling.move(
            best_position="invalid",
            behavior_type="diving",
            members=None,
            coef=0.5,
            it=0,
            max_it=100,
        )

        # The move should complete without error.
        # Position may or may not change depending on acceptance criteria,
        # but the method should not raise an exception.
        assert starling.position is not None
        assert starling.position.shape == original_position.shape

    def test_dive_none_best_position(self, starling):
        """Diving with None best_position also triggers the else branch."""
        original_shape = starling.position.shape
        starling.move(
            best_position=None,
            behavior_type="diving",
            members=None,
            coef=0.5,
            it=0,
            max_it=100,
        )
        assert starling.position.shape == original_shape


class TestStarlingWhirlingInvalidBest:
    """Tests for whirling behavior with invalid best_position."""

    def test_whirl_invalid_best_position(self, starling):
        """Lines 114-115: Call move with None best_position for whirling behavior.

        When best_position is None (no 'shape' attribute),
        the else branch at lines 114-115 should execute (random movement).
        """
        original_position = copy.deepcopy(starling.position)

        starling.move(
            best_position=None,
            behavior_type="whirling",
            members=None,
            coef=0.5,
            it=0,
            max_it=100,
        )

        assert starling.position is not None
        assert starling.position.shape == original_position.shape

    def test_whirl_string_best_position(self, starling):
        """Whirling with string best_position triggers the else branch."""
        original_shape = starling.position.shape
        starling.move(
            best_position="invalid",
            behavior_type="whirling",
            members=None,
            coef=0.5,
            it=0,
            max_it=100,
        )
        assert starling.position.shape == original_shape


class TestStarlingMoveExceptionHandler:
    """Tests for the outer exception handler in move()."""

    def test_move_exception_handler(self, starling):
        """Lines 119-125: Trigger the outer except block in move().

        numpy.random.Generator attributes are read-only, so we replace the
        entire rng object with a MagicMock that raises on .random() but
        provides a working .uniform() for the except handler's fallback.
        """
        original_position = copy.deepcopy(starling.position)
        shape = starling.position.shape

        # Create a mock rng where .random() raises but .uniform() works
        mock_rng = MagicMock()
        mock_rng.random.side_effect = RuntimeError("Simulated RNG failure")
        # The except handler calls self.rng.uniform(-0.05, 0.05, shape)
        mock_rng.uniform.return_value = np.zeros(shape)

        starling.rng = mock_rng

        # Use separating behavior which calls rng.random() first (line 85)
        starling.move(
            best_position=None,
            behavior_type="separating",
            members=None,
            coef=0.5,
            it=0,
            max_it=100,
        )

        # The exception handler should have been triggered
        assert mock_rng.random.called, "rng.random should have been called"
        assert mock_rng.uniform.called, "rng.uniform should have been called (fallback)"
        # The starling should still have a valid position
        assert starling.position is not None
        assert starling.position.shape == original_position.shape


class TestStarlingEvaluateExceptionHandler:
    """Tests for the exception handler in the evaluate block of move()."""

    def test_evaluate_exception_handler(self, starling):
        """Line 144: Patch problem.evaluate to raise RuntimeError.

        This triggers the except block at line 144-146 that keeps the
        current position unchanged.
        """
        original_position = copy.deepcopy(starling.position)
        original_fitness = starling._fitness

        with patch.object(
            starling.problem, "evaluate", side_effect=RuntimeError("Simulated eval failure")
        ):
            starling.move(
                best_position=None,
                behavior_type="separating",
                members=None,
                coef=0.5,
                it=0,
                max_it=100,
            )

        # Position should remain unchanged because evaluate raised an exception
        np.testing.assert_array_equal(
            starling.position, original_position,
            err_msg="Position should not change when evaluate raises an exception"
        )
        assert starling._fitness == original_fitness, (
            "Fitness should not change when evaluate raises an exception"
        )
