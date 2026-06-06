"""
Adapter exposing validated ``mealpy`` optimizers through this framework's
algorithm interface, so modern state-of-the-art metaheuristics (L-SHADE, SHADE,
JADE, SADE, GSKA) can be benchmarked side-by-side with the in-repo algorithms
on the CEC harness.

Why an adapter (not a re-implementation)
----------------------------------------
Re-implementing competition winners is error-prone (cf. the HO fidelity audit).
``mealpy`` ships peer-used implementations with author-recommended defaults, in
line with Rodrigo's protocol (Section 4: "parameters with the values
recommended by their original authors, without re-tuning").

FES accounting
--------------
``mealpy`` controls its own evaluation loop, so instead of the per-iteration
``BudgetExhausted`` guard used for the in-repo algorithms, this adapter uses
mealpy's NATIVE ``termination={"max_fe": MaxFES}``, which stops at EXACTLY
MaxFES objective evaluations. When the harness passes an ``FESLimitProblem``
wrapper, the adapter reads ``max_fes`` from it and runs mealpy on the inner raw
problem (no double counting).

Interface contract honored
--------------------------
``__init__(problem, population_size, max_iterations, seed, **kwargs)``,
``execute()``, ``best_solution.fitness()`` / ``.position``, ``get_parameters()``
-- matching what ``run_with_fes`` / ``run_cell`` expect.
"""

import warnings
from typing import Any, Optional

import numpy as np

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from mealpy import FloatVar
    from mealpy.evolutionary_based.DE import JADE, SADE
    from mealpy.evolutionary_based.SHADE import L_SHADE, OriginalSHADE
    from mealpy.human_based.GSKA import OriginalGSKA


class _BestWrapper:
    """Minimal best-solution object exposing ``fitness()`` and ``position``."""

    def __init__(self, position, fitness_value: float):
        self.position = np.asarray(position, dtype=float)
        self._fitness = float(fitness_value)

    def fitness(self) -> float:
        return self._fitness


class MealpyAlgorithm:
    """Wrap a mealpy optimizer class behind this framework's interface."""

    #: mealpy optimizer class (set by subclasses / factory).
    MEALPY_CLASS: Any = None
    #: human-readable algorithm name.
    NAME: str = "mealpy"
    #: author-recommended extra params (besides epoch/pop_size).
    MEALPY_PARAMS: dict = {}

    def __init__(self, problem: Any, population_size: int = 30,
                 max_iterations: int = 100, seed: Optional[int] = None,
                 **kwargs):
        self.problem = problem
        self.population_size = int(population_size)
        self.max_iterations = int(max_iterations)
        self.seed = seed
        # Ignore IL hooks: these are reference competitors, not IL targets.
        kwargs.pop("use_il", None)
        kwargs.pop("il_model", None)
        self.extra = {**self.MEALPY_PARAMS, **kwargs}

        self.best_solution = None
        self.convergence_curve = []
        self._model = None

    def _resolve_problem_and_budget(self):
        """Return (raw_problem, max_fes), unwrapping FESLimitProblem if present."""
        prob = self.problem
        if hasattr(prob, "inner") and hasattr(prob, "max_fes"):
            return prob.inner, int(prob.max_fes)
        # No FES wrapper: derive a budget from pop x iterations.
        return prob, int(self.population_size * self.max_iterations)

    def execute(self):
        raw, max_fes = self._resolve_problem_and_budget()
        lb = np.asarray(raw.get_lower_bounds(), dtype=float).tolist()
        ub = np.asarray(raw.get_upper_bounds(), dtype=float).tolist()

        def obj(x):
            return float(raw.evaluate(x))

        problem_dict = {
            "obj_func": obj,
            "bounds": FloatVar(lb=lb, ub=ub),
            "minmax": "min",
            "log_to": None,
        }
        # mealpy caps epoch at 100000 and stops at whichever binds first
        # (epoch OR max_fe). Size epoch so max_fe is the binding stop for the
        # given pop; the FES termination remains the exact cut.
        import math
        epoch = max(1, min(100000,
                           math.ceil(max_fes / max(1, self.population_size)) + 1))
        model = self.MEALPY_CLASS(
            epoch=epoch, pop_size=self.population_size, **self.extra
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model.solve(problem_dict, termination={"max_fe": max_fes},
                        seed=self.seed)
        self._model = model
        self.best_solution = _BestWrapper(
            model.g_best.solution, model.g_best.target.fitness
        )
        # mealpy's global-best history (per epoch) as a convergence proxy.
        try:
            self.convergence_curve = [
                float(a.target.fitness) for a in model.history.list_global_best
            ]
        except Exception:
            self.convergence_curve = [self.best_solution.fitness()]
        return self.best_solution

    def get_best_solution(self):
        return self.best_solution

    def get_parameters(self) -> dict:
        return {
            "algorithm": self.NAME,
            "population_size": self.population_size,
            "backend": "mealpy",
            "mealpy_class": getattr(self.MEALPY_CLASS, "__name__", None),
            "author_params": self.extra,
            "seed": self.seed,
        }


def _make(name, mealpy_cls, **default_params):
    """Build a concrete MealpyAlgorithm subclass for one optimizer."""
    return type(name, (MealpyAlgorithm,), {
        "MEALPY_CLASS": mealpy_cls,
        "NAME": name,
        "MEALPY_PARAMS": dict(default_params),
    })


# Concrete modern-roster adapters (author-recommended defaults from mealpy).
LSHADE = _make("L-SHADE", L_SHADE)
SHADE = _make("SHADE", OriginalSHADE)
JADEAlgo = _make("JADE", JADE)
SADEAlgo = _make("SADE", SADE)
GSKA = _make("GSKA", OriginalGSKA)

MEALPY_ROSTER = {
    "L-SHADE": LSHADE,
    "SHADE": SHADE,
    "JADE": JADEAlgo,
    "SADE": SADEAlgo,
    "GSKA": GSKA,
}
