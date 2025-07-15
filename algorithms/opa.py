"""Orca Predator Algorithm (OPA).

This module implements the Orca Predator Algorithm, inspired by the
sophisticated hunting strategies of killer whales (orcas).

The algorithm models orca hunting behaviors:
1. Chasing phase: High-speed pursuit of prey
2. Attacking phase: Coordinated attack strategies
3. Driving phase: Herding prey into tight groups

OPA uses a unique direct route manipulation approach for VRP problems.

Reference:
    Jiang, Y., Wu, Q., Zhu, S., & Zhang, L. (2021).
    Orca Predation Algorithm: A Novel Bio-Inspired Algorithm for Global
    Optimization Problems.
    Expert Systems with Applications, 188, 116026.
    DOI: 10.1016/j.eswa.2021.116026

Example:
    >>> from algorithms.opa import OPA
    >>> from problems.vrp import VRPProblem
    >>>
    >>> # Load a VRP instance
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>>
    >>> # Initialize and run OPA
    >>> algo = OPA(problem, population_size=30)
    >>> algo.initialize_population()
    >>> best_solution = algo.run(iterations=100)
"""
import copy
import random
import numpy as np
import time
from algorithms.base import Individual, MetaheuristicAlgorithm


class Orca(Individual):
    """An orca (VRP solution) with route-based representation."""

    def __init__(self, problem):
        self.problem = problem
        # Initialize with random routes directly
        self.position = self.problem.random_routes()
        self._fitness = None
        self.personal_best_position = copy.deepcopy(self.position)
        self.personal_best_fitness = self.fitness()

    def copy(self, other=None):
        """Copy method that follows the base class interface.

        Args:
            other: If provided, copy attributes from other to self.
                   If None, return a deep copy of self.

        Returns:
            Orca: A new Orca instance if other is None, otherwise None
        """
        if other is None:
            return copy.deepcopy(self)
        else:
            # Copy attributes from other to self
            self.position = copy.deepcopy(other.position)
            self._fitness = other._fitness
            self.personal_best_position = copy.deepcopy(other.personal_best_position)
            self.personal_best_fitness = other.personal_best_fitness
            return None

    def move(self, population, iteration, max_iterations):
        """Not used in OPA - update() method is used instead.

        This method is required by the base class but OPA uses a different
        update mechanism that works directly with route representations.
        """
        # Not used directly, update is used instead
        pass

    def fitness(self):
        """Calculate and return the fitness value using direct route evaluation.

        Returns:
            float: The fitness value (total cost) of the current route configuration
        """
        if self._fitness is None:
            # Direct evaluation using routes
            self._fitness = self.problem.evaluate_routes(self.position)
        return self._fitness

    def is_feasible(self):
        """Check if the orca's route configuration is feasible.

        Returns:
            bool: True if all routes satisfy capacity and other constraints
        """
        return bool(self.problem.routes_are_feasible(self.position))

    # --- util operators --------------------------------------------------
    def _random_swap(self, routes):
        """Swap two random customers between two different routes."""
        non_empty = [r for r in routes if len(r) > 2]  # Routes with at least one customer
        if len(non_empty) < 2:
            return
        r1, r2 = random.sample(non_empty, 2)
        # Choose random customers (excluding depot at start and end)
        i = random.randrange(1, len(r1) - 1) if len(r1) > 2 else 1
        j = random.randrange(1, len(r2) - 1) if len(r2) > 2 else 1
        r1[i], r2[j] = r2[j], r1[i]

    def _two_opt(self, route):
        """Apply 2-opt to a single route."""
        if len(route) < 4:  # Route must have at least 2 customers
            return
        # Choose two positions within the route (excluding depot)
        i = random.randrange(1, len(route) - 2)
        k = random.randrange(i + 1, len(route) - 1)
        # Reverse the segment between i and k
        route[i : k + 1] = list(reversed(route[i : k + 1]))

    def _relocate(self, routes, leader_routes):
        """
        Move a customer from a random route to another position.
        If leader_routes is provided, preferentially insert into one of these routes.
        """
        # Identify routes with at least one customer
        src_candidates = [r for r in routes if len(r) > 2]
        if not src_candidates:
            return  # No routes with customers

        # Choose source route and customer to move
        src = random.choice(src_candidates)
        idx = random.randrange(1, len(src) - 1)  # Choose a customer (not depot)
        cust = src.pop(idx)

        # If source route only has depots left, remove it
        if len(src) <= 2:
            routes.remove(src)

        # Choose destination route, preferentially from leader
        dst_candidates = []
        if leader_routes:
            dst_candidates = [r for r in leader_routes if r != src]

        # If no leader routes, use any other existing route
        if not dst_candidates:
            dst_candidates = [r for r in routes if r != src]

        # If no destination routes, create a new one
        if not dst_candidates:
            new_route = [0, cust, 0]  # New route with depot - customer - depot
            routes.append(new_route)
            return

        # Insert into destination route
        dst = random.choice(dst_candidates)
        insert_pos = random.randrange(
            1, len(dst)
        )  # Position after initial depot
        dst.insert(insert_pos, cust)

    def update(self, g_best, phase, accept_prob):
        """
        Update the Orca's position according to phase and probability.

        Args:
            g_best: Global best position (leader's routes)
            phase: "chase" for exploration, "attack" for exploitation
            accept_prob: Probability of accepting worse solutions
        """
        # Create a copy of current position to modify
        new_pos = copy.deepcopy(self.position)

        # Apply operators according to phase
        if phase == "chase":  # Exploration phase
            self._random_swap(new_pos)
            candidates_2opt = [r for r in new_pos if len(r) >= 4]
            if candidates_2opt:
                route_for_2opt = random.choice(candidates_2opt)
                self._two_opt(route_for_2opt)
        else:  # Attack phase (exploitation)
            self._relocate(new_pos, g_best)

        # Repair solution if problem offers that functionality
        if hasattr(self.problem, "repair_routes"):
            new_pos = self.problem.repair_routes(new_pos)

        # Check feasibility
        if not self.problem.routes_are_feasible(new_pos):
            return  # Don't update if not feasible

        # Evaluate new position
        new_fit = self.problem.evaluate_routes(new_pos)

        # Update if improved or according to acceptance probability
        if new_fit < self.fitness() or random.random() < accept_prob:
            self.position = new_pos
            self._fitness = new_fit
            # Update personal best position if applicable
            if new_fit < self.personal_best_fitness:
                self.personal_best_position = copy.deepcopy(new_pos)
                self.personal_best_fitness = new_fit


class OPA(MetaheuristicAlgorithm):
    """
    Orca Predator Algorithm (OPA) - Adapted for Vehicle Routing Problem (VRP)
    Inspired by: Jiang et al. (2021)

    This implementation works directly with route representation for VRP.
    """

    def __init__(self, problem, population_size=40, max_iterations=1000, seed=None):
        super().__init__(problem, population_size, max_iterations, seed)
        self.current_iter = 0
        self.population = []
        self.best_solution = None
        self.convergence_curve = []

    def initialize_population(self) -> None:
        """Initialize the orca population with random solutions."""
        if self.seed is not None:
            random.seed(self.seed)
            np.random.seed(self.seed)

        self.population = [Orca(self.problem) for _ in range(self.population_size)]
        self.best_solution = min(self.population, key=lambda o: o.fitness()).copy()
        self.convergence_curve = [self.best_solution.fitness()]
        self.current_iter = 0

    def update_population(self) -> None:
        """Update the population for one iteration."""
        # Determine current phase and acceptance probability
        frac = self.current_iter / self.max_iterations
        phase = "chase" if frac < 0.5 else "attack"
        accept_prob = 0.3 * (1 - frac)

        # Get current global best position
        leader_pos = copy.deepcopy(self.best_solution.position)

        # Update each orca
        for orca in self.population:
            orca.update(leader_pos, phase, accept_prob)

        # Update global best solution
        current_best = min(self.population, key=lambda o: o.fitness())
        if current_best.is_better_than(self.best_solution):
            self.best_solution = current_best.copy()

        # Update convergence curve
        self.convergence_curve.append(self.best_solution.fitness())
        self.current_iter += 1

    def execute(self):
        """Ejecuta el algoritmo completo."""
        self.start_time = time.time()
        self.initialize_population()
        try:
            for _ in range(self.max_iterations):
                self.update_population()
        finally:
            self.end_time = time.time()
        return self.best_solution

    def get_execution_time(self):
        """Retorna el tiempo de ejecución en segundos."""
        return self.end_time - self.start_time

    def get_convergence_curve(self):
        """Retorna la curva de convergencia."""
        return self.convergence_curve
