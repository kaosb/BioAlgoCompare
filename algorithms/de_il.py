"""
DE+IL: Differential Evolution augmented with the trained Behavioral-Cloning
parameter-control policy — the IL variant of the protocol.

It loads the LEGITIMATE policy: a BC clone of a JADE teacher (state -> absolute
(F, CR)), trained on CEC2014 10D demonstrations
(``models/de_il_jade_cec2014_10d.pkl``), and runs faithful DE/rand/1/bin with
per-iteration control of (F, CR).

Contract note (critical):
  * The policy predicts ABSOLUTE (F, CR); DE's IL hook expects MULTIPLICATIVE
    factors over its base (F, CR). The two are bridged by ``AbsoluteToFactor``
    (utils/bc_policy.py). Feeding the absolute policy straight into DE's hook
    would double-apply the base (0.8 * 0.5 = 0.4) and corrupt the semantics.

Integrity note (8 Jul 2026):
  * This wrapper previously loaded ``de_il_cec2014_10d.pkl`` — the BC policy of
    the MYOPIC (lookahead-1) oracle, which the pre-registered study REFUTED
    (a trivial static F is statistically indistinguishable from it; see
    tesis-mia/gestion_proyecto/AUDITORIA_PROFUNDA_ESTUDIO_IL.md). That model is
    NO LONGER used. The legitimate expert here is the hindsight/JADE clone.
  * Central finding: for DE the optimal (F, CR) control is of LEVEL, not
    SCHEDULE. This variant therefore does NOT beat well-tuned static DE; it is
    reported as an honest negative, not as a "winning proposed algorithm".

Scope notes (declared for the paper):
  * The policy consumes only clairvoyance-free, FES-free state features; the
    FES budget of DE+IL is identical to DE's.
  * Trained at 10D / pop 30 on CEC2014 only. Runs at other dims/pops are
    GENERALIZATION tests (features are scale-free by design, but 50D and
    pop != 30 are outside the demonstrated range -- report as extrapolation).
"""

import os

from algorithms.de import DE

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_MODEL_PATH = os.path.join(_REPO_ROOT, "models", "de_il_jade_cec2014_10d.pkl")

# DE's base (F, CR); the absolute-policy adapter divides by these.
_BASE_F, _BASE_CR = 0.8, 0.9

# Lazy per-process cache: workers instantiate many DEIL objects; load once.
_POLICY_CACHE = {}


def _load_policy():
    if "policy" not in _POLICY_CACHE:
        from utils.bc_policy import BCPolicy, AbsoluteToFactor
        raw = BCPolicy.load(_MODEL_PATH)
        _POLICY_CACHE["policy"] = AbsoluteToFactor(raw, base_f=_BASE_F,
                                                   base_cr=_BASE_CR)
    return _POLICY_CACHE["policy"]


class DEIL(DE):
    """DE with the trained IL (BC-of-JADE) parameter-control policy always on."""

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
