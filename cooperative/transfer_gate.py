"""
Negative-transfer prevention gate.

The gate decides whether a candidate transfer (a source solver's elite solution,
or a parameter regime) should be applied to a target solver. It is the central
contribution of Fase 3 and directly operationalizes the IL finding "no signal to
transfer -> do not transfer".

Initial predicate (calibrable): apply a transfer only if
  (1) UTILITY  — the source candidate beats the target's median fitness, AND
  (2) CONDITION — the target is stagnating (no recent improvement), AND
  (3) HISTORY  — the (source, target) pair is not flagged harmful by memory.
Disabling the gate (``enabled=False``) yields the C2 ablation (transfer always).
"""

import numpy as np


class TransferGate:
    def __init__(self, enabled: bool = True, stagnation_window: int = 5,
                 memory=None):
        self.enabled = bool(enabled)
        self.stagnation_window = int(stagnation_window)
        self.memory = memory

    def _is_stagnating(self, target_curve) -> bool:
        w = self.stagnation_window
        if len(target_curve) <= w:
            return False
        recent = target_curve[-(w + 1):]
        # no meaningful improvement over the window
        return (recent[0] - recent[-1]) <= 1e-12 * (abs(recent[0]) + 1e-12)

    def allows(self, source_name: str, target_name: str,
               candidate_fitness: float, target_fitnesses, target_curve) -> bool:
        """Return True iff the transfer passes all gate conditions.

        C2 ablation: with ``enabled=False`` the gate always allows (still logs so
        negative-transfer-avoided can be measured against C3).
        """
        if not self.enabled:
            return True
        # (1) utility: candidate beats target median
        median = float(np.median(np.asarray(target_fitnesses, dtype=float)))
        if candidate_fitness >= median:
            return False
        # (2) condition: target is stagnating
        if not self._is_stagnating(target_curve):
            return False
        # (3) history: pair not flagged harmful
        if self.memory is not None and self.memory.is_harmful_pair(
                source_name, target_name):
            return False
        return True
