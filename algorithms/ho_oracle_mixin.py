"""
Oracle variant of HO via the generic OracleMixin (for the cross-algorithm IL
pipeline; the older standalone ``ho_oracle.HOOracle`` remains for the legacy
screen).

HO is parameter-free in Amiri et al. 2024 — the (alpha, beta, gamma)
multiplicative factors are an INVENTED augmentation (neutral (1,1,1) is the
faithful algorithm). HO stays in the study as the reference case: prior
evidence shows modulation does not help it, so the expected pipeline outcome
is neutral-to-negative. Including it keeps the cross-algorithm table honest.
"""

from itertools import product

from algorithms.ho import HO
from algorithms.oracle_mixin import OracleMixin

_F = [0.6, 1.0, 1.4]


class HOOracleM(OracleMixin, HO):
    IL_NEUTRAL = (1.0, 1.0, 1.0)
    IL_GRID = [p for p in product(_F, _F, _F) if p != (1.0, 1.0, 1.0)]

    def _oracle_score(self) -> float:
        """HO tracks its incumbent in ``dominant`` (best_solution may lag)."""
        return float(self.dominant.fitness())

    def get_parameters(self) -> dict:
        params = super().get_parameters()
        params["algorithm"] = "HO+Oracle(mixin)"
        params["oracle_grid_size"] = len(self.IL_GRID)
        params["n_eval_samples"] = self.n_eval_samples
        return params
