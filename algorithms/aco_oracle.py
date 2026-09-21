"""
Oracle variant of Ant Colony Optimization for continuous domains (ACO_R).

Measures the achievable ceiling of per-iteration multiplicative modulation of
ACO_R's two real control parameters: the convergence speed ``xi`` and the
locality ``q``. Factors multiply the base values:
    xi_eff = xi * xi_factor
    q_eff  = q  * q_factor      (selection probabilities recomputed when != 1)

The neutral point ``(1.0, 1.0)`` reduces exactly to standard ACO_R. The grid
spans roughly +/-40% around each base value, excluding neutral.
"""

from itertools import product

from algorithms.aco import ACO
from algorithms.oracle_mixin import OracleMixin

_XI = [0.6, 1.0, 1.4]
_Q = [0.6, 1.0, 1.4]


class ACOOracle(OracleMixin, ACO):
    """ACO_R whose per-iteration (xi_factor, q_factor) are oracle-chosen."""

    IL_NEUTRAL = (1.0, 1.0)
    IL_GRID = [p for p in product(_XI, _Q) if p != (1.0, 1.0)]

    def get_parameters(self) -> dict:
        params = super().get_parameters()
        params["algorithm"] = "ACO+Oracle"
        params["oracle_grid_size"] = len(self.IL_GRID)
        params["oracle_lookahead"] = self.oracle_lookahead
        params["n_eval_samples"] = self.n_eval_samples
        return params
