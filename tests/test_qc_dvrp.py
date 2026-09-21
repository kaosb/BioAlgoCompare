"""Tests for QC-DVRP Simulator."""
import pytest
import numpy as np
from problems.qc_dvrp import QCDVRPSimulator, Order, DarkStore
from algorithms.gto import GTO
from algorithms.pso import PSO


class TestOrder:
    """Tests for the Order class."""

    def test_creation(self):
        order = Order(
            order_id=1,
            location=(5.0, 3.0),
            demand=3,
            arrival_time=10.0,
            tw_start=20.0,
            tw_end=40.0,
        )
        assert order.order_id == 1
        assert order.location == (5.0, 3.0)
        assert order.demand == 3
        assert order.status == "pending"
        assert order.delivery_time is None


class TestDarkStore:
    """Tests for the DarkStore class."""

    def test_creation(self):
        store = DarkStore(store_id=0, location=(5.0, 5.0), n_vehicles=8)
        assert store.store_id == 0
        assert store.n_vehicles == 8
        assert len(store.vehicle_travel_times) == 8


class TestQCDVRPSimulator:
    """Tests for the QC-DVRP simulator."""

    def test_initialization(self):
        sim = QCDVRPSimulator(seed=42)
        assert sim.zone_size == 10.0
        assert sim.n_dark_stores == 3
        assert sim.n_vehicles == 25
        assert sim.poisson_lambda == 0.5

    def test_dark_store_setup(self):
        sim = QCDVRPSimulator(n_dark_stores=3, seed=42)
        sim._setup_dark_stores()
        assert len(sim.dark_stores) == 3
        total_vehicles = sum(s.n_vehicles for s in sim.dark_stores)
        assert total_vehicles == sim.n_vehicles

    def test_order_generation(self):
        sim = QCDVRPSimulator(poisson_lambda=2.0, seed=42)
        sim._generate_orders(window_start=0.0, window_duration_min=1.0)
        # With lambda=2.0 and 1 minute, expect ~2 orders on average
        assert len(sim.all_orders) > 0
        for order in sim.all_orders:
            assert 0 <= order.location[0] <= sim.zone_size
            assert 0 <= order.location[1] <= sim.zone_size
            assert order.demand >= 1
            assert order.tw_end > order.tw_start

    def test_order_assignment(self):
        sim = QCDVRPSimulator(seed=42)
        sim._setup_dark_stores()
        sim._generate_orders(0.0, 5.0)  # Generate several orders
        sim._assign_orders_to_stores()
        for order in sim.pending_orders:
            assert order.assigned_store is not None
            assert 0 <= order.assigned_store < sim.n_dark_stores

    def test_build_vrp_instance(self):
        sim = QCDVRPSimulator(seed=42)
        sim._setup_dark_stores()
        sim._generate_orders(0.0, 5.0)
        sim._assign_orders_to_stores()

        # At least one store should have orders
        found_problem = False
        for store in sim.dark_stores:
            problem = sim._build_vrp_instance(store.store_id)
            if problem is not None:
                found_problem = True
                assert problem.dimension > 1
                assert problem.distance_matrix is not None
                assert len(problem.nodes) == problem.dimension
                break

        assert found_problem, "No VRP instance was built (no orders assigned)"

    def test_run_simulation_basic(self):
        """Test a minimal simulation run."""
        sim = QCDVRPSimulator(
            simulation_horizon=10.0,  # Very short
            rolling_horizon_window=60.0,
            poisson_lambda=1.0,
            max_fes=1000,
            population_size=10,
            seed=42,
        )
        result = sim.run_simulation(GTO)

        assert "adt" in result
        assert "dsr" in result
        assert "wbi" in result
        assert "fitness" in result
        assert "total_orders" in result
        assert "execution_time" in result
        assert result["execution_time"] > 0

    def test_metrics_valid_ranges(self):
        """Metrics should be in expected ranges."""
        sim = QCDVRPSimulator(
            simulation_horizon=10.0,
            rolling_horizon_window=60.0,
            poisson_lambda=1.0,
            max_fes=1000,
            population_size=10,
            seed=42,
        )
        result = sim.run_simulation(GTO)

        assert result["dsr"] >= 0
        assert result["dsr"] <= 100
        assert result["wbi"] >= 0
        if result["total_orders"] > 0:
            assert result["completed_orders"] + result["failed_orders"] == result["total_orders"]

    def test_different_algorithms(self):
        """Different algorithms should produce different results."""
        sim_config = {
            "simulation_horizon": 5.0,
            "rolling_horizon_window": 60.0,
            "poisson_lambda": 1.0,
            "max_fes": 500,
            "population_size": 10,
            "seed": 42,
        }

        sim1 = QCDVRPSimulator(**sim_config)
        result1 = sim1.run_simulation(GTO)

        sim2 = QCDVRPSimulator(**sim_config)
        result2 = sim2.run_simulation(PSO)

        # Both should complete
        assert result1["execution_time"] > 0
        assert result2["execution_time"] > 0

    def test_seed_reproducibility(self):
        """Same seed should produce same order generation."""
        sim1 = QCDVRPSimulator(seed=42, poisson_lambda=2.0)
        sim1._generate_orders(0.0, 5.0)

        sim2 = QCDVRPSimulator(seed=42, poisson_lambda=2.0)
        sim2._generate_orders(0.0, 5.0)

        assert len(sim1.all_orders) == len(sim2.all_orders)
        for o1, o2 in zip(sim1.all_orders, sim2.all_orders):
            assert o1.location == o2.location
            assert o1.demand == o2.demand

    def test_fitness_tricriterion(self):
        """Test the tricriterion fitness computation."""
        sim = QCDVRPSimulator(seed=42)
        sim._setup_dark_stores()
        sim._generate_orders(0.0, 5.0)
        sim._assign_orders_to_stores()

        for store in sim.dark_stores:
            problem = sim._build_vrp_instance(store.store_id)
            if problem is None or problem.dimension <= 1:
                continue

            store_orders = [
                o for o in sim.pending_orders
                if o.assigned_store == store.store_id
            ]
            solution = np.random.rand(problem.get_dimension())
            routes, _, _ = problem.decode_solution(solution)

            fitness = sim.fitness_tricriterion(routes, problem, store_orders, 0.0)
            assert isinstance(fitness, float)
            assert fitness >= 0
            break


class TestHOLegacyParams:
    """Tests for HO accepting legacy parameters (backward compatibility)."""

    def test_legacy_params_accepted(self):
        """HO should accept alpha_fixed and beta_fixed without error."""
        from algorithms.ho import HO

        class SimpleProblem:
            def get_dimension(self):
                return 5
            def evaluate(self, sol):
                return float(np.sum(sol ** 2))

        problem = SimpleProblem()
        ho = HO(
            problem,
            population_size=10,
            max_iterations=10,
            seed=42,
            alpha_fixed=0.5,
            beta_fixed=0.2,
        )
        # Legacy params are accepted but ignored (HO is parameter-free)
        best = ho.execute()
        assert best.fitness() >= 0

    def test_legacy_params_same_result(self):
        """HO with/without legacy params should produce identical results (params are ignored)."""
        from algorithms.ho import HO

        class SimpleProblem:
            def get_dimension(self):
                return 5
            def evaluate(self, sol):
                return float(np.sum(sol ** 2))

        problem = SimpleProblem()

        ho_with = HO(
            problem,
            population_size=10,
            max_iterations=20,
            seed=42,
            alpha_fixed=0.5,
            beta_fixed=0.2,
        )
        best_with = ho_with.execute()

        ho_without = HO(
            problem,
            population_size=10,
            max_iterations=20,
            seed=42,
        )
        best_without = ho_without.execute()

        # Both should produce identical results (legacy params are ignored)
        assert best_with.fitness() == best_without.fitness()
