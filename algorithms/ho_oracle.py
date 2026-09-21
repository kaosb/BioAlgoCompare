"""
Oracle variant of the Hippopotamus Optimization Algorithm (HO).

Purpose
-------
Quantify the UPPER BOUND of improvement achievable by per-iteration
multiplicative parameter modulation (alpha, beta, gamma) of HO.

At every iteration, instead of asking a learned IL model for the parameters,
the oracle *cheats*: it snapshots the full optimizer state (population, dominant,
RNG), evaluates a grid of candidate (alpha, beta, gamma) values by rolling the
population forward `lookahead` iteration(s) with each candidate, restores the
state, and finally applies the candidate that produced the best fitness.

Interpretation
--------------
- The oracle is the best a *greedy* per-iteration modulation policy could ever
  do (no real model can beat it within the searched grid + lookahead).
- It includes the NEUTRAL point (1, 1, 1) == unmodulated HO as a reference,
  so we can tell whether ANY modulation helps at all.
- Crucially, the IL action space is alpha in [0.1, 0.9], beta in [0.2, 0.8],
  gamma in [0.3, 1.0] -- which EXCLUDES the neutral point. So we report two
  numbers per state:
    * best fitness over the IL-reachable grid  -> upper bound for HO+IL
    * fitness at the neutral point (1, 1, 1)    -> unmodulated HO
  If neutral <= best-IL across iterations, no IL policy can beat plain HO.

This is the decisive test: if even the oracle cannot improve over neutral HO,
the negative IL result is fundamental, not an artifact of a weak RF model or
domain shift.
"""

from itertools import product
from typing import List, Tuple

import numpy as np

from algorithms.ho import HO
from utils.generate_demos import _clone_ho_state, _restore_ho_state


# IL-reachable action space (same bounds as SimpleILModel / generate_demos)
IL_GRID = {
    "alpha": [0.1, 0.5, 0.9],
    "beta": [0.2, 0.5, 0.8],
    "gamma": [0.3, 0.65, 1.0],
}
NEUTRAL = (1.0, 1.0, 1.0)


class HOOracle(HO):
    """HO whose per-iteration (alpha, beta, gamma) are chosen by a greedy oracle.

    Extra args:
        oracle_grid: list of (alpha, beta, gamma) tuples to search each iteration.
                     Defaults to the 27-point IL-reachable grid PLUS neutral.
        oracle_lookahead: iterations to roll forward when scoring a candidate.
        record_oracle: if True, store per-iteration best-IL vs neutral fitness
                       to quantify the achievable modulation gain.
    """

    def __init__(self, *args, oracle_grid=None, oracle_lookahead: int = 1,
                 n_eval_samples: int = 1,
                 record_oracle: bool = True, demo_log_path: str = None, **kwargs):
        # Strip IL kwargs the parent may receive from the factory; the oracle
        # does not use a learned model.
        kwargs.pop("use_il", None)
        kwargs.pop("il_model_path", None)
        super().__init__(*args, **kwargs)
        # If set, append (state features -> chosen params) demos to this CSV.
        # These are IN-DOMAIN demonstrations (generated in the same environment
        # where the model will be evaluated), unlike the static CVRPLIB demos.
        self.demo_log_path = demo_log_path

        if oracle_grid is None:
            il_pts = list(product(IL_GRID["alpha"], IL_GRID["beta"], IL_GRID["gamma"]))
            oracle_grid = il_pts  # neutral handled separately as reference
        self.oracle_grid: List[Tuple[float, float, float]] = oracle_grid
        self.oracle_lookahead = oracle_lookahead
        # n_eval_samples > 1 => ROBUST oracle: score each candidate by the MEAN
        # fitness over n independent stochastic continuations (different RNG),
        # so the choice does not exploit one realized random draw. This estimates
        # the ceiling achievable by a policy that cannot see future randomness.
        self.n_eval_samples = n_eval_samples
        self.record_oracle = record_oracle

        self._in_rollout = False
        self._fixed_params = NEUTRAL
        self.oracle_log = []  # per-iteration {iter, best_il_fit, neutral_fit, best_params}

    def _get_il_params(self, iteration: int) -> tuple:
        """Return the oracle-selected (alpha, beta, gamma) for this iteration.

        During candidate rollouts we are re-entrant: just return the fixed
        candidate to avoid infinite recursion.
        """
        if self._in_rollout:
            return self._fixed_params

        snapshot = _clone_ho_state(self)

        def _one_rollout(params):
            self._fixed_params = params
            for _ in range(self.oracle_lookahead):
                self.update_population()
            return self.dominant.fitness()

        def score(params):
            if self.n_eval_samples <= 1:
                _restore_ho_state(self, snapshot)
                return _one_rollout(params)
            # ROBUST: mean fitness over n independent rng continuations.
            # Same seed per sample index j across all candidates -> paired.
            saved_rng = self.rng
            vals = []
            for j in range(self.n_eval_samples):
                _restore_ho_state(self, snapshot)
                self.rng = np.random.default_rng([iteration, j])
                vals.append(_one_rollout(params))
            self.rng = saved_rng
            return float(np.mean(vals))

        self._in_rollout = True
        try:
            # Neutral reference (unmodulated HO)
            neutral_fit = score(NEUTRAL)
            # Best over the IL-reachable grid
            best_params, best_fit = None, float("inf")
            for params in self.oracle_grid:
                f = score(params)
                if f < best_fit:
                    best_fit, best_params = f, params
        finally:
            _restore_ho_state(self, snapshot)
            self._in_rollout = False

        if self.record_oracle:
            self.oracle_log.append({
                "iteration": iteration,
                "neutral_fit": float(neutral_fit),
                "best_il_fit": float(best_fit),
                "best_params": tuple(float(x) for x in best_params),
                # positive => modulation beats neutral at this step
                "gain_vs_neutral": float(neutral_fit - best_fit),
            })

        # Log an in-domain demonstration: (state features -> oracle-chosen params)
        if self.demo_log_path is not None:
            self._log_demo(iteration, best_params, neutral_fit - best_fit)

        # Apply whichever is better: if neutral is at least as good, stay neutral.
        # (The oracle is allowed to pick neutral; but neutral is outside the IL
        #  grid, so this is the honest "best the oracle can do, IL-reachable only".)
        return best_params

    def _log_demo(self, iteration, params, gain):
        """Append one in-domain demonstration row to the demo CSV."""
        import csv
        import os
        try:
            from utils.imitation_learning import create_state_from_problem
            state = create_state_from_problem(
                self.problem, self, iteration, self.max_iterations
            )
        except Exception:
            return
        row = dict(state)
        row["alpha"], row["beta"], row["gamma"] = (float(p) for p in params)
        row["gain_vs_neutral"] = float(gain)
        write_header = not os.path.exists(self.demo_log_path)
        with open(self.demo_log_path, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(row.keys()))
            if write_header:
                w.writeheader()
            w.writerow(row)

    def get_oracle_summary(self) -> dict:
        """Aggregate the per-iteration oracle log into a single summary."""
        if not self.oracle_log:
            return {}
        gains = np.array([r["gain_vs_neutral"] for r in self.oracle_log])
        return {
            "n_decisions": len(self.oracle_log),
            "mean_gain_vs_neutral": float(gains.mean()),
            "frac_iters_modulation_helps": float((gains > 1e-9).mean()),
            "max_gain": float(gains.max()),
        }

    def get_parameters(self) -> dict:
        params = super().get_parameters()
        params["algorithm"] = "HO+Oracle"
        params["oracle_grid_size"] = len(self.oracle_grid)
        params["oracle_lookahead"] = self.oracle_lookahead
        return params
