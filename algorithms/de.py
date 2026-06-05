"""
Differential Evolution (DE/rand/1/bin)
======================================

Classic Differential Evolution, strategy DE/rand/1/bin, faithful to
Storn & Price (1997). Population of ``NP`` real vectors. Each generation,
for every target ``x_i`` a mutant (donor) is built from three distinct random
members, a trial is formed by binomial crossover, and greedy selection keeps
the better of trial vs target. Generation is SYNCHRONOUS (children buffered and
committed at the end of the generation).

Spec (Storn & Price 1997):
    NP = population_size
    F  = 0.8          differential weight / scale factor
    CR = 0.9          crossover probability
    Mutation (rand/1):  v_i = x_r1 + F * (x_r2 - x_r3),  r1,r2,r3 distinct, != i
    Crossover (bin):    u_{i,j} = v_{i,j} if rand_j <= CR or j == j_rand
                                  else x_{i,j}   (j_rand guarantees u != x_i)
    Selection (greedy): x_i(next) = u_i if f(u_i) <= f(x_i) else x_i
    Bound repair:       out-of-range component -> uniform reinit in [lb, ub]

References:
    Storn, R., & Price, K. (1997). Differential Evolution - A Simple and
    Efficient Heuristic for Global Optimization over Continuous Spaces.
    Journal of Global Optimization, 11(4), 341-359.
"""

import numpy as np
from typing import Any
from algorithms.base import MetaheuristicAlgorithm, Individual


class DEVector(Individual):
    """A real-valued candidate solution in the DE population."""

    def __init__(self, dimension: int, problem: Any, rng=None,
                 lower_bounds=None, upper_bounds=None, position=None):
        self.dimension = dimension
        self.problem = problem
        self.rng = rng if rng is not None else np.random.default_rng()

        # Bounds: default to [0, 1] (e.g. random-key VRP) when not provided.
        if lower_bounds is None:
            lower_bounds = np.zeros(dimension)
        if upper_bounds is None:
            upper_bounds = np.ones(dimension)
        self.lower_bounds = np.asarray(lower_bounds, dtype=float)
        self.upper_bounds = np.asarray(upper_bounds, dtype=float)

        if position is None:
            self.position = self.rng.uniform(
                self.lower_bounds, self.upper_bounds, dimension
            )
        else:
            self.position = np.asarray(position, dtype=float)
        self._fitness = None

    def fitness(self) -> float:
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self) -> bool:
        return bool(self.problem.is_valid(self.position))

    def copy(self, other: 'DEVector') -> None:
        self.position = other.position.copy()
        self._fitness = other._fitness

    def move(self, population: list = None, iteration: int = 0,
             max_iterations: int = 100) -> None:
        """Movement is orchestrated by DE.update_population()."""
        pass


class DE(MetaheuristicAlgorithm):
    """Differential Evolution DE/rand/1/bin (Storn & Price, 1997).

    Same interface as :class:`PSO`: reads ``get_lower_bounds`` /
    ``get_upper_bounds`` from the problem (fallback ``[0, 1]^D``), exposes
    ``initialize_population`` / ``update_population`` and tracks
    ``best_solution`` and ``convergence_curve``.
    """

    def __init__(self, problem: Any, population_size: int = 30,
                 max_iterations: int = 100, seed: int = None,
                 F: float = 0.8, CR: float = 0.9,
                 use_il: bool = False, il_model: Any = None):
        super().__init__(problem, population_size, max_iterations, seed)

        self.dimension = self.problem.get_dimension()
        self.F = float(F)
        self.CR = float(CR)

        # IL hooks (neutral by default).
        self.use_il = use_il
        self.il_model = il_model

        # Bounds (fallback to [0, 1]^D when the problem does not expose them).
        self.lower_bounds = np.asarray(
            getattr(self.problem, "get_lower_bounds",
                    lambda: np.zeros(self.dimension))(),
            dtype=float,
        )
        self.upper_bounds = np.asarray(
            getattr(self.problem, "get_upper_bounds",
                    lambda: np.ones(self.dimension))(),
            dtype=float,
        )

    def _get_il_params(self, iteration: int) -> tuple:
        """Predict IL modulation factors or return neutral (1.0, 1.0).

        Returns ``(mF, mCR)`` multipliers applied as ``F_eff = F * mF`` and
        ``CR_eff = clip(CR * mCR, 0, 1)``. Neutral (1.0, 1.0) reduces exactly
        to standard DE; a future IL model can adapt them online.
        """
        if not self.use_il or self.il_model is None:
            return 1.0, 1.0
        try:
            mF, mCR = self.il_model.predict(self, iteration)
            return float(mF), float(mCR)
        except Exception:
            return 1.0, 1.0

    def initialize_population(self) -> None:
        """Initialize NP random vectors uniformly within the bounds."""
        self.population = []
        for _ in range(self.population_size):
            ind = DEVector(
                dimension=self.dimension,
                problem=self.problem,
                rng=self.rng,
                lower_bounds=self.lower_bounds,
                upper_bounds=self.upper_bounds,
            )
            ind.fitness()
            self.population.append(ind)

        self.best_solution = min(self.population, key=lambda v: v.fitness())
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self) -> None:
        """One synchronous DE/rand/1/bin generation."""
        iteration = len(self.convergence_curve) - 1
        NP = self.population_size
        D = self.dimension

        # IL modulation (neutral by default).
        mF, mCR = self._get_il_params(iteration)
        F_eff = self.F * mF
        CR_eff = float(np.clip(self.CR * mCR, 0.0, 1.0))

        positions = np.array([v.position for v in self.population], dtype=float)
        next_population = []

        for i in range(NP):
            # Pick r1, r2, r3 distinct and != i (DE/rand/1).
            choices = [j for j in range(NP) if j != i]
            r1, r2, r3 = self.rng.choice(choices, size=3, replace=False)

            # Mutation: v = x_r1 + F * (x_r2 - x_r3)
            v = positions[r1] + F_eff * (positions[r2] - positions[r3])

            # Binomial crossover with guaranteed index j_rand.
            x_i = positions[i]
            j_rand = int(self.rng.integers(0, D))
            cross_mask = self.rng.random(D) <= CR_eff
            cross_mask[j_rand] = True
            u = np.where(cross_mask, v, x_i)

            # Bound repair: out-of-range components -> uniform reinit.
            oob = (u < self.lower_bounds) | (u > self.upper_bounds)
            if oob.any():
                reinit = self.rng.uniform(self.lower_bounds, self.upper_bounds, D)
                u = np.where(oob, reinit, u)

            # Greedy selection (minimization, <= keeps the original convention).
            trial = DEVector(
                dimension=D, problem=self.problem, rng=self.rng,
                lower_bounds=self.lower_bounds, upper_bounds=self.upper_bounds,
                position=u,
            )
            if trial.fitness() <= self.population[i].fitness():
                next_population.append(trial)
            else:
                next_population.append(self.population[i])

        # Synchronous update.
        self.population = next_population

        gen_best = min(self.population, key=lambda v: v.fitness())
        if gen_best.fitness() < self.best_solution.fitness():
            self.best_solution = gen_best
        self.convergence_curve.append(self.best_solution.fitness())

    def get_parameters(self) -> dict:
        """Get algorithm parameters for reporting."""
        return {
            'algorithm': 'DE/rand/1/bin',
            'population_size': self.population_size,
            'max_iterations': self.max_iterations,
            'F': self.F,
            'CR': self.CR,
            'seed': self.seed,
        }
