"""
Adapter exposing the C++ ``minionpy`` optimizers (CEC competition winners and
top performers) through this framework's algorithm interface.

Why minionpy
------------
The actual IEEE CEC winners/top-ranked real-parameter optimizers (jSO,
NL-SHADE-RSP, L-SRTDE, j2020, ARRDE, AGSK, IMODE, LSHADE-cnEpSin, CMA-ES...)
are published in MATLAB/C++ and are absent from pure-Python libraries.
``minionpy`` (PyPI, C++ core with a Python binding) ships faithful, peer-used
implementations of exactly these. This lets the benchmark include genuine
state-of-the-art competitors -- satisfying Rodrigo's protocol Section 3
("include recent CEC competition winners ... avoid selecting only weak
competitors") -- without re-implementing MATLAB (the HO fidelity lesson).

FES accounting
--------------
``minionpy.Minimizer`` takes ``maxevals`` (exact FES budget) and ``relTol``;
with ``relTol=0`` it runs to the budget. The objective is called in BATCH
(a (pop, dim) matrix -> list of fitness), which minionpy counts natively, so
``nfev`` lands at the budget. When the harness passes an ``FESLimitProblem``
wrapper, the adapter reads ``max_fes`` from it and evaluates on the inner raw
problem (minionpy does its own counting; no double charge).

Author-recommended parameters: minionpy uses each algorithm's author defaults
(no ``options`` override), consistent with protocol Section 4.
"""

import warnings
from typing import Any, Optional

import numpy as np

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import minionpy as mp


class _BestWrapper:
    """Minimal best-solution object exposing ``fitness()`` and ``position``."""

    def __init__(self, position, fitness_value: float):
        self.position = np.asarray(position, dtype=float)
        self._fitness = float(fitness_value)

    def fitness(self) -> float:
        return self._fitness


class MinionAlgorithm:
    """Wrap a minionpy optimizer (by name) behind this framework's interface."""

    MINION_ALGO: str = "ARRDE"   # minionpy algo string (set by factory)
    NAME: str = "minion"

    def __init__(self, problem: Any, population_size: int = 100,
                 max_iterations: int = 100, seed: Optional[int] = None,
                 **kwargs):
        self.problem = problem
        self.population_size = int(population_size)
        self.max_iterations = int(max_iterations)
        self.seed = seed
        kwargs.pop("use_il", None)
        kwargs.pop("il_model", None)
        self.best_solution = None
        self.convergence_curve = []
        self._result = None

    def _resolve_problem_and_budget(self):
        prob = self.problem
        if hasattr(prob, "inner") and hasattr(prob, "max_fes"):
            return prob.inner, int(prob.max_fes)
        return prob, int(self.population_size * self.max_iterations)

    def execute(self):
        raw, max_fes = self._resolve_problem_and_budget()
        lb = np.asarray(raw.get_lower_bounds(), dtype=float)
        ub = np.asarray(raw.get_upper_bounds(), dtype=float)
        bounds = list(zip(lb.tolist(), ub.tolist()))

        def f(X, data=None):
            X = np.asarray(X, dtype=float)
            if X.ndim == 1:
                return float(raw.evaluate(X))
            return [float(raw.evaluate(row)) for row in X]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = mp.Minimizer(
                func=f, bounds=bounds, x0=None, algo=self.MINION_ALGO,
                relTol=0.0, maxevals=int(max_fes), seed=self.seed,
            )
            res = m.optimize()
        self._result = res
        self.best_solution = _BestWrapper(res.x, res.fun)
        self.convergence_curve = [self.best_solution.fitness()]
        return self.best_solution

    def get_best_solution(self):
        return self.best_solution

    def get_parameters(self) -> dict:
        return {
            "algorithm": self.NAME,
            "backend": "minionpy",
            "minion_algo": self.MINION_ALGO,
            "author_params": "minionpy defaults (author-recommended)",
            "seed": self.seed,
        }


def _make(name, minion_algo):
    return type(f"Minion_{minion_algo}", (MinionAlgorithm,), {
        "MINION_ALGO": minion_algo, "NAME": name,
    })


# CEC winners / top performers (faithful C++ implementations).
JSO = _make("jSO", "jSO")                       # top CEC2017
NLSHADE_RSP = _make("NL-SHADE-RSP", "NLSHADE_RSP")  # winner CEC2021
LSRTDE = _make("L-SRTDE", "LSRTDE")             # winner CEC2024
J2020 = _make("j2020", "j2020")                 # CEC2020
ARRDE = _make("ARRDE", "ARRDE")                 # minion default, strong
AGSK = _make("AGSK", "AGSK")                    # CEC2020 top
IMODE = _make("IMODE", "IMODE")                 # winner CEC2020
LSHADE_cnEpSin = _make("LSHADE-cnEpSin", "LSHADE_cnEpSin")  # top CEC2017
LSHADE_M = _make("L-SHADE", "LSHADE")           # faithful C++ L-SHADE
JADE_M = _make("JADE", "JADE")                  # faithful C++ JADE
CMAES = _make("CMA-ES", "CMAES")                # the ES baseline
BIPOP_CMAES = _make("BIPOP-aCMAES", "BIPOP_aCMAES")

MINION_ROSTER = {
    "jSO": JSO, "NL-SHADE-RSP": NLSHADE_RSP, "L-SRTDE": LSRTDE, "j2020": J2020,
    "ARRDE": ARRDE, "AGSK": AGSK, "IMODE": IMODE,
    "LSHADE-cnEpSin": LSHADE_cnEpSin, "L-SHADE": LSHADE_M, "JADE": JADE_M,
    "CMA-ES": CMAES, "BIPOP-aCMAES": BIPOP_CMAES,
}
