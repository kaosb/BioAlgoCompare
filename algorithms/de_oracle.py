"""
Oracle variant of Differential Evolution (DE/rand/1/bin).

Measures the achievable ceiling of per-iteration multiplicative modulation of
DE's two real, author-grounded control parameters: the scale factor ``F`` and
the crossover rate ``CR`` (the same knobs adaptive DE variants such as JADE and
SHADE learn online). Factors multiply the base values:
    F_eff  = F  * mF
    CR_eff = clip(CR * mCR, 0, 1)

The neutral point ``(1.0, 1.0)`` reduces exactly to standard DE. The grid spans
roughly +/-40% around each base value (literature-meaningful range), excluding
neutral, so ``gain_vs_neutral`` answers: can non-trivial F/CR modulation beat
plain DE at all?
"""

from itertools import product

from algorithms.de import DE
from algorithms.oracle_mixin import OracleMixin

_MF = [0.6, 1.0, 1.4]
_MCR = [0.6, 1.0, 1.4]


class DEOracle(OracleMixin, DE):
    """DE whose per-iteration (mF, mCR) are chosen by a greedy/robust oracle."""

    IL_NEUTRAL = (1.0, 1.0)
    IL_GRID = [p for p in product(_MF, _MCR) if p != (1.0, 1.0)]

    def get_parameters(self) -> dict:
        params = super().get_parameters()
        params["algorithm"] = "DE+Oracle"
        params["oracle_grid_size"] = len(self.IL_GRID)
        params["oracle_lookahead"] = self.oracle_lookahead
        params["n_eval_samples"] = self.n_eval_samples
        return params
