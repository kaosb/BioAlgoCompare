"""CEC continuous benchmark problems (CEC2014 / CEC2017 / CEC2022).

Backend (revisión interna del 23-Sep-2026): the functions come from
``minionpy`` (``CEC2014Functions`` / ``CEC2017Functions`` /
``CEC2022Functions``), a C++ port of the OFFICIAL Suganthan C code with the
official data files. It matches the compiled official C code in 142/142
(function x dimension) cases (max relative error <= 3.7e-10), verified by
``tests/test_cec_official.py`` against stored reference values.

The previous backend, ``opfunu`` 1.0.1, matched the official definitions in
only 32/142 cases (inverted Schwefel sign, NaN in CEC2017 F17/F29 at 10D,
CEC2017 data shifted by one index, wrong range scalings, hybrid functions
permuting before rotating). It is kept ONLY as ``backend="opfunu_legacy"`` to
reproduce historical results bit for bit; never use it for new experiments.

Design notes
------------
* Numbering is OFFICIAL for every suite (CEC2017: 1..30; F2 is the function
  retired by the organisers and is rejected unless ``allow_retired=True``).
* ``evaluate`` returns the **error to the optimum**, ``f(x) - bias``. A value
  below ``-ERROR_TOL`` or non-finite is IMPOSSIBLE for a correct CEC function
  and raises :class:`InvalidEvaluation` instead of being silently clipped
  (the legacy wrapper clipped negatives to 0 and turned NaN into 0, which
  hid the opfunu defects). Errors in ``[-ERROR_TOL, 0)`` are floating-point
  noise and are reported as 0.
* ``FESLimitProblem`` enforces a hard MaxFES budget; ``run_with_fes`` runs an
  algorithm under an exact budget.

References
----------
* Liang, Qu & Suganthan (2013). CEC 2014 technical report.
* Awad, Ali, Liang, Qu & Suganthan (2016). CEC 2017 technical report.
* Kumar, Price, Mohamed, Hadi & Suganthan (2021). CEC 2022 technical report.
"""

import math
import warnings
from typing import Optional

import numpy as np

ERROR_TOL = 1e-8

# Official biases (f* at the optimum).
_CEC2022_BIAS = [300, 400, 600, 800, 900, 1800, 2000, 2200, 2300, 2400, 2600, 2700]
_N_FUNCS = {"CEC2014": 30, "CEC2017": 30, "CEC2022": 12}
_DIMS = {"CEC2014": (10, 20, 30, 50, 100), "CEC2017": (10, 20, 30, 50, 100),
         "CEC2022": (10, 20)}


class InvalidEvaluation(RuntimeError):
    """A benchmark returned a value impossible for its definition."""


def _official_bias(suite: str, fnum: int) -> float:
    if suite == "CEC2022":
        return float(_CEC2022_BIAS[fnum - 1])
    return 100.0 * fnum


class CECProblem:
    """One CEC benchmark function, objective = error to the optimum (>= 0).

    Args:
        suite: ``'CEC2014'``, ``'CEC2017'`` or ``'CEC2022'``.
        fnum: OFFICIAL function number (CEC2017: 1..30, F2 retired).
        ndim: dimensionality (CEC2022 supports only 10 and 20).
        backend: ``'official'`` (minionpy, default) or ``'opfunu_legacy'``.
        allow_retired: accept CEC2017 F2 (numerically unstable, retired).
    """

    def __init__(self, suite: str, fnum: int, ndim: int, backend: str = "official",
                 allow_retired: bool = False):
        if suite not in _N_FUNCS:
            raise ValueError(f"Unknown suite '{suite}'. Valid: {sorted(_N_FUNCS)}")
        if ndim < 1:
            raise ValueError(f"ndim must be >= 1, got {ndim}")
        self.suite, self.fnum, self.ndim, self.backend = suite, int(fnum), int(ndim), backend
        if backend == "opfunu_legacy":
            self._init_opfunu()
            return
        if backend != "official":
            raise ValueError(f"Unknown backend '{backend}'")
        if not 1 <= self.fnum <= _N_FUNCS[suite]:
            raise ValueError(f"{suite} has functions 1..{_N_FUNCS[suite]}, got {fnum}")
        if suite == "CEC2017" and self.fnum == 2 and not allow_retired:
            raise ValueError("CEC2017 F2 was retired by the organisers; pass allow_retired=True")
        if self.ndim not in _DIMS[suite]:
            raise ValueError(f"{suite} is defined for D in {_DIMS[suite]}, got {ndim}")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import minionpy as mp
        cls = {"CEC2014": mp.CEC2014Functions, "CEC2017": mp.CEC2017Functions,
               "CEC2022": mp.CEC2022Functions}[suite]
        self._func = cls(self.fnum, self.ndim)
        self.f_global = _official_bias(suite, self.fnum)
        self._lb = np.full(self.ndim, -100.0)
        self._ub = np.full(self.ndim, 100.0)

    def _init_opfunu(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import opfunu
        year = self.suite[3:]
        cands = [c for c in opfunu.get_functions_based_classname(year)
                 if c.__name__ == f"F{self.fnum}{year}"]
        if not cands:
            raise ValueError(f"opfunu has no F{self.fnum}{year}")
        self._func = cands[0](ndim=self.ndim)
        self.f_global = float(self._func.f_global)
        self._lb = np.asarray(self._func.lb, dtype=float).copy()
        self._ub = np.asarray(self._func.ub, dtype=float).copy()

    def raw(self, x) -> float:
        """Raw objective value f(x) (no bias subtraction)."""
        x = np.asarray(x, dtype=float)
        if self.backend == "opfunu_legacy":
            return float(self._func.evaluate(x))
        return float(self._func([x.tolist()])[0])

    def evaluate(self, x) -> float:
        """Error to the optimum. Raises InvalidEvaluation on impossible values."""
        value = self.raw(x)
        error = value - self.f_global
        if self.backend == "opfunu_legacy":
            # historical behaviour, kept only for bit-exact reproduction
            return error if error > 0.0 else 0.0
        if not math.isfinite(error) or error < -ERROR_TOL:
            raise InvalidEvaluation(
                f"{self.suite} F{self.fnum} D={self.ndim}: error={error!r} at x={np.asarray(x).tolist()}")
        return error if error > 0.0 else 0.0

    def get_dimension(self) -> int:
        return self.ndim

    def get_lower_bounds(self) -> np.ndarray:
        return self._lb.copy()

    def get_upper_bounds(self) -> np.ndarray:
        return self._ub.copy()

    def is_valid(self, x) -> bool:
        """Continuous box-constrained problems treat any point as valid."""
        return True


class _FESBudgetExhausted(Exception):
    """Internal signal raised when the MaxFES budget is exceeded."""


class BudgetExhausted(Exception):
    """Raised by FESLimitProblem when the MaxFES budget is exhausted."""

    def __init__(self, best_error: float):
        super().__init__(f"FES budget exhausted (best_error={best_error})")
        self.best_error = best_error


class FESLimitProblem:
    """Wrap a problem to enforce a hard Maximum-Function-Evaluations budget.

    Every call to :meth:`evaluate` increments an internal counter. Once the
    budget is exhausted, additional evaluations are not charged and the best
    error found so far is returned instead, so the wrapped algorithm can keep
    running without ever exceeding ``max_fes`` real evaluations.

    The delegate methods (dimension/bounds/validity) are forwarded to the
    inner problem unchanged.
    """

    def __init__(self, inner, max_fes: int):
        if max_fes < 1:
            raise ValueError(f"max_fes must be >= 1, got {max_fes}")
        self.inner = inner
        self.max_fes = int(max_fes)
        self.fes = 0
        self.best_error = float("inf")

    def evaluate(self, x) -> float:
        """Evaluate ``x`` honoring the MaxFES budget (hard guard).

        Raises :class:`BudgetExhausted` once ``max_fes`` real evaluations have
        been charged, so the run stops EXACTLY at the budget regardless of how
        many evaluations each algorithm performs per iteration (ACO does m=2,
        HO does several per individual, etc.). ``run_with_fes`` catches it.
        """
        if self.fes >= self.max_fes:
            raise BudgetExhausted(self.best_error)
        self.fes += 1
        error = float(self.inner.evaluate(x))
        if error < self.best_error:
            self.best_error = error
        return error

    # --- Delegated problem interface -----------------------------------
    def get_dimension(self) -> int:
        return self.inner.get_dimension()

    def get_lower_bounds(self):
        return self.inner.get_lower_bounds()

    def get_upper_bounds(self):
        return self.inner.get_upper_bounds()

    def is_valid(self, x) -> bool:
        return self.inner.is_valid(x)

    def budget_exhausted(self) -> bool:
        return self.fes >= self.max_fes


def schedule_horizon(algo, budget: int) -> int:
    """Iterations T such that init_evals + T * evals_per_iteration >= budget.

    Iteration-based schedules (PSO inertia, GWO ``a``) then span exactly the
    evaluations the solver really gets. Uses the algorithm's own
    ``init_evals`` / ``evals_per_iteration`` (GA: pop - elitism; ACO_R:
    archive k, then m ants). The FES guard remains the exact stop.
    """
    def _int(v, default):
        try:
            return max(1, int(v() if callable(v) else v))
        except Exception:
            return default
    pop = int(getattr(algo, "population_size", 1))
    epi = _int(getattr(algo, "evals_per_iteration", pop), max(1, pop))
    init = _int(getattr(algo, "init_evals", pop), max(1, pop))
    return max(1, int(math.ceil(max(0, int(budget) - init) / epi)))


def run_with_fes(
    algo_class,
    problem,
    pop_size: int,
    max_fes: int,
    seed: Optional[int] = None,
    algo_params: Optional[dict] = None,
):
    """Run a metaheuristic respecting an exact MaxFES budget.

    The number of iterations is derived as ``ceil(max_fes / pop_size)`` and the
    problem is wrapped in :class:`FESLimitProblem` to act as a hard guard: even
    if an algorithm's per-iteration evaluation count is irregular, no more than
    ``max_fes`` real evaluations are ever charged.

    Args:
        algo_class: Metaheuristic class (e.g. ``PSO``, ``GA``, ``GWO``, ``HO``).
        problem: A problem instance (e.g. :class:`CECProblem`).
        pop_size: Population size.
        max_fes: Maximum number of function evaluations (hard cap).
        seed: Random seed for reproducibility.
        algo_params: Extra keyword arguments forwarded to the algorithm.

    Returns:
        The best error (float) found within the MaxFES budget.
    """
    if pop_size < 1:
        raise ValueError(f"pop_size must be >= 1, got {pop_size}")
    if max_fes < 1:
        raise ValueError(f"max_fes must be >= 1, got {max_fes}")

    algo_params = dict(algo_params or {})

    wrapped = FESLimitProblem(problem, max_fes)
    algo = algo_class(
        problem=wrapped,
        population_size=pop_size,
        max_iterations=1,  # overwritten below using evals_per_iteration
        seed=seed,
        **algo_params,
    )

    # max_iterations is set so the iteration-based schedules (PSO inertia,
    # GWO a, HO temperature) span the actual run length: iters = MaxFES /
    # (evals per iteration). Algorithms whose evals/iter != pop_size expose
    # ``evals_per_iteration`` (ACO -> m; HO -> ~3*pop); the rest default to
    # pop_size. The FES guard (BudgetExhausted) is the EXACT stop on top.
    algo.max_iterations = schedule_horizon(algo, max_fes)

    try:
        algo.execute()
    except BudgetExhausted:
        pass  # budget reached exactly; wrapped.best_error holds the result

    # The hard guard guarantees best_error reflects only charged evaluations.
    best = wrapped.best_error
    if best == float("inf"):
        # Defensive fallback: algorithm produced a best_solution but never
        # routed through the wrapper counter (should not happen here).
        sol = getattr(algo, "best_solution", None)
        if sol is not None and hasattr(sol, "fitness"):
            best = float(sol.fitness())
    return float(best)
