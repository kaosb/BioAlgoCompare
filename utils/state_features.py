"""
Generic, clairvoyance-free state features for IL parameter-control policies.

Computed ONLY from information the algorithm already has at decision time:
cached fitness values, current positions, and the convergence curve. No calls
to problem.evaluate() are ever made here (zero extra FES), and no feature can
leak future randomness or the function's identity/scale:

  * progress          iteration / max_iterations                     [0, 1]
  * diversity         mean per-dim std of positions / search range   [0, ~1]
  * stagnation        iters since last incumbent improvement / T     [0, 1]
  * recent_improve    log10 relative incumbent improvement over the
                      last W iterations, squashed to [0, 1]
  * spread            (median - best) / |median| of cached population
                      fitness, clipped to [0, 10] then /10 (scale-free)
  * dim_norm          dimension / 100

These are the ONLY inputs the learned policy sees, which keeps the policy
FES-fair (features are free) and function-agnostic (no absolute fitness).
"""

from typing import Any, List

import numpy as np

FEATURE_NAMES: List[str] = [
    "progress", "diversity", "stagnation", "recent_improve", "spread",
    "dim_norm",
]

_W = 5  # window (iterations) for the recent-improvement feature


def compute_state_features(algo: Any, iteration: int) -> np.ndarray:
    """Return the 6-dim feature vector for the algorithm's current state."""
    T = max(1, int(algo.max_iterations))
    progress = min(1.0, iteration / T)

    # --- population geometry (positions only; no evaluations) -------------
    pos = np.array([ind.position for ind in algo.population], dtype=float)
    dim = pos.shape[1] if pos.ndim == 2 else 1
    lb = np.asarray(getattr(algo.problem, "get_lower_bounds",
                            lambda: np.zeros(dim))(), dtype=float)
    ub = np.asarray(getattr(algo.problem, "get_upper_bounds",
                            lambda: np.ones(dim))(), dtype=float)
    span = np.maximum(ub - lb, 1e-12)
    diversity = float(np.mean(np.std(pos, axis=0) / span))

    # --- cached population fitness (never triggers an evaluation) ---------
    fits = np.array(
        [ind._fitness for ind in algo.population if getattr(ind, "_fitness", None) is not None],
        dtype=float,
    )
    if fits.size >= 2:
        best, med = float(np.min(fits)), float(np.median(fits))
        spread = (med - best) / (abs(med) + 1e-12)
        spread = float(np.clip(spread, 0.0, 10.0)) / 10.0
    else:
        spread = 0.0

    # --- convergence-curve dynamics ---------------------------------------
    curve = list(getattr(algo, "convergence_curve", []) or [])
    stagnation = 0.0
    recent = 0.0
    if len(curve) >= 2:
        c = np.asarray(curve, dtype=float)
        # iterations since the incumbent last improved
        improved = np.where(np.diff(c) < 0)[0]
        last_imp = int(improved[-1]) + 1 if improved.size else 0
        stagnation = min(1.0, (len(c) - 1 - last_imp) / T)
        # relative improvement over the last W iterations, log-squashed
        w = min(_W, len(c) - 1)
        prev, now = float(c[-1 - w]), float(c[-1])
        rel = (prev - now) / (abs(prev) + 1e-12)   # >= 0 for minimisation
        # map rel in [0, inf) -> [0, 1]: 0 => no progress, 1 => huge progress
        recent = float(np.clip(np.log10(1.0 + rel * 1e4) / 5.0, 0.0, 1.0))

    return np.array(
        [progress, diversity, stagnation, recent, spread, dim / 100.0],
        dtype=float,
    )
