"""
Oracle variant of GA via the generic OracleMixin.

Measures the achievable ceiling of per-iteration MULTIPLICATIVE modulation of
GA's two real control parameters (crossover_rate, mutation_rate — both are
probabilities, clipped to [0, 1] inside GA.update_population). Neutral (1, 1)
reduces exactly to standard GA (author values 0.8 / 0.1).
"""

from itertools import product

from algorithms.ga import GA
from algorithms.oracle_mixin import OracleMixin

_F = [0.6, 1.0, 1.4]


class GAOracle(OracleMixin, GA):
    IL_NEUTRAL = (1.0, 1.0)
    IL_GRID = [p for p in product(_F, _F) if p != (1.0, 1.0)]

    def get_parameters(self) -> dict:
        params = super().get_parameters()
        params["algorithm"] = "GA+Oracle"
        params["oracle_grid_size"] = len(self.IL_GRID)
        params["n_eval_samples"] = self.n_eval_samples
        return params
