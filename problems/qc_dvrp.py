"""QC-DVRP Simulator (Quick Commerce Dynamic Vehicle Routing Problem).

Implements the discrete event simulation described in the IWINAC 2026 paper.
Simulates a Quick Commerce scenario with multiple dark stores, dynamic order
arrivals via Poisson process, and rolling horizon re-optimization.

The simulator creates temporary VRP instances at each rolling horizon window
and uses metaheuristic algorithms to solve them. It collects three key metrics:
- ADT: Average Delivery Time (minutes)
- DSR: Delivery Success Rate (% within time window)
- WBI: Workload Balance Index (std of vehicle travel times)

Reference:
    Section 4 of the IWINAC 2026 paper - Simulation Framework.
"""
import math
import numpy as np
import time
from typing import Dict, List, Tuple, Any, Optional, Type
from problems.vrp import VRPProblem
from algorithms.base import MetaheuristicAlgorithm


class Order:
    """Represents a customer order in the QC-DVRP simulation."""

    def __init__(
        self,
        order_id: int,
        location: Tuple[float, float],
        demand: int,
        arrival_time: float,
        tw_start: float,
        tw_end: float,
    ):
        self.order_id = order_id
        self.location = location
        self.demand = demand
        self.arrival_time = arrival_time
        self.tw_start = tw_start  # Earliest delivery time
        self.tw_end = tw_end  # Latest delivery time (deadline)
        self.assigned_store = None
        self.delivery_time = None
        self.status = "pending"  # pending, assigned, delivered, failed


class DarkStore:
    """Represents a dark store (micro-fulfillment center)."""

    def __init__(self, store_id: int, location: Tuple[float, float], n_vehicles: int):
        self.store_id = store_id
        self.location = location
        self.n_vehicles = n_vehicles
        self.vehicle_travel_times = [0.0] * n_vehicles


class QCDVRPSimulator:
    """Simulator for Quick Commerce Dynamic Vehicle Routing Problem.

    Implements a rolling horizon approach where at each time window,
    pending orders are collected, a VRP instance is built, and a
    metaheuristic is used to find optimized routes.

    Args:
        zone_size: Service zone size in km (square zone_size x zone_size)
        n_dark_stores: Number of dark stores
        n_vehicles: Total number of vehicles across all stores
        vehicle_capacity: Maximum items per vehicle trip
        poisson_lambda: Order arrival rate (orders per minute)
        time_window_min: Minimum delivery time window (minutes from order)
        time_window_max: Maximum delivery time window (minutes from order)
        rolling_horizon_window: Re-optimization interval in seconds
        simulation_horizon: Total simulation time in minutes
        service_time: Time per delivery stop (minutes)
        avg_speed: Average vehicle speed (km/h)
        omega_weights: Fitness weights (distance, tw_violation, wl_balance)
        max_fes: Maximum function evaluations across entire simulation
        population_size: Population size for the metaheuristic
        seed: Random seed for reproducibility
    """

    def __init__(
        self,
        zone_size: float = 10.0,
        n_dark_stores: int = 3,
        n_vehicles: int = 25,
        vehicle_capacity: int = 50,
        poisson_lambda: float = 0.5,
        time_window_min: float = 10.0,
        time_window_max: float = 30.0,
        rolling_horizon_window: float = 60.0,
        simulation_horizon: float = 240.0,
        service_time: float = 5.0,
        avg_speed: float = 40.0,
        omega_weights: Tuple[float, float, float] = (0.4, 0.4, 0.2),
        max_fes: int = 50000,
        population_size: int = 100,
        seed: int = 42,
    ):
        self.zone_size = zone_size
        self.n_dark_stores = n_dark_stores
        self.n_vehicles = n_vehicles
        self.vehicle_capacity = vehicle_capacity
        self.poisson_lambda = poisson_lambda
        self.time_window_min = time_window_min
        self.time_window_max = time_window_max
        self.rolling_horizon_window = rolling_horizon_window  # seconds
        self.simulation_horizon = simulation_horizon  # minutes
        self.service_time = service_time
        self.avg_speed = avg_speed
        self.omega_weights = omega_weights
        self.max_fes = max_fes
        self.population_size = population_size
        self.seed = seed

        self.rng = np.random.RandomState(seed)

        # State
        self.dark_stores: List[DarkStore] = []
        self.all_orders: List[Order] = []
        self.pending_orders: List[Order] = []
        self.completed_orders: List[Order] = []
        self.failed_orders: List[Order] = []
        self.order_counter = 0

    def _setup_dark_stores(self):
        """Generate dark store positions spread across the zone."""
        self.dark_stores = []
        vehicles_per_store = self.n_vehicles // self.n_dark_stores
        remainder = self.n_vehicles % self.n_dark_stores

        if self.n_dark_stores == 1:
            positions = [(self.zone_size / 2, self.zone_size / 2)]
        elif self.n_dark_stores == 3:
            # Triangular layout for good coverage
            cx, cy = self.zone_size / 2, self.zone_size / 2
            r = self.zone_size * 0.3
            positions = [
                (cx, cy + r),
                (cx - r * 0.866, cy - r * 0.5),
                (cx + r * 0.866, cy - r * 0.5),
            ]
        else:
            # Grid-like positions
            positions = []
            for i in range(self.n_dark_stores):
                angle = 2 * np.pi * i / self.n_dark_stores
                cx = self.zone_size / 2 + self.zone_size * 0.3 * np.cos(angle)
                cy = self.zone_size / 2 + self.zone_size * 0.3 * np.sin(angle)
                positions.append((cx, cy))

        for i, pos in enumerate(positions):
            n_v = vehicles_per_store + (1 if i < remainder else 0)
            self.dark_stores.append(DarkStore(i, pos, n_v))

    def _generate_orders(self, window_start: float, window_duration_min: float):
        """Generate new orders via Poisson process during a time window.

        Args:
            window_start: Start time of the window (minutes)
            window_duration_min: Duration of the window (minutes)
        """
        n_new = self.rng.poisson(self.poisson_lambda * window_duration_min)

        for _ in range(n_new):
            x = self.rng.uniform(0, self.zone_size)
            y = self.rng.uniform(0, self.zone_size)
            demand = self.rng.randint(1, min(10, self.vehicle_capacity // 3) + 1)

            arrival_time = window_start + self.rng.uniform(0, window_duration_min)
            tw_start = arrival_time + self.time_window_min
            tw_end = arrival_time + self.time_window_max

            order = Order(
                order_id=self.order_counter,
                location=(x, y),
                demand=demand,
                arrival_time=arrival_time,
                tw_start=tw_start,
                tw_end=tw_end,
            )
            self.order_counter += 1
            self.all_orders.append(order)
            self.pending_orders.append(order)

    def _assign_orders_to_stores(self):
        """Assign pending orders to nearest dark store."""
        for order in self.pending_orders:
            if order.assigned_store is not None:
                continue
            min_dist = float("inf")
            best_store = 0
            for store in self.dark_stores:
                dist = np.sqrt(
                    (order.location[0] - store.location[0]) ** 2
                    + (order.location[1] - store.location[1]) ** 2
                )
                if dist < min_dist:
                    min_dist = dist
                    best_store = store.store_id
            order.assigned_store = best_store

    def _build_vrp_instance(self, store_id: int) -> Optional[VRPProblem]:
        """Build a temporary VRP instance for a store's pending orders.

        Args:
            store_id: Dark store ID

        Returns:
            VRPProblem instance or None if no orders for this store
        """
        store = self.dark_stores[store_id]
        store_orders = [
            o for o in self.pending_orders
            if o.assigned_store == store_id and o.status == "pending"
        ]

        if not store_orders:
            return None

        # Build node list: depot (store) + customers (orders)
        nodes = [store.location]
        demands = [0]  # Depot has no demand

        for order in store_orders:
            nodes.append(order.location)
            demands.append(order.demand)

        # Create VRP problem without loading from file
        problem = VRPProblem()
        problem.nodes = nodes
        problem.demands = demands
        problem.dimension = len(nodes)
        problem.capacity = self.vehicle_capacity
        problem.depot_index = 0
        problem.avg_speed = self.avg_speed
        problem.service_time = self.service_time
        problem.compute_distance_matrix()

        return problem

    def _solve_vrp(
        self,
        problem: VRPProblem,
        algorithm_class: Type[MetaheuristicAlgorithm],
        algo_params: Dict[str, Any],
        fes_budget: int,
    ) -> Tuple[List[List[int]], float]:
        """Solve a VRP instance using the given algorithm.

        Args:
            problem: VRP problem instance
            algorithm_class: Metaheuristic class
            algo_params: Additional algorithm parameters
            fes_budget: Function evaluation budget

        Returns:
            Tuple of (routes, fitness_value)
        """
        iterations = max(1, fes_budget // self.population_size)

        algo = algorithm_class(
            problem=problem,
            population_size=self.population_size,
            max_iterations=iterations,
            seed=self.rng.randint(0, 2**31),
            **algo_params,
        )

        best = algo.execute()

        if hasattr(best, "position"):
            routes, distance, _ = problem.decode_solution(best.position)
            fitness = best.fitness()
        else:
            # Fallback
            routes, distance, _ = problem.decode_solution(
                np.random.rand(problem.get_dimension())
            )
            fitness = distance

        return routes, fitness

    def _simulate_deliveries(
        self,
        store_id: int,
        routes: List[List[int]],
        current_time: float,
    ):
        """Simulate delivery execution for routes from a store.

        Updates order status and delivery times based on route execution.

        Args:
            store_id: Dark store ID
            routes: List of routes (each route is list of node indices)
            current_time: Current simulation time (minutes)
        """
        store = self.dark_stores[store_id]
        store_orders = [
            o for o in self.pending_orders
            if o.assigned_store == store_id and o.status == "pending"
        ]

        # Map route node indices to orders (node 0 = depot, node i = store_orders[i-1])
        vehicle_idx = 0
        for route in routes:
            if vehicle_idx >= store.n_vehicles:
                break

            route_time = current_time
            route_travel = 0.0
            prev_node = 0  # Start at depot

            for node in route[1:-1]:  # Skip depot at start/end
                order_idx = node - 1  # Node 1 maps to store_orders[0]
                if 0 <= order_idx < len(store_orders):
                    order = store_orders[order_idx]

                    # Calculate travel time from previous node
                    if prev_node == 0:
                        prev_loc = store.location
                    else:
                        prev_order_idx = prev_node - 1
                        if 0 <= prev_order_idx < len(store_orders):
                            prev_loc = store_orders[prev_order_idx].location
                        else:  # pragma: no cover – prev_node always valid (set on line 347)
                            prev_loc = store.location

                    dist = np.sqrt(
                        (order.location[0] - prev_loc[0]) ** 2
                        + (order.location[1] - prev_loc[1]) ** 2
                    )
                    travel_time = (dist / self.avg_speed) * 60  # minutes
                    route_time += travel_time + self.service_time
                    route_travel += travel_time + self.service_time

                    # Record delivery
                    order.delivery_time = route_time
                    if route_time <= order.tw_end:
                        order.status = "delivered"
                        self.completed_orders.append(order)
                    else:
                        order.status = "failed"
                        self.failed_orders.append(order)

                    prev_node = node

            # Track vehicle travel time
            if vehicle_idx < len(store.vehicle_travel_times):
                store.vehicle_travel_times[vehicle_idx] += route_travel
            vehicle_idx += 1

        # Remove processed orders from pending
        processed_ids = {o.order_id for o in store_orders if o.status != "pending"}
        self.pending_orders = [
            o for o in self.pending_orders if o.order_id not in processed_ids
        ]

    def fitness_tricriterion(
        self,
        routes: List[List[int]],
        problem: VRPProblem,
        store_orders: List[Order],
        current_time: float,
    ) -> float:
        """Compute tricriterion fitness as per Eq.1 of the paper.

        Z = w1 * total_distance + w2 * sum(max(0, arrival_i - deadline_i))
            + w3 * std(workload_k)

        Args:
            routes: Solution routes
            problem: VRP problem instance
            store_orders: Orders assigned to this store
            current_time: Current simulation time

        Returns:
            Combined fitness value
        """
        w1, w2, w3 = self.omega_weights

        # Component 1: Total distance
        total_distance = 0.0
        for route in routes:
            for i in range(len(route) - 1):
                if route[i] < problem.distance_matrix.shape[0] and \
                   route[i + 1] < problem.distance_matrix.shape[0]:
                    total_distance += problem.distance_matrix[route[i], route[i + 1]]

        # Component 2: Time window violations
        tw_violation = 0.0
        workloads = []
        for route in routes:
            route_time = current_time
            route_workload = 0.0
            prev_node = 0

            for node in route[1:-1]:
                order_idx = node - 1
                if 0 <= order_idx < len(store_orders):
                    order = store_orders[order_idx]
                    # Estimate travel time
                    if prev_node < problem.distance_matrix.shape[0] and \
                       node < problem.distance_matrix.shape[0]:
                        dist = problem.distance_matrix[prev_node, node]
                    else:
                        dist = 0
                    travel_time = (dist / self.avg_speed) * 60
                    route_time += travel_time + self.service_time
                    route_workload += travel_time + self.service_time

                    # Violation: how much we exceed the deadline
                    violation = max(0, route_time - order.tw_end)
                    tw_violation += violation

                    prev_node = node

            workloads.append(route_workload)

        # Component 3: Workload balance (std of workloads)
        wl_std = np.std(workloads) if workloads else 0.0

        return w1 * total_distance + w2 * tw_violation + w3 * wl_std

    def run_simulation(
        self,
        algorithm_class: Type[MetaheuristicAlgorithm],
        algo_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run the full QC-DVRP simulation with rolling horizon.

        Args:
            algorithm_class: Metaheuristic algorithm class to use
            algo_params: Additional parameters for the algorithm

        Returns:
            Dictionary with simulation results and metrics
        """
        if algo_params is None:
            algo_params = {}

        # Reset state
        self.all_orders = []
        self.pending_orders = []
        self.completed_orders = []
        self.failed_orders = []
        self.order_counter = 0

        # Setup dark stores
        self._setup_dark_stores()

        # Calculate rolling horizon parameters
        window_duration_min = self.rolling_horizon_window / 60.0  # Convert seconds to minutes
        n_windows = int(self.simulation_horizon / window_duration_min)
        fes_per_window = max(
            self.population_size,
            self.max_fes // max(1, n_windows * self.n_dark_stores),
        )

        start_time = time.time()

        # Rolling horizon loop
        for w in range(n_windows):
            window_start = w * window_duration_min

            # 1. Generate new orders via Poisson process
            self._generate_orders(window_start, window_duration_min)

            if not self.pending_orders:
                continue

            # 2. Assign orders to nearest dark store
            self._assign_orders_to_stores()

            # 3. For each store, build and solve VRP
            for store in self.dark_stores:
                problem = self._build_vrp_instance(store.store_id)
                if problem is None:
                    continue

                # Skip if too few customers (some algorithms fail with dim<2)
                if problem.dimension <= 2:
                    # Trivial case: 0 or 1 customer, assign directly
                    store_orders = [
                        o for o in self.pending_orders
                        if o.assigned_store == store.store_id
                        and o.status == "pending"
                    ]
                    for order in store_orders:
                        dist = math.sqrt(
                            (order.location[0] - store.location[0]) ** 2
                            + (order.location[1] - store.location[1]) ** 2
                        )
                        travel_time = (dist / self.avg_speed) * 60
                        order.delivery_time = window_start + travel_time + self.service_time
                        if order.delivery_time <= order.tw_end:
                            order.status = "completed"
                            self.completed_orders.append(order)
                        else:
                            order.status = "failed"
                            self.failed_orders.append(order)
                    self.pending_orders = [
                        o for o in self.pending_orders if o.status == "pending"
                    ]
                    continue

                # Solve with metaheuristic
                routes, _ = self._solve_vrp(
                    problem, algorithm_class, algo_params, fes_per_window
                )

                # 4. Simulate deliveries
                self._simulate_deliveries(store.store_id, routes, window_start)

        execution_time = time.time() - start_time

        # Mark remaining pending as failed
        for order in self.pending_orders:
            order.status = "failed"
            self.failed_orders.append(order)
        self.pending_orders = []

        # Compute final metrics
        return self._compute_metrics(execution_time)

    def _compute_metrics(self, execution_time: float) -> Dict[str, Any]:
        """Compute ADT, DSR, WBI metrics from simulation results.

        Returns:
            Dictionary with all metrics
        """
        total_orders = len(self.all_orders)

        # ADT: Average Delivery Time (only for completed orders)
        if self.completed_orders:
            delivery_times = [
                o.delivery_time - o.arrival_time
                for o in self.completed_orders
                if o.delivery_time is not None
            ]
            adt = np.mean(delivery_times) if delivery_times else float("inf")
        else:
            adt = float("inf")

        # DSR: Delivery Success Rate (% delivered within time window)
        if total_orders > 0:
            on_time = sum(
                1 for o in self.completed_orders
                if o.delivery_time is not None and o.delivery_time <= o.tw_end
            )
            dsr = (on_time / total_orders) * 100
        else:
            dsr = 0.0

        # WBI: Workload Balance Index (std of vehicle travel times)
        all_travel_times = []
        for store in self.dark_stores:
            all_travel_times.extend(store.vehicle_travel_times)
        wbi = np.std(all_travel_times) if all_travel_times else 0.0

        # Total fitness (tricriterion Z)
        w1, w2, w3 = self.omega_weights
        total_distance = sum(
            np.sqrt(
                (o.location[0] - self.dark_stores[o.assigned_store].location[0]) ** 2
                + (o.location[1] - self.dark_stores[o.assigned_store].location[1]) ** 2
            )
            for o in self.all_orders
            if o.assigned_store is not None
        )
        total_tw_violation = sum(
            max(0, o.delivery_time - o.tw_end)
            for o in self.completed_orders
            if o.delivery_time is not None
        ) + sum(
            self.time_window_max
            for o in self.failed_orders
        )
        fitness_z = w1 * total_distance + w2 * total_tw_violation + w3 * wbi

        return {
            "adt": adt,
            "dsr": dsr,
            "wbi": wbi,
            "fitness": fitness_z,
            "total_orders": total_orders,
            "completed_orders": len(self.completed_orders),
            "failed_orders": len(self.failed_orders),
            "execution_time": execution_time,
            "n_windows": int(self.simulation_horizon / (self.rolling_horizon_window / 60.0)),
        }
