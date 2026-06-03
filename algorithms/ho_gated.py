"""
HO with GATED Imitation Learning.

Addresses the structural limitation found in the plain HO+IL: the multiplicative
action space (alpha in [0.1,0.9], beta in [0.2,0.8], gamma in [0.3,1.0]) cannot
represent the NEUTRAL point (1,1,1), which the oracle showed to be optimal in
~61% of optimization states. Plain HO+IL is therefore forced to perturb at every
step, injecting harmful modulation where none is warranted.

The gated model decouples two decisions:
  1. GATE (classifier): should we modulate at all in this state?  (highly
     learnable: ~0.91 AUC from oracle demos)
  2. MAGNITUDE (regressors): if yes, which (alpha, beta, gamma)?  (weakly
     learnable: R^2 ~ 0.2)

At inference: gate == 0  -> return neutral (1, 1, 1) (== unmodulated HO);
              gate == 1  -> return clipped regressor predictions.

The model file is a plain pickle dict:
  {gate, reg_alpha, reg_beta, reg_gamma, scaler, feature_names}
"""

import pickle

import numpy as np

from algorithms.ho import HO


class HOGatedIL(HO):
    """HO whose (alpha,beta,gamma) come from a gated IL model (gate + regressors)."""

    def __init__(self, *args, gated_model_path: str = None,
                 gate_threshold: float = 0.5, **kwargs):
        kwargs.pop("use_il", None)
        kwargs.pop("il_model_path", None)
        super().__init__(*args, **kwargs)
        self.use_il = True  # enable the IL code path in update_population
        # STRICT neutral fallback: modulate only if P(modulation helps) >= threshold.
        # threshold=0.5 == default gate; higher == stricter (stays neutral more,
        # guaranteeing HO+IL closer to HO -- honoring Rodrigo's "no puede funcionar
        # peor que el que no tiene mejora").
        self.gate_threshold = gate_threshold
        self._gated = None
        self._gate_on = 0
        self._gate_off = 0
        if gated_model_path:
            with open(gated_model_path, "rb") as f:
                self._gated = pickle.load(f)

    def _get_il_params(self, iteration: int) -> tuple:
        if self._gated is None:
            return 1.0, 1.0, 1.0
        try:
            from utils.imitation_learning import create_state_from_problem
            state = create_state_from_problem(
                self.problem, self, iteration, self.max_iterations
            )
            feats = np.array(
                [state.get(f, 0) for f in self._gated["feature_names"]]
            ).reshape(1, -1)
            feats = self._gated["scaler"].transform(feats)
            gate = self._gated["gate"]
            try:
                p_help = float(gate.predict_proba(feats)[0][1])
            except Exception:
                p_help = float(gate.predict(feats)[0])
            if p_help < self.gate_threshold:
                self._gate_off += 1
                return 1.0, 1.0, 1.0  # neutral: unmodulated HO
            self._gate_on += 1
            a = float(np.clip(self._gated["reg_alpha"].predict(feats)[0], 0.1, 0.9))
            b = float(np.clip(self._gated["reg_beta"].predict(feats)[0], 0.2, 0.8))
            g = float(np.clip(self._gated["reg_gamma"].predict(feats)[0], 0.3, 1.0))
            return a, b, g
        except Exception:
            self._il_fallback_count += 1
            return 1.0, 1.0, 1.0

    def get_parameters(self) -> dict:
        params = super().get_parameters()
        params["algorithm"] = "HO+GatedIL"
        tot = self._gate_on + self._gate_off
        params["gate_modulate_frac"] = self._gate_on / tot if tot else 0.0
        return params
