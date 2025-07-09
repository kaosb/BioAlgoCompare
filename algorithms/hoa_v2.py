"""
Hippopotamus Optimization Algorithm (HOA) - Version 2

This module implements the Hippopotamus Optimization Algorithm (HOA) based on
the paper by Amiri et al. (2024), adapted for discrete optimization problems
like the VRP.
"""

import numpy as np
import random
import copy
from typing import List, Tuple

from algorithms.base_v2_migration import MetaheuristicAlgorithm, Individual, MoveContext
from problems.vrp_v2 import VRPProblemV2


class HOAIndividual(Individual):
    """
    Represents an individual solution in the HOA algorithm.
    The 'position' is a list of routes, suitable for the VRP.
    """

    def __init__(self, problem: VRPProblemV2):
        super().__init__(problem)
        self.position: List[List[int]] = []

    def initialize(self) -> None:
        """Initializes the individual with a random, feasible VRP solution."""
        self.position = self.problem.random_solution()

    def move(self, context: MoveContext) -> None:
        """
        Moves the individual according to the HOA logic, adapted for discrete VRP.

        Args:
            context: The context object with all necessary data for the move.
        """
        # HOA parameters from the paper (can be tuned)
        p = 0.5  # Probability to switch between phases 1 and 2
        l = context.iteration / context.max_iterations # Ratio of current iteration

        # --- Phase 1: Position updating (Exploitation) ---
        if np.random.rand() < p:
            # This phase moves the hippo towards the best solution
            # We model this with a guided local search operator
            new_position = self._relocate_towards_best(context.best_individual.position)
        
        # --- Phase 2: Group defense (Exploitation) ---
        else:
            # This phase models group defense, we adapt it as a crossover
            # between the current individual and a random one from the population.
            other_individual = random.choice(context.population)
            if other_individual is not self:
                new_position = self._crossover(other_individual.position)
            else:
                new_position = self.position # No change if same individual is chosen

        # --- Phase 3: Predator evasion (Exploration) ---
        # This phase is applied on top of the previous result to add exploration
        # The probability of this phase increases as iterations pass
        if np.random.rand() < (0.1 + 0.8 * l**2): # Increasing probability
            final_position = self._scramble_mutation(new_position)
        else:
            final_position = new_position

        # Final check: repair the solution to ensure feasibility
        self.position = self.problem.repair(final_position)
        self.invalidate_fitness()

    # --- Discrete Operators (Adaptations of HOA equations) ---

    def _relocate_towards_best(self, best_position: List[List[int]]) -> List[List[int]]:
        """ 
        Operator inspired by moving towards the best. 
        Picks a customer and tries to move it to a better position, 
        mimicking the attraction to the best-known solution.
        """
        new_pos = copy.deepcopy(self.position)
        if not new_pos:
            return self.position

        # Pick a random route and a customer from it
        route_idx = random.randrange(len(new_pos))
        route = new_pos[route_idx]
        if len(route) <= 2: # Only depot
            return self.position

        customer_idx_in_route = random.randrange(1, len(route) - 1)
        customer_to_move = route.pop(customer_idx_in_route)

        # Find the best place to re-insert the customer (in any route)
        best_insertion_cost = float('inf')
        best_insertion_pos = (route_idx, customer_idx_in_route) # (route, index_in_route)

        for r_idx, r in enumerate(new_pos):
            for i in range(1, len(r)):
                # Calculate cost of inserting customer_to_move at this position
                r.insert(i, customer_to_move)
                cost = self.problem.evaluate(new_pos)
                r.pop(i) # Backtrack

                if cost < best_insertion_cost:
                    best_insertion_cost = cost
                    best_insertion_pos = (r_idx, i)

        # Perform the best insertion
        best_route_idx, best_idx_in_route = best_insertion_pos
        new_pos[best_route_idx].insert(best_idx_in_route, customer_to_move)
        
        return new_pos

    def _crossover(self, other_position: List[List[int]]) -> List[List[int]]:
        """
        Operator inspired by group defense. 
        Creates a new solution by combining routes from self and another individual.
        """
        # Simple crossover: take some routes from self, some from other
        num_routes_self = random.randint(1, len(self.position))
        
        new_pos = copy.deepcopy(self.position[:num_routes_self])
        
        # Add routes from other_position if they don't introduce duplicate customers
        customers_in_new_pos = {c for r in new_pos for c in r[1:-1]}
        
        for route in other_position:
            has_duplicates = any(c in customers_in_new_pos for c in route[1:-1])
            if not has_duplicates:
                new_pos.append(copy.deepcopy(route))
                for c in route[1:-1]:
                    customers_in_new_pos.add(c)

        return new_pos

    def _scramble_mutation(self, position: List[List[int]]) -> List[List[int]]:
        """
        Operator inspired by predator evasion.
        Applies a strong mutation (scramble) to a random route for exploration.
        """
        new_pos = copy.deepcopy(position)
        if not new_pos:
            return position

        route_idx = random.randrange(len(new_pos))
        route_to_scramble = new_pos[route_idx][1:-1] # Exclude depot
        
        if len(route_to_scramble) > 1:
            random.shuffle(route_to_scramble)
            new_pos[route_idx] = [self.problem.depot_index] + route_to_scramble + [self.problem.depot_index]

        return new_pos


class HOAV2(MetaheuristicAlgorithm[HOAIndividual]):
    """
    The Hippopotamus Optimization Algorithm (HOA) v2, adapted for VRP.
    """

    def __init__(self, problem: VRPProblemV2, population_size: int = 50, max_iterations: int = 100, seed: int = None):
        super().__init__(problem, population_size, max_iterations, seed)

    def _create_individual(self) -> HOAIndividual:
        """Factory method to create a new HOA individual."""
        return HOAIndividual(self.problem)

    def _create_move_context(self) -> MoveContext:
        """
        Creates the context for the HOA move.
        """
        return MoveContext(
            iteration=self.iteration,
            max_iterations=self.max_iterations,
            population=self.population,
            best_individual=self.best_solution
        )