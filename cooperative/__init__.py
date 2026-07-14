"""
Cooperative metaheuristics — real-time cross-algorithm knowledge transfer.

New research line (Fase 3, Jul 2026): heterogeneous metaheuristics run
concurrently on the same problem and transfer useful knowledge online, gated to
prevent negative transfer. Rebanada de magister del eje 1 de la propuesta
FONDECYT Regular 2027 (dir. R. Olivares). Diseno:
tesis-mia/gestion_proyecto/DISENO_TRANSFERENCIA_MHS.md

Public API:
    CooperativeRunner  -- orchestrates N concurrent solvers under a shared FES
                          budget, with periodic gated transfer.
    TransferGate       -- negative-transfer prevention predicate.
    TransferMemory     -- online (condition, transfer, effect) memory.
"""

from cooperative.orchestrator import CooperativeRunner
from cooperative.transfer_gate import TransferGate
from cooperative.transfer_memory import TransferMemory

__all__ = ["CooperativeRunner", "TransferGate", "TransferMemory"]
