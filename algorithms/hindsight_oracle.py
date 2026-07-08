"""
Hindsight (optimal-control) oracle for DE parameter control — the LEGITIMATE
expert for the rigorous IL study (tesis-mia gestion_proyecto/DISENO_IL_RIGUROSO).

Unlike the refuted greedy/myopic oracle, this expert is defined by END-TO-END
optimality: for a training instance, it finds the parameter trajectory
(F_1,CR_1),...,(F_K,CR_K) over K temporal blocks that minimizes the EXPECTED
final error of DE, averaged over M seeds (robust; anti-clairvoyance). The
trajectory is optimized by CMA-ES.

This is apprenticeship learning (Abbeel & Ng 2004): the expert is optimal for
the actual objective (final error), it is not a hand-written formula, and it
induces a genuine state->action mapping (each visited state has the action of
its active block). Its per-step actions can then be behaviorally cloned.

Diagnostic use: the trajectory's dynamic variability tells us a-priori whether
there is any SCHEDULE signal for IL to learn (vs a near-constant level).
"""

import math
from typing import Any, List, Tuple

import numpy as np

from problems.continuous.cec_problem import CECProblem, run_with_fes
from algorithms.de import DE

# Action space (absolute DE parameters).
F_LO, F_HI = 0.1, 1.2
CR_LO, CR_HI = 0.0, 1.0
BASE_F, BASE_CR = 0.8, 0.9


class BlockSchedule:
    """Piecewise-constant (F, CR) schedule over K temporal blocks.

    Exposes DE's il_model hook (predict -> multiplicative factors), so DE runs
    unmodified. Blocks are indexed by iteration progress t / max_iterations.
    """

    n_outputs = 2

    def __init__(self, Fs: List[float], CRs: List[float]):
        self.Fs = np.asarray(Fs, dtype=float)
        self.CRs = np.asarray(CRs, dtype=float)
        self.K = len(self.Fs)

    def predict(self, algo: Any, iteration: int):
        T = max(1, int(algo.max_iterations))
        blk = min(self.K - 1, int(iteration / T * self.K))
        return (self.Fs[blk] / BASE_F, self.CRs[blk] / BASE_CR)


def _theta_to_schedule(theta: np.ndarray, K: int) -> BlockSchedule:
    """Map a normalized vector in [0,1]^{2K} to a BlockSchedule."""
    t = np.clip(np.asarray(theta, dtype=float), 0.0, 1.0)
    Fs = F_LO + t[0::2] * (F_HI - F_LO)
    CRs = CR_LO + t[1::2] * (CR_HI - CR_LO)
    return BlockSchedule(Fs, CRs)


def _mean_final_error(suite: str, fnum: int, dim: int, budget: int,
                      sched: BlockSchedule, seeds: List[int], pop: int) -> float:
    errs = []
    for s in seeds:
        prob = CECProblem(suite, fnum, dim)
        errs.append(run_with_fes(DE, prob, pop_size=pop, max_fes=budget, seed=s,
                                 algo_params={"use_il": True, "il_model": sched}))
    return float(np.mean(errs))


def optimize_hindsight(suite: str, fnum: int, dim: int, budget: int,
                       K: int = 5, M: int = 3, cma_budget: int = 400,
                       pop: int = 30, seed: int = 0) -> Tuple[BlockSchedule, dict]:
    """CMA-ES over the 2K block parameters -> the hindsight-optimal schedule.

    Returns (best_schedule, info). ``info`` includes the robust final error of
    the optimum and of the neutral baseline, and the trajectory's dynamic range.
    """
    import warnings
    seeds = list(range(100, 100 + M))

    def objective(X):
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            return _mean_final_error(suite, fnum, dim, budget,
                                     _theta_to_schedule(X, K), seeds, pop)
        return [_mean_final_error(suite, fnum, dim, budget,
                                  _theta_to_schedule(row, K), seeds, pop)
                for row in X]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import minionpy as mp
        bounds = [(0.0, 1.0)] * (2 * K)
        m = mp.Minimizer(func=objective, bounds=bounds, x0=None, algo="CMAES",
                         relTol=0.0, maxevals=int(cma_budget), seed=seed)
        res = m.optimize()
    best = _theta_to_schedule(np.asarray(res.x), K)

    # Diagnostics: neutral baseline and dynamic range of the optimal schedule.
    neutral = BlockSchedule([BASE_F] * K, [BASE_CR] * K)
    neutral_err = _mean_final_error(suite, fnum, dim, budget, neutral, seeds, pop)
    info = {
        "best_err": float(res.fun),
        "neutral_err": float(neutral_err),
        "rel_gain": float((neutral_err - res.fun) / (abs(neutral_err) + 1e-12)),
        "F_traj": best.Fs.tolist(),
        "CR_traj": best.CRs.tolist(),
        "F_range": float(best.Fs.max() - best.Fs.min()),
        "CR_range": float(best.CRs.max() - best.CRs.min()),
    }
    return best, info
