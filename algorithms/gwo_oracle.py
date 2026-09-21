"""
Oracle variant of GWO via the generic OracleMixin.

Measures the achievable ceiling of per-iteration MULTIPLICATIVE modulation of
GWO's single real control coefficient ``a`` (which decreases linearly 2->0 and
governs exploration vs exploitation). Factor multiplies the base schedule:
    a_eff = (2 - 2 t/T) * a_f
Neutral (1.0,) reduces exactly to standard GWO.
"""

from algorithms.gwo import GWO
from algorithms.oracle_mixin import OracleMixin


class GWOOracle(OracleMixin, GWO):
    IL_NEUTRAL = (1.0,)
    # 1-D grid around neutral (excludes 1.0).
    IL_GRID = [(0.5,), (0.7,), (0.85,), (1.15,), (1.3,), (1.5,)]

    def get_parameters(self) -> dict:
        params = super().get_parameters()
        params["algorithm"] = "GWO+Oracle"
        params["oracle_grid_size"] = len(self.IL_GRID)
        params["n_eval_samples"] = self.n_eval_samples
        return params
