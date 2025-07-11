"""
Tests for QC-DVRP benchmarking functionality.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from utils.qc_dvrp_benchmarking import (
    QCDVRPBenchmarkResult,
    run_qc_dvrp_benchmark,
    create_qc_dvrp_summary_dataframe,
)
from utils.multiobjective_metrics import (
    calculate_hypervolume,
    calculate_igd,
    get_non_dominated_solutions,
    simulate_dynamic_demands,
    calculate_qc_metrics,
)
from problems.vrp import VRPProblem
from algorithms.ho import HO


class TestQCDVRPBenchmarkResult:
    """Test QCDVRPBenchmarkResult class."""

    def test_initialization(self):
        """Test initialization of QC-DVRP benchmark result."""
        result = QCDVRPBenchmarkResult("HO", "Solomon-RC101", runs=30)

        assert result.algorithm_name == "HO"
        assert result.instance_name == "Solomon-RC101"
        assert result.pareto_fronts == []
        assert result.hypervolume_values == []
        assert result.igd_values == []

    def test_add_multiobjective_run(self):
        """Test adding multi-objective run results."""
        result = QCDVRPBenchmarkResult("HO", "Solomon-RC101")

        pareto_front = [(25.5, 0.15, 1500.0), (28.0, 0.12, 1450.0)]
        qc_metrics = {
            "avg_delivery_time": 25.5,
            "on_time_rate": 0.85,
            "load_variation_coef": 0.15,
        }

        result.add_multiobjective_run(
            pareto_front, hypervolume=0.8, igd=0.05, qc_metrics=qc_metrics
        )

        assert len(result.pareto_fronts) == 1
        assert result.hypervolume_values[0] == 0.8
        assert result.igd_values[0] == 0.05
        assert result.delivery_times[0] == 25.5
        assert result.on_time_rates[0] == 0.85

    def test_compute_metrics(self):
        """Test metric computation."""
        result = QCDVRPBenchmarkResult("HO", "Solomon-RC101")

        # Add some data
        for i in range(5):
            result.add_multiobjective_run(
                [(25 + i, 0.15, 1500)],
                hypervolume=0.8 + i * 0.01,
                igd=0.05 - i * 0.005,
                qc_metrics={
                    "avg_delivery_time": 25 + i,
                    "on_time_rate": 0.8,
                    "load_variation_coef": 0.15,
                },
            )
            result.fitness_values.append(1500 + i * 10)
            result.execution_times.append(1.0 + i * 0.1)

        result.compute_metrics()

        assert result.avg_hypervolume == pytest.approx(0.82, rel=1e-3)
        assert result.avg_igd == pytest.approx(0.04, rel=1e-3)
        assert result.avg_delivery_time == pytest.approx(27.0, rel=1e-3)
        assert result.on_time_delivery_rate == pytest.approx(0.8, rel=1e-3)


class TestMultiobjectiveMetrics:
    """Test multi-objective metrics functions."""

    def test_calculate_hypervolume_empty(self):
        """Test hypervolume with empty front."""
        hv = calculate_hypervolume([])
        assert hv == 0.0

    def test_calculate_hypervolume_single_point(self):
        """Test hypervolume with single point."""
        pareto_front = [(20.0, 0.1, 1000.0)]
        hv = calculate_hypervolume(pareto_front)
        assert hv > 0

    def test_calculate_hypervolume_multiple_points(self):
        """Test hypervolume with multiple points."""
        pareto_front = [(20.0, 0.1, 1000.0), (25.0, 0.08, 950.0), (30.0, 0.05, 900.0)]
        hv = calculate_hypervolume(pareto_front)
        assert hv > 0

    def test_calculate_igd(self):
        """Test IGD calculation."""
        pareto_front = [(20.0, 0.1, 1000.0), (25.0, 0.08, 950.0)]
        reference_set = [(18.0, 0.1, 1000.0), (23.0, 0.08, 950.0)]

        igd = calculate_igd(pareto_front, reference_set)
        assert igd > 0
        assert igd < 10  # Should be a reasonable distance

    def test_get_non_dominated_solutions(self):
        """Test non-dominated solution filtering."""
        solutions = [
            (30.0, 0.2, 1500.0),  # Dominated
            (20.0, 0.1, 1000.0),  # Non-dominated
            (25.0, 0.15, 1200.0),  # Dominated
            (22.0, 0.08, 1100.0),  # Non-dominated
        ]

        non_dominated = get_non_dominated_solutions(solutions)
        assert len(non_dominated) == 2
        assert (20.0, 0.1, 1000.0) in non_dominated
        assert (22.0, 0.08, 1100.0) in non_dominated

    def test_simulate_dynamic_demands(self):
        """Test dynamic demand simulation."""
        problem = Mock()
        problem.dimension = 10
        problem.nodes = {i: (i * 10, i * 10) for i in range(10)}

        orders = simulate_dynamic_demands(
            problem, lambda_rate=10, time_horizon=60, seed=42
        )

        assert len(orders) > 0
        assert all("customer_id" in order for order in orders)
        assert all("arrival_time" in order for order in orders)
        assert all(0 <= order["arrival_time"] <= 60 for order in orders)

    def test_calculate_qc_metrics(self):
        """Test QC metrics calculation."""
        solution = Mock()
        solution.position = np.random.rand(10)

        problem = Mock()
        problem.evaluate_multi = Mock(return_value=(25.0, 0.15, 1200.0))

        metrics = calculate_qc_metrics(solution, problem)

        assert metrics["avg_delivery_time"] == 25.0
        assert metrics["on_time_rate"] == 1.0
        assert metrics["load_variation_coef"] == 0.15
        assert metrics["total_distance"] == 1200.0
        assert metrics["service_level"] > 0


class TestQCDVRPBenchmarking:
    """Test QC-DVRP benchmarking function."""

    @patch("utils.qc_dvrp_benchmarking.VRPProblem")
    @patch("os.path.exists")
    def test_run_qc_dvrp_benchmark(self, mock_exists, mock_vrp):
        """Test running QC-DVRP benchmark."""
        # Mock file existence
        mock_exists.return_value = True

        # Mock VRP problem
        mock_problem = Mock()
        mock_problem.dimension = 10
        mock_problem.evaluate_multi = Mock(return_value=(25.0, 0.15, 1200.0))
        mock_problem.nodes = {i: (i * 10, i * 10) for i in range(10)}
        mock_vrp.return_value = mock_problem

        # Mock algorithm
        mock_algo = Mock()
        mock_algo.execute = Mock(
            return_value=Mock(
                fitness=Mock(return_value=1200.0), position=np.random.rand(10)
            )
        )
        mock_algo.get_convergence_curve = Mock(return_value=[1500, 1400, 1300, 1200])
        mock_algo.population = [Mock(position=np.random.rand(10)) for _ in range(5)]
        mock_algo.pareto_front = [(25.0, 0.15, 1200.0), (27.0, 0.12, 1250.0)]

        algorithms = {"test_algo": Mock(return_value=mock_algo)}

        # Run benchmark
        results = run_qc_dvrp_benchmark(
            algorithms,
            ["test_instance"],
            runs=2,
            iterations=10,
            population=5,
            seed=42,
            dynamic=True,
            multiobjective=True,
        )

        assert len(results) == 1
        assert results[0].algorithm_name == "test_algo"
        assert results[0].instance_name == "test_instance"
        assert len(results[0].fitness_values) == 2

    def test_create_summary_dataframe(self):
        """Test creating summary dataframe."""
        # Create mock results
        result1 = QCDVRPBenchmarkResult("HO", "Solomon-RC101")
        result1.fitness_values = [1200, 1250, 1180]
        result1.execution_times = [1.0, 1.1, 0.9]
        result1.hypervolume_values = [0.8, 0.82, 0.79]
        result1.delivery_times = [25, 26, 24]
        result1.on_time_rates = [0.8, 0.85, 0.75]
        result1.load_variations = [0.15, 0.14, 0.16]
        result1.compute_metrics()

        result2 = QCDVRPBenchmarkResult("SHO", "Solomon-RC101")
        result2.fitness_values = [1300, 1350]
        result2.execution_times = [1.2, 1.3]
        result2.hypervolume_values = [0.75, 0.73]
        result2.delivery_times = [28, 30]
        result2.on_time_rates = [0.7, 0.65]
        result2.load_variations = [0.18, 0.20]
        result2.compute_metrics()

        df = create_qc_dvrp_summary_dataframe([result1, result2])

        assert len(df) == 5  # 3 + 2 runs
        assert "Hypervolume" in df.columns
        assert "OnTimeRate" in df.columns
        assert df[df["Algorithm"] == "HO"]["Hypervolume"].mean() == pytest.approx(
            0.803, rel=1e-2
        )
