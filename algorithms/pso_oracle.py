"""
Oracle variant of PSO via the generic OracleMixin.

Measures the achievable ceiling of per-iteration MULTIPLICATIVE modulation of
PSO's three real control parameters (inertia w, cognitive c1, social c2 --
Kennedy-Eberhart / Shi-Eberhart). Factors multiply the base schedule:
    w_eff  = base_w(t) * w_f
    c1_eff = 2.0 * c1_f
    c2_eff = 2.0 * c2_f
Neutral (1, 1, 1) reduces exactly to standard PSO. Supersedes the earlier
absolute-value PSO oracle from the (discarded) HO study; this version shares
the robust RNG-averaged methodology used for DE/ACO oracles.
"""

from itertools import product

from algorithms.pso import PSO
from algorithms.oracle_mixin import OracleMixin

_F = [0.6, 1.0, 1.4]


class PSOOracle(OracleMixin, PSO):
    IL_NEUTRAL = (1.0, 1.0, 1.0)
    IL_GRID = [p for p in product(_F, _F, _F) if p != (1.0, 1.0, 1.0)]

    def get_parameters(self) -> dict:
        params = super().get_parameters()
        params["algorithm"] = "PSO+Oracle"
        params["oracle_grid_size"] = len(self.IL_GRID)
        params["n_eval_samples"] = self.n_eval_samples
        return params
