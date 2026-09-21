"""
State features for mealpy models — same 6 clairvoyance-free, FES-free features
as utils/state_features.py, computed from a mealpy Optimizer's population and
history so that a mealpy TEACHER (e.g. JADE) and an in-repo STUDENT (e.g. DE)
describe their states in the same language.

Semantic parity with state_features.FEATURE_NAMES:
    progress        fe_used / max_fe (budget-based, horizon-free)
    diversity       mean per-dim std of positions / search range
    stagnation      epochs since incumbent improvement / total epochs
    recent_improve  log-squashed relative incumbent gain over last 5 epochs
    spread          (median - best) / |median| of current population fitness
    dim_norm        dimension / 100
"""

from typing import Any

import numpy as np

_W = 5


def compute_state_features_mealpy(model: Any, max_fe: int,
                                  total_epochs: int) -> np.ndarray:
    """Feature vector for a mealpy model mid-run (no extra evaluations)."""
    # --- progress by consumed evaluations (mealpy tracks nfe_counter) -------
    nfe = getattr(model, "nfe_counter", 0) or 0
    progress = min(1.0, float(nfe) / max(1, max_fe))

    # --- population geometry ------------------------------------------------
    pos = np.array([agent.solution for agent in model.pop], dtype=float)
    dim = pos.shape[1] if pos.ndim == 2 else 1
    lb = np.asarray(model.problem.lb, dtype=float)
    ub = np.asarray(model.problem.ub, dtype=float)
    span = np.maximum(ub - lb, 1e-12)
    diversity = float(np.mean(np.std(pos, axis=0) / span))

    # --- population fitness (already evaluated by mealpy) -------------------
    fits = np.array([agent.target.fitness for agent in model.pop], dtype=float)
    if fits.size >= 2:
        best, med = float(np.min(fits)), float(np.median(fits))
        spread = (med - best) / (abs(med) + 1e-12)
        spread = float(np.clip(spread, 0.0, 10.0)) / 10.0
    else:
        spread = 0.0

    # --- incumbent dynamics from history ------------------------------------
    hist = getattr(model, "history", None)
    curve = ([float(a.target.fitness) for a in hist.list_global_best]
             if hist and getattr(hist, "list_global_best", None) else [])
    stagnation = 0.0
    recent = 0.0
    T = max(1, int(total_epochs))
    if len(curve) >= 2:
        c = np.asarray(curve, dtype=float)
        improved = np.where(np.diff(c) < 0)[0]
        last_imp = int(improved[-1]) + 1 if improved.size else 0
        stagnation = min(1.0, (len(c) - 1 - last_imp) / T)
        w = min(_W, len(c) - 1)
        prev, now = float(c[-1 - w]), float(c[-1])
        rel = (prev - now) / (abs(prev) + 1e-12)
        recent = float(np.clip(np.log10(1.0 + rel * 1e4) / 5.0, 0.0, 1.0))

    return np.array(
        [progress, diversity, stagnation, recent, spread, dim / 100.0],
        dtype=float,
    )
