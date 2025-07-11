"""
Multi-objective optimization metrics for QC-DVRP.

This module provides implementations of hypervolume and IGD metrics
for evaluating multi-objective optimization algorithms.
"""

import numpy as np
from typing import List, Tuple, Optional
from math import sqrt
import logging

logger = logging.getLogger(__name__)

# Try to import DEAP for better hypervolume calculation
try:
    from deap.tools import hypervolume as deap_hypervolume

    DEAP_AVAILABLE = True
except ImportError:
    DEAP_AVAILABLE = False
    logger.info("DEAP not available, using simplified hypervolume calculation")


def calculate_hypervolume(
    pareto_front: List[Tuple[float, float, float]],
    reference_point: Optional[Tuple[float, float, float]] = None,
) -> float:
    """
    Calculate the hypervolume of a Pareto front.

    Args:
        pareto_front: List of solutions [(obj1, obj2, obj3), ...]
        reference_point: Reference point (worst case)

    Returns:
        float: Hypervolume value
    """
    if not pareto_front:
        return 0.0

    # If DEAP is available, use its implementation
    if DEAP_AVAILABLE:
        if reference_point is None:
            # Calculate reference point automatically
            max_obj1 = max(s[0] for s in pareto_front) * 1.1
            max_obj2 = max(s[1] for s in pareto_front) * 1.1
            max_obj3 = max(s[2] for s in pareto_front) * 1.1
            reference_point = [max_obj1, max_obj2, max_obj3]

        hv = deap_hypervolume.Hypervolume(reference_point)
        return hv.compute(pareto_front)
    else:
        # Simplified implementation if DEAP not available
        if reference_point is None:
            reference_point = [
                max(s[0] for s in pareto_front) * 1.1,
                max(s[1] for s in pareto_front) * 1.1,
                max(s[2] for s in pareto_front) * 1.1,
            ]

        # Simple approximation: sum of dominated volumes
        volume = 0.0
        for sol in pareto_front:
            vol = 1.0
            for i in range(3):
                diff = reference_point[i] - sol[i]
                if diff > 0:
                    vol *= diff
                else:
                    vol = 0
                    break
            volume += vol
        return volume


def calculate_igd(
    pareto_front: List[Tuple[float, float, float]],
    reference_set: List[Tuple[float, float, float]],
) -> float:
    """
    Calculate the Inverted Generational Distance (IGD).

    Args:
        pareto_front: Obtained Pareto front
        reference_set: Reference set (known Pareto optimal)

    Returns:
        float: IGD value
    """
    if not pareto_front or not reference_set:
        return float("inf")

    total_distance = 0.0
    for ref_point in reference_set:
        min_distance = float("inf")
        for sol in pareto_front:
            # Euclidean distance
            distance = sum((ref_point[i] - sol[i]) ** 2 for i in range(len(ref_point)))
            distance = sqrt(distance)
            min_distance = min(min_distance, distance)
        total_distance += min_distance

    return total_distance / len(reference_set)


def get_non_dominated_solutions(
    solutions: List[Tuple[float, float, float]],
) -> List[Tuple[float, float, float]]:
    """
    Filter non-dominated solutions from a set.

    Args:
        solutions: List of solutions [(obj1, obj2, obj3), ...]

    Returns:
        List of non-dominated solutions
    """
    non_dominated = []

    for i, sol1 in enumerate(solutions):
        dominated = False
        for j, sol2 in enumerate(solutions):
            if i != j:
                # Check if sol2 dominates sol1 (all objectives <= and at least one <)
                if all(sol2[k] <= sol1[k] for k in range(len(sol1))) and any(
                    sol2[k] < sol1[k] for k in range(len(sol1))
                ):
                    dominated = True
                    break
        if not dominated:
            non_dominated.append(sol1)

    return non_dominated


def calculate_spacing(pareto_front: List[Tuple[float, float, float]]) -> float:
    """
    Calculate spacing metric for Pareto front distribution.

    Lower values indicate better distribution.

    Args:
        pareto_front: List of solutions

    Returns:
        float: Spacing value
    """
    if len(pareto_front) < 2:
        return 0.0

    distances = []
    for i, sol1 in enumerate(pareto_front):
        min_dist = float("inf")
        for j, sol2 in enumerate(pareto_front):
            if i != j:
                dist = sum((sol1[k] - sol2[k]) ** 2 for k in range(len(sol1)))
                dist = sqrt(dist)
                min_dist = min(min_dist, dist)
        distances.append(min_dist)

    mean_dist = np.mean(distances)
    spacing = sqrt(sum((d - mean_dist) ** 2 for d in distances) / len(distances))

    return spacing


def calculate_spread(
    pareto_front: List[Tuple[float, float, float]],
    extreme_points: Optional[List[Tuple[float, float, float]]] = None,
) -> float:
    """
    Calculate spread metric for Pareto front coverage.

    Args:
        pareto_front: List of solutions
        extreme_points: Known extreme points (optional)

    Returns:
        float: Spread value (0 to 1, higher is better)
    """
    if len(pareto_front) < 2:
        return 0.0

    # Find extreme points in each objective if not provided
    if extreme_points is None:
        extreme_points = []
        for obj_idx in range(3):
            # Find solution with minimum value in this objective
            min_sol = min(pareto_front, key=lambda x: x[obj_idx])
            extreme_points.append(min_sol)

    # Calculate distances
    df = sum(
        sqrt(sum((pareto_front[0][k] - ep[k]) ** 2 for k in range(3)))
        for ep in extreme_points
    )
    dl = sum(
        sqrt(sum((pareto_front[-1][k] - ep[k]) ** 2 for k in range(3)))
        for ep in extreme_points
    )

    # Calculate sum of consecutive distances
    d_sum = 0.0
    for i in range(len(pareto_front) - 1):
        d_sum += sqrt(
            sum((pareto_front[i][k] - pareto_front[i + 1][k]) ** 2 for k in range(3))
        )

    d_mean = d_sum / (len(pareto_front) - 1) if len(pareto_front) > 1 else 0

    # Calculate spread
    if d_mean * (len(pareto_front) - 1) + df + dl > 0:
        spread = (
            df + dl + sum(abs(d - d_mean) for d in [d_sum / (len(pareto_front) - 1)])
        ) / (df + dl + d_mean * (len(pareto_front) - 1))
    else:
        spread = 0.0

    return spread


def simulate_dynamic_demands(
    problem,
    lambda_rate: float = 10,
    time_horizon: float = 480,
    seed: Optional[int] = None,
) -> List[dict]:
    """
    Simulate dynamic demands following a Poisson process.

    Args:
        problem: VRPProblem instance
        lambda_rate: Poisson arrival rate (orders/hour)
        time_horizon: Time horizon in minutes
        seed: Random seed for reproducibility

    Returns:
        List of new orders with timestamps
    """
    if seed is not None:
        np.random.seed(seed)

    dynamic_orders = []
    current_time = 0

    while current_time < time_horizon:
        # Time until next order (exponential)
        interval = np.random.exponential(60 / lambda_rate)  # in minutes
        current_time += interval

        if current_time < time_horizon:
            # Generate new order
            customer_id = np.random.randint(1, problem.dimension)
            demand = np.random.randint(5, 20)

            order = {
                "customer_id": customer_id,
                "demand": demand,
                "arrival_time": current_time,
                "coord": problem.nodes[customer_id]
                if hasattr(problem, "nodes")
                else (0, 0),
                "time_window": (current_time, current_time + 120),  # 2 hour window
            }
            dynamic_orders.append(order)

    return dynamic_orders


def calculate_qc_metrics(
    solution, problem, dynamic_orders: Optional[List[dict]] = None
) -> dict:
    """
    Calculate Quick Commerce specific metrics.

    Args:
        solution: Solution to evaluate
        problem: VRPProblem instance
        dynamic_orders: List of dynamic orders (optional)

    Returns:
        Dictionary with QC metrics
    """
    metrics = {}

    # Evaluate multi-objective if available
    if hasattr(problem, "evaluate_multi"):
        delivery_time, load_var, distance = problem.evaluate_multi(solution.position)

        # On-time delivery rate (≤30 min)
        metrics["avg_delivery_time"] = delivery_time
        metrics["on_time_rate"] = 1.0 if delivery_time <= 30 else 0.0
        metrics["load_variation_coef"] = load_var
        metrics["total_distance"] = distance

        # Additional QC metrics
        metrics["service_level"] = (
            min(1.0, 30.0 / delivery_time) if delivery_time > 0 else 1.0
        )

    # Dynamic metrics if orders provided
    if dynamic_orders:
        metrics["total_dynamic_orders"] = len(dynamic_orders)
        metrics["orders_per_hour"] = (
            len(dynamic_orders) * 60 / 480
        )  # Assuming 8hr horizon

    return metrics
