"""
Behavioral-Cloning policy for online parameter control (the IL in "IL improves
optimization").

Trains a multi-output regressor mapping clairvoyance-free state features (see
``utils/state_features.py``) to the multiplicative modulation factors chosen by
the ROBUST oracle. At evaluation time the policy consumes ONLY free features
(zero extra FES) and plugs into any algorithm exposing the ``il_model`` hook:

    model = BCPolicy.load("models/pso_il_cec2014.pkl")
    algo = PSO(problem, ..., use_il=True, il_model=model)

The hook contract is ``il_model.predict(algo, iteration) -> factor tuple``
(the algorithms already unpack it: PSO 3 factors, DE 2, GWO 1).

Design choices (documented for the paper):
  * RandomForestRegressor: reproducible (seeded), CPU-cheap, no tuning drama,
    handles the small demo sets and non-linear feature interactions.
  * Predictions are clipped to the oracle's grid hull [0.6, 1.4] so the policy
    can never extrapolate outside the action space it was demonstrated.
  * Demos where the oracle fell back to neutral ARE kept: the policy must also
    learn WHEN not to modulate.
"""

import json
import os
import pickle
from typing import Any, List, Sequence

import numpy as np
from sklearn.ensemble import RandomForestRegressor

from utils.state_features import compute_state_features, FEATURE_NAMES

_CLIP_LO, _CLIP_HI = 0.6, 1.4


class BCPolicy:
    """Multi-output BC regressor: state features -> actions.

    Actions may be multiplicative factors (default clip hull [0.6, 1.4]) or
    absolute parameter values (pass explicit clip_lo/clip_hi, e.g. the
    demonstrated hull of an expert's (F, CR) trajectory).
    """

    def __init__(self, n_outputs: int, seed: int = 0,
                 clip_lo: float = _CLIP_LO, clip_hi: float = _CLIP_HI):
        self.n_outputs = int(n_outputs)
        self.seed = int(seed)
        # clip bounds may be scalar (shared hull) or per-output array.
        self.clip_lo = np.asarray(clip_lo, float) if np.ndim(clip_lo) else float(clip_lo)
        self.clip_hi = np.asarray(clip_hi, float) if np.ndim(clip_hi) else float(clip_hi)
        self.model = RandomForestRegressor(
            n_estimators=200, min_samples_leaf=5, random_state=seed, n_jobs=1
        )
        self.n_demos = 0

    # --- training ----------------------------------------------------------
    def fit(self, features: Sequence[Sequence[float]],
            actions: Sequence[Sequence[float]]) -> "BCPolicy":
        X = np.asarray(features, dtype=float)
        y = np.asarray(actions, dtype=float)
        if y.ndim == 1:
            y = y.reshape(-1, 1)
        assert y.shape[1] == self.n_outputs, (y.shape, self.n_outputs)
        self.model.fit(X, y)
        self.n_demos = len(X)
        return self

    @classmethod
    def train_from_demo_files(cls, paths: List[str], n_outputs: int,
                              seed: int = 0, clip_lo: float = _CLIP_LO,
                              clip_hi: float = _CLIP_HI) -> "BCPolicy":
        """Train from JSON demo files (OracleMixin.demo_log or teacher logs)."""
        feats, acts = [], []
        for p in paths:
            with open(p) as fh:
                for rec in json.load(fh):
                    feats.append(rec["features"])
                    acts.append(rec["action"])
        policy = cls(n_outputs=n_outputs, seed=seed,
                     clip_lo=clip_lo, clip_hi=clip_hi)
        policy.fit(feats, acts)
        return policy

    # --- inference (the il_model hook) --------------------------------------
    def predict(self, algo: Any, iteration: int):
        """Return the action tuple for the algorithm's state.

        clip_lo/clip_hi may be scalars (shared hull) or per-output arrays
        (independent hull per action dimension, e.g. separate F and CR ranges).
        """
        x = compute_state_features(algo, iteration).reshape(1, -1)
        y = np.atleast_1d(self.model.predict(x)[0])
        lo = getattr(self, "clip_lo", _CLIP_LO)
        hi = getattr(self, "clip_hi", _CLIP_HI)
        y = np.clip(y, lo, hi)
        return tuple(float(v) for v in y)

    # --- persistence ---------------------------------------------------------
    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as fh:
            pickle.dump(self, fh)

    @staticmethod
    def load(path: str) -> "BCPolicy":
        with open(path, "rb") as fh:
            return pickle.load(fh)

    def feature_importances(self) -> dict:
        return dict(zip(FEATURE_NAMES,
                        (float(v) for v in self.model.feature_importances_)))
