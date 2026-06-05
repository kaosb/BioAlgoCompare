"""CEC continuous benchmark problems (CEC2014 / CEC2017 / CEC2022).

This module wraps the ``opfunu`` library to expose CEC benchmark functions
through the same problem interface used by the metaheuristics in this
framework (``evaluate``, ``get_dimension``, ``get_lower_bounds``,
``get_upper_bounds``, ``is_valid``).

Design notes
------------
* The objective reported by ``evaluate`` is the **error to the global
  optimum**: ``error = f.evaluate(x) - f.f_global``, which is ``>= 0`` and
  equals ``0`` at the global optimum. This is the standard reporting metric
  for CEC suites and makes results comparable across functions.
* ``FESLimitProblem`` wraps any problem and enforces a hard Maximum number of
  Function Evaluations (MaxFES) budget by tracking a counter and returning the
  best error seen so far once the budget is exhausted (no further "real"
  evaluations are charged).
* ``run_with_fes`` is a thin helper that runs any algorithm in this framework
  respecting an exact MaxFES budget.

References
----------
* Wu, Mallipeddi & Suganthan (2017). Problem definitions and evaluation
  criteria for the CEC 2017 competition on constrained real-parameter
  optimization.
* Nguyen Van Thieu, *opfunu*: An open-source benchmark functions library.
"""

import math
from typing import Optional

import numpy as np

try:  # opfunu emits a harmless pkg_resources deprecation warning on import
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import opfunu
except ImportError as exc:  # pragma: no cover - environment guard
    raise ImportError(
        "CECProblem requires the 'opfunu' package. Install it with "
        "'pip install opfunu'."
    ) from exc


# Map the user-facing suite name to the year token used by opfunu.
_SUITE_TO_YEAR = {
    "CEC2014": "2014",
    "CEC2017": "2017",
    "CEC2022": "2022",
}


class CECProblem:
    """Self-contained wrapper around a single CEC benchmark function.

    Args:
        suite: One of ``'CEC2014'``, ``'CEC2017'`` or ``'CEC2022'``.
        fnum: Function number (1-based), e.g. ``1`` -> ``F1{year}``.
        ndim: Problem dimensionality.

    The wrapped objective is the *error* to the global optimum (>= 0), so the
    global optimum has objective value ``0`` for every function.
    """

    def __init__(self, suite: str, fnum: int, ndim: int):
        if suite not in _SUITE_TO_YEAR:
            raise ValueError(
                f"Unknown suite '{suite}'. Valid options: "
                f"{sorted(_SUITE_TO_YEAR)}"
            )
        if fnum < 1:
            raise ValueError(f"fnum must be >= 1, got {fnum}")
        if ndim < 1:
            raise ValueError(f"ndim must be >= 1, got {ndim}")

        self.suite = suite
        self.fnum = int(fnum)
        self.ndim = int(ndim)
        year = _SUITE_TO_YEAR[suite]
        class_name = f"F{self.fnum}{year}"

        # Discover the function class via opfunu's introspection helper.
        candidates = opfunu.get_functions_based_classname(year)
        match = [c for c in candidates if c.__name__ == class_name]
        if not match:
            available = sorted(c.__name__ for c in candidates)
            raise ValueError(
                f"Function '{class_name}' not found in suite {suite}. "
                f"Available: {available}"
            )

        # Instantiate the function at the requested dimensionality.
        self._func = match[0](ndim=self.ndim)

        # f_global is the objective value at the global optimum.
        self.f_global = float(self._func.f_global)

        # Bounds from the function definition (typically +/- 100 for CEC).
        self._lb = np.asarray(self._func.lb, dtype=float).copy()
        self._ub = np.asarray(self._func.ub, dtype=float).copy()

    def evaluate(self, x) -> float:
        """Return the error to the global optimum (>= 0, optimum = 0)."""
        x = np.asarray(x, dtype=float)
        value = float(self._func.evaluate(x))
        error = value - self.f_global
        # Numerical floor: error is non-negative by definition.
        return error if error > 0.0 else 0.0

    def get_dimension(self) -> int:
        """Return the problem dimensionality."""
        return self.ndim

    def get_lower_bounds(self) -> np.ndarray:
        """Return the per-dimension lower bounds."""
        return self._lb.copy()

    def get_upper_bounds(self) -> np.ndarray:
        """Return the per-dimension upper bounds."""
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
    epi = getattr(algo, "evals_per_iteration", pop_size)
    try:
        epi = int(epi() if callable(epi) else epi)
    except Exception:
        epi = pop_size
    epi = max(1, epi)
    algo.max_iterations = max(1, int(math.ceil(max_fes / epi)))

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
