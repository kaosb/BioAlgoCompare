"""
Parametric transfer (Nivel B) via functional intent — pre-registro v2 §5.5.

Instead of transferring a solution point (structural, 1 FES, diluted), the
source solver broadcasts a solver-independent FUNCTIONAL INTENT — "what is
working for me right now": INTENSIFY (exploit) or DIVERSIFY (explore). The
target re-instantiates that intent with its OWN control parameters through the
existing ``il_model`` hook (multiplicative factors over the solver's base
parameters; neutral = 1.0 reduces exactly to the base algorithm). Zero FES cost:
only reads already-evaluated state and writes multipliers.

Design rules (frozen in the pre-registro; do NOT tune post-hoc):
  * Intent is extracted ONLY from a HEALTHY source (recent improvement > 0);
    a stagnating source emits None -> nothing to teach (this operationalizes
    the IL lesson: do not transfer where there is no signal).
  * INTENSIFY if the source is improving with LOW population diversity
    (exploitation is what works); DIVERSIFY if improving with high diversity.
  * ADVERSARIAL is a deliberately harmful preset used ONLY by the CTRL+
    positive control (pre-registro §2.2) to verify the gate/rollback DETECTS
    negative transfer. It must never be emitted by classify_intent.
"""

import numpy as np

INTENSIFY = "INTENSIFY"
DIVERSIFY = "DIVERSIFY"
ADVERSARIAL = "ADVERSARIAL"   # CTRL+ only (catastrophic, sanity test)
MODERATE = "MODERATE"         # E4: mildly suboptimal, NOT freezing — tests
                              # whether the gate discriminates SUBTLE harm

# Multiplicative presets per solver class name, per intent (frozen).
# Contracts: DE (mF, mCR) | PSO (w_f, c1_f, c2_f) | GWO (a_f,) |
#            GA (cx_f, mut_f) | ACO (xi_f, q_f)
PRESETS = {
    "DE":  {INTENSIFY: (0.65, 1.10), DIVERSIFY: (1.35, 0.60),
            ADVERSARIAL: (0.10, 0.05), MODERATE: (0.45, 0.55)},
    "PSO": {INTENSIFY: (0.70, 0.80, 1.30), DIVERSIFY: (1.20, 1.30, 0.70),
            ADVERSARIAL: (1.60, 0.10, 0.10), MODERATE: (1.15, 1.10, 0.85)},
    "GWO": {INTENSIFY: (0.50,), DIVERSIFY: (1.50,),
            ADVERSARIAL: (2.50,), MODERATE: (1.70,)},
    "GA":  {INTENSIFY: (1.10, 0.40), DIVERSIFY: (0.90, 2.50),
            ADVERSARIAL: (0.05, 8.00), MODERATE: (0.70, 2.80)},
    "ACO": {INTENSIFY: (0.70, 0.50), DIVERSIFY: (1.30, 1.80),
            ADVERSARIAL: (3.00, 6.00), MODERATE: (1.60, 2.20)},
}

# classify_intent thresholds (frozen)
_IMPROVE_WINDOW = 5        # convergence-curve entries
_REL_IMPROVE_TAU = 1e-6    # source is "healthy" if rel improvement > tau
_DIVERSITY_THRESH = 0.10   # fraction of domain width


def _recent_rel_improvement(curve, window=_IMPROVE_WINDOW):
    if len(curve) <= window:
        return 0.0
    prev, now = curve[-(window + 1)], curve[-1]
    return (prev - now) / (abs(prev) + 1e-12)


def _population_diversity(solver):
    """Mean per-dimension std of positions, normalized by the domain width."""
    pos = np.array([ind.position for ind in solver.population], dtype=float)
    lo = np.min(pos, axis=0)
    hi = np.max(pos, axis=0)
    prob = solver.problem
    try:
        width = float(np.mean(np.asarray(prob.get_upper_bounds(), float)
                              - np.asarray(prob.get_lower_bounds(), float)))
    except Exception:
        width = float(np.mean(hi - lo)) or 1.0
    return float(np.mean(np.std(pos, axis=0)) / (width + 1e-12))


def classify_intent(solver):
    """Extract the functional intent of a (potential) source solver.

    Returns INTENSIFY / DIVERSIFY when the source is healthy (improving),
    None when it has nothing to teach. Never returns ADVERSARIAL.
    """
    if _recent_rel_improvement(solver.convergence_curve) <= _REL_IMPROVE_TAU:
        return None
    div = _population_diversity(solver)
    return INTENSIFY if div < _DIVERSITY_THRESH else DIVERSIFY


class RegimeController:
    """il_model-hook adapter holding the currently committed intent.

    Neutral by default (all factors 1.0 -> exact base algorithm). ``set_intent``
    switches to the preset of the target's solver class; ``reset`` rolls back to
    neutral. The orchestrator owns commit/rollback bookkeeping.
    """

    def __init__(self, solver_key: str):
        if solver_key not in PRESETS:
            raise KeyError(f"no parametric presets for solver '{solver_key}'")
        self.solver_key = solver_key
        self.n_outputs = len(PRESETS[solver_key][INTENSIFY])
        self._neutral = tuple(1.0 for _ in range(self.n_outputs))
        self._active = self._neutral
        self.intent = None

    def set_intent(self, intent: str) -> None:
        self._active = PRESETS[self.solver_key][intent]
        self.intent = intent

    def reset(self) -> None:
        self._active = self._neutral
        self.intent = None

    # --- il_model hook -------------------------------------------------------
    def predict(self, algo, iteration):
        return self._active
