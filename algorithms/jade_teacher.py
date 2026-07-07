"""
LoggingJADE — the EXPERT TEACHER for the pre-registered expert-imitation study
(tesis-mia gestion_proyecto/PREREGISTRO_IL_EXPERTO.md).

Subclasses mealpy's validated JADE (Zhang & Sanderson 2009: per-individual
Cauchy-F / Normal-CR, success-history Lehmer/arithmetic means, external
archive) and, after every generation, logs one demonstration:

    (6 state features of the teacher's population) -> (dyn_miu_f, dyn_miu_cr)

The logged (miu_F, miu_CR) are JADE's CURRENT adaptive parameter beliefs --
the genuine expert signal a fixed-parameter DE student will try to imitate.
No algorithmic behaviour is modified (logging only), so the teacher remains
the validated implementation bit-for-bit.
"""

from typing import Optional

from mealpy.evolutionary_based.DE import JADE

from utils.mealpy_features import compute_state_features_mealpy


class LoggingJADE(JADE):
    """JADE that records (state features -> (miu_F, miu_CR)) each generation."""

    def __init__(self, *args, log_max_fe: Optional[int] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.demo_log = []
        self._log_max_fe = log_max_fe  # budget for the progress feature

    def evolve(self, epoch):
        super().evolve(epoch)
        try:
            feats = compute_state_features_mealpy(
                self, max_fe=self._log_max_fe or (self.epoch * self.pop_size),
                total_epochs=self.epoch,
            )
            self.demo_log.append({
                "features": feats.tolist(),
                # ABSOLUTE expert parameters (not multiplicative factors).
                "action": (float(self.dyn_miu_f), float(self.dyn_miu_cr)),
            })
        except Exception:
            # Logging must never alter or abort the teacher's run.
            pass
