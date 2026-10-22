"""
Concurrent knowledge transfer between heterogeneous metaheuristics.

New research line (Fase 3, Jul 2026): heterogeneous metaheuristics run
concurrently on the same problem and transfer useful knowledge online, gated to
prevent negative transfer. Current guide:
README_FASE_POSITIVA.md.

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
