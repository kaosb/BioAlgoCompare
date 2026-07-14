"""
Online behavioral memory for cooperative transfer.

Records (condition, transfer, effect) triples so the gate can learn which
source->target transfers helped vs harmed, and forget/penalize harmful ones.
Simplified version of the propuesta's ``online behavioral memory``.
"""

from collections import defaultdict
from typing import Dict, List, Tuple


class TransferMemory:
    def __init__(self, recency: int = 20):
        # per (source, target) pair: recent observed net effects (Δerror < 0 good)
        self._effects: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        self._recency = int(recency)
        self.records: List[dict] = []

    def record(self, source: str, target: str, condition: dict,
               applied: bool, effect: float = None) -> None:
        """Log a (gated) transfer decision and, if applied, its observed effect.

        effect = target_error_after - target_error_before  (negative = improved).
        """
        self.records.append({
            "source": source, "target": target, "condition": condition,
            "applied": bool(applied), "effect": effect,
        })
        if applied and effect is not None:
            hist = self._effects[(source, target)]
            hist.append(float(effect))
            if len(hist) > self._recency:
                del hist[0]

    def is_harmful_pair(self, source: str, target: str,
                        min_obs: int = 3) -> bool:
        """True if recent applied transfers from source->target hurt on average.

        Operationalizes the negative-transfer lesson: a pair whose recent
        transfers degraded the target (mean effect > 0) is flagged so the gate
        can cool it down.
        """
        hist = self._effects.get((source, target), [])
        if len(hist) < min_obs:
            return False
        return (sum(hist) / len(hist)) > 0.0

    def usefulness_matrix(self) -> Dict[Tuple[str, str], float]:
        """Mean observed effect per pair (for reporting the source->target map)."""
        return {k: (sum(v) / len(v)) for k, v in self._effects.items() if v}
