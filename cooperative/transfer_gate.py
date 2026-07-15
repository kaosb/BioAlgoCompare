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

    def allows_parametric(self, source_name: str, target_name: str,
                          source_curve, target_curve, intent: str) -> bool:
        """Gate for parametric (functional-intent) transfers.

        Conditions (pre-registro v2, frozen):
          (1) SOURCE HEALTH — the source must be improving (a stagnating source
              has nothing to teach; operationalizes the IL 'no signal' lesson).
          (2) TARGET CONDITION — the target must be stagnating (a target that is
              improving should not be perturbed).
          (3) HISTORY — the (source, target, intent) triple must not be flagged
              harmful by the rollback memory.
        ``enabled=False`` = C2p ablation (always allow).
        """
        if not self.enabled:
            return True
        if intent is None:
            return False
        # (1) source health: improvement over the stagnation window
        w = self.stagnation_window
        if len(source_curve) > w:
            prev, now = source_curve[-(w + 1)], source_curve[-1]
            if (prev - now) <= 1e-12 * (abs(prev) + 1e-12):
                return False
        else:
            return False
        # (2) target stagnating
        if not self._is_stagnating(target_curve):
            return False
        # (3) triple not flagged harmful
        if self.memory is not None and self.memory.is_harmful_triple(
                source_name, target_name, intent):
            return False
        return True
