"""
Ant Colony Optimization for Continuous Domains (ACO_R)
=====================================================

ACO_R extends the Ant Colony Optimization metaphor to continuous search
spaces. Instead of a discrete pheromone matrix, ACO_R maintains an *archive*
``T`` of the ``k`` best solutions found so far, sorted in ascending order by
objective value (minimization). Each solution in the archive acts as the mean
of a Gaussian kernel; the set of all archive solutions forms a Gaussian kernel
PDF per dimension. At every iteration ``m`` ants sample new solutions from this
kernel PDF, the new solutions are merged into the archive, and only the ``k``
best are retained.

Spec (faithful to Socha & Dorigo 2008, Table 2 defaults):
    m  = 2          ants per iteration
    k  = archive size (here ``max(50, population_size)``, requires ``k >= D``)
    q  = 1e-4       locality of the search (smaller -> exploit best solutions)
    xi = 0.85       speed of convergence (pheromone evaporation analogue)

Per iteration:
    1. Rank weights for archive position ``l = 1..k``:
           w_l = exp(-(l-1)^2 / (2 q^2 k^2))
           p_l = w_l / sum_e w_e
    2. For each ant:
           - choose a single guiding solution index ``l`` ~ {p_l}
             (the SAME ``l`` is used for every dimension of that ant)
           - for each dimension ``i``:
                 sigma_i = xi * sum_{e=1..k} |s_e[i] - s_l[i]| / (k - 1)
                 x_new[i] = s_l[i] + sigma_i * N(0, 1)
           - repair to bounds
    3. Evaluate the ``m`` new solutions, merge into archive, re-sort
       ascending by ``f`` and keep the ``k`` best.

References:
    Socha, K., & Dorigo, M. (2008). Ant colony optimization for continuous
    domains. European Journal of Operational Research, 185(3), 1155-1173.
"""

import numpy as np
from typing import Any, Optional
from algorithms.base import MetaheuristicAlgorithm, Individual


class Ant(Individual):
    """A solution in the ACO_R archive (a candidate point in R^D)."""

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
        """Calculate and cache fitness value."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self) -> bool:
        """Check whether the position represents a feasible solution."""
        return bool(self.problem.is_valid(self.position))

    def copy(self, other: 'Ant') -> None:
        """Copy values from another ant."""
        self.position = other.position.copy()
        self._fitness = other._fitness

    def move(self, population: list = None, iteration: int = 0,
             max_iterations: int = 100) -> None:
        """Movement is orchestrated by the ACO_R archive update."""
        pass


class ACO(MetaheuristicAlgorithm):
    """Ant Colony Optimization for continuous domains (ACO_R).

    Same interface as :class:`PSO`: reads ``get_lower_bounds`` /
    ``get_upper_bounds`` from the problem (fallback ``[0, 1]^D``), exposes
    ``initialize_population`` / ``update_population`` and tracks
    ``best_solution`` and ``convergence_curve``.
    """

    def __init__(self, problem: Any, population_size: int = 30,
                 max_iterations: int = 100, seed: int = None,
                 m: int = 2, q: float = 1e-4, xi: float = 0.85,
                 archive_size: Optional[int] = None,
                 use_il: bool = False, il_model: Any = None):
        """
        Initialize ACO_R.

        Args:
            problem: Problem instance (continuous box-constrained).
            population_size: Used to size the archive (k = max(50, pop)).
            max_iterations: Maximum number of iterations.
            seed: Random seed for reproducibility.
            m: Number of ants sampled per iteration (Table 2 default = 2).
            q: Locality of the search / weight spread (default = 1e-4).
            xi: Convergence speed, scales sigma (default = 0.85).
            archive_size: Override for k. If None, k = max(50, pop).
            use_il / il_model: Hooks for future Imitation Learning modulation.
        """
        super().__init__(problem, population_size, max_iterations, seed)

        self.dimension = self.problem.get_dimension()
        self.m = int(m)
        self.q = float(q)
        self.xi = float(xi)

        # Archive size k. Spec: k = max(50, population_size), and k >= D.
        if archive_size is None:
            k = max(50, self.population_size)
        else:
            k = int(archive_size)
        if k < self.dimension:
            k = self.dimension
        self.k = int(k)

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

        # Precompute the rank-based selection probabilities p_l (constant
        # across iterations because they depend only on rank, q and k).
        ranks = np.arange(1, self.k + 1)  # l = 1..k
        w = np.exp(-((ranks - 1) ** 2) / (2.0 * (self.q ** 2) * (self.k ** 2)))
        total = w.sum()
        # Guard against numerical underflow (extremely small q*k).
        if not np.isfinite(total) or total <= 0.0:
            w = np.zeros(self.k)
            w[0] = 1.0
            total = 1.0
        self.weights = w
        self.probs = w / total

    def _get_il_params(self, iteration: int) -> tuple:
        """Predict IL modulation factors or return neutral (1.0, 1.0).

        Returns a multiplier pair ``(xi_factor, q_factor)`` applied on top of
        the base ``xi`` and ``q``. Neutral by default; a future IL model can
        override this to adapt exploration/exploitation online.
        """
        if not self.use_il or self.il_model is None:
            return 1.0, 1.0
        try:
            xi_factor, q_factor = self.il_model.predict(self, iteration)
            return float(xi_factor), float(q_factor)
        except Exception:
            return 1.0, 1.0

    def initialize_population(self) -> None:
        """Build the initial archive of k random solutions, sorted by f."""
        self.population = []
        for _ in range(self.k):
            ant = Ant(
                dimension=self.dimension,
                problem=self.problem,
                rng=self.rng,
                lower_bounds=self.lower_bounds,
                upper_bounds=self.upper_bounds,
            )
            ant.fitness()
            self.population.append(ant)

        # Archive T sorted ascending by f.
        self.population.sort(key=lambda a: a.fitness())
        self.population = self.population[:self.k]

        self.best_solution = self.population[0]
        self.convergence_curve = [self.best_solution.fitness()]

    def _sample_ant(self, l_idx: int, xi_eff: float) -> Ant:
        """Sample one new solution guided by archive solution at index l_idx."""
        s_l = self.population[l_idx].position
        # Matrix of all archive positions: shape (k, D).
        archive = np.array([a.position for a in self.population], dtype=float)

        # Per-dimension sigma using the SAME guiding solution l for all dims.
        # sigma_i = xi * sum_{e=1..k} |s_e[i] - s_l[i]| / (k - 1)
        if self.k > 1:
            sigma = xi_eff * np.sum(np.abs(archive - s_l), axis=0) / (self.k - 1)
        else:
            sigma = np.zeros(self.dimension)

        noise = self.rng.standard_normal(self.dimension)
        x_new = s_l + sigma * noise

        # Repair to bounds.
        x_new = np.clip(x_new, self.lower_bounds, self.upper_bounds)

        return Ant(
            dimension=self.dimension,
            problem=self.problem,
            rng=self.rng,
            lower_bounds=self.lower_bounds,
            upper_bounds=self.upper_bounds,
            position=x_new,
        )

    def update_population(self) -> None:
        """One ACO_R iteration: sample m ants, merge into archive, keep k best."""
        iteration = len(self.convergence_curve) - 1

        # IL modulation (neutral by default).
        xi_factor, q_factor = self._get_il_params(iteration)
        xi_eff = self.xi * xi_factor

        if q_factor != 1.0:
            # Recompute selection probabilities under modulated q.
            q_eff = self.q * q_factor
            ranks = np.arange(1, self.k + 1)
            w = np.exp(-((ranks - 1) ** 2) / (2.0 * (q_eff ** 2) * (self.k ** 2)))
            total = w.sum()
            if not np.isfinite(total) or total <= 0.0:
                probs = np.zeros(self.k)
                probs[0] = 1.0
            else:
                probs = w / total
        else:
            probs = self.probs

        new_ants = []
        for _ in range(self.m):
            # Choose a single guiding solution index l ~ {p_l} (once per ant).
            l_idx = int(self.rng.choice(self.k, p=probs))
            ant = self._sample_ant(l_idx, xi_eff)
            ant.fitness()  # evaluate the new solution
            new_ants.append(ant)

        # Pheromone update: T = T + new ants, re-sort ascending, keep k best.
        self.population.extend(new_ants)
        self.population.sort(key=lambda a: a.fitness())
        self.population = self.population[:self.k]

        # Track best and convergence.
        if self.population[0].fitness() < self.best_solution.fitness():
            self.best_solution = self.population[0]
        self.convergence_curve.append(self.best_solution.fitness())

    @property
    def evals_per_iteration(self) -> int:
        """Function evaluations charged per update_population() call (m ants)."""
        return self.m

    def get_parameters(self) -> dict:
        """Get algorithm parameters for reporting."""
        return {
            'algorithm': 'ACO_R',
            'population_size': self.population_size,
            'archive_size_k': self.k,
            'max_iterations': self.max_iterations,
            'ants_per_iter_m': self.m,
            'q': self.q,
            'xi': self.xi,
            'seed': self.seed,
        }
