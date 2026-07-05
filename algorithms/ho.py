"""
Hippopotamus Optimization Algorithm (HO)

Faithful re-implementation aligned to the AUTHORS' official MATLAB code
(Khodadadi et al., github.com/inimakhan/HO) and Amiri et al. (2024),
Scientific Reports 14:5032. https://doi.org/10.1038/s41598-024-54909-3

Structure (per the official HO.m):
- The population is split. For i = 1..N/2 (first half) the river/pond phase is
  applied: a dominant-attraction update (X_P1) AND a mean-group update (X_P2),
  each with greedy selection. For i = N/2+1..N (second half) the predator-defense
  phase is applied (X_P3). Finally ALL individuals undergo the escape phase (X_P4).
- The dominant (Xbest) used during an iteration is the global best from the
  PREVIOUS iteration (fixed across the phases), as in HO.m.
- HO is parameter-free: with use_il=False (alpha=beta=gamma=1) this reduces
  EXACTLY to the official HO.

Optional Imitation Learning (multiplicative, neutral at 1.0):
- alpha scales the dominant-attraction step in X_P1 (river phase).
- beta  scales the A/B mean-group factors in X_P2 (river phase).
- gamma scales the perturbation amplitude in defense (X_P3) and the local-bound
  width in escape (X_P4).
With alpha=beta=gamma=1 the equations are identical to the official HO.
"""

import math
import numpy as np
from algorithms.base import Individual, MetaheuristicAlgorithm
from utils.math_functions import levy_flight


class Hippopotamus(Individual):
    """Individual in the Hippopotamus Optimization Algorithm."""

    def __init__(self, problem, rng=None):
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

    def fitness(self) -> float:
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self) -> bool:
        return True

    def copy(self, other: "Hippopotamus") -> None:
        self.position = other.position.copy()
        self._fitness = other._fitness

    def move(self, population: list, iteration: int, max_iterations: int) -> None:
        """Movement logic is handled in HO.update_population()."""
        pass


class HO(MetaheuristicAlgorithm):
    """Hippopotamus Optimization Algorithm (Amiri et al., 2024).

    Parameter-free by default; faithful to the official MATLAB implementation.
    When use_il=True, an Imitation Learning model predicts adaptive multiplicative
    factors (alpha, beta, gamma) each iteration (neutral 1.0 == unmodified HO).
    """

    def __init__(
        self,
        problem,
        population_size: int = 30,
        max_iterations: int = 100,
        seed: int = None,
        use_il: bool = False,
        il_model_path: str = None,
        il_model=None,
    ):
        super().__init__(problem, population_size, max_iterations, seed)
        self.dominant = None  # D_hippo / Xbest: global best so far
        self.use_il = use_il
        # A pre-loaded model object (e.g. utils/bc_policy.BCPolicy) takes
        # precedence over il_model_path (legacy SimpleILModel loading).
        self.il_model = il_model
        self._il_params_history = []
        self._il_fallback_count = 0

        if self.use_il and self.il_model is None and il_model_path:
            try:
                from utils.train_il_simple import SimpleILModel
                self.il_model = SimpleILModel()
                self.il_model.load(il_model_path)
                if not self.il_model.is_trained:
                    raise ValueError("Model loaded but not trained")
            except Exception as e:
                import warnings
                warnings.warn(f"Could not load IL model: {e}. Running without IL.")
                self.use_il = False

    def initialize_population(self) -> None:
        self.population = []
        for _ in range(self.population_size):
            self.population.append(Hippopotamus(self.problem, rng=self.rng))
        self.dominant = self._copy_hippo(
            min(self.population, key=lambda h: h.fitness())
        )
        self.best_solution = self.dominant
        self.convergence_curve = [self.dominant.fitness()]

    def _copy_hippo(self, source):
        h = object.__new__(Hippopotamus)
        h.problem = self.problem
        h.dimension = source.dimension
        h.rng = self.rng
        h.position = source.position.copy()
        h._fitness = source._fitness
        return h

    def _get_il_params(self, iteration: int) -> tuple:
        """Predict IL parameters (alpha, beta, gamma) or return neutral (1,1,1)."""
        if not self.use_il or self.il_model is None:
            return 1.0, 1.0, 1.0

        # New-style policy (utils/bc_policy.BCPolicy): predict(algo, iteration)
        # -> factor tuple. Detected by its n_outputs attribute.
        if hasattr(self.il_model, "n_outputs"):
            try:
                alpha, beta, gamma = self.il_model.predict(self, iteration)
                self._il_params_history.append({
                    'iteration': iteration,
                    'alpha': float(alpha), 'beta': float(beta), 'gamma': float(gamma),
                })
                return float(alpha), float(beta), float(gamma)
            except Exception:
                self._il_fallback_count += 1
                return 1.0, 1.0, 1.0

        try:
            from utils.imitation_learning import create_state_from_problem
            state = create_state_from_problem(
                self.problem, self, iteration, self.max_iterations
            )
            if iteration <= 1 and self.il_model.feature_names is not None:
                missing = set(self.il_model.feature_names) - set(state.keys())
                if missing:
                    import warnings
                    warnings.warn(
                        f"IL feature mismatch: model expects {missing} "
                        f"not in state. Using 0 for missing features."
                    )
            alpha, beta, gamma = self.il_model.predict(state)
            self._il_params_history.append({
                'iteration': iteration,
                'alpha': float(alpha), 'beta': float(beta), 'gamma': float(gamma),
            })
            return alpha, beta, gamma
        except Exception as e:
            self._il_fallback_count += 1
            if self._il_fallback_count == 1:
                import warnings
                warnings.warn(
                    f"IL prediction failed at iteration {iteration}: {e}. "
                    f"Falling back to neutral params (1.0, 1.0, 1.0)."
                )
            return 1.0, 1.0, 1.0

    def update_population(self) -> None:
        """One HO iteration, faithful to the official HO.m.

        First half: river/pond phase (X_P1 dominant attraction + X_P2 mean-group).
        Second half: defense against predators (X_P3).
        All: escape/exploitation (X_P4). Greedy selection after each sub-update.
        """
        iteration = len(self.convergence_curve)  # 1-based after init
        N = self.population_size
        dim = self.population[0].dimension
        # Use the problem's bounds (default [0, 1] for random-key VRP),
        # taken from any individual (all share the same bounds).
        lb = getattr(self.population[0], "lower_bounds", np.zeros(dim))
        ub = getattr(self.population[0], "upper_bounds", np.ones(dim))

        # Dominant = global best from previous iteration (fixed across phases).
        D = self.dominant.position
        T = math.exp(-iteration / self.max_iterations)  # Eq. 5
        alpha, beta, gamma = self._get_il_params(iteration)

        half = N // 2

        # ============================================================
        # PHASE 1 (first half): position in river/pond (Exploration)
        # ============================================================
        for i in range(half):
            x_i = self.population[i].position
            f_i = self.population[i].fitness()

            I1 = self.rng.integers(1, 3)  # scalar in {1,2}
            I2 = self.rng.integers(1, 3)
            Ip1 = self.rng.integers(0, 2, size=2)

            # Mean of a random group (random size)
            rgn = int(self.rng.integers(1, N + 1))
            rg = self.rng.choice(N, size=rgn, replace=False)
            MG = np.mean([self.population[g].position for g in rg], axis=0)

            # Alfa set (official HO.m): A and B each chosen at random from it
            alfa = [
                I2 * self.rng.random(dim) + (1 - Ip1[0]),
                2 * self.rng.random(dim) - 1,
                self.rng.random(dim),
                I1 * self.rng.random(dim) + (1 - Ip1[1]),
                self.rng.random(),
            ]
            A = alfa[int(self.rng.integers(0, 5))]
            B = alfa[int(self.rng.integers(0, 5))]

            # X_P1 (Eq. 3): dominant attraction; alpha scales the step
            y1 = self.rng.random()  # scalar, per HO.m
            x_p1 = x_i + (alpha * y1) * (D - I1 * x_i)
            x_p1 = np.clip(x_p1, lb, ub)

            # X_P2 (Eqs. 6-7): mean-group update; beta scales A/B
            if T > 0.6:
                x_p2 = x_i + (beta * A) * (D - I2 * MG)
            else:
                if self.rng.random() > 0.5:
                    x_p2 = x_i + (beta * B) * (MG - D)
                else:
                    x_p2 = lb + self.rng.random(dim) * (ub - lb)
            x_p2 = np.clip(x_p2, lb, ub)

            # Greedy selection after each sub-update
            f_p1 = self.problem.evaluate(x_p1)
            if f_p1 < f_i:
                x_i, f_i = x_p1, f_p1
            f_p2 = self.problem.evaluate(x_p2)
            if f_p2 < f_i:
                x_i, f_i = x_p2, f_p2

            self.population[i].position = x_i
            self.population[i]._fitness = f_i

        # ============================================================
        # PHASE 2 (second half): defense against predators (Exploration)
        # ============================================================
        for i in range(half, N):
            x_i = self.population[i].position
            f_i = self.population[i].fitness()

            predator = lb + self.rng.random(dim) * (ub - lb)  # Eq. 10
            f_pred = self.problem.evaluate(predator)
            dist = np.abs(predator - x_i) + 1e-12  # Eq. 11

            b = self.rng.uniform(2, 4)
            c = self.rng.uniform(1, 1.5)
            d = self.rng.uniform(2, 3)
            l = self.rng.uniform(-2 * math.pi, 2 * math.pi)
            RL = 0.05 * levy_flight(dim, beta=1.5, rng=self.rng) * gamma  # Eqs. 13-14

            factor = (b / (c - d * math.cos(l))) * gamma  # gamma scales displacement
            if f_i > f_pred:  # current worse than predator -> Eq. 12 case 1
                x_def = RL * predator + factor * (1.0 / dist)
            else:             # Eq. 12 case 2
                x_def = RL * predator + factor * (1.0 / (2.0 * dist + self.rng.random(dim)))
            x_def = np.clip(x_def, lb, ub)

            f_def = self.problem.evaluate(x_def)
            if f_def < f_i:
                x_i, f_i = x_def, f_def

            self.population[i].position = x_i
            self.population[i]._fitness = f_i

        # ============================================================
        # PHASE 3 (all): escaping from the predator (Exploitation)
        # ============================================================
        # gamma scales the local-bound width (gamma=1 -> bounds = lb/t, ub/t).
        t_local = max(1, iteration) / gamma
        lo_local = lb / t_local
        hi_local = ub / t_local
        for i in range(N):
            x_i = self.population[i].position
            f_i = self.population[i].fitness()

            sc = int(self.rng.integers(0, 3))  # Eq. 18: random scenario for s
            if sc == 0:
                s = 2 * self.rng.random(dim) - 1
            elif sc == 1:
                s = self.rng.random()
            else:
                s = self.rng.standard_normal(dim)

            x_esc = x_i + self.rng.random() * (lo_local + s * (hi_local - lo_local))
            x_esc = np.clip(x_esc, lb, ub)

            f_esc = self.problem.evaluate(x_esc)
            if f_esc < f_i:
                x_i, f_i = x_esc, f_esc

            self.population[i].position = x_i
            self.population[i]._fitness = f_i

            if f_i < self.dominant.fitness():
                self.dominant = self._copy_hippo(self.population[i])

        self.best_solution = self.dominant
        self.convergence_curve.append(self.dominant.fitness())

    @property
    def evals_per_iteration(self) -> int:
        """Function evaluations charged per update_population() call (~3*N):
        first half ~2 (X_P1+X_P2), second half ~2 (predator+defense), all 1
        (escape)."""
        return 3 * self.population_size

    def get_parameters(self) -> dict:
        params = {
            'algorithm': 'HO+IL' if self.use_il else 'HO',
            'population_size': self.population_size,
            'max_iterations': self.max_iterations,
            'levy_beta': 1.5,
            'phases': '3 (river [first half], defense [second half], escape [all])',
            'seed': self.seed,
            'use_il': self.use_il,
        }
        if self.use_il:
            params['il_model'] = 'SimpleILModel (RandomForest)'
            params['il_params'] = 'alpha (attraction), beta (mean-group), gamma (perturbation)'
            params['il_fallback_count'] = self._il_fallback_count
            if self._il_fallback_count > 0:
                fallback_pct = (self._il_fallback_count / max(1, self.max_iterations)) * 100
                params['il_fallback_pct'] = f"{fallback_pct:.1f}%"
                if fallback_pct > 10:
                    import warnings
                    warnings.warn(
                        f"IL fallback rate {fallback_pct:.1f}% exceeds 10%. "
                        f"Results may not reflect IL behavior."
                    )
        return params

    def get_il_params_history(self) -> list:
        return self._il_params_history
