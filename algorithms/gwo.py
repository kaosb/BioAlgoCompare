"""Grey Wolf Optimizer (GWO).

This module implements the Grey Wolf Optimizer, a nature-inspired
metaheuristic algorithm that simulates the leadership hierarchy and
hunting mechanism of grey wolves in nature.

The algorithm models four types of wolves:
1. Alpha: Best solution (leader)
2. Beta: Second best solution (advisor)
3. Delta: Third best solution (scout)
4. Omega: Remaining wolves (followers)

Reference:
    Mirjalili, S., Mirjalili, S. M., & Lewis, A. (2014).
    Grey Wolf Optimizer. Advances in Engineering Software, 69, 46-61.
    DOI: 10.1016/j.advengsoft.2013.12.007

Example:
    >>> from algorithms.gwo import GWO
    >>> from problems.vrp import VRPProblem
    >>>
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>>
    >>> algo = GWO(problem, population_size=30)
    >>> best_solution = algo.run(iterations=100)
"""
import numpy as np
import random
from .base import Individual, MetaheuristicAlgorithm


class Wolf(Individual):
    """Individual in the Grey Wolf Optimizer."""

    def __init__(self, problem, rng=None):
        """
        Initialize a wolf with random position.

        Args:
            problem: Problem instance to solve
            rng: NumPy random generator instance
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.rng = rng if rng is not None else np.random.default_rng()
        # Read bounds from the problem when available; default to [0, 1]
        # (e.g. random-key VRP) when the problem does not expose them.
        lo = getattr(problem, "get_lower_bounds", lambda: np.zeros(self.dimension))()
        hi = getattr(problem, "get_upper_bounds", lambda: np.ones(self.dimension))()
        self.lower_bounds = np.asarray(lo, dtype=float)
        self.upper_bounds = np.asarray(hi, dtype=float)
        self.position = self.rng.uniform(self.lower_bounds, self.upper_bounds, self.dimension)
        self._fitness = None

    def fitness(self):
        """Calculate the fitness of this wolf."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self):
        """Check if the solution is feasible."""
        return True  # VRP decoder always produces feasible solutions

    def move(self, population, iteration, max_iterations):
        """Movement logic (handled in GWO.update_population)."""
        pass

    def copy(self, other):
        """
        Copy values from another wolf.

        Args:
            other: Another Wolf individual
        """
        self.position = np.copy(other.position)
        self._fitness = other._fitness


class GWO(MetaheuristicAlgorithm):
    """Grey Wolf Optimizer implementation.

    Models the social hierarchy and hunting behavior of grey wolves.
    Parameter 'a' decreases linearly from 2 to 0 over iterations,
    controlling the transition from exploration to exploitation.
    """

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None,
                 use_il=False, il_model=None):
        """
        Initialize GWO.

        Args:
            problem: Problem instance
            population_size: Wolf pack size
            max_iterations: Maximum iterations
            seed: Random seed for reproducibility
            use_il / il_model: hooks for Imitation-Learning modulation of the
                control coefficient ``a``. Neutral by default.
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.convergence_curve = []
        self.use_il = use_il
        self.il_model = il_model
        self.alpha = None  # Best wolf
        self.beta = None   # Second best
        self.delta = None  # Third best
        self._alpha_score = self._beta_score = self._delta_score = float("inf")

    def _get_il_params(self, iteration):
        """Return a 1-tuple (a_factor,) for the control coefficient; neutral (1.0,)."""
        if not self.use_il or self.il_model is None:
            return (1.0,)
        try:
            out = self.il_model.predict(self, iteration)
            if isinstance(out, (tuple, list, np.ndarray)):
                out = out[0]
            return (float(out),)
        except Exception:
            return (1.0,)

    def initialize_population(self):
        """Initialize the wolf pack and identify alpha, beta, delta."""
        self.population = [Wolf(self.problem, rng=self.rng) for _ in range(self.population_size)]

        # Sort by fitness to find alpha, beta, delta
        self._update_hierarchy()

        self.convergence_curve = [self.alpha.fitness()]

    def _copy_wolf(self, source):
        """Snapshot a wolf (without consuming RNG)."""
        w = object.__new__(Wolf)
        w.problem = source.problem
        w.dimension = source.dimension
        w.rng = self.rng
        w.position = np.copy(source.position)
        w._fitness = source._fitness
        w.lower_bounds = source.lower_bounds
        w.upper_bounds = source.upper_bounds
        return w

    def _consider(self, wolf):
        """Leader update exactly as in the official GWO.m (Mirjalili 2014):

            if f < Alpha_score                       -> alpha
            if f > Alpha_score and f < Beta_score    -> beta
            if f > Alpha_score and f > Beta_score and f < Delta_score -> delta

        Scores start at +inf ONCE and are never reset, so the leaders are
        elitist across iterations (verified 24-Sep-2026 against two
        independent copies of GWO.m). A new alpha does not demote the old one.
        """
        f = wolf.fitness()
        if f < self._alpha_score:
            self._alpha_score = f
            self.alpha = self._copy_wolf(wolf)
        if f > self._alpha_score and f < self._beta_score:
            self._beta_score = f
            self.beta = self._copy_wolf(wolf)
        if f > self._alpha_score and f > self._beta_score and f < self._delta_score:
            self._delta_score = f
            self.delta = self._copy_wolf(wolf)

    def _update_hierarchy(self):
        """Evaluate the pack in index order and update the leaders (GWO.m)."""
        if self.alpha is None:
            # GWO.m initialises Alpha/Beta/Delta_pos = zeros(1, dim), score inf
            template = self.population[0]
            self._alpha_score = self._beta_score = self._delta_score = float("inf")
            self.alpha, self.beta, self.delta = (self._zero_wolf(template) for _ in range(3))
        for wolf in self.population:
            self._consider(wolf)
        self.best_solution = self.alpha

    def _zero_wolf(self, template):
        w = self._copy_wolf(template)
        w.position = np.zeros_like(template.position)
        w._fitness = float("inf")
        return w

    def absorb_injected(self, index):
        """A migrant was written into population[index] and evaluated."""
        self._consider(self.population[index])
        self.best_solution = self.alpha

    def update_population(self):
        """Update the wolf pack positions.

        Parameter a decreases linearly from 2 to 0 (Eq. 3.3).
        Each omega wolf updates position guided by alpha, beta, delta.
        """
        # GWO.m: l = 0 on the first position update, a = 2 - l*2/Max_iter
        t = len(self.convergence_curve) - 1
        T = self.max_iterations

        # IL modulation of the control coefficient (neutral by default).
        (a_factor,) = self._get_il_params(t)

        # a decreases linearly from 2 to 0 (Eq. 3.3), then modulate.
        a = (2 - 2 * (t / T)) * a_factor

        for i in range(self.population_size):
            dim = self.population[i].dimension

            # Encircling alpha (Eqs. 3.5-3.6)
            r1 = self.rng.random(dim)
            r2 = self.rng.random(dim)
            A1 = 2 * a * r1 - a
            C1 = 2 * r2
            D_alpha = np.abs(C1 * self.alpha.position - self.population[i].position)
            X1 = self.alpha.position - A1 * D_alpha

            # Encircling beta
            r1 = self.rng.random(dim)
            r2 = self.rng.random(dim)
            A2 = 2 * a * r1 - a
            C2 = 2 * r2
            D_beta = np.abs(C2 * self.beta.position - self.population[i].position)
            X2 = self.beta.position - A2 * D_beta

            # Encircling delta
            r1 = self.rng.random(dim)
            r2 = self.rng.random(dim)
            A3 = 2 * a * r1 - a
            C3 = 2 * r2
            D_delta = np.abs(C3 * self.delta.position - self.population[i].position)
            X3 = self.delta.position - A3 * D_delta

            # New position: average of the three guides (Eq. 3.7)
            new_position = (X1 + X2 + X3) / 3.0

            # Clip to bounds
            self.population[i].position = np.clip(
                new_position,
                self.population[i].lower_bounds,
                self.population[i].upper_bounds,
            )
            self.population[i]._fitness = None

        self._update_hierarchy()
        self.convergence_curve.append(self._alpha_score)
