"""
Extended benchmarking functionality for QC-DVRP.

This module extends the base benchmarking with support for:
- Dynamic demand simulation
- Multi-objective evaluation
- QC-specific metrics
"""

import numpy as np
import pandas as pd
import os
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from utils.benchmarking import (
    BenchmarkResult as BaseBenchmarkResult,
    run_benchmark as base_run_benchmark,
    OPTIMAL_VALUES,
)
from utils.multiobjective_metrics import (
    calculate_hypervolume,
    calculate_igd,
    get_non_dominated_solutions,
    simulate_dynamic_demands,
    calculate_qc_metrics,
)
from problems.vrp import VRPProblem

logger = logging.getLogger(__name__)

# Extended optimal values including Solomon instances
QC_OPTIMAL_VALUES = OPTIMAL_VALUES.copy()
QC_OPTIMAL_VALUES.update(
    {
        "Solomon-RC101": 1696.94,  # Best known solution
        "Solomon-RC102": 1554.75,
        "Solomon-RC103": 1261.67,
        "Solomon-RC104": 1135.48,
        "Solomon-RC105": 1629.44,
        "Solomon-RC106": 1424.73,
        "Solomon-RC107": 1230.48,
        "Solomon-RC108": 1139.82,
    }
)


class QCDVRPBenchmarkResult(BaseBenchmarkResult):
    """Extended benchmark result for QC-DVRP with multi-objective metrics."""

    def __init__(self, algorithm_name, instance_name, runs=None):
        super().__init__(algorithm_name, instance_name, runs)

        # Multi-objective metrics
        self.pareto_fronts = []
        self.hypervolume_values = []
        self.igd_values = []
        self.spacing_values = []

        # QC-DVRP specific metrics
        self.delivery_times = []
        self.on_time_rates = []
        self.load_variations = []
        self.dynamic_metrics = []

        # Aggregated metrics
        self.avg_hypervolume = None
        self.avg_igd = None
        self.avg_delivery_time = None
        self.on_time_delivery_rate = None
        self.avg_load_variation = None

    def add_multiobjective_run(
        self, pareto_front, hypervolume=None, igd=None, qc_metrics=None
    ):
        """Add results from a multi-objective run."""
        self.pareto_fronts.append(pareto_front)

        if hypervolume is not None:
            self.hypervolume_values.append(hypervolume)
        if igd is not None:
            self.igd_values.append(igd)

        if qc_metrics:
            self.delivery_times.append(qc_metrics.get("avg_delivery_time", 0))
            self.on_time_rates.append(qc_metrics.get("on_time_rate", 0))
            self.load_variations.append(qc_metrics.get("load_variation_coef", 0))
            self.dynamic_metrics.append(qc_metrics)

    def compute_metrics(self):
        """Compute derived metrics including multi-objective ones."""
        super().compute_metrics()

        # Multi-objective metrics
        if self.hypervolume_values:
            self.avg_hypervolume = np.mean(self.hypervolume_values)

        if self.igd_values:
            self.avg_igd = np.mean(self.igd_values)

        # QC-DVRP metrics
        if self.delivery_times:
            self.avg_delivery_time = np.mean(self.delivery_times)

        if self.on_time_rates:
            self.on_time_delivery_rate = np.mean(self.on_time_rates)

        if self.load_variations:
            self.avg_load_variation = np.mean(self.load_variations)

    def to_dict(self):
        """Convert to dictionary with extended metrics."""
        result = super().to_dict()

        # Add multi-objective metrics
        result["metrics"].update(
            {
                "avg_hypervolume": self.avg_hypervolume,
                "avg_igd": self.avg_igd,
                "avg_delivery_time": self.avg_delivery_time,
                "on_time_delivery_rate": self.on_time_delivery_rate,
                "avg_load_variation": self.avg_load_variation,
            }
        )

        # Add detailed multi-objective results
        result["multiobjective_results"] = {
            "hypervolume_values": self.hypervolume_values,
            "igd_values": self.igd_values,
            "delivery_times": self.delivery_times,
            "on_time_rates": self.on_time_rates,
            "load_variations": self.load_variations,
        }

        return result


def run_qc_dvrp_benchmark(
    algorithms,
    problem_instances,
    runs=30,
    iterations=100,
    population=40,
    seed=None,
    parallel=False,
    dynamic=True,
    multiobjective=True,
    lambda_range=(5, 15),
    reference_point=None,
):
    """
    Run benchmark for QC-DVRP with dynamic and multi-objective features.

    Args:
        algorithms: Dictionary of algorithms {name: class}
        problem_instances: List of instance names
        runs: Number of independent runs (min 30 for statistical rigor)
        iterations: Number of iterations per run
        population: Population size
        seed: Random seed for reproducibility
        parallel: Whether to run in parallel
        dynamic: Enable dynamic demand simulation
        multiobjective: Enable multi-objective evaluation
        lambda_range: Range for Poisson arrival rate
        reference_point: Reference point for hypervolume

    Returns:
        List of QCDVRPBenchmarkResult objects
    """
    results = []

    for instance_name in problem_instances:
        # Load problem instance
        instance_path = f"data/vrp/{instance_name}.vrp"
        if not os.path.exists(instance_path):
            # Try Solomon instance format
            instance_path = f"data/solomon/{instance_name}.txt"
            if not os.path.exists(instance_path):
                logger.warning(f"Instance {instance_name} not found")
                continue

        problem = VRPProblem(instance_path)

        # Configure for QC-DVRP if dynamic
        if dynamic and not hasattr(problem, "depots"):
            problem.depots = [(0, 0)]  # Default depot

        logger.info(
            f"Benchmarking {instance_name} with {problem.dimension - 1} customers"
        )

        for algo_name, AlgoClass in algorithms.items():
            logger.info(f"  Running {algo_name}...")
            benchmark_result = QCDVRPBenchmarkResult(algo_name, instance_name, runs)

            for run_idx in range(runs):
                run_seed = seed + run_idx if seed is not None else None

                # Configure algorithm
                algo_params = {
                    "population_size": population,
                    "max_iterations": iterations,
                    "seed": run_seed,
                }

                # Add IL support for HO
                if algo_name.lower() in ["ho", "hoa"]:
                    il_model_path = "models/ho_il_model.pth"
                    if os.path.exists(il_model_path):
                        algo_params["use_il"] = True
                        algo_params["il_model_path"] = il_model_path

                algo = AlgoClass(problem, **algo_params)

                # Dynamic demand simulation
                dynamic_orders = []
                if dynamic:
                    lambda_rate = np.random.uniform(*lambda_range)
                    dynamic_orders = simulate_dynamic_demands(
                        problem, lambda_rate=lambda_rate, seed=run_seed
                    )

                    # Update problem with initial orders
                    if hasattr(problem, "update_demand"):
                        initial_orders = dynamic_orders[: min(5, len(dynamic_orders))]
                        for order in initial_orders:
                            problem.update_demand([order])

                # Execute algorithm
                start_time = time.time()
                best_solution = algo.execute()
                execution_time = time.time() - start_time

                # Standard evaluation
                fitness = best_solution.fitness()
                convergence_curve = algo.get_convergence_curve()
                benchmark_result.add_run(fitness, execution_time, convergence_curve)

                # Multi-objective evaluation
                if multiobjective and hasattr(problem, "evaluate_multi"):
                    # Get Pareto front
                    pareto_front = []

                    if hasattr(algo, "pareto_front") and algo.pareto_front:
                        pareto_front = algo.pareto_front
                    elif hasattr(algo, "population"):
                        # Evaluate population to get Pareto approximation
                        solutions = []
                        for ind in algo.population:
                            obj_vals = problem.evaluate_multi(ind.position)
                            solutions.append(obj_vals)
                        pareto_front = get_non_dominated_solutions(solutions)
                    else:
                        # Single solution
                        obj_vals = problem.evaluate_multi(best_solution.position)
                        pareto_front = [obj_vals]

                    # Calculate hypervolume
                    hv = calculate_hypervolume(pareto_front, reference_point)

                    # Calculate IGD if reference set available
                    igd = None  # Would need reference set

                    # QC metrics
                    qc_metrics = calculate_qc_metrics(
                        best_solution, problem, dynamic_orders
                    )

                    # Add multi-objective results
                    benchmark_result.add_multiobjective_run(
                        pareto_front, hv, igd, qc_metrics
                    )

                # Progress
                if (run_idx + 1) % 5 == 0:
                    logger.info(f"    Progress: {run_idx + 1}/{runs} runs completed")

            # Compute aggregated metrics
            benchmark_result.compute_metrics()
            results.append(benchmark_result)

            # Report results
            logger.info(f"  Results for {algo_name}:")
            logger.info(f"    Best fitness: {benchmark_result.best_fitness:.2f}")
            logger.info(
                f"    Mean fitness: {benchmark_result.mean_fitness:.2f} ± {benchmark_result.std_fitness:.2f}"
            )

            if multiobjective and benchmark_result.avg_hypervolume:
                logger.info(
                    f"    Avg hypervolume: {benchmark_result.avg_hypervolume:.3f}"
                )
                logger.info(
                    f"    On-time rate: {benchmark_result.on_time_delivery_rate*100:.1f}%"
                )
                logger.info(
                    f"    Load variation: {benchmark_result.avg_load_variation:.3f}"
                )

    return results


def create_qc_dvrp_summary_dataframe(benchmark_results):
    """Create summary DataFrame with QC-DVRP metrics."""
    data = []

    for result in benchmark_results:
        result.compute_metrics()

        # Basic row data
        row_base = {
            "Algorithm": result.algorithm_name,
            "Instance": result.instance_name,
            "Best_Cost": result.best_fitness,
            "Mean_Cost": result.mean_fitness,
            "Std_Cost": result.std_fitness,
            "Mean_Time": result.mean_time,
        }

        # Add multi-objective metrics if available
        if result.avg_hypervolume is not None:
            row_base.update(
                {
                    "Hypervolume": result.avg_hypervolume,
                    "IGD": result.avg_igd if result.avg_igd is not None else np.nan,
                    "DeliveryTime": result.avg_delivery_time,
                    "OnTimeRate": result.on_time_delivery_rate,
                    "LoadVariation": result.avg_load_variation,
                }
            )

        # Add gap if optimal known
        if result.optimal_value:
            row_base["Gap_%"] = result.gap_to_optimal

        # Add row for each run (for statistical analysis)
        for i in range(len(result.fitness_values)):
            row = row_base.copy()
            row["Run"] = i + 1
            row["Best_Cost"] = result.fitness_values[i]
            row["Time"] = result.execution_times[i]

            if i < len(result.hypervolume_values):
                row["Hypervolume"] = result.hypervolume_values[i]
            if i < len(result.delivery_times):
                row["DeliveryTime"] = result.delivery_times[i]
                row["OnTimeRate"] = result.on_time_rates[i]
                row["LoadVariation"] = result.load_variations[i]

            data.append(row)

    return pd.DataFrame(data)
