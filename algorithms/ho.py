"""
Hippopotamus Optimization Algorithm (HO)

Faithful implementation of the algorithm proposed by Amiri et al. (2024).
All three phases are applied SEQUENTIALLY to ALL individuals in EACH iteration.
The algorithm is essentially parameter-free (no tunable hyperparameters).

Supports optional Imitation Learning (IL) for adaptive parameter control:
when use_il=True, a trained model predicts dynamic parameters (alpha, beta, gamma)
at each iteration based on the current optimization state, enabling adaptive
exploration-exploitation balance.

Reference:
    Mohammad Hussein Amiri, Nastaran Mehrabi Hashjin, Mohsen Montazeri,
    Seyedali Mirjalili & Nima Khodadadi.
    "Hippopotamus optimization algorithm: a novel nature-inspired
    optimization algorithm".
    Scientific Reports 14, Article number: 5032 (2024).
    https://doi.org/10.1038/s41598-024-54909-3

Phases:
1. Position phase (exploration): Male hippo (Eq. 6) + Female/immature (Eqs. 9-10)
2. Defense phase: Random predator + spiral movement + Levy flight (Eq. 15)
3. Evasion phase (exploitation): Shrinking local bounds (Eqs. 19-20)
"""

import numpy as np
import math
from typing import List, Optional
from algorithms.base import Individual, MetaheuristicAlgorithm
from utils.math_functions import levy_flight


class Hippopotamus(Individual):
    """Individual in the Hippopotamus Optimization Algorithm."""

    def __init__(self, problem, rng=None):
        """Initialize a hippopotamus with random position in [0,1].

        Args:
            problem: Problem instance to solve
            rng: NumPy random generator instance
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.rng = rng if rng is not None else np.random.default_rng()
        self.position = self.rng.uniform(0, 1, self.dimension)
        self._fitness = None

    def fitness(self) -> float:
        """Return cached fitness, computing if needed."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self) -> bool:
        """Check if solution is feasible."""
        return True

    def copy(self, other: "Hippopotamus") -> None:
        """Copy values from another hippopotamus."""
        self.position = other.position.copy()
        self._fitness = other._fitness

    def move(self, population: list, iteration: int, max_iterations: int) -> None:
        """Movement logic is handled in HO.update_population()."""
        pass


class HO(MetaheuristicAlgorithm):
    """Hippopotamus Optimization Algorithm (Amiri et al., 2024).

    The algorithm is parameter-free by default. It applies three phases
    sequentially to all individuals every iteration, with greedy selection
    after each phase.

    When use_il=True, an Imitation Learning model predicts adaptive parameters
    (alpha, beta, gamma) at each iteration to control exploration-exploitation.
    """

    def __init__(
        self,
        problem,
        population_size: int = 30,
        max_iterations: int = 100,
        seed: int = None,
        use_il: bool = False,
        il_model_path: str = None,
    ):
        """
        Initialize HO algorithm.

        Args:
            problem: Problem instance to solve
            population_size: Population size
            max_iterations: Maximum iterations
            seed: Random seed for reproducibility
            use_il: Enable Imitation Learning for adaptive parameters
            il_model_path: Path to trained IL model (.pkl)
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.dominant = None  # D_hippo: best solution found
        self.use_il = use_il
        self.il_model = None
        self._il_params_history = []  # Track predicted params for analysis
        self._il_fallback_count = 0  # Count fallbacks to detect silent failures

        if self.use_il and il_model_path:
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
        """Initialize population of hippopotami."""
        self.population = []
        for _ in range(self.population_size):
            hippo = Hippopotamus(self.problem, rng=self.rng)
            self.population.append(hippo)

        # Find dominant hippo (best fitness)
        self.dominant = self._copy_hippo(
            min(self.population, key=lambda h: h.fitness())
        )
        self.best_solution = self.dominant
        self.convergence_curve = [self.dominant.fitness()]

    def _copy_hippo(self, source):
        """Create an independent copy of a hippopotamus."""
        h = object.__new__(Hippopotamus)
        h.problem = self.problem
        h.dimension = source.dimension
        h.rng = self.rng
        h.position = source.position.copy()
        h._fitness = source._fitness
        return h

    def _get_il_params(self, iteration: int) -> tuple:
        """Predict IL parameters or return defaults.

        Returns:
            Tuple (alpha, beta, gamma) where:
            - alpha in [0.1, 0.9]: scales attraction to dominant in Phase 1
            - beta in [0.2, 0.8]: scales female/immature adaptation in Phase 1
            - gamma in [0.3, 1.0]: scales perturbation amplitude in Phases 2-3
        """
        if not self.use_il or self.il_model is None:
            return 1.0, 1.0, 1.0  # Neutral: no modification to original HO

        try:
            from utils.imitation_learning import create_state_from_problem
            state = create_state_from_problem(
                self.problem, self, iteration, self.max_iterations
            )
            # Validate feature alignment on first call
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
                'alpha': float(alpha),
                'beta': float(beta),
                'gamma': float(gamma),
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
        """Apply all three phases sequentially to all individuals.

        Per Amiri et al. (2024): phases are NOT mutually exclusive.
        Each individual goes through all three phases every iteration,
        with greedy selection after each sub-phase.

        When IL is active, alpha/beta/gamma modulate the phase behaviors:
        - alpha: exploration intensity in male update (Phase 1)
        - beta: female adaptation strength (Phase 1)
        - gamma: perturbation amplitude in defense/evasion (Phases 2-3)
        """
        iteration = len(self.convergence_curve)  # 1-based after init
        lb = np.zeros(self.population[0].dimension)
        ub = np.ones(self.population[0].dimension)

        # Temperature factor (Eq. 8)
        T = math.exp(-iteration / self.max_iterations)

        # IL adaptive parameters (neutral 1.0 if IL disabled)
        alpha, beta, gamma = self._get_il_params(iteration)

        for i in range(self.population_size):
            dim = self.population[i].dimension
            x_i = self.population[i].position
            f_i = self.population[i].fitness()

            # ============================================
            # PHASE 1: Position in river/pond (Exploration)
            # ============================================

            # --- Eq. 6: Male hippo update ---
            # alpha modulates exploration intensity toward dominant
            y1 = self.rng.random(dim) * alpha
            I1 = self.rng.integers(1, 3, size=dim)  # {1, 2}
            x_male = x_i + y1 * (self.dominant.position - I1 * x_i)
            x_male = np.clip(x_male, lb, ub)

            # Greedy selection for male update (Eq. 11)
            f_male = self.problem.evaluate(x_male)
            if f_male < f_i:
                x_i = x_male
                f_i = f_male

            # --- Eqs. 9-10: Female/immature hippo update ---
            # Compute MG_i: mean of a random group
            group_size = max(2, self.rng.integers(2, max(3, self.population_size // 3)))
            group_indices = self.rng.choice(
                self.population_size, size=min(group_size, self.population_size), replace=False
            )
            MG_i = np.mean([self.population[g].position for g in group_indices], axis=0)

            # Compute h vectors (Eq. 7 simplified)
            I2 = self.rng.integers(1, 3, size=dim)
            r1 = self.rng.random(dim)
            r2 = self.rng.random(dim)
            r3 = self.rng.random(dim) + 1e-10  # avoid division by zero
            r4 = self.rng.random(dim)
            r5 = self.rng.random() + 1e-10
            rho1 = self.rng.integers(0, 2, size=dim)
            rho2 = self.rng.integers(0, 2, size=dim)

            h = (I2 * r1 + (1 - rho1) * 2 * (r2 - 1)) / r3
            h = h / ((I1 * r4 + (1 - rho2)) / r5)
            # beta modulates female/immature adaptation strength
            h = h * beta

            if T > 0.6:
                # Eq. 9: early iterations (high temperature)
                x_female = x_i + h[:dim] * (self.dominant.position - I2 * MG_i)
            else:
                # Eq. 10: later iterations
                r6 = self.rng.random()
                if r6 > 0.5:
                    x_female = x_i + h[:dim] * (MG_i - self.dominant.position)
                else:
                    r7 = self.rng.random(dim)
                    x_female = lb + r7 * (ub - lb)

            x_female = np.clip(x_female, lb, ub)

            # Greedy selection for female update (Eq. 12)
            f_female = self.problem.evaluate(x_female)
            if f_female < f_i:
                x_i = x_female
                f_i = f_female

            # ============================================
            # PHASE 2: Defense against predators
            # ============================================

            # Eq. 13: Random predator position
            r8 = self.rng.random(dim)
            predator = lb + r8 * (ub - lb)
            f_predator = self.problem.evaluate(predator)

            # Eq. 14: Distance to predator
            D_vec = np.abs(predator - x_i) + 1e-10  # avoid div by zero

            # Levy flight (Eqs. 17-18): Mantegna method with vartheta=1.5
            # gamma modulates perturbation amplitude
            RL = levy_flight(dim, beta=1.5, rng=self.rng) * 0.05 * gamma

            # Random parameters for spiral movement
            f_param = self.rng.uniform(2, 4) * gamma
            d_param = self.rng.uniform(2, 3) * gamma
            g_param = self.rng.uniform(-1, 1)

            if f_predator < f_i:
                # Eq. 15a: Predator is better, move closer (inversely proportional)
                x_defense = (
                    RL + predator
                    + (f_param - d_param) * math.cos(2 * math.pi * g_param) * (1.0 / D_vec)
                )
            else:
                # Eq. 15b: Predator is worse, move away (proportional)
                r9 = self.rng.random(dim)
                x_defense = (
                    RL + predator
                    + (f_param - d_param) * math.cos(2 * math.pi * g_param) * 12 * D_vec
                    + r9
                )

            x_defense = np.clip(x_defense, lb, ub)

            # Greedy selection for defense (Eq. 16)
            f_defense = self.problem.evaluate(x_defense)
            if f_defense < f_i:
                x_i = x_defense
                f_i = f_defense

            # ============================================
            # PHASE 3: Evasion/Escape (Exploitation)
            # ============================================

            # Eqs. 19-20: Local bounds shrink with iteration
            # gamma modulates bounds: high gamma → smaller t_safe → wider local
            # bounds → more exploration. Consistent with Phase 2 where high gamma
            # also increases perturbation amplitude.
            t_safe = max(1, iteration) * (1.0 / gamma)
            lb_local = lb / t_safe
            ub_local = ub / t_safe

            # Eq. 21: Choose perturbation scenario randomly
            r_scenario = self.rng.random()
            if r_scenario < 0.33:
                s = 2 * self.rng.random(dim) - 1  # Uniform [-1, 1]
            elif r_scenario < 0.66:
                s = self.rng.standard_normal(dim)  # N(0, 1)
            else:
                s = self.rng.random(dim)  # Uniform [0, 1]

            # Eq. 19: Evasion position
            r10 = self.rng.random(dim)
            x_evasion = x_i + r10 * (lb_local + s * (ub_local - lb_local))
            x_evasion = np.clip(x_evasion, lb, ub)

            # Greedy selection for evasion (Eq. 22)
            f_evasion = self.problem.evaluate(x_evasion)
            if f_evasion < f_i:
                x_i = x_evasion
                f_i = f_evasion

            # ============================================
            # Apply final position
            # ============================================
            self.population[i].position = x_i
            self.population[i]._fitness = f_i

            # Update dominant if improved
            if f_i < self.dominant.fitness():
                self.dominant = self._copy_hippo(self.population[i])

        self.best_solution = self.dominant
        self.convergence_curve.append(self.dominant.fitness())

    def get_parameters(self) -> dict:
        """Get algorithm parameters for reporting."""
        params = {
            'algorithm': 'HO+IL' if self.use_il else 'HO',
            'population_size': self.population_size,
            'max_iterations': self.max_iterations,
            'levy_beta': 1.5,
            'phases': '3 sequential (position, defense, evasion)',
            'seed': self.seed,
            'use_il': self.use_il,
        }
        if self.use_il:
            params['il_model'] = 'SimpleILModel (RandomForest)'
            params['il_params'] = 'alpha (attraction), beta (adaptation), gamma (perturbation)'
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
        """Return history of IL-predicted parameters for analysis."""
        return self._il_params_history
