"""
DE+IL: Differential Evolution augmented with the trained Behavioral-Cloning
parameter-control policy — the "proposed algorithm" slot of the protocol.

Self-contained wrapper so the protocol harness can instantiate it exactly like
any other algorithm (``cls(problem, population_size, max_iterations, seed)``).
It loads the BC policy trained on CEC2014 10D demonstrations
(``models/de_il_cec2014_10d.pkl``) and runs faithful DE/rand/1/bin with
per-iteration multiplicative modulation of (F, CR).

Scope notes (declared for the paper):
  * The policy consumes only clairvoyance-free, FES-free state features; the
    FES budget of DE+IL is identical to DE's.
  * Trained at 10D / pop 30 on CEC2014 only. Runs at other dims/pops are
    GENERALIZATION tests (features are scale-free by design, but 50D is
    outside the demonstrated dim range -- report as extrapolation).
"""

import os

from algorithms.de import DE

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_MODEL_PATH = os.path.join(_REPO_ROOT, "models", "de_il_cec2014_10d.pkl")

# Lazy per-process cache: workers instantiate many DEIL objects; load once.
_POLICY_CACHE = {}


def _load_policy():
    if "policy" not in _POLICY_CACHE:
        from utils.bc_policy import BCPolicy
        _POLICY_CACHE["policy"] = BCPolicy.load(_MODEL_PATH)
    return _POLICY_CACHE["policy"]


class DEIL(DE):
    """DE with the trained IL (BC) parameter-control policy always on."""

    def __init__(self, problem, population_size=30, max_iterations=100,
                 seed=None, **kwargs):
        kwargs.pop("use_il", None)
        kwargs.pop("il_model", None)
        super().__init__(problem, population_size=population_size,
                         max_iterations=max_iterations, seed=seed,
                         use_il=True, il_model=_load_policy(), **kwargs)

    def get_parameters(self) -> dict:
        params = super().get_parameters()
        params["algorithm"] = "DE+IL"
        params["il_policy"] = os.path.basename(_MODEL_PATH)
        return params
