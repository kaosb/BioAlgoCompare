"""FES-exact convergence-curve recording (pre-registro fase positiva, v0.2).

Fase 1 of the pre-registration bounds the gain of any budget-allocation
mechanism from the ISOLATED (C0) curves of each solver. The historical campaign
persisted only final errors, so C0 is re-instrumented here: same seeds, same
construction as ``run_with_fes`` (bit-identical finals, verified by the runner),
plus the best-so-far error sampled at every multiple of ``delta`` FES.

``curve[k]`` = best error after ``(k + 1) * delta`` charged evaluations.
"""

import math

from problems.continuous.cec_problem import schedule_horizon, BudgetExhausted, FESLimitProblem


class FESCurveProblem(FESLimitProblem):
    """FESLimitProblem that records the incumbent error on a fixed FES grid."""

    def __init__(self, inner, max_fes: int, delta: int = 500):
        super().__init__(inner, max_fes)
        if delta < 1:
            raise ValueError(f"delta must be >= 1, got {delta}")
        self.delta = int(delta)
        self.curve: list[float] = []

    def evaluate(self, x) -> float:
        err = super().evaluate(x)            # counts FES, updates best_error
        if self.fes % self.delta == 0:
            self.curve.append(float(self.best_error))
        return err


def run_with_curve(algo_class, problem, pop_size: int, max_fes: int,
                   seed: int, delta: int = 500, algo_params: dict | None = None):
    """Exact mirror of ``run_with_fes`` that also returns the FES-grid curve.

    Returns ``(best_error, curve)``. Any divergence from ``run_with_fes`` would
    break the bit-identity check of the Fase 1 runner, so keep both in sync.
    """
    if pop_size < 1 or max_fes < 1:
        raise ValueError("pop_size and max_fes must be >= 1")
    algo_params = dict(algo_params or {})
    wrapped = FESCurveProblem(problem, max_fes, delta=delta)
    algo = algo_class(problem=wrapped, population_size=pop_size,
                      max_iterations=1, seed=seed, **algo_params)
    algo.max_iterations = schedule_horizon(algo, max_fes)
    try:
        algo.execute()
    except BudgetExhausted:
        pass
    best = wrapped.best_error
    if best == float("inf"):
        sol = getattr(algo, "best_solution", None)
        if sol is not None and hasattr(sol, "fitness"):
            best = float(sol.fitness())
    # pad if the run ended between grid points (cannot happen with exact stop,
    # kept as a guard so the array length is always max_fes // delta)
    while len(wrapped.curve) < max_fes // delta:
        wrapped.curve.append(float(wrapped.best_error))
    return float(best), list(wrapped.curve)
