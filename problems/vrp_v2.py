"""
Module for the VRP Problem, Version 2.

This module provides a VRP problem implementation that aligns with the
v2 architecture, inheriting from AbstractProblem and working directly
with discrete route representations (`List[List[int]]`).
"""

import numpy as np
import math
from typing import List, Tuple, Dict, Set, cast
from collections import Counter

from .base import AbstractProblem

# Constants for penalties, consistent with the original implementation
PENALTY_FACTOR = 1000.0
PENALTY_CAP = PENALTY_FACTOR
PENALTY_MISSING = PENALTY_FACTOR * 10


class VRPProblemV2(AbstractProblem[List[List[int]]]):
    """
    Represents and evaluates VRP (Vehicle Routing Problem) instances.

    This v2 implementation works directly with discrete solutions (a list of routes)
    and is fully compatible with the v2 metaheuristic algorithm architecture.
    """

    def __init__(self, instance_path: str):
        """
        Initializes the VRP problem from a Solomon-formatted instance file.

        Args:
            instance_path: Path to the VRP instance file.
        """
        self.instance_path = instance_path
        self._name: str = ""
        self._dimension: int = 0
        self.capacity: int = 0
        self.depot_index: int = 0
        self.nodes: List[Tuple[float, float]] = []  # List of (x, y) coordinates
        self.demands: List[int] = []
        self.distance_matrix: np.ndarray = np.array([])

        self._load_instance()
        self._compute_distance_matrix()
        
        # Initialize base class
        super().__init__(name=self._name)

    def _load_instance(self) -> None:
        """Loads the instance data from the file."""
        with open(self.instance_path, "r") as f:
            lines = f.readlines()

        # Parse header
        for line in lines:
            line = line.strip()
            if line.startswith("NAME"):
                self._name = line.split(":")[1].strip()
            elif line.startswith("DIMENSION"):
                self._dimension = int(line.split(":")[1].strip())
            elif line.startswith("CAPACITY"):
                self.capacity = int(line.split(":")[1].strip())
            elif line.startswith("NODE_COORD_SECTION"):
                break

        # Pre-allocate lists
        self.nodes = [(0, 0)] * self._dimension
        self.demands = [0] * self._dimension

        # Parse node coordinates and demands
        node_section = False
        demand_section = False
        for line in lines:
            line = line.strip()
            if line == "NODE_COORD_SECTION":
                node_section = True
                demand_section = False
                continue
            if line == "DEMAND_SECTION":
                node_section = False
                demand_section = True
                continue
            if line == "DEPOT_SECTION":
                break

            if node_section:
                parts = line.split()
                if len(parts) >= 3:
                    node_id = int(parts[0]) - 1  # 0-indexed
                    self.nodes[node_id] = (float(parts[1]), float(parts[2]))
            
            if demand_section:
                parts = line.split()
                if len(parts) >= 2:
                    node_id = int(parts[0]) - 1  # 0-indexed
                    demand = int(parts[1])
                    self.demands[node_id] = demand
                    if demand == 0:
                        self.depot_index = node_id

    def _compute_distance_matrix(self) -> None:
        """Computes the Euclidean distance matrix between all nodes."""
        n = self._dimension
        self.distance_matrix = np.zeros((n, n))
        coords = np.array(self.nodes)
        for i in range(n):
            for j in range(i, n):
                dist = np.linalg.norm(coords[i] - coords[j])
                self.distance_matrix[i, j] = dist
                self.distance_matrix[j, i] = dist

    @property
    def dimension(self) -> int:
        """Returns the dimension of the problem (number of customers)."""
        return self._dimension - 1  # Exclude the depot

    def evaluate(self, solution: List[List[int]]) -> float:
        """
        Evaluates a list of routes and returns its fitness (total distance + penalties).

        Args:
            solution: A list of routes, where each route is a list of node indices.

        Returns:
            The fitness value (lower is better).
        """
        self._evaluations += 1
        total_distance, penalties, _ = self.evaluate_detailed(solution)
        
        total_penalty = sum(penalties.values())
        
        return total_distance + total_penalty

    def is_feasible(self, solution: List[List[int]]) -> bool:
        """
        Checks if a solution (list of routes) is feasible.

        Args:
            solution: A list of routes.

        Returns:
            True if the solution is feasible, False otherwise.
        """
        is_feasible, _ = self._check_feasibility(solution)
        return is_feasible

    def random_solution(self) -> List[List[int]]:
        """
        Generates a random, feasible solution using a simple greedy construction.

        Returns:
            A list of routes.
        """
        customers = list(range(1, self._dimension))
        np.random.shuffle(customers)

        routes: List[List[int]] = []
        current_route: List[int] = [self.depot_index]
        current_load = 0

        for customer in customers:
            if current_load + self.demands[customer] > self.capacity:
                current_route.append(self.depot_index)
                routes.append(current_route)
                current_route = [self.depot_index, customer]
                current_load = self.demands[customer]
            else:
                current_route.append(customer)
                current_load += self.demands[customer]
        
        if len(current_route) > 1:
            current_route.append(self.depot_index)
            routes.append(current_route)

        return routes

    def repair(self, solution: List[List[int]]) -> List[List[int]]:
        """
        Repairs an infeasible solution to make it feasible.
        It handles missing and duplicate customers.

        Args:
            solution: The list of routes to repair.

        Returns:
            A repaired, feasible list of routes.
        """
        all_customers_in_solution = [
            node for route in solution for node in route if node != self.depot_index
        ]
        
        # Handle duplicates by order of appearance
        seen = set()
        unique_customers = [
            c for c in all_customers_in_solution if not (c in seen or seen.add(c))
        ]
        
        # Find missing customers
        required_customers = set(range(1, self._dimension))
        missing_customers = list(required_customers - set(unique_customers))
        
        # Re-build routes from unique and missing customers
        customers_to_route = unique_customers + missing_customers
        
        repaired_routes: List[List[int]] = []
        current_route = [self.depot_index]
        current_load = 0

        for customer in customers_to_route:
            if current_load + self.demands[customer] > self.capacity:
                current_route.append(self.depot_index)
                repaired_routes.append(current_route)
                current_route = [self.depot_index, customer]
                current_load = self.demands[customer]
            else:
                current_route.append(customer)
                current_load += self.demands[customer]
        
        if len(current_route) > 1:
            current_route.append(self.depot_index)
            repaired_routes.append(current_route)
            
        return repaired_routes

    def evaluate_detailed(self, solution: List[List[int]]) -> Tuple[float, Dict[str, float], List[str]]:
        """
        Evaluates a solution and provides detailed metrics.

        Args:
            solution: A list of routes.

        Returns:
            A tuple containing:
            - Total distance.
            - A dictionary of penalties (capacity, missing, duplicate).
            - A list of human-readable error messages.
        """
        total_distance = 0.0
        penalties: Dict[str, float] = {"capacity": 0.0, "missing": 0.0, "duplicate": 0.0}
        
        # Calculate distance and capacity penalty
        for route in solution:
            route_distance = 0.0
            route_load = 0
            if len(route) > 1:
                for i in range(len(route) - 1):
                    route_distance += self.distance_matrix[route[i], route[i+1]]
                total_distance += route_distance
                
                route_load = sum(self.demands[node] for node in route[1:-1])
                if route_load > self.capacity:
                    penalties["capacity"] += (route_load - self.capacity) * PENALTY_CAP

        # Check for missing and duplicate customers
        is_feasible, error_messages = self._check_feasibility(solution)
        
        # This is a simplified penalty calculation based on the feasibility check
        if not is_feasible:
            if any("Faltan clientes" in msg for msg in error_messages):
                 penalties["missing"] = PENALTY_MISSING * sum("Faltan clientes" in msg for msg in error_messages)
            if any("Clientes duplicados" in msg for msg in error_messages):
                 penalties["duplicate"] = PENALTY_MISSING * sum("Clientes duplicados" in msg for msg in error_messages)


        return total_distance, penalties, error_messages

    def _check_feasibility(self, solution: List[List[int]]) -> Tuple[bool, List[str]]:
        """Helper method to check all feasibility constraints."""
        error_messages: List[str] = []

        # 1. Check capacity
        for i, route in enumerate(solution):
            load = sum(self.demands[node] for node in route[1:-1])
            if load > self.capacity:
                error_messages.append(f"Ruta {i} excede capacidad: {load} > {self.capacity}")

        # 2. Check customer coverage (missing and duplicates)
        required_customers = set(range(1, self._dimension))
        serviced_customers = set()
        all_serviced_nodes = []
        for route in solution:
            for node in route[1:-1]:
                serviced_customers.add(node)
                all_serviced_nodes.append(node)

        missing = required_customers - serviced_customers
        if missing:
            error_messages.append(f"Faltan clientes: {sorted(list(missing))}")

        counts = Counter(all_serviced_nodes)
        duplicates = [node for node, count in counts.items() if count > 1]
        if duplicates:
            error_messages.append(f"Clientes duplicados: {sorted(duplicates)}")

        return len(error_messages) == 0, error_messages
