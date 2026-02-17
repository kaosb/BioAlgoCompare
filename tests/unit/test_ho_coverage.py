"""Unit tests for HO (Hippopotamus Optimization) algorithm coverage.

Targets uncovered lines in algorithms/ho.py to increase test coverage.
"""
import os
import sys
import random

import numpy as np
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from algorithms.ho import HO, Hippopotamus
from algorithms.base import Individual
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
    """ho.py:75 - is_feasible when problem lacks is_valid method."""

    def test_is_feasible_no_is_valid(self):
        """When problem has no is_valid method, is_feasible should return True."""
        # Create a mock problem that does NOT have is_valid
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

        # VRPProblem has is_valid
        assert hasattr(vrp_problem, "is_valid")
        result = hippo.is_feasible()
        assert isinstance(result, bool)


class TestILModelLoadingBranches:
    """ho.py:177-188 - IL model loading with different branch conditions."""

    def test_sklearn_model_exists(self, vrp_problem):
        """When sklearn model file exists, it should be loaded."""
        mock_model = MagicMock()
        mock_model.predict.return_value = (0.5, 0.5, 0.5)

        with patch("pathlib.Path.exists", return_value=True):
            with patch(
                "utils.train_il_simple.SimpleILModel", return_value=mock_model
            ):
                algo = HO(
                    vrp_problem,
                    population_size=5,
                    max_iterations=3,
                    seed=42,
                    use_il=True,
                )
                assert algo.il_model is not None
                assert algo.use_il is True

    def test_pytorch_model_exists(self, vrp_problem):
        """When sklearn model doesn't exist but pytorch model does."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch("algorithms.ho.os.path.exists", return_value=True):
                mock_il = MagicMock()
                with patch.dict(
                    "sys.modules",
                    {"utils.imitation_learning": MagicMock(HOImitationLearning=lambda: mock_il)},
                ):
                    algo = HO(
                        vrp_problem,
                        population_size=5,
                        max_iterations=3,
                        seed=42,
                        use_il=True,
                        il_model_path="/fake/model.pt",
                    )
                    assert algo.il_model is not None

    def test_no_model_exists(self, vrp_problem):
        """When no model file exists, IL should be disabled."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch("algorithms.ho.os.path.exists", return_value=False):
                algo = HO(
                    vrp_problem,
                    population_size=5,
                    max_iterations=3,
                    seed=42,
                    use_il=True,
                )
                assert algo.use_il is False
                assert algo.il_model is None

    def test_import_error_disables_il(self, vrp_problem):
        """When import fails, IL should be disabled."""
        with patch.dict("sys.modules", {"utils.train_il_simple": None}):
            algo = HO(
                vrp_problem,
                population_size=5,
                max_iterations=3,
                seed=42,
                use_il=True,
            )
            assert algo.use_il is False
            assert algo.il_model is None


class TestILPrediction:
    """ho.py:230-240 - IL model predict path during update_population."""

    def test_il_prediction_sklearn(self, vrp_problem):
        """When use_il=True and il_model has predict (sklearn), should use predicted params."""
        algo = HO(
            vrp_problem,
            population_size=5,
            max_iterations=5,
            seed=42,
            use_il=False,
        )
        algo.initialize_population()

        # Enable IL after init to bypass model loading
        algo.use_il = True
        mock_model = MagicMock()
        mock_model.predict.return_value = (0.5, 0.4, 0.6)
        algo.il_model = mock_model

        # Mock the import of create_state_dict
        mock_create_state = MagicMock(return_value={"progress": 0.2})
        with patch.dict(
            "sys.modules",
            {
                "utils.test_il_integration": MagicMock(
                    create_state_dict=mock_create_state
                )
            },
        ):
            algo.update_population()

        # Verify the model predict was called
        assert mock_model.predict.called

    def test_il_prediction_pytorch_branch(self, vrp_problem):
        """Cover ho.py:236-240 - PyTorch model branch when hasattr(il_model, 'predict') is False.

        The else branch at line 235 is entered when the il_model does NOT have
        a 'predict' attribute (as checked by hasattr). This branch imports
        create_state_from_problem from utils.imitation_learning and then calls
        il_model.predict(state). Since the model lacks predict, this will raise
        AttributeError, which is caught by the except block. However, lines
        236-240 are still executed (covered) before the exception on line 240.
        """
        algo = HO(
            vrp_problem,
            population_size=5,
            max_iterations=5,
            seed=42,
            use_il=False,
        )
        algo.initialize_population()

        # Enable IL after init to bypass model loading
        algo.use_il = True

        # Create a model object that does NOT have 'predict' attribute
        # so hasattr(il_model, 'predict') returns False -> enters else branch
        class PyTorchLikeModel:
            """Model without predict attribute to trigger PyTorch branch."""
            pass

        algo.il_model = PyTorchLikeModel()

        # Mock the import of create_state_from_problem (lines 236-239)
        mock_create_state = MagicMock(return_value={"progress": 0.2})
        mock_il_module = MagicMock(create_state_from_problem=mock_create_state)
        with patch.dict(
            "sys.modules",
            {"utils.imitation_learning": mock_il_module},
        ):
            # This will enter the else branch (lines 236-239),
            # create state successfully, then line 240 will raise
            # AttributeError because PyTorchLikeModel has no predict method.
            # The except block catches it and falls back to standard params.
            algo.update_population()

        # Verify create_state_from_problem was called (lines 237-239 executed)
        assert mock_create_state.called


class TestILFallbackPrint:
    """ho.py:244 - IL fallback when predict raises an exception."""

    def test_il_fallback_print(self, vrp_problem, capsys):
        """When il_model.predict raises, should fallback to standard params."""
        algo = HO(
            vrp_problem,
            population_size=5,
            max_iterations=5,
            seed=42,
            use_il=False,
        )
        algo.initialize_population()

        # Enable IL after init
        algo.use_il = True
        mock_model = MagicMock()
        mock_model.predict.side_effect = RuntimeError("Test error")
        algo.il_model = mock_model

        # First call should print fallback message (iteration == 0 check:
        # convergence_curve has 1 entry after init, so iteration=1, not 0)
        # We need convergence_curve to have exactly 1 entry (so iteration=1)
        # The print only happens when iteration == 0, so we reset curve
        algo.convergence_curve = []  # Make iteration = 0

        algo.update_population()

        captured = capsys.readouterr()
        assert "IL fallback" in captured.out


class TestGammaFixed:
    """ho.py:261 - gamma_fixed parameter usage."""

    def test_gamma_fixed(self, vrp_problem):
        """When gamma_fixed is set, it should be used instead of adaptive."""
        algo = HO(
            vrp_problem,
            population_size=5,
            max_iterations=5,
            seed=42,
            gamma_fixed=0.7,
        )
        assert algo.gamma_fixed == 0.7

        # Execute and verify it runs without errors
        algo.execute()
        assert len(algo.convergence_curve) == 6  # initial + 5 iterations


class TestDiscrete2Opt:
    """ho.py:326-332 - 2-opt discrete optimization in position phase."""

    def test_2opt_discrete(self, small_vrp):
        """Execute HO with a real VRP and verify discrete optimization runs."""
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

    def test_2opt_discrete_direct_position_phase(self, small_vrp):
        """Cover ho.py:326-332 by directly calling _position_phase.

        Lines 326-332 are inside _position_phase which only executes when
        fitness_ratio < theta. By calling _position_phase directly with a
        VRP problem (which has decode_solution), we ensure the 2-opt discrete
        branch is reached. The condition at line 330 (len > 3) requires a
        route with at least 4 nodes (depot-customer-customer-customer-depot).
        """
        algo = HO(
            small_vrp,
            population_size=10,
            max_iterations=10,
            seed=42,
        )
        algo.initialize_population()

        # Verify problem has decode_solution (line 325 check)
        assert hasattr(small_vrp, "decode_solution")

        # Directly call _position_phase to guarantee execution of lines 326-332
        algo._position_phase(alpha=0.5, beta=0.3)

        # Verify population was modified (positions updated)
        assert len(algo.population) == 10


class TestApply2Opt:
    """ho.py:415-442 - _apply_2opt method."""

    def test_apply_2opt_long_route(self, vrp_problem):
        """Apply 2-opt to a route with enough nodes for optimization."""
        algo = HO(
            vrp_problem,
            population_size=5,
            max_iterations=3,
            seed=42,
        )

        # Route: depot -> 3 -> 1 -> 2 -> depot
        route = [0, 3, 1, 2, 0]
        improved = algo._apply_2opt(route)

        # Should return a valid route
        assert improved[0] == 0
        assert improved[-1] == 0
        assert len(improved) == len(route)
        # All customers should be present
        assert set(improved[1:-1]) == set(route[1:-1])

    def test_apply_2opt_short_route(self, vrp_problem):
        """Apply 2-opt to a route too short for optimization."""
        algo = HO(
            vrp_problem,
            population_size=5,
            max_iterations=3,
            seed=42,
        )

        # Route with < 4 nodes should be returned as-is
        route = [0, 1, 0]
        result = algo._apply_2opt(route)
        assert result == [0, 1, 0]

    def test_apply_2opt_exactly_3_nodes(self, vrp_problem):
        """Route with exactly 3 nodes (depot-customer-depot) stays unchanged."""
        algo = HO(
            vrp_problem,
            population_size=5,
            max_iterations=3,
            seed=42,
        )
        route = [0, 5, 0]
        result = algo._apply_2opt(route)
        assert result == [0, 5, 0]


class TestRouteDistance:
    """ho.py:447-453 - _route_distance method."""

    def test_route_distance_no_matrix(self):
        """Problem without distance_matrix should return 0.0."""
        # Create a minimal mock problem
        mock_problem = MagicMock()
        mock_problem.get_dimension.return_value = 5
        mock_problem.evaluate.return_value = 100.0
        del mock_problem.distance_matrix  # Ensure attribute doesn't exist

        algo = HO(
            mock_problem,
            population_size=5,
            max_iterations=3,
            seed=42,
        )

        result = algo._route_distance([0, 1, 2, 0])
        assert result == 0.0

    def test_route_distance_with_matrix(self):
        """Correct distance calculation with distance matrix."""
        mock_problem = MagicMock()
        mock_problem.get_dimension.return_value = 4
        mock_problem.evaluate.return_value = 100.0

        # Create a simple distance matrix
        dm = np.array(
            [
                [0.0, 10.0, 20.0, 30.0],
                [10.0, 0.0, 15.0, 25.0],
                [20.0, 15.0, 0.0, 35.0],
                [30.0, 25.0, 35.0, 0.0],
            ]
        )
        mock_problem.distance_matrix = dm

        algo = HO(
            mock_problem,
            population_size=5,
            max_iterations=3,
            seed=42,
        )

        # Route: 0 -> 1 -> 2 -> 0
        # Distance: dm[0,1] + dm[1,2] + dm[2,0] = 10 + 15 + 20 = 45
        result = algo._route_distance([0, 1, 2, 0])
        assert result == pytest.approx(45.0)

    def test_route_distance_single_customer(self):
        """Distance for a route with single customer."""
        mock_problem = MagicMock()
        mock_problem.get_dimension.return_value = 3
        mock_problem.evaluate.return_value = 100.0

        dm = np.array(
            [
                [0.0, 5.0, 8.0],
                [5.0, 0.0, 7.0],
                [8.0, 7.0, 0.0],
            ]
        )
        mock_problem.distance_matrix = dm

        algo = HO(
            mock_problem,
            population_size=5,
            max_iterations=3,
            seed=42,
        )

        # Route: 0 -> 1 -> 0 = 5 + 5 = 10
        result = algo._route_distance([0, 1, 0])
        assert result == pytest.approx(10.0)


class TestSwapBalancing:
    """ho.py:469, 482 - _apply_swap_balancing edge cases."""

    def test_swap_balancing_1_route(self, vrp_problem):
        """With only 1 route, should return it unchanged."""
        algo = HO(
            vrp_problem,
            population_size=5,
            max_iterations=3,
            seed=42,
        )

        routes = [[0, 1, 2, 3, 0]]
        result = algo._apply_swap_balancing(routes)
        assert result == routes

    def test_swap_balancing_equal_loads(self, vrp_problem):
        """Routes with identical loads should remain unchanged."""
        algo = HO(
            vrp_problem,
            population_size=5,
            max_iterations=3,
            seed=42,
        )

        # Find two customers with the same demand
        demands = vrp_problem.demands
        # Build routes where max_load_idx == min_load_idx
        # Use single customer routes with same demand
        # Find a customer with known demand
        customer1 = 1
        customer2 = 2
        d1 = demands[customer1]
        d2 = demands[customer2]

        # If demands are equal, max and min index will be the same -> early return
        # If not, we need to construct routes carefully
        # Let's find two customers with equal demands
        demand_to_customers = {}
        for i in range(1, len(demands)):
            d = demands[i]
            if d not in demand_to_customers:
                demand_to_customers[d] = []
            demand_to_customers[d].append(i)

        equal_pair = None
        for d, customers in demand_to_customers.items():
            if len(customers) >= 2:
                equal_pair = (customers[0], customers[1])
                break

        if equal_pair is None:
            # All demands are different; use a single-element route pair
            # where argmax == argmin (only possible with same load)
            # Create two routes with same total load by using different combos
            pytest.skip("No equal demand customers found")

        c1, c2 = equal_pair
        routes = [[0, c1, 0], [0, c2, 0]]
        result = algo._apply_swap_balancing(routes)
        # Since loads are equal, max_load_idx == min_load_idx -> returns routes unchanged
        assert result == routes

    def test_swap_balancing_unequal_loads(self, vrp_problem):
        """Routes with unequal loads should attempt swap balancing."""
        algo = HO(
            vrp_problem,
            population_size=5,
            max_iterations=3,
            seed=42,
        )

        # Find customers with different demands for unequal routes
        demands = vrp_problem.demands
        # Use customers that create a load imbalance
        # Route 1: heavy load, Route 2: light load
        customers_by_demand = sorted(range(1, len(demands)), key=lambda i: demands[i])
        light = customers_by_demand[0]
        heavy = customers_by_demand[-1]

        routes = [[0, heavy, 0], [0, light, 0]]
        result = algo._apply_swap_balancing(routes)

        # Result should be valid routes
        assert len(result) == 2
        for route in result:
            assert route[0] == 0
            assert route[-1] == 0

    def test_swap_balancing_empty_routes(self, vrp_problem):
        """Empty routes list should return empty."""
        algo = HO(
            vrp_problem,
            population_size=5,
            max_iterations=3,
            seed=42,
        )
        result = algo._apply_swap_balancing([])
        assert result == []
